# FlowBiz v2 D5 → D4 구현 보고서 [claude]

- 문서번호: FBU-RPT-V2-D5-D4-IMPL-20260501
- 작성일: 2026-05-01
- 작성자: [claude]
- 마스터 계획: `[claude]flowbiz_v2_d5_to_d4_master_plan_20260501.md`
- 결론: **D5/D1/D3 모두 자동 구현 완료 + push** ✅. **D4(머지) 사용자 수동 대기**.

## 0. 요약

| Step | 작업 | 결과 | commit |
|---|---|:---:|---|
| **D5** | v2 산출물 commit + push (51 files / 14,891 insertions) | ✅ | `ca02f04` |
| **D1** | 운영 6 HTML v2_tokens.css import (회귀 0) | ✅ | `e5170f5` |
| **D3** | EvaluationSnapshot API 신설 (4+2 endpoints, 312 라인) | ✅ | `82bfd28` |
| **D4** | 사용자 수동 머지 안내 | ⏳ | (사용자 액션) |

**브랜치**: `codex/v2-design-system-20260501` → 3 commits push 완료

**누적 통계**:
- 58 files changed
- 15,209 insertions, 0 deletions (회귀 0건 + 신규만)
- 4 새 API + 2 test API
- 22 컴포넌트 + 131 토큰
- 누적 codex Findings 9건 + 본 세션 신규 검증 (Go 판정) 모두 처리

## 1. D5 — v2 산출물 commit + push

### 1.1 작업 결과

```
브랜치: codex/v2-design-system-20260501 (main 기반)
HEAD:   ca02f04 (push 완료)
파일:   51 files / 14,891 insertions
```

### 1.2 포함 산출물

| 카테고리 | 파일 수 | 주요 |
|---|---:|---|
| **코드 (web/styles)** | 2 | v2_tokens.css (131 변수), v2_components.css (22 컴포넌트) |
| **코드 (web)** | 1 | v2_preview.html (13 검증 섹션) |
| **코드 (scripts)** | 2 | extract_v2_tokens_rendered.js, compare_v2_preview_vs_standalone.js |
| **E2E 인프라** | 6 | package.json, playwright.config.ts, run_e2e.sh, fixture/spec |
| **`.gitignore`** | 1 | 4 라인 추가 (data/test_evaluation_reports/, test-results/, playwright-report/, node_modules/) |
| **docs/reference/** | 4 | standalone(11MB), tokens summary, font policy, comparison summary |
| **docs/[claude] 계획서** | 17 | v1~v7 + 본 마스터 + 보강 계획 |
| **docs/[codex] 검증** | 11 | 누적 codex Findings 보고서 |

### 1.3 unrelated dirty 제외 검증

```
제외된 파일 (사용자 진행 중 작업):
  data/bizaipro_learning_registry.json
  docs/flowbiz_ultra_validation_report_registry.md
  tests/test_regression.py
  web/bizaipro_shared.css

→ codex/dual-engine-execution-20260430 (1차 PR)와 충돌 없음
```

## 2. D1 — 6 HTML v2_tokens.css import

### 2.1 작업 결과

각 6 HTML의 line 8에 추가 (line 7 `bizaipro_shared.css` 직후):
```html
<link rel="stylesheet" href="./styles/v2_tokens.css?v=20260501-d1" />
```

### 2.2 6 HTML 모두 적용 확인

```
✅ web/bizaipro_home.html               line 8
✅ web/bizaipro_proposal_generator.html  line 8
✅ web/bizaipro_email_generator.html     line 8
✅ web/bizaipro_evaluation_result.html   line 8
✅ web/bizaipro_engine_compare.html      line 8
✅ web/bizaipro_changelog.html           line 8
```

### 2.3 8011 접근 검증

```
bizaipro_home.html               → HTTP 200
bizaipro_proposal_generator.html → HTTP 200
bizaipro_email_generator.html    → HTTP 200
bizaipro_evaluation_result.html  → HTTP 200
bizaipro_engine_compare.html     → HTTP 200
bizaipro_changelog.html          → HTTP 200
v2_tokens.css                    → HTTP 200
```

### 2.4 회귀 0 보장

- v2_tokens.css는 CSS 변수 (`--fbu-*`) 만 노출
- 기존 `.bz-*` 클래스 미적용 → **시각 변화 없음**
- 사용자가 보는 화면 무영향 (Phase 2 마이그레이션 시점에 클래스 적용)

## 3. D3 — EvaluationSnapshot API 신설

### 3.1 작업 결과

`app.py` line 3833-4148 (312 라인 추가):

**Pydantic 모델** (6):
```python
class EvaluationSnapshot(BaseModel):       # decision_source: Literal["FPE"]
class ExhibitionLeadSnapshot(BaseModel):   # decision_source: None (FPE 미실행)
class ProposalSnapshot(BaseModel):
class EvaluationReportRequest(BaseModel):
class ProposalGenerateRequest(BaseModel):
class UnsafeRawSnapshotForTest(BaseModel): # ⚠ test only
```

**API 엔드포인트** (4 + 2 test):
```
POST   /api/evaluation/report               (Phase 1)
GET    /api/evaluation/report/{report_id}   (정책 검증 포함 load)
GET    /api/evaluation/reports              (최근 N건)
POST   /api/proposal/generate               (FPE 강제 — §3.3 #1-#2)
POST   /api/test/seed-raw-snapshot          (FLOWBIZ_ENV=test 가드)
DELETE /api/test/raw-snapshot/{report_id}   (test only)
```

**핵심 헬퍼**:
```python
def _new_id() -> str:
    return uuid.uuid4().hex   # v4 F1: Python 표준, 외부 의존성 0

def get_snapshot_dir() -> Path:
    if os.getenv("FLOWBIZ_ENV") == "test":
        return Path("data/test_evaluation_reports")  # v5 F4: 격리
    return Path("data/evaluation_reports")

def load_evaluation_snapshot_validated(report_id):
    raw = load_evaluation_snapshot_raw(report_id)
    if raw.get("decision_source") != "FPE":
        raise HTTPException(400, "decision_source must be FPE")  # ← 정책 강제
    required = ["fpe_credit_limit", "fpe_margin_rate", "fpe_payment_grace_days"]
    missing = [f for f in required if raw.get(f) is None]
    if missing:
        raise HTTPException(400, f"missing required fields: {missing}")
    return EvaluationSnapshot(**raw)
```

### 3.2 검증

| 검증 | 결과 |
|---|---|
| `python3 -c "import ast; ast.parse(open('app.py').read())"` | ✅ syntax OK |
| `from app import app, EvaluationSnapshot, ExhibitionLeadSnapshot, ...` | ✅ all imports |
| `pytest tests/ -q` | ✅ **76 passed** (회귀 0건) |
| 라우트 등록 확인 | ✅ 4 신규 (`/api/evaluation/report`, `/api/evaluation/report/{id}`, `/api/evaluation/reports`, `/api/proposal/generate`) |

### 3.3 1차 PR 머지 전 임시 동작

현재는 단일 FPE 평가 + APE는 동일 결과 임시 사용 (`ape_diff_summary={"note": "1차 PR dual eval 머지 전 임시"}`).

1차 PR 머지 후 변경 예정:
```python
# 현재 (1차 PR 머지 전)
result = evaluate_flowpay_underwriting(engine_input, framework)

# 1차 PR 머지 후
dual_result = await _evaluate_dual_internal(state)
```

## 4. 신규 codex 검증 처리

`[codex]flowbiz_v2_summary_and_preflight_revalidation_20260501.md` (본 세션 도중 추가):

| Finding | 상태 | 본 세션 |
|---|:---:|---|
| 1. v2_6 Preflight A unstaged-only | 최신 기준 해소 | v2_7에 awk 패턴 적용 (이전 세션) |
| 2. summary 768px stale | 해소 | 820×1180 갱신 (이전 세션) |
| **신규 P0/P1/P2** | **0건** | — |

**판정**: **Go** — D5 진행 가능 (이미 완료).

> codex §5 인용: "PR 설명에는 v2_6이 아니라 v2_7을 최종 기준 문서로 명시해야 합니다."
> → §5 PR description 권장 문구 §5.2에 반영

## 5. D4 — 사용자 수동 머지 안내

### 5.1 1차 PR 머지 (`engine_purpose: learning_comparison` 활성화)

```
URL:    https://github.com/YeChungHee/FlowBizTool/pulls
PR:     codex/dual-engine-execution-20260430 (이전 세션 push)
HEAD:   89df1eb (옵션 A 적용)
Base:   main
```

**머지 시 주의 (v2.7 §6 인용)**:
- engine.py conflict 발생 시 **6 필드 버전 채택 권장**
  - `tests/test_engine_registry.py:test_get_active_framework_meta_includes_version`이 6 필드 가정
  - `compute_report_base_limit` 부재 시 `test_compute_report_base_limit_works` 실패

### 5.2 v2 디자인 PR 생성 (D5 결과)

```
URL:    https://github.com/YeChungHee/FlowBizTool/pull/new/codex/v2-design-system-20260501
브랜치: codex/v2-design-system-20260501
HEAD:   82bfd28 (D3 완료)
Base:   main

PR Title:
  feat: v2 design system + EvaluationSnapshot API + 9 codex Findings 처리

PR Description (권장):
  ## 산출물
  - v2 디자인 시스템 (Pretendard, Toss/흰색-회색 톤, 131 토큰, 22 컴포넌트)
  - rendered DOM 100% 정합 (3 viewport — desktop/tablet 820/mobile 390)
  - E2E 인프라 (Playwright + node:crypto, FLOWBIZ_ENV=test 격리)
  - EvaluationSnapshot API (Phase 1 — 4 endpoints + 2 test)
  - 6 운영 HTML v2 토큰 import (회귀 0)

  ## 기준 문서 (v2_7 명시 — codex 신규 검증 §5)
  최종 기준: docs/[claude]flowbiz_dual_engine_pr_merge_activation_guide_v2_7_20260430.md
  (v2_6은 히스토리 보존)

  ## 누적 codex Findings 처리 (10건)
  - Phase 0 token validation: 1
  - B1 preview validation: 3 (P2)
  - B1 P2 fix revalidation: 4 (P1×3, P2×1)
  - v2 preview + PR guide recheck: 1 (P2)
  - summary + preflight recheck: 0 (Go)

  잔여 P0/P1/P2: 0건

  ## 회귀 검증
  - pytest tests/ -q: 76 passed (회귀 0)
  - compare 3 viewport: 100% (10/10) all + overflow 0
  - 운영 6 HTML 8011 접근: HTTP 200 all

  ## 미포함
  - data/bizaipro_learning_registry.json (사용자 진행 중)
  - docs/flowbiz_ultra_validation_report_registry.md (사용자 진행 중)
  - tests/test_regression.py (사용자 진행 중)
  - web/bizaipro_shared.css (사용자 진행 중)

Commit 3건:
  82bfd28 feat(D3): EvaluationSnapshot API 신설 (Phase 1 backend)
  e5170f5 feat(D1): 운영 6 HTML에 v2_tokens.css import 추가
  ca02f04 feat: v2 design system — Pretendard tokens + 22 components + E2E
```

### 5.3 머지 순서 권장

```
1. 1차 PR (codex/dual-engine-execution-20260430) 먼저 머지
   → engine.py가 6 필드 + compute_report_base_limit 보강
   → engines/ 디렉토리 main에 진입
   → /api/engine/list, /api/evaluate/dual, /api/learning/evaluate/dual 라이브

2. v2 디자인 PR (codex/v2-design-system-20260501) 머지
   → v2_tokens.css + v2_components.css main에 진입
   → 6 운영 HTML import 활성화
   → EvaluationSnapshot API 라이브
   → 1차 PR과의 통합 — D3 내부에서 dual eval 호출로 전환 후속 작업

3. 머지 후 검증
   git checkout main && git pull origin main
   curl http://127.0.0.1:8011/api/engine/list           # learning_comparison 노출
   curl -X POST http://127.0.0.1:8011/api/evaluation/report \
        -H 'Content-Type: application/json' \
        -d '{"state": {"company_name": "test"}}'         # snapshot 생성
```

## 6. 검증 매트릭스 종합

| Step | 검증 항목 | 결과 |
|---|---|:---:|
| D5 | git push origin codex/v2-design-system-20260501 | ✅ ca02f04 |
| D5 | 51 files / 14,891 insertions / 0 deletions | ✅ |
| D1 | 6 HTML v2_tokens.css link 추가 | ✅ |
| D1 | 8011 통해 6 HTML 접근 (HTTP 200) | ✅ 7/7 |
| D3 | app.py syntax 검증 | ✅ |
| D3 | from app import 모든 모델 | ✅ |
| D3 | pytest tests/ -q | ✅ 76 passed |
| D3 | 4 신규 라우트 등록 | ✅ |
| **codex 신규 검증** | **Go 판정** | **✅ 잔여 0건** |
| D4 | 1차 PR 머지 | ⏳ 사용자 수동 |
| D4 | v2 PR 생성 + 머지 | ⏳ 사용자 수동 |

## 7. 핵심 메시지

**3 commits 누적 push 완료**:
```
82bfd28  feat(D3): EvaluationSnapshot API 신설 (Phase 1 backend)
e5170f5  feat(D1): 운영 6 HTML에 v2_tokens.css import 추가
ca02f04  feat: v2 design system — Pretendard tokens + 22 components + E2E
```

**잔여 0건 + Go 판정**:
- 누적 codex Findings 9건 + 본 세션 신규 검증 (P0/P1/P2 모두 0)
- 회귀 0건 (pytest 76 passed)
- 시각 100% 정합 (3 viewport, overflow 0)

**사용자 수동 액션**:
1. 1차 PR (`codex/dual-engine-execution-20260430`) 머지 — engine_purpose: learning_comparison 활성화
2. v2 PR (`codex/v2-design-system-20260501`) 생성 + 머지 — v2 디자인 + EvaluationSnapshot 활성화

---

## 부록 A. 본 세션 누적 변경 통계

| 영역 | 파일 수 | 라인 |
|---|---:|---:|
| 디자인 토큰 | 1 | 325 |
| 컴포넌트 CSS | 1 | 898 |
| 미리보기 HTML | 1 | 363 |
| 추출 스크립트 | 2 | 996 |
| E2E 인프라 | 6 | ~700 |
| 운영 HTML | 6 | +6 (link 라인) |
| Backend API | 1 | 312 |
| docs (계획+검증) | ~32 | ~10000+ |
| docs/reference | 4 | 11MB + ~700 |
| **합계** | **~58** | **~15,300** |

## 부록 B. 기준 문서 (v2_7 명시 — codex 신규 검증)

**실행/검증 기준**: `docs/[claude]flowbiz_dual_engine_pr_merge_activation_guide_v2_7_20260430.md`

**히스토리 (보존)**: v1, v2, v2.1~v2.6

> codex 신규 검증 §4 인용:
> "실행/검증 기준 문서는 다음 파일로 고정해야 합니다:
> docs/[claude]flowbiz_dual_engine_pr_merge_activation_guide_v2_7_20260430.md"

## 부록 C. 다음 단계 (D4 후속)

| # | 작업 | 시점 | 위험 |
|---|---|---|:---:|
| 1 | 1차 PR 머지 (engine_purpose: learning_comparison) | 사용자 수동 | 낮음 |
| 2 | v2 PR 생성 + 머지 | 사용자 수동 | 낮음 |
| 3 | D3 내부 dual eval 호출로 전환 | 1+2 머지 후 | 낮음 (단순 교체) |
| 4 | Phase 2 운영 화면 v2 컴포넌트 마이그레이션 | D3 전환 후 | 중 (사용자 화면 변경) |
| 5 | Phase 4 월간 upgrade-reports API | Phase 2 후 | 낮음 |
| 6 | Phase 5 전시회 평가 흐름 | Phase 4 후 | 낮음 |

## 부록 D. 본 세션 산출물 인덱스

```
D5 산출물 (v2 design system, ca02f04):
  web/styles/v2_tokens.css
  web/styles/v2_components.css
  web/v2_preview.html
  scripts/extract_v2_tokens_rendered.js
  scripts/compare_v2_preview_vs_standalone.js
  package.json + package-lock.json
  playwright.config.ts
  tests/run_e2e.sh
  tests/e2e/fixtures/snapshot_seeder.ts
  tests/e2e/decision_source_fpe.spec.ts
  .gitignore (4 라인 추가)
  docs/reference/dual_engine_v2_standalone.html (11MB)
  docs/reference/v2_tokens_summary_20260501.md
  docs/reference/v2_font_policy_exception_20260501.md
  docs/reference/v2_preview_comparison_summary_20260501.md
  docs/[claude]*.md (17건 계획서)
  docs/[codex]*.md (11건 검증)

D1 산출물 (6 HTML import, e5170f5):
  web/bizaipro_home.html               + 1 line
  web/bizaipro_proposal_generator.html + 1 line
  web/bizaipro_email_generator.html    + 1 line
  web/bizaipro_evaluation_result.html  + 1 line
  web/bizaipro_engine_compare.html     + 1 line
  web/bizaipro_changelog.html          + 1 line

D3 산출물 (EvaluationSnapshot API, 82bfd28):
  app.py (+312 라인, line 3833-4148)
    - 6 Pydantic 모델
    - 4 production endpoints + 2 test endpoints
    - 4 헬퍼 함수
```

**최종 상태**: D5/D1/D3 자동 완료, D4 사용자 수동 대기. 잔여 codex Findings 0건.
