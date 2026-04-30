# FPE_v.16.01 — 276홀딩스 한도 정책 매뉴얼 기반 고정 심사엔진

학습하지 않음. 정책 파일이 모든 평가 기준의 단일 진실 위치.

## 식별

| 필드 | 값 |
|---|---|
| engine_id | `FPE` |
| engine_label | `FPE_v.16.01` |
| engine_locked | `true` (학습 금지) |
| engine_purpose | `fixed_screening` |
| policy_source | `276holdings_limit_policy_manual` |

## 모듈 구조

```
engines/fpe/
├── __init__.py     ← META + 공개 API export
├── policy.py       ← load_policy, fpe_policy_grade, FPE_POLICY_PATH
└── eval.py         ← evaluate (메인 머지 후 actual implementation 이동 예정)
```

## 데이터 위치

```
data/engines/fpe/
└── policy.json     ← 276홀딩스 매뉴얼 매핑 정책
                       (메인 머지 시 data/fpe_v1601_policy.json → 여기로 이동)
```

## 정책 핵심 파라미터 (정책 JSON)

| 항목 | 값 |
|---|---|
| `base_sales_ratio` | 0.0075 (연매출 0.75%) |
| `conservative_sales_ratio` | 0.005 |
| `grade_factors` | A=4.0 / B=1.5 / C=1.0 / D=0.5 / E=0.0 |
| `transaction_execution_ratios` | A=1.0 / B=0.8 / C=0.5 |
| `margin.base_margin_pct` | 5.0% (tenor 프리미엄 + 신용보강 조정) |
| `knockout.excluded_credit_grades` | CCC- / CC / C / D |

## 평가 흐름 (engine.py:evaluate_fpe_v1601)

```
input_data
    ↓
evaluate_flowpay_underwriting()    ← 점수 인프라 공유
    ↓
fpe_detect_knockout_reasons()       ← 276홀딩스 정책 knockout
    ↓
compute_fpe_customer_base_limit()   ← Tier1: 고객 기본 한도
    ↓
classify_fpe_transaction_risk()     ← 거래 위험 등급
    ↓
compute_fpe_limit_adjustment()      ← 한도 조정
    ↓
compute_fpe_transaction_limit()     ← Tier2: 거래 한도
    ↓
compute_fpe_margin()                ← 마진
    ↓
classify_fpe_review_path()          ← fast_track / team / management
```

## 분리 작업 상태

**현재 (워크트리)**: scaffolding만 있음 — `eval.py:evaluate`는 메인의 `evaluate_fpe_v1601` import를 시도하고 실패 시 `NotImplementedError`.

**메인 머지 후**: 다음 함수들이 메인의 `engine.py`에서 `engines/fpe/eval.py`로 이동:
- `evaluate_fpe_v1601` (~engine.py:1194)
- `fpe_detect_knockout_reasons` (~engine.py:826)
- `compute_fpe_customer_base_limit` (~engine.py:852)
- `classify_fpe_transaction_risk` (~engine.py:873)
- `compute_fpe_limit_adjustment` (~engine.py:930)
- `compute_fpe_transaction_limit` (~engine.py:983)
- `compute_fpe_margin` (~engine.py:1005)
- `classify_fpe_review_path` (~engine.py:1043)
- `fpe_policy_grade` (~engine.py:557, policy.py로 이동)

## 잠금 정책 (engine_locked)

학습 파이프라인이 실수로 FPE 정책을 학습 결과로 덮어쓰지 못하도록 `engine_locked: true`.

```python
# bizaipro_learning.py:run_promote()
if snapshot.get("engine_locked"):
    return {"promoted": False, "reason": f"{snapshot.get('engine_id')} is locked"}
```

(머지 후 가드 추가 예정)

## 사용 예 (Python, 머지 후)

```python
from engines import get_engine
fpe = get_engine("FPE_v.16.01")
result = fpe.evaluate(input_data)
```
