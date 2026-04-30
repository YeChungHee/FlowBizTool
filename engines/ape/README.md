# APE_v1.01 — Adaptive Proposal Engine

학습 기반 비즈니스 제안 평가 엔진. FlowPay 거래 가능성·예상 한도·마진율을 학습 데이터로 지속 고도화.

## 식별

| 필드 | 값 |
|---|---|
| engine_id | `APE` |
| engine_label | `APE_v1.01` |
| engine_locked | `false` (학습 가능) |
| engine_purpose | `learning_proposal` |
| policy_source | `bizaipro_learning_loop` |

## 모듈 구조

```
engines/ape/
├── __init__.py     ← META + 공개 API export
├── framework.py    ← load_active_framework, get_active_framework_meta, compute_report_base_limit
└── eval.py         ← compute_limit_amount(_detail), DR adjustment, C+ 등급 판정
```

## 데이터 위치

```
data/engines/ape/
├── frameworks/
│   ├── _baseline.json      ← APE baseline (BIZAIPRO_BASELINE)
│   ├── v.1.16.01.json      ← 학습 가중치 보정 체크포인트
│   └── v.1.18.02.json      ← annual_sales_rate × DR_adj 산식
├── active_framework.json   ← 라이브 (promote 결과)
└── learning_registry.json  ← 학습 케이스 누적 (계획)
```

## 한도 산식 mode

| mode | base 산식 | 적용 체크포인트 |
|---|---|---|
| `monthly_sales_ratio` | `annual_sales / 12 × ratio` | v.1.16.01, baseline |
| `annual_sales_rate_with_dynamic_rate_adjustment` | `annual_sales × 0.075 × DR_adj` | v.1.18.02 |

**5개 보정계수**(age/profit/risk/buyer/tenor)는 mode 공통 적용.
**C+ c_grade_factor 0.60**는 v.1.18.02 한정. C/CCC-/CC/D는 baseline knockout 경로.

## Dynamic Rate adjustment

```
DR_raw = GM*0.30 + OP*0.50 + NP*0.20  (decimal)
DR_adj = clamp(1 + (DR_raw - 0.075) × 5, 0.60, 1.50)
GM 누락 → DR_adj = 1.0 (use_center_rate_only fallback)
```

검증 예: GM=8.5%, OP=5%, NP=3% → DR_adj = **0.9075**

## promote / rollback

```bash
# 체크포인트 라이브 적용
python3 bizaipro_learning.py promote --version v.1.18.02

# baseline 복귀
python3 bizaipro_learning.py rollback

# 특정 버전으로 복귀
python3 bizaipro_learning.py rollback --to v.1.16.01
```

## 사용 예 (Python)

```python
from engines import get_engine
ape = get_engine("ape")
result = ape.evaluate(input_data)  # active framework 자동 로드
```
