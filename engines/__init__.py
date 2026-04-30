"""Engine registry — 단일 진입점.

새 엔진 추가 시 _REGISTRY에 등록만 하면 API/CLI/UI가 자동 인식한다.

사용 예:
    from engines import get_engine, list_engines
    fpe = get_engine("fpe")
    result = fpe.evaluate(input_data, framework=...)

Aliases (case-insensitive 우선, fallback case-sensitive):
- FPE: "fpe", "FPE", "FPE_v.16.01", "FPE_v16.01", "fpe_v1601", "fpe_v.16.01"
- APE: "ape", "APE", "APE_v1.01", "ape_v1_01"
"""
from __future__ import annotations

from typing import Any

from . import ape, fpe
from ._base import EngineMeta

_REGISTRY: dict[str, Any] = {}


def _register(engine_module, aliases: list[str]) -> None:
    for alias in aliases:
        _REGISTRY[alias] = engine_module
        _REGISTRY[alias.lower()] = engine_module


_register(fpe, [
    "FPE", "FPE_v.16.01", "FPE_v16.01", "fpe_v1601", "fpe_v.16.01",
])
_register(ape, [
    "APE", "APE_v1.01", "ape_v1_01",
])


def get_engine(alias: str):
    """alias로 엔진 모듈 조회 — case-insensitive 우선."""
    if not alias:
        raise ValueError("Engine alias is required")
    key = alias.strip()
    if key in _REGISTRY:
        return _REGISTRY[key]
    if key.lower() in _REGISTRY:
        return _REGISTRY[key.lower()]
    raise ValueError(f"Unknown engine alias: {alias}")


def list_engines() -> list[dict[str, Any]]:
    """모든 등록된 엔진의 메타를 반환 — /api/engine/list에서 사용."""
    seen = set()
    result = []
    for module in _REGISTRY.values():
        meta = module.META
        if meta.engine_id in seen:
            continue
        seen.add(meta.engine_id)
        result.append(meta.asdict())
    return result


__all__ = ["get_engine", "list_engines", "EngineMeta", "ape", "fpe"]
