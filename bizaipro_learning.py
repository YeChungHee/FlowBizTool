from __future__ import annotations

import argparse
import copy
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from engine import FRAMEWORK_PATH, evaluate_flowpay_underwriting, load_json


BASE_DIR = Path(__file__).resolve().parent
REGISTRY_PATH = BASE_DIR / "data" / "bizaipro_learning_registry.json"
UPDATES_DIR = BASE_DIR / "outputs" / "bizaipro_updates"
ACTIVE_FRAMEWORK_PATH = BASE_DIR / "data" / "active_framework.json"
BASELINE_VERSION = "v.1.0.00"


@dataclass
class LearningProgress:
    total_candidates: int
    qualified_cases: int
    weighted_total: float
    ready_for_update: bool
    remaining_cases: int
    remaining_weight_gap: float


def utc_now_text() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def load_registry(path: Path = REGISTRY_PATH) -> dict[str, Any]:
    if path.exists():
        with path.open("r", encoding="utf-8") as fp:
            return json.load(fp)
    return {
        "engine_name": "BizAiPro",
        "current_version": BASELINE_VERSION,
        "cases": [],
        "updates": [],
    }


def save_registry(registry: dict[str, Any], path: Path = REGISTRY_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fp:
        json.dump(registry, fp, ensure_ascii=False, indent=2)


def _learning_context(input_data: dict[str, Any]) -> dict[str, Any]:
    context = input_data.get("learning_context")
    if isinstance(context, dict):
        return context
    return {}


_DQ_KEY_FIELDS = [
    "companyName", "representativeName", "businessNumber",
    "creditGrade", "annualSales", "buyerName", "supplierName",
    "requestedTenorDays", "reportIncorporatedDate",
]


def ensure_data_quality(input_data: dict[str, Any]) -> dict[str, Any]:
    """CLI 입력 JSON에 data_quality 필드가 없으면 자동 계산해 삽입."""
    if "data_quality" in input_data:
        return input_data
    missing: list[str] = []
    defaulted: list[str] = []
    for field in _DQ_KEY_FIELDS:
        val = input_data.get(field)
        if val is None or (isinstance(val, str) and not val.strip()):
            missing.append(field)
            # Known defaults
            defaults = {
                "annualSales": "annualSales→0",
                "buyerName": "buyerName→'매출처 확인 필요'",
                "supplierName": "supplierName→'매입처 확인 필요'",
                "requestedTenorDays": "requestedTenorDays→60",
                "reportIncorporatedDate": "reportIncorporatedDate→businessYears=0",
            }
            if field in defaults:
                defaulted.append(defaults[field])
    confidence = round(1.0 - len(missing) / len(_DQ_KEY_FIELDS), 2)
    patched = dict(input_data)
    patched["data_quality"] = {
        "missing_fields": missing,
        "defaulted_fields": defaulted,
        "data_confidence": confidence,
    }
    return patched


def compute_learning_weight(input_data: dict[str, Any]) -> dict[str, Any]:
    """Compute learning weight aligned with the web update_eligible criteria (FBU-VAL-0006 F3).

    Previously: qualified = flow_score AND consultation  (CLI only)
    Now:        evaluation_ready = flow_score AND (consultation OR meeting)
                update_eligible  = evaluation_ready AND internal_review  (same as web)
                qualified        = update_eligible  (unified definition)

    meeting_report (0.10) is an independent complement to consultation_report.
    """
    context = _learning_context(input_data)
    flow_score = bool(context.get("flow_score_report_submitted", False))
    consultation = bool(context.get("consultation_report_submitted", False))
    meeting_report = bool(context.get("meeting_report_submitted", False))
    internal_review = bool(context.get("internal_review_link"))
    additional_sources = context.get("additional_sources", [])
    additional_count = len(additional_sources) if isinstance(additional_sources, list) else 0

    components = {
        "flow_score_report": 0.35 if flow_score else 0.0,
        "consultation_report": 0.35 if consultation else 0.0,
        "meeting_report": 0.10 if meeting_report else 0.0,
        "internal_review": 0.15 if internal_review else 0.0,
        "additional_sources": min(additional_count, 3) * 0.05,
    }
    total_weight = round(sum(components.values()), 2)
    # evaluation_ready: meeting이 consultation을 보완 — 둘 중 하나만 있어도 통과
    has_report_coverage = consultation or meeting_report
    evaluation_ready = flow_score and has_report_coverage
    update_eligible = evaluation_ready and internal_review
    return {
        "evaluation_ready": evaluation_ready,
        "update_eligible": update_eligible,
        "qualified": update_eligible,  # unified: qualified == update_eligible
        "total_weight": total_weight,
        "components": components,
        "additional_source_count": additional_count,
    }


def learning_progress(registry: dict[str, Any]) -> LearningProgress:
    qualified_cases = [case for case in registry["cases"] if case["learning"]["qualified"]]
    weighted_total = round(sum(float(case["learning"]["total_weight"]) for case in qualified_cases), 2)
    qualified_count = len(qualified_cases)
    ready = qualified_count >= 10 and weighted_total >= 7.5
    return LearningProgress(
        total_candidates=len(registry["cases"]),
        qualified_cases=qualified_count,
        weighted_total=weighted_total,
        ready_for_update=ready,
        remaining_cases=max(0, 10 - qualified_count),
        remaining_weight_gap=round(max(0.0, 7.5 - weighted_total), 2),
    )


def _case_id(registry: dict[str, Any]) -> str:
    return f"case-{len(registry['cases']) + 1:04d}"


def record_learning_case(input_path: Path, label: str | None = None, registry_path: Path = REGISTRY_PATH) -> dict[str, Any]:
    registry = load_registry(registry_path)
    framework = load_json(FRAMEWORK_PATH)
    input_data = load_json(input_path)

    if input_data.get("analysis_type") != "flowpay_underwriting":
        raise ValueError("BizAiPro learning only supports flowpay_underwriting inputs.")

    input_data = ensure_data_quality(input_data)
    result = evaluate_flowpay_underwriting(input_data, framework)
    learning_meta = compute_learning_weight(input_data)

    case = {
        "id": _case_id(registry),
        "label": label or input_data.get("company_name") or input_path.stem,
        "input_path": str(input_path),
        "created_at": utc_now_text(),
        "engine_version": registry.get("current_version", BASELINE_VERSION),
        "input_data": input_data,
        "result_snapshot": result,
        "learning": learning_meta,
    }
    registry["cases"].append(case)
    save_registry(registry, registry_path)
    progress = learning_progress(registry)

    return {
        "case_id": case["id"],
        "label": case["label"],
        "engine_version": case["engine_version"],
        "qualified": learning_meta["qualified"],
        "learning_weight": learning_meta["total_weight"],
        "progress": progress.__dict__,
    }


def _current_week() -> int:
    return datetime.now().isocalendar().week


def next_version_name(registry: dict[str, Any]) -> str:
    week = _current_week()
    week_updates = [
        item
        for item in registry.get("updates", [])
        if int(str(item["version"]).split(".")[2]) == week
    ]
    sequence = len(week_updates) + 1
    return f"v.1.{week}.{sequence:02d}"


def build_updated_framework(base_framework: dict[str, Any], qualifying_cases: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any]]:
    framework = copy.deepcopy(base_framework)
    model = framework["flowpay_underwriting"]
    base_weights = model["overall_weights"]

    total_weight = sum(case["learning"]["total_weight"] for case in qualifying_cases) or 1.0
    weighted_scores = {"applicant": 0.0, "buyer": 0.0, "transaction": 0.0}
    for case in qualifying_cases:
        weight = float(case["learning"]["total_weight"])
        snapshot = case["result_snapshot"]
        weighted_scores["applicant"] += float(snapshot["applicant"]["score"]) * weight
        weighted_scores["buyer"] += float(snapshot["buyer"]["score"]) * weight
        weighted_scores["transaction"] += float(snapshot["transaction"]["score"]) * weight

    avg_scores = {name: weighted_scores[name] / total_weight for name in weighted_scores}

    # We increase the weight on the weaker area so future evaluations become a bit more conservative there.
    base_target = 65.0
    raw_weights = {}
    for name, base_weight in base_weights.items():
        score_gap = max(0.0, base_target - avg_scores[name])
        multiplier = 1.0 + min(0.20, score_gap / 100.0)
        raw_weights[name] = float(base_weight) * multiplier

    normalized_total = sum(raw_weights.values()) or 1.0
    new_weights = {name: round(raw_weights[name] / normalized_total, 4) for name in raw_weights}
    model["overall_weights"] = new_weights

    # Margin sensitivity also becomes slightly more conservative when weighted average quality is low.
    avg_learning_weight = total_weight / max(len(qualifying_cases), 1)
    commercial_max = model["margin"]["max_rate_by_month"]
    margin_cap_adjustment = 0.0 if avg_learning_weight >= 0.9 else 0.5
    adjusted_margin_caps = {
        month: round(float(value) + margin_cap_adjustment, 2)
        for month, value in commercial_max.items()
    }
    model["margin"]["max_rate_by_month"] = adjusted_margin_caps

    update_summary = {
        "applied_overall_weights": new_weights,
        "average_scores": {name: round(value, 2) for name, value in avg_scores.items()},
        "average_learning_weight": round(avg_learning_weight, 2),
        "applied_margin_caps": adjusted_margin_caps,
    }
    return framework, update_summary


def reevaluate_cases_with_framework(cases: list[dict[str, Any]], framework: dict[str, Any], version_name: str) -> list[dict[str, Any]]:
    reevaluated: list[dict[str, Any]] = []
    for case in cases:
        result = evaluate_flowpay_underwriting(case["input_data"], framework)
        reevaluated.append(
            {
                "case_id": case["id"],
                "label": case["label"],
                "version": version_name,
                "before": case["result_snapshot"],
                "after": result,
                "learning_weight": case["learning"]["total_weight"],
            }
        )
    return reevaluated


def build_comparison_report(
    previous_version: str,
    new_version: str,
    update_generated: bool,
    update_summary: dict[str, Any],
    progress: LearningProgress,
    reevaluated_cases: list[dict[str, Any]],
) -> str:
    lines = [
        "# BizAiPro 업데이트 비교 리포트",
        "",
        f"- 이전 버전: {previous_version}",
        f"- 새 버전: {new_version}",
        f"- 업데이트 생성 여부: {'생성됨' if update_generated else '미생성'}",
        f"- 학습 적격 건수: {progress.qualified_cases}건",
        f"- 누적 학습 가중치: {progress.weighted_total}",
        "",
        "## 적용 가중치",
        f"- 신청업체 가중치: {update_summary['applied_overall_weights']['applicant']:.2%}",
        f"- 매출처 가중치: {update_summary['applied_overall_weights']['buyer']:.2%}",
        f"- 거래구조 가중치: {update_summary['applied_overall_weights']['transaction']:.2%}",
        "",
        "## 평균 참고점수",
        f"- 신청업체 평균점수: {update_summary['average_scores']['applicant']:.2f}",
        f"- 매출처 평균점수: {update_summary['average_scores']['buyer']:.2f}",
        f"- 거래구조 평균점수: {update_summary['average_scores']['transaction']:.2f}",
        "",
        "## 케이스별 전후 비교",
    ]

    for item in reevaluated_cases:
        before = item["before"]
        after = item["after"]
        delta = round(float(after["overall"]["score"]) - float(before["overall"]["score"]), 2)
        lines.extend(
            [
                f"### {item['label']} ({item['case_id']})",
                f"- 학습 가중치: {item['learning_weight']}",
                f"- 이전 결과: {before['sales_view']['recommendation']} / {before['overall']['score']:.2f}",
                f"- 새 결과: {after['sales_view']['recommendation']} / {after['overall']['score']:.2f}",
                f"- 통합점수 변화: {delta:+.2f}",
            ]
        )

    return "\n".join(lines)


def run_update(registry_path: Path = REGISTRY_PATH, output_dir: Path = UPDATES_DIR) -> dict[str, Any]:
    registry = load_registry(registry_path)
    progress = learning_progress(registry)
    qualifying_cases = [case for case in registry["cases"] if case["learning"]["qualified"]][-10:]

    if not progress.ready_for_update:
        return {
            "update_generated": False,
            "current_version": registry.get("current_version", BASELINE_VERSION),
            "progress": progress.__dict__,
            "reason": "학습 적격 10건과 최소 가중치 7.5를 충족해야 합니다.",
        }

    previous_version = registry.get("current_version", BASELINE_VERSION)
    new_version = next_version_name(registry)

    base_framework = load_json(FRAMEWORK_PATH)
    updated_framework, update_summary = build_updated_framework(base_framework, qualifying_cases)
    reevaluated_cases = reevaluate_cases_with_framework(qualifying_cases, updated_framework, new_version)

    report = build_comparison_report(
        previous_version=previous_version,
        new_version=new_version,
        update_generated=True,
        update_summary=update_summary,
        progress=progress,
        reevaluated_cases=reevaluated_cases,
    )

    version_dir = output_dir / new_version
    version_dir.mkdir(parents=True, exist_ok=True)
    (version_dir / "comparison_report.md").write_text(report, encoding="utf-8")
    # framework_snapshot: promote 전까지 라이브 API에 적용되지 않는 대기 상태
    (version_dir / "framework_snapshot.json").write_text(
        json.dumps(updated_framework, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (version_dir / "update_summary.json").write_text(
        json.dumps(
            {
                "previous_version": previous_version,
                "new_version": new_version,
                "update_generated": True,
                "progress": progress.__dict__,
                "weighting": update_summary,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    registry["current_version"] = new_version
    registry["updates"].append(
        {
            "version": new_version,
            "created_at": utc_now_text(),
            "previous_version": previous_version,
            "update_generated": True,
            "progress": progress.__dict__,
            "weighting": update_summary,
            "output_dir": str(version_dir),
        }
    )
    save_registry(registry, registry_path)

    snapshot_path = version_dir / "framework_snapshot.json"
    return {
        "update_generated": True,
        "previous_version": previous_version,
        "new_version": new_version,
        "progress": progress.__dict__,
        "weighting": update_summary,
        "output_dir": str(version_dir),
        "snapshot_path": str(snapshot_path),
        "promote_hint": f"python3 bizaipro_learning.py promote --version {new_version}",
    }


def run_promote(version: str | None = None, output_dir: Path = UPDATES_DIR) -> dict[str, Any]:
    """스냅샷을 active_framework.json으로 승격(promote)해 라이브 API에 적용."""
    registry = load_registry()

    # 버전 미지정 시 최신 업데이트 사용
    if version is None:
        updates = registry.get("updates") or []
        if not updates:
            return {"promoted": False, "reason": "promote 가능한 업데이트가 없습니다. run update 먼저 실행하세요."}
        version = updates[-1]["version"]

    snapshot_path = output_dir / version / "framework_snapshot.json"
    if not snapshot_path.exists():
        return {"promoted": False, "reason": f"framework_snapshot.json 없음: {snapshot_path}"}

    snapshot = load_json(snapshot_path)

    # Shadow evaluation: 직전 qualified 케이스 최대 3건으로 before/after 비교
    qualifying_cases = [c for c in registry["cases"] if c["learning"]["qualified"]][-3:]
    shadow = []
    for case in qualifying_cases:
        before = case.get("result_snapshot")
        after = evaluate_flowpay_underwriting(case["input_data"], snapshot)
        if before:
            delta = round(float(after["overall"]["score"]) - float(before["overall"]["score"]), 2)
            shadow.append({
                "case_id": case["id"],
                "label": case["label"],
                "before_score": round(float(before["overall"]["score"]), 2),
                "after_score": round(float(after["overall"]["score"]), 2),
                "delta": delta,
                "before_rec": before["sales_view"]["recommendation"],
                "after_rec": after["sales_view"]["recommendation"],
            })

    # promote: active_framework.json 갱신
    ACTIVE_FRAMEWORK_PATH.parent.mkdir(parents=True, exist_ok=True)
    with ACTIVE_FRAMEWORK_PATH.open("w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)

    registry["active_version"] = version
    save_registry(registry)

    return {
        "promoted": True,
        "version": version,
        "active_framework_path": str(ACTIVE_FRAMEWORK_PATH),
        "shadow_evaluation": shadow,
    }


def print_status(registry: dict[str, Any]) -> None:
    progress = learning_progress(registry)
    print("BizAiPro Learning Status")
    print(f"  Current version     : {registry.get('current_version', BASELINE_VERSION)}")
    print(f"  Total candidates    : {progress.total_candidates}")
    print(f"  Qualified cases     : {progress.qualified_cases}")
    print(f"  Weighted total      : {progress.weighted_total:.2f}")
    print(f"  Ready for update    : {progress.ready_for_update}")
    print(f"  Remaining cases     : {progress.remaining_cases}")
    print(f"  Remaining weight gap: {progress.remaining_weight_gap:.2f}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="BizAiPro learning loop manager.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    record = subparsers.add_parser("record", help="Record a new learning candidate from an input JSON.")
    record.add_argument("--input", type=Path, required=True, help="Path to flowpay_underwriting input JSON.")
    record.add_argument("--label", type=str, help="Optional label for the learning case.")

    subparsers.add_parser("status", help="Show current learning progress.")
    subparsers.add_parser("update", help="Run BizAiPro update if learning threshold is met.")

    promote = subparsers.add_parser("promote", help="Promote a framework snapshot to active_framework.json.")
    promote.add_argument("--version", type=str, default=None, help="Version to promote (default: latest).")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.command == "record":
        result = record_learning_case(args.input, label=args.label)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    registry = load_registry()
    if args.command == "status":
        print_status(registry)
        return

    if args.command == "update":
        result = run_update()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if args.command == "promote":
        result = run_promote(version=getattr(args, "version", None))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return


if __name__ == "__main__":
    main()
