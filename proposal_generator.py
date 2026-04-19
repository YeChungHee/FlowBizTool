from __future__ import annotations

from typing import Any


def _currency(value: int | float | None) -> str:
    if value is None:
        return "-"
    return f"{int(round(value)):,}원"


def _percent(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:.2f}%"


def _list_or_default(items: list[str] | None, default: list[str]) -> list[str]:
    if items:
        cleaned = [str(item).strip() for item in items if str(item).strip()]
        if cleaned:
            return cleaned
    return default


def _proposal_context(input_data: dict[str, Any]) -> dict[str, Any]:
    return input_data.get("proposal_context", {})


def generate_bizaipro_proposal(input_data: dict[str, Any], result: dict[str, Any]) -> str:
    context = _proposal_context(input_data)
    applicant_name = result["applicant"]["name"]
    supplier_name = str(context.get("purchase_supplier_name") or context.get("supplier_name") or "동대문 OEM 제조 공급처")
    sales_destination_name = str(context.get("sales_destination_name") or context.get("customer_name") or result["buyer"]["name"])
    tenor_months = result["requested_tenor_months"]
    sales_view = result["sales_view"]
    financials = input_data.get("financials", {})
    annual_sales = financials.get("annual_sales")

    proposal_title = str(context.get("title") or f"{applicant_name} 대상 FlowPay BizAiPro 제안서")
    business_summary = str(
        context.get("business_summary")
        or f"{applicant_name}는 현재 거래 확대 여력은 있으나 선집행 자금과 회수 구조 정리가 필요한 상태로 해석됩니다."
    )
    sales_goal = str(
        context.get("sales_goal")
        or "거래 가능성을 빠르게 설명하고, 고객이 이해하기 쉬운 조건으로 초기 제안을 제시하는 것입니다."
    )
    use_of_funds = str(
        context.get("use_of_funds")
        or "매입처 대금 선집행과 납품 전 운전자금 공백 해소"
    )

    pain_points = _list_or_default(
        context.get("pain_points"),
        [
            "선결제가 필요한 구간에서 자금 여유가 부족할 수 있음",
            "결제기간 동안 현금흐름 압박이 생길 수 있음",
            "거래증빙과 회수자료를 함께 정리해야 제안 설득력이 높아짐",
        ],
    )
    strengths = _list_or_default(
        context.get("strengths"),
        [
            "거래 구조가 비교적 명확하고 설명이 쉬움",
            "외부 데이터와 내부 자료를 함께 반영해 영업 참고 근거가 존재함",
            "예상 한도와 마진율을 함께 제시할 수 있어 조건 협의가 빠름",
        ],
    )

    required_documents = _list_or_default(
        context.get("required_documents"),
        [
            "최근 거래 관련 발주서 또는 계약서",
            "세금계산서 또는 납품 확인 자료",
            "최근 3~6개월 입출금 또는 정산 흐름 자료",
            "국세, 지방세, 4대보험 관련 기본 증빙",
        ],
    )

    next_steps = _list_or_default(
        context.get("next_steps"),
        [
            "기본 거래 자료를 받아 예상 조건을 다시 정리합니다.",
            "한도와 마진율을 고객 상황에 맞게 조정합니다.",
            "최종 제안 메일과 설명 자료를 함께 전달합니다.",
        ],
    )

    lines = [
        f"# {proposal_title}",
        "",
        "## 1. 제안 개요",
        business_summary,
        "",
        f"이번 제안의 목적은 {sales_goal}",
        "",
        "## 2. 현재 상황 요약",
        f"- 신청업체: {applicant_name}",
        f"- 매입처: {supplier_name}",
        f"- 매출처: {sales_destination_name}",
        f"- 연간 매출 참고값: {_currency(annual_sales)}",
        f"- 제안 기준 결제기간: {tenor_months}개월",
        f"- 자금 사용 목적: {use_of_funds}",
        "",
        "## 3. FlowPay 제안 구조",
        f"1. 신청업체인 {applicant_name}가 매입처인 {supplier_name}와 거래를 진행합니다.",
        f"2. 276홀딩스가 {supplier_name}에 대금을 먼저 집행합니다.",
        f"3. 신청업체는 생산 또는 납품을 완료한 뒤 매출처인 {sales_destination_name}에서 대금을 회수합니다.",
        "4. 회수 시점에 맞춰 276홀딩스에 원금과 마진을 정산하는 구조로 운영합니다.",
        "",
        "## 4. 영업 참고 결과",
        f"- 거래 가능성: {sales_view['recommendation']}",
        f"- 예상 한도액: {_currency(sales_view['estimated_limit_krw'])}",
        f"- 예상 마진율: {_percent(sales_view['estimated_margin_rate_pct'])}",
        f"- 예상 마진액: {_currency(sales_view['estimated_margin_amount_krw'])}",
        f"- 보수적 설명 기준 마진율: {_percent(sales_view['estimated_compliant_margin_rate_pct'])}",
        "",
        "## 5. 왜 지금 제안할 수 있나요",
    ]

    for item in strengths:
        lines.append(f"- {item}")

    lines.extend(["", "## 6. 고객이 느끼는 과제"])
    for item in pain_points:
        lines.append(f"- {item}")

    lines.extend(["", "## 7. 제안 조건 초안"])
    lines.extend(
        [
            f"- 예상 1회 거래 한도: {_currency(sales_view['estimated_limit_krw'])}",
            f"- 제안 기준 결제기간: {tenor_months}개월",
            f"- 예상 마진율: {_percent(sales_view['estimated_margin_rate_pct'])}",
            f"- 예상 마진액: {_currency(sales_view['estimated_margin_amount_krw'])}",
            f"- 다음 행동 제안: {sales_view['next_action']}",
        ]
    )

    lines.extend(["", "## 8. 제안 전 확인이 필요한 자료"])
    for item in required_documents:
        lines.append(f"- {item}")
    for note in sales_view["risk_notes"]:
        lines.append(f"- 추가 확인 포인트: {note}")

    if result.get("api_enrichment", {}).get("summary_changes"):
        lines.extend(["", "## 9. 외부 데이터 참고"])
        for item in result["api_enrichment"]["summary_changes"]:
            lines.append(f"- {item}")

    lines.extend(["", "## 10. 다음 진행 제안"])
    for item in next_steps:
        lines.append(f"- {item}")

    lines.extend(
        [
            "",
            "## 11. 마무리",
            f"{applicant_name} 건은 현재 자료 기준으로 `{sales_view['recommendation']}` 수준으로 해석됩니다.",
            "따라서 이번 제안서는 최종 승인 확정문서가 아니라, 고객과의 대화를 빠르게 시작하고 조건을 구체화하기 위한 영업용 초안으로 활용하는 것이 적절합니다.",
        ]
    )

    return "\n".join(lines)
