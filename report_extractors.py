from __future__ import annotations

import json
import re
from io import BytesIO
from pathlib import Path
from typing import Any

from pypdf import PdfReader


PARSER_VERSION = "2026.04.19"


def extract_pdf_text(raw_bytes: bytes) -> str:
    reader = PdfReader(BytesIO(raw_bytes))
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def normalize_compact_text(value: str) -> str:
    text = value
    text = re.sub(r"\(\s*주\s*\)", "(주)", text)
    text = re.sub(r"(?<=[가-힣A-Za-z0-9])\s+(?=[가-힣A-Za-z0-9])", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def clean_company_name(value: str | None) -> str | None:
    if not value:
        return None
    text = value.strip()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\(\s*주\s*\)", "(주)", text)
    text = re.sub(r"(?<=[가-힣A-Za-z])\s+(?=[가-힣A-Za-z])", "", text)
    return text.strip()


def infer_short_name(company_name: str | None) -> str | None:
    if not company_name:
        return None
    value = re.sub(r"^\(?주\)?|\(주\)|㈜", "", company_name).strip()
    return value or None


def infer_company_name_from_source(source_file: str | None) -> str | None:
    if not source_file:
        return None
    base = Path(source_file).stem
    base = re.sub(r"^신용평가리포트[_-]*", "", base)
    base = re.sub(r"[\s_-]+(회사소개서|현황자료|기업리포트|신용평가리포트).*", "", base)
    base = re.sub(r"[\s_-]+20\d{2}.*$", "", base)
    base = re.sub(r"\s+", " ", base).strip(" _-")
    return clean_company_name(base) if base else None


def find_first(patterns: list[str], text: str) -> re.Match[str] | None:
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match
    return None


def parse_table_financial_summary(text: str) -> dict[str, dict[str, str]]:
    summary: dict[str, dict[str, str]] = {}

    def is_numeric_cell(value: str) -> bool:
        return bool(re.fullmatch(r"-|\-?\d{1,3}(?:,\d{3})*", value))

    def split_merged_numeric_token(value: str) -> tuple[str, str] | None:
        for index in range(1, len(value)):
            left = value[:index]
            right = value[index:]
            if is_numeric_cell(left) and is_numeric_cell(right):
                return left, right
        return None

    def tokenize_financial_row(rest: str) -> list[str]:
        tokens = re.findall(r"-?[\d,]+|-", rest)
        repaired = list(tokens)
        while len(repaired) < 6:
            split_applied = False
            for idx, token in enumerate(repaired):
                if token == "-" or is_numeric_cell(token):
                    continue
                split_tokens = split_merged_numeric_token(token)
                if split_tokens:
                    repaired = repaired[:idx] + [split_tokens[0], split_tokens[1]] + repaired[idx + 1 :]
                    split_applied = True
                    break
            if not split_applied:
                break
        return repaired

    # FlowScore-style compact summary block
    summary_match = re.search(
        r"손익계산서요약.*?항목(\d{4})(\d{4})YoY"
        r".*?매출액([0-9.]+억원)([0-9.]+억원)([-+0-9.]+%)"
        r".*?영업이익([0-9.\-]+억원)([0-9.\-]+억원)([-+0-9.]+%)"
        r".*?당기순이익([0-9.\-]+억원)([0-9.\-]+억원)([-+0-9.]+%)",
        text,
    )
    if summary_match:
        year_a, year_b = summary_match.group(1), summary_match.group(2)
        summary[year_a] = {
            "sales": summary_match.group(3),
            "operating_profit": summary_match.group(6),
            "net_income": summary_match.group(9),
        }
        summary[year_b] = {
            "sales": summary_match.group(4),
            "operating_profit": summary_match.group(7),
            "net_income": summary_match.group(10),
        }

    def normalize_financial_cell(value: str) -> str | None:
        return None if value == "-" else f"{value}천원"

    # New report layout: 경영규모 table rows
    for line in text.splitlines():
        line = line.strip()
        row_match = re.match(r"^(20\d{2})-\d{2}-\d{2}\s+(.*)$", line)
        if not row_match:
            continue
        year = row_match.group(1)
        rest = row_match.group(2)
        tokens = tokenize_financial_row(rest)
        if len(tokens) != 6:
            continue
        _assets, _capital, _equity, sales, operating_profit, net_income = tokens
        summary[year] = {
            "sales": normalize_financial_cell(sales),
            "operating_profit": normalize_financial_cell(operating_profit),
            "net_income": normalize_financial_cell(net_income),
        }

    return summary


def parse_flowscore_report_text(raw_text: str, source_file: str | None = None) -> dict[str, Any]:
    compact = normalize_compact_text(raw_text)
    raw_text_length = len((raw_text or "").strip())
    compact_text_length = len(compact)

    company_match = find_first(
        [
            r"기업명\s*(.*?)\s*영문기업명",
            r"신용평가리포트\s*(.*?)\s*사업자번호",
            r"AI기반중소기업동적신용평가리포트\s*(.*?)\s*사업자번호",
            r"\|\s*평가사유코드\s*(.*?)\s*\d{4}-\d{2}-\d{2}",
            r"^(.*?)\s+\d{3}-\d{2}-\d{5}\s+[가-힣A-Za-z]{2,20}",
        ],
        compact,
    )
    company_name = clean_company_name(company_match.group(1)) if company_match else None
    if not company_name:
        company_name = infer_company_name_from_source(source_file)

    biz_numbers = re.findall(r"(?<!\d)\d{3}-\d{2}-\d{5}(?!\d)", compact)
    masked_biz_numbers = re.findall(r"\b\d{3}-\*\*-\*+\b", compact)
    business_number = biz_numbers[0] if biz_numbers else (masked_biz_numbers[0] if masked_biz_numbers else None)

    grade_match = find_first(
        [
            r"기업신용등급\s*평가일자\s*:\s*[0-9.-]+\s*결산일자\s*:\s*[0-9.-]+\s*([A-Za-z]{1,3}[+-]?)",
            r"\b([A-Z]{1,3}[+-]?)\s*신용등급",
            r"신용등급\|\s*([A-Z]{1,3}[+-]?)\b",
        ],
        compact,
    )
    score_match = re.search(r"종합점수\s*([0-9.]+)\s*/\s*1,000", compact)
    pd_match = re.search(r"부도확률\s*\(PD\)\s*([0-9.]+)%", compact)
    discount_match = re.search(r"연간적용할인율\s*([0-9.]+)%", compact)
    monthly_limit_match = find_first(
        [
            r"월간\s*적정\s*신용한도\s*[:：]?\s*([0-9][0-9,]*원)",
            r"월간\s*적정\s*신용한도\s*[:：]?\s*([0-9.]+억원)",
            r"월간적정신용한도\s*([0-9][0-9,]*원)",
            r"월간적정신용한도\s*([0-9.]+억원)",
            r"추천\s*신용한도\s*[:：]?\s*([0-9][0-9,]*원)",
            r"추천\s*신용한도\s*[:：]?\s*([0-9.]+억원)",
            r"추천신용한도\s*([0-9][0-9,]*원)",
            r"추천신용한도\s*([0-9.]+억원)",
        ],
        raw_text,
    )
    if not monthly_limit_match:
        monthly_limit_match = find_first(
            [
                r"월간적정신용한도\s*([0-9][0-9,]*원)",
                r"월간적정신용한도\s*([0-9.]+억원)",
                r"추천신용한도\s*([0-9][0-9,]*원)",
                r"추천신용한도\s*([0-9.]+억원)",
            ],
            compact,
        )
    eval_date_match = re.search(r"평가일(?:자)?\s*:\s*([0-9.-]+)", compact)
    if not eval_date_match:
        eval_date_match = re.search(r"평가일(?:자)?\s*([0-9.-]+)", compact)
    incorporated_match = re.search(r"설립일(?:자)?\s*:\s*([0-9.-]+)", compact)
    if not incorporated_match:
        incorporated_match = re.search(r"설립일(?:자)?\s*([0-9.-]+)", compact)

    representative_match = find_first(
        [
            r"대표자명\s*([가-힣A-Za-z]{2,20})\s*(?:기업유형|설립일(?:자)?|기업규모|전화번호)",
            r"대표자명\s*([가-힣A-Za-z]{2,20})",
            r"^(?:.*?\s+)?\d{3}-\d{2}-\d{5}\s+([가-힣A-Za-z]{2,20})\s*(?:요약|기업프로필)",
        ],
        compact,
    )

    dimension_patterns = {
        "financial_soundness": r"재무건전성\s*([0-9.]+)",
        "structural_stability": r"구조안(?:정성)?\s*([0-9.]+)",
        "operating_will": r"운영의지\s*([0-9.]+)",
        "transaction_soundness": r"거래건전성\s*([0-9.]+)",
        "communication_issue": r"통이슈\s*([0-9.]+)|소통이슈\s*([0-9.]+)",
    }
    dimension_scores: dict[str, float] = {}
    for key, pattern in dimension_patterns.items():
        match = re.search(pattern, compact)
        if match:
            value = next((group for group in match.groups() if group is not None), None)
            if value is not None:
                dimension_scores[key] = float(value)

    positives: list[dict[str, Any]] = []
    negatives: list[dict[str, Any]] = []
    for label in ["금융비용대매출액비율", "이자보상배율", "자기자본비율"]:
        match = re.search(rf"{label}.*?([0-9]+(?:\.[0-9]+)?)", compact)
        if match:
            positives.append({"factor": label, "value": float(match.group(1))})
    for label in ["총자본세전계속사업이익율", "순차입금의존도", "영업현금흐름대총차입금비율"]:
        match = re.search(rf"{label}.*?([0-9]+(?:\.[0-9]+)?)", compact)
        if match:
            negatives.append({"factor": label, "value": float(match.group(1))})

    financial_summary = parse_table_financial_summary(raw_text)

    limit_match = find_first(
        [
            r"추천\s*신용한도\s*([0-9.]+억원|[0-9][0-9,]*원).*?한도범위\s*[:：]?\s*([0-9.]+억원|[0-9][0-9,]*원)\s*[~\-]\s*([0-9.]+억원|[0-9][0-9,]*원).*?한도등급\s*([A-Z])",
            r"추천신용한도\s*([0-9.]+억원|[0-9][0-9,]*원).*?한도범위\s*[:：]?\s*([0-9.]+억원|[0-9][0-9,]*원)\s*[~\-]\s*([0-9.]+억원|[0-9][0-9,]*원).*?한도등급\s*([A-Z])",
        ],
        compact,
    )

    has_credit_metrics = bool(grade_match or score_match or pd_match or monthly_limit_match or financial_summary or limit_match)
    is_scan_like = compact_text_length < 30
    report_type = "flowscore_credit_report_pdf"
    if is_scan_like:
        report_type = "image_or_scan_pdf"
    elif not has_credit_metrics:
        report_type = "generic_company_pdf"

    readiness_issues: list[str] = []
    if is_scan_like:
        readiness_issues.append("PDF 텍스트 추출 실패(OCR 필요)")
    if not company_name:
        readiness_issues.append("회사명 자동 추출 보정 필요")
    if not business_number:
        readiness_issues.append("사업자번호 자동 추출 보정 필요")
    if not grade_match:
        readiness_issues.append("신용등급 자동 추출 보정 필요")
    if not financial_summary:
        readiness_issues.append("재무 요약표 추출 보정 필요")

    return {
        "report_type": report_type,
        "source_file": source_file,
        "parser_version": PARSER_VERSION,
        "raw_text_length": raw_text_length,
        "normalized_text_length": compact_text_length,
        "company_name": company_name,
        "short_name": infer_short_name(company_name),
        "business_number": business_number,
        "representative_name": clean_company_name(representative_match.group(1)) if representative_match else None,
        "evaluation_date": eval_date_match.group(1) if eval_date_match else None,
        "incorporated_date": incorporated_match.group(1) if incorporated_match else None,
        "credit_grade": grade_match.group(1).upper() if grade_match else None,
        "total_score": float(score_match.group(1)) if score_match else None,
        "score_scale": 1000,
        "pd_pct": float(pd_match.group(1)) if pd_match else None,
        "annual_discount_rate_pct": float(discount_match.group(1)) if discount_match else None,
        "monthly_credit_limit": monthly_limit_match.group(1) if monthly_limit_match else None,
        "dimension_scores": dimension_scores,
        "top_positive_factors": positives,
        "top_negative_factors": negatives,
        "financial_summary": financial_summary,
        "recommended_credit_limit": {
            "recommended": limit_match.group(1) if limit_match else None,
            "minimum": limit_match.group(2) if limit_match else None,
            "maximum": limit_match.group(3) if limit_match else None,
            "limit_grade": limit_match.group(4) if limit_match else None,
        },
        "learning_ready": {
            "usable": not is_scan_like,
            "confidence": "low" if is_scan_like else ("medium-high" if len(readiness_issues) <= 1 else "medium"),
            "issues": readiness_issues,
        },
        "normalized_excerpt": compact[:1200],
    }


def parse_flowscore_report_pdf(raw_bytes: bytes, source_file: str | None = None) -> dict[str, Any]:
    return parse_flowscore_report_text(extract_pdf_text(raw_bytes), source_file=source_file)


def dump_json(data: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Parse FlowScore credit report PDF into normalized JSON.")
    parser.add_argument("pdf_path", help="Path to FlowScore report PDF")
    parser.add_argument("--out", help="Optional output JSON path")
    args = parser.parse_args()

    pdf_path = Path(args.pdf_path)
    parsed = parse_flowscore_report_pdf(pdf_path.read_bytes(), source_file=pdf_path.name)
    if args.out:
        dump_json(parsed, Path(args.out))
    print(json.dumps(parsed, ensure_ascii=False, indent=2))
