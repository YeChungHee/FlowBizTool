"""순수 helper. 어떤 engines/* 모듈도 import하지 않는다 (terminal node).

v2.11 ALLOWED_COMMON 화이트리스트: 8개 helper. 메인 engine.py에서 본체 그대로 이동.
"""
from __future__ import annotations

from typing import Any
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

__all__ = [
    "load_json",
    "_safe_float",
    "_safe_int",
    "_round_krw",
    "bounded_score",
    "score_band_multiplier",
    "resolve_reference_purchase_amount",
    "compute_margin_amounts",
]


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fp:
        return json.load(fp)


def bounded_score(value: float) -> float:
    return max(0.0, min(100.0, float(value)))


def score_band_multiplier(score: float, bands: list[tuple[float, float]]) -> float:
    for minimum, value in bands:
        if score >= minimum:
            return value
    return bands[-1][1]


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, ""):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value in (None, ""):
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _round_krw(value: float, unit: int = 1000) -> int:
    if value <= 0:
        return 0
    return int(round(value / unit) * unit)


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
