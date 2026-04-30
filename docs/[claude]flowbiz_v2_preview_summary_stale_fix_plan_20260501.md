# FlowBiz v2 Preview Summary Stale 정정 추가 계획서 [claude]

- 문서번호: FBU-PLAN-V2-SUMMARY-STALE-FIX-20260501
- 작성일: 2026-05-01
- 작성자: [claude]
- 검증: `[codex]flowbiz_v2_preview_and_pr_guide_revalidation_20260501.md` (P2 1건 — **조건부 Go**)
- 변경 사유: codex 재검증 결과 **이전 6 Finding 중 5건 해소 + 1건 잔여(P2)** 즉시 정정

## 0. 검증 결과 요약

### 0.1 codex 판정

| 항목 | 결과 |
|---|---|
| 이전 6 Finding 중 해소 | **5/6** |
| 잔여 | **F1 P2 1건** (`reference summary 문서 stale`) |
| Go/No-Go | **조건부 Go** (잔여 F1 정정 후 D5 진행 가능) |

### 0.2 이전 Finding 해소 매트릭스

| # | 이전 Finding | codex 판정 |
|---|---|:---:|
| 1 | 반응형 검증이 desktop만 반영 | ✅ 해소 |
| 2 | 768px tablet 설명 vs CSS 불일치 | 🟡 부분 해소 (스크립트는 820, summary 문서만 stale) |
| 3 | 모바일 390px 가로 overflow | ✅ 해소 |
| 4 | visible copy 100% 정합 표현 과장 | ✅ 해소 |
| 5 | preflight grep 변수 대입 실패 가능 | ✅ 해소 |
| 6 | stash 복구 stash@{0} 의존 | ✅ 해소 |

→ **5건 해소 + 1건(F1 P2) 본 세션 정정 완료**.

### 0.3 실행 검증 결과 (codex §3 인용)

```
| Viewport          | 결과         | Overflow |
|-------------------|--------------|----------|
| desktop 1200x900  | 100% (10/10) | ok       |
| tablet  820x1180  | 100% (10/10) | ok       |
| mobile  390x844   | 100% (10/10) | ok       |
```

→ 코드/실행 검증 모두 통과. 잔여는 PR 추적용 docs 1개만.

## 1. F1 [P2] 즉시 정정 — 본 세션 완료

### 1.1 잔여 위치 (codex §4 인용)

`docs/reference/v2_preview_comparison_summary_20260501.md`가 다음 stale 정보 유지:
- tablet 행: `768 × 1024`
- 산출물 파일: `standalone_tablet.png (768x1024)`, `v2_preview_tablet.png (768x1024)`

### 1.2 정정 내용 (3 위치)

#### 위치 1 — §2.2 반응형 검증 표
```diff
- | **tablet (iPad)** | 768 × 1024 | ✅ 토큰 100% + 5열→3열 reflow |
+ | **tablet (iPad Air)** | **820 × 1180** | ✅ 토큰 100% + 5열→3열 reflow (1024px 미디어쿼리 적용) |
+
+ > **태블릿 viewport 820px 채택 사유** (codex B1-P2-fix F1 정정):
+ > 기존 768px은 모바일 미디어쿼리(`@media (max-width: 768px)`) 경계에 걸려 1열 reflow되어
+ > 1024px 미디어쿼리(`@media (max-width: 1024px)`) 검증이 불가능했음.
+ > 820px (iPad Air width)로 변경하여 1024px 미디어쿼리만 정상 적용 검증.
```

#### 위치 2 — §5 산출물 매트릭스
```diff
- ├── standalone_tablet.png       (768×1024)
- ├── v2_preview_tablet.png       (768×1024)
+ ├── standalone_tablet.png       (820×1180)   ← codex B1-P2-fix F1 정정 (768→820)
+ ├── v2_preview_tablet.png       (820×1180)   ← codex B1-P2-fix F1 정정
```

#### 위치 3 — §3 본 검증으로 확인된 사항
```diff
- 4. **반응형 안정성**: 768px/390px에서도 핵심 토큰 변화 없음
+ 4. **반응형 안정성**: 1200px/820px/390px 모두 핵심 토큰 100% 일치 + overflow 0
+ 5. **모바일 horizontal overflow 차단**: box-sizing border-box + body overflow-x:hidden 보조
```

#### 위치 4 — §7 codex 검증 처리 매트릭스 (확장)
```diff
+ | `[codex]flowbiz_ui_v2_b1_p2_fix_revalidation_20260501.md` F1 (768 vs CSS) | ✅ 태블릿 820×1180으로 변경 |
+ | 동 F2 (3 viewport 자동 비교) | ✅ viewport별 matchRate/matches/totalCmp 자동 출력 |
+ | 동 F3 (모바일 overflow 10px) | ✅ 14 컴포넌트 box-sizing + scrollWidth assertion 0 |
+ | 동 F4 (화면 문구 과함) | ✅ "핵심 10개 computed style 기준 100%" 정정 |
+ | `[codex]flowbiz_v2_preview_and_pr_guide_revalidation_20260501.md` §4 F1 P2 (summary stale) | ✅ **본 §2.2 + §5 viewport 768→820 갱신** (본 세션) |
```

### 1.3 정정 검증

```bash
$ grep -n "768\|820" docs/reference/v2_preview_comparison_summary_20260501.md
52:| **tablet (iPad Air)** | **820 × 1180** | ...
57:> **태블릿 viewport 820px 채택 사유** ...
64:4. **반응형 안정성**: 1200px/820px/390px ...
82:├── standalone_tablet.png       (820×1180)
85:├── v2_preview_tablet.png       (820×1180)
123:| 동 §5 P2-2 (반응형 768/390 추가) | ✅ ...   ← codex 인용 컨텍스트만
125:| ... F1 (768 vs CSS) | ✅ 태블릿 820×1180으로 변경 |   ← 정정 사실 인용
129:| ... summary stale | ✅ 본 §2.2 + §5 viewport 768→820 갱신 |
```

→ **본문 viewport 768 잔재 0**, codex 검증 인용 컨텍스트만 768 유지 (정합).

## 2. codex §5 Go/No-Go 충족

| codex §5 조건 | 본 세션 처리 |
|---|:---:|
| `docs/reference/v2_preview_comparison_summary_20260501.md` 갱신 | ✅ |
| tablet 행 820×1180 | ✅ |
| 설명에 820px 기준 명시 | ✅ |
| 산출물 목록의 tablet 파일 820×1180 | ✅ |

→ **모든 조건 충족** → **D5 산출물 commit + PR 분리 가능 상태**.

## 3. 핵심 메시지

**6 → 0 잔여 Finding**:
- 이전 6 Finding → 본 세션 직전 5건 해소
- 본 세션 F1 P2 1건 정정 → **모든 잔여 0건**

→ codex §5 인용: "코드와 실행 검증 기준으로는 D5 진행이 가능해졌습니다. 다만 PR에 포함되는 docs 문서가 아직 stale이므로, 이 문서만 갱신한 뒤 D5 산출물 commit + PR 분리를 진행하는 것이 안전합니다."

→ **본 세션 정정으로 D5 진행 안전 조건 충족**.

---

## 부록 A. 누적 codex Findings 처리 매트릭스 (전체)

| codex 보고서 | 신규 Finding | 처리 단계 | 잔여 |
|---|---|---|:---:|
| Phase 0 token validation | 1 | A3+A1 | 0 |
| B1 preview validation | 3 | C1 | 0 |
| B1 P2 fix revalidation | 4 (P1×3, P2×1) | B1-P2-fix v2 | 0 |
| **v2 preview + PR guide revalidation** | **1 (P2)** | **본 세션** | **0** |
| **누적** | **9** | **전체 처리** | **0** |

## 부록 B. 본 세션 즉시 실행 작업 로그

| 작업 | 결과 |
|---|---|
| `docs/reference/v2_preview_comparison_summary_20260501.md` §2.2 tablet 820 정정 | ✅ |
| 동 §3 본 검증 §3.4-§3.5 추가 (1200/820/390 + overflow) | ✅ |
| 동 §5 산출물 표기 820×1180 정정 | ✅ |
| 동 §7 codex 검증 처리 매트릭스 확장 (B1-P2-fix + v2-recheck) | ✅ |
| grep 검증 — 본문 768 잔재 0 | ✅ |

## 부록 C. D5 진행 직전 체크리스트

| # | 항목 | 상태 |
|---|---|:---:|
| 1 | 코드 변경 검증 (compare 스크립트 3 viewport 100%) | ✅ |
| 2 | overflow assertion 0 (3 viewport 모두) | ✅ |
| 3 | v2_preview.html 화면 문구 정확 | ✅ |
| 4 | docs/reference/ 요약 stale 0 | ✅ (**본 세션**) |
| 5 | codex 검증 P0/P1/P2 잔여 0 | ✅ (**본 세션**) |
| 6 | git status 정리 (unrelated dirty 분리) | ⏳ D5 진행 시 |
| 7 | PR description 작성 | ⏳ D5 진행 시 |

→ **5/7 완료 + 2건은 D5 직전 작업**. 사용자 신호 시 D5 진행 가능.

## 부록 D. D5 산출물 PR 범위 (제안)

본 PR에 포함:
```
산출물 (작성):
  scripts/extract_v2_tokens_rendered.js                   (A3)
  scripts/compare_v2_preview_vs_standalone.js              (C1+B1-P2-fix)
  web/styles/v2_tokens.css                                  (A1)
  web/styles/v2_components.css                              (B1+B1-P2-fix)
  web/v2_preview.html                                       (B1+B1-P2-fix)
  package.json                                              (Phase 0)
  playwright.config.ts                                      (Phase 0)
  tests/run_e2e.sh                                          (Phase 0)
  tests/e2e/fixtures/snapshot_seeder.ts                     (Phase 0)
  tests/e2e/decision_source_fpe.spec.ts                     (Phase 0)
  .gitignore                                                 (4 라인 추가)

문서 (PR 추적):
  docs/reference/dual_engine_v2_standalone.html             (11MB 시안)
  docs/reference/v2_tokens_summary_20260501.md              (P2-1)
  docs/reference/v2_font_policy_exception_20260501.md       (P2-2)
  docs/reference/v2_preview_comparison_summary_20260501.md  (P2-3 + 본 세션 정정)

계획서 (코드 무관):
  docs/[claude]flowbiz_ui_v2_standalone_design_implementation_plan_v7_*.md
  docs/[claude]flowbiz_ui_v2_b1_p2_fix_v2_plan_*.md
  docs/[claude]flowbiz_v2_preview_summary_stale_fix_plan_*.md (본 문서)

PR 제외 (본 PR과 무관):
  data/bizaipro_learning_registry.json (기존 dirty)
  docs/flowbiz_ultra_validation_report_registry.md (기존 dirty)
  tests/test_regression.py (기존 dirty)
  web/bizaipro_shared.css (기존 dirty)
  data/test_evaluation_reports/ (gitignore)
  outputs/ (gitignore)
  node_modules/ (gitignore)
```

## 부록 E. 다음 단계 결정

| # | 작업 | 위험 | 추천 시점 |
|---|---|:---:|:---:|
| **D5** | A3+A1+B1+C1+B1-P2-fix v2 + 본 세션 정정 별도 PR 분리 | 낮음 | **지금** (모든 codex 검증 통과) |
| D1 | 운영 6 HTML에 v2 토큰 import (Phase 2 선행) | 낮음 | D5 후 |
| D3 | EvaluationSnapshot API 신설 (Phase 1 backend) | 낮음 | D5 후 / 1차 PR 머지 후 |
| D4 | 1차 PR 머지 (`engine_purpose: learning_comparison`) | 낮음 | 사용자 수동 |

**대기 상태**. D5 진행 시 git commit + PR 분리 자동화 가능.
