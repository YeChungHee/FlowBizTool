#!/usr/bin/env python3
"""APE/FPE/common 분리를 위한 dependency closure 추출 (v2.11).

v2.11 핵심:
- evaluate_flowpay_underwriting을 FPE closure boundary leaf로 처리
- ALLOWED_COMMON 8 helper를 APE/FPE 모듈에서 명시적으로 제외
- 출력 3구역(common / APE module / FPE module)이 상호 배제(disjoint)
"""
import ast
import sys
from pathlib import Path

ALLOWED_COMMON = {
    "load_json", "_safe_float", "_safe_int", "_round_krw",
    "bounded_score", "score_band_multiplier",
    "resolve_reference_purchase_amount", "compute_margin_amounts",
}
APE_ROOT = "evaluate_flowpay_underwriting"
FPE_ROOT = "evaluate_fpe_v1601"


def main() -> int:
    src = Path("engine.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    funcs = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}

    if APE_ROOT not in funcs:
        print(f"[FAIL] {APE_ROOT} 함수가 engine.py에 없음")
        return 1
    if FPE_ROOT not in funcs:
        print(f"[FAIL] {FPE_ROOT} 함수가 engine.py에 없음")
        return 1

    calls_in: dict[str, set[str]] = {}
    for name, node in funcs.items():
        calls = set()
        for sub in ast.walk(node):
            if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Name):
                if sub.func.id in funcs:
                    calls.add(sub.func.id)
        calls_in[name] = calls

    def closure(start: str, calls: dict, boundary: set[str] = frozenset()) -> set[str]:
        seen = {start}
        stack = [start]
        while stack:
            f = stack.pop()
            if f in boundary and f != start:
                continue
            for callee in calls.get(f, ()):
                if callee not in seen:
                    seen.add(callee)
                    stack.append(callee)
        return seen

    ape_funcs = closure(APE_ROOT, calls_in)
    fpe_funcs = closure(FPE_ROOT, calls_in, boundary={APE_ROOT})

    # ALLOWED_COMMON과 closure 합집합으로 common 산출
    common_funcs = ALLOWED_COMMON & (ape_funcs | fpe_funcs)

    # APE/FPE 모듈에서 common helper 명시적 제외
    ape_module_funcs = ape_funcs - common_funcs
    fpe_module_funcs = (fpe_funcs - {APE_ROOT}) - common_funcs

    # disjoint 검증
    overlap_acm = ape_module_funcs & common_funcs
    overlap_fcm = fpe_module_funcs & common_funcs
    overlap_apf = ape_module_funcs & fpe_module_funcs
    if overlap_acm or overlap_fcm or overlap_apf:
        print("[FAIL] 구역 중복 발견:")
        if overlap_acm: print(f"  APE ∩ common: {sorted(overlap_acm)}")
        if overlap_fcm: print(f"  FPE ∩ common: {sorted(overlap_fcm)}")
        if overlap_apf: print(f"  APE ∩ FPE   : {sorted(overlap_apf)}")
        return 1

    # ALLOWED_COMMON 외 양쪽 의존 발견 시 경고
    extra_common = (ape_funcs & fpe_funcs) - {APE_ROOT} - common_funcs
    if extra_common:
        print(f"[WARN] ALLOWED_COMMON 외 양쪽 의존 발견 (검토 필요): {sorted(extra_common)}")
        print("       이들은 ALLOWED_COMMON 화이트리스트에 추가하거나 APE 본체로 분류해야 함.")

    print(f"=== common.py 고정 ({len(common_funcs)}/{len(ALLOWED_COMMON)}개 사용 중) ===")
    for f in sorted(common_funcs):
        print(f"  {f}")

    print(f"\n=== APE module → engines/ape/eval.py ({len(ape_module_funcs)}개) ===")
    for f in sorted(ape_module_funcs):
        print(f"  {f}")

    print(f"\n=== FPE module → engines/fpe/{{eval,view,policy}}.py ({len(fpe_module_funcs)}개) ===")
    for f in sorted(fpe_module_funcs):
        print(f"  {f}")

    print(f"\n[OK] 3구역 disjoint 검증 통과")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
