"""v2.11 §2.4 Step 10.5: 듀얼 평가 4 consensus 케이스 회귀 테스트.

라이브 서버(127.0.0.1:8012) 가정. Step 12 prelude에서 health check 후 실행.
httpx 미설치 환경 호환 — urllib만 사용.
"""
from __future__ import annotations

import json
import os
import urllib.request
import urllib.error
from pathlib import Path

import pytest

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "v_compare"
SERVER_URL = os.environ.get("DUAL_SERVER_URL", "http://127.0.0.1:8012")


def _post_json(path: str, body: dict) -> dict:
    req = urllib.request.Request(
        f"{SERVER_URL}{path}",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        try:
            return {"_error_status": exc.code, "_error_body": json.loads(exc.read().decode())}
        except Exception:
            return {"_error_status": exc.code}


def _get_json(path: str) -> dict:
    try:
        with urllib.request.urlopen(f"{SERVER_URL}{path}", timeout=5) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError):
        return {}


def _server_ready() -> bool:
    try:
        return bool(_get_json("/api/engine/list").get("engines"))
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not _server_ready(), reason=f"라이브 서버 부재: {SERVER_URL}")


@pytest.mark.parametrize("fixture_name,expected_consensus", [
    ("both_go_normal.json", "both_go"),
    ("fpe_blocked_ccc.json", "fpe_blocked"),
    ("ape_only_positive.json", "ape_only_positive"),
    ("both_review_low_score.json", "both_review"),
])
def test_dual_evaluation_consensus(fixture_name, expected_consensus):
    """4 consensus 케이스 — 의도된 결과와 정확히 일치."""
    payload = json.load((FIXTURE_DIR / fixture_name).open())
    data = _post_json("/api/evaluate/dual", payload)
    if "_error_status" in data:
        pytest.fail(f"HTTP {data['_error_status']}: {data.get('_error_body')}")
    actual = (data.get("agreement") or {}).get("consensus")
    fpe_gate = data.get("fpe_gate_passed")
    fpe_decision = ((data.get("screening") or {}).get("result") or {}).get("decision")
    ape_decision = ((data.get("ape") or {}).get("result") or {}).get("decision") if (data.get("ape") or {}).get("result") else None
    review_path = ((data.get("agreement") or {}).get("fpe_review_path"))
    assert actual == expected_consensus, (
        f"{fixture_name}: expected '{expected_consensus}', got '{actual}'\n"
        f"  fpe_gate_passed: {fpe_gate}, fpe_decision: {fpe_decision}, ape_decision: {ape_decision}, fpe_review_path: {review_path}"
    )


def test_engine_list_endpoint():
    """v2.11 Step 8: /api/engine/list — FPE + APE 양쪽 META 노출."""
    data = _get_json("/api/engine/list")
    engines = data.get("engines", [])
    engine_ids = {e.get("engine_id") for e in engines}
    assert "FPE" in engine_ids
    assert "APE" in engine_ids


def test_server_input_hash_changes_on_credit_grade():
    """v2.11 §2.2 F2: server_input_hash가 입력 변경 감지."""
    h1 = _post_json("/api/learning/evaluate/dual", {
        "state": {"companyName": "X", "reportCreditGrade": "BB+"}
    }).get("server_input_hash")
    h2 = _post_json("/api/learning/evaluate/dual", {
        "state": {"companyName": "X", "financialFilterSignal": "CCC-"}
    }).get("server_input_hash")
    assert h1 and h2, f"server_input_hash 빈 값: h1={h1}, h2={h2}"
    assert h1 != h2, f"hash 동일: {h1}"


def test_force_ape_default_rejected():
    """v2.11 §2.5: force_ape 기본 거부 — admin token 없으면 무시."""
    data = _post_json("/api/evaluate/dual", {
        "company_name": "X",
        "screening": {"credit_grade": "CCC-"},  # FPE knockout
        "force_ape": True,  # admin token 없음 → 무시
    })
    assert data.get("fpe_gate_passed") is False
    assert data.get("admin_override_active") is False
    assert (data.get("ape") or {}).get("result") is None
