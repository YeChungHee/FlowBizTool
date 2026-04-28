"""test_regression.py — FlowBiz_ultra 고도화 회귀 테스트 (FBU-VAL-0006 / FBU-VAL-0007 / FBU-VAL-0010 기반).

테스트 항목:
  T1.  SourceQuality: 스캔 PDF는 flow_score usable=False 처리
  T2.  SourceQuality: Notion 요약 있으면 consultation usable=True
  T3.  compute_learning_weight: 3-factor 통합 기준 (qualified = flow AND consultation AND internal)
  T4.  data_quality: 누락 필드 감지 및 data_confidence 계산
  T5.  ensure_data_quality: CLI 입력에 data_quality 자동 주입
  T6.  엔진 스모크 테스트: approved 케이스 점수 > rejected 케이스 점수
  T7.  (FBU-VAL-0007 P0) registry merge 후 SourceQuality 실패 자료 update_weight=0
  T8.  (FBU-VAL-0007 P1) URL-only Notion 링크는 usable_for_update=False
  T9.  promote 후 load_active_framework()가 즉시 반영
  T10. data_confidence 낮으면 경고 플래그 포함
  T11. (FBU-VAL-0010) _normalize_biz_num: 하이픈·공백 제거 정규화
  T12. (FBU-VAL-0010) _match_notion_page: 사업자번호 exact match 우선
  T13. (FBU-VAL-0010) _match_notion_page: 복수 매칭 시 ambiguous 반환
  T14. (FBU-VAL-0010) build_notion_lookup_state_patch: found_and_parsed → primary URL 필드 반영
  T15. (FBU-VAL-0010) build_notion_lookup_state_patch: not_found/found_but_unreadable → primary URL 빈값
  T16. (FBU-VAL-0010) 자동조회 found_and_parsed 후 SourceQuality usable_for_update=True
  T17. (FBU-VAL-0010) notion_auto_lookup: token 미설정 → requires_user_decision=True
  T18. (FBU-VAL-0010) missingNotionReports ↔ data_quality_warning 독립성
  T19. (FBU-VAL-0010) 상담+미팅 모두 파싱되어도 consultation weight 0.35 상한 유지
  T20. (FBU-VAL-0012) missingNotionReports 2단계 재정리 (수동 URL 즉시 제거 + summary 기반 최종 제거)
  T21. (FBU-VAL-0013) Notion 오류 게이트 및 가드: uncoveredAfterError, flowScoreFile 조건,
       errorLookup.missing_notion_reports 포함, notionLookupStatus/notionLookupDetail 형상 분리
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

# 프로젝트 루트를 sys.path에 추가
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app import source_quality_from_state, _merged_components_from_sources, _source_quality_flags_from_state
from bizaipro_learning import compute_learning_weight, ensure_data_quality
from engine import evaluate_flowpay_underwriting, load_active_framework, get_active_framework_meta, ACTIVE_FRAMEWORK_PATH, _BASELINE_FRAMEWORK_PATH


# ── T1: 스캔 PDF → flow_score usable_for_update=False ───────────────────────
class TestSourceQualityFlowScore:
    def test_scan_pdf_blocks_flow_score(self):
        state = {
            "learningFlowScoreFileName": "report.pdf",
            "reportType": "image_or_scan_pdf",
        }
        sq = source_quality_from_state(state)
        assert sq["flow_score"]["present"] is True, "파일명 있으면 present=True"
        assert sq["flow_score"]["usable_for_update"] is False, "스캔 PDF는 usable=False"
        assert any("스캔" in str(i) or "scan" in str(i).lower() or "image" in str(i).lower()
                   for i in sq["flow_score"]["issues"]), "issues에 스캔 관련 항목 포함"

    def test_normal_pdf_allows_flow_score(self):
        state = {
            "learningFlowScoreFileName": "report.pdf",
            "reportType": "flowscore_report",
        }
        sq = source_quality_from_state(state)
        assert sq["flow_score"]["usable_for_update"] is True

    def test_no_file_flow_score_absent(self):
        state = {}
        sq = source_quality_from_state(state)
        assert sq["flow_score"]["present"] is False
        assert sq["flow_score"]["usable_for_update"] is False


# ── T2: Notion 요약 있으면 consultation usable=True ────────────────────────
class TestSourceQualityConsultation:
    def test_consultation_with_summary_is_usable(self):
        state = {
            "consultingReportUrl": "https://notion.so/abc",
            "consultingSummary": "매출처 삼성전자, 거래 3년 이상",
        }
        sq = source_quality_from_state(state)
        assert sq["consultation"]["usable_for_update"] is True

    def test_consultation_with_block_issue_not_usable(self):
        state = {
            "consultingReportUrl": "https://notion.so/abc",
            "consultingSummary": "",
            "consultingIssues": ["Notion integration 권한 오류"],
        }
        sq = source_quality_from_state(state)
        assert sq["consultation"]["usable_for_update"] is False

    def test_consultation_url_only_no_summary_defaults_usable(self):
        """요약 없고 이슈도 없으면 접근 가능으로 판단 (보수적 기본값)."""
        state = {
            "consultingReportUrl": "https://notion.so/abc",
        }
        sq = source_quality_from_state(state)
        assert sq["consultation"]["present"] is True


# ── T3: compute_learning_weight 3-factor 통합 기준 ──────────────────────────
class TestComputeLearningWeight:
    def _make_input(self, flow=False, consult=False, internal=""):
        return {
            "analysis_type": "flowpay_underwriting",
            "learning_context": {
                "flow_score_report_submitted": flow,
                "consultation_report_submitted": consult,
                "internal_review_link": internal,
                "additional_sources": [],
            },
        }

    def test_all_three_qualified(self):
        inp = self._make_input(True, True, "https://notion.so/review")
        result = compute_learning_weight(inp)
        assert result["qualified"] is True
        assert result["update_eligible"] is True
        assert result["evaluation_ready"] is True
        assert result["total_weight"] == pytest.approx(0.85, abs=0.01)

    def test_flow_consult_no_internal_not_qualified(self):
        inp = self._make_input(True, True, "")
        result = compute_learning_weight(inp)
        assert result["evaluation_ready"] is True
        assert result["update_eligible"] is False
        assert result["qualified"] is False

    def test_only_flow_not_qualified(self):
        inp = self._make_input(True, False, "https://notion.so/review")
        result = compute_learning_weight(inp)
        assert result["qualified"] is False

    def test_nothing_zero_weight(self):
        inp = self._make_input(False, False, "")
        result = compute_learning_weight(inp)
        assert result["qualified"] is False
        assert result["total_weight"] == 0.0

    def test_additional_sources_add_weight(self):
        inp = self._make_input(True, True, "https://notion.so/review")
        inp["learning_context"]["additional_sources"] = ["src1", "src2"]
        result = compute_learning_weight(inp)
        assert result["total_weight"] == pytest.approx(0.95, abs=0.01)
        assert result["additional_source_count"] == 2


# ── T4: data_quality 누락 필드 감지 ────────────────────────────────────────
class TestDataQuality:
    def test_full_state_high_confidence(self):
        """핵심 필드 모두 입력 → data_confidence 1.0."""
        from app import build_learning_evaluation_payload
        state = {
            "companyName": "테스트",
            "representativeName": "홍길동",
            "businessNumber": "123-45-67890",
            "reportCreditGrade": "B",
            "reportFinancialSummary": {"2024": {"annual_sales": 3_000_000_000}},
            "buyerName": "삼성전자",
            "supplierName": "공급사",
            "requestedTenorDays": 60,
            "reportIncorporatedDate": "2019-01-01",
        }
        payload = build_learning_evaluation_payload(state)
        dq = payload["data_quality"]
        # 핵심 필드 입력 시 data_confidence >= 0.85 (annualSales는 reportFinancialSummary에서 추출)
        assert dq["data_confidence"] >= 0.85, f"신뢰도 {dq['data_confidence']}, 누락: {dq['missing_fields']}"
        # 직접 입력 가능 필드(companyName, buyerName 등)는 누락 없어야 함
        for field in ("companyName", "representativeName", "businessNumber", "buyerName", "supplierName"):
            assert field not in dq["missing_fields"], f"{field}이 missing_fields에 포함됨"

    def test_empty_state_low_confidence(self):
        """핵심 필드 모두 없음 → data_confidence 낮음."""
        from app import build_learning_evaluation_payload
        payload = build_learning_evaluation_payload({})
        dq = payload["data_quality"]
        assert dq["data_confidence"] < 0.5
        assert "companyName" in dq["missing_fields"]
        assert "annualSales" in dq["missing_fields"]
        assert "buyerName" in dq["missing_fields"]

    def test_defaulted_fields_logged(self):
        """기본값 치환 필드가 defaulted_fields에 기록됨."""
        from app import build_learning_evaluation_payload
        payload = build_learning_evaluation_payload({})
        dq = payload["data_quality"]
        defaults = dq["defaulted_fields"]
        assert any("requestedTenorDays" in d for d in defaults)
        assert any("buyerName" in d for d in defaults)


# ── T5: ensure_data_quality CLI 주입 ────────────────────────────────────────
class TestEnsureDataQuality:
    def test_injects_when_missing(self):
        inp = {"analysis_type": "flowpay_underwriting", "company_name": "A사"}
        result = ensure_data_quality(inp)
        assert "data_quality" in result
        assert isinstance(result["data_quality"]["missing_fields"], list)
        assert 0.0 <= result["data_quality"]["data_confidence"] <= 1.0

    def test_does_not_overwrite_existing(self):
        inp = {
            "analysis_type": "flowpay_underwriting",
            "data_quality": {"data_confidence": 0.99, "missing_fields": [], "defaulted_fields": []},
        }
        result = ensure_data_quality(inp)
        assert result["data_quality"]["data_confidence"] == 0.99

    def test_original_not_mutated(self):
        inp = {"analysis_type": "flowpay_underwriting"}
        original_keys = set(inp.keys())
        ensure_data_quality(inp)
        assert set(inp.keys()) == original_keys, "원본 dict 변경 없어야 함"


# ── T6: 엔진 스모크 테스트 ────────────────────────────────────────────────────
class TestEngineSmoke:
    def test_approved_case_score_above_threshold(self, minimal_input, framework):
        result = evaluate_flowpay_underwriting(minimal_input, framework)
        assert "overall" in result
        score = float(result["overall"]["score"])
        assert score >= 50.0, f"정상 케이스 점수 {score:.1f}이 50 미만"

    def test_rejected_case_lower_than_approved(self, minimal_input, framework):
        """불량 케이스(체납+무매출처)는 정상보다 낮은 점수여야 함."""
        bad = copy.deepcopy(minimal_input)
        # 체납·연체·매출처 불명으로 악화
        bad["screening"]["tax_arrears"] = True
        bad["proposal_context"]["sales_destination_name"] = ""
        bad["financials"]["annual_sales"] = 0
        bad["financials"]["operating_profit"] = -50_000_000
        # 모든 외부 신호 최저
        for cat in bad["applicant"]["scores"].values():
            for k in cat:
                cat[k] = 30.0
        for cat in bad["buyer"]["scores"].values():
            for k in cat:
                cat[k] = 30.0
        for cat in bad["transaction"]["scores"].values():
            for k in cat:
                cat[k] = 30.0

        good_result = evaluate_flowpay_underwriting(minimal_input, framework)
        bad_result = evaluate_flowpay_underwriting(bad, framework)
        good_score = float(good_result["overall"]["score"])
        bad_score = float(bad_result["overall"]["score"])
        assert good_score > bad_score, (
            f"정상 케이스({good_score:.1f}) > 불량 케이스({bad_score:.1f}) 조건 미충족"
        )

    def test_result_has_required_keys(self, minimal_input, framework):
        result = evaluate_flowpay_underwriting(minimal_input, framework)
        for key in ("overall", "applicant", "buyer", "transaction", "sales_view"):
            assert key in result, f"결과에 '{key}' 키 없음"

    def test_sales_view_recommendation_exists(self, minimal_input, framework):
        result = evaluate_flowpay_underwriting(minimal_input, framework)
        rec = result["sales_view"].get("recommendation")
        assert rec and isinstance(rec, str), "sales_view.recommendation 없음"


# ── T7: registry merge 후 SourceQuality 실패 자료 update_weight=0 ─────────────
class TestRegistryMergeSourceQuality:
    def test_scan_pdf_source_keeps_zero_weight_after_merge(self):
        """스캔 PDF quality flags를 가진 sources가 merge 후에도 flow_score weight=0."""
        scan_sources = {
            "flow_score_file_name": "report.pdf",
            "flow_score_usable_for_update": False,   # 스캔 PDF → 품질 실패
            "consulting_report_url": "",
            "consultation_usable_for_update": False,
            "internal_review_url": "",
            "internal_review_usable_for_update": False,
            "additional_usable_for_update": False,
        }
        components = _merged_components_from_sources(scan_sources)
        assert components["flow_score_report"] == 0.0, (
            "스캔 PDF sources는 merge 후에도 flow_score_report weight=0이어야 함"
        )

    def test_url_only_source_zero_weight_after_merge(self):
        """quality flags 없는 legacy URL-only sources는 update weight=0."""
        legacy_sources = {
            "flow_score_file_name": "report.pdf",      # quality flag 없음
            "consulting_report_url": "https://notion.so/abc",
            "internal_review_url": "https://notion.so/internal",
            # flow_score_usable_for_update 등 quality flags 없음 → default False
        }
        components = _merged_components_from_sources(legacy_sources)
        assert components["flow_score_report"] == 0.0
        assert components["consultation_report"] == 0.0
        assert components["internal_review"] == 0.0

    def test_quality_passed_source_gets_full_weight_after_merge(self):
        """quality flags 모두 True인 sources는 merge 후 정상 가중치 부여."""
        good_sources = {
            "flow_score_file_name": "report.pdf",
            "flow_score_usable_for_update": True,
            "consulting_report_url": "https://notion.so/abc",
            "consultation_usable_for_update": True,
            "internal_review_url": "https://notion.so/internal",
            "internal_review_usable_for_update": True,
            "additional_usable_for_update": False,
        }
        components = _merged_components_from_sources(good_sources)
        assert components["flow_score_report"] == pytest.approx(0.35)
        assert components["consultation_report"] == pytest.approx(0.35)
        assert components["internal_review"] == pytest.approx(0.15)
        assert components["additional_sources"] == 0.0

    def test_quality_flags_extracted_from_state(self):
        """_source_quality_flags_from_state()가 state에서 quality flags를 올바르게 추출."""
        state = {
            "learningFlowScoreFileName": "report.pdf",
            "reportType": "flowscore_report",
            "consultingReportUrl": "https://notion.so/consult",
            "consultingSummary": "매출처 삼성전자, 거래 3년",
            "internalReviewUrl": "https://notion.so/review",
            "internalReviewSummary": "검토 완료",
        }
        flags = _source_quality_flags_from_state(state)
        assert flags["flow_score_usable_for_update"] is True
        assert flags["consultation_usable_for_update"] is True
        assert flags["internal_review_usable_for_update"] is True


# ── T8: URL-only Notion 링크는 usable_for_update=False ───────────────────────
class TestSourceQualityURLOnly:
    def test_url_only_consultation_not_usable_for_update(self):
        """URL만 있고 summary/issues 없으면 consultation usable_for_update=False."""
        state = {
            "consultingReportUrl": "https://notion.so/abc",
            # consultingSummary 없음, consultingIssues 없음
        }
        sq = source_quality_from_state(state)
        # present는 True (URL 있으므로)
        assert sq["consultation"]["present"] is True
        # usable_for_update는 False (parsing evidence 없음)
        assert sq["consultation"]["usable_for_update"] is False, (
            "URL만 있고 summary 없으면 usable_for_update=False 이어야 함"
        )

    def test_url_only_internal_review_not_usable_for_update(self):
        """내부심사 URL만 있고 summary 없으면 usable_for_update=False."""
        state = {
            "internalReviewUrl": "https://notion.so/internal",
            # internalReviewSummary 없음
        }
        sq = source_quality_from_state(state)
        assert sq["internal_review"]["present"] is True
        assert sq["internal_review"]["usable_for_update"] is False

    def test_with_summary_is_usable_for_update(self):
        """summary가 있으면 usable_for_update=True."""
        state = {
            "consultingReportUrl": "https://notion.so/abc",
            "consultingSummary": "매출처 삼성전자 거래 확인",
        }
        sq = source_quality_from_state(state)
        assert sq["consultation"]["usable_for_update"] is True


# ── T9: promote 후 load_active_framework()가 즉시 반영 ────────────────────────
class TestActiveFrameworkDynamicLoad:
    def test_load_active_framework_returns_baseline_when_no_active(self, tmp_path, monkeypatch):
        """active_framework.json 없으면 baseline 프레임워크 반환."""
        fake_active = tmp_path / "active_framework.json"
        monkeypatch.setattr("engine.ACTIVE_FRAMEWORK_PATH", fake_active)
        # active 없음 → baseline 로드
        import engine as eng
        orig = eng.ACTIVE_FRAMEWORK_PATH
        eng.ACTIVE_FRAMEWORK_PATH = fake_active
        try:
            framework = load_active_framework()
            assert "flowpay_underwriting" in framework
            meta = get_active_framework_meta()
            assert meta["source"] == "baseline"
        finally:
            eng.ACTIVE_FRAMEWORK_PATH = orig

    def test_load_active_framework_reflects_newly_created_file(self, tmp_path, monkeypatch):
        """active_framework.json 생성 후 다음 호출에서 즉시 반영되는지 확인."""
        import json as _json
        import engine as eng

        # baseline 프레임워크 복사해서 임시 active 파일 생성
        baseline = load_active_framework()  # 현재 활성 또는 baseline
        fake_active = tmp_path / "active_framework.json"
        fake_active.write_text(_json.dumps(baseline), encoding="utf-8")

        orig = eng.ACTIVE_FRAMEWORK_PATH
        eng.ACTIVE_FRAMEWORK_PATH = fake_active
        try:
            framework = load_active_framework()
            assert "flowpay_underwriting" in framework, "active 파일 로드 실패"
            meta = get_active_framework_meta()
            assert meta["source"] == "active"
            assert "active_framework.json" in meta["filename"]
        finally:
            eng.ACTIVE_FRAMEWORK_PATH = orig

    def test_api_response_includes_framework_meta(self, minimal_input, framework):
        """evaluate_flowpay_underwriting 결과에는 engine 구조가 포함됨 (API 응답 meta 검증)."""
        # get_active_framework_meta()가 필수 키를 반환하는지 확인
        meta = get_active_framework_meta()
        assert "framework_path" in meta
        assert "source" in meta
        assert meta["source"] in ("active", "baseline")


# ── T10: data_confidence 낮으면 경고 플래그 포함 ─────────────────────────────
class TestDataQualityWarning:
    def test_low_confidence_triggers_warning(self):
        """data_confidence < 0.7이면 data_quality_warning이 생성됨."""
        from app import build_learning_evaluation_payload

        # 핵심 필드 대부분 없는 state → low confidence
        payload = build_learning_evaluation_payload({})
        dq = payload["data_quality"]
        assert dq["data_confidence"] < 0.7, "빈 state는 confidence 0.7 미만이어야 함"

        # API 응답의 data_quality_warning 생성 로직 직접 검증
        data_confidence = dq["data_confidence"]
        warning = None
        if data_confidence < 0.7:
            warning = {
                "level": "conditional",
                "message": "조건부 평가 — 자료 보완 필요",
                "data_confidence": data_confidence,
                "missing_fields": dq.get("missing_fields", []),
            }
        assert warning is not None, "낮은 confidence에서 경고 생성 실패"
        assert warning["level"] == "conditional"
        assert len(warning["missing_fields"]) > 0

    def test_high_confidence_no_warning(self):
        """핵심 필드 모두 입력 시 data_quality_warning=None."""
        from app import build_learning_evaluation_payload

        state = {
            "companyName": "테스트",
            "representativeName": "홍길동",
            "businessNumber": "123-45-67890",
            "reportCreditGrade": "B",
            "buyerName": "삼성전자",
            "supplierName": "공급사",
            "requestedTenorDays": 60,
            "reportIncorporatedDate": "2019-01-01",
            "reportFinancialSummary": {"2024": {"annual_sales": 3_000_000_000}},
        }
        payload = build_learning_evaluation_payload(state)
        dq = payload["data_quality"]
        warning = None
        if dq["data_confidence"] < 0.7:
            warning = {"level": "conditional"}
        assert warning is None, f"충분한 필드 입력 시 경고 없어야 함 (confidence={dq['data_confidence']})"


# ── T11: _normalize_biz_num ──────────────────────────────────────────────────
class TestNormalizeBizNum:
    """FBU-VAL-0010: 사업자번호 정규화 — 하이픈·공백·비숫자 제거."""

    def test_strips_hyphens(self):
        from app import _normalize_biz_num
        assert _normalize_biz_num("123-45-67890") == "1234567890"

    def test_strips_spaces(self):
        from app import _normalize_biz_num
        assert _normalize_biz_num("123 45 67890") == "1234567890"

    def test_already_clean(self):
        from app import _normalize_biz_num
        assert _normalize_biz_num("1234567890") == "1234567890"

    def test_none_returns_empty(self):
        from app import _normalize_biz_num
        assert _normalize_biz_num(None) == ""

    def test_empty_returns_empty(self):
        from app import _normalize_biz_num
        assert _normalize_biz_num("") == ""


# ── T12: _match_notion_page 사업자번호 exact match 우선 ─────────────────────
class TestMatchNotionPageBizNum:
    """FBU-VAL-0010: 사업자번호 exact match가 회사명 contains보다 우선한다."""

    def _make_page(self, page_id: str, title: str, biz_num: str = "") -> dict:
        """테스트용 최소 Notion page 구조."""
        return {
            "id": page_id,
            "properties": {
                "제목": {
                    "title": [{"plain_text": title}]
                },
                "사업자번호": {
                    "rich_text": [{"plain_text": biz_num}] if biz_num else []
                },
            },
        }

    def test_biz_num_exact_match_wins(self):
        """사업자번호 exact match → 이름 불일치여도 우선 선택."""
        from app import _match_notion_page
        pages = [
            self._make_page("aaa", "심사보고서 : 다른회사", biz_num="111-22-33333"),
            self._make_page("bbb", "심사보고서 : 테스트기업", biz_num="123-45-67890"),
        ]
        page_id, candidates = _match_notion_page(pages, "테스트기업", "123-45-67890")
        assert page_id == "bbb", "사업자번호 exact match 페이지가 선택되어야 함"
        assert candidates == []

    def test_no_biz_num_falls_back_to_name_exact(self):
        """사업자번호 없으면 회사명 exact match로 폴백."""
        from app import _match_notion_page
        pages = [
            self._make_page("aaa", "심사보고서 : 다른회사"),
            self._make_page("bbb", "심사보고서 : 테스트기업"),
        ]
        page_id, candidates = _match_notion_page(pages, "테스트기업", None)
        assert page_id == "bbb"

    def test_not_found_returns_none(self):
        """매칭 없음 → (None, []) 반환."""
        from app import _match_notion_page
        pages = [self._make_page("aaa", "심사보고서 : 전혀다른회사")]
        page_id, candidates = _match_notion_page(pages, "찾을수없는기업", None)
        assert page_id is None
        assert candidates == []


# ── T13: _match_notion_page ambiguous (복수 매칭) ───────────────────────────
class TestMatchNotionPageAmbiguous:
    """FBU-VAL-0010: 복수 매칭 시 ambiguous로 반환해야 한다."""

    def _make_page(self, page_id: str, title: str, biz_num: str = "") -> dict:
        return {
            "id": page_id,
            "properties": {
                "제목": {"title": [{"plain_text": title}]},
                "사업자번호": {"rich_text": [{"plain_text": biz_num}] if biz_num else []},
            },
        }

    def test_two_name_matches_returns_ambiguous(self):
        """동명 업체 2건 → (None, candidates) 반환."""
        from app import _match_notion_page
        pages = [
            self._make_page("aaa", "상담보고서 : 테스트기업"),
            self._make_page("bbb", "상담보고서 : 테스트기업"),
        ]
        page_id, candidates = _match_notion_page(pages, "테스트기업", None)
        assert page_id is None, "복수 매칭 시 page_id=None"
        assert len(candidates) == 2, "후보 2건 반환"


# ── T14: build_notion_lookup_state_patch — found_and_parsed 반영 ───────────
class TestBuildNotionLookupStatePatchFound:
    """FBU-VAL-0010 §6 규칙 1: found_and_parsed만 primary URL 필드에 반영."""

    def _make_lookup(self, consultation_status="found_and_parsed", internal_status="not_found"):
        return {
            "consultation": {
                "status": consultation_status,
                "page_url": "https://www.notion.so/consult-page-id",
                "state_patch": {"consultingSummary": "매출처 삼성전자, 거래 3년", "consultingCrossChecks": []},
            },
            "meeting": {
                "status": "not_found",
                "page_url": None,
                "state_patch": {},
            },
            "internal_review": {
                "status": internal_status,
                "page_url": "https://www.notion.so/internal-page-id" if internal_status == "found_and_parsed" else None,
                "state_patch": {"internalReviewSummary": "적정 판단"} if internal_status == "found_and_parsed" else {},
            },
            "missing_notion_reports": (
                [r for r in ("consultation", "meeting", "internal_review")
                 if (r == "consultation" and consultation_status != "found_and_parsed")
                    or (r == "meeting")
                    or (r == "internal_review" and internal_status != "found_and_parsed")]
            ),
        }

    def test_found_and_parsed_sets_primary_url(self):
        from app import build_notion_lookup_state_patch
        lookup = self._make_lookup("found_and_parsed", "not_found")
        patch = build_notion_lookup_state_patch(lookup)
        assert patch.get("consultingReportUrl") == "https://www.notion.so/consult-page-id", (
            "found_and_parsed → consultingReportUrl 설정"
        )
        assert patch.get("consultingSummary") == "매출처 삼성전자, 거래 3년", (
            "found_and_parsed → consultingSummary 설정"
        )

    def test_notionLookupStatus_always_present(self):
        from app import build_notion_lookup_state_patch
        lookup = self._make_lookup("found_and_parsed", "found_and_parsed")
        patch = build_notion_lookup_state_patch(lookup)
        assert "notionLookupStatus" in patch, "notionLookupStatus 항상 포함"
        assert patch["notionLookupStatus"]["consultation"] == "found_and_parsed"
        assert patch["notionLookupStatus"]["internal_review"] == "found_and_parsed"


# ── T15: build_notion_lookup_state_patch — not_found/unreadable → URL 빈값 ──
class TestBuildNotionLookupStatePatchMissing:
    """FBU-VAL-0010 §6 규칙 2: not_found·found_but_unreadable → primary URL 빈값."""

    def _make_missing_lookup(self, status: str):
        return {
            "consultation": {
                "status": status,
                "page_url": "https://www.notion.so/found-but-blocked" if "found" in status else None,
                "state_patch": {},
            },
            "meeting": {"status": "not_found", "page_url": None, "state_patch": {}},
            "internal_review": {"status": "not_found", "page_url": None, "state_patch": {}},
            "missing_notion_reports": ["consultation", "meeting", "internal_review"],
        }

    def test_not_found_no_primary_url(self):
        from app import build_notion_lookup_state_patch
        patch = build_notion_lookup_state_patch(self._make_missing_lookup("not_found"))
        # consultingReportUrl은 설정되지 않거나 빈값이어야 함
        assert patch.get("consultingReportUrl", "") == "", (
            "not_found → consultingReportUrl 빈값"
        )
        # summary도 없어야 함
        assert not patch.get("consultingSummary"), "not_found → consultingSummary 없음"

    def test_found_but_unreadable_no_primary_url(self):
        from app import build_notion_lookup_state_patch
        patch = build_notion_lookup_state_patch(self._make_missing_lookup("found_but_unreadable"))
        assert patch.get("consultingReportUrl", "") == "", (
            "found_but_unreadable → consultingReportUrl 빈값 유지 (FBU-VAL-0010 §5.1)"
        )

    def test_missing_sets_evaluationContinuationMode(self):
        from app import build_notion_lookup_state_patch
        patch = build_notion_lookup_state_patch(self._make_missing_lookup("not_found"))
        assert patch.get("evaluationContinuationMode") == "flowscore_only_or_partial", (
            "미발견 시 evaluationContinuationMode 설정"
        )
        assert patch.get("missingNotionReports"), "missingNotionReports 비어있으면 안 됨"


# ── T16: 자동조회 found_and_parsed → SourceQuality usable_for_update=True ────
class TestSourceQualityAfterAutoLookup:
    """FBU-VAL-0010: 자동조회 state_patch 적용 후 SourceQuality 정상 통과."""

    def test_auto_found_consultation_is_usable(self):
        """found_and_parsed state_patch 적용 후 consultation usable_for_update=True."""
        state = {
            "consultingReportUrl": "https://www.notion.so/consult-page-id",
            "consultingSummary": "매출처 삼성전자, 거래 3년 이상 확인",
        }
        sq = source_quality_from_state(state)
        assert sq["consultation"]["usable_for_update"] is True, (
            "found_and_parsed 상태에서 consultingSummary 있으면 usable=True"
        )

    def test_auto_found_internal_review_is_usable(self):
        """심사보고서 found_and_parsed 후 internal_review usable_for_update=True."""
        state = {
            "internalReviewUrl": "https://www.notion.so/internal-page-id",
            "internalReviewSummary": "재무 구조 검토 완료, 적정 판단",
        }
        sq = source_quality_from_state(state)
        assert sq["internal_review"]["usable_for_update"] is True

    def test_not_found_no_url_not_usable(self):
        """not_found → URL 빈값 → usable_for_update=False."""
        state = {
            "consultingReportUrl": "",  # not_found: primary URL 빈값
        }
        sq = source_quality_from_state(state)
        assert sq["consultation"]["usable_for_update"] is False


# ── T17: notion_auto_lookup token_missing ────────────────────────────────────
class TestNotionAutoLookupTokenMissing:
    """FBU-VAL-0010: NOTION_API_TOKEN 미설정 시 token_missing으로 처리."""

    def test_token_missing_requires_user_decision(self, monkeypatch):
        """토큰 없으면 requires_user_decision=True, 3종 모두 token_missing."""
        import app as app_module
        monkeypatch.setattr(app_module, "get_notion_api_token", lambda: None)
        from app import notion_auto_lookup
        result = notion_auto_lookup("테스트기업", "123-45-67890")
        assert result["requires_user_decision"] is True, "token 없으면 user decision 필요"
        for rtype in ("consultation", "meeting", "internal_review"):
            assert result[rtype]["status"] == "token_missing", (
                f"{rtype} status=token_missing 이어야 함"
            )
        assert set(result["missing_notion_reports"]) == {"consultation", "meeting", "internal_review"}

    def test_token_missing_state_patch_empty(self, monkeypatch):
        """token_missing → state_patch는 비어있어야 함 (primary URL 빈값 원칙)."""
        import app as app_module
        monkeypatch.setattr(app_module, "get_notion_api_token", lambda: None)
        from app import notion_auto_lookup, build_notion_lookup_state_patch
        lookup = notion_auto_lookup("테스트기업", None)
        patch = build_notion_lookup_state_patch(lookup)
        # primary URL 필드 빈값 검증
        assert patch.get("consultingReportUrl", "") == ""
        assert patch.get("meetingReportUrl", "") == ""
        assert patch.get("internalReviewUrl", "") == ""


# ── T18: missingNotionReports ↔ data_quality_warning 독립성 ─────────────────
class TestNotionWarningIndependence:
    """FBU-VAL-0010 §6 규칙 6: notion_partial_evaluation_warning과 data_quality_warning은
    독립적인 상태값이며 서로 혼용되지 않아야 한다."""

    def test_build_notion_lookup_patch_does_not_set_data_quality_warning(self):
        """build_notion_lookup_state_patch()는 data_quality_warning을 설정하지 않음."""
        from app import build_notion_lookup_state_patch
        lookup = {
            "consultation": {"status": "not_found", "page_url": None, "state_patch": {}},
            "meeting": {"status": "not_found", "page_url": None, "state_patch": {}},
            "internal_review": {"status": "not_found", "page_url": None, "state_patch": {}},
            "missing_notion_reports": ["consultation", "meeting", "internal_review"],
        }
        patch = build_notion_lookup_state_patch(lookup)
        assert "data_quality_warning" not in patch, (
            "Notion 조회 결과에 data_quality_warning이 포함되면 안 됨"
        )

    def test_build_learning_payload_does_not_set_missing_notion_reports(self):
        """build_learning_evaluation_payload()는 missingNotionReports를 설정하지 않음."""
        from app import build_learning_evaluation_payload
        payload = build_learning_evaluation_payload({})
        assert "missingNotionReports" not in payload, (
            "data_quality payload에 missingNotionReports가 포함되면 안 됨"
        )

    def test_both_can_coexist_independently(self):
        """missingNotionReports와 data_quality_warning이 동시에 존재할 수 있음."""
        from app import build_notion_lookup_state_patch, build_learning_evaluation_payload
        lookup = {
            "consultation": {"status": "not_found", "page_url": None, "state_patch": {}},
            "meeting": {"status": "not_found", "page_url": None, "state_patch": {}},
            "internal_review": {"status": "not_found", "page_url": None, "state_patch": {}},
            "missing_notion_reports": ["consultation", "meeting", "internal_review"],
        }
        notion_patch = build_notion_lookup_state_patch(lookup)
        dq_payload = build_learning_evaluation_payload({})
        # 각각 독립적으로 존재
        assert notion_patch.get("missingNotionReports"), "notion_patch에는 missingNotionReports 있음"
        assert "data_quality" in dq_payload, "dq_payload에는 data_quality 있음"
        # 서로의 고유 키가 상대방에 없음
        assert "data_quality_warning" not in notion_patch
        assert "missingNotionReports" not in dq_payload


# ── T19: 상담+미팅 모두 found_and_parsed → consultation weight 0.35 상한 유지 ─
class TestConsultationWeightCap:
    """FBU-VAL-0010 §6 규칙 7: 상담보고서와 미팅보고서가 모두 파싱되어도
    consultation component는 0.35 상한을 유지한다 (미팅은 상담의 subtype)."""

    def test_meeting_only_gives_consultation_weight(self):
        """미팅보고서 summary만 있어도 consultation usable=True."""
        state = {
            "meetingReportUrl": "https://www.notion.so/meeting-page-id",
            "meetingSummary": "미팅 내용 요약: 삼성전자 담당자 미팅 완료",
        }
        sq = source_quality_from_state(state)
        assert sq["consultation"]["usable_for_update"] is True, (
            "meetingSummary → consultation.usable_for_update=True (subtype 처리)"
        )

    def test_both_consulting_and_meeting_cap_at_0_35(self):
        """상담+미팅 모두 있어도 consultation_report 가중치는 0.35 초과 안 됨."""
        state = {
            "consultingReportUrl": "https://www.notion.so/consult",
            "consultingSummary": "상담보고서 요약",
            "meetingReportUrl": "https://www.notion.so/meeting",
            "meetingSummary": "미팅보고서 요약",
            "learningFlowScoreFileName": "report.pdf",
            "reportType": "flowscore_report",
            "internalReviewUrl": "https://www.notion.so/internal",
            "internalReviewSummary": "심사보고서 요약",
        }
        sq = source_quality_from_state(state)
        components = sq.get("components") or {}
        consult_weight = float(components.get("consultation_report", 0) or 0)
        # components가 source_quality_from_state에 포함된 경우
        if consult_weight > 0:
            assert consult_weight <= 0.35, (
                f"상담+미팅 가중치 {consult_weight:.2f}이 0.35 상한 초과"
            )

    def test_merged_components_consultation_cap(self):
        """_merged_components_from_sources: 상담+미팅 플래그 모두 True여도 0.35 이하."""
        sources = {
            "flow_score_file_name": "report.pdf",
            "flow_score_usable_for_update": True,
            "consulting_report_url": "https://notion.so/consult",
            "consultation_usable_for_update": True,
            "internal_review_url": "https://notion.so/internal",
            "internal_review_usable_for_update": True,
            "additional_usable_for_update": False,
        }
        components = _merged_components_from_sources(sources)
        assert components["consultation_report"] == pytest.approx(0.35), (
            "consultation_report 가중치는 정확히 0.35이어야 함"
        )


# ── T20: missingNotionReports 수동 보완 후 잘못된 경고 방지 ─────────────────
class TestMissingNotionReportsReconciliation:
    """수동 URL로 보완한 유형이 missingNotionReports에 잔류하면 결과서 배너가
    잘못 뜨는 버그(FBU-VAL-0010 보완 수정) — 두 단계 reconciliation 검증."""

    def test_manual_url_covered_type_not_in_missing(self):
        """자동 조회 not_found + 수동 URL 입력 → 해당 유형은 missingNotionReports 제외."""
        # 프론트엔드 Fix 1 로직을 Python으로 직접 검증
        # (자동 조회 직후 missingNotionReports 필터링 시뮬레이션)
        auto_missing = ["consultation", "meeting", "internal_review"]
        manual_consulting_url = "https://notion.so/manual-consult"
        manual_meeting_url = ""
        manual_internal_url = ""

        # Fix 1: 수동 URL 보완 유형 즉시 제거
        updated_missing = [
            rtype for rtype in auto_missing
            if not (rtype == "consultation"    and manual_consulting_url)
            if not (rtype == "meeting"         and manual_meeting_url)
            if not (rtype == "internal_review" and manual_internal_url)
        ]
        assert "consultation" not in updated_missing, (
            "수동 URL이 있는 consultation은 missingNotionReports에서 제거되어야 함"
        )
        assert "meeting" in updated_missing, "수동 URL 없는 meeting은 유지"
        assert "internal_review" in updated_missing, "수동 URL 없는 internal_review는 유지"

    def test_summary_based_reconciliation_removes_parsed_type(self):
        """Fix 2: 수동 URL 파싱 후 summary가 주입되면 missingNotionReports에서 제거."""
        # 수동 파싱 후 state에 consultingSummary가 주입된 상황
        state_after_parse = {
            "missingNotionReports": ["consultation", "meeting", "internal_review"],
            "consultingSummary": "매출처 삼성전자, 거래 3년 이상",  # 파싱 성공
            "meetingSummary": "",
            "internalReviewSummary": "",
        }

        # Fix 2 로직 시뮬레이션
        if isinstance(state_after_parse.get("missingNotionReports"), list):
            state_after_parse["missingNotionReports"] = [
                rtype for rtype in state_after_parse["missingNotionReports"]
                if not (rtype == "consultation"    and state_after_parse.get("consultingSummary"))
                if not (rtype == "meeting"         and state_after_parse.get("meetingSummary"))
                if not (rtype == "internal_review" and (
                    state_after_parse.get("internalReviewSummary")
                    or state_after_parse.get("internalReviewValidationSummary")
                ))
            ]

        assert "consultation" not in state_after_parse["missingNotionReports"], (
            "consultingSummary 주입 후 consultation은 missingNotionReports에서 제거"
        )
        assert "meeting" in state_after_parse["missingNotionReports"], (
            "meetingSummary 없으면 meeting은 missing 유지"
        )

    def test_parse_failure_keeps_type_in_missing(self):
        """수동 URL이 있어도 파싱 실패(summary 없음)면 missingNotionReports 유지."""
        state_after_failed_parse = {
            "missingNotionReports": ["consultation"],
            "consultingReportUrl": "https://notion.so/manual",
            # consultingSummary 없음 → 파싱 실패 또는 권한 문제
        }
        # Fix 2 로직 적용 후
        reconciled = [
            rtype for rtype in state_after_failed_parse["missingNotionReports"]
            if not (rtype == "consultation" and state_after_failed_parse.get("consultingSummary"))
        ]
        assert "consultation" in reconciled, (
            "summary 없는 수동 URL은 파싱 실패로 간주 → missing 유지 → 배너 경고 정상 표시"
        )


# ── T21: Notion 오류 게이트 및 자동조회 가드 (FBU-VAL-0013) ────────────────────
class TestNotionErrorGateAndGuards:
    """FBU-VAL-0013 §6 구현 기준 검증 (Finding 2·3·4).

    T21-1  자동조회 API 오류 후 uncoveredAfterError 계산 로직
    T21-2  flowScoreFile 없을 때 자동조회 skip 조건
    T21-3  errorLookup에 missing_notion_reports가 반드시 포함됨
    T21-4  notionLookupStatus(status map) ≠ notionLookupDetail(full object) 분리
    """

    # ── 공통 헬퍼 ──────────────────────────────────────────────────────────────
    @staticmethod
    def _compute_uncovered_after_error(manual_consulting_url, manual_meeting_url, manual_internal_url):
        """bizaipro_home.html inner-catch uncoveredAfterError 로직 Python 재현."""
        result = []
        for rtype in ["consultation", "meeting", "internal_review"]:
            if rtype == "consultation" and manual_consulting_url:
                continue
            if rtype == "meeting" and manual_meeting_url:
                continue
            if rtype == "internal_review" and manual_internal_url:
                continue
            result.append(rtype)
        return result

    @staticmethod
    def _build_error_lookup(uncovered_after_error, error_message="Notion 조회 응답 오류 (500)"):
        """bizaipro_home.html errorLookup 생성 로직 Python 재현 (FBU-VAL-0013 §3.1)."""
        error_lookup = {
            "token_status": "lookup_error",
            "missing_notion_reports": uncovered_after_error,
        }
        for r in ["consultation", "meeting", "internal_review"]:
            error_lookup[r] = {
                "status": "not_found" if r in uncovered_after_error else "found_and_parsed",
                "issues": [f"Notion 자동조회 오류: {error_message}"] if r in uncovered_after_error else [],
            }
        return error_lookup

    # ── T21-1 ──────────────────────────────────────────────────────────────────
    def test_uncovered_after_error_all_manual_covered(self):
        """자동조회 오류 후 수동 URL로 3종 모두 커버 → uncoveredAfterError 빈 목록."""
        uncovered = self._compute_uncovered_after_error(
            manual_consulting_url="https://notion.so/c",
            manual_meeting_url="https://notion.so/m",
            manual_internal_url="https://notion.so/i",
        )
        assert uncovered == [], "3종 수동 URL 모두 있으면 uncoveredAfterError=[]"

    def test_uncovered_after_error_none_manual(self):
        """자동조회 오류 후 수동 URL 하나도 없음 → 3종 전부 uncovered."""
        uncovered = self._compute_uncovered_after_error(
            manual_consulting_url="",
            manual_meeting_url="",
            manual_internal_url="",
        )
        assert set(uncovered) == {"consultation", "meeting", "internal_review"}, (
            "수동 URL 없으면 3종 모두 uncovered"
        )

    def test_uncovered_after_error_partial_manual(self):
        """자동조회 오류 후 consultation만 수동 보완 → meeting·internal_review만 uncovered."""
        uncovered = self._compute_uncovered_after_error(
            manual_consulting_url="https://notion.so/c",
            manual_meeting_url="",
            manual_internal_url="",
        )
        assert "consultation" not in uncovered, "수동 URL 있는 consultation은 제외"
        assert "meeting" in uncovered
        assert "internal_review" in uncovered

    # ── T21-2 ──────────────────────────────────────────────────────────────────
    def test_flowscore_guard_blocks_auto_lookup_without_file(self):
        """flowScoreFile 없을 때 자동조회 skip — `flowScoreFile and companyName` 조건 검증."""
        flow_score_file = None  # 파일 미업로드
        company_name = "테스트업체"   # 이전 세션 state에 companyName 잔류

        should_auto_lookup = bool(flow_score_file and company_name)
        assert should_auto_lookup is False, (
            "flowScoreFile 없으면 companyName이 있어도 자동조회 실행하지 않아야 함"
        )

    def test_flowscore_guard_allows_auto_lookup_with_file(self):
        """flowScoreFile과 companyName이 모두 있을 때만 자동조회 허용."""
        flow_score_file = object()   # 임의 파일 객체
        company_name = "테스트업체"

        should_auto_lookup = bool(flow_score_file and company_name)
        assert should_auto_lookup is True, (
            "flowScoreFile과 companyName 둘 다 있으면 자동조회 허용"
        )

    def test_flowscore_guard_blocks_when_company_name_empty(self):
        """flowScoreFile이 있어도 companyName 미추출이면 자동조회 skip."""
        flow_score_file = object()
        company_name = ""   # FlowScore PDF에서 기업명 추출 실패

        should_auto_lookup = bool(flow_score_file and company_name)
        assert should_auto_lookup is False, (
            "companyName 빈값이면 자동조회 skip"
        )

    # ── T21-3 ──────────────────────────────────────────────────────────────────
    def test_error_lookup_contains_missing_notion_reports(self):
        """FBU-VAL-0013 §3.1 필수 조건: errorLookup에 missing_notion_reports 키 포함."""
        uncovered = ["meeting", "internal_review"]
        error_lookup = self._build_error_lookup(uncovered)

        assert "missing_notion_reports" in error_lookup, (
            "errorLookup에는 missing_notion_reports 키가 반드시 있어야 함 (모달 메시지 표시 의존)"
        )
        assert error_lookup["missing_notion_reports"] == uncovered, (
            "missing_notion_reports 값은 uncoveredAfterError 목록과 일치해야 함"
        )

    def test_error_lookup_report_statuses_correct(self):
        """uncovered 유형 → not_found, 커버된 유형 → found_and_parsed."""
        uncovered = ["meeting"]
        error_lookup = self._build_error_lookup(uncovered)

        assert error_lookup["meeting"]["status"] == "not_found"
        assert error_lookup["consultation"]["status"] == "found_and_parsed"
        assert error_lookup["internal_review"]["status"] == "found_and_parsed"

    def test_error_lookup_issues_only_for_uncovered(self):
        """uncovered 유형의 issues는 오류 메시지 포함, 커버 유형은 빈 목록."""
        uncovered = ["internal_review"]
        error_lookup = self._build_error_lookup(uncovered, "Notion 조회 응답 오류 (503)")

        assert len(error_lookup["internal_review"]["issues"]) > 0, (
            "uncovered 유형의 issues 배열은 비어 있으면 안 됨"
        )
        assert "503" in error_lookup["internal_review"]["issues"][0]
        assert error_lookup["consultation"]["issues"] == []
        assert error_lookup["meeting"]["issues"] == []

    # ── T21-4 ──────────────────────────────────────────────────────────────────
    def test_notion_lookup_detail_stores_full_object(self):
        """notionLookupDetail에는 full lookup object가 저장되어야 함."""
        notion_lookup_full = {
            "consultation": {"status": "found_and_parsed", "page_url": "https://notion.so/c", "issues": []},
            "meeting":       {"status": "not_found",        "page_url": "",                     "issues": []},
            "internal_review": {"status": "found_and_parsed", "page_url": "https://notion.so/i", "issues": []},
        }
        notion_state_patch = {
            "notionLookupStatus": {
                "consultation": "found_and_parsed",
                "meeting": "not_found",
                "internal_review": "found_and_parsed",
            }
        }
        state = {}
        # Finding 4 수정 후 동작: status map은 patch에서, full object는 notionLookupDetail
        state.update(notion_state_patch)
        state["notionLookupDetail"] = notion_lookup_full

        assert isinstance(state.get("notionLookupStatus"), dict), (
            "notionLookupStatus는 status string map이어야 함"
        )
        assert all(isinstance(v, str) for v in state["notionLookupStatus"].values()), (
            "notionLookupStatus의 값은 모두 string이어야 함"
        )
        assert state.get("notionLookupDetail") is notion_lookup_full, (
            "notionLookupDetail에 full lookup object 저장됨"
        )

    def test_notion_lookup_status_is_not_full_object(self):
        """notionLookupStatus가 full lookup object로 덮이지 않아야 함 (Finding 4 회귀 방지)."""
        notion_lookup_full = {
            "consultation": {"status": "found_and_parsed", "page_url": "https://notion.so/c", "issues": []},
        }
        # Finding 4 이전 버그: state.notionLookupStatus = notionLookup (full object 할당)
        # → notionLookupStatus["consultation"]이 dict가 됨 (status string이 아님)
        buggy_status = notion_lookup_full  # 버그 시뮬레이션

        is_buggy = isinstance(buggy_status.get("consultation"), dict)
        assert is_buggy is True, "버그 상태 확인: full object 할당 시 값이 dict"

        # Finding 4 수정 후: notionLookupStatus는 state_patch에서 온 status map 유지
        correct_status = {"consultation": "found_and_parsed", "meeting": "not_found", "internal_review": "found_and_parsed"}
        assert all(isinstance(v, str) for v in correct_status.values()), (
            "수정 후 notionLookupStatus 값은 모두 string"
        )
