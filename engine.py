from __future__ import annotations

import argparse
import copy
import math
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from external_apis import DartClient, EcosClient, ExternalApiError, load_api_keys
from proposal_generator import generate_bizaipro_proposal


BASE_DIR = Path(__file__).resolve().parent
ACTIVE_FRAMEWORK_PATH = BASE_DIR / "data" / "active_framework.json"
_BASELINE_FRAMEWORK_PATH = BASE_DIR / "data" / "integrated_credit_rating_framework.json"
# import 시점 고정값 — 하위 호환용으로만 유지. 평가 호출은 load_active_framework() 사용 권장
FRAMEWORK_PATH = ACTIVE_FRAMEWORK_PATH if ACTIVE_FRAMEWORK_PATH.exists() else _BASELINE_FRAMEWORK_PATH


@dataclass
class RatingResult:
    name: str
    score: float
    rating: str


@dataclass
class SurvivalResult:
    score: float
    judgment: str
    survival_probability: str


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fp:
        return json.load(fp)


def load_active_framework() -> dict[str, Any]:
    """매 호출 시 active_framework.json 존재 여부를 다시 확인해 로드.

    서버 실행 중 promote로 active_framework.json이 생성·갱신되어도
    다음 평가 호출부터 즉시 반영된다 (FBU-VAL-0007 Finding 2 수정).
    """
    if ACTIVE_FRAMEWORK_PATH.exists():
        return load_json(ACTIVE_FRAMEWORK_PATH)
    return load_json(_BASELINE_FRAMEWORK_PATH)


def get_active_framework_meta() -> dict[str, str]:
    """현재 사용 중인 framework의 경로와 소스 유형을 반환."""
    if ACTIVE_FRAMEWORK_PATH.exists():
        return {
            "framework_path": str(ACTIVE_FRAMEWORK_PATH),
            "source": "active",
            "filename": ACTIVE_FRAMEWORK_PATH.name,
        }
    return {
        "framework_path": str(_BASELINE_FRAMEWORK_PATH),
        "source": "baseline",
        "filename": _BASELINE_FRAMEWORK_PATH.name,
    }


def bounded_score(value: float) -> float:
    return max(0.0, min(100.0, float(value)))


def compute_category_score(category_name: str, category_data: dict[str, Any], input_scores: dict[str, Any]) -> float:
    subfactors = category_data["subfactors"]
    provided = input_scores.get(category_name, {})

    missing = [name for name in subfactors if name not in provided]
    if missing:
        missing_str = ", ".join(missing)
        raise ValueError(f"Missing subfactor scores for '{category_name}': {missing_str}")

    total = 0.0
    for subfactor, weight in subfactors.items():
        total += bounded_score(provided[subfactor]) * float(weight)
    return round(total, 2)


def compute_model_scores(model_categories: dict[str, Any], input_scores: dict[str, Any]) -> dict[str, float]:
    scores: dict[str, float] = {}
    for category_name, category_data in model_categories.items():
        scores[category_name] = compute_category_score(category_name, category_data, input_scores)
    return scores


def score_to_rating(score: float, scale: list[dict[str, Any]]) -> str:
    for row in scale:
        if score >= float(row["min_score"]):
            return row["rating"]
    return scale[-1]["rating"]


def score_to_grade(score: float, scale: list[dict[str, Any]]) -> str:
    for row in scale:
        if score >= float(row["min_score"]):
            return row["grade"]
    return scale[-1]["grade"]


def rating_rank_map(scale: list[dict[str, Any]]) -> dict[str, int]:
    return {row["rating"]: idx for idx, row in enumerate(scale)}


def judgment_rank_map(scale: list[dict[str, Any]]) -> dict[str, int]:
    return {row["judgment"]: idx for idx, row in enumerate(scale)}


def apply_critical_factor_floor(
    tentative_rating: str,
    input_scores: dict[str, Any],
    framework: dict[str, Any],
) -> str:
    scale = framework["rating_scale"]
    ranks = rating_rank_map(scale)
    final_rating = tentative_rating
    final_rank = ranks[tentative_rating]

    flat_scores: dict[str, float] = {}
    for category_scores in input_scores.values():
        for key, value in category_scores.items():
            flat_scores[key] = bounded_score(value)

    for factor, rule in framework.get("critical_factors", {}).items():
        value = flat_scores.get(factor)
        if value is None:
            continue
        if value < float(rule["floor_if_below"]):
            capped_rating = rule["max_rating"]
            capped_rank = ranks[capped_rating]
            if capped_rank > final_rank:
                final_rating = capped_rating
                final_rank = capped_rank
    return final_rating


def survival_score_to_result(score: float, scale: list[dict[str, Any]]) -> SurvivalResult:
    for row in scale:
        if score >= float(row["min_score"]):
            return SurvivalResult(
                score=round(score, 2),
                judgment=row["judgment"],
                survival_probability=row["survival_probability"],
            )
    fallback = scale[-1]
    return SurvivalResult(
        score=round(score, 2),
        judgment=fallback["judgment"],
        survival_probability=fallback["survival_probability"],
    )


def apply_survival_floor(
    result: SurvivalResult,
    input_scores: dict[str, Any],
    framework: dict[str, Any],
) -> SurvivalResult:
    scale = framework["flowpay_3m_survival"]["survival_scale"]
    ranks = judgment_rank_map(scale)
    final_judgment = result.judgment
    final_rank = ranks[result.judgment]

    flat_scores: dict[str, float] = {}
    for category_scores in input_scores.values():
        for key, value in category_scores.items():
            flat_scores[key] = bounded_score(value)

    for factor, rule in framework["flowpay_3m_survival"].get("critical_factors", {}).items():
        value = flat_scores.get(factor)
        if value is None:
            continue
        if value < float(rule["floor_if_below"]):
            capped_judgment = rule["max_judgment"]
            capped_rank = ranks[capped_judgment]
            if capped_rank > final_rank:
                final_judgment = capped_judgment
                final_rank = capped_rank

    for row in scale:
        if row["judgment"] == final_judgment:
            return SurvivalResult(
                score=result.score,
                judgment=final_judgment,
                survival_probability=row["survival_probability"],
            )
    return result


def compute_weighted_score(category_scores: dict[str, float], weights: dict[str, float], modifier_total: float) -> float:
    score = 0.0
    for category_name, weight in weights.items():
        score += category_scores[category_name] * float(weight)
    score += modifier_total
    return round(bounded_score(score), 2)


def build_weighted_breakdown(category_scores: dict[str, float], weights: dict[str, float]) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    total = 0.0
    for category_name, weight in weights.items():
        contribution = category_scores[category_name] * float(weight)
        items.append(
            {
                "name": category_name,
                "score": round(category_scores[category_name], 2),
                "weight": round(float(weight), 4),
                "contribution": round(contribution, 2),
            }
        )
        total += contribution
    return {
        "items": items,
        "total": round(total, 2),
    }


def build_strengths_and_weaknesses(category_scores: dict[str, float]) -> tuple[list[str], list[str]]:
    ordered = sorted(category_scores.items(), key=lambda item: item[1], reverse=True)
    strength_items = ordered[: min(2, len(ordered))]
    weak_candidates = list(reversed(ordered))
    weakness_items: list[tuple[str, float]] = []
    used_strength_names = {name for name, _ in strength_items}

    for item in weak_candidates:
        if len(weakness_items) >= min(2, len(ordered) - len(strength_items)):
            break
        if item[0] not in used_strength_names:
            weakness_items.append(item)

    if not weakness_items and ordered:
        weakness_items = [ordered[-1]]

    strengths = [f"{name}: {score:.2f}" for name, score in strength_items]
    weaknesses = [f"{name}: {score:.2f}" for name, score in weakness_items]
    return strengths, weaknesses


def build_deep_weaknesses(category_scores: dict[str, float], threshold: float = 60.0) -> list[str]:
    return [name for name, score in category_scores.items() if score < threshold]


def evaluate(input_data: dict[str, Any], framework: dict[str, Any]) -> dict[str, Any]:
    raw_scores = input_data["scores"]
    category_scores = compute_model_scores(framework["categories"], raw_scores)

    modifiers = input_data.get("modifiers", {})
    modifier_total = round(sum(float(value) for value in modifiers.values()), 2)

    integrated_score = compute_weighted_score(
        category_scores,
        framework["integrated_weights"],
        modifier_total,
    )
    integrated_rating = score_to_rating(integrated_score, framework["rating_scale"])
    integrated_rating = apply_critical_factor_floor(integrated_rating, raw_scores, framework)

    agency_results: list[RatingResult] = []
    for agency_name, weights in framework["agency_weights"].items():
        score = compute_weighted_score(category_scores, weights, modifier_total)
        rating = score_to_rating(score, framework["rating_scale"])
        rating = apply_critical_factor_floor(rating, raw_scores, framework)
        agency_results.append(RatingResult(name=agency_name, score=score, rating=rating))

    strengths, weaknesses = build_strengths_and_weaknesses(category_scores)

    return {
        "company_name": input_data.get("company_name", "Unknown Company"),
        "industry": input_data.get("industry", "Unknown Industry"),
        "modifier_total": modifier_total,
        "integrated": {
            "score": integrated_score,
            "rating": integrated_rating,
        },
        "agencies": [agency_result.__dict__ for agency_result in agency_results],
        "category_scores": category_scores,
        "strengths": strengths,
        "weaknesses": weaknesses,
    }


def compute_data_reliability_adjustment(data_reliability_score: float) -> float:
    # SME filings and audit practices can be noisy, so lower reliability receives a nonlinear haircut.
    if data_reliability_score >= 75:
        return 0.0
    if data_reliability_score >= 65:
        return -1.5
    if data_reliability_score >= 55:
        return -3.0
    if data_reliability_score >= 45:
        return -5.0
    return -8.0


def confidence_level(data_reliability_score: float) -> str:
    if data_reliability_score >= 75:
        return "High"
    if data_reliability_score >= 60:
        return "Moderate"
    if data_reliability_score >= 45:
        return "Low"
    return "Very Low"


def blend_signal_score(manual_score: float, api_score: float, manual_weight: float, api_weight: float) -> float:
    total_weight = manual_weight + api_weight
    if total_weight <= 0:
        return round(bounded_score(api_score), 2)
    blended = ((manual_score * manual_weight) + (api_score * api_weight)) / total_weight
    return round(bounded_score(blended), 2)


def apply_api_enrichment(input_data: dict[str, Any], framework: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    working = copy.deepcopy(input_data)
    request = working.get("api_enrichment", {})
    result: dict[str, Any] = {
        "enabled": bool(request.get("enabled", False)),
        "applied": False,
        "warnings": [],
        "summary_changes": [],
        "applicant": {},
        "buyer": {},
        "transaction": {},
    }

    if not result["enabled"]:
        return working, result

    api_framework = framework.get("api_enrichment", {})
    blend_cfg = api_framework.get("blend", {})
    manual_weight = float(blend_cfg.get("manual_weight", 0.5))
    api_weight = float(blend_cfg.get("api_weight", 0.5))
    default_ecos_industry_code = str(api_framework.get("default_ecos_industry_code", "C0000"))
    dart_lookback_years = int(api_framework.get("dart_financial_lookback_years", 3))

    api_keys = load_api_keys()
    ecos_client = None
    dart_client = None

    if api_keys.get("ecos_api_key"):
        try:
            ecos_client = EcosClient(api_keys["ecos_api_key"])
        except ExternalApiError as exc:
            result["warnings"].append(str(exc))
    else:
        result["warnings"].append("ECOS API key가 없어 거시지표 보강을 건너뛰었습니다.")

    if api_keys.get("dart_api_key"):
        try:
            dart_client = DartClient(api_keys["dart_api_key"])
        except ExternalApiError as exc:
            result["warnings"].append(str(exc))
    else:
        result["warnings"].append("DART API key가 없어 공시정보 보강을 건너뛰었습니다.")

    ecos_scores_for_transaction: list[float] = []
    party_specs = [
        ("applicant", "ecos_signal", "dart_signal"),
        ("buyer", "buyer_ecos_signal", "buyer_dart_signal"),
    ]

    for party_name, ecos_key, dart_key in party_specs:
        party_request = request.get(party_name, {})
        party_scores = working.get(party_name, {}).get("scores", {}).get("external", {})

        if not party_scores:
            continue

        ecos_industry_code = str(party_request.get("ecos_industry_code", "")).strip()
        if ecos_client and ecos_industry_code:
            try:
                ecos_result = ecos_client.score_macro_signal(
                    industry_code=ecos_industry_code,
                    fallback_industry_code=default_ecos_industry_code,
                )
                manual_score = float(party_scores.get(ecos_key, 50.0))
                api_score = float(ecos_result["score"])
                final_score = blend_signal_score(manual_score, api_score, manual_weight, api_weight)
                party_scores[ecos_key] = final_score
                ecos_scores_for_transaction.append(api_score)
                party_result = {
                    "applied": True,
                    "manual_score": round(manual_score, 2),
                    "api_score": round(api_score, 2),
                    "final_score": final_score,
                    "details": ecos_result["details"],
                    "warnings": ecos_result.get("warnings", []),
                }
                result[party_name]["ecos"] = party_result
                result["applied"] = True
                result["summary_changes"].append(
                    f"{party_name} ECOS {manual_score:.1f}->{final_score:.1f}"
                )
                result["warnings"].extend(ecos_result.get("warnings", []))
            except Exception as exc:  # pragma: no cover - network/runtime failures
                result[party_name]["ecos"] = {
                    "applied": False,
                    "warning": str(exc),
                }
                result["warnings"].append(f"{party_name} ECOS 조회 실패: {exc}")

        if dart_client:
            corp_code = str(party_request.get("dart_corp_code", "")).strip() or None
            corp_name = str(party_request.get("dart_corp_name", "")).strip() or None
            stock_code = str(party_request.get("dart_stock_code", "")).strip() or None
            if corp_code or corp_name or stock_code:
                try:
                    dart_result = dart_client.score_disclosure_signal(
                        corp_code=corp_code,
                        corp_name=corp_name,
                        stock_code=stock_code,
                        lookback_years=dart_lookback_years,
                    )
                    manual_score = float(party_scores.get(dart_key, 50.0))
                    api_score = dart_result.get("score")
                    if api_score is None:
                        result[party_name]["dart"] = {
                            "applied": False,
                            "manual_score": round(manual_score, 2),
                            "api_score": None,
                            "final_score": round(manual_score, 2),
                            "details": dart_result.get("details", {}),
                            "warnings": dart_result.get("warnings", []),
                        }
                        result["warnings"].extend(dart_result.get("warnings", []))
                    else:
                        api_score = float(api_score)
                        final_score = blend_signal_score(manual_score, api_score, manual_weight, api_weight)
                        party_scores[dart_key] = final_score
                        result[party_name]["dart"] = {
                            "applied": True,
                            "manual_score": round(manual_score, 2),
                            "api_score": round(api_score, 2),
                            "final_score": final_score,
                            "details": dart_result["details"],
                            "warnings": dart_result.get("warnings", []),
                        }
                        result["applied"] = True
                        result["summary_changes"].append(
                            f"{party_name} DART {manual_score:.1f}->{final_score:.1f}"
                        )
                        result["warnings"].extend(dart_result.get("warnings", []))
                except Exception as exc:  # pragma: no cover - network/runtime failures
                    result[party_name]["dart"] = {
                        "applied": False,
                        "warning": str(exc),
                    }
                    result["warnings"].append(f"{party_name} DART 조회 실패: {exc}")

    transaction_macro = working.get("transaction", {}).get("scores", {}).get("macro", {})
    if ecos_scores_for_transaction and "industry_outlook" in transaction_macro:
        manual_score = float(transaction_macro["industry_outlook"])
        api_score = sum(ecos_scores_for_transaction) / len(ecos_scores_for_transaction)
        final_score = blend_signal_score(manual_score, api_score, manual_weight, api_weight)
        transaction_macro["industry_outlook"] = final_score
        result["transaction"]["industry_outlook"] = {
            "applied": True,
            "manual_score": round(manual_score, 2),
            "api_score": round(api_score, 2),
            "final_score": final_score,
        }
        result["applied"] = True
        result["summary_changes"].append(f"transaction industry_outlook {manual_score:.1f}->{final_score:.1f}")

    if result["warnings"]:
        deduped: list[str] = []
        for warning in result["warnings"]:
            if warning not in deduped:
                deduped.append(warning)
        result["warnings"] = deduped

    return working, result


def evaluate_flowpay_3m(input_data: dict[str, Any], framework: dict[str, Any]) -> dict[str, Any]:
    model = framework["flowpay_3m_survival"]
    raw_scores = input_data["scores"]
    category_scores = compute_model_scores(model["categories"], raw_scores)

    base_score = compute_weighted_score(category_scores, model["weights"], 0.0)
    reporting_haircut = compute_data_reliability_adjustment(category_scores["data_reliability"])

    modifiers = input_data.get("modifiers", {})
    modifier_total = round(sum(float(value) for value in modifiers.values()), 2)
    total_adjustment = round(reporting_haircut + modifier_total, 2)
    adjusted_score = round(bounded_score(base_score + total_adjustment), 2)

    result = survival_score_to_result(adjusted_score, model["survival_scale"])
    result = apply_survival_floor(result, raw_scores, framework)
    strengths, weaknesses = build_strengths_and_weaknesses(category_scores)

    return {
        "company_name": input_data.get("company_name", "Unknown Company"),
        "industry": input_data.get("industry", "Unknown Industry"),
        "analysis_type": "flowpay_3m_receivable",
        "base_score": base_score,
        "reporting_haircut": reporting_haircut,
        "modifier_total": modifier_total,
        "total_adjustment": total_adjustment,
        "confidence_level": confidence_level(category_scores["data_reliability"]),
        "survival": {
            "score": result.score,
            "judgment": result.judgment,
            "survival_probability": result.survival_probability,
        },
        "category_scores": category_scores,
        "strengths": strengths,
        "weaknesses": weaknesses,
    }


def score_band_multiplier(score: float, bands: list[tuple[float, float]]) -> float:
    for minimum, value in bands:
        if score >= minimum:
            return value
    return bands[-1][1]


def detect_knockout_reasons(input_data: dict[str, Any], model: dict[str, Any]) -> list[str]:
    screening = input_data.get("screening", {})
    rules = model["knockout_rules"]
    reasons: list[str] = []

    business_years = float(screening.get("business_years", 0.0))
    fast_track_supported = bool(screening.get("startup_fast_track_supported", False))
    if business_years < float(rules["minimum_business_years"]):
        if not (rules["allow_fast_track_if_supported"] and fast_track_supported):
            reasons.append("업력 1년 미만이며 패스트트랙 근거가 부족합니다.")

    if rules.get("exclude_complete_capital_impairment") and bool(screening.get("complete_capital_impairment", False)):
        reasons.append("완전자본잠식 상태입니다.")

    if rules.get("exclude_tax_arrears") and bool(screening.get("tax_arrears", False)):
        reasons.append("국세/지방세 또는 4대보험 체납 이력이 있습니다.")

    credit_grade = str(screening.get("credit_grade", "")).strip().upper()
    if credit_grade in set(rules.get("excluded_credit_grades", [])):
        reasons.append(f"기업 신용등급이 제외 구간({credit_grade})입니다.")

    recent_legal_action_years = float(screening.get("recent_legal_action_within_years", 99.0))
    if recent_legal_action_years <= float(rules.get("exclude_recent_legal_action_years", 0)):
        reasons.append("최근 3년 내 가압류/소송 등 법적 조치 이력이 있습니다.")

    industry_tag = str(screening.get("industry_tag", "")).strip().lower()
    if industry_tag in set(rules.get("excluded_industries", [])):
        reasons.append(f"제외 업종({industry_tag})으로 분류됩니다.")

    return reasons


def get_industry_thresholds(industry_profile: str, model: dict[str, Any]) -> dict[str, float]:
    profile = model["industry_thresholds"].get(industry_profile)
    if profile:
        return profile
    return model["industry_thresholds"]["default"]


def evaluate_industry_fit(input_data: dict[str, Any], model: dict[str, Any]) -> dict[str, Any]:
    financials = input_data.get("financials", {})
    industry_profile = str(input_data.get("industry_profile", "default"))
    thresholds = get_industry_thresholds(industry_profile, model)

    operating_margin = float(financials.get("operating_margin_pct", 0.0))
    ebitda_coverage = float(financials.get("ebitda_interest_coverage", 0.0))
    ccc_days = float(financials.get("cash_conversion_cycle_days", 0.0))
    requested_tenor_months = int(input_data.get("requested_tenor_months", 3))
    requested_tenor_days = requested_tenor_months * 30

    findings = {
        "industry_profile": industry_profile,
        "operating_margin_ok": operating_margin >= float(thresholds["recommended_operating_margin"]),
        "ebitda_interest_ok": ebitda_coverage >= float(thresholds["recommended_ebitda_interest_coverage"]),
        "ccc_ok": ccc_days <= requested_tenor_days,
        "recommended_operating_margin": thresholds["recommended_operating_margin"],
        "recommended_ebitda_interest_coverage": thresholds["recommended_ebitda_interest_coverage"],
        "cash_conversion_cycle_days": ccc_days,
        "requested_tenor_days": requested_tenor_days,
    }
    return findings


def compute_pd_curve(score: float, weakness_count: int, framework: dict[str, Any]) -> list[dict[str, Any]]:
    pd_model = framework["flowpay_underwriting"]["default_probability"]
    hazard_cfg = pd_model["hazard"]

    score_gap = (100.0 - score) / 100.0
    stress = score_gap ** float(hazard_cfg["score_power"])
    weakness_factor = weakness_count / 10.0
    base_hazard = float(hazard_cfg["base"]) + (float(hazard_cfg["score_multiplier"]) * stress) + (
        float(hazard_cfg["weakness_multiplier"]) * weakness_factor
    )

    curve: list[dict[str, Any]] = []
    for month_text, growth in pd_model["month_growth_factors"].items():
        month = int(month_text)
        cumulative_pd = 1 - math.exp(-(base_hazard * float(growth) * month))
        curve.append(
            {
                "month": month,
                "default_probability_pct": round(cumulative_pd * 100.0, 2),
                "survival_probability_pct": round((1 - cumulative_pd) * 100.0, 2),
            }
        )
    return curve


def compute_limit_amount(input_data: dict[str, Any], overall_score: float, buyer_score: float, model: dict[str, Any]) -> int:
    financials = input_data.get("financials", {})
    requested_tenor_months = int(input_data.get("requested_tenor_months", 3))
    annual_sales = float(financials.get("annual_sales", 0.0))
    business_years = float(input_data.get("screening", {}).get("business_years", 0.0))
    operating_profit = float(financials.get("operating_profit", 0.0))
    net_profit = float(financials.get("net_profit", 0.0))

    base_monthly_sales = annual_sales / 12.0
    limit_cfg = model["limit"]
    base_limit = base_monthly_sales * float(limit_cfg["base_monthly_sales_ratio"])

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
    elif operating_profit < 0 and net_profit < 0:
        profit_factor = float(limit_cfg["profit_factor"]["both_negative"])
    else:
        profit_factor = float(limit_cfg["profit_factor"]["one_negative"])

    risk_factor = score_band_multiplier(
        overall_score,
        [(80, 1.10), (70, 1.00), (60, 0.85), (50, 0.70), (0, 0.55)],
    )
    buyer_factor = score_band_multiplier(
        buyer_score,
        [(80, 1.05), (70, 1.00), (60, 0.90), (50, 0.80), (0, 0.65)],
    )
    tenor_factor = {1: 1.00, 2: 0.90, 3: 0.80, 4: 0.70, 5: 0.60}.get(requested_tenor_months, 0.55)

    raw_limit = base_limit * age_factor * profit_factor * risk_factor * buyer_factor * tenor_factor
    hard_cap = base_monthly_sales * float(limit_cfg["monthly_sales_cap_ratio"])
    final_limit = min(raw_limit, hard_cap)
    return int(round(final_limit / 1000.0) * 1000)


def compute_margin_result(
    requested_tenor_months: int,
    applicant_score: float,
    buyer_score: float,
    transaction_score: float,
    overall_score: float,
    applicant_compliance_score: float,
    model: dict[str, Any],
) -> dict[str, Any]:
    margin_cfg = model["margin"]
    supported_months = set(margin_cfg["supported_deferral_months"])
    if requested_tenor_months not in supported_months:
        return {
            "supported": False,
            "reason": "현재 가격정책은 1~3개월 유예기간만 지원합니다.",
        }

    base_rate = float(margin_cfg["base_rate_by_month"][str(requested_tenor_months)])
    max_rate = float(margin_cfg["max_rate_by_month"][str(requested_tenor_months)])

    adjustment = 0.0
    adjustment += score_band_multiplier(overall_score, [(80, -0.50), (70, 0.00), (60, 0.75), (50, 1.50), (0, 2.50)])
    if buyer_score < 60:
        adjustment += 0.75
    if applicant_score < 60:
        adjustment += 0.50
    if transaction_score < 60:
        adjustment += 0.50
    if applicant_compliance_score < 55:
        adjustment += 0.75

    commercial_rate = round(max(0.0, min(base_rate + adjustment, max_rate)), 2)
    legal_cap_rate = round(float(margin_cfg["annual_legal_cap_rate"]) * (requested_tenor_months / 12.0), 2)
    compliant_rate = round(min(commercial_rate, legal_cap_rate), 2)
    annualized_commercial_rate = round(commercial_rate * (12.0 / requested_tenor_months), 2)
    exceeds_legal_cap = annualized_commercial_rate > float(margin_cfg["annual_legal_cap_rate"])

    return {
        "supported": True,
        "base_rate_pct": base_rate,
        "commercial_rate_pct": commercial_rate,
        "max_rate_pct": max_rate,
        "annualized_commercial_rate_pct": annualized_commercial_rate,
        "legal_cap_rate_pct_for_tenor": legal_cap_rate,
        "compliant_rate_pct": compliant_rate,
        "exceeds_annual_legal_cap": exceeds_legal_cap,
    }


def compute_ews(input_data: dict[str, Any], model: dict[str, Any]) -> dict[str, Any]:
    ews_cfg = model["early_warning_system"]
    ews_input = input_data.get("ews_inputs", {})
    triggers: list[str] = []

    rep_drop = float(ews_input.get("representative_credit_drop_notches", 0.0))
    yoy_sales_drop = float(ews_input.get("yoy_sales_drop_pct", 0.0))
    short_term_debt_growth = float(ews_input.get("short_term_debt_growth_pct", 0.0))

    if rep_drop >= float(ews_cfg["rep_credit_drop_notches"]):
        triggers.append("대표자 개인신용등급 급락")
    if yoy_sales_drop >= float(ews_cfg["yoy_sales_drop_pct"]):
        triggers.append("전년동기 대비 월매출 30% 이상 급락")
    if short_term_debt_growth >= float(ews_cfg["short_term_debt_growth_pct"]):
        triggers.append("단기차입금 급증")

    return {
        "triggered": bool(triggers),
        "triggers": triggers,
        "actions": ews_cfg["actions"] if triggers else [],
    }


def sales_decision_label(decision: str) -> str:
    return {
        "APPROVE": "거래 가능성 높음",
        "REVIEW": "추가 확인 필요",
        "REJECT": "제안 비추천",
    }.get(decision, "추가 확인 필요")


def sales_grade_meanings() -> list[dict[str, Any]]:
    return [
        {"grade": "A", "range": "85~100", "meaning": "거래 가능성이 높고 적극 제안 가능한 구간"},
        {"grade": "B+", "range": "75~84.99", "meaning": "전반적으로 양호하며 일반적인 확인 후 제안 가능한 구간"},
        {"grade": "B", "range": "65~74.99", "meaning": "기본 제안은 가능하지만 조건 설명과 자료 확인이 필요한 구간"},
        {"grade": "C+", "range": "55~64.99", "meaning": "조건부 제안은 가능하나 추가 확인이 필요한 구간"},
        {"grade": "C", "range": "45~54.99", "meaning": "리스크가 커서 보수적 접근이 필요한 구간"},
        {"grade": "D", "range": "0~44.99", "meaning": "현 단계에서는 제안이 어렵거나 비추천인 구간"},
    ]


def sales_next_action(decision: str, has_knockout: bool, has_ews: bool) -> str:
    if decision == "REJECT" or has_knockout:
        return "지금은 바로 제안하지 말고 구조 보완 또는 대체 거래안을 먼저 검토합니다."
    if decision == "REVIEW" or has_ews:
        return "추가 자료를 받은 뒤 조건부 제안서로 접근하는 것이 좋습니다."
    return "현재 자료 기준으로는 제안서를 먼저 보내고 세부 조건을 협의하는 흐름이 적절합니다."


def resolve_reference_purchase_amount(input_data: dict[str, Any], limit_amount: int) -> tuple[int, str]:
    candidates = [
        ("requested_purchase_amount_krw", input_data.get("requested_purchase_amount_krw")),
        ("requested_purchase_amount", input_data.get("requested_purchase_amount")),
        ("purchase_amount_krw", input_data.get("purchase_amount_krw")),
        ("purchase_amount", input_data.get("purchase_amount")),
    ]
    for source, value in candidates:
        if value is None:
            continue
        amount = int(float(value))
        if amount > 0:
            return amount, source
    return limit_amount, "limit_reference"


def compute_margin_amounts(reference_amount: int, margin_result: dict[str, Any]) -> dict[str, Any]:
    if not margin_result.get("supported"):
        return {
            "reference_amount_krw": reference_amount,
            "commercial_margin_amount_krw": None,
            "compliant_margin_amount_krw": None,
        }

    commercial_margin_amount = int(round(reference_amount * (float(margin_result["commercial_rate_pct"]) / 100.0)))
    compliant_margin_amount = int(round(reference_amount * (float(margin_result["compliant_rate_pct"]) / 100.0)))
    return {
        "reference_amount_krw": reference_amount,
        "commercial_margin_amount_krw": commercial_margin_amount,
        "compliant_margin_amount_krw": compliant_margin_amount,
    }


def build_sales_view(result: dict[str, Any], input_data: dict[str, Any]) -> dict[str, Any]:
    recommendation = sales_decision_label(result["decision"])
    next_action = sales_next_action(
        decision=result["decision"],
        has_knockout=bool(result["knockout"]["reasons"]),
        has_ews=result["ews"]["triggered"],
    )
    reference_amount, reference_source = resolve_reference_purchase_amount(
        input_data=input_data,
        limit_amount=result["limit"]["single_delivery_limit_krw"],
    )
    margin_amounts = compute_margin_amounts(reference_amount, result["margin"])

    key_points = [
        f"예상 한도는 {result['limit']['single_delivery_limit_krw']:,}원 수준입니다.",
    ]
    if result["margin"].get("supported"):
        key_points.append(f"예상 마진율은 {result['margin']['commercial_rate_pct']:.2f}% 수준입니다.")
        key_points.append(
            f"기준 금액 {reference_amount:,}원으로 보면 예상 마진액은 {margin_amounts['commercial_margin_amount_krw']:,}원입니다."
        )
    else:
        key_points.append("결제기간이 표준 가격정책을 벗어나 마진율은 수기 협의가 필요합니다.")

    risk_notes: list[str] = []
    if result["knockout"]["reasons"]:
        risk_notes.extend(result["knockout"]["reasons"])
    if result["ews"]["triggered"]:
        risk_notes.extend(result["ews"]["triggers"])
    if result["industry_fit"]["ccc_ok"] is False:
        risk_notes.append("현금전환주기가 결제기간보다 길어 거래 구조 보완이 필요합니다.")

    return {
        "recommendation": recommendation,
        "next_action": next_action,
        "reference_purchase_amount_krw": reference_amount,
        "reference_purchase_amount_source": reference_source,
        "estimated_limit_krw": result["limit"]["single_delivery_limit_krw"],
        "estimated_margin_rate_pct": result["margin"].get("commercial_rate_pct"),
        "estimated_compliant_margin_rate_pct": result["margin"].get("compliant_rate_pct"),
        "estimated_margin_amount_krw": margin_amounts["commercial_margin_amount_krw"],
        "estimated_compliant_margin_amount_krw": margin_amounts["compliant_margin_amount_krw"],
        "key_points": key_points,
        "risk_notes": risk_notes,
    }


def generate_sales_summary(result: dict[str, Any]) -> str:
    sales_view = result["sales_view"]
    limit_amount = format(result["limit"]["single_delivery_limit_krw"], ",")
    applicant_grade = result["applicant"]["grade"]
    buyer_grade = result["buyer"]["grade"]
    overall_grade = result["overall"]["grade"]
    requested_tenor = result["requested_tenor_months"]
    margin = result["margin"]

    lines = [
        f"영업 참고 결과: {sales_view['recommendation']}",
        f"신청업체 참고등급은 {applicant_grade}, 매출처 참고등급은 {buyer_grade}, 통합 참고등급은 {overall_grade}입니다.",
        f"예상 1회 거래 한도는 {limit_amount}원이며, 제안 기준 결제기간은 {requested_tenor}개월입니다.",
    ]

    if margin.get("supported"):
        lines.append(
            f"영업 참고용 예상 마진율은 {margin['commercial_rate_pct']:.2f}%이고, 보수적으로 보면 {margin['compliant_rate_pct']:.2f}% 수준까지 설명하는 것이 안전합니다."
        )
    else:
        lines.append("현재 가격정책상 해당 결제기간은 자동 산정 대상이 아니며 별도 협의가 필요합니다.")

    if result["knockout"]["reasons"]:
        lines.append(f"제안 전 주의할 항목: {'; '.join(result['knockout']['reasons'])}")

    if result["ews"]["triggered"]:
        lines.append(f"추가 확인 신호: {', '.join(result['ews']['triggers'])}")

    api_enrichment = result.get("api_enrichment", {})
    if api_enrichment.get("summary_changes"):
        lines.append(f"외부 API 보강: {'; '.join(api_enrichment['summary_changes'])}")

    lines.append(f"권장 다음 행동: {sales_view['next_action']}")

    return " ".join(lines)


def generate_sales_email(result: dict[str, Any]) -> str:
    sales_view = result["sales_view"]
    limit_amount = format(result["limit"]["single_delivery_limit_krw"], ",")
    margin = result["margin"]

    if margin.get("supported"):
        margin_text = (
            f"현재 자료 기준으로는 결제기간 {result['requested_tenor_months']}개월 조건에서 "
            f"예상 마진율을 {margin['commercial_rate_pct']:.2f}% 수준으로 검토하고 있습니다."
        )
    else:
        margin_text = "요청하신 결제기간은 표준 기준을 벗어나 있어 세부 조건은 추가 협의가 필요합니다."

    caution_text = ""
    if result["sales_view"]["risk_notes"]:
        caution_text = f" 다만, {result['sales_view']['risk_notes'][0]} 신호는 추가 확인이 필요합니다."

    return (
        f"안녕하세요. 플로우페이 거래 가능성을 사전 검토한 내용을 공유드립니다.\n\n"
        f"현재 영업 참고 결과는 '{sales_view['recommendation']}'입니다. "
        f"예상 1회 거래 한도는 {limit_amount}원 수준으로 보고 있으며, {margin_text}{caution_text} "
        f"가능하시면 관련 증빙이나 추가 자료를 보내주시면 제안 조건을 더 구체화해드리겠습니다.\n\n"
        f"감사합니다."
    )


def generate_sales_report(result: dict[str, Any]) -> str:
    sales_view = result["sales_view"]
    score_breakdown = result.get("score_breakdown", {})
    proposal_context = result.get("proposal_context", {})
    purchase_supplier_name = (
        str(proposal_context.get("purchase_supplier_name") or proposal_context.get("supplier_name") or "").strip()
    )
    sales_destination_name = (
        str(proposal_context.get("sales_destination_name") or proposal_context.get("customer_name") or result["buyer"]["name"]).strip()
    )
    reference_source_map = {
        "requested_purchase_amount_krw": "입력된 매입액 기준",
        "requested_purchase_amount": "입력된 매입액 기준",
        "purchase_amount_krw": "입력된 매입액 기준",
        "purchase_amount": "입력된 매입액 기준",
        "limit_reference": "예상 한도액 기준",
    }
    reference_label = reference_source_map.get(sales_view["reference_purchase_amount_source"], "참고 금액 기준")

    lines = [
        "# 거래 가설 평가 리포트",
        f"영업 참고 결과: {sales_view['recommendation']}",
        "",
        "## 한눈에 보기",
        f"- 신청업체: {result['applicant']['name']}",
        f"- 매입처: {purchase_supplier_name or '-'}",
        f"- 매출처: {sales_destination_name}",
        f"- 제안 기준 결제기간: {result['requested_tenor_months']}개월",
        f"- 예상 거래 한도: {result['limit']['single_delivery_limit_krw']:,}원",
    ]

    if result["margin"].get("supported"):
        lines.extend(
            [
                f"- 예상 마진율: {result['margin']['commercial_rate_pct']:.2f}%",
                f"- 예상 마진액: {sales_view['estimated_margin_amount_krw']:,}원 ({reference_label}: {sales_view['reference_purchase_amount_krw']:,}원)",
            ]
        )
    else:
        lines.append("- 예상 마진율: 자동 산정 불가, 별도 협의 필요")

    lines.extend(
        [
            "",
            "## 기업과 거래 해석",
            f"- 신청업체 참고등급: {result['applicant']['grade']} / 점수 {result['applicant']['score']:.2f}",
            f"- 매출처 참고등급: {result['buyer']['grade']} / 점수 {result['buyer']['score']:.2f}",
            f"- 거래구조 참고등급: {result['transaction']['grade']} / 점수 {result['transaction']['score']:.2f}",
            f"- 통합 참고등급: {result['overall']['grade']} / 점수 {result['overall']['score']:.2f}",
            "",
            "## 영업 포인트",
        ]
    )
    for point in sales_view["key_points"]:
        lines.append(f"- {point}")

    if score_breakdown:
        lines.extend(["", "## 점수 계산 방식"])
        section_label_map = {
            "applicant": "신청업체",
            "buyer": "매출처",
            "transaction": "거래구조",
            "overall": "통합",
        }
        for section_name in ("applicant", "buyer", "transaction"):
            section = score_breakdown.get(section_name, {})
            if not section:
                continue
            item_texts = [
                f"{item['name']} {item['score']:.2f} x {item['weight'] * 100:.0f}% = {item['contribution']:.2f}"
                for item in section.get("items", [])
            ]
            if item_texts:
                lines.append(
                    f"- {section_label_map[section_name]} 점수: " + " + ".join(item_texts) + f" -> {section['total']:.2f}"
                )

        overall_section = score_breakdown.get("overall", {})
        overall_items = [
            f"{section_label_map.get(item['name'], item['name'])} {item['score']:.2f} x {item['weight'] * 100:.0f}% = {item['contribution']:.2f}"
            for item in overall_section.get("items", [])
        ]
        if overall_items:
            lines.append("- 통합 점수: " + " + ".join(overall_items) + f" -> {overall_section['total']:.2f}")

    lines.extend(["", "## 점수와 등급 기준", "- 모든 점수는 100점 만점 기준입니다."])
    for row in sales_grade_meanings():
        lines.append(f"- {row['grade']}: {row['range']} / {row['meaning']}")

    lines.extend(["", "## 주의할 점"])
    if sales_view["risk_notes"]:
        for note in sales_view["risk_notes"]:
            lines.append(f"- {note}")
    else:
        lines.append("- 현재 자료 기준으로 큰 경고 신호는 제한적입니다.")

    if result.get("api_enrichment", {}).get("summary_changes"):
        lines.extend(["", "## 외부 데이터 보강", *[f"- {item}" for item in result["api_enrichment"]["summary_changes"]]])

    lines.extend(
        [
            "",
            "## 권장 다음 행동",
            f"- {sales_view['next_action']}",
        ]
    )
    return "\n".join(lines)


def build_web_context(input_data: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    proposal_context = input_data.get("proposal_context", {})
    return {
        "analysis_type": result.get("analysis_type"),
        "engine_version": input_data.get("engine_version", "unversioned"),
        "company_name": result.get("company_name"),
        "requested_tenor_months": result.get("requested_tenor_months"),
        "decision": result.get("decision"),
        "proposal_context": proposal_context,
        "sales_view": result.get("sales_view", {}),
        "overall": result.get("overall", {}),
        "applicant": {
            "name": result.get("applicant", {}).get("name"),
            "score": result.get("applicant", {}).get("score"),
            "grade": result.get("applicant", {}).get("grade"),
        },
        "buyer": {
            "name": result.get("buyer", {}).get("name"),
            "score": result.get("buyer", {}).get("score"),
            "grade": result.get("buyer", {}).get("grade"),
        },
        "transaction": {
            "score": result.get("transaction", {}).get("score"),
            "grade": result.get("transaction", {}).get("grade"),
        },
        "limit": result.get("limit", {}),
        "margin": result.get("margin", {}),
        "ews": result.get("ews", {}),
        "knockout": result.get("knockout", {}),
        "industry_fit": result.get("industry_fit", {}),
        "api_enrichment": result.get("api_enrichment", {}),
        "score_breakdown": result.get("score_breakdown", {}),
        "proposal_draft": result.get("proposal_draft", ""),
        "sales_report": result.get("sales_report", ""),
        "sales_email_draft": result.get("sales_email_draft", ""),
        "sales_summary": result.get("sales_summary", ""),
    }


def write_sales_bundle(result: dict[str, Any], output_dir: Path, input_data: dict[str, Any] | None = None) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    files = {
        "sales_summary.txt": result.get("sales_summary", ""),
        "sales_report.md": result.get("sales_report", ""),
        "proposal_draft.md": result.get("proposal_draft", ""),
        "sales_email_draft.txt": result.get("sales_email_draft", ""),
    }
    for filename, content in files.items():
        (output_dir / filename).write_text(content, encoding="utf-8")
    if input_data is not None:
        web_context = build_web_context(input_data, result)
        (output_dir / "web_context.json").write_text(
            json.dumps(web_context, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


def evaluate_flowpay_underwriting(input_data: dict[str, Any], framework: dict[str, Any]) -> dict[str, Any]:
    model = framework["flowpay_underwriting"]
    input_data, api_enrichment = apply_api_enrichment(input_data, framework)
    requested_tenor_months = int(input_data.get("requested_tenor_months", 3))

    applicant_input = input_data["applicant"]
    buyer_input = input_data["buyer"]
    transaction_input = input_data["transaction"]

    applicant_scores = compute_model_scores(model["applicant"]["categories"], applicant_input["scores"])
    buyer_scores = compute_model_scores(model["buyer"]["categories"], buyer_input["scores"])
    transaction_scores = compute_model_scores(model["transaction"]["categories"], transaction_input["scores"])

    applicant_score = compute_weighted_score(applicant_scores, model["applicant"]["weights"], 0.0)
    buyer_score = compute_weighted_score(buyer_scores, model["buyer"]["weights"], 0.0)
    transaction_score = compute_weighted_score(transaction_scores, model["transaction"]["weights"], 0.0)
    overall_score = round(
        (applicant_score * float(model["overall_weights"]["applicant"]))
        + (buyer_score * float(model["overall_weights"]["buyer"]))
        + (transaction_score * float(model["overall_weights"]["transaction"])),
        2,
    )
    applicant_breakdown = build_weighted_breakdown(applicant_scores, model["applicant"]["weights"])
    buyer_breakdown = build_weighted_breakdown(buyer_scores, model["buyer"]["weights"])
    transaction_breakdown = build_weighted_breakdown(transaction_scores, model["transaction"]["weights"])
    overall_breakdown = build_weighted_breakdown(
        {
            "applicant": applicant_score,
            "buyer": buyer_score,
            "transaction": transaction_score,
        },
        model["overall_weights"],
    )

    applicant_grade = score_to_grade(applicant_score, model["party_grade_scale"])
    buyer_grade = score_to_grade(buyer_score, model["party_grade_scale"])
    transaction_grade = score_to_grade(transaction_score, model["party_grade_scale"])
    overall_grade = score_to_grade(overall_score, model["party_grade_scale"])

    knockout_reasons = detect_knockout_reasons(input_data, model)
    industry_fit = evaluate_industry_fit(input_data, model)
    ews_result = compute_ews(input_data, model)

    applicant_weak = build_deep_weaknesses(applicant_scores)
    buyer_weak = build_deep_weaknesses(buyer_scores)
    transaction_weak = build_deep_weaknesses(transaction_scores)

    applicant_pd = compute_pd_curve(applicant_score, len(applicant_weak), framework)
    buyer_pd = compute_pd_curve(buyer_score, len(buyer_weak), framework)
    overall_pd = compute_pd_curve(overall_score, len(applicant_weak) + len(buyer_weak) + len(transaction_weak), framework)

    limit_amount = compute_limit_amount(input_data, overall_score, buyer_score, model)
    margin_result = compute_margin_result(
        requested_tenor_months=requested_tenor_months,
        applicant_score=applicant_score,
        buyer_score=buyer_score,
        transaction_score=transaction_score,
        overall_score=overall_score,
        applicant_compliance_score=applicant_scores["compliance"],
        model=model,
    )

    strengths, weaknesses = build_strengths_and_weaknesses(
        {
            "applicant": applicant_score,
            "buyer": buyer_score,
            "transaction": transaction_score,
        }
    )

    decision = "APPROVE"
    if knockout_reasons:
        decision = "REJECT"
    elif overall_score < 60 or buyer_score < 55 or transaction_score < 55:
        decision = "REVIEW"

    result = {
        "analysis_type": "flowpay_underwriting",
        "company_name": input_data.get("company_name", applicant_input.get("company_name", "Unknown Applicant")),
        "requested_tenor_months": requested_tenor_months,
        "decision": decision,
        "knockout": {
            "passed": not knockout_reasons,
            "reasons": knockout_reasons,
        },
        "industry_fit": industry_fit,
        "overall": {
            "score": overall_score,
            "grade": overall_grade,
        },
        "applicant": {
            "name": applicant_input.get("company_name", "Applicant"),
            "score": applicant_score,
            "grade": applicant_grade,
            "category_scores": applicant_scores,
        },
        "buyer": {
            "name": buyer_input.get("company_name", "Buyer"),
            "score": buyer_score,
            "grade": buyer_grade,
            "category_scores": buyer_scores,
        },
        "transaction": {
            "score": transaction_score,
            "grade": transaction_grade,
            "category_scores": transaction_scores,
        },
        "score_breakdown": {
            "applicant": applicant_breakdown,
            "buyer": buyer_breakdown,
            "transaction": transaction_breakdown,
            "overall": overall_breakdown,
        },
        "default_probability": {
            "applicant": applicant_pd,
            "buyer": buyer_pd,
            "overall": overall_pd,
        },
        "limit": {
            "single_delivery_limit_krw": limit_amount,
        },
        "margin": margin_result,
        "ews": ews_result,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "api_enrichment": api_enrichment,
        "proposal_context": input_data.get("proposal_context", {}),
    }

    result["sales_view"] = build_sales_view(result, input_data)
    result["report_summary"] = generate_sales_summary(result)
    result["sales_summary"] = result["report_summary"]
    result["email_draft"] = generate_sales_email(result)
    result["sales_email_draft"] = result["email_draft"]
    result["sales_report"] = generate_sales_report(result)
    result["proposal_draft"] = generate_bizaipro_proposal(input_data, result)
    return result


def format_table(framework: dict[str, Any]) -> str:
    lines = []
    header = f"{'Category':<20} {'Integrated':>10} {'KIS':>10} {'NICE':>10} {'KR':>10}"
    lines.append(header)
    lines.append("-" * len(header))

    for category_name in framework["categories"]:
        integrated = framework["integrated_weights"][category_name]
        kis = framework["agency_weights"]["KIS"][category_name]
        nice = framework["agency_weights"]["NICE"][category_name]
        kr = framework["agency_weights"]["KR"][category_name]
        lines.append(
            f"{category_name:<20} {integrated:>10.2%} {kis:>10.2%} {nice:>10.2%} {kr:>10.2%}"
        )
    return "\n".join(lines)


def print_result(result: dict[str, Any]) -> None:
    print(f"Company: {result['company_name']}")
    print(f"Industry: {result['industry']}")
    print(f"Modifier total: {result['modifier_total']:+.2f}")
    print()
    print("Integrated View")
    print(f"  Score : {result['integrated']['score']:.2f}")
    print(f"  Rating: {result['integrated']['rating']}")
    print()
    print("Agency Views")
    for agency in result["agencies"]:
        print(f"  {agency['name']:<5} Score {agency['score']:.2f}  Rating {agency['rating']}")
    print()
    print("Category Scores")
    for category_name, score in result["category_scores"].items():
        print(f"  {category_name:<20} {score:.2f}")
    print()
    print("Top Strengths")
    for line in result["strengths"]:
        print(f"  - {line}")
    print("Top Weaknesses")
    for line in result["weaknesses"]:
        print(f"  - {line}")


def print_flowpay_result(result: dict[str, Any]) -> None:
    print(f"Company: {result['company_name']}")
    print(f"Industry: {result['industry']}")
    print("Analysis: FlowPay 3M Receivable Survival")
    print()
    print("Survival View")
    print(f"  Base score         : {result['base_score']:.2f}")
    print(f"  Reporting haircut  : {result['reporting_haircut']:+.2f}")
    print(f"  Other modifiers    : {result['modifier_total']:+.2f}")
    print(f"  Total adjustment   : {result['total_adjustment']:+.2f}")
    print(f"  Final score        : {result['survival']['score']:.2f}")
    print(f"  Judgment           : {result['survival']['judgment']}")
    print(f"  Survival prob.     : {result['survival']['survival_probability']}")
    print(f"  Data confidence    : {result['confidence_level']}")
    print()
    print("Category Scores")
    for category_name, score in result["category_scores"].items():
        print(f"  {category_name:<24} {score:.2f}")
    print()
    print("Top Strengths")
    for line in result["strengths"]:
        print(f"  - {line}")
    print("Top Weaknesses")
    for line in result["weaknesses"]:
        print(f"  - {line}")


def print_flowpay_underwriting_result(result: dict[str, Any]) -> None:
    print(f"Company: {result['company_name']}")
    print("Analysis: FlowPay Sales Opportunity")
    print(f"Sales recommendation: {result['sales_view']['recommendation']}")
    print(f"Requested tenor: {result['requested_tenor_months']} month(s)")
    print()
    print("Sales View")
    print(f"  Recommendation       : {result['sales_view']['recommendation']}")
    print(f"  Next action          : {result['sales_view']['next_action']}")
    print(f"  Estimated limit      : {result['sales_view']['estimated_limit_krw']:,} KRW")
    if result["sales_view"].get("estimated_margin_rate_pct") is not None:
        print(f"  Estimated margin     : {result['sales_view']['estimated_margin_rate_pct']:.2f}%")
    if result["sales_view"].get("estimated_margin_amount_krw") is not None:
        print(f"  Estimated margin amt : {result['sales_view']['estimated_margin_amount_krw']:,} KRW")
    print()
    print("Reference Scores")
    print(f"  Overall     Score {result['overall']['score']:.2f}  Grade {result['overall']['grade']}")
    print(f"  Applicant   {result['applicant']['name']}  Score {result['applicant']['score']:.2f}  Grade {result['applicant']['grade']}")
    print(f"  Buyer       {result['buyer']['name']}  Score {result['buyer']['score']:.2f}  Grade {result['buyer']['grade']}")
    print(f"  Transaction Score {result['transaction']['score']:.2f}  Grade {result['transaction']['grade']}")
    print()
    print("Estimated Terms")
    print(f"  Estimated transaction limit: {result['limit']['single_delivery_limit_krw']:,} KRW")
    print()
    print("Estimated Margin")
    if result["margin"].get("supported"):
        print(f"  Sales reference rate : {result['margin']['commercial_rate_pct']:.2f}%")
        print(f"  Conservative rate    : {result['margin']['compliant_rate_pct']:.2f}%")
        print(f"  Legal cap for tenor  : {result['margin']['legal_cap_rate_pct_for_tenor']:.2f}%")
    else:
        print(f"  {result['margin']['reason']}")
    print()
    print("Risk Checks")
    print(f"  Passed hard checks: {result['knockout']['passed']}")
    if result["knockout"]["reasons"]:
        for reason in result["knockout"]["reasons"]:
            print(f"  - {reason}")
    print()
    print("Industry Fit")
    print(f"  Profile               : {result['industry_fit']['industry_profile']}")
    print(f"  Operating margin OK   : {result['industry_fit']['operating_margin_ok']}")
    print(f"  EBITDA/Interest OK    : {result['industry_fit']['ebitda_interest_ok']}")
    print(f"  CCC within tenor      : {result['industry_fit']['ccc_ok']}")
    print()
    print("Additional Check Signals")
    print(f"  Triggered: {result['ews']['triggered']}")
    for trigger in result["ews"]["triggers"]:
        print(f"  - {trigger}")
    print()
    api_enrichment = result.get("api_enrichment", {})
    if api_enrichment.get("enabled"):
        print("API Enrichment")
        if api_enrichment.get("summary_changes"):
            for change in api_enrichment["summary_changes"]:
                print(f"  - {change}")
        else:
            print("  - No score overrides applied")
        for warning in api_enrichment.get("warnings", []):
            print(f"  * {warning}")
        print()
    print("Monthly Risk Curve")
    for row in result["default_probability"]["overall"]:
        print(
            f"  Month {row['month']}: default {row['default_probability_pct']:.2f}% / survival {row['survival_probability_pct']:.2f}%"
        )
    print()
    print("Sales Summary")
    print(f"  {result['sales_summary']}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="FlowPay sales automation engine for opportunity scoring, proposal drafting, and email drafting.")
    parser.add_argument("--input", type=Path, help="Path to input JSON file.")
    parser.add_argument("--show-table", action="store_true", help="Show agency comparison weights.")
    parser.add_argument("--json", action="store_true", help="Print result as JSON.")
    parser.add_argument("--bundle-out", type=Path, help="Write sales summary, report, proposal, and email drafts to a directory.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    framework = load_json(FRAMEWORK_PATH)

    if args.show_table:
        print(format_table(framework))
        if not args.input:
            return
        print()

    if not args.input:
        raise SystemExit("Provide --input <file.json> or use --show-table.")

    input_data = load_json(args.input)
    analysis_type = input_data.get("analysis_type", "corporate_rating")

    if analysis_type == "flowpay_3m_receivable":
        result = evaluate_flowpay_3m(input_data, framework)
    elif analysis_type == "flowpay_underwriting":
        result = evaluate_flowpay_underwriting(input_data, framework)
    else:
        result = evaluate(input_data, framework)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if args.bundle_out and analysis_type == "flowpay_underwriting":
            write_sales_bundle(result, args.bundle_out, input_data)
        return

    if analysis_type == "flowpay_3m_receivable":
        print_flowpay_result(result)
    elif analysis_type == "flowpay_underwriting":
        print_flowpay_underwriting_result(result)
        if args.bundle_out:
            write_sales_bundle(result, args.bundle_out, input_data)
            print()
            print(f"Bundle written to: {args.bundle_out}")
    else:
        print_result(result)


if __name__ == "__main__":
    main()
