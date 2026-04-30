"""FPE_v.16.01 — 276홀딩스 한도 정책 매뉴얼 기반 고정 심사엔진.

학습하지 않음. 정책 파일 (data/engines/fpe/policy.json)이 모든 평가 기준.

머지 후 활성화 단계:
1. data/fpe_v1601_policy.json → data/engines/fpe/policy.json 이동
2. engine.py의 evaluate_fpe_v1601 + 8 helper → engines/fpe/eval.py로 이동
3. engine.py 호환 shim에 re-export 추가
"""
from __future__ import annotations

from .._base import EngineMeta
from .policy import FPE_POLICY_PATH, load_policy, fpe_policy_grade
from .eval import evaluate, evaluate_fpe_v1601


META = EngineMeta(
    engine_id="FPE",
    engine_label="FPE_v.16.01",
    engine_version="16.01",
    engine_locked=True,
    engine_purpose="fixed_screening",
    policy_source="276holdings_limit_policy_manual",
)


def get_meta() -> dict:
    base = META.asdict()
    policy = load_policy()
    base["policy_loaded"] = bool(policy)
    base["policy_path"] = str(FPE_POLICY_PATH)
    return base


__all__ = [
    "META",
    "get_meta",
    "evaluate",
    "evaluate_fpe_v1601",
    "load_policy",
    "fpe_policy_grade",
    "FPE_POLICY_PATH",
]
