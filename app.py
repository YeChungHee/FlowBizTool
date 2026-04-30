from __future__ import annotations

import hashlib
import json
import os
import re
import unicodedata
from datetime import date, datetime
from html import unescape
from io import BytesIO
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pypdf import PdfReader

from engine import (
    FRAMEWORK_PATH,
    load_active_framework,
    get_active_framework_meta,
    build_web_context,
    compute_margin_result,
    evaluate_flowpay_underwriting,
    load_json,
    score_band_multiplier,
)
from report_extractors import parse_flowscore_report_pdf


BASE_DIR = Path(__file__).resolve().parent
WEB_DIR = BASE_DIR / "web"
DATA_DIR = BASE_DIR / "data"
OUTPUTS_DIR = BASE_DIR / "outputs"
LIVE_LEARNING_REGISTRY_PATH = DATA_DIR / "bizaipro_learning_registry.json"
DOWNLOADS_DIR = Path.home() / "Downloads"
NOTION_API_BASE = "https://api.notion.com/v1"
NOTION_API_VERSION = "2022-06-28"
NOTION_REPORTS_DB_ID = "20a16c59d686800c884cebb7816829ea"  # 플로우페이_보고서 관리

# 자동조회 보고서 유형 → Notion select 값 매핑
_NOTION_REPORT_TYPE_LABEL: dict[str, str] = {
    "consultation": "상담보고서",
    "meeting": "미팅보고서",
    "internal_review": "심사보고서",
}

ENGINE_PRESETS = {
    "latest": {
        "key": "latest",
        "label": "최신 엔진 v.local.learning",
        "engine_version": "v.local.learning",
        "description": "업로드 자료와 Notion 자동조회 결과를 즉시 반영하는 실시간 학습 기준",
    },
    "previous": {
        "key": "previous",
        "label": "업데이트 전 엔진 v.1.0.00",
        "engine_version": "v.1.0.00",
        "description": "재무 필터와 액션을 더 보수적으로 보던 이전 기준",
    },
    "base": {
        "key": "base",
        "label": "기본 KCNC 샘플",
        "engine_version": "base",
        "description": "페이지 초기 샘플 기준",
    },
}

app = FastAPI(title="BizAiPro Web API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def normalize_space(value: str | None) -> str:
    return re.sub(r"\s+", " ", (value or "")).strip()


def strip_tags(value: str) -> str:
    no_script = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", value, flags=re.I | re.S)
    no_tags = re.sub(r"<[^>]+>", " ", no_script)
    return normalize_space(unescape(no_tags))


def match_first(patterns: list[str], value: str) -> str | None:
    for pattern in patterns:
        match = re.search(pattern, value, re.I | re.S)
        if match:
            return normalize_space(match.group(1))
    return None


def fetch_page_snapshot(url: str | None) -> dict[str, str]:
    if not url:
        return {}
    response = requests.get(
        url,
        timeout=15,
        headers={"User-Agent": "Mozilla/5.0 (BizAiPro/1.0)"},
    )
    response.raise_for_status()
    html = response.text
    body_text = strip_tags(html)
    title = match_first([r"<title[^>]*>(.*?)</title>"], html) or ""
    og_title = match_first(
        [
            r'property=["\']og:title["\']\s+content=["\'](.*?)["\']',
            r'content=["\'](.*?)["\']\s+property=["\']og:title["\']',
        ],
        html,
    ) or ""
    description = match_first(
        [
            r'name=["\']description["\']\s+content=["\'](.*?)["\']',
            r'content=["\'](.*?)["\']\s+name=["\']description["\']',
        ],
        html,
    ) or ""
    h1 = match_first([r"<h1[^>]*>(.*?)</h1>"], html) or ""

    return {
        "url": url,
        "title": strip_tags(title),
        "og_title": strip_tags(og_title),
        "description": strip_tags(description),
        "h1": strip_tags(h1),
        "body": body_text[:4000],
    }


def safe_fetch_page_snapshot(url: str | None) -> dict[str, str]:
    try:
        return fetch_page_snapshot(url)
    except Exception:
        return {"url": url or "", "title": "", "og_title": "", "description": "", "h1": "", "body": ""}


def extract_notion_page_id(url: str | None) -> str | None:
    if not url:
        return None
    match = re.search(r"([0-9a-f]{32})", url.replace("-", ""), re.I)
    if match:
        return match.group(1).lower()
    return None


def is_notion_url(url: str | None) -> bool:
    if not url:
        return False
    parsed = urlparse(url)
    return "notion.so" in parsed.netloc or "notion.site" in parsed.netloc


def get_notion_public_access_role(page_id: str | None) -> str | None:
    if not page_id:
        return None
    try:
        response = requests.post(
            "https://www.notion.so/api/v3/getPublicPageData",
            json={"blockId": page_id},
            timeout=15,
            headers={
                "User-Agent": "Mozilla/5.0 (BizAiPro/1.0)",
                "Content-Type": "application/json",
            },
        )
        response.raise_for_status()
        payload = response.json()
        return payload.get("publicAccessRole")
    except Exception:
        return None


def fetch_notion_public_page_payload(page_id: str | None) -> dict[str, Any]:
    if not page_id:
        return {}
    try:
        response = requests.post(
            "https://www.notion.so/api/v3/getPublicPageData",
            json={"blockId": page_id},
            timeout=15,
            headers={
                "User-Agent": "Mozilla/5.0 (BizAiPro/1.0)",
                "Content-Type": "application/json",
            },
        )
        response.raise_for_status()
        payload = response.json()
        return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}


def get_notion_api_token() -> str | None:
    for key in ("NOTION_API_TOKEN", "NOTION_TOKEN"):
        value = os.getenv(key)
        if value:
            return value.strip()
    local_keys_path = DATA_DIR / "api_keys.local.json"
    if local_keys_path.exists():
        try:
            payload = json.loads(local_keys_path.read_text(encoding="utf-8"))
        except Exception:
            payload = {}
        for key in ("NOTION_API_TOKEN", "NOTION_TOKEN", "notion_api_token", "notion_token"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    return None


def notion_headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_API_VERSION,
        "Content-Type": "application/json",
        "User-Agent": "BizAiPro/1.0",
    }


def notion_api_get(path: str, token: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    response = requests.get(
        f"{NOTION_API_BASE}{path}",
        params=params or {},
        timeout=20,
        headers=notion_headers(token),
    )
    response.raise_for_status()
    payload = response.json()
    return payload if isinstance(payload, dict) else {}


def extract_notion_rich_text_text(value: Any) -> str:
    if not isinstance(value, list):
        return ""
    parts: list[str] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        text = normalize_space(item.get("plain_text") or "")
        if not text:
            text = normalize_space(
                ((item.get("text") or {}).get("content") if isinstance(item.get("text"), dict) else "")
                or item.get("href")
                or ""
            )
        if text:
            parts.append(text)
    return normalize_space(" ".join(parts))


def extract_text_from_public_record_map(payload: dict[str, Any], page_id: str | None = None) -> str:
    record_map = payload.get("recordMap") if isinstance(payload, dict) else None
    blocks = (record_map or {}).get("block") if isinstance(record_map, dict) else None
    if not isinstance(blocks, dict):
        return ""

    ordered_blocks: list[tuple[int, dict[str, Any]]] = []
    if page_id and page_id in blocks:
        ordered_blocks.append((0, blocks[page_id]))
    for index, (_, wrapper) in enumerate(blocks.items(), start=1):
        if page_id and _ == page_id:
            continue
        ordered_blocks.append((index, wrapper))

    texts: list[str] = []
    for _, wrapper in sorted(ordered_blocks, key=lambda item: item[0]):
        value = wrapper.get("value") if isinstance(wrapper, dict) else None
        if not isinstance(value, dict):
            continue
        block_type = value.get("type")
        properties = value.get("properties") or {}
        title = extract_notion_rich_text_text(properties.get("title"))
        if title:
            texts.append(title)
            continue
        if block_type == "table_row":
            cells = properties.get("cells") or []
            cell_text = " | ".join(extract_notion_rich_text_text(cell) for cell in cells if extract_notion_rich_text_text(cell))
            if cell_text:
                texts.append(cell_text)
        elif block_type == "page":
            page_title = extract_notion_rich_text_text(properties.get("title"))
            if page_title:
                texts.append(page_title)
    return normalize_space("\n".join(texts))


def extract_title_from_notion_page_object(page: dict[str, Any]) -> str:
    properties = page.get("properties")
    if not isinstance(properties, dict):
        return ""
    for prop in properties.values():
        if not isinstance(prop, dict):
            continue
        if prop.get("type") == "title":
            return extract_notion_rich_text_text(prop.get("title"))
    return ""


def extract_text_from_notion_page_properties(page: dict[str, Any]) -> str:
    properties = page.get("properties")
    if not isinstance(properties, dict):
        return ""

    lines: list[str] = []
    for name, prop in properties.items():
        if not isinstance(prop, dict):
            continue
        prop_type = prop.get("type")
        value = ""
        if prop_type == "rich_text":
            value = extract_notion_rich_text_text(prop.get("rich_text"))
        elif prop_type == "title":
            value = extract_notion_rich_text_text(prop.get("title"))
        elif prop_type == "select":
            select = prop.get("select") or {}
            value = normalize_space(select.get("name") or "")
        elif prop_type == "status":
            status = prop.get("status") or {}
            value = normalize_space(status.get("name") or "")
        elif prop_type == "date":
            date = prop.get("date") or {}
            value = normalize_space(date.get("start") or "")
        elif prop_type == "people":
            people = prop.get("people") or []
            names = [normalize_space(person.get("name") or "") for person in people if isinstance(person, dict)]
            value = ", ".join([n for n in names if n])
        elif prop_type == "multi_select":
            items = prop.get("multi_select") or []
            names = [normalize_space(item.get("name") or "") for item in items if isinstance(item, dict)]
            value = ", ".join([n for n in names if n])

        value = normalize_space(value)
        if value:
            lines.append(f"{name}: {value}")

    return normalize_space("\n".join(lines))


def extract_text_from_notion_block(block: dict[str, Any]) -> str:
    if not isinstance(block, dict):
        return ""
    block_type = block.get("type")
    if not isinstance(block_type, str):
        return ""
    block_value = block.get(block_type)
    if not isinstance(block_value, dict):
        return ""
    if "rich_text" in block_value:
        return extract_notion_rich_text_text(block_value.get("rich_text"))
    if "title" in block_value:
        return extract_notion_rich_text_text(block_value.get("title"))
    if block_type == "child_page":
        return normalize_space(block_value.get("title") or "")
    if block_type == "table_row":
        cells = block_value.get("cells") or []
        return normalize_space(" | ".join(extract_notion_rich_text_text(cell) for cell in cells if extract_notion_rich_text_text(cell)))
    return ""


def fetch_notion_text_via_api(page_id: str, token: str, max_blocks: int = 200) -> tuple[str, str]:
    """Notion 페이지 텍스트 추출.

    DB 페이지(상담/심사/미팅보고서 등)는 내용이 속성(property) 필드에,
    일반 페이지는 블록(block)에 저장되어 있으므로 두 경로를 항상 모두 추출해 합산한다.
    - property_text : 제목·rich_text·select·status·date 등 DB 속성값
    - block_text    : 본문 블록 재귀 탐색 결과
    최종 반환값은 속성 텍스트를 먼저, 블록 텍스트를 뒤에 결합한다.
    """
    page = notion_api_get(f"/pages/{page_id}", token)
    title = extract_title_from_notion_page_object(page)
    property_text = extract_text_from_notion_page_properties(page)

    queue: list[str] = [page_id]
    visited: set[str] = set()
    block_texts: list[str] = []
    processed = 0

    while queue and processed < max_blocks:
        block_id = queue.pop(0)
        if block_id in visited:
            continue
        visited.add(block_id)
        next_cursor: str | None = None
        while True:
            params: dict[str, Any] = {"page_size": 100}
            if next_cursor:
                params["start_cursor"] = next_cursor
            payload = notion_api_get(f"/blocks/{block_id}/children", token, params=params)
            results = payload.get("results") or []
            for block in results:
                if not isinstance(block, dict):
                    continue
                processed += 1
                text = extract_text_from_notion_block(block)
                if text:
                    block_texts.append(text)
                if block.get("has_children") and block.get("id"):
                    queue.append(str(block["id"]))
                if processed >= max_blocks:
                    break
            if processed >= max_blocks or not payload.get("has_more"):
                break
            next_cursor = payload.get("next_cursor")

    # 속성 텍스트 + 블록 텍스트 항상 합산 (어느 한쪽만 있어도 누락 없이 반환)
    parts = [p for p in [property_text, normalize_space("\n".join(block_texts))] if p]
    return normalize_space("\n".join(parts)), title


def snapshot_has_meaningful_text(snapshot: dict[str, str]) -> bool:
    body = normalize_space(snapshot.get("body") or "")
    title = normalize_space(snapshot.get("title") or snapshot.get("og_title") or "")
    description = normalize_space(snapshot.get("description") or "")
    if not body:
        return False
    generic_markers = [
        "A collaborative AI workspace",
        "JavaScript must be enabled in order to use Notion",
        "Please enable JavaScript to continue.",
    ]
    if any(marker in body for marker in generic_markers):
        return False
    if any(marker in description for marker in generic_markers):
        return False
    if title.lower() == "notion" and len(body) < 160:
        return False
    return True


def sentence_split(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?다])\s+|\n+", text or "")
    return [normalize_space(part) for part in parts if normalize_space(part)]


# ── Notion 자동조회 헬퍼 (FBU-VAL-0010 확정 규칙 적용) ────────────────────

def _normalize_biz_num(biz_num: str | None) -> str:
    """사업자번호 정규화: 하이픈·공백 제거 후 숫자만 반환."""
    return re.sub(r"[^0-9]", "", biz_num or "")


def _notion_title_company_name(props: dict[str, Any]) -> str:
    """Notion 제목 property에서 회사명 파싱.

    예: '심사보고서 : 해남참농가' → '해남참농가'
    콜론이 없으면 제목 전체를 반환.
    """
    items = (
        (props.get("제목") or props.get("Name") or {}).get("title") or []
    )
    raw = "".join(item.get("plain_text", "") for item in items).strip()
    if ":" in raw:
        return raw.split(":", 1)[1].strip()
    return raw


def _notion_query_report_db(
    token: str,
    report_type_label: str,
    page_size: int = 50,
) -> list[dict[str, Any]]:
    """Notion 보고서 DB를 보고서 유형으로 필터링해 조회한다.

    Raises:
        PermissionError: HTTP 401/403 권한 오류 시.
        Exception: 그 외 네트워크·파싱 오류 시.
    """
    payload: dict[str, Any] = {
        "filter": {
            "property": "보고서 유형",
            "select": {"equals": report_type_label},
        },
        "sorts": [{"property": "상담(실사)일", "direction": "descending"}],
        "page_size": page_size,
    }
    try:
        resp = requests.post(
            f"{NOTION_API_BASE}/databases/{NOTION_REPORTS_DB_ID}/query",
            json=payload,
            headers=notion_headers(token),
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json().get("results") or []
    except requests.HTTPError as exc:
        status_code = exc.response.status_code if exc.response is not None else 0
        if status_code in (401, 403):
            raise PermissionError("db_permission_error") from exc
        raise


def _match_notion_page(
    pages: list[dict[str, Any]],
    company_name: str,
    business_number: str | None,
) -> tuple[str | None, list[dict[str, Any]]]:
    """페이지 목록에서 회사명·사업자번호로 최적 1건을 찾는다.

    매칭 우선순위 (FBU-VAL-0010):
      1. 사업자번호 exact match (하이픈 제거 후)
      2. 회사명 exact match (canonical_company_token 정규화 후)
      3. 회사명 contains fallback

    Returns:
        (page_id, [])           - 명확히 1건 매칭
        (None, candidates)      - 복수 매칭 → ambiguous
        (None, [])              - 매칭 없음 → not_found
    """
    norm_biz = _normalize_biz_num(business_number)
    clean_name = canonical_company_token(company_name or "")

    # 1순위: 사업자번호 exact
    if norm_biz:
        for page in pages:
            props = page.get("properties") or {}
            biz_prop = (props.get("사업자번호") or {}).get("rich_text") or []
            page_biz = _normalize_biz_num(
                "".join(item.get("plain_text", "") for item in biz_prop).strip()
            )
            if page_biz and page_biz == norm_biz:
                return page["id"], []

    # 2순위: 회사명 exact
    exact_matches = [
        p for p in pages
        if canonical_company_token(_notion_title_company_name(p.get("properties") or {})) == clean_name
    ]
    if len(exact_matches) == 1:
        return exact_matches[0]["id"], []
    if len(exact_matches) > 1:
        return None, exact_matches

    # 3순위: 회사명 contains
    if clean_name:
        contains_matches = [
            p for p in pages
            if (lambda pc: clean_name in pc or pc in clean_name)(
                canonical_company_token(_notion_title_company_name(p.get("properties") or {}))
            )
        ]
        if len(contains_matches) == 1:
            return contains_matches[0]["id"], []
        if len(contains_matches) > 1:
            return None, contains_matches

    return None, []


def notion_lookup_one(
    report_type: str,
    company_name: str,
    business_number: str | None,
    token: str,
) -> dict[str, Any]:
    """단일 보고서 유형에 대해 Notion DB를 조회하고 즉시 파싱한다.

    FBU-VAL-0010 §6 규칙:
      - found_and_parsed만 state_patch에 URL·summary 포함.
      - found_but_unreadable·ambiguous는 page_url을 metadata에만 보존.

    Returns 구조:
        status: 6종 enum
        page_id, page_url, title: metadata (found_and_parsed 아니어도 보존)
        issues: 오류·경고 메시지
        state_patch: found_and_parsed 시에만 실질 내용 포함
        candidates: ambiguous 시 후보 목록
    """
    report_type_label = _NOTION_REPORT_TYPE_LABEL.get(report_type, "상담보고서")
    result: dict[str, Any] = {
        "status": "not_found",
        "report_family": "consultation" if report_type in ("consultation", "meeting") else "internal_review",
        "subtype": report_type,
        "page_id": None,
        "page_url": None,
        "title": None,
        "issues": [],
        "state_patch": {},
    }

    # ── DB 조회 ──────────────────────────────────────────────────────────
    try:
        pages = _notion_query_report_db(token, report_type_label)
    except PermissionError:
        result["status"] = "db_permission_error"
        result["issues"] = [f"Notion DB 접근 권한 없음 ({report_type_label})"]
        return result
    except Exception as exc:
        result["status"] = "db_permission_error"
        result["issues"] = [f"Notion DB 쿼리 오류: {exc}"]
        return result

    # ── 매칭 ─────────────────────────────────────────────────────────────
    page_id, candidates = _match_notion_page(pages, company_name, business_number)

    if candidates:
        result["status"] = "ambiguous"
        result["issues"] = [f"동명 업체 {len(candidates)}건 발견 — 수동 선택 필요"]
        result["candidates"] = [
            {
                "page_id": p["id"],
                "page_url": f"https://www.notion.so/{p['id'].replace('-', '')}",
                "title": _notion_title_company_name(p.get("properties") or {}),
            }
            for p in candidates
        ]
        return result

    if not page_id:
        return result  # not_found

    # ── found → 즉시 파싱 ─────────────────────────────────────────────────
    page_url = f"https://www.notion.so/{page_id.replace('-', '')}"
    # metadata는 found_and_parsed 여부와 무관하게 항상 보존 (FBU-VAL-0010 §6 규칙 3)
    result["page_id"] = page_id
    result["page_url"] = page_url
    matched_page = next((p for p in pages if p["id"] == page_id), None)
    if matched_page:
        result["title"] = _notion_title_company_name(matched_page.get("properties") or {})

    try:
        parsed = parse_consulting_report_url(
            page_url,
            fallback_company_name=company_name or None,
            fallback_business_number=business_number or None,
            source_label=report_type_label,
        )
        has_evidence = bool(normalize_space(parsed.get("summary") or ""))
        if has_evidence:
            result["status"] = "found_and_parsed"
            if report_type == "internal_review":
                result["state_patch"] = apply_internal_review_enrichment({}, parsed)
            else:
                prefix = "consulting" if report_type == "consultation" else "meeting"
                label = "상담보고서" if report_type == "consultation" else "미팅보고서"
                result["state_patch"] = apply_consulting_enrichment(
                    {}, parsed, state_prefix=prefix, source_display_label=label
                )
        else:
            result["status"] = "found_but_unreadable"
            result["issues"] = parsed.get("issues") or ["본문을 추출하지 못했습니다."]
    except Exception as exc:
        result["status"] = "found_but_unreadable"
        result["issues"] = [f"페이지 파싱 오류: {exc}"]

    return result


def notion_auto_lookup(
    company_name: str,
    business_number: str | None,
) -> dict[str, Any]:
    """상담·미팅·심사보고서 3종을 순차 조회하고 통합 결과를 반환한다.

    token_missing 시 전체 스킵하고 requires_user_decision=True 반환.
    """
    token = get_notion_api_token()
    if not token:
        return {
            "company_name_used": company_name,
            "business_number_used": business_number,
            "token_status": "missing",
            "consultation": {"status": "token_missing", "state_patch": {}, "issues": ["NOTION_API_TOKEN 미설정"]},
            "meeting": {"status": "token_missing", "state_patch": {}, "issues": ["NOTION_API_TOKEN 미설정"]},
            "internal_review": {"status": "token_missing", "state_patch": {}, "issues": ["NOTION_API_TOKEN 미설정"]},
            "missing_notion_reports": ["consultation", "meeting", "internal_review"],
            "requires_user_decision": True,
        }

    results: dict[str, Any] = {
        "company_name_used": company_name,
        "business_number_used": business_number,
        "token_status": "ok",
    }
    for rtype in ("consultation", "meeting", "internal_review"):
        results[rtype] = notion_lookup_one(rtype, company_name, business_number, token)

    missing = [
        rtype for rtype in ("consultation", "meeting", "internal_review")
        if results[rtype].get("status") != "found_and_parsed"
    ]
    results["missing_notion_reports"] = missing
    results["requires_user_decision"] = len(missing) > 0
    return results


def build_notion_lookup_state_patch(lookup_result: dict[str, Any]) -> dict[str, Any]:
    """found_and_parsed 항목의 state_patch만 병합해 반환한다.

    FBU-VAL-0010 §6 규칙 1·2:
      - found_and_parsed만 primary URL 필드에 반영.
      - 나머지 status는 primary URL 빈값 (URL은 notion_lookup metadata에만 보존).
    """
    merged: dict[str, Any] = {}
    url_field_map = {
        "consultation": "consultingReportUrl",
        "meeting": "meetingReportUrl",
        "internal_review": "internalReviewUrl",
    }
    for rtype, url_field in url_field_map.items():
        entry = lookup_result.get(rtype) or {}
        if entry.get("status") == "found_and_parsed":
            merged.update(entry.get("state_patch") or {})
            merged[url_field] = entry.get("page_url") or ""
        # else: url_field는 빈값 유지 (primary URL 필드에 미반영)

    # notionLookupStatus state 필드 주입
    merged["notionLookupStatus"] = {
        rtype: (lookup_result.get(rtype) or {}).get("status", "not_found")
        for rtype in ("consultation", "meeting", "internal_review")
    }
    missing = lookup_result.get("missing_notion_reports") or []
    merged["missingNotionReports"] = missing
    if missing:
        _label_map = {
            "consultation": "상담보고서",
            "meeting": "미팅보고서",
            "internal_review": "심사보고서",
        }
        merged["evaluationContinuationMode"] = "flowscore_only_or_partial"
        merged["conditionalEvaluationReason"] = (
            ", ".join(_label_map[r] for r in missing if r in _label_map) + " 미확인"
        )
    return merged


def find_sentence_by_keywords(text: str, keywords: list[str]) -> str | None:
    for sentence in sentence_split(text):
        if len(sentence) > 180:
            continue
        if any(keyword in sentence for keyword in keywords):
            return sentence
    return None


def clean_extracted_phrase(value: str) -> str | None:
    value = normalize_space(value)
    if not value:
        return None
    value = re.sub(r"^[\-–—:：]+", "", value).strip()
    value = re.sub(r"(입니다|입니다\.|입니다만|임)$", "", value).strip()
    value = re.sub(r"^(은|는)\s+", "", value).strip()
    value = re.sub(r"\s*(?:이며|이고|이고,|이고\.|으로|로)\s.*$", "", value).strip()
    value = re.sub(r"\s*(?:은|는)\s.*$", "", value).strip()
    value = value.strip("()[]{} ")
    if not value or len(value) < 2:
        return None
    return value


def extract_named_field(
    text: str,
    labels: list[str],
    max_len: int = 80,
    *,
    require_delimiter: bool = True,
) -> str | None:
    delimiter_pattern = r"\s*[:：]\s*" if require_delimiter else r"\s*[:：]?\s*"
    for label in labels:
        match = re.search(
            rf"{label}{delimiter_pattern}([^\n\r|]{{2,{max_len}}})",
            text,
            re.I,
        )
        if match:
            value = clean_extracted_phrase(match.group(1)[:max_len])
            if value:
                return value
    return None


def extract_company_name_from_text(text: str) -> str | None:
    explicit = extract_named_field(
        text,
        ["기업명", "업체명", "회사명", "신청업체", "고객사"],
        max_len=100,
        require_delimiter=True,
    )
    if explicit:
        return explicit
    return None


def extract_supplier_name(text: str) -> str | None:
    explicit = extract_named_field(
        text,
        ["매입처", "공급처", "제조 공급처", "OEM 공급처", "공급사"],
        max_len=120,
        require_delimiter=True,
    )
    if explicit:
        return explicit

    manufacturer_match = re.search(
        r"중국\s*제조사\s*['\"“”‘’]?\s*([A-Z][A-Z0-9\-]{1,20})",
        text,
        re.I,
    )
    if manufacturer_match:
        value = clean_extracted_phrase(manufacturer_match.group(1))
        if value:
            return value
    return None


def extract_buyer_name(text: str) -> str | None:
    explicit = extract_named_field(
        text,
        ["매출처", "원청", "플랫폼"],
        max_len=120,
        require_delimiter=True,
    )
    if explicit:
        return explicit

    buyer_patterns = [
        r"(KT&G)[^\n]{0,30}매출처",
        r"(대기업/공공기관)[^\n]{0,30}납품",
        r"(공공기관\s*및\s*대기업)[^\n]{0,30}납품",
        r"(글로벌\s*다국적\s*기업)[^\n]{0,30}매출처",
    ]
    for pattern in buyer_patterns:
        match = re.search(pattern, text, re.I)
        if match:
            value = clean_extracted_phrase(match.group(1))
            if value:
                return value
    return None


def infer_tenor_from_text(text: str) -> dict[str, int | None]:
    range_month_match = re.search(
        r"(?:결제(?:유예)?기간|유예기간|결제기간|정산주기|회수주기|사후\s*결제)[^0-9]{0,30}(\d{1,2})\s*[~\-]\s*(\d{1,2})\s*개월",
        text,
        re.I,
    )
    if range_month_match:
        first = int(range_month_match.group(1))
        second = int(range_month_match.group(2))
        months = max(first, second)
        return {"months": months, "days": months * 30}

    month_match = re.search(
        r"(?:결제(?:유예)?기간|유예기간|결제기간|정산주기|회수주기)[^0-9]{0,12}(\d{1,2})\s*개월",
        text,
        re.I,
    )
    if month_match:
        months = int(month_match.group(1))
        return {"months": months, "days": months * 30}

    day_match = re.search(
        r"(?:결제(?:유예)?기간|유예기간|결제기간|정산주기|회수주기)[^0-9]{0,12}(\d{1,3})\s*일",
        text,
        re.I,
    )
    if day_match:
        days = int(day_match.group(1))
        months = max(1, round(days / 30))
        return {"months": months, "days": days}

    return {"months": None, "days": None}


def parse_supporting_text_block(
    text: str,
    *,
    source_label: str,
    fallback_company_name: str | None = None,
    fallback_business_number: str | None = None,
    fallback_representative_name: str | None = None,
    inaccessible_reason: str | None = None,
) -> dict[str, Any]:
    company_name = fallback_company_name or extract_company_name_from_text(text)
    business_number = (
        match_first([r"(\d{3}-\d{2}-\d{5})"], text)
        or fallback_business_number
    )
    representative_name = (
        extract_named_field(text, ["대표자", "대표", "실경영자"], require_delimiter=True)
        or fallback_representative_name
    )
    supplier = extract_supplier_name(text)
    buyer = extract_buyer_name(text)
    purpose = find_sentence_by_keywords(text, ["자금", "필요", "매입", "납품", "발주", "거래"])
    risk = find_sentence_by_keywords(text, ["리스크", "확인 필요", "주의", "문제", "체납", "연체"])
    tenor = infer_tenor_from_text(text)

    issues: list[str] = []
    if inaccessible_reason:
        issues.append(inaccessible_reason)
    if not normalize_space(text):
        issues.append(f"{source_label} 본문 추출이 비어 있습니다.")

    cross_checks: list[str] = []
    if company_name and fallback_company_name:
        if normalize_space(company_name).replace("(주)", "") == normalize_space(fallback_company_name).replace("(주)", ""):
            cross_checks.append(f"기업명은 리포트와 {source_label}가 일치합니다: {company_name}")
        else:
            cross_checks.append(f"기업명 불일치 가능성: 리포트 {fallback_company_name} / {source_label} {company_name}")
    if representative_name and fallback_representative_name:
        if normalize_space(representative_name) == normalize_space(fallback_representative_name):
            cross_checks.append(f"대표자명은 일치합니다: {representative_name}")
        else:
            cross_checks.append(
                f"대표자명 불일치 가능성: 리포트 {fallback_representative_name} / {source_label} {representative_name}"
            )
    if business_number and fallback_business_number:
        if business_number == fallback_business_number:
            cross_checks.append(f"사업자번호는 일치합니다: {business_number}")
        else:
            cross_checks.append(
                f"사업자번호 불일치 가능성: 리포트 {fallback_business_number} / {source_label} {business_number}"
            )

    summary_parts: list[str] = []
    if supplier:
        summary_parts.append(f"매입처는 {supplier}로 읽힙니다.")
    if buyer:
        summary_parts.append(f"매출처는 {buyer}로 읽힙니다.")
    if tenor["days"]:
        summary_parts.append(f"{source_label} 기준 결제유예기간은 {tenor['days']}일로 읽힙니다.")
    if purpose:
        summary_parts.append(purpose)
    if risk:
        summary_parts.append(f"리스크 메모: {risk}")
    if not summary_parts and issues:
        summary_parts.append(f"{source_label}는 연결됐지만 본문을 자동 구조화하지 못했습니다.")

    return {
        "company_name": company_name,
        "business_number": business_number,
        "representative_name": representative_name,
        "supplier": supplier,
        "buyer": buyer,
        "requested_tenor_months": tenor["months"],
        "requested_tenor_days": tenor["days"],
        "purpose": purpose,
        "risk": risk,
        "summary": " ".join(summary_parts).strip(),
        "cross_checks": cross_checks,
        "issues": issues,
    }


def parse_consulting_report_url(
    url: str,
    fallback_company_name: str | None = None,
    fallback_business_number: str | None = None,
    fallback_representative_name: str | None = None,
    source_label: str = "상담보고서",
) -> dict[str, Any]:
    page_id = extract_notion_page_id(url)
    notion_url = is_notion_url(url)
    notion_api_token = get_notion_api_token() if notion_url else None
    notion_public_payload = fetch_notion_public_page_payload(page_id) if notion_url else {}
    notion_access_role = notion_public_payload.get("publicAccessRole") if notion_url else None
    snapshot = safe_fetch_page_snapshot(url)

    body_text = ""
    notion_read_method = "none"
    notion_read_error = ""
    notion_api_available = bool(notion_api_token)
    notion_api_used = False

    if notion_url and page_id and notion_api_token:
        notion_api_used = True
        try:
            api_body_text, api_title = fetch_notion_text_via_api(page_id, notion_api_token)
            body_text = api_body_text
            notion_read_method = "official_api"
            if api_title and not snapshot.get("title"):
                snapshot["title"] = api_title
        except requests.HTTPError as exc:
            status_code = exc.response.status_code if exc.response is not None else None
            if status_code in (401, 403):
                notion_read_error = f"Notion API 인증 또는 권한 문제로 {source_label} 본문을 읽지 못했습니다."
            elif status_code == 404:
                notion_read_error = (
                    f"Notion API 토큰은 연결됐지만 현재 {source_label} 페이지가 해당 integration에 공유되지 않아 본문을 읽지 못했습니다."
                )
            else:
                notion_read_error = f"Notion API 응답 오류로 {source_label} 본문을 읽지 못했습니다."
        except Exception:
            notion_read_error = f"Notion API 호출 중 오류로 {source_label} 본문을 읽지 못했습니다."

    if notion_url and not body_text:
        public_body_text = extract_text_from_public_record_map(notion_public_payload, page_id)
        if public_body_text:
            body_text = public_body_text
            notion_read_method = "public_page_data"

    if not body_text:
        html_body_text = snapshot.get("body", "")
        if snapshot_has_meaningful_text(snapshot):
            body_text = html_body_text
            notion_read_method = "html_snapshot"

    inaccessible_reason = None
    if notion_url and not body_text:
        if notion_read_error:
            inaccessible_reason = notion_read_error
        elif not notion_api_token:
            inaccessible_reason = (
                f"웹앱 백엔드에 Notion API 토큰이 없어 공개 링크 방식으로만 {source_label} 본문 읽기를 시도했지만 "
                "읽을 수 있는 텍스트를 추출하지 못했습니다."
            )
        else:
            inaccessible_reason = (
                f"현재 웹앱 백엔드에서 {source_label} Notion 본문을 읽지 못했습니다. "
                "공개 링크 또는 API 권한 상태를 확인해 주세요."
            )

    parsed = parse_supporting_text_block(
        body_text,
        source_label=source_label,
        fallback_company_name=fallback_company_name,
        fallback_business_number=fallback_business_number,
        fallback_representative_name=fallback_representative_name,
        inaccessible_reason=inaccessible_reason,
    )

    return {
        "url": url,
        "page_id": page_id,
        "notion_public_access_role": notion_access_role,
        "notion_api_available": notion_api_available,
        "notion_api_used": notion_api_used,
        "notion_read_method": notion_read_method,
        "notion_read_error": notion_read_error,
        "snapshot": snapshot,
        "body_text": body_text[:6000],
        **parsed,
    }


def apply_consulting_enrichment(
    state_patch: dict[str, Any],
    consulting_report: dict[str, Any],
    *,
    state_prefix: str = "consulting",
    source_display_label: str = "상담보고서",
) -> dict[str, Any]:
    next_patch = dict(state_patch)
    summary = consulting_report.get("summary")
    cross_checks = consulting_report.get("cross_checks") or []
    issues = consulting_report.get("issues") or []
    summary_key = f"{state_prefix}Summary"
    cross_checks_key = f"{state_prefix}CrossChecks"
    issues_key = f"{state_prefix}Issues"
    validation_key = f"{state_prefix}ValidationSummary"

    if consulting_report.get("company_name") and not next_patch.get("companyName"):
        next_patch["companyName"] = consulting_report["company_name"]
    if consulting_report.get("representative_name") and not next_patch.get("representativeName"):
        next_patch["representativeName"] = consulting_report["representative_name"]
    if consulting_report.get("business_number") and not next_patch.get("businessNumber"):
        next_patch["businessNumber"] = consulting_report["business_number"]
    if consulting_report.get("requested_tenor_months"):
        next_patch["requestedTenorMonths"] = consulting_report["requested_tenor_months"]
    if consulting_report.get("requested_tenor_days"):
        next_patch["requestedTenorDays"] = consulting_report["requested_tenor_days"]
    if consulting_report.get("supplier"):
        next_patch["supplierName"] = consulting_report["supplier"]
    if consulting_report.get("buyer"):
        next_patch["buyerName"] = consulting_report["buyer"]

    if summary:
        next_patch[summary_key] = summary
    if cross_checks:
        next_patch[cross_checks_key] = cross_checks
    if issues:
        next_patch[issues_key] = issues

    if consulting_report.get("supplier") or consulting_report.get("buyer"):
        checks = list(next_patch.get("checks") or [])
        if consulting_report.get("supplier"):
            checks.insert(0, f"{source_display_label} 매입처: {consulting_report['supplier']}")
        if consulting_report.get("buyer"):
            checks.insert(0, f"{source_display_label} 매출처: {consulting_report['buyer']}")
        next_patch["checks"] = checks[:5]

    summary_bits = []
    if summary:
        summary_bits.append(summary)
    if cross_checks:
        summary_bits.append(" ".join(cross_checks[:2]))
    if issues:
        summary_bits.append(" ".join(issues[:2]))
    if summary_bits:
        next_patch[validation_key] = " ".join(summary_bits).strip()

    return next_patch


def apply_internal_review_enrichment(state_patch: dict[str, Any], internal_review: dict[str, Any]) -> dict[str, Any]:
    next_patch = dict(state_patch)
    summary = internal_review.get("summary")
    cross_checks = internal_review.get("cross_checks") or []
    issues = internal_review.get("issues") or []

    if summary:
        next_patch["internalReviewSummary"] = summary
    if cross_checks:
        next_patch["internalReviewCrossChecks"] = cross_checks
    if issues:
        next_patch["internalReviewIssues"] = issues

    summary_bits = []
    if summary:
        summary_bits.append(summary)
    if cross_checks:
        summary_bits.append(" ".join(cross_checks[:2]))
    if issues:
        summary_bits.append(" ".join(issues[:2]))
    if summary_bits:
        next_patch["internalReviewValidationSummary"] = " ".join(summary_bits).strip()
    return next_patch


def apply_supporting_file_enrichment(state_patch: dict[str, Any], parsed_doc: dict[str, Any], field_prefix: str) -> dict[str, Any]:
    next_patch = dict(state_patch)
    summary = parsed_doc.get("summary")
    issues = parsed_doc.get("issues") or []
    cross_checks = parsed_doc.get("cross_checks") or []

    if summary:
        next_patch[f"{field_prefix}Summary"] = summary
    if issues:
        next_patch[f"{field_prefix}Issues"] = issues
    if cross_checks:
        next_patch[f"{field_prefix}CrossChecks"] = cross_checks

    if parsed_doc.get("requested_tenor_months"):
        next_patch["requestedTenorMonths"] = parsed_doc["requested_tenor_months"]
    if parsed_doc.get("requested_tenor_days"):
        next_patch["requestedTenorDays"] = parsed_doc["requested_tenor_days"]
    if parsed_doc.get("supplier"):
        next_patch["supplierName"] = parsed_doc["supplier"]
    if parsed_doc.get("buyer"):
        next_patch["buyerName"] = parsed_doc["buyer"]
    return next_patch


def apply_additional_info_enrichment(state_patch: dict[str, Any], parsed_extra: dict[str, Any]) -> dict[str, Any]:
    next_patch = dict(state_patch)
    summary = parsed_extra.get("summary")
    issues = parsed_extra.get("issues") or []
    if summary:
        next_patch["additionalInfoSummary"] = summary
    if issues:
        next_patch["additionalInfoIssues"] = issues
    if parsed_extra.get("requested_tenor_months"):
        next_patch["requestedTenorMonths"] = parsed_extra["requested_tenor_months"]
    if parsed_extra.get("requested_tenor_days"):
        next_patch["requestedTenorDays"] = parsed_extra["requested_tenor_days"]
    if parsed_extra.get("supplier"):
        next_patch["supplierName"] = parsed_extra["supplier"]
    if parsed_extra.get("buyer"):
        next_patch["buyerName"] = parsed_extra["buyer"]
    return next_patch


def extract_report_text(raw_bytes: bytes) -> str:
    try:
        reader = PdfReader(BytesIO(raw_bytes))
        pages = [page.extract_text() or "" for page in reader.pages[:3]]
        return normalize_space(" ".join(pages))
    except Exception:
        try:
            return normalize_space(raw_bytes.decode("utf-8"))
        except Exception:
            return ""


def parse_krw_text_to_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    text = str(value).strip()
    match = re.search(r"-?[\d,]+", text)
    if not match:
        return None
    numeric = int(match.group(0).replace(",", ""))
    if "천원" in text:
        return numeric * 1000
    if "억원" in text:
        return int(round(float(match.group(0).replace(",", "")) * 100_000_000))
    return numeric


def build_report_limit_from_financials(parsed_report: dict[str, Any]) -> int | None:
    financial_summary = parsed_report.get("financial_summary") or {}
    if not financial_summary:
        return None
    latest_year = sorted(financial_summary.keys())[-1]
    latest_values = financial_summary.get(latest_year, {})
    annual_sales_krw = parse_krw_text_to_int(latest_values.get("sales"))
    if not annual_sales_krw:
        return None
    # FlowPay 기본 한도 규칙: 연간 매출 / 12 * 70%
    return int(round(((annual_sales_krw / 12.0) * 0.7) / 1000.0) * 1000)


def normalize_limit_display_text(value: Any) -> str:
    parsed = parse_krw_text_to_int(value)
    if parsed is not None:
        return format_krw(parsed)
    if value in (None, ""):
        return "확인 필요"
    return str(value)


def apply_report_enrichment(state_patch: dict[str, Any], parsed_report: dict[str, Any]) -> dict[str, Any]:
    next_patch = dict(state_patch)
    report_type = parsed_report.get("report_type")
    company_name = parsed_report.get("company_name")
    short_name = parsed_report.get("short_name")
    representative_name = parsed_report.get("representative_name")
    business_number = parsed_report.get("business_number")
    monthly_credit_limit = parsed_report.get("monthly_credit_limit")
    recommended_limit = parsed_report.get("recommended_credit_limit", {}).get("recommended")
    derived_limit_krw = build_report_limit_from_financials(parsed_report)
    parsed_monthly_limit_krw = parse_krw_text_to_int(recommended_limit or monthly_credit_limit)
    base_monthly_limit_krw = parsed_monthly_limit_krw or derived_limit_krw
    base_monthly_limit_text = normalize_limit_display_text(base_monthly_limit_krw)
    grade = parsed_report.get("credit_grade")
    total_score = parsed_report.get("total_score")
    pd_pct = parsed_report.get("pd_pct")
    evaluation_date = parsed_report.get("evaluation_date")

    priority = None
    proposal_state = None
    estimated_margin = None
    if grade:
        if grade.startswith(("AAA", "AA", "A")):
            priority = "상"
            proposal_state = "거래 가능성 높음"
            estimated_margin = "약 5~6%대"
        elif grade.startswith("BBB"):
            priority = "중상"
            proposal_state = "추가 확인 필요"
            estimated_margin = "약 5~6%대"
        elif grade.startswith(("BB", "B")):
            priority = "중"
            proposal_state = "추가 확인 필요"
            estimated_margin = "약 6~8%대"
        else:
            priority = "낮음"
            proposal_state = "제안 비추천"
            estimated_margin = "보수 검토"

    if company_name:
        next_patch["companyName"] = company_name
    if short_name or company_name:
        next_patch["shortName"] = short_name or company_name.replace("(주)", "").strip()
    if representative_name:
        next_patch["representativeName"] = representative_name
    if business_number:
        next_patch["businessNumber"] = business_number
    if base_monthly_limit_krw:
        next_patch["reportMonthlyCreditLimit"] = base_monthly_limit_text
        next_patch["baseMonthlyLimitLabel"] = "기준 월간 적정 한도"
        next_patch["baseMonthlyLimitValue"] = base_monthly_limit_text
        next_patch["estimatedLimitLabel"] = "기준 월간 적정 한도"
        next_patch["estimatedLimitValue"] = base_monthly_limit_text
    if grade:
        next_patch["financialFilterSignal"] = grade
    else:
        next_patch["financialFilterSignal"] = "확인 필요"
    if total_score is not None:
        next_patch["reportTotalScore"] = f"{total_score:.1f} / 1,000"
    if pd_pct is not None:
        next_patch["reportPdPct"] = f"{pd_pct:.2f}%"
    if evaluation_date:
        next_patch["reportEvaluationDate"] = evaluation_date
    if parsed_report.get("incorporated_date"):
        next_patch["reportIncorporatedDate"] = parsed_report.get("incorporated_date")
    if parsed_report.get("report_type"):
        next_patch["reportType"] = parsed_report.get("report_type")
    if parsed_report.get("source_file"):
        next_patch["reportSourceFileName"] = parsed_report.get("source_file")
    if grade:
        next_patch["reportCreditGrade"] = grade

    financial_summary = parsed_report.get("financial_summary") or {}
    if financial_summary:
        next_patch["reportFinancialSummary"] = financial_summary
    if financial_summary:
        latest_year = sorted(financial_summary.keys())[-1]
        latest_values = financial_summary.get(latest_year, {})
        next_patch["recentRevenueLabel"] = f"{latest_year}년 매출액"
        next_patch["operatingProfitLabel"] = f"{latest_year}년 영업이익"
        next_patch["netIncomeLabel"] = f"{latest_year}년 당기순이익"
        next_patch["recentRevenueValue"] = latest_values.get("sales") or "확인 필요"
        next_patch["operatingProfitValue"] = latest_values.get("operating_profit") or "확인 필요"
        next_patch["netIncomeValue"] = latest_values.get("net_income") or "확인 필요"
        next_patch["recentRevenueYear"] = latest_year
        next_patch["operatingProfitYear"] = latest_year
    if priority:
        next_patch["proposalPriority"] = priority
    elif company_name:
        next_patch["proposalPriority"] = "중"
    if proposal_state:
        next_patch["currentProposalState"] = proposal_state
    elif company_name:
        next_patch["currentProposalState"] = "추가 확인 필요"
    if estimated_margin:
        next_patch["estimatedMarginValue"] = estimated_margin
    elif company_name:
        next_patch["estimatedMarginValue"] = "추가 확인 필요"
    if not base_monthly_limit_krw and company_name:
        next_patch["estimatedLimitValue"] = "추가 확인 필요"

    summary_parts = []
    if company_name:
        if report_type == "flowscore_credit_report_pdf":
            summary_parts.append(f"{company_name} FlowScore 리포트를 기준으로")
        elif report_type == "generic_company_pdf":
            summary_parts.append(f"{company_name} 일반 기업자료를 기준으로")
        else:
            summary_parts.append(f"{company_name} 업로드 자료를 기준으로")
    else:
        summary_parts.append("업로드한 자료를 기준으로")
    if grade:
        summary_parts.append(f"재무 필터 신호는 {grade}입니다.")
    if total_score is not None:
        summary_parts.append(f"종합점수는 {total_score:.1f} / 1,000입니다.")
    if pd_pct is not None:
        summary_parts.append(f"부도확률(PD)은 {pd_pct:.2f}%입니다.")
    if parsed_monthly_limit_krw:
        summary_parts.append(f"리포트 기준 월간 적정 신용한도는 {base_monthly_limit_text} 수준으로 읽힙니다.")
    elif derived_limit_krw:
        summary_parts.append(
            f"리포트 최신 매출액 기준 월간 적정 한도는 {format_krw(derived_limit_krw)} 수준으로 계산됩니다."
        )
    if evaluation_date:
        summary_parts.append(f"평가기준일은 {evaluation_date}입니다.")
    if report_type == "image_or_scan_pdf":
        summary_parts.append("현재 업로드 자료는 스캔 또는 이미지 PDF로 읽혀 OCR 없이 재무 추출이 불가능합니다.")
    elif not grade and company_name:
        summary_parts.append("현재 업로드 자료는 일반 기업소개 또는 추가 정보 자료로 읽혀 재무 필터는 추가 확인이 필요합니다.")
    next_patch["overviewSummary"] = " ".join(summary_parts)

    issues = parsed_report.get("learning_ready", {}).get("issues", [])
    next_patch["additionalInfoReportReady"] = "학습 가능" if not issues else "보정 후 학습 가능"
    if issues:
        next_patch["additionalInfoReportIssues"] = " / ".join(issues)
    return next_patch


def infer_exhibition_year(*values: str) -> int:
    merged = " ".join(values)
    match = re.search(r"\b(20\d{2})\b", merged)
    if match:
        return int(match.group(1))
    return date.today().year


def infer_exhibition_name(exhibition_snapshot: dict[str, str], fallback_year: int) -> str:
    candidates = [
        exhibition_snapshot.get("og_title", ""),
        exhibition_snapshot.get("title", ""),
        exhibition_snapshot.get("h1", ""),
        exhibition_snapshot.get("body", ""),
    ]
    merged = " ".join(candidates)
    if "SIMTOS" in merged.upper():
        return f"SIMTOS {fallback_year}"
    match = re.search(r"([A-Z][A-Z0-9&+\-]{2,}(?:\s+[A-Z0-9&+\-]{2,})?\s+20\d{2})", merged)
    if match:
        return normalize_space(match.group(1))
    match = re.search(r"([가-힣A-Za-z0-9&+\-]{2,}\s+20\d{2})", merged)
    if match:
        return normalize_space(match.group(1))
    domain = urlparse(exhibition_snapshot.get("url", "")).netloc.replace("www.", "")
    if domain:
        return f"{domain.split('.')[0].upper()} {fallback_year}"
    return f"전시회 {fallback_year}"


def infer_company_name(
    website_snapshot: dict[str, str],
    exhibition_snapshot: dict[str, str],
    report_text: str,
) -> str | None:
    website_title = normalize_space(website_snapshot.get("title", ""))
    if website_title and len(website_title) <= 40 and "http" not in website_title.lower():
        return website_title

    for source in [report_text, exhibition_snapshot.get("body", ""), exhibition_snapshot.get("title", "")]:
        match = re.search(r"([가-힣A-Za-z0-9()㈜\s]{2,40})\s+(\d{3}-\d{2}-\d{5})", source)
        if match:
            return normalize_space(match.group(1))

    domain = urlparse(website_snapshot.get("url", "")).netloc.replace("www.", "")
    if domain:
        return domain.split(".")[0].upper()
    return None


def infer_business_number(report_text: str) -> str | None:
    match = re.search(r"(\d{3}-\d{2}-\d{5})", report_text)
    return match.group(1) if match else None


def infer_representative_name(report_text: str) -> str | None:
    patterns = [
        r"대표자명\s+([가-힣A-Za-z]{2,20})",
        r"([가-힣A-Za-z]{2,20})\s+\d{3}-\d{2}-\d{5}",
    ]
    for pattern in patterns:
        match = re.search(pattern, report_text)
        if match:
            return normalize_space(match.group(1))
    return None


def infer_industry_item(website_snapshot: dict[str, str], report_text: str) -> str:
    merged = " ".join(
        [
            website_snapshot.get("description", ""),
            website_snapshot.get("body", ""),
            report_text,
        ]
    )
    if "CNC" in merged.upper():
        return "CNC 제어시스템 / 제조장비 제어"
    match = re.search(r"주요제품.*?([가-힣A-Za-z0-9/\-\s]{3,60})", report_text)
    if match:
        return normalize_space(match.group(1))
    return "확인 후 입력"


def infer_short_name(company_name: str | None) -> str | None:
    if not company_name:
        return None
    value = normalize_space(company_name)
    value = re.sub(r"^\(?주\)?|\(주\)|㈜", "", value)
    return normalize_space(value)


def canonical_company_token(value: Any) -> str:
    text = unicodedata.normalize("NFKC", normalize_space(value))
    text = re.sub(r"\.pdf$", "", text, flags=re.IGNORECASE)
    text = re.sub(r"[_\-\s]*리포트$", "", text)
    text = re.sub(r"^\(?주\)?|\(주\)|㈜", "", text)
    text = re.sub(r"[^0-9A-Za-z가-힣]+", "", text)
    return text.lower()


def load_dashboard_registry() -> dict[str, Any]:
    live_path = DATA_DIR / "bizaipro_learning_registry.json"
    if live_path.exists():
        try:
            registry = normalize_dashboard_registry(json.loads(live_path.read_text(encoding="utf-8")))
            return refresh_registry_cases_from_sources(registry, live_path)
        except Exception:
            pass
    return {"engine_name": "BizAiPro", "current_version": "v.1.0.00", "cases": [], "updates": []}


def load_live_learning_registry(path: Path = LIVE_LEARNING_REGISTRY_PATH) -> dict[str, Any]:
    if path.exists():
        try:
            registry = normalize_dashboard_registry(json.loads(path.read_text(encoding="utf-8")))
            return refresh_registry_cases_from_sources(registry, path)
        except Exception:
            pass
    return {"engine_name": "BizAiPro", "current_version": "v.1.0.00", "cases": [], "updates": []}


def save_live_learning_registry(registry: dict[str, Any], path: Path = LIVE_LEARNING_REGISTRY_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(registry, ensure_ascii=False, indent=2), encoding="utf-8")


# ── SourceQuality helpers (FBU-VAL-0006 Finding 1) ──────────────────────────
_NOTION_BLOCK_PATTERNS = ["권한", "본문", "읽기 실패", "접근 불가", "integration", "oops", "공개 링크", "API 없"]
_SCAN_REPORT_TYPES = {"image_or_scan_pdf", "generic_company_pdf"}


def _notion_body_accessible(issues: list | None, summary: str | None, for_update: bool = False) -> bool:
    """True when the Notion body was successfully extracted.

    for_update=False (evaluation):
      summary 있으면 True, 차단 이슈 있으면 False, 그 외 True (legacy 호환)
    for_update=True (update weight):
      summary/parsing evidence 필수 — URL만 있고 evidence 없으면 False.
      이 기준이 핵심: "자료 존재"와 "자료 품질" 분리 (FBU-VAL-0007 Finding 3).
    """
    if normalize_space(summary or ""):
        return True
    if for_update:
        # update 기준: 실제 파싱 evidence(summary) 없으면 False
        return False
    # evaluation 기준: 차단 이슈 없으면 legacy 호환 허용
    for issue in issues or []:
        if any(p in str(issue) for p in _NOTION_BLOCK_PATTERNS):
            return False
    return True


def source_quality_from_state(state: dict[str, Any]) -> dict[str, Any]:
    """Return a SourceQuality snapshot for display / logging.

    Fields per resource:
      present          – URL or filename exists in state
      usable_for_evaluation – can contribute to evaluation (partial text OK)
      usable_for_update     – must pass stricter gate (body extracted, no blocking issue)
    """
    # FlowScore PDF
    fs_file = bool(normalize_space(state.get("learningFlowScoreFileName")))
    report_type = state.get("reportType") or ""
    fs_scan = report_type in _SCAN_REPORT_TYPES
    # If reportType not yet set (legacy / not parsed yet) fall back to existence
    fs_usable = fs_file and (not report_type or not fs_scan)

    # Consulting (상담보고서: URL 또는 파일)
    has_consult_url = bool(
        normalize_space(state.get("consultingReportUrl"))
        or normalize_space(state.get("learningConsultingFileName"))
    )
    consult_issues = list(state.get("consultingIssues") or [])
    consult_summary = state.get("consultingSummary")
    consult_usable_eval = has_consult_url and _notion_body_accessible(consult_issues, consult_summary, for_update=False)
    consult_usable_update = has_consult_url and _notion_body_accessible(consult_issues, consult_summary, for_update=True)

    # Meeting (미팅보고서: URL 별도 추적 — 상담보고서와 독립 컴포넌트)
    has_meeting_url = bool(normalize_space(state.get("meetingReportUrl")))
    meeting_issues = list(state.get("meetingIssues") or [])
    meeting_summary = state.get("meetingSummary")
    meeting_usable_eval = has_meeting_url and _notion_body_accessible(meeting_issues, meeting_summary, for_update=False)
    meeting_usable_update = has_meeting_url and _notion_body_accessible(meeting_issues, meeting_summary, for_update=True)

    # Internal review
    has_internal_url = bool(normalize_space(state.get("internalReviewUrl")))
    internal_issues = list(state.get("internalReviewIssues") or [])
    internal_summary = state.get("internalReviewSummary") or state.get("internalReviewValidationSummary")
    internal_usable_eval = has_internal_url and _notion_body_accessible(internal_issues, internal_summary, for_update=False)
    internal_usable_update = has_internal_url and _notion_body_accessible(internal_issues, internal_summary, for_update=True)

    # Additional info
    extra = normalize_space(state.get("learningExtraInfo") or "")
    additional_usable = len(extra) >= 30

    return {
        "flow_score": {
            "present": fs_file,
            "usable_for_evaluation": fs_usable,
            "usable_for_update": fs_usable,
            "issues": ["스캔/OCR 필요 PDF — 재무 추출 불가"] if fs_scan else [],
        },
        "consultation": {
            "present": has_consult_url,
            "usable_for_evaluation": consult_usable_eval,
            "usable_for_update": consult_usable_update,
            "issues": (
                [i for i in consult_issues if any(p in str(i) for p in _NOTION_BLOCK_PATTERNS)]
                if not consult_usable_update else []
            ) + (["상담보고서 본문 미추출 — update 제외"] if consult_usable_eval and not consult_usable_update else []),
        },
        "meeting": {
            "present": has_meeting_url,
            "usable_for_evaluation": meeting_usable_eval,
            "usable_for_update": meeting_usable_update,
            "issues": (
                [i for i in meeting_issues if any(p in str(i) for p in _NOTION_BLOCK_PATTERNS)]
                if not meeting_usable_update else []
            ) + (["미팅보고서 본문 미추출 — update 제외"] if meeting_usable_eval and not meeting_usable_update else []),
        },
        "internal_review": {
            "present": has_internal_url,
            "usable_for_evaluation": internal_usable_eval,
            "usable_for_update": internal_usable_update,
            "issues": (
                [i for i in internal_issues if any(p in str(i) for p in _NOTION_BLOCK_PATTERNS)]
                if not internal_usable_update else []
            ) + (["내부심사 본문 미추출 — update 제외"] if internal_usable_eval and not internal_usable_update else []),
        },
        "additional": {
            "present": bool(extra),
            "usable_for_evaluation": additional_usable,
            "usable_for_update": additional_usable,
            "issues": ["추가정보 본문 30자 미만"] if extra and not additional_usable else [],
        },
    }


def learning_material_components(state: dict[str, Any]) -> dict[str, float]:
    """Compute per-source learning weights based on SourceQuality (FBU-VAL-0006 F1).

    Weights are set to 0.0 when the source is present but fails the quality gate
    (e.g. Notion body inaccessible, scan PDF, empty extra-info).  Downstream
    callers (learning_material_flags_from_components, learning_status_from_components)
    remain unchanged — they just see 0.0 instead of a positive weight.

    meeting_report (0.10) is counted independently from consultation_report.
    evaluation_ready requires flow_score AND (consultation OR meeting).
    """
    sq = source_quality_from_state(state)
    return {
        "flow_score_report": 0.35 if sq["flow_score"]["usable_for_update"] else 0.0,
        "consultation_report": 0.35 if sq["consultation"]["usable_for_update"] else 0.0,
        "meeting_report": 0.10 if sq["meeting"]["usable_for_update"] else 0.0,
        "internal_review": 0.15 if sq["internal_review"]["usable_for_update"] else 0.0,
        "additional_sources": 0.05 if sq["additional"]["usable_for_update"] else 0.0,
    }


def _source_quality_flags_from_state(state: dict[str, Any]) -> dict[str, bool]:
    """state에서 source별 usable_for_update 플래그를 추출 — sources dict에 저장하기 위한 헬퍼."""
    sq = source_quality_from_state(state)
    return {
        "flow_score_usable_for_update": sq["flow_score"]["usable_for_update"],
        "consultation_usable_for_update": sq["consultation"]["usable_for_update"],
        "meeting_usable_for_update": sq["meeting"]["usable_for_update"],
        "internal_review_usable_for_update": sq["internal_review"]["usable_for_update"],
        "additional_usable_for_update": sq["additional"]["usable_for_update"],
    }


def _merged_components_from_sources(merged_sources: dict[str, Any]) -> dict[str, float]:
    """merged_sources의 quality flags 기반으로 학습 가중치를 계산.

    quality flags(flow_score_usable_for_update 등)가 있으면 사용하고,
    없는 legacy 항목은 URL/파일명 존재 여부로 평가 기여는 허용하되
    update 가중치는 0으로 처리(usable_for_update=False 간주).
    """
    # quality flag 우선 — 없으면 legacy URL 존재 기준이지만 update weight=0
    flow_usable = merged_sources.get("flow_score_usable_for_update", False)
    consult_usable = merged_sources.get("consultation_usable_for_update", False)
    meeting_usable = merged_sources.get("meeting_usable_for_update", False)
    internal_usable = merged_sources.get("internal_review_usable_for_update", False)
    additional_usable = merged_sources.get("additional_usable_for_update", False)
    return {
        "flow_score_report": 0.35 if flow_usable else 0.0,
        "consultation_report": 0.35 if consult_usable else 0.0,
        "meeting_report": 0.10 if meeting_usable else 0.0,
        "internal_review": 0.15 if internal_usable else 0.0,
        "additional_sources": 0.05 if additional_usable else 0.0,
    }


def normalize_engine_version(value: Any) -> str:
    normalized = normalize_space(value)
    match = re.search(r"v\.\d+(?:\.\d+){1,3}", normalized, re.IGNORECASE)
    if match:
        return match.group(0)
    return normalized or "v.1.0.00"


def learning_material_flags_from_components(components: dict[str, float]) -> dict[str, bool]:
    return {
        "has_flow_score_report": float(components.get("flow_score_report", 0) or 0) > 0,
        "has_consultation_report": float(components.get("consultation_report", 0) or 0) > 0,
        "has_meeting_report": float(components.get("meeting_report", 0) or 0) > 0,
        "has_internal_review": float(components.get("internal_review", 0) or 0) > 0,
        "has_additional_sources": float(components.get("additional_sources", 0) or 0) > 0,
    }


def learning_status_from_components(components: dict[str, float]) -> dict[str, Any]:
    flags = learning_material_flags_from_components(components)
    # evaluation_ready: flow_score AND (consultation OR meeting) — meeting은 consultation의 보완재
    has_report_coverage = flags["has_consultation_report"] or flags["has_meeting_report"]
    evaluation_ready = flags["has_flow_score_report"] and has_report_coverage
    update_eligible = evaluation_ready and flags["has_internal_review"]
    evaluation_weight = round(sum(components.values()), 2) if evaluation_ready else 0.0
    update_weight = round(sum(components.values()), 2) if update_eligible else 0.0
    return {
        "evaluation_ready": evaluation_ready,
        "update_eligible": update_eligible,
        "evaluation_weight": evaluation_weight,
        "update_weight": update_weight,
        "flags": flags,
    }


def learning_case_identity(
    state: dict[str, Any],
    state_patch: dict[str, Any],
    engine_input: dict[str, Any],
) -> str:
    business_number = normalize_space(
        state_patch.get("businessNumber") or state.get("businessNumber") or engine_input.get("business_number")
    )
    company_name = (
        state_patch.get("companyName")
        or state.get("companyName")
        or engine_input.get("company_name")
        or state.get("learningFlowScoreFileName")
    )
    company_token = canonical_company_token(company_name)
    if business_number:
        return f"biz:{business_number}"
    if company_token:
        return f"name:{company_token}"
    return ""


def learning_case_id_from_identity(identity: str) -> str:
    return hashlib.sha1(identity.encode("utf-8")).hexdigest()[:16]


def extract_case_business_number(case: dict[str, Any]) -> str:
    sources = case.get("sources") or {}
    state_snapshot = case.get("state_snapshot") or {}
    proposal_context = (case.get("result_snapshot") or {}).get("proposal_context") or {}
    engine_input_snapshot = case.get("engine_input_snapshot") or {}
    return normalize_space(
        state_snapshot.get("businessNumber")
        or proposal_context.get("business_number")
        or engine_input_snapshot.get("business_number")
        or sources.get("business_number")
    )


def extract_case_company_token(case: dict[str, Any]) -> str:
    sources = case.get("sources") or {}
    state_snapshot = case.get("state_snapshot") or {}
    return canonical_company_token(
        case.get("company_name")
        or case.get("label")
        or state_snapshot.get("companyName")
        or sources.get("flow_score_file_name")
    )


def learning_case_merge_key_from_case(case: dict[str, Any]) -> str:
    stored_identity = normalize_space(case.get("merge_identity"))
    if stored_identity:
        if stored_identity.startswith(("biz:", "name:")):
            return stored_identity
        if re.fullmatch(r"\d{3}-\d{2}-\d{5}", stored_identity):
            return f"biz:{stored_identity}"
        stored_token = canonical_company_token(stored_identity)
        if stored_token:
            return f"name:{stored_token}"
    business_number = extract_case_business_number(case)
    if business_number:
        return f"biz:{business_number}"
    company_token = extract_case_company_token(case)
    if company_token:
        return f"name:{company_token}"
    return ""


def learning_case_merge_key_from_inputs(
    state: dict[str, Any],
    state_patch: dict[str, Any],
    engine_input: dict[str, Any],
) -> str:
    business_number = normalize_space(
        state_patch.get("businessNumber") or state.get("businessNumber") or engine_input.get("business_number")
    )
    if business_number:
        return f"biz:{business_number}"
    company_token = canonical_company_token(
        state_patch.get("companyName")
        or state.get("companyName")
        or engine_input.get("company_name")
        or state.get("learningFlowScoreFileName")
    )
    if company_token:
        return f"name:{company_token}"
    return ""


def learning_case_aliases_from_case(case: dict[str, Any]) -> set[str]:
    merge_key = learning_case_merge_key_from_case(case)
    return {merge_key} if merge_key else set()


def learning_case_aliases_from_inputs(
    state: dict[str, Any],
    state_patch: dict[str, Any],
    engine_input: dict[str, Any],
) -> set[str]:
    merge_key = learning_case_merge_key_from_inputs(state, state_patch, engine_input)
    return {merge_key} if merge_key else set()


def learning_case_identity_from_case(case: dict[str, Any]) -> str:
    merge_key = learning_case_merge_key_from_case(case)
    return merge_key or f"id:{normalize_space(case.get('id'))}" if normalize_space(case.get("id")) else ""


def locate_downloads_file(file_name: str) -> Path | None:
    normalized_name = normalize_space(file_name)
    if not normalized_name:
        return None
    direct = DOWNLOADS_DIR / normalized_name
    if direct.exists():
        return direct
    matches = list(DOWNLOADS_DIR.rglob(normalized_name))
    return matches[0] if matches else None


def business_number_from_text(value: Any) -> str:
    text = normalize_space(value)
    match = re.search(r"(\d{3})-?(\d{2})-?(\d{5})", text)
    if not match:
        return ""
    return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"


def company_name_from_filename(value: Any) -> str:
    text = unicodedata.normalize("NFKC", normalize_space(value))
    if not text:
        return ""
    stem = Path(text).stem
    stem = re.sub(r"^재무제표[_\-\s]*", "", stem)
    stem = re.sub(r"^신용평가리포트[_\-\s]*", "", stem)
    stem = re.sub(r"[_\-\s]*20\d{2}.*$", "", stem)
    stem = re.sub(r"\b\d{10}\b", "", stem)
    stem = stem.replace("주식회사", "")
    stem = re.sub(r"\(C\s*lab\)", "", stem, flags=re.I)
    stem = re.sub(r"[_\-\s]+", " ", stem).strip(" _-")
    return normalize_space(stem)


def infer_report_source_identity(file_name: str) -> dict[str, str]:
    identity = {
        "company_name": "",
        "business_number": "",
        "credit_grade": "",
    }
    path = locate_downloads_file(file_name)
    if path and path.is_file():
        try:
            parsed = parse_flowscore_report_pdf(path.read_bytes(), path.name)
            identity["company_name"] = normalize_space(parsed.get("company_name"))
            identity["business_number"] = normalize_space(parsed.get("business_number"))
            identity["credit_grade"] = normalize_space(parsed.get("credit_grade"))
        except Exception:
            pass
    if not identity["business_number"]:
        identity["business_number"] = business_number_from_text(file_name)
    if not identity["company_name"]:
        identity["company_name"] = company_name_from_filename(file_name)
    return identity


def find_best_report_file_name(company_name: str, business_number: str) -> str:
    business_digits = re.sub(r"\D", "", business_number or "")
    company_token = canonical_company_token(company_name)
    matches: list[Path] = []
    if DOWNLOADS_DIR.exists():
        for path in DOWNLOADS_DIR.rglob("*.pdf"):
            name = path.name
            normalized_name = canonical_company_token(name)
            if business_digits and business_digits in re.sub(r"\D", "", name):
                matches.append(path)
                continue
            if company_token and company_token and company_token in normalized_name:
                matches.append(path)
    if not matches:
        return ""
    matches.sort(key=lambda item: item.stat().st_mtime, reverse=True)
    return matches[0].name


def build_flow_report_only_case(
    template_case: dict[str, Any],
    flow_score_file_name: str,
    company_name: str,
    business_number: str,
    credit_grade: str,
) -> dict[str, Any]:
    state_snapshot: dict[str, Any] = {
        "mode": "learning",
        "companyName": company_name,
        "businessNumber": business_number,
        "financialFilterSignal": credit_grade or "확인 필요",
        "learningEligible": "자료 보완 필요",
    }
    if flow_score_file_name:
        try:
            parsed = parse_flowscore_report_pdf(locate_downloads_file(flow_score_file_name).read_bytes(), flow_score_file_name)
            state_snapshot = apply_report_enrichment(state_snapshot, parsed)
        except Exception:
            pass
    case = {
        "id": learning_case_id_from_identity(f"biz:{business_number}" if business_number else f"name:{canonical_company_token(company_name)}"),
        "merge_identity": f"biz:{business_number}" if business_number else f"name:{canonical_company_token(company_name)}",
        "label": company_name or flow_score_file_name,
        "company_name": company_name or flow_score_file_name,
        "created_at": template_case.get("created_at") or template_case.get("updated_at") or datetime.now().replace(microsecond=0).isoformat(),
        "updated_at": template_case.get("updated_at") or template_case.get("created_at") or datetime.now().replace(microsecond=0).isoformat(),
        "engine_version": normalize_engine_version(template_case.get("engine_version")),
        "learning": {
            "qualified": False,
            "total_weight": 0.0,
            "evaluation_ready": False,
            "update_eligible": False,
            "evaluation_weight": 0.0,
            "update_weight": 0.0,
            "components": {
                "flow_score_report": 0.35,
                "consultation_report": 0.0,
                "internal_review": 0.0,
                "additional_sources": 0.0,
            },
        },
        "sources": {
            "flow_score_file_name": flow_score_file_name,
            "consulting_report_url": "",
            "meeting_report_url": "",
            "consulting_file_name": "",
            "internal_review_url": "",
            "additional_info": "",
            "business_number": business_number,
        },
        "state_snapshot": state_snapshot,
        "engine_input_snapshot": {},
        "web_context_snapshot": {},
        "result_snapshot": {},
    }
    return normalize_learning_case(case)


def repair_case_flow_source_mismatch(case: dict[str, Any]) -> list[dict[str, Any]]:
    normalized_case = normalize_learning_case(case)
    sources = dict(normalized_case.get("sources") or {})
    flow_score_file_name = normalize_space(sources.get("flow_score_file_name"))
    if not flow_score_file_name:
        return [normalized_case]

    case_business_number = extract_case_business_number(normalized_case)
    case_company_token = extract_case_company_token(normalized_case)
    report_identity = infer_report_source_identity(flow_score_file_name)
    report_business_number = normalize_space(report_identity.get("business_number"))
    report_company_name = normalize_space(report_identity.get("company_name"))
    report_company_token = canonical_company_token(report_company_name)

    mismatched_business = bool(case_business_number and report_business_number and case_business_number != report_business_number)
    mismatched_company = bool(
        not case_business_number
        and case_company_token
        and report_company_token
        and case_company_token != report_company_token
    )

    if not (mismatched_business or mismatched_company):
        return [normalized_case]

    split_case = build_flow_report_only_case(
        normalized_case,
        flow_score_file_name,
        report_company_name or company_name_from_filename(flow_score_file_name),
        report_business_number,
        report_identity.get("credit_grade") or "",
    )

    remaining_case = dict(normalized_case)
    remaining_sources = dict(sources)
    remaining_sources["flow_score_file_name"] = ""
    company_name = normalize_space(remaining_case.get("company_name") or remaining_case.get("label"))
    replacement_file_name = find_best_report_file_name(company_name, case_business_number)
    if replacement_file_name and replacement_file_name != flow_score_file_name:
        remaining_sources["flow_score_file_name"] = replacement_file_name
    remaining_case["sources"] = remaining_sources
    remaining_merge_key = (
        f"biz:{case_business_number}"
        if case_business_number
        else f"name:{case_company_token}"
        if case_company_token
        else ""
    )
    if remaining_merge_key:
        remaining_case["merge_identity"] = remaining_merge_key
        remaining_case["id"] = learning_case_id_from_identity(remaining_merge_key)
    remaining_case = normalize_learning_case(remaining_case)
    return [remaining_case, split_case]


def merge_non_empty_dict(previous: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    merged = dict(previous or {})
    for key, value in (incoming or {}).items():
        if isinstance(value, str):
            if normalize_space(value):
                merged[key] = value
        elif value not in (None, "", [], {}):
            merged[key] = value
    return merged


def learning_status_label(status: dict[str, Any]) -> str:
    if status.get("update_eligible"):
        return "엔진 업데이트 적격"
    if status.get("evaluation_ready"):
        return "평가 반영 완료"
    return "자료 보완 필요"


def normalize_learning_case(case: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(case or {})
    components = (normalized.get("learning") or {}).get("components", {}) or {}
    status = learning_status_from_components(components)
    learning = dict(normalized.get("learning") or {})
    learning["components"] = components
    learning["evaluation_ready"] = status["evaluation_ready"]
    learning["update_eligible"] = status["update_eligible"]
    learning["evaluation_weight"] = status["evaluation_weight"]
    learning["update_weight"] = status["update_weight"]
    learning["qualified"] = status["update_eligible"]
    learning["total_weight"] = status["update_weight"]
    normalized["learning"] = learning
    normalized_merge_key = learning_case_merge_key_from_case(normalized)
    normalized["merge_identity"] = normalized_merge_key or normalize_space(normalized.get("merge_identity")) or learning_case_identity_from_case(
        normalized
    )
    if normalized["merge_identity"]:
        normalized["id"] = learning_case_id_from_identity(normalized["merge_identity"])
    normalized["engine_version"] = normalize_engine_version(normalized.get("engine_version"))
    return normalized


def looks_like_report_filename(value: Any) -> bool:
    text = unicodedata.normalize("NFKC", normalize_space(value)).lower()
    return bool(text and (text.endswith(".pdf") or "리포트" in text or "_" in text))


def case_quality_score(case: dict[str, Any]) -> int:
    score = 0
    company_name = normalize_space(case.get("company_name") or case.get("label"))
    if company_name and not looks_like_report_filename(company_name):
        score += 3
    if extract_case_business_number(case):
        score += 2
    state_snapshot = case.get("state_snapshot") or {}
    if normalize_space(state_snapshot.get("financialFilterSignal")) not in ("", "확인 필요"):
        score += 2
    limit_krw = (((case.get("result_snapshot") or {}).get("limit") or {}).get("single_delivery_limit_krw"))
    if isinstance(limit_krw, (int, float)) and limit_krw > 0:
        score += 1
    return score


def merge_learning_case_entries(primary: dict[str, Any], secondary: dict[str, Any]) -> dict[str, Any]:
    primary = normalize_learning_case(primary)
    secondary = normalize_learning_case(secondary)
    primary_updated = primary.get("updated_at") or primary.get("created_at") or ""
    secondary_updated = secondary.get("updated_at") or secondary.get("created_at") or ""
    newer, older = (secondary, primary) if secondary_updated >= primary_updated else (primary, secondary)
    richer = primary if case_quality_score(primary) >= case_quality_score(secondary) else secondary

    merged_sources = merge_non_empty_dict(older.get("sources") or {}, newer.get("sources") or {})
    # SourceQuality 기반 가중치 계산 — URL/파일명 존재만으로 update weight 부여하지 않음
    merged_components = _merged_components_from_sources(merged_sources)
    merged_status = learning_status_from_components(merged_components)
    merged = dict(richer)
    merged["id"] = normalize_space(older.get("id")) or normalize_space(newer.get("id")) or learning_case_id_from_identity(
        learning_case_identity_from_case(newer)
    )
    merged["created_at"] = older.get("created_at") or newer.get("created_at")
    merged["updated_at"] = newer.get("updated_at") or older.get("updated_at")
    merged["company_name"] = normalize_space(richer.get("company_name")) or normalize_space(newer.get("company_name")) or normalize_space(older.get("company_name"))
    merged["label"] = normalize_space(richer.get("label")) or normalize_space(newer.get("label")) or normalize_space(older.get("label")) or merged["company_name"]
    merged["sources"] = merged_sources
    merged["merge_identity"] = learning_case_identity_from_case(richer)
    merged_state_snapshot = merge_non_empty_dict(older.get("state_snapshot") or {}, newer.get("state_snapshot") or {})
    richer_state_snapshot = richer.get("state_snapshot") or {}
    if normalize_space(richer_state_snapshot.get("companyName")) and not looks_like_report_filename(richer_state_snapshot.get("companyName")):
        merged_state_snapshot["companyName"] = richer_state_snapshot.get("companyName")
    richer_business_number = extract_case_business_number(richer)
    if richer_business_number:
        merged_state_snapshot["businessNumber"] = richer_business_number
    richer_grade = normalize_space(richer_state_snapshot.get("financialFilterSignal"))
    if richer_grade and richer_grade != "확인 필요":
        merged_state_snapshot["financialFilterSignal"] = richer_grade
    merged["state_snapshot"] = merged_state_snapshot
    learning = dict(merged.get("learning") or {})
    learning["components"] = merged_components
    learning["evaluation_ready"] = merged_status["evaluation_ready"]
    learning["update_eligible"] = merged_status["update_eligible"]
    learning["evaluation_weight"] = merged_status["evaluation_weight"]
    learning["update_weight"] = merged_status["update_weight"]
    learning["qualified"] = merged_status["update_eligible"]
    learning["total_weight"] = merged_status["update_weight"]
    merged["learning"] = learning
    return normalize_learning_case(merged)


def normalize_dashboard_registry(registry: dict[str, Any]) -> dict[str, Any]:
    normalized_registry = {
        "engine_name": registry.get("engine_name", "BizAiPro"),
        "current_version": normalize_engine_version(registry.get("current_version", "v.1.0.00")),
        "updates": registry.get("updates", []),
        "cases": [],
    }
    merged_by_key: dict[str, dict[str, Any]] = {}
    passthrough_cases: list[dict[str, Any]] = []
    for raw_case in registry.get("cases", []):
        for repaired_case in repair_case_flow_source_mismatch(raw_case):
            case = normalize_learning_case(repaired_case)
            merge_key = learning_case_merge_key_from_case(case)
            if not merge_key:
                passthrough_cases.append(case)
                continue
            existing = merged_by_key.get(merge_key)
            if existing is None:
                merged_by_key[merge_key] = case
            else:
                merged_by_key[merge_key] = merge_learning_case_entries(existing, case)
    normalized_registry["cases"] = [*merged_by_key.values(), *passthrough_cases]
    return normalized_registry


def record_live_learning_case(
    state: dict[str, Any],
    state_patch: dict[str, Any],
    engine_input: dict[str, Any],
    result: dict[str, Any],
    context: dict[str, Any] | None = None,
    path: Path = LIVE_LEARNING_REGISTRY_PATH,
) -> dict[str, Any]:
    registry = load_live_learning_registry(path)
    current_version = normalize_engine_version(state.get("engineVersion") or registry.get("current_version") or "v.1.0.00")
    registry["engine_name"] = "BizAiPro"
    registry["current_version"] = current_version

    components = learning_material_components(state)
    learning_status = learning_status_from_components(components)
    merge_identity = learning_case_identity(state, state_patch, engine_input)
    merge_key = learning_case_merge_key_from_inputs(state, state_patch, engine_input)
    case_id = learning_case_id_from_identity(merge_identity)
    now_text = datetime.now().replace(microsecond=0).isoformat()

    # quality flags를 sources에 함께 저장 — merge 후에도 SourceQuality 기준 유지
    _sq_flags = _source_quality_flags_from_state(state)
    incoming_sources = {
        "flow_score_file_name": normalize_space(state.get("learningFlowScoreFileName")),
        "consulting_report_url": normalize_space(state.get("consultingReportUrl")),
        "meeting_report_url": normalize_space(state.get("meetingReportUrl")),
        "consulting_file_name": normalize_space(state.get("learningConsultingFileName")),
        "internal_review_url": normalize_space(state.get("internalReviewUrl")),
        "additional_info": normalize_space(state.get("learningExtraInfo")),
        "business_number": normalize_space(state_patch.get("businessNumber") or state.get("businessNumber")),
        **_sq_flags,
    }

    cases = registry.setdefault("cases", [])
    existing_index = next(
        (
            idx
            for idx, case in enumerate(cases)
            if merge_key and learning_case_merge_key_from_case(case) == merge_key
        ),
        None,
    )
    previous_case = cases[existing_index] if existing_index is not None else {}
    merged_sources = merge_non_empty_dict(previous_case.get("sources") or {}, incoming_sources)
    # SourceQuality 기반 가중치 계산 — URL/파일명 존재만으로 update weight 부여하지 않음
    merged_components = _merged_components_from_sources(merged_sources)
    merged_status = learning_status_from_components(merged_components)

    case_entry = {
        "id": normalize_space(previous_case.get("id")) or case_id,
        "merge_identity": merge_identity,
        "label": normalize_space(state_patch.get("companyName") or state.get("companyName") or engine_input.get("company_name"))
        or normalize_space(previous_case.get("label"))
        or "이름 미확인",
        "company_name": normalize_space(state_patch.get("companyName") or state.get("companyName"))
        or normalize_space(previous_case.get("company_name")),
        "created_at": now_text,
        "updated_at": now_text,
        "engine_version": current_version,
        "learning": {
            "qualified": merged_status["update_eligible"],
            "total_weight": merged_status["update_weight"],
            "evaluation_ready": merged_status["evaluation_ready"],
            "update_eligible": merged_status["update_eligible"],
            "evaluation_weight": merged_status["evaluation_weight"],
            "update_weight": merged_status["update_weight"],
            "components": merged_components,
        },
        "sources": merged_sources,
        "engine_input_snapshot": engine_input,
        "web_context_snapshot": normalize_learning_context_for_display(context or build_web_context(engine_input, result)),
        "state_snapshot": {
            "mode": "learning",
            "companyName": state_patch.get("companyName"),
            "businessNumber": state_patch.get("businessNumber") or state.get("businessNumber"),
            "financialFilterSignal": state_patch.get("financialFilterSignal"),
            "reportMonthlyCreditLimit": state_patch.get("reportMonthlyCreditLimit"),
            "baseMonthlyLimitLabel": state_patch.get("baseMonthlyLimitLabel"),
            "baseMonthlyLimitValue": state_patch.get("baseMonthlyLimitValue"),
            "engineAdjustedLimitLabel": state_patch.get("engineAdjustedLimitLabel"),
            "engineAdjustedLimitValue": state_patch.get("engineAdjustedLimitValue"),
            "learningOperationalLimitLabel": state_patch.get("learningOperationalLimitLabel"),
            "learningOperationalLimitValue": state_patch.get("learningOperationalLimitValue"),
            "estimatedLimitLabel": state_patch.get("estimatedLimitLabel"),
            "estimatedLimitValue": state_patch.get("estimatedLimitValue"),
            "estimatedMarginValue": state_patch.get("estimatedMarginValue"),
            "currentProposalState": state_patch.get("currentProposalState"),
            "recommendedTenorText": state_patch.get("recommendedTenorText"),
            "learningEligible": state_patch.get("learningEligible"),
            "consultingReportUrl": state.get("consultingReportUrl"),
            "meetingReportUrl": state.get("meetingReportUrl"),
            "internalReviewUrl": state.get("internalReviewUrl"),
            "learningExtraInfo": state.get("learningExtraInfo"),
            "consultingValidationSummary": state_patch.get("consultingValidationSummary") or state.get("consultingValidationSummary"),
            "consultingSummary": state_patch.get("consultingSummary") or state.get("consultingSummary"),
            "consultingCrossChecks": state_patch.get("consultingCrossChecks") or state.get("consultingCrossChecks"),
            "consultingIssues": state_patch.get("consultingIssues") or state.get("consultingIssues"),
            "meetingValidationSummary": state_patch.get("meetingValidationSummary") or state.get("meetingValidationSummary"),
            "meetingSummary": state_patch.get("meetingSummary") or state.get("meetingSummary"),
            "meetingCrossChecks": state_patch.get("meetingCrossChecks") or state.get("meetingCrossChecks"),
            "meetingIssues": state_patch.get("meetingIssues") or state.get("meetingIssues"),
            "internalReviewValidationSummary": state_patch.get("internalReviewValidationSummary") or state.get("internalReviewValidationSummary"),
            "internalReviewSummary": state_patch.get("internalReviewSummary") or state.get("internalReviewSummary"),
            "internalReviewCrossChecks": state_patch.get("internalReviewCrossChecks") or state.get("internalReviewCrossChecks"),
            "internalReviewIssues": state_patch.get("internalReviewIssues") or state.get("internalReviewIssues"),
            "supportingDocumentSummary": state_patch.get("supportingDocumentSummary") or state.get("supportingDocumentSummary"),
            "supportingDocumentIssues": state_patch.get("supportingDocumentIssues") or state.get("supportingDocumentIssues"),
            "additionalInfoSummary": state_patch.get("additionalInfoSummary") or state.get("additionalInfoSummary"),
            "additionalInfoIssues": state_patch.get("additionalInfoIssues") or state.get("additionalInfoIssues"),
            "supplierName": state_patch.get("supplierName") or state.get("supplierName"),
            "buyerName": state_patch.get("buyerName") or state.get("buyerName"),
            "requestedTenorDays": state_patch.get("requestedTenorDays") or state.get("requestedTenorDays"),
            "requestedTenorMonths": state_patch.get("requestedTenorMonths") or state.get("requestedTenorMonths"),
        },
        "result_snapshot": result,
    }

    if existing_index is None:
        cases.append(case_entry)
    else:
        case_entry["created_at"] = previous_case.get("created_at", now_text)
        cases[existing_index] = case_entry

    save_live_learning_registry(registry, path)
    return registry


def infer_engine_traits(engine_version: str) -> list[str]:
    normalized = str(engine_version or "")
    if "local.learning" in normalized:
        return [
            "업로드된 FlowScore와 Notion 자동조회 결과를 즉시 실시간 평가에 반영합니다.",
            "상담·미팅·심사보고서 누락 시 평가 취소 또는 FlowScore 단독 평가 진행을 선택합니다.",
            "자료 품질과 파싱 성공 여부를 분리해 평가 반영 상태를 표시합니다.",
        ]
    if "1.16.01" in normalized:
        return [
            "전시회 URL과 기업 웹주소 URL을 함께 읽어 핵심 정보를 자동 추출합니다.",
            "재무는 제공 가능 여부를 거르는 필터로, 비재무는 제안 메시지 근거로 해석합니다.",
            "평가 결과에서 제안서와 이메일 초안까지 한 흐름으로 연결합니다.",
        ]
    if "1.0.00" in normalized:
        return [
            "재무 필터를 더 보수적으로 보는 초기 기준입니다.",
            "전시회형 메시지보다 기본 소개 메일 흐름을 우선시합니다.",
            "결제유예기간과 초기 한도를 짧고 보수적으로 제안합니다.",
        ]
    return [
        "샘플 기준으로 화면 구조와 문장 흐름을 검토하는 베이스 엔진입니다.",
        "입력값과 업로드 결과에 맞춰 제안서와 이메일 문구를 다시 그립니다.",
    ]


def collect_generation_history(limit: int = 5) -> list[dict[str, str]]:
    doc_type_by_name = {
        "proposal_draft.md": "제안서",
        "sales_report.md": "평가 결과 리포트",
        "sales_email_draft.txt": "이메일",
        "comparison_report.md": "엔진 비교",
    }
    items: list[dict[str, str]] = []
    for path in OUTPUTS_DIR.rglob("*"):
        if not path.is_file() or path.name not in doc_type_by_name:
            continue
        stat = path.stat()
        updated_at = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
        bundle_name = path.parent.name.replace("_", " ")
        items.append(
            {
                "type": doc_type_by_name[path.name],
                "name": bundle_name,
                "updated_at": updated_at,
                "path": str(path.relative_to(BASE_DIR)),
            }
        )
    items.sort(key=lambda item: item["updated_at"], reverse=True)
    return items[:limit]


def serialize_learning_case(case: dict[str, Any]) -> dict[str, Any]:
    case = normalize_learning_case(case)
    sources = case.get("sources") or {}
    components = (case.get("learning") or {}).get("components", {}) or {}
    source_links: list[dict[str, str]] = []
    consulting_url = normalize_space(sources.get("consulting_report_url"))
    meeting_url = normalize_space(sources.get("meeting_report_url"))
    internal_url = normalize_space(sources.get("internal_review_url"))
    if consulting_url:
        source_links.append({"label": "상담리포트", "url": consulting_url})
    if meeting_url:
        source_links.append({"label": "미팅보고서", "url": meeting_url})
    if internal_url:
        source_links.append({"label": "심사보고서", "url": internal_url})
    return {
        "id": case.get("id"),
        "label": case.get("label") or case.get("company_name") or "이름 미확인",
        "company_name": case.get("company_name") or case.get("label") or "이름 미확인",
        "updated_at": case.get("updated_at") or case.get("created_at") or "",
        "engine_version": case.get("engine_version") or "",
        "evaluation_ready": bool((case.get("learning") or {}).get("evaluation_ready")),
        "update_eligible": bool((case.get("learning") or {}).get("update_eligible")),
        "evaluation_weight": (case.get("learning") or {}).get("evaluation_weight") or 0,
        "update_weight": (case.get("learning") or {}).get("update_weight") or 0,
        "qualified": bool((case.get("learning") or {}).get("update_eligible")),
        "total_weight": (case.get("learning") or {}).get("update_weight") or 0,
        "has_flow_score_report": float(components.get("flow_score_report", 0) or 0) > 0,
        "has_consultation_report": float(components.get("consultation_report", 0) or 0) > 0,
        "has_internal_review": float(components.get("internal_review", 0) or 0) > 0,
        "detail_url": f"/web/bizaipro_evaluation_result.html?case_id={case.get('id')}",
        "source_links": source_links,
    }


def sort_learning_cases(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        [normalize_learning_case(case) for case in cases],
        key=lambda case: case.get("updated_at") or case.get("created_at") or "",
        reverse=True,
    )


def build_learning_case_state(case: dict[str, Any]) -> dict[str, Any]:
    case = normalize_learning_case(case)
    state_patch: dict[str, Any] = {"mode": "learning"}
    web_context = None
    engine_input_snapshot = case.get("engine_input_snapshot")
    result_snapshot = case.get("result_snapshot")
    if isinstance(engine_input_snapshot, dict) and engine_input_snapshot and isinstance(result_snapshot, dict) and result_snapshot:
        web_context = build_web_context(engine_input_snapshot, result_snapshot)
    if not web_context:
        web_context = case.get("web_context_snapshot")
    context_patch: dict[str, Any] = {}
    if isinstance(web_context, dict) and web_context:
        web_context = normalize_learning_context_for_display(web_context)
        context_patch = state_patch_from_context(web_context)
        state_patch.update(context_patch)
    state_snapshot = case.get("state_snapshot")
    if isinstance(state_snapshot, dict) and state_snapshot:
        state_patch.update(state_snapshot)
    if context_patch:
        for key in [
            "reportMonthlyCreditLimit",
            "baseMonthlyLimitLabel",
            "baseMonthlyLimitValue",
            "engineAdjustedLimitLabel",
            "engineAdjustedLimitValue",
            "learningOperationalLimitLabel",
            "learningOperationalLimitValue",
            "estimatedLimitLabel",
            "estimatedLimitValue",
        ]:
            if context_patch.get(key):
                state_patch[key] = context_patch.get(key)
    financial_summary = state_patch.get("reportFinancialSummary") or {}
    if isinstance(financial_summary, dict) and financial_summary:
        latest_year = sorted(financial_summary.keys())[-1]
        latest_values = financial_summary.get(latest_year) or {}
        state_patch["recentRevenueLabel"] = state_patch.get("recentRevenueLabel") or f"{latest_year}년 매출액"
        state_patch["recentRevenueValue"] = state_patch.get("recentRevenueValue") or latest_values.get("sales") or "확인 필요"
        state_patch["operatingProfitLabel"] = state_patch.get("operatingProfitLabel") or f"{latest_year}년 영업이익"
        state_patch["operatingProfitValue"] = (
            state_patch.get("operatingProfitValue") or latest_values.get("operating_profit") or "확인 필요"
        )
        state_patch["netIncomeLabel"] = state_patch.get("netIncomeLabel") or f"{latest_year}년 당기순이익"
        state_patch["netIncomeValue"] = state_patch.get("netIncomeValue") or latest_values.get("net_income") or "확인 필요"
    state_patch["estimatedLimitLabel"] = state_patch.get("estimatedLimitLabel") or "예상 한도"
    state_patch["estimatedMarginLabel"] = state_patch.get("estimatedMarginLabel") or "예상 마진율"
    state_patch["mode"] = "learning"
    state_patch["learningEligible"] = state_patch.get("learningEligible") or learning_status_label(case.get("learning") or {})
    if not state_patch.get("learningWeight"):
        update_weight = float((case.get("learning") or {}).get("update_weight") or 0)
        evaluation_weight = float((case.get("learning") or {}).get("evaluation_weight") or 0)
        state_patch["learningWeight"] = f"{update_weight:.2f}" if update_weight else f"{evaluation_weight:.2f}"
    return state_patch


def detail_score_label(section_key: str, item_name: str) -> str:
    labels = {
        "applicant": {
            "financial": "재무",
            "business": "사업",
            "management": "경영관리",
            "compliance": "준법/정합성",
            "external": "외부신호",
        },
        "buyer": {
            "financial": "재무",
            "business": "사업",
            "payment": "결제/회수",
            "external": "외부신호",
        },
        "transaction": {
            "structure": "거래구조",
            "tenor": "결제유예기간",
            "macro": "업황/거시",
        },
        "overall": {
            "applicant": "신청업체",
            "buyer": "매출처",
            "transaction": "거래구조",
        },
    }
    return labels.get(section_key, {}).get(item_name, item_name)


def build_detail_score_section(section_key: str, title: str, result_snapshot: dict[str, Any]) -> dict[str, Any]:
    score_breakdown = ((result_snapshot or {}).get("score_breakdown") or {}).get(section_key) or {}
    breakdown_items = score_breakdown.get("items") or score_breakdown.get("weighted_items") or []
    grade_source_key = "overall" if section_key == "overall" else section_key
    grade_source = (result_snapshot or {}).get(grade_source_key) or {}
    total_score = grade_source.get("score")
    if total_score in (None, ""):
        total_score = score_breakdown.get("total")
    return {
        "key": section_key,
        "title": title,
        "score": round(float(total_score), 2) if total_score not in (None, "") else None,
        "grade": grade_source.get("grade"),
        "rows": [
            {
                "label": detail_score_label(section_key, str(item.get("name", ""))),
                "score": round(float(item.get("score", 0.0)), 2),
                "weight_text": f"{float(item.get('weight', 0.0)) * 100:.0f}%",
                "contribution": round(float(item.get("contribution", 0.0)), 2),
            }
            for item in breakdown_items
        ],
    }


def build_limit_detail_rows(
    state_patch: dict[str, Any], engine_input_snapshot: dict[str, Any], result_snapshot: dict[str, Any]
) -> dict[str, Any]:
    framework = load_active_framework()
    model = framework["flowpay_underwriting"]
    limit_cfg = model["limit"]

    base_monthly_limit_krw = parse_krw_text_to_int(state_patch.get("baseMonthlyLimitValue") or state_patch.get("reportMonthlyCreditLimit"))
    engine_adjusted_limit_krw = parse_krw_text_to_int(state_patch.get("engineAdjustedLimitValue"))
    learning_operational_limit_krw = parse_krw_text_to_int(state_patch.get("learningOperationalLimitValue"))

    financials = engine_input_snapshot.get("financials") or {}
    annual_sales = float(financials.get("annual_sales") or 0.0)
    operating_profit = float(financials.get("operating_profit") or 0.0)
    net_profit = float(financials.get("net_profit") or 0.0)
    business_years = float((engine_input_snapshot.get("screening") or {}).get("business_years") or 0.0)
    requested_tenor_months = int(engine_input_snapshot.get("requested_tenor_months") or 3)
    overall_score = float(((result_snapshot.get("overall") or {}).get("score")) or 0.0)
    buyer_score = float(((result_snapshot.get("buyer") or {}).get("score")) or 0.0)

    if business_years <= 2:
        age_factor = float(limit_cfg["age_factor"]["lte_2"])
    elif business_years <= 3:
        age_factor = float(limit_cfg["age_factor"]["lte_3"])
    elif business_years < 7:
        age_factor = float(limit_cfg["age_factor"]["lt_7"])
    else:
        age_factor = float(limit_cfg["age_factor"]["gte_7"])

    if operating_profit >= 0 and net_profit >= 0:
        profit_factor = float(limit_cfg["profit_factor"]["both_positive"])
        profit_note = "영업이익/당기순이익 모두 흑자"
    elif operating_profit < 0 and net_profit < 0:
        profit_factor = float(limit_cfg["profit_factor"]["both_negative"])
        profit_note = "영업이익/당기순이익 모두 적자"
    else:
        profit_factor = float(limit_cfg["profit_factor"]["one_negative"])
        profit_note = "영업이익 또는 당기순이익 중 하나가 적자"

    risk_factor = score_band_multiplier(
        overall_score,
        [(80, 1.10), (70, 1.00), (60, 0.85), (50, 0.70), (0, 0.55)],
    )
    buyer_factor = score_band_multiplier(
        buyer_score,
        [(80, 1.05), (70, 1.00), (60, 0.90), (50, 0.80), (0, 0.65)],
    )
    tenor_factor = {1: 1.00, 2: 0.90, 3: 0.80, 4: 0.70, 5: 0.60}.get(requested_tenor_months, 0.55)

    current_amount = float(base_monthly_limit_krw or 0)
    factor_rows = [
        {
            "label": state_patch.get("baseMonthlyLimitLabel") or "기준 월간 적정 한도",
            "factor_text": "-",
            "result_text": format_krw(base_monthly_limit_krw),
            "note": "리포트 직접값이 있으면 우선 사용하고, 없으면 연매출/12 x 70% 기준을 사용합니다.",
        }
    ]

    for label, factor, note in [
        ("업력 보정", age_factor, f"업력 {business_years:.2f}년 기준"),
        ("손익 보정", profit_factor, profit_note),
        ("통합점수 보정", risk_factor, f"통합 점수 {overall_score:.2f}점"),
        ("매출처 보정", buyer_factor, f"매출처 점수 {buyer_score:.2f}점"),
        ("결제유예기간 보정", tenor_factor, f"결제유예기간 {requested_tenor_months}개월 기준"),
    ]:
        current_amount *= factor
        factor_rows.append(
            {
                "label": label,
                "factor_text": f"{factor:.2f}배",
                "result_text": format_krw(int(round(current_amount))),
                "note": note,
            }
        )

    hard_cap = (annual_sales / 12.0) * float(limit_cfg["monthly_sales_cap_ratio"]) if annual_sales > 0 else None
    if hard_cap:
        capped_amount = min(current_amount, hard_cap)
        if capped_amount != current_amount:
            factor_rows.append(
                {
                    "label": "월매출 상한 적용",
                    "factor_text": "cap",
                    "result_text": format_krw(int(round(capped_amount))),
                    "note": "엔진은 월매출 상한을 넘지 않도록 한도를 제한합니다.",
                }
            )
            current_amount = capped_amount

    factor_rows.append(
        {
            "label": state_patch.get("engineAdjustedLimitLabel") or "엔진 보정 한도",
            "factor_text": "최종",
            "result_text": format_krw(engine_adjusted_limit_krw),
            "note": "위 보정 배수와 천원 단위 반올림을 적용한 엔진 최종 한도입니다.",
        }
    )
    factor_rows.append(
        {
            "label": state_patch.get("learningOperationalLimitLabel") or "학습모드 운영 한도(주간 1회 기준)",
            "factor_text": "/4",
            "result_text": format_krw(learning_operational_limit_krw),
            "note": "학습모드 화면에서는 엔진 보정 한도를 4로 나눈 뒤 백만원 미만 절사해 보수적으로 표시합니다.",
        }
    )

    return {
        "base_monthly_limit_text": format_krw(base_monthly_limit_krw),
        "engine_adjusted_limit_text": format_krw(engine_adjusted_limit_krw),
        "learning_operational_limit_text": format_krw(learning_operational_limit_krw),
        "rows": factor_rows,
    }


def build_tenor_margin_rows(engine_input_snapshot: dict[str, Any], result_snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    framework = load_active_framework()
    model = framework["flowpay_underwriting"]
    supported_months = sorted(model["margin"]["supported_deferral_months"])
    applicant_score = float(((result_snapshot.get("applicant") or {}).get("score")) or 0.0)
    buyer_score = float(((result_snapshot.get("buyer") or {}).get("score")) or 0.0)
    transaction_score = float(((result_snapshot.get("transaction") or {}).get("score")) or 0.0)
    overall_score = float(((result_snapshot.get("overall") or {}).get("score")) or 0.0)
    applicant_compliance_score = float(
        (((result_snapshot.get("applicant") or {}).get("category_scores") or {}).get("compliance")) or 0.0
    )
    selected_month = int(engine_input_snapshot.get("requested_tenor_months") or 0)

    rows: list[dict[str, Any]] = []
    for month in supported_months:
        margin = compute_margin_result(
            requested_tenor_months=month,
            applicant_score=applicant_score,
            buyer_score=buyer_score,
            transaction_score=transaction_score,
            overall_score=overall_score,
            applicant_compliance_score=applicant_compliance_score,
            model=model,
        )
        note = "대안 검토"
        if month == selected_month:
            note = "현재 제안 · 적정 유예기간 및 마진율"
        elif month > selected_month:
            note = "보수 검토"
        rows.append(
            {
                "months": month,
                "tenor_label": f"{month}개월",
                "commercial_rate_text": format_percent(margin.get("commercial_rate_pct")),
                "compliant_rate_text": format_percent(margin.get("compliant_rate_pct")),
                "selected": month == selected_month,
                "note": note,
            }
        )
    return rows


def build_evaluation_detail_report(case: dict[str, Any]) -> dict[str, Any]:
    result_snapshot = case.get("result_snapshot") or {}
    engine_input_snapshot = case.get("engine_input_snapshot") or {}
    if not result_snapshot:
        return {}

    state_patch = build_learning_case_state(case)
    sales_view = result_snapshot.get("sales_view") or {}
    return {
        "score_sections": [
            build_detail_score_section("applicant", "신청업체 점수표", result_snapshot),
            build_detail_score_section("buyer", "매출처 점수표", result_snapshot),
            build_detail_score_section("transaction", "거래구조 점수표", result_snapshot),
            build_detail_score_section("overall", "통합 점수표", result_snapshot),
        ],
        "limit_section": build_limit_detail_rows(state_patch, engine_input_snapshot, result_snapshot),
        "tenor_margin_rows": build_tenor_margin_rows(engine_input_snapshot, result_snapshot),
        "current_tenor_text": state_patch.get("recommendedTenorText") or "결제기간 확인 필요",
        "risk_notes": list(sales_view.get("risk_notes") or []),
        "strengths": list(result_snapshot.get("strengths") or []),
        "weaknesses": list(result_snapshot.get("weaknesses") or []),
    }


def format_krw(value: Any) -> str:
    if value in (None, ""):
        return "확인 필요"
    try:
        return f"{int(round(float(value))):,}원"
    except (TypeError, ValueError):
        return str(value)


def format_percent(value: Any) -> str:
    if value in (None, ""):
        return "확인 필요"
    try:
        return f"{float(value):.2f}%"
    except (TypeError, ValueError):
        return str(value)


def truncate_below_million(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        numeric = int(float(value))
    except (TypeError, ValueError):
        return None
    if numeric <= 0:
        return None
    return (numeric // 1_000_000) * 1_000_000


def weekly_learning_limit_from_engine(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    if numeric <= 0:
        return None
    return truncate_below_million(numeric / 4.0)


def recalculate_margin_amount(limit_krw: Any, rate_pct: Any) -> int | None:
    if limit_krw in (None, "") or rate_pct in (None, ""):
        return None
    try:
        return int(round(float(limit_krw) * float(rate_pct) / 100.0))
    except (TypeError, ValueError):
        return None


def replace_learning_display_amounts(text: str, limit_krw: int | None, margin_amount_krw: int | None) -> str:
    if not text:
        return text
    updated = text
    if limit_krw:
        limit_text = format_krw(limit_krw)
        updated = re.sub(r"예상 1회 거래 한도는 [0-9,]+원", f"예상 1회 거래 한도는 {limit_text}", updated)
        updated = re.sub(r"예상 한도는 [0-9,]+원", f"예상 한도는 {limit_text}", updated)
        updated = re.sub(r"기준 금액 [0-9,]+원", f"기준 금액 {limit_text}", updated)
    if margin_amount_krw:
        margin_text = format_krw(margin_amount_krw)
        updated = re.sub(r"예상 마진액은 [0-9,]+원", f"예상 마진액은 {margin_text}", updated)
    return updated


def normalize_learning_context_for_display(context: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(context, dict) or not context:
        return {}
    normalized = json.loads(json.dumps(context, ensure_ascii=False))
    sales_view = dict(normalized.get("sales_view") or {})
    engine_adjusted_limit_krw = sales_view.get("estimated_limit_krw")
    base_monthly_limit_krw = sales_view.get("reference_purchase_amount_krw")
    weekly_limit_krw = weekly_learning_limit_from_engine(engine_adjusted_limit_krw)

    sales_view["raw_estimated_limit_krw"] = engine_adjusted_limit_krw
    sales_view["base_monthly_limit_krw"] = base_monthly_limit_krw
    sales_view["engine_adjusted_limit_krw"] = engine_adjusted_limit_krw
    sales_view["learning_operational_limit_krw"] = weekly_limit_krw

    learning_margin_amount_krw = recalculate_margin_amount(weekly_limit_krw, sales_view.get("estimated_margin_rate_pct"))
    learning_compliant_margin_amount_krw = recalculate_margin_amount(
        weekly_limit_krw, sales_view.get("estimated_compliant_margin_rate_pct")
    )
    if learning_margin_amount_krw is not None:
        sales_view["learning_operational_margin_amount_krw"] = learning_margin_amount_krw
    if learning_compliant_margin_amount_krw is not None:
        sales_view["learning_operational_compliant_margin_amount_krw"] = learning_compliant_margin_amount_krw

    normalized["sales_view"] = sales_view
    return normalized


def format_tenor_text(months: Any, days: Any) -> str:
    try:
        if days not in (None, "") and float(days) > 0:
            day_value = int(float(days))
            if day_value % 30 != 0:
                return f"{day_value}일 기준 검토"
    except (TypeError, ValueError):
        pass
    try:
        if months not in (None, "") and float(months) > 0:
            return f"{int(float(months))}개월 우선 검토"
    except (TypeError, ValueError):
        pass
    try:
        if days not in (None, "") and float(days) > 0:
            return f"{int(float(days))}일 기준 검토"
    except (TypeError, ValueError):
        pass
    return "결제기간 확인 필요"


def parse_iso_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def years_since(value: str | None) -> float:
    parsed = parse_iso_date(value)
    if not parsed:
        return 0.0
    return round((date.today() - parsed).days / 365.25, 2)


def grade_to_signal_score(grade: str | None, default: float = 55.0) -> float:
    if not grade:
        return default
    normalized = str(grade).upper().strip()
    base_map = {
        "AAA": 96.0,
        "AA": 90.0,
        "A": 82.0,
        "BBB": 72.0,
        "BB": 62.0,
        "B": 52.0,
        "CCC": 38.0,
        "CC": 30.0,
        "C": 22.0,
        "D": 10.0,
    }
    modifier = 0.0
    if normalized.endswith("+"):
        modifier = 3.0
        normalized = normalized[:-1]
    elif normalized.endswith("-"):
        modifier = -3.0
        normalized = normalized[:-1]
    for prefix, base in base_map.items():
        if normalized.startswith(prefix):
            return max(0.0, min(100.0, base + modifier))
    return default


def classify_industry_profile(text: str) -> tuple[str, str, str]:
    normalized = normalize_space(text).lower()
    if any(keyword in normalized for keyword in ["제조", "cnc", "금속", "구리", "부품", "가공", "기계", "장비", "수출"]):
        return "manufacturing", "manufacturing", "C0000"
    if any(keyword in normalized for keyword in ["서비스", "it", "소프트웨어", "플랫폼", "saas", "클라우드"]):
        return "service_it", "service_it", "J0000"
    return "default", "general", "C0000"


def buyer_signal_score(name: str | None) -> float:
    value = normalize_space(name)
    if not value:
        return 52.0
    high_keywords = ["삼성", "현대", "lg", "쿠팡", "g마켓", "하프클럽", "현대중공업", "sk", "포스코", "공사", "공단"]
    mid_keywords = ["주식회사", "(주)", "유한", "코리아", "인터내셔널"]
    lowered = value.lower()
    if any(keyword.lower() in lowered for keyword in high_keywords):
        return 82.0
    if any(keyword.lower() in lowered for keyword in mid_keywords):
        return 66.0
    return 58.0


def latest_financial_values(state: dict[str, Any]) -> tuple[int | None, int | None, int | None]:
    annual_sales = parse_krw_text_to_int(state.get("recentRevenueValue"))
    operating_profit = parse_krw_text_to_int(state.get("operatingProfitValue"))
    net_profit = parse_krw_text_to_int(state.get("netIncomeValue"))
    return annual_sales, operating_profit, net_profit


def yoy_sales_drop_pct(financial_summary: dict[str, Any] | None) -> float:
    if not financial_summary or len(financial_summary) < 2:
        return 0.0
    years = sorted(financial_summary.keys(), reverse=True)
    latest = parse_krw_text_to_int((financial_summary.get(years[0]) or {}).get("sales"))
    previous = parse_krw_text_to_int((financial_summary.get(years[1]) or {}).get("sales"))
    if not latest or not previous or previous <= 0:
        return 0.0
    decline = ((previous - latest) / previous) * 100.0
    return round(max(0.0, decline), 2)


def build_learning_evaluation_payload(state: dict[str, Any]) -> dict[str, Any]:
    company_name = normalize_space(state.get("companyName")) or "업로드 기업"
    representative_name = normalize_space(state.get("representativeName")) or "확인 필요"
    business_number = normalize_space(state.get("businessNumber")) or ""
    credit_grade = normalize_space(state.get("reportCreditGrade") or state.get("financialFilterSignal"))
    annual_sales, operating_profit, net_profit = latest_financial_values(state)
    report_financial_summary = state.get("reportFinancialSummary") or {}
    reported_monthly_limit_krw = parse_krw_text_to_int(
        state.get("reportMonthlyCreditLimit") or state.get("baseMonthlyLimitValue")
    )
    base_monthly_limit_krw = reported_monthly_limit_krw or (annual_sales / 12 * 0.7 if annual_sales else None)
    business_years = years_since(state.get("reportIncorporatedDate"))
    raw_tenor_days = state.get("requestedTenorDays")
    raw_tenor_months = state.get("requestedTenorMonths")
    requested_tenor_days = int(raw_tenor_days or 60)
    if raw_tenor_months not in (None, ""):
        requested_tenor_months = int(raw_tenor_months)
        if requested_tenor_days % 30 != 0:
            requested_tenor_months = max(1, round(requested_tenor_days / 30))
    else:
        requested_tenor_months = max(1, round(requested_tenor_days / 30))
    supplier_name = normalize_space(state.get("supplierName")) or "매입처 확인 필요"
    buyer_name = normalize_space(state.get("buyerName")) or "매출처 확인 필요"
    industry_text = " ".join(
        [
            str(state.get("industryItem") or ""),
            str(state.get("companyOverview") or ""),
            str(state.get("websiteSummary") or ""),
            str(state.get("additionalInfoSummary") or ""),
        ]
    )
    industry_profile, industry_tag, ecos_industry_code = classify_industry_profile(industry_text)

    operating_margin_pct = 0.0
    if annual_sales and operating_profit is not None and annual_sales > 0:
        operating_margin_pct = round((operating_profit / annual_sales) * 100.0, 2)

    applicant_grade_score = grade_to_signal_score(credit_grade, 55.0)
    buyer_grade_score = buyer_signal_score(buyer_name)
    consultation_validation_summary = state.get("consultingValidationSummary") or state.get("meetingValidationSummary")
    data_support_bonus = 8.0 if consultation_validation_summary else 0.0
    # meeting_support_bonus: meetingSummary/meetingCrossChecks 키워드 분석 — 매출처 결제 관련 신호 추출
    _meeting_text = " ".join([
        str(state.get("meetingSummary") or ""),
        str(state.get("meetingCrossChecks") or ""),
    ])
    _payment_keywords = ["결제", "입금", "정산", "대금", "지급", "수령", "거래처", "수금", "매출처"]
    _settlement_keywords = ["정산주기", "결제조건", "지급조건", "어음", "선불", "후불", "월말"]
    _invoice_keywords = ["세금계산서", "계산서", "발행", "인수", "승인", "매입확인", "거래확인"]
    _meeting_payment_score = 3.0 if any(k in _meeting_text for k in _payment_keywords) else 0.0
    _meeting_settlement_score = 3.0 if any(k in _meeting_text for k in _settlement_keywords) else 0.0
    _meeting_invoice_score = 3.0 if any(k in _meeting_text for k in _invoice_keywords) else 0.0
    meeting_support_bonus = min(6.0, _meeting_payment_score + _meeting_settlement_score + _meeting_invoice_score) if _meeting_text.strip() else 0.0
    internal_support_bonus = 6.0 if state.get("internalReviewValidationSummary") else 0.0
    file_support_bonus = 5.0 if state.get("supportingDocumentSummary") else 0.0
    extra_support_bonus = 4.0 if state.get("additionalInfoSummary") else 0.0
    structure_bonus = data_support_bonus + meeting_support_bonus + internal_support_bonus + file_support_bonus + extra_support_bonus

    ccc_days = 75.0 if industry_profile == "manufacturing" else 45.0 if industry_profile == "service_it" else 60.0
    tenor_fit_score = 80.0 if requested_tenor_days >= ccc_days else 45.0
    ccc_fit_score = 78.0 if requested_tenor_days >= ccc_days else 42.0

    compliance_issue_text = " ".join(
        [
            *[str(item) for item in (state.get("consultingIssues") or [])],
            *[str(item) for item in (state.get("meetingIssues") or [])],
            *[str(item) for item in (state.get("internalReviewIssues") or [])],
            *[str(item) for item in (state.get("supportingDocumentIssues") or [])],
            *[str(item) for item in (state.get("additionalInfoIssues") or [])],
        ]
    )
    has_delinquency = any(keyword in compliance_issue_text for keyword in ["체납", "연체", "가압류", "소송"])
    compliance_base = 78.0 if not has_delinquency else 40.0

    applicant_external_base = max(45.0, applicant_grade_score)
    buyer_external_base = max(45.0, buyer_grade_score)

    # ── data_quality ──────────────────────────────────────────────────────
    _KEY_FIELDS = [
        "companyName", "representativeName", "businessNumber",
        "creditGrade", "annualSales", "buyerName", "supplierName",
        "requestedTenorDays", "reportIncorporatedDate",
    ]
    missing_fields: list[str] = []
    defaulted_fields: list[str] = []
    if not normalize_space(state.get("companyName")):
        missing_fields.append("companyName")
    if not normalize_space(state.get("representativeName")):
        missing_fields.append("representativeName")
    if not normalize_space(state.get("businessNumber")):
        missing_fields.append("businessNumber")
    if not credit_grade:
        missing_fields.append("creditGrade")
    if not annual_sales:
        missing_fields.append("annualSales")
        defaulted_fields.append("annualSales→0")
    if not normalize_space(state.get("buyerName")):
        missing_fields.append("buyerName")
        defaulted_fields.append("buyerName→'매출처 확인 필요'")
    if not normalize_space(state.get("supplierName")):
        missing_fields.append("supplierName")
        defaulted_fields.append("supplierName→'매입처 확인 필요'")
    if raw_tenor_days is None:
        missing_fields.append("requestedTenorDays")
        defaulted_fields.append("requestedTenorDays→60")
    if not state.get("reportIncorporatedDate"):
        missing_fields.append("reportIncorporatedDate")
        defaulted_fields.append("reportIncorporatedDate→businessYears=0")
    data_confidence = round(1.0 - len(missing_fields) / len(_KEY_FIELDS), 2)

    return {
        "analysis_type": "flowpay_underwriting",
        "engine_version": normalize_space(state.get("engineVersion")) or "v.local.learning",
        "company_name": company_name,
        "industry_profile": industry_profile,
        "requested_tenor_months": requested_tenor_months,
        "requested_purchase_amount_krw": base_monthly_limit_krw,
        "financials": {
            "annual_sales": annual_sales or 0,
            "operating_profit": operating_profit or 0,
            "net_profit": net_profit or 0,
            "operating_margin_pct": operating_margin_pct,
            "ebitda_interest_coverage": 2.5 if operating_profit and operating_profit > 0 else 0.8,
            "cash_conversion_cycle_days": ccc_days,
        },
        "screening": {
            "business_years": business_years or 0,
            "startup_fast_track_supported": False,
            "complete_capital_impairment": False,
            "tax_arrears": has_delinquency,
            "credit_grade": credit_grade,
            "recent_legal_action_within_years": 99.0,
            "industry_tag": industry_tag,
        },
        "ews_inputs": {
            "representative_credit_drop_notches": 0,
            "yoy_sales_drop_pct": yoy_sales_drop_pct(report_financial_summary),
            "short_term_debt_growth_pct": 0,
        },
        "proposal_context": {
            "representative_name": representative_name,
            "business_number": business_number,
            "supplier_name": supplier_name,
            "purchase_supplier_name": supplier_name,
            "sales_destination_name": buyer_name,
            "consulting_report_url": state.get("consultingReportUrl") or "",
            "meeting_report_url": state.get("meetingReportUrl") or "",
            "internal_review_url": state.get("internalReviewUrl") or "",
        },
        "api_enrichment": {
            "enabled": True,
            "applicant": {
                "ecos_industry_code": ecos_industry_code,
                "dart_corp_name": company_name,
            },
            "buyer": {
                "ecos_industry_code": ecos_industry_code,
                "dart_corp_name": buyer_name if buyer_name != "매출처 확인 필요" else "",
            },
        },
        "applicant": {
            "company_name": company_name,
            "scores": {
                "financial": {
                    "annual_sales_scale": 70.0 if annual_sales and annual_sales >= 10_000_000_000 else 58.0 if annual_sales else 40.0,
                    "revenue_stability": 72.0 if yoy_sales_drop_pct(report_financial_summary) < 10 else 50.0,
                    "operating_profitability": 75.0 if operating_profit and operating_profit > 0 else 38.0,
                    "net_profitability": 72.0 if net_profit and net_profit > 0 else 42.0,
                    "liquidity_cashflow": 68.0 if annual_sales else 45.0,
                    "leverage": 60.0,
                },
                "business": {
                    "onsite_business_alignment": 74.0,
                    "registry_business_alignment": 70.0,
                    "industry_condition": 62.0,
                    "business_model_resilience": 64.0,
                    "external_funding_validation": 55.0,
                    "customer_diversification": 60.0 if buyer_name == "매출처 확인 필요" else 68.0,
                },
                "management": {
                    "representative_execution": 72.0,
                    "actual_manager_match": 85.0 if representative_name != "확인 필요" else 55.0,
                    "shareholder_structure": 62.0,
                    "representative_history": 65.0,
                    "employee_history": 60.0,
                    "governance_control": 60.0,
                },
                "compliance": {
                    "national_tax_compliance": compliance_base,
                    "local_tax_compliance": compliance_base,
                    "four_insurance_compliance": compliance_base,
                    "trade_delinquency": 40.0 if has_delinquency else 72.0,
                    "loan_delinquency": 40.0 if has_delinquency else 72.0,
                    "legal_dispute_status": 45.0 if has_delinquency else 74.0,
                },
                "external": {
                    "corporate_credit_grade_signal": applicant_grade_score,
                    "dart_signal": applicant_external_base,
                    "ecos_signal": 58.0,
                    "cretop_signal": applicant_external_base,
                    "public_reputation": 62.0,
                    "employee_reputation": 58.0,
                },
            },
        },
        "buyer": {
            "company_name": buyer_name,
            "scores": {
                "financial": {
                    "buyer_revenue_scale": buyer_grade_score,
                    "buyer_profitability": buyer_grade_score - 4.0,
                    "buyer_liquidity": buyer_grade_score,
                    "buyer_leverage": max(35.0, buyer_grade_score - 8.0),
                    "buyer_cashflow": buyer_grade_score,
                },
                "business": {
                    "buyer_industry_condition": 65.0,
                    "buyer_business_stability": buyer_grade_score,
                    "buyer_market_position": buyer_grade_score,
                    "buyer_reputation": buyer_grade_score,
                    "buyer_registry_alignment": 60.0 if buyer_name == "매출처 확인 필요" else 75.0,
                },
                "payment": {
                    # payment_history: 미팅 결제 키워드 확인 시 상향 보정
                    "payment_history": (
                        55.0 if buyer_name == "매출처 확인 필요"
                        else 76.0 if _meeting_payment_score > 0
                        else 72.0
                    ),
                    # settlement_stability: 정산주기/조건 미팅 내용으로 세분화
                    "settlement_stability": (
                        58.0 if buyer_name == "매출처 확인 필요"
                        else 74.0 if _meeting_settlement_score > 0
                        else 70.0
                    ),
                    # invoice_acceptance_clarity: 상담/미팅 세금계산서 확인 반영
                    "invoice_acceptance_clarity": (
                        58.0 if not consultation_validation_summary and not _meeting_invoice_score
                        else 76.0 if _meeting_invoice_score > 0
                        else 72.0
                    ),
                    "dispute_setoff_risk": 52.0 if buyer_name == "매출처 확인 필요" else 65.0,
                    "concentration_risk": 50.0 if buyer_name == "매출처 확인 필요" else 62.0,
                    "delay_pattern": 52.0 if buyer_name == "매출처 확인 필요" else 68.0,
                },
                "external": {
                    "buyer_credit_grade_signal": buyer_grade_score,
                    "buyer_dart_signal": buyer_external_base,
                    "buyer_ecos_signal": 60.0,
                    "buyer_cretop_signal": buyer_external_base,
                    "buyer_funding_signal": 62.0 if buyer_name != "매출처 확인 필요" else 50.0,
                },
            },
        },
        "data_quality": {
            "missing_fields": missing_fields,
            "defaulted_fields": defaulted_fields,
            "data_confidence": data_confidence,
        },
        "transaction": {
            "scores": {
                "structure": {
                    "order_authenticity": min(85.0, 45.0 + structure_bonus),
                    "contract_enforceability": min(82.0, 42.0 + structure_bonus),
                    "delivery_verification": min(82.0, 40.0 + structure_bonus),
                    "invoice_proof": min(82.0, 40.0 + structure_bonus),
                    "recourse_strength": min(78.0, 38.0 + structure_bonus),
                    "fraud_control_strength": min(80.0, 42.0 + structure_bonus),
                },
                "tenor": {
                    "cash_conversion_cycle_fit": ccc_fit_score,
                    "requested_tenor_fit": tenor_fit_score,
                    "seller_survival_buffer": 62.0 if operating_profit and operating_profit > 0 else 45.0,
                    "buyer_survival_buffer": 58.0 if buyer_name == "매출처 확인 필요" else 68.0,
                    "emergency_liquidity_backstop": 50.0,
                },
                "macro": {
                    "industry_outlook": 58.0,
                    "macro_sensitivity": 52.0 if industry_profile == "manufacturing" else 60.0,
                    "commodity_volatility": 42.0 if "금속" in industry_text or "구리" in industry_text else 55.0,
                    "fx_or_policy_risk": 50.0 if "수출" in industry_text else 58.0,
                },
            },
        },
    }


def proposal_priority_from_grade(grade: str | None) -> str:
    normalized = normalize_space(grade)
    if normalized == "A":
        return "최상"
    if normalized in {"B+", "B"}:
        return "상"
    if normalized == "C+":
        return "중상"
    if normalized == "C":
        return "중"
    if normalized == "D":
        return "낮음"
    return "중"


def state_patch_from_context(context: dict[str, Any]) -> dict[str, Any]:
    proposal_context = context.get("proposal_context", {})
    sales_view = context.get("sales_view", {})
    risk_notes = sales_view.get("risk_notes", [])
    overall_grade = context.get("overall", {}).get("grade")
    requested_tenor_months = context.get("requested_tenor_months")
    requested_tenor_days = (
        context.get("industry_fit", {}).get("requested_tenor_days")
        or (requested_tenor_months * 30 if requested_tenor_months else None)
    )
    base_monthly_limit_krw = sales_view.get("base_monthly_limit_krw") or sales_view.get("reference_purchase_amount_krw")
    engine_adjusted_limit_krw = (
        sales_view.get("engine_adjusted_limit_krw")
        or sales_view.get("raw_estimated_limit_krw")
        or sales_view.get("estimated_limit_krw")
    )
    learning_operational_limit_krw = sales_view.get("learning_operational_limit_krw")
    engine_adjusted_limit_text = format_krw(engine_adjusted_limit_krw)

    return {
        "engineVersion": context.get("engine_version", "업로드 결과"),
        "companyName": context.get("company_name"),
        "shortName": context.get("company_name"),
        "representativeName": proposal_context.get("representative_name"),
        "proposalPriority": proposal_priority_from_grade(overall_grade),
        "currentProposalState": sales_view.get("recommendation"),
        "heroNextAction": sales_view.get("next_action"),
        "nextAction": str(sales_view.get("next_action", "")).replace("\n", "<br />"),
        "requestedTenorMonths": requested_tenor_months,
        "requestedTenorDays": requested_tenor_days,
        "recommendedTenorText": format_tenor_text(requested_tenor_months, requested_tenor_days),
        "reportMonthlyCreditLimit": format_krw(base_monthly_limit_krw),
        "baseMonthlyLimitLabel": "기준 월간 적정 한도",
        "baseMonthlyLimitValue": format_krw(base_monthly_limit_krw),
        "estimatedLimitLabel": "엔진 보정 한도",
        "estimatedLimitValue": engine_adjusted_limit_text,
        "engineAdjustedLimitLabel": "엔진 보정 한도",
        "engineAdjustedLimitValue": engine_adjusted_limit_text,
        "learningOperationalLimitLabel": "학습모드 운영 한도(주간 1회 기준)",
        "learningOperationalLimitValue": format_krw(learning_operational_limit_krw),
        "estimatedMarginValue": format_percent(sales_view.get("estimated_margin_rate_pct")),
        "financialFilterSignal": context.get("applicant", {}).get("grade") or context.get("overall", {}).get("grade"),
        "cashflowSignal": risk_notes[0] if risk_notes else "확인 필요",
        "overviewSummary": context.get("sales_summary"),
        "proposal": {
            "executive": (
                f"{context.get('company_name', '기업')} 관련 영업 참고 결과는 "
                f"'{sales_view.get('recommendation', '추가 확인 필요')}'입니다. "
                f"엔진 보정 한도는 {engine_adjusted_limit_text} 수준입니다."
            ),
            "company": (
                f"신청업체 참고등급은 {context.get('applicant', {}).get('grade', '-')}, "
                f"매출처 참고등급은 {context.get('buyer', {}).get('grade', '-')}, "
                f"거래구조 참고등급은 {context.get('transaction', {}).get('grade', '-')}, "
                f"통합 참고등급은 {context.get('overall', {}).get('grade', '-')}입니다."
            ),
            "structure": (
                f"엔진 보정 한도는 {engine_adjusted_limit_text}, "
                f"예상 마진율은 {format_percent(sales_view.get('estimated_margin_rate_pct'))} 수준입니다."
            ),
            "risks": " ".join(risk_notes) if risk_notes else "",
            "next": sales_view.get("next_action", ""),
        },
        "email": {
            "subject": f"{context.get('company_name', '기업')} 관련 제안드립니다",
            "bodyLines": str(context.get("sales_email_draft", "")).split("\n"),
        },
    }


def exhibition_state_patch_from_extract(
    exhibition_info_url: str,
    website_url: str,
    exhibition_name: str,
    exhibition_year: int,
    company_name: str,
    representative_name: str | None,
    business_number: str | None,
    industry_item: str,
    website_snapshot: dict[str, str],
    exhibition_snapshot: dict[str, str],
) -> dict[str, Any]:
    short_name = infer_short_name(company_name) or company_name
    website_summary = (
        website_snapshot.get("description")
        or website_snapshot.get("h1")
        or website_snapshot.get("title")
        or "홈페이지 공개 정보를 기준으로 사업 내용을 확인했습니다."
    )
    exhibition_summary = (
        exhibition_snapshot.get("h1")
        or exhibition_snapshot.get("title")
        or exhibition_snapshot.get("description")
        or "전시회 참여 정보를 기준으로 공개 근거를 확인했습니다."
    )
    return {
        "mode": "exhibition",
        "exhibitionInfoUrl": exhibition_info_url,
        "website": website_url,
        "exhibitionName": exhibition_name,
        "exhibitionYear": exhibition_year,
        "companyName": company_name,
        "shortName": short_name,
        "representativeName": representative_name,
        "businessNumber": business_number,
        "industryItem": industry_item,
        "overviewSummary": (
            f"{company_name} 관련 공개 정보는 전시회 URL과 기업 홈페이지를 기준으로 자동 정리했습니다. "
            "추출이 부족한 경우에는 업로드한 기업리포트를 보조 근거로 반영합니다."
        ),
        "websiteSummary": website_summary,
        "exhibitionSummary": exhibition_summary,
    }


@app.get("/")
def root() -> RedirectResponse:
    return RedirectResponse(url="/web/bizaipro_home.html")


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {"ok": True, "service": "BizAiPro Web API"}


@app.get("/api/engine-presets")
def engine_presets() -> dict[str, Any]:
    registry = load_dashboard_registry()
    current_version = normalize_engine_version(registry.get("current_version") or ENGINE_PRESETS["latest"]["engine_version"])
    latest = dict(ENGINE_PRESETS["latest"])
    latest["label"] = f"최신 엔진 {current_version}"
    latest["engine_version"] = current_version
    return {
        "items": [latest, ENGINE_PRESETS["previous"], ENGINE_PRESETS["base"]],
    }


@app.get("/api/dashboard")
def dashboard_summary() -> dict[str, Any]:
    registry = load_dashboard_registry()
    cases = sort_learning_cases(registry.get("cases", []))
    updates = registry.get("updates", [])
    latest_update = updates[-1] if updates else {}

    learned_company_reports = sum(
        1
        for case in cases
        if float((case.get("learning", {}).get("components", {}) or {}).get("flow_score_report", 0) or 0) > 0
    )
    learned_consultations = sum(
        1
        for case in cases
        if float((case.get("learning", {}).get("components", {}) or {}).get("consultation_report", 0) or 0) > 0
    )
    learned_internal_reviews = sum(
        1
        for case in cases
        if float((case.get("learning", {}).get("components", {}) or {}).get("internal_review", 0) or 0) > 0
    )

    current_version = registry.get("current_version", "v.1.0.00")
    latest_update_progress = latest_update.get("progress", {}) if isinstance(latest_update, dict) else {}
    current_version_qualified = sum(
        1
        for case in cases
        if normalize_engine_version(case.get("engine_version")) == normalize_engine_version(current_version)
        and bool((case.get("learning") or {}).get("update_eligible"))
    )
    current_version_weighted_total = round(
        sum(
            float((case.get("learning") or {}).get("update_weight") or 0)
            for case in cases
            if normalize_engine_version(case.get("engine_version")) == normalize_engine_version(current_version)
            and bool((case.get("learning") or {}).get("update_eligible"))
        ),
        2,
    )

    return {
        "engine_name": registry.get("engine_name", "BizAiPro"),
        "current_version": normalize_engine_version(current_version),
        "learning_cards": {
            "company_reports": learned_company_reports,
            "consultation_reports": learned_consultations,
            "internal_reviews": learned_internal_reviews,
        },
        "engine_traits": infer_engine_traits(current_version),
        "latest_update": {
            "version": latest_update.get("version", current_version),
            "created_at": latest_update.get("created_at", ""),
            "qualified_cases": latest_update_progress.get("qualified_cases", current_version_qualified),
            "weighted_total": latest_update_progress.get("weighted_total", current_version_weighted_total),
            "update_generated": latest_update.get("update_generated", False),
        },
        "recent_learning_cases": [serialize_learning_case(case) for case in cases[:5]],
        "total_learning_cases": len(cases),
    }


@app.get("/api/learning/cases")
def learning_cases(offset: int = 0, limit: int = 5) -> dict[str, Any]:
    registry = load_dashboard_registry()
    cases = sort_learning_cases(registry.get("cases", []))
    safe_offset = max(0, int(offset))
    safe_limit = max(1, min(int(limit), 50))
    sliced = cases[safe_offset : safe_offset + safe_limit]
    return {
        "items": [serialize_learning_case(case) for case in sliced],
        "offset": safe_offset,
        "limit": safe_limit,
        "total": len(cases),
        "has_more": safe_offset + safe_limit < len(cases),
    }


@app.get("/api/learning/cases/{case_id}")
def learning_case_detail(case_id: str) -> dict[str, Any]:
    registry = load_dashboard_registry()
    cases = registry.get("cases", [])
    case = next((item for item in cases if normalize_space(str(item.get("id"))) == normalize_space(case_id)), None)
    if case is None:
        raise HTTPException(status_code=404, detail="학습 케이스를 찾지 못했습니다.")
    return {
        "case": serialize_learning_case(case),
        "state_patch": build_learning_case_state(case),
        "result_snapshot": case.get("result_snapshot") or {},
        "detail_report": build_evaluation_detail_report(case),
    }


@app.post("/api/web-context/parse")
async def parse_web_context(file: UploadFile = File(...)) -> dict[str, Any]:
    try:
        raw = await file.read()
        context = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=400, detail="유효한 web_context.json이 아닙니다.") from exc

    return {
        "raw_context": context,
        "state_patch": state_patch_from_context(context),
    }


@app.post("/api/report/flowscore-parse")
async def parse_flowscore_report(
    file: UploadFile = File(...),
    auto_notion_lookup: bool = Form(False),
) -> dict[str, Any]:
    """FlowScore PDF를 파싱한다.

    auto_notion_lookup=True 시, 추출된 회사명·사업자번호로 Notion 3종 보고서를
    자동 조회·파싱하여 응답에 notion_lookup 포함.
    """
    raw_bytes = await file.read()
    if not raw_bytes:
        raise HTTPException(status_code=400, detail="리포트 파일이 비어 있습니다.")

    try:
        parsed = parse_flowscore_report_pdf(raw_bytes, source_file=file.filename)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="FlowScore 리포트를 읽지 못했습니다.") from exc

    state_patch = apply_report_enrichment({}, parsed)
    response: dict[str, Any] = {
        "parsed_report": parsed,
        "state_patch": state_patch,
    }

    if auto_notion_lookup:
        company_name = normalize_space(
            parsed.get("company_name") or state_patch.get("companyName") or ""
        )
        business_number = normalize_space(
            parsed.get("business_number") or state_patch.get("businessNumber") or ""
        ) or None
        lookup = notion_auto_lookup(company_name, business_number)
        notion_state_patch = build_notion_lookup_state_patch(lookup)
        # FlowScore state_patch와 notion 결과 병합 (FlowScore가 우선)
        merged_patch = {**notion_state_patch, **state_patch}
        response["state_patch"] = merged_patch
        response["notion_lookup"] = lookup
        response["missing_notion_reports"] = lookup.get("missing_notion_reports") or []
        response["requires_user_decision"] = lookup.get("requires_user_decision", False)

    return response


@app.post("/api/notion/auto-lookup-and-parse")
async def notion_auto_lookup_and_parse(
    company_name: str = Form(...),
    business_number: str = Form(""),
) -> dict[str, Any]:
    """회사명·사업자번호로 Notion 보고서 3종을 자동 조회·파싱한다.

    FlowScore 업로드 없이 온디맨드 재조회 시 사용.
    found_and_parsed 항목의 state_patch를 포함해 반환.
    """
    company_name = company_name.strip()
    biz_num = business_number.strip() or None
    if not company_name:
        raise HTTPException(status_code=400, detail="company_name이 비어 있습니다.")

    lookup = notion_auto_lookup(company_name, biz_num)
    notion_state_patch = build_notion_lookup_state_patch(lookup)
    return {
        "notion_lookup": lookup,
        "state_patch": notion_state_patch,
        "missing_notion_reports": lookup.get("missing_notion_reports") or [],
        "requires_user_decision": lookup.get("requires_user_decision", False),
    }


@app.post("/api/consulting/parse")
async def parse_consulting_report(
    consulting_url: str = Form(...),
    company_name: str = Form(""),
    business_number: str = Form(""),
    representative_name: str = Form(""),
) -> dict[str, Any]:
    consulting_url = consulting_url.strip()
    if not consulting_url:
        raise HTTPException(status_code=400, detail="상담보고서 링크가 비어 있습니다.")

    try:
        parsed = parse_consulting_report_url(
            consulting_url,
            fallback_company_name=company_name.strip() or None,
            fallback_business_number=business_number.strip() or None,
            fallback_representative_name=representative_name.strip() or None,
        )
    except requests.RequestException as exc:
        raise HTTPException(status_code=400, detail="상담보고서 링크를 불러오지 못했습니다.") from exc

    state_patch = apply_consulting_enrichment({}, parsed, state_prefix="consulting", source_display_label="상담보고서")
    return {
        "parsed_consulting_report": parsed,
        "state_patch": state_patch,
    }


@app.post("/api/meeting/parse")
async def parse_meeting_report(
    meeting_url: str = Form(...),
    company_name: str = Form(""),
    business_number: str = Form(""),
    representative_name: str = Form(""),
) -> dict[str, Any]:
    meeting_url = meeting_url.strip()
    if not meeting_url:
        raise HTTPException(status_code=400, detail="미팅보고서 링크가 비어 있습니다.")

    try:
        parsed = parse_consulting_report_url(
            meeting_url,
            fallback_company_name=company_name.strip() or None,
            fallback_business_number=business_number.strip() or None,
            fallback_representative_name=representative_name.strip() or None,
            source_label="미팅보고서",
        )
    except requests.RequestException as exc:
        raise HTTPException(status_code=400, detail="미팅보고서 링크를 불러오지 못했습니다.") from exc

    state_patch = apply_consulting_enrichment({}, parsed, state_prefix="meeting", source_display_label="미팅보고서")
    return {
        "parsed_meeting_report": parsed,
        "state_patch": state_patch,
    }


@app.post("/api/internal-review/parse")
async def parse_internal_review(
    review_url: str = Form(...),
    company_name: str = Form(""),
    business_number: str = Form(""),
    representative_name: str = Form(""),
) -> dict[str, Any]:
    review_url = review_url.strip()
    if not review_url:
        raise HTTPException(status_code=400, detail="심사보고서 링크가 비어 있습니다.")

    try:
        parsed = parse_consulting_report_url(
            review_url,
            fallback_company_name=company_name.strip() or None,
            fallback_business_number=business_number.strip() or None,
            fallback_representative_name=representative_name.strip() or None,
            source_label="심사보고서",
        )
    except requests.RequestException as exc:
        raise HTTPException(status_code=400, detail="심사보고서 링크를 불러오지 못했습니다.") from exc

    state_patch = apply_internal_review_enrichment({}, parsed)
    return {
        "parsed_internal_review": parsed,
        "state_patch": state_patch,
    }


@app.post("/api/supporting-document/parse")
async def parse_supporting_document(
    label: str = Form("보조자료"),
    company_name: str = Form(""),
    business_number: str = Form(""),
    representative_name: str = Form(""),
    file: UploadFile = File(...),
) -> dict[str, Any]:
    raw_bytes = await file.read()
    if not raw_bytes:
        raise HTTPException(status_code=400, detail="보조자료 파일이 비어 있습니다.")

    text = extract_report_text(raw_bytes)
    parsed = parse_supporting_text_block(
        text,
        source_label=label.strip() or "보조자료",
        fallback_company_name=company_name.strip() or None,
        fallback_business_number=business_number.strip() or None,
        fallback_representative_name=representative_name.strip() or None,
    )
    parsed["source_file"] = file.filename
    return {
        "parsed_document": parsed,
        "state_patch": apply_supporting_file_enrichment({}, parsed, "supportingDocument"),
    }


@app.post("/api/additional-info/parse")
async def parse_additional_info(
    text: str = Form(""),
    company_name: str = Form(""),
    business_number: str = Form(""),
    representative_name: str = Form(""),
) -> dict[str, Any]:
    parsed = parse_supporting_text_block(
        text,
        source_label="추가 정보",
        fallback_company_name=company_name.strip() or None,
        fallback_business_number=business_number.strip() or None,
        fallback_representative_name=representative_name.strip() or None,
    )
    return {
        "parsed_additional_info": parsed,
        "state_patch": apply_additional_info_enrichment({}, parsed),
    }


@app.post("/api/exhibition/extract")
async def extract_exhibition_fields(
    exhibition_info_url: str = Form(""),
    website_url: str = Form(""),
    report_file: UploadFile | None = File(default=None),
) -> dict[str, Any]:
    if not exhibition_info_url and not website_url:
        raise HTTPException(status_code=400, detail="전시회 정보 URL 또는 기업 웹주소 URL이 필요합니다.")

    exhibition_snapshot: dict[str, str] = {}
    website_snapshot: dict[str, str] = {}
    report_text = ""
    parsed_report: dict[str, Any] | None = None

    try:
        if exhibition_info_url:
            exhibition_snapshot = fetch_page_snapshot(exhibition_info_url)
        if website_url:
            website_snapshot = fetch_page_snapshot(website_url)
    except requests.RequestException as exc:
        raise HTTPException(status_code=400, detail="URL 정보를 불러오지 못했습니다.") from exc

    if report_file is not None:
        raw_bytes = await report_file.read()
        report_text = extract_report_text(raw_bytes)
        try:
            parsed_report = parse_flowscore_report_pdf(raw_bytes, source_file=report_file.filename)
        except Exception:
            parsed_report = None

    year = infer_exhibition_year(
        exhibition_snapshot.get("title", ""),
        exhibition_snapshot.get("og_title", ""),
        exhibition_snapshot.get("body", ""),
        exhibition_info_url,
    )
    exhibition_name = infer_exhibition_name(exhibition_snapshot, year)
    company_name = infer_company_name(website_snapshot, exhibition_snapshot, report_text)
    representative_name = infer_representative_name(report_text)
    business_number = infer_business_number(report_text)
    industry_item = infer_industry_item(website_snapshot, report_text)

    if parsed_report:
        company_name = parsed_report.get("company_name") or company_name
        representative_name = parsed_report.get("representative_name") or representative_name
        business_number = parsed_report.get("business_number") or business_number

    if not company_name:
        raise HTTPException(status_code=422, detail="기업명을 자동 추출하지 못했습니다. 기업리포트를 함께 넣어주세요.")

    state_patch = exhibition_state_patch_from_extract(
        exhibition_info_url=exhibition_info_url,
        website_url=website_url,
        exhibition_name=exhibition_name,
        exhibition_year=year,
        company_name=company_name,
        representative_name=representative_name,
        business_number=business_number,
        industry_item=industry_item,
        website_snapshot=website_snapshot,
        exhibition_snapshot=exhibition_snapshot,
    )
    if parsed_report:
        state_patch = apply_report_enrichment(state_patch, parsed_report)

    return {
        "extracted": {
            "company_name": company_name,
            "short_name": infer_short_name(company_name) or company_name,
            "exhibition_name": exhibition_name,
            "exhibition_year": year,
            "representative_name": representative_name,
            "business_number": business_number,
            "industry_item": industry_item,
            "website_title": website_snapshot.get("title", ""),
            "exhibition_title": exhibition_snapshot.get("title", ""),
            "used_report_fallback": bool(report_text),
        },
        "state_patch": state_patch,
        "parsed_report": parsed_report,
    }


@app.post("/api/evaluate")
async def evaluate(payload: dict[str, Any]) -> dict[str, Any]:
    framework = load_active_framework()
    analysis_type = payload.get("analysis_type")
    if analysis_type != "flowpay_underwriting":
        raise HTTPException(status_code=400, detail="현재는 flowpay_underwriting만 지원합니다.")

    result = evaluate_flowpay_underwriting(payload, framework)
    context = build_web_context(payload, result)
    return {
        "result": result,
        "web_context": context,
        "state_patch": state_patch_from_context(context),
        "framework_meta": get_active_framework_meta(),
    }


@app.post("/api/learning/evaluate")
async def evaluate_learning_mode(payload: dict[str, Any]) -> dict[str, Any]:
    state = payload.get("state") or {}
    framework = load_active_framework()
    engine_input = build_learning_evaluation_payload(state)
    result = evaluate_flowpay_underwriting(engine_input, framework)
    context = normalize_learning_context_for_display(build_web_context(engine_input, result))
    state_patch = apply_learning_engine_state_patch(state, context)
    registry = record_live_learning_case(state, state_patch, engine_input, result, context)
    dq = engine_input.get("data_quality") or {}
    data_confidence = float(dq.get("data_confidence", 1.0))
    data_quality_warning = None
    if data_confidence < 0.7:
        data_quality_warning = {
            "level": "conditional",
            "message": "조건부 평가 — 자료 보완 필요",
            "data_confidence": data_confidence,
            "missing_fields": dq.get("missing_fields", []),
        }
    return {
        "engine_input": engine_input,
        "result": result,
        "web_context": context,
        "state_patch": state_patch,
        "dashboard_summary": dashboard_summary(),
        "registry_size": len(registry.get("cases", [])),
        "framework_meta": get_active_framework_meta(),
        "data_quality_warning": data_quality_warning,
    }


def apply_learning_engine_state_patch(
    state: dict[str, Any],
    context: dict[str, Any],
) -> dict[str, Any]:
    state_patch = state_patch_from_context(context)
    report_grade = normalize_space(state.get("reportCreditGrade") or state.get("financialFilterSignal"))
    if report_grade:
        state_patch["financialFilterSignal"] = report_grade
        state_patch["reportCreditGrade"] = report_grade
    if state.get("recentRevenueLabel"):
        state_patch["recentRevenueLabel"] = state.get("recentRevenueLabel")
    if state.get("recentRevenueValue"):
        state_patch["recentRevenueValue"] = state.get("recentRevenueValue")
    if state.get("operatingProfitLabel"):
        state_patch["operatingProfitLabel"] = state.get("operatingProfitLabel")
    if state.get("operatingProfitValue"):
        state_patch["operatingProfitValue"] = state.get("operatingProfitValue")
    if state.get("netIncomeLabel"):
        state_patch["netIncomeLabel"] = state.get("netIncomeLabel")
    if state.get("netIncomeValue"):
        state_patch["netIncomeValue"] = state.get("netIncomeValue")
    if not parse_krw_text_to_int(state.get("recentRevenueValue")):
        state_patch["estimatedLimitValue"] = "추가 확인 필요"
    if state.get("requestedTenorDays"):
        state_patch["requestedTenorDays"] = int(state.get("requestedTenorDays"))
        state_patch["recommendedTenorText"] = format_tenor_text(
            state_patch.get("requestedTenorMonths"),
            state.get("requestedTenorDays"),
        )
    if not parse_krw_text_to_int(state_patch.get("baseMonthlyLimitValue")) and state.get("reportMonthlyCreditLimit"):
        state_patch["reportMonthlyCreditLimit"] = normalize_limit_display_text(state.get("reportMonthlyCreditLimit"))
        state_patch["baseMonthlyLimitLabel"] = "기준 월간 적정 한도"
        state_patch["baseMonthlyLimitValue"] = normalize_limit_display_text(state.get("reportMonthlyCreditLimit"))
    learning_status = learning_status_from_components(learning_material_components(state))
    state_patch["learningEligible"] = learning_status_label(learning_status)
    state_patch["learningWeight"] = (
        f"{learning_status['update_weight']:.2f}"
        if learning_status["update_eligible"]
        else f"{learning_status['evaluation_weight']:.2f}"
    )
    return state_patch


def refresh_learning_case_from_sources(case: dict[str, Any], framework: dict[str, Any]) -> dict[str, Any]:
    normalized_case = normalize_learning_case(case)
    sources = normalized_case.get("sources") or {}
    flow_score_file_name = normalize_space(sources.get("flow_score_file_name"))
    if not flow_score_file_name:
        return normalized_case

    report_path = locate_downloads_file(flow_score_file_name)
    if not report_path or not report_path.is_file():
        return normalized_case

    try:
        parsed_report = parse_flowscore_report_pdf(report_path.read_bytes(), source_file=flow_score_file_name)
    except Exception:
        return normalized_case

    base_state = dict(normalized_case.get("state_snapshot") or {})
    base_state["mode"] = "learning"
    base_state["learningFlowScoreFileName"] = flow_score_file_name
    if normalize_space(sources.get("consulting_report_url")):
        base_state["consultingReportUrl"] = normalize_space(sources.get("consulting_report_url"))
    if normalize_space(sources.get("meeting_report_url")):
        base_state["meetingReportUrl"] = normalize_space(sources.get("meeting_report_url"))
    if normalize_space(sources.get("consulting_file_name")):
        base_state["learningConsultingFileName"] = normalize_space(sources.get("consulting_file_name"))
    if normalize_space(sources.get("internal_review_url")):
        base_state["internalReviewUrl"] = normalize_space(sources.get("internal_review_url"))
    if normalize_space(sources.get("additional_info")):
        base_state["learningExtraInfo"] = normalize_space(sources.get("additional_info"))

    refreshed_state = apply_report_enrichment(base_state, parsed_report)
    for key in [
        "consultingValidationSummary",
        "consultingSummary",
        "consultingCrossChecks",
        "consultingIssues",
        "meetingValidationSummary",
        "meetingSummary",
        "meetingCrossChecks",
        "meetingIssues",
        "internalReviewValidationSummary",
        "internalReviewSummary",
        "internalReviewCrossChecks",
        "internalReviewIssues",
        "supportingDocumentSummary",
        "supportingDocumentIssues",
        "additionalInfoSummary",
        "additionalInfoIssues",
        "supplierName",
        "buyerName",
        "requestedTenorDays",
        "requestedTenorMonths",
    ]:
        if key in base_state and base_state.get(key) not in (None, "", [], {}):
            refreshed_state[key] = base_state.get(key)

    engine_input = build_learning_evaluation_payload(refreshed_state)
    result = evaluate_flowpay_underwriting(engine_input, framework)
    context = normalize_learning_context_for_display(build_web_context(engine_input, result))
    state_patch = apply_learning_engine_state_patch(refreshed_state, context)

    normalized_case["engine_input_snapshot"] = engine_input
    normalized_case["web_context_snapshot"] = context
    normalized_case["result_snapshot"] = result
    normalized_case["state_snapshot"] = merge_non_empty_dict(normalized_case.get("state_snapshot") or {}, state_patch)
    normalized_case["state_snapshot"]["mode"] = "learning"
    return normalize_learning_case(normalized_case)


def refresh_registry_cases_from_sources(registry: dict[str, Any], path: Path) -> dict[str, Any]:
    cases = registry.get("cases", [])
    if not cases:
        return registry
    framework = load_active_framework()
    refreshed_cases = [refresh_learning_case_from_sources(case, framework) for case in cases]
    refreshed_registry = dict(registry)
    refreshed_registry["cases"] = refreshed_cases
    refreshed_registry = normalize_dashboard_registry(refreshed_registry)
    if refreshed_registry != registry:
        save_live_learning_registry(refreshed_registry, path)
    return refreshed_registry


# ============================================================
# D3 — EvaluationSnapshot API (Phase 1)
# ============================================================
# 문서번호: FBU-PLAN-V2-D5-D4-MASTER-20260501 §3
# 출처: [claude]flowbiz_ui_v2_standalone_design_implementation_plan_v7
# 누적 codex Findings 반영:
#   v3 F1 P1: Pydantic BaseModel + Content-Type
#   v3 F2 P1: ExhibitionLeadSnapshot (FPE 미실행)
#   v4 F1 P1: uuid.uuid4().hex (ulid 의존성 제거)
#   v4 F2 P1: UnsafeRawSnapshotForTest (Pydantic 우회 raw fixture)
#   v5 F4 P2: test 디렉토리 격리 (data/test_evaluation_reports)
# ============================================================
import uuid
from typing import Literal, Optional
from pydantic import BaseModel, Field, ConfigDict


def _new_id() -> str:
    """v4 표준 — Python 표준 라이브러리 uuid (외부 의존성 0)"""
    return uuid.uuid4().hex


def get_snapshot_dir() -> Path:
    """환경별 snapshot 저장 디렉토리 (v5 §11.5 정정)

    - production: data/evaluation_reports/
    - test:       data/test_evaluation_reports/ (또는 FLOWBIZ_TEST_SNAPSHOT_DIR)
    """
    if os.getenv("FLOWBIZ_ENV") == "test":
        custom = os.getenv("FLOWBIZ_TEST_SNAPSHOT_DIR")
        if custom:
            return Path(custom)
        return Path("data/test_evaluation_reports")
    return Path("data/evaluation_reports")


# ====================================================
# Pydantic 모델 (v3 §7.1, v4 §7)
# ====================================================
class EvaluationSnapshot(BaseModel):
    """FPE가 실제 실행된 평가 결과 — v3 F2 P2 분리"""
    model_config = ConfigDict(extra="allow")

    report_id: str = Field(default_factory=_new_id)
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    company_name: str = ""
    state_key: str = ""
    server_input_hash: str = ""

    decision_source: Literal["FPE"] = "FPE"
    evaluation_status: Literal["evaluated"] = "evaluated"
    fpe_version: str = ""
    ape_version: str = ""

    # FPE 결과 (제안서/이메일 기준)
    fpe_flow_score: int = 0
    fpe_credit_limit: int = 0
    fpe_margin_rate: float = 0.0
    fpe_payment_grace_days: int = 0
    fpe_knockout_reasons: list[str] = []
    proposal_allowed: bool = False
    blocked_reason: Optional[str] = None

    # APE 비교 (참고)
    ape_flow_score: int = 0
    ape_credit_limit: int = 0
    ape_margin_rate: float = 0.0
    ape_diff_summary: dict = {}

    consensus: Literal["both_go", "fpe_blocked", "ape_only_positive", "ape_blocked", "both_review"] = "both_review"
    source_quality: dict = {}


class ExhibitionLeadSnapshot(BaseModel):
    """전시회 사전평가 — FPE 미실행 (v3 F2 P1)"""
    lead_id: str = Field(default_factory=_new_id)
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    company_name: str
    exhibition_name: str
    exhibition_year: int
    industry: str
    homepage: Optional[str] = None
    contact_name: Optional[str] = None

    decision_source: Optional[str] = None  # FPE 미실행 — null
    evaluation_status: Literal["not_evaluated"] = "not_evaluated"
    proposal_allowed: bool = False
    blocked_reason: str = "기업리포트/FlowScore 미연결"
    required_actions: list[str] = [
        "기업리포트 업로드",
        "FlowScore 자동 조회 시도",
        "관리자에게 추가 심사 요청",
    ]


class ProposalSnapshot(BaseModel):
    proposal_id: str = Field(default_factory=_new_id)
    report_id: str
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    company_name: str
    credit_limit: int
    margin_rate: float
    payment_grace_days: int
    template_variant: str = "standard"


class EvaluationReportRequest(BaseModel):
    state: dict
    force_recreate: bool = False
    notes: Optional[str] = None


class ProposalGenerateRequest(BaseModel):
    report_id: str
    template_variant: Literal["standard", "exhibition"] = "standard"
    notes: Optional[str] = None


class UnsafeRawSnapshotForTest(BaseModel):
    """⚠ TEST ONLY — Pydantic 검증 우회 raw fixture (v4 F2 P1)

    잘못된 decision_source, 누락 필드 등 시뮬레이션용.
    production 환경에서는 라우트 등록 안 됨 (FLOWBIZ_ENV=test 가드).
    """
    model_config = ConfigDict(extra="allow")
    report_id: str
    decision_source: Optional[str] = None  # Literal 강제 없음 — test 의도
    evaluation_status: Optional[str] = None
    proposal_allowed: Optional[bool] = None


# ====================================================
# Snapshot 저장/로드 헬퍼
# ====================================================
def save_evaluation_snapshot(snapshot_data: dict) -> Path:
    """raw dict 저장 (production 또는 test)"""
    snapshot_dir = get_snapshot_dir()
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    path = snapshot_dir / f"{snapshot_data['report_id']}.json"
    path.write_text(json.dumps(snapshot_data, default=str, ensure_ascii=False))
    return path


def load_evaluation_snapshot_raw(report_id: str) -> dict:
    """raw load (정책 검증 전)"""
    snapshot_dir = get_snapshot_dir()
    path = snapshot_dir / f"{report_id}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"snapshot not found: {report_id}")
    return json.loads(path.read_text())


def load_evaluation_snapshot_validated(report_id: str) -> EvaluationSnapshot:
    """raw load + 정책 검증 (v4 §11.2)"""
    raw = load_evaluation_snapshot_raw(report_id)

    # decision_source 강제 (§3.3 #1)
    if raw.get("decision_source") != "FPE":
        raise HTTPException(
            status_code=400,
            detail=f"decision_source must be FPE (got: {raw.get('decision_source')})",
        )

    # FPE 필수 필드 검증
    required = ["fpe_credit_limit", "fpe_margin_rate", "fpe_payment_grace_days"]
    missing = [f for f in required if raw.get(f) is None]
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"missing required fields: {missing}",
        )

    return EvaluationSnapshot(**raw)


# ====================================================
# API 엔드포인트
# ====================================================
@app.post("/api/evaluation/report", response_model=EvaluationSnapshot)
async def create_evaluation_report(req: EvaluationReportRequest):
    """평가보고서 생성 + EvaluationSnapshot 저장 (Phase 1)

    1차 PR 머지 후 dual eval 호출로 전환 예정.
    현재는 단일 FPE 평가 + APE는 동일 결과 임시 사용.
    """
    framework = load_active_framework()
    framework_meta = get_active_framework_meta()
    engine_input = build_learning_evaluation_payload(req.state)
    result = evaluate_flowpay_underwriting(engine_input, framework)

    company_name = (
        req.state.get("company_name")
        or req.state.get("companyName")
        or engine_input.get("company_name", "")
    )

    server_input_hash = hashlib.sha256(
        json.dumps(engine_input, sort_keys=True, default=str).encode()
    ).hexdigest()[:16]

    fpe_score = int(result.get("flow_score") or 0)
    fpe_credit_limit = int(result.get("credit_limit") or 0)
    fpe_margin_rate = float(result.get("margin_rate") or 0.0)
    fpe_grace = int(result.get("payment_grace_days") or 0)
    knockout_reasons = result.get("knockout_reasons") or []
    proposal_allowed = not knockout_reasons

    consensus: Literal["both_go", "fpe_blocked", "ape_only_positive", "ape_blocked", "both_review"]
    if proposal_allowed:
        consensus = "both_go"
    else:
        consensus = "fpe_blocked"

    snapshot = EvaluationSnapshot(
        company_name=str(company_name),
        state_key=str(req.state.get("learningCaseId") or req.state.get("state_key") or ""),
        server_input_hash=server_input_hash,
        decision_source="FPE",
        evaluation_status="evaluated",
        fpe_version=framework_meta.get("version", "FPE_v.16.01") if isinstance(framework_meta, dict) else "FPE_v.16.01",
        ape_version="APE_v1.01",
        fpe_flow_score=fpe_score,
        fpe_credit_limit=fpe_credit_limit,
        fpe_margin_rate=fpe_margin_rate,
        fpe_payment_grace_days=fpe_grace,
        fpe_knockout_reasons=list(knockout_reasons),
        proposal_allowed=proposal_allowed,
        blocked_reason=knockout_reasons[0] if knockout_reasons else None,
        ape_flow_score=fpe_score,  # 1차 PR 머지 전 — FPE와 동일
        ape_credit_limit=fpe_credit_limit,
        ape_margin_rate=fpe_margin_rate,
        ape_diff_summary={"note": "1차 PR dual eval 머지 전 임시"},
        consensus=consensus,
        source_quality={},
    )

    save_evaluation_snapshot(snapshot.model_dump())
    return snapshot


@app.get("/api/evaluation/report/{report_id}", response_model=EvaluationSnapshot)
async def get_evaluation_report(report_id: str):
    """저장된 snapshot 조회 (정책 검증 포함)"""
    return load_evaluation_snapshot_validated(report_id)


@app.get("/api/evaluation/reports")
async def list_evaluation_reports(limit: int = 20):
    """snapshot 목록 (최근 N건)"""
    snapshot_dir = get_snapshot_dir()
    if not snapshot_dir.exists():
        return {"reports": [], "total": 0}

    files = sorted(
        snapshot_dir.glob("*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )[:limit]

    reports = []
    for f in files:
        try:
            raw = json.loads(f.read_text())
            reports.append(raw)
        except Exception:
            continue

    return {"reports": reports, "total": len(reports)}


@app.post("/api/proposal/generate", response_model=ProposalSnapshot)
async def generate_proposal(req: ProposalGenerateRequest):
    """snapshot 기반 제안서 — FPE 강제 (§3.3 #1-#2)"""
    snapshot = load_evaluation_snapshot_validated(req.report_id)

    if not snapshot.proposal_allowed:
        raise HTTPException(
            status_code=403,
            detail=f"FPE blocked: {snapshot.blocked_reason}",
        )

    return ProposalSnapshot(
        report_id=req.report_id,
        company_name=snapshot.company_name,
        credit_limit=snapshot.fpe_credit_limit,  # ← FPE만
        margin_rate=snapshot.fpe_margin_rate,
        payment_grace_days=snapshot.fpe_payment_grace_days,
        template_variant=req.template_variant,
    )


# ====================================================
# Test-only API (FLOWBIZ_ENV=test 가드)
# ====================================================
if os.getenv("FLOWBIZ_ENV") == "test":

    @app.post("/api/test/seed-raw-snapshot")
    async def seed_raw_snapshot(snapshot: UnsafeRawSnapshotForTest):
        """⚠ TEST ONLY — Pydantic 우회 raw 저장 (v4 F2 P1)"""
        raw_dict = snapshot.model_dump(exclude_unset=False)
        path = save_evaluation_snapshot(raw_dict)
        return {"report_id": snapshot.report_id, "saved_to": str(path)}

    @app.delete("/api/test/raw-snapshot/{report_id}")
    async def delete_raw_snapshot(report_id: str):
        snapshot_dir = get_snapshot_dir()
        path = snapshot_dir / f"{report_id}.json"
        if path.exists():
            path.unlink()
        return {"deleted": report_id}


app.mount("/web", StaticFiles(directory=WEB_DIR, html=True), name="web")
