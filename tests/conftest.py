"""conftest.py — FlowBiz_ultra pytest 공통 픽스처."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

BASE_DIR = Path(__file__).resolve().parent.parent


@pytest.fixture
def framework():
    """실제 평가 프레임워크 JSON 로드."""
    path = BASE_DIR / "data" / "integrated_credit_rating_framework.json"
    with path.open(encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def minimal_input():
    """평가 엔진 최소 입력 (모든 필수 키 포함)."""
    return {
        "analysis_type": "flowpay_underwriting",
        "engine_version": "v.test",
        "company_name": "테스트업체",
        "industry_profile": "manufacturing",
        "requested_tenor_months": 2,
        "requested_purchase_amount_krw": 50_000_000,
        "financials": {
            "annual_sales": 3_000_000_000,
            "operating_profit": 150_000_000,
            "net_profit": 100_000_000,
            "operating_margin_pct": 5.0,
            "ebitda_interest_coverage": 3.0,
            "cash_conversion_cycle_days": 60,
        },
        "screening": {
            "business_years": 5,
            "startup_fast_track_supported": False,
            "complete_capital_impairment": False,
            "tax_arrears": False,
            "credit_grade": "B",
            "recent_legal_action_within_years": 99.0,
            "industry_tag": "general_manufacturing",
        },
        "ews_inputs": {
            "representative_credit_drop_notches": 0,
            "yoy_sales_drop_pct": 3.0,
            "short_term_debt_growth_pct": 5.0,
        },
        "proposal_context": {
            "representative_name": "홍길동",
            "business_number": "123-45-67890",
            "supplier_name": "공급업체A",
            "purchase_supplier_name": "공급업체A",
            "sales_destination_name": "삼성전자",
            "consulting_report_url": "https://notion.so/test",
            "meeting_report_url": "",
            "internal_review_url": "https://notion.so/internal",
        },
        "api_enrichment": {"enabled": False, "applicant": {}, "buyer": {}},
        "applicant": {
            "company_name": "테스트업체",
            "scores": {
                "financial": {
                    "annual_sales_scale": 70.0,
                    "revenue_stability": 72.0,
                    "operating_profitability": 75.0,
                    "net_profitability": 72.0,
                    "liquidity_cashflow": 68.0,
                    "leverage": 60.0,
                },
                "business": {
                    "onsite_business_alignment": 74.0,
                    "registry_business_alignment": 70.0,
                    "industry_condition": 62.0,
                    "business_model_resilience": 64.0,
                    "external_funding_validation": 55.0,
                    "customer_diversification": 68.0,
                },
                "management": {
                    "representative_execution": 72.0,
                    "actual_manager_match": 85.0,
                    "shareholder_structure": 62.0,
                    "representative_history": 65.0,
                    "employee_history": 60.0,
                    "governance_control": 60.0,
                },
                "compliance": {
                    "national_tax_compliance": 78.0,
                    "local_tax_compliance": 78.0,
                    "four_insurance_compliance": 78.0,
                    "trade_delinquency": 72.0,
                    "loan_delinquency": 72.0,
                    "legal_dispute_status": 74.0,
                },
                "external": {
                    "corporate_credit_grade_signal": 65.0,
                    "dart_signal": 65.0,
                    "ecos_signal": 58.0,
                    "cretop_signal": 65.0,
                    "public_reputation": 62.0,
                    "employee_reputation": 58.0,
                },
            },
        },
        "buyer": {
            "company_name": "삼성전자",
            "scores": {
                "financial": {
                    "buyer_revenue_scale": 90.0,
                    "buyer_profitability": 86.0,
                    "buyer_liquidity": 90.0,
                    "buyer_leverage": 82.0,
                    "buyer_cashflow": 90.0,
                },
                "business": {
                    "buyer_industry_condition": 85.0,
                    "buyer_business_stability": 90.0,
                    "buyer_market_position": 90.0,
                    "buyer_reputation": 90.0,
                    "buyer_registry_alignment": 85.0,
                },
                "payment": {
                    "payment_history": 88.0,
                    "settlement_stability": 86.0,
                    "invoice_acceptance_clarity": 85.0,
                    "dispute_setoff_risk": 78.0,
                    "concentration_risk": 70.0,
                    "delay_pattern": 82.0,
                },
                "external": {
                    "buyer_credit_grade_signal": 90.0,
                    "buyer_dart_signal": 88.0,
                    "buyer_ecos_signal": 80.0,
                    "buyer_cretop_signal": 88.0,
                    "buyer_funding_signal": 85.0,
                },
            },
        },
        "transaction": {
            "scores": {
                "structure": {
                    "order_authenticity": 75.0,
                    "contract_enforceability": 72.0,
                    "delivery_verification": 72.0,
                    "invoice_proof": 72.0,
                    "recourse_strength": 68.0,
                    "fraud_control_strength": 72.0,
                },
                "tenor": {
                    "cash_conversion_cycle_fit": 78.0,
                    "requested_tenor_fit": 80.0,
                    "seller_survival_buffer": 62.0,
                    "buyer_survival_buffer": 68.0,
                    "emergency_liquidity_backstop": 50.0,
                },
                "macro": {
                    "industry_outlook": 58.0,
                    "macro_sensitivity": 52.0,
                    "commodity_volatility": 55.0,
                    "fx_or_policy_risk": 50.0,
                },
            },
        },
        "learning_context": {
            "flow_score_report_submitted": True,
            "consultation_report_submitted": True,
            "internal_review_link": "https://notion.so/internal",
            "additional_sources": [],
        },
    }
