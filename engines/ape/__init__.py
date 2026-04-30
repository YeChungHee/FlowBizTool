"""APE_v1.01 — Adaptive Proposal Engine (학습 기반 비즈니스 제안 평가).

학습 체크포인트:
- v.1.16.01: monthly_sales_ratio mode (학습 가중치 보정)
- v.1.18.02: annual_sales_rate_with_dynamic_rate_adjustment + C+ c_grade_factor

데이터 위치: data/engines/ape/
- frameworks/<id>.json — 후보 체크포인트
- active_framework.json — 라이브 (promote 결과)
- learning_registry.json — 학습 케이스 누적
"""
from __future__ import annotations

from .._base import EngineMeta
from .framework import (
    ACTIVE_FRAMEWORK_PATH,
    FRAMEWORKS_DIR,
    compute_report_base_limit,
    get_active_framework_meta,
    load_active_framework,
)
from .eval import (
    compute_limit_amount,
    compute_limit_amount_detail,
    evaluate,
    _compute_dynamic_rate_adjustment,
    _is_c_plus_grade,
    _pct_to_decimal,
)


META = EngineMeta(
    engine_id="APE",
    engine_label="APE_v1.01",
    engine_version="v.1.18.02",  # 동적: get_active_framework_meta()도 노출
    engine_locked=False,
    engine_purpose="learning_proposal",
    policy_source="bizaipro_learning_loop",
)


def get_meta() -> dict:
    """현재 active 메타까지 합쳐 반환 — registry list_engines가 사용."""
    base = META.asdict()
    active = get_active_framework_meta()
    base["active_version"] = active.get("version", "")
    base["active_source"] = active.get("source", "")
    return base


__all__ = [
    "META",
    "get_meta",
    "evaluate",
    "load_active_framework",
    "get_active_framework_meta",
    "compute_report_base_limit",
    "compute_limit_amount",
    "compute_limit_amount_detail",
    "ACTIVE_FRAMEWORK_PATH",
    "FRAMEWORKS_DIR",
]
