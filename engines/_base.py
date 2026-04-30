"""Common helpers shared across engine packages.

Each engine module exposes:
- META: dataclass-like object with engine_id/engine_label/engine_version/engine_locked/engine_purpose
- evaluate(input_data, **kwargs) -> dict
- get_meta() -> dict (serializable form of META)
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


@dataclass(frozen=True)
class EngineMeta:
    engine_id: str          # "FPE" | "APE"
    engine_label: str       # "FPE_v.16.01" | "APE_v1.01"
    engine_version: str     # "16.01" | "v.1.18.02"
    engine_locked: bool     # FPE=True (학습 안 함), APE=False
    engine_purpose: str     # "fixed_screening" | "learning_proposal"
    policy_source: str = "" # 정책 출처 (예: "276holdings_limit_policy_manual")

    def asdict(self) -> dict[str, Any]:
        return asdict(self)
