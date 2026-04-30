"""APE_v1.01 본체 — 메인 engine.py의 24 함수 re-export.

v2.11 마이그레이션 단계:
  1차 (현 PR): engine.py → re-export thin layer (회귀 안전 우선)
  2차 (후속 PR): 함수 본체를 본 파일로 점진 이동, engine.py는 shim으로 축소

24 함수 (engine.py에서 정의):
  evaluate_flowpay_underwriting (메인 진입점)
  apply_api_enrichment, blend_signal_score, build_deep_weaknesses,
  build_sales_view, build_strengths_and_weaknesses, build_weighted_breakdown,
  compute_category_score, compute_ews, compute_limit_amount,
  compute_margin_result, compute_model_scores, compute_pd_curve,
  compute_weighted_score, detect_knockout_reasons, evaluate_industry_fit,
  generate_sales_email, generate_sales_report, generate_sales_summary,
  get_industry_thresholds, sales_decision_label, sales_grade_meanings,
  sales_next_action, score_to_grade
"""
from __future__ import annotations
from typing import Any

# v2.11 1차: engine.py에서 본체 import. 2차에서 본체 이동 후 import 방향 역전 예정.
from engine import (
    evaluate_flowpay_underwriting,
    apply_api_enrichment,
    blend_signal_score,
    build_deep_weaknesses,
    build_sales_view,
    build_strengths_and_weaknesses,
    build_weighted_breakdown,
    compute_category_score,
    compute_ews,
    compute_limit_amount,
    compute_margin_result,
    compute_model_scores,
    compute_pd_curve,
    compute_weighted_score,
    detect_knockout_reasons,
    evaluate_industry_fit,
    generate_sales_email,
    generate_sales_report,
    generate_sales_summary,
    get_industry_thresholds,
    sales_decision_label,
    sales_grade_meanings,
    sales_next_action,
    score_to_grade,
)


# Compatibility — 워크트리 origin engines/ape에 있던 helper들 (없으면 fallback)
try:
    from engine import (
        compute_limit_amount_detail,
        _compute_dynamic_rate_adjustment,
        _is_c_plus_grade,
        _pct_to_decimal,
    )
except ImportError:
    # 메인 engine.py에 아직 없는 함수 — APE checkpoint 작업 후 추가 예정
    def compute_limit_amount_detail(*args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError("APE checkpoint v.1.18.02 작업에서 추가 예정")

    def _compute_dynamic_rate_adjustment(*args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError("APE checkpoint v.1.18.02 작업에서 추가 예정")

    def _is_c_plus_grade(*args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError("APE checkpoint v.1.18.02 작업에서 추가 예정")

    def _pct_to_decimal(value: Any) -> Any:
        if value is None:
            return None
        try:
            return float(value) / 100.0
        except (TypeError, ValueError):
            return None


def evaluate(input_data: dict[str, Any], framework: dict[str, Any] | None = None, **kwargs: Any) -> dict[str, Any]:
    """APE 엔진 통합 진입점 — registry에서 호출.

    framework 미지정 시 active framework 자동 로드.
    """
    if framework is None:
        from .framework import load_active_framework
        framework = load_active_framework()
    return evaluate_flowpay_underwriting(input_data, framework)
