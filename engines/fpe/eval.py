"""FPE_v.16.01 본체 — 메인 engine.py의 8개 평가 함수 re-export.

v2.11 단방향 룰: eval은 view를 import 가능. view는 eval import 금지.

8 함수:
  evaluate_fpe_v1601 (메인 진입점)
  fpe_detect_knockout_reasons, compute_fpe_customer_base_limit,
  classify_fpe_transaction_risk, compute_fpe_limit_adjustment,
  compute_fpe_transaction_limit, compute_fpe_margin, classify_fpe_review_path

v2.11 마이그레이션:
  1차 (현 PR): engine.py에서 본체 re-export.
  2차 (후속 PR): 함수 본체를 본 파일로 점진 이동.
"""
from __future__ import annotations
from typing import Any

# v2.11 1차: 메인 engine.py에서 본체 import. 2차에서 본체 이동 예정.
from engine import (
    evaluate_fpe_v1601,
    fpe_detect_knockout_reasons,
    compute_fpe_customer_base_limit,
    classify_fpe_transaction_risk,
    compute_fpe_limit_adjustment,
    compute_fpe_transaction_limit,
    compute_fpe_margin,
    classify_fpe_review_path,
)

from .policy import load_policy
from .view import (
    build_fpe_sales_view,
    generate_fpe_sales_summary,
    generate_fpe_sales_report,
    generate_fpe_sales_email,
)


def evaluate(input_data: dict[str, Any], framework: dict[str, Any] | None = None, **kwargs: Any) -> dict[str, Any]:
    """FPE 엔진 통합 진입점 — registry에서 호출.

    framework 미지정 시 active framework 자동 로드.
    """
    if framework is None:
        from engine import load_active_framework
        framework = load_active_framework()
    return evaluate_fpe_v1601(input_data, framework, load_policy())
