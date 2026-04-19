from __future__ import annotations

import io
import json
import math
import os
import re
import ssl
import urllib.parse
import urllib.request
import zipfile
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

try:
    import certifi
except ImportError:  # pragma: no cover - fallback for bare environments
    certifi = None


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
API_KEYS_PATH = DATA_DIR / "api_keys.local.json"
DART_CORP_CACHE_PATH = DATA_DIR / "dart_corp_codes_cache.json"
ECOS_BASE_URL = "https://ecos.bok.or.kr/api"
DART_BASE_URL = "https://opendart.fss.or.kr/api"


class ExternalApiError(RuntimeError):
    pass


def bounded_score(value: float) -> float:
    return max(0.0, min(100.0, float(value)))


def load_api_keys() -> dict[str, str]:
    keys = {
        "ecos_api_key": os.getenv("ECOS_API_KEY", "").strip(),
        "dart_api_key": os.getenv("DART_API_KEY", "").strip(),
    }

    if API_KEYS_PATH.exists():
        with API_KEYS_PATH.open("r", encoding="utf-8") as fp:
            file_keys = json.load(fp)
        keys["ecos_api_key"] = keys["ecos_api_key"] or str(file_keys.get("ecos_api_key", "")).strip()
        keys["dart_api_key"] = keys["dart_api_key"] or str(file_keys.get("dart_api_key", "")).strip()

    return keys


def _ssl_context() -> ssl.SSLContext:
    if certifi is not None:
        return ssl.create_default_context(cafile=certifi.where())
    return ssl.create_default_context()


def _read_json_url(url: str, timeout: float = 20.0) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": "FlowBiz-Ultra/0.1"})
    with urllib.request.urlopen(request, timeout=timeout, context=_ssl_context()) as response:
        payload = response.read()
    return json.loads(payload.decode("utf-8"))


def _read_bytes_url(url: str, timeout: float = 30.0) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "FlowBiz-Ultra/0.1"})
    with urllib.request.urlopen(request, timeout=timeout, context=_ssl_context()) as response:
        return response.read()


def _add_months(base: date, months: int) -> date:
    year = base.year + ((base.month - 1 + months) // 12)
    month = ((base.month - 1 + months) % 12) + 1
    return date(year, month, 1)


def _month_text(value: date) -> str:
    return f"{value.year}{value.month:02d}"


def _parse_number(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text in {"-", "N/A"}:
        return None
    negative = text.startswith("(") and text.endswith(")")
    cleaned = text.replace(",", "").replace("(", "").replace(")", "")
    try:
        number = float(cleaned)
    except ValueError:
        return None
    return -number if negative else number


def _normalize_corp_name(value: str) -> str:
    lowered = value.lower()
    lowered = lowered.replace("주식회사", "")
    lowered = lowered.replace("(주)", "")
    lowered = lowered.replace("㈜", "")
    return re.sub(r"[^0-9a-z가-힣]", "", lowered)


def _account_value(rows: list[dict[str, Any]], names: list[str]) -> float | None:
    for row in rows:
        account_name = str(row.get("account_nm", "")).strip()
        if account_name in names:
            return _parse_number(row.get("thstrm_amount"))
    return None


class EcosClient:
    def __init__(self, api_key: str) -> None:
        if not api_key:
            raise ExternalApiError("ECOS API key is not configured.")
        self.api_key = api_key

    def _stat_rows(self, stat_code: str, cycle: str, start_time: str, end_time: str, *items: str) -> list[dict[str, Any]]:
        params = [stat_code, cycle, start_time, end_time, *items]
        encoded_params = "/".join(urllib.parse.quote(str(param), safe="") for param in params)
        url = f"{ECOS_BASE_URL}/StatisticSearch/{self.api_key}/json/kr/1/200/{encoded_params}"
        payload = _read_json_url(url)
        search = payload.get("StatisticSearch", {})
        rows = search.get("row", [])
        if not rows:
            raise ExternalApiError(f"ECOS returned no rows for stat_code={stat_code}.")
        return rows

    def _window(self, months_back: int = 24) -> tuple[str, str]:
        end = date.today().replace(day=1) - timedelta(days=1)
        end = end.replace(day=1)
        start = _add_months(end, -(months_back - 1))
        return _month_text(start), _month_text(end)

    def fetch_base_rate_latest(self) -> dict[str, Any]:
        start, end = self._window()
        rows = self._stat_rows("722Y001", "M", start, end, "0101000")
        latest = rows[-1]
        return {
            "time": latest["TIME"],
            "value": float(latest["DATA_VALUE"]),
            "label": latest["ITEM_NAME1"],
        }

    def fetch_sme_loan_rate_latest(self) -> dict[str, Any]:
        start, end = self._window()
        rows = self._stat_rows("121Y006", "M", start, end, "BECBLA0202")
        latest = rows[-1]
        return {
            "time": latest["TIME"],
            "value": float(latest["DATA_VALUE"]),
            "label": latest["ITEM_NAME1"],
        }

    def fetch_cpi_yoy_latest(self) -> dict[str, Any]:
        start, end = self._window()
        rows = self._stat_rows("901Y009", "M", start, end, "0")
        series = {row["TIME"]: float(row["DATA_VALUE"]) for row in rows}
        latest_time = sorted(series)[-1]
        latest_month = datetime.strptime(latest_time, "%Y%m").date()
        prior_time = _month_text(_add_months(latest_month, -12))
        if prior_time not in series:
            raise ExternalApiError("ECOS CPI series does not have a 12 month comparison point.")

        latest_value = series[latest_time]
        prior_value = series[prior_time]
        yoy = ((latest_value / prior_value) - 1.0) * 100.0
        return {
            "time": latest_time,
            "value": round(latest_value, 2),
            "yoy_pct": round(yoy, 2),
        }

    def fetch_bsi_latest(self, industry_code: str) -> dict[str, Any]:
        start, end = self._window()
        rows = self._stat_rows("512Y008", "M", start, end, "BA", industry_code)
        latest = rows[-1]
        return {
            "time": latest["TIME"],
            "value": float(latest["DATA_VALUE"]),
            "industry_code": industry_code,
            "industry_name": latest.get("ITEM_NAME2", industry_code),
            "label": latest.get("ITEM_NAME1", "업황전망BSI"),
        }

    def score_macro_signal(self, industry_code: str, fallback_industry_code: str = "C0000") -> dict[str, Any]:
        warnings: list[str] = []
        try:
            bsi = self.fetch_bsi_latest(industry_code)
        except ExternalApiError:
            if industry_code != fallback_industry_code:
                warnings.append(f"ECOS 업종코드 {industry_code} 조회가 실패하여 {fallback_industry_code}로 대체했습니다.")
                bsi = self.fetch_bsi_latest(fallback_industry_code)
            else:
                raise

        base_rate = self.fetch_base_rate_latest()
        loan_rate = self.fetch_sme_loan_rate_latest()
        cpi = self.fetch_cpi_yoy_latest()

        adjustments: list[dict[str, Any]] = []
        score = 50.0

        if bsi["value"] >= 105:
            delta = 20
        elif bsi["value"] >= 95:
            delta = 12
        elif bsi["value"] >= 85:
            delta = 5
        elif bsi["value"] >= 75:
            delta = 0
        elif bsi["value"] >= 65:
            delta = -5
        else:
            delta = -10
        score += delta
        adjustments.append({"metric": "bsi_outlook", "value": bsi["value"], "delta": delta})

        if loan_rate["value"] <= 4.0:
            delta = 10
        elif loan_rate["value"] <= 5.0:
            delta = 5
        elif loan_rate["value"] <= 6.0:
            delta = 0
        elif loan_rate["value"] <= 7.0:
            delta = -5
        else:
            delta = -10
        score += delta
        adjustments.append({"metric": "sme_loan_rate", "value": loan_rate["value"], "delta": delta})

        if base_rate["value"] <= 2.5:
            delta = 5
        elif base_rate["value"] <= 3.5:
            delta = 0
        else:
            delta = -5
        score += delta
        adjustments.append({"metric": "base_rate", "value": base_rate["value"], "delta": delta})

        if cpi["yoy_pct"] <= 2.5:
            delta = 5
        elif cpi["yoy_pct"] <= 4.0:
            delta = 0
        else:
            delta = -5
        score += delta
        adjustments.append({"metric": "cpi_yoy", "value": cpi["yoy_pct"], "delta": delta})

        return {
            "score": round(bounded_score(score), 2),
            "warnings": warnings,
            "details": {
                "bsi": bsi,
                "base_rate": base_rate,
                "sme_loan_rate": loan_rate,
                "cpi": cpi,
                "adjustments": adjustments,
            },
        }


class DartClient:
    def __init__(self, api_key: str) -> None:
        if not api_key:
            raise ExternalApiError("DART API key is not configured.")
        self.api_key = api_key

    def _json(self, endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
        query = urllib.parse.urlencode(params)
        url = f"{DART_BASE_URL}/{endpoint}?{query}"
        payload = _read_json_url(url)
        status = payload.get("status")
        if status and status != "000":
            raise ExternalApiError(f"DART error {status}: {payload.get('message', 'unknown error')}")
        return payload

    def _load_corp_codes(self) -> list[dict[str, str]]:
        if DART_CORP_CACHE_PATH.exists():
            age = datetime.now() - datetime.fromtimestamp(DART_CORP_CACHE_PATH.stat().st_mtime)
            if age < timedelta(days=7):
                with DART_CORP_CACHE_PATH.open("r", encoding="utf-8") as fp:
                    return json.load(fp)

        payload = _read_bytes_url(f"{DART_BASE_URL}/corpCode.xml?crtfc_key={self.api_key}")
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            name = archive.namelist()[0]
            with archive.open(name) as xml_file:
                root = ElementTree.parse(xml_file).getroot()

        rows: list[dict[str, str]] = []
        for node in root.findall("list"):
            rows.append(
                {
                    "corp_code": str(node.findtext("corp_code", "")).strip(),
                    "corp_name": str(node.findtext("corp_name", "")).strip(),
                    "stock_code": str(node.findtext("stock_code", "")).strip(),
                    "modify_date": str(node.findtext("modify_date", "")).strip(),
                }
            )

        with DART_CORP_CACHE_PATH.open("w", encoding="utf-8") as fp:
            json.dump(rows, fp, ensure_ascii=False)
        return rows

    def find_company_reference(
        self,
        corp_code: str | None = None,
        corp_name: str | None = None,
        stock_code: str | None = None,
    ) -> dict[str, str] | None:
        rows = self._load_corp_codes()

        if corp_code:
            for row in rows:
                if row["corp_code"] == corp_code:
                    return row
            return None

        if stock_code:
            stock_code = stock_code.zfill(6)
            for row in rows:
                if row["stock_code"] == stock_code:
                    return row
            return None

        if not corp_name:
            return None

        normalized_target = _normalize_corp_name(corp_name)
        exact_matches = [row for row in rows if _normalize_corp_name(row["corp_name"]) == normalized_target]
        if exact_matches:
            return sorted(exact_matches, key=lambda row: (row["stock_code"] == "", len(row["corp_name"])))[0]

        partial_matches = [row for row in rows if normalized_target in _normalize_corp_name(row["corp_name"])]
        if partial_matches:
            return sorted(partial_matches, key=lambda row: (row["stock_code"] == "", len(row["corp_name"])))[0]
        return None

    def fetch_company_info(self, corp_code: str) -> dict[str, Any]:
        return self._json("company.json", {"crtfc_key": self.api_key, "corp_code": corp_code})

    def fetch_latest_financials(self, corp_code: str, lookback_years: int = 3) -> dict[str, Any] | None:
        current_year = date.today().year
        for year in range(current_year - 1, current_year - lookback_years - 1, -1):
            payload = self._json(
                "fnlttSinglAcnt.json",
                {
                    "crtfc_key": self.api_key,
                    "corp_code": corp_code,
                    "bsns_year": str(year),
                    "reprt_code": "11011",
                },
            )
            rows = payload.get("list", [])
            if rows:
                return {"bsns_year": year, "rows": rows}
        return None

    def score_disclosure_signal(
        self,
        corp_code: str | None = None,
        corp_name: str | None = None,
        stock_code: str | None = None,
        lookback_years: int = 3,
    ) -> dict[str, Any]:
        reference = self.find_company_reference(corp_code=corp_code, corp_name=corp_name, stock_code=stock_code)
        if not reference:
            return {
                "score": None,
                "warnings": ["DART 법인코드를 찾지 못했습니다."],
                "details": {
                    "corp_reference": None,
                },
            }

        company_info = self.fetch_company_info(reference["corp_code"])
        financials = self.fetch_latest_financials(reference["corp_code"], lookback_years=lookback_years)

        score = 25.0
        adjustments: list[dict[str, Any]] = [{"metric": "dart_match", "value": reference["corp_code"], "delta": 25}]

        corp_cls = str(company_info.get("corp_cls", "")).strip()
        if corp_cls in {"Y", "K"}:
            delta = 20
        elif corp_cls:
            delta = 10
        else:
            delta = 0
        score += delta
        adjustments.append({"metric": "corp_class", "value": corp_cls or "unknown", "delta": delta})

        est_dt = str(company_info.get("est_dt", "")).strip()
        if est_dt:
            try:
                established = datetime.strptime(est_dt, "%Y%m%d").date()
                years = max(0.0, (date.today() - established).days / 365.25)
            except ValueError:
                years = 0.0
            if years >= 10:
                delta = 7
            elif years >= 5:
                delta = 5
            elif years >= 3:
                delta = 3
            else:
                delta = 0
            score += delta
            adjustments.append({"metric": "company_age_years", "value": round(years, 1), "delta": delta})

        metrics: dict[str, float | None] = {}
        if financials:
            rows = financials["rows"]
            revenue = _account_value(rows, ["매출액", "영업수익", "수익(매출액)", "영업수익(매출액)"])
            operating_income = _account_value(rows, ["영업이익", "영업손익"])
            net_income = _account_value(rows, ["당기순이익(손실)", "당기순이익"])
            assets = _account_value(rows, ["자산총계"])
            liabilities = _account_value(rows, ["부채총계"])
            equity = _account_value(rows, ["자본총계"])
            debt_ratio = None
            if equity and equity > 0 and liabilities is not None:
                debt_ratio = (liabilities / equity) * 100.0

            metrics = {
                "revenue": revenue,
                "operating_income": operating_income,
                "net_income": net_income,
                "assets": assets,
                "liabilities": liabilities,
                "equity": equity,
                "debt_ratio_pct": round(debt_ratio, 2) if debt_ratio is not None else None,
            }

            if revenue is not None:
                if revenue >= 100_000_000_000:
                    delta = 12
                elif revenue >= 10_000_000_000:
                    delta = 9
                elif revenue >= 1_000_000_000:
                    delta = 6
                elif revenue > 0:
                    delta = 3
                else:
                    delta = 0
                score += delta
                adjustments.append({"metric": "revenue_scale", "value": revenue, "delta": delta})

            if operating_income is not None:
                delta = 12 if operating_income > 0 else -4
                score += delta
                adjustments.append({"metric": "operating_income", "value": operating_income, "delta": delta})

            if net_income is not None:
                delta = 10 if net_income > 0 else -4
                score += delta
                adjustments.append({"metric": "net_income", "value": net_income, "delta": delta})

            if debt_ratio is not None:
                if debt_ratio <= 100:
                    delta = 12
                elif debt_ratio <= 200:
                    delta = 8
                elif debt_ratio <= 300:
                    delta = 4
                elif debt_ratio <= 500:
                    delta = -2
                else:
                    delta = -8
                score += delta
                adjustments.append({"metric": "debt_ratio_pct", "value": round(debt_ratio, 2), "delta": delta})

        return {
            "score": round(bounded_score(score), 2),
            "warnings": [],
            "details": {
                "corp_reference": reference,
                "company_info": company_info,
                "financial_year": financials["bsns_year"] if financials else None,
                "metrics": metrics,
                "adjustments": adjustments,
            },
        }
