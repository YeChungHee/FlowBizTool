"""FPE_v.16.01 정책 로더 + 등급 helper — 메인 engine.py로부터 6개 helper re-export.

v2.11 마이그레이션 단계:
  1차 (현 PR): engine.py에서 정책/등급 helper re-export. 정책 파일은 dual-read fallback.
  2차 (후속 PR): 함수 본체를 본 파일로 점진 이동.

6 helper:
  fpe_policy_grade, _normalize_credit_grade,
  _credit_enhancement_level, _item_type_level,
  _buyer_grade_level, _ews_level
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent.parent.parent
NEW_PATH = BASE_DIR / "data" / "engines" / "fpe" / "policy.json"
LEGACY_PATH = BASE_DIR / "data" / "fpe_v1601_policy.json"

# 신규 경로 우선 → legacy fallback. 둘 다 없으면 정책 파일 부재 (FPE 미지원)
FPE_POLICY_PATH = NEW_PATH if NEW_PATH.exists() else LEGACY_PATH


def load_policy() -> dict[str, Any]:
    """276홀딩스 정책 JSON 로드. 신규 경로 → legacy 순 탐색."""
    for path in (NEW_PATH, LEGACY_PATH):
        if path.exists():
            with path.open("r", encoding="utf-8") as fp:
                return json.load(fp)
    return {}


# v2.11 1차: 메인 engine.py에서 본체 import. 2차에서 본체 이동 예정.
from engine import (
    fpe_policy_grade,
    _normalize_credit_grade,
    _credit_enhancement_level,
    _item_type_level,
    _buyer_grade_level,
    _ews_level,
)
