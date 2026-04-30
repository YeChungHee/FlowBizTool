"""APE_v1.01 framework loader + active framework state management.

학습 체크포인트 라이프사이클:
- data/engines/ape/frameworks/<id>.json — 후보 체크포인트
- data/engines/ape/active_framework.json — 현재 라이브 (promote 결과)
- data/integrated_credit_rating_framework.json — fallback baseline

bizaipro_learning.py promote/rollback이 이 모듈의 ACTIVE_FRAMEWORK_PATH를 갱신한다.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# Repo root — engines/ape/ → engines/ → repo
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENGINE_DATA_DIR = BASE_DIR / "data" / "engines" / "ape"
FRAMEWORKS_DIR = ENGINE_DATA_DIR / "frameworks"
ACTIVE_FRAMEWORK_PATH = ENGINE_DATA_DIR / "active_framework.json"

# Fallback (공통 baseline) — APE 전용 _baseline.json이 없으면 메인 baseline 사용
_BASELINE_FALLBACK_PATH = BASE_DIR / "data" / "integrated_credit_rating_framework.json"


def _resolve_baseline_path() -> Path:
    """APE 전용 baseline (data/engines/ape/frameworks/_baseline.json)이 있으면 그것을, 없으면 fallback."""
    ape_baseline = FRAMEWORKS_DIR / "_baseline.json"
    return ape_baseline if ape_baseline.exists() else _BASELINE_FALLBACK_PATH


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fp:
        return json.load(fp)


def load_active_framework() -> dict[str, Any]:
    """매 호출 시 active_framework.json 존재 여부를 다시 확인해 로드.

    promote으로 active_framework.json이 생성/갱신되면 다음 평가부터 즉시 반영.
    """
    if ACTIVE_FRAMEWORK_PATH.exists():
        return load_json(ACTIVE_FRAMEWORK_PATH)
    return load_json(_resolve_baseline_path())


def get_active_framework_meta() -> dict[str, str]:
    """active framework의 경로/소스/버전/엔진 식별을 반환.

    `engine_id`/`engine_label`로 학습 엔진(APE)과 심사기준 엔진(baseline/FPE)을 구분.
    `version`은 framework checkpoint 식별자 (v.1.16.01, v.1.18.02 등).
    """
    path = ACTIVE_FRAMEWORK_PATH if ACTIVE_FRAMEWORK_PATH.exists() else _resolve_baseline_path()
    source = "active" if path == ACTIVE_FRAMEWORK_PATH else "baseline"
    try:
        data = load_json(path)
        version = str(data.get("version") or "")
        engine_id = str(data.get("engine_id") or "")
        engine_label = str(data.get("engine_label") or "")
    except (FileNotFoundError, json.JSONDecodeError):
        version = ""
        engine_id = ""
        engine_label = ""
    return {
        "framework_path": str(path),
        "source": source,
        "filename": path.name,
        "version": version,
        "engine_id": engine_id,
        "engine_label": engine_label,
    }


def compute_report_base_limit(annual_sales: float, framework: dict[str, Any]) -> int | None:
    """기업리포트 표시용 기본 한도 — financials 미보유 환경에서 호출.

    DR adjustment는 financials가 없으므로 fallback=1.0 적용.
    """
    if not annual_sales:
        return None
    limit_cfg = framework.get("flowpay_underwriting", {}).get("limit", {})
    mode = limit_cfg.get("limit_formula_mode", "monthly_sales_ratio")
    if mode == "monthly_sales_ratio":
        ratio = float(limit_cfg.get("base_monthly_sales_ratio", 0.7))
        base = (annual_sales / 12.0) * ratio
    elif mode == "annual_sales_rate_with_dynamic_rate_adjustment":
        rate = float(limit_cfg.get("annual_sales_rate", 0.075))
        base = annual_sales * rate
    else:
        return None
    return int(round(base / 1000.0) * 1000)
