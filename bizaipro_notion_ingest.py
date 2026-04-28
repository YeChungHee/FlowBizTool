"""bizaipro_notion_ingest.py — Notion 심사보고서 배치 추출 및 학습 registry 적재.

2단계 고도화 (FBU-VAL-0006 기반):
  - 플로우페이_보고서 관리 DB에서 보고서 유형=심사보고서 필터 쿼리
  - 심사결과 → outcome_label 매핑
  - SourceQuality 기준 적용 (본문 최소 50자, 심사결과 입력 필수)
  - bizaipro_learning_registry.json에 자동 적재

실행:
  python3 bizaipro_notion_ingest.py --dry-run       # 적재 없이 결과만 미리 보기
  python3 bizaipro_notion_ingest.py                 # 실제 적재
  python3 bizaipro_notion_ingest.py --limit 10      # 최대 10건만
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent

# ── 환경 설정 ──────────────────────────────────────────────────────────────
NOTION_DB_ID = "20a16c59d686800c884cebb7816829ea"  # 플로우페이_보고서 관리
API_KEYS_PATH = BASE_DIR / "data" / "api_keys.local.json"
REGISTRY_PATH = BASE_DIR / "data" / "bizaipro_learning_registry.json"
FRAMEWORK_PATH = BASE_DIR / "data" / "integrated_credit_rating_framework.json"

OUTCOME_LABEL_MAP: dict[str, str] = {
    "진행 가능": "approved",
    "보완시 심사": "conditional",
    "제출시 검토": "review_required",
    "진행 불가": "rejected",
}

SENTIMENT_LABEL_MAP: dict[str, str] = {
    "긍정적": "positive",
    "중립적": "neutral",
    "부정적": "negative",
    "매우 부정적": "very_negative",
}

MIN_BODY_LENGTH = 50  # SourceQuality 최소 본문 길이


# ── Notion API 헬퍼 ────────────────────────────────────────────────────────
def _load_token() -> str:
    if not API_KEYS_PATH.exists():
        sys.exit(f"[ERROR] {API_KEYS_PATH} not found.")
    with API_KEYS_PATH.open(encoding="utf-8") as f:
        keys = json.load(f)
    token = keys.get("NOTION_API_TOKEN") or ""
    if not token:
        sys.exit("[ERROR] NOTION_API_TOKEN not set in api_keys.local.json")
    return token


def _notion_headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }


def _notion_post(endpoint: str, token: str, payload: dict[str, Any]) -> dict[str, Any]:
    import urllib.request

    url = f"https://api.notion.com/v1{endpoint}"
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers=_notion_headers(token), method="POST")
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read())


def _notion_get(endpoint: str, token: str) -> dict[str, Any]:
    import urllib.request

    url = f"https://api.notion.com/v1{endpoint}"
    req = urllib.request.Request(url, headers=_notion_headers(token), method="GET")
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read())


# ── DB 쿼리 ────────────────────────────────────────────────────────────────
def query_shimsa_pages(token: str, limit: int | None = None) -> list[dict[str, Any]]:
    """심사보고서 필터로 DB 페이지 목록을 반환."""
    results: list[dict[str, Any]] = []
    payload: dict[str, Any] = {
        "filter": {
            "property": "보고서 유형",
            "select": {"equals": "심사보고서"},
        },
        "page_size": 100,
    }
    cursor: str | None = None
    while True:
        if cursor:
            payload["start_cursor"] = cursor
        resp = _notion_post(f"/databases/{NOTION_DB_ID}/query", token, payload)
        results.extend(resp.get("results") or [])
        if limit and len(results) >= limit:
            results = results[:limit]
            break
        if not resp.get("has_more"):
            break
        cursor = resp.get("next_cursor")
    return results


# ── 속성 추출 헬퍼 ──────────────────────────────────────────────────────────
def _rich_text_str(prop: dict[str, Any] | None) -> str:
    if not prop:
        return ""
    items = prop.get("rich_text") or prop.get("title") or []
    return "".join(item.get("plain_text", "") for item in items).strip()


def _select_str(prop: dict[str, Any] | None) -> str:
    if not prop:
        return ""
    sel = prop.get("select") or {}
    return sel.get("name") or ""


def _status_str(prop: dict[str, Any] | None) -> str:
    if not prop:
        return ""
    sts = prop.get("status") or {}
    return sts.get("name") or ""


def _date_str(prop: dict[str, Any] | None) -> str:
    if not prop:
        return ""
    dt = prop.get("date") or {}
    return dt.get("start") or ""


def _title_str(prop: dict[str, Any] | None) -> str:
    if not prop:
        return ""
    items = prop.get("title") or []
    return "".join(item.get("plain_text", "") for item in items).strip()


# ── 블록 텍스트 추출 ────────────────────────────────────────────────────────
def _fetch_block_text(page_id: str, token: str, max_blocks: int = 200) -> str:
    texts: list[str] = []
    queue = [page_id]
    visited: set[str] = set()
    processed = 0
    while queue and processed < max_blocks:
        bid = queue.pop(0)
        if bid in visited:
            continue
        visited.add(bid)
        cursor: str | None = None
        while True:
            params = "?page_size=100"
            if cursor:
                params += f"&start_cursor={cursor}"
            try:
                payload = _notion_get(f"/blocks/{bid}/children{params}", token)
            except Exception:
                break
            for block in payload.get("results") or []:
                processed += 1
                bt = block.get("type", "")
                bv = block.get(bt) or {}
                if "rich_text" in bv:
                    t = "".join(item.get("plain_text", "") for item in bv.get("rich_text") or [])
                    if t:
                        texts.append(t)
                if block.get("has_children") and block.get("id"):
                    queue.append(str(block["id"]))
                if processed >= max_blocks:
                    break
            if processed >= max_blocks or not payload.get("has_more"):
                break
            cursor = payload.get("next_cursor")
    return "\n".join(texts).strip()


# ── 페이지 파싱 ─────────────────────────────────────────────────────────────
def parse_shimsa_page(page: dict[str, Any], token: str) -> dict[str, Any]:
    """단일 심사보고서 Notion 페이지를 파싱하여 학습 적재 형식으로 반환."""
    props = page.get("properties") or {}
    page_id = page.get("id", "")

    # 기본 속성 추출
    # 제목 필드에서 회사명 추출 (예: "심사보고서 : 해남참농가" → "해남참농가")
    raw_title = _title_str(props.get("제목")) or _title_str(props.get("Name")) or ""
    if ":" in raw_title:
        company_name = raw_title.split(":", 1)[1].strip()
    else:
        company_name = raw_title.strip()
    outcome_raw = _select_str(props.get("심사결과")) or _status_str(props.get("심사결과"))
    sentiment_raw = _select_str(props.get("심사_첫인상")) or ""
    shimsa_date = _date_str(props.get("상담(실사)일")) or _date_str(props.get("심사일"))

    # 본문 추출: 속성 rich_text 필드 + 블록
    prop_text_parts: list[str] = []
    for pname, prop in props.items():
        if prop.get("type") in ("rich_text", "title"):
            t = _rich_text_str(prop)
            if t:
                prop_text_parts.append(f"{pname}: {t}")
    prop_text = "\n".join(prop_text_parts)

    block_text = _fetch_block_text(page_id, token)
    body_text = "\n".join(p for p in [prop_text, block_text] if p).strip()

    outcome_label = OUTCOME_LABEL_MAP.get(outcome_raw)
    sentiment_label = SENTIMENT_LABEL_MAP.get(sentiment_raw)

    # SourceQuality 판정
    quality_issues: list[str] = []
    if not company_name:
        quality_issues.append("업체명 미확인")
    if not outcome_label:
        quality_issues.append(f"심사결과 미입력 또는 매핑 불가: '{outcome_raw}'")
    if len(body_text) < MIN_BODY_LENGTH:
        quality_issues.append(f"본문 {len(body_text)}자 — 최소 {MIN_BODY_LENGTH}자 미달")

    usable = len(quality_issues) == 0

    return {
        "page_id": page_id,
        "company_name": company_name,
        "outcome_raw": outcome_raw,
        "outcome_label": outcome_label,
        "sentiment_raw": sentiment_raw,
        "sentiment_label": sentiment_label,
        "shimsa_date": shimsa_date,
        "body_text": body_text,
        "body_length": len(body_text),
        "quality": {
            "usable_for_update": usable,
            "issues": quality_issues,
        },
    }


# ── registry 적재 ──────────────────────────────────────────────────────────
def _utc_now() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def load_registry() -> dict[str, Any]:
    if REGISTRY_PATH.exists():
        with REGISTRY_PATH.open(encoding="utf-8") as f:
            return json.load(f)
    return {"engine_name": "BizAiPro", "current_version": "v.1.0.00", "cases": [], "updates": []}


def save_registry(registry: dict[str, Any]) -> None:
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with REGISTRY_PATH.open("w", encoding="utf-8") as f:
        json.dump(registry, f, ensure_ascii=False, indent=2)


def _existing_page_ids(registry: dict[str, Any]) -> set[str]:
    ids: set[str] = set()
    for case in registry.get("cases") or []:
        pid = case.get("notion_page_id")
        if pid:
            ids.add(pid)
    return ids


def build_registry_case(parsed: dict[str, Any], case_id: str) -> dict[str, Any]:
    """심사보고서 파싱 결과를 registry case 형식으로 변환."""
    internal_review_link = f"https://www.notion.so/{parsed['page_id'].replace('-', '')}"
    learning_context = {
        "flow_score_report_submitted": False,
        "consultation_report_submitted": False,
        "internal_review_link": internal_review_link,
        "additional_sources": [],
    }
    # 심사보고서만 있을 때 학습 가중치: internal_review = 0.15
    # flow_score, consultation 없으므로 evaluation_ready=False, qualified=False
    components = {
        "flow_score_report": 0.0,
        "consultation_report": 0.0,
        "internal_review": 0.15,
        "additional_sources": 0.0,
    }
    total_weight = 0.15
    evaluation_ready = False
    update_eligible = False  # needs flow_score AND consultation AND internal_review

    return {
        "id": case_id,
        "label": parsed["company_name"] or case_id,
        "source": "notion_shimsa",
        "notion_page_id": parsed["page_id"],
        "created_at": _utc_now(),
        "engine_version": "v.local.learning",
        "outcome_label": parsed["outcome_label"],
        "sentiment_label": parsed["sentiment_label"],
        "shimsa_date": parsed["shimsa_date"],
        "body_text_length": parsed["body_length"],
        "quality": parsed["quality"],
        "input_data": {
            "analysis_type": "flowpay_underwriting",
            "engine_version": "v.local.learning",
            "company_name": parsed["company_name"],
            "source_text": parsed["body_text"][:3000],
            "learning_context": learning_context,
        },
        "result_snapshot": None,  # 심사보고서 단독 케이스는 평가엔진 실행 전
        "learning": {
            "evaluation_ready": evaluation_ready,
            "update_eligible": update_eligible,
            "qualified": update_eligible,
            "total_weight": total_weight,
            "components": components,
            "additional_source_count": 0,
        },
    }


# ── 메인 ───────────────────────────────────────────────────────────────────
def run_ingest(dry_run: bool = False, limit: int | None = None, verbose: bool = False) -> dict[str, Any]:
    token = _load_token()
    registry = load_registry()
    existing_ids = _existing_page_ids(registry)
    next_case_num = len(registry["cases"]) + 1

    print(f"[INFO] DB 쿼리 중... (DB: {NOTION_DB_ID})")
    pages = query_shimsa_pages(token, limit=limit)
    print(f"[INFO] 심사보고서 {len(pages)}건 조회됨")

    stats = {
        "total_queried": len(pages),
        "already_exists": 0,
        "quality_fail": 0,
        "loaded": 0,
        "skipped_no_outcome": 0,
        "cases": [],
    }

    new_cases: list[dict[str, Any]] = []
    for page in pages:
        pid = page.get("id", "")
        if pid in existing_ids:
            stats["already_exists"] += 1
            continue

        print(f"  파싱 중: {pid[:8]}...", end="", flush=True)
        try:
            parsed = parse_shimsa_page(page, token)
        except Exception as e:
            print(f" ⚠️ 파싱 오류: {e}")
            continue

        if not parsed["outcome_label"]:
            stats["skipped_no_outcome"] += 1
            print(f" 건너뜀 (심사결과 없음: '{parsed['outcome_raw']}')")
            continue

        if not parsed["quality"]["usable_for_update"]:
            stats["quality_fail"] += 1
            issues_str = " / ".join(parsed["quality"]["issues"])
            print(f" 품질 미달: {issues_str}")
            if verbose:
                print(f"    회사: {parsed['company_name']} | 본문: {parsed['body_length']}자")
            continue

        case_id = f"case-{next_case_num:04d}"
        next_case_num += 1
        case = build_registry_case(parsed, case_id)
        new_cases.append(case)
        stats["loaded"] += 1
        stats["cases"].append({
            "id": case_id,
            "company": parsed["company_name"],
            "outcome_label": parsed["outcome_label"],
            "body_length": parsed["body_length"],
        })
        print(f" ✅ {parsed['company_name']} [{parsed['outcome_label']}] {parsed['body_length']}자")

    print(f"\n[SUMMARY] 조회: {stats['total_queried']}건 | 기존 중복: {stats['already_exists']}건 | "
          f"심사결과 없음: {stats['skipped_no_outcome']}건 | 품질 미달: {stats['quality_fail']}건 | "
          f"적재 예정: {stats['loaded']}건")

    if not dry_run and new_cases:
        registry["cases"].extend(new_cases)
        save_registry(registry)
        print(f"[INFO] ✅ {len(new_cases)}건 registry에 적재 완료 → {REGISTRY_PATH}")
    elif dry_run:
        print("[DRY-RUN] 실제 저장 생략")

    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description="Notion 심사보고서 배치 추출 및 학습 registry 적재")
    parser.add_argument("--dry-run", action="store_true", help="저장 없이 결과만 출력")
    parser.add_argument("--limit", type=int, default=None, help="처리할 최대 케이스 수")
    parser.add_argument("--verbose", "-v", action="store_true", help="상세 출력")
    args = parser.parse_args()
    result = run_ingest(dry_run=args.dry_run, limit=args.limit, verbose=args.verbose)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
