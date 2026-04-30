"""engines/ registry + 모듈 분리 회귀 테스트.

검증 대상:
- engines.get_engine alias 매핑 (case-insensitive + 4가지 FPE 변형 + APE)
- engines.list_engines() 응답 shape
- engines.ape / engines.fpe 모듈 META + get_meta
- 분리 후 backward-compat (engine.py에서 모든 기존 export)
"""
from __future__ import annotations

import pytest

from engines import get_engine, list_engines, ape, fpe


class TestRegistryAliases:
    @pytest.mark.parametrize("alias,expected_id", [
        ("fpe", "FPE"),
        ("FPE", "FPE"),
        ("FPE_v.16.01", "FPE"),
        ("FPE_v16.01", "FPE"),
        ("fpe_v1601", "FPE"),
        ("fpe_v.16.01", "FPE"),
        ("ape", "APE"),
        ("APE", "APE"),
        ("APE_v1.01", "APE"),
        ("ape_v1_01", "APE"),
    ])
    def test_alias_resolves(self, alias, expected_id):
        engine = get_engine(alias)
        assert engine.META.engine_id == expected_id

    def test_unknown_alias_raises(self):
        with pytest.raises(ValueError, match="Unknown engine alias"):
            get_engine("NOT_A_REAL_ENGINE")

    def test_empty_alias_raises(self):
        with pytest.raises(ValueError, match="Engine alias is required"):
            get_engine("")


class TestListEngines:
    def test_returns_two_engines(self):
        engines = list_engines()
        ids = {e["engine_id"] for e in engines}
        assert "FPE" in ids
        assert "APE" in ids
        assert len(engines) == 2

    def test_engine_meta_required_keys(self):
        for engine in list_engines():
            for key in ("engine_id", "engine_label", "engine_version", "engine_locked", "engine_purpose"):
                assert key in engine

    def test_fpe_locked_ape_unlocked(self):
        engines = {e["engine_id"]: e for e in list_engines()}
        assert engines["FPE"]["engine_locked"] is True
        assert engines["APE"]["engine_locked"] is False


class TestEngineMeta:
    def test_ape_meta_constants(self):
        assert ape.META.engine_id == "APE"
        assert ape.META.engine_label == "APE_v1.01"
        assert ape.META.engine_purpose == "learning_comparison"
        assert ape.META.engine_locked is False

    def test_fpe_meta_constants(self):
        assert fpe.META.engine_id == "FPE"
        assert fpe.META.engine_label == "FPE_v.16.01"
        assert fpe.META.engine_purpose == "fixed_screening"
        assert fpe.META.engine_locked is True
        assert fpe.META.policy_source == "276holdings_limit_policy_manual"

    def test_ape_get_meta_includes_active(self):
        meta = ape.get_meta()
        assert "active_version" in meta
        assert "active_source" in meta


class TestBackwardCompat:
    """engine.py 호환 shim — 기존 import 경로 유지."""

    def test_compute_limit_amount_signature_preserved(self):
        from engine import compute_limit_amount
        import inspect
        sig = inspect.signature(compute_limit_amount)
        assert list(sig.parameters.keys()) == ["input_data", "overall_score", "buyer_score", "model"]

    def test_load_active_framework_works(self):
        from engine import load_active_framework
        fw = load_active_framework()
        assert isinstance(fw, dict)
        assert "version" in fw

    def test_get_active_framework_meta_includes_version(self):
        from engine import get_active_framework_meta
        meta = get_active_framework_meta()
        for key in ("framework_path", "source", "filename", "version", "engine_id", "engine_label"):
            assert key in meta

    def test_compute_report_base_limit_works(self):
        from engine import compute_report_base_limit, load_active_framework
        result = compute_report_base_limit(10_000_000_000, load_active_framework())
        assert isinstance(result, int)
        assert result > 0


class TestApeFromEnginesPackage:
    def test_compute_limit_amount_via_engines_ape(self):
        from engines.ape import compute_limit_amount, load_active_framework
        fw = load_active_framework()
        result = compute_limit_amount(
            {"requested_tenor_months": 2,
             "financials": {"annual_sales": 1_000_000_000, "operating_profit": 50_000_000, "net_profit": 30_000_000},
             "screening": {"business_years": 8.0, "credit_grade": "BB+"}},
            70.0, 70.0, fw["flowpay_underwriting"],
        )
        assert isinstance(result, int)
        assert result > 0

    def test_engines_ape_eval_evaluates(self):
        # engines.ape.evaluate은 framework 미지정 시 active 자동 로드
        # 이 테스트는 input shape 정합성보다 import + 호출 가능성 확인이 목적
        from engines.ape import evaluate
        # 잘못된 input → ValueError but importable + callable
        with pytest.raises((KeyError, ValueError, AttributeError)):
            evaluate({})  # 빈 input → 일부 키 누락 에러는 정상
