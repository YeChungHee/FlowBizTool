# 웹 디자인 전면 재작업 계획서 (v2 standalone 기반) [claude]

- 문서번호: FBU-PLAN-WEB-FULL-REDESIGN-V2-20260430
- 작성일: 2026-04-30
- 작성자: [claude]
- 사용자 지시: "기존 웹디자인은 전부 삭제하고 다시 작업하려고 해"
- 디자인 원본: `FlowBizTool _ v2 _standalone.html`
- 관련 계획:
  - `[claude]flowbiz_ui_v2_standalone_design_implementation_plan_20260430.md` (디자인 토큰)
  - `[claude]flowbiz_dual_engine_pr_merge_activation_guide_v2_7_20260430.md` (1차 PR 진행 중)
  - `flowbiz_dual_engine_evaluation_and_upgrade_lifecycle_plan_20260430.md` (듀얼 사이클)
- 결론: **"기존 웹디자인 전부 삭제"의 정확한 의미를 3구역으로 분리해 결정 필요**. HTML/CSS는 전면 재작성 가능하나 `bizaipro_shared.js`(64KB 비즈니스 로직)는 보존이 필수. **1차 PR 머지 후 별도 새 PR로 진행 권장**.

## 0. 핵심 결정 사항 — 사용자 확인 필요

### 0.1 "기존 웹디자인" 3 구역 분리

| 구역 | 파일 | 성격 | 삭제 가능성 |
|---|---|---|---|
| **A. UI 마크업/스타일** | 8 HTML + `bizaipro_shared.css` | 화면 구조 + 시각 디자인 | ✅ **삭제 + 재작성 안전** |
| **B. 비즈니스 로직** | `bizaipro_shared.js` (64KB) | parseReport, evaluateState, Notion 자동조회 등 | ❌ **삭제 금지** (백엔드 직결 — 삭제 시 평가/제안서/이메일 전체 마비) |
| **C. 산출물 자원** | mockup_*.png/svg, wireframe HTML | 시안/와이어프레임 (개발 참고용) | 🟡 **legacy/로 이동 권장** |

### 0.2 1차 PR 산출물 (보존 필수)

본 1차 PR(`codex/dual-engine-execution-20260430`)에서 web/에 추가/변경된 파일:

| 파일 | 1차 PR 변경 | 재작업 시 처리 |
|---|---|---|
| `web/dual_eval_helpers.js` | 신규 (107 lines) | **그대로 유지** (`window.FlowBizDualEvalHelpers` 네임스페이스 — 듀얼 엔진 helper) |
| 6 HTML 내부 `<script src="./dual_eval_helpers.js?v=...">` 라인 | 1줄씩 추가 | 새 HTML에도 동일 라인 포함 |

→ 1차 PR을 **먼저 main에 머지한 뒤**, 별도 PR로 web/ 재작업이 안전. 그렇지 않으면 1차 PR 변경분이 충돌.

## 1. 사용자 결정 옵션 3가지

### 1.1 옵션 1 — A 전면 + C 정리 (**권장**)

| 항목 | 내용 |
|---|---|
| 범위 | HTML 8개 + `bizaipro_shared.css` 전면 재작성 + `mockup_*.png/svg`/`wireframe.html` → `web/legacy/`로 이동 |
| 보존 | `bizaipro_shared.js` (그대로) + `dual_eval_helpers.js` (1차 PR 산출물) + `index.html` (FastAPI redirect 타깃) |
| 디자인 | v2 standalone 토큰 기반 (베이지 #F5F4EE + 검정 #0F1115 + AppleGothic) |
| 위험 | 낮음 (백엔드 무영향, JS 로직 보존) |
| 기간 | 4-6주 (Phase 1-3) |

### 1.2 옵션 2 — A + B + C 모두 신규

| 항목 | 내용 |
|---|---|
| 범위 | web/ 전체 + `bizaipro_shared.js` 64KB도 새로 작성 |
| 보존 | (없음) |
| 디자인 | v2 standalone 토큰 + React/Vite 도입 검토 |
| 위험 | **매우 높음** — parseReport/evaluateState 재구현 시 회귀 다발 발생 가능, 1차 PR `dual_eval_helpers.js` 무효화 |
| 기간 | 12-16주 (전체 frontend 스택 변경) |
| 비고 | **비추천** — 본 1차 PR과의 정합성 깨짐 |

### 1.3 옵션 3 — A 일부 (최소 필수 화면만)

| 항목 | 내용 |
|---|---|
| 범위 | 6 운영 HTML만 재작성 (home/proposal/email/evaluation/compare/changelog) + 엔진관리 탭 신규 |
| 보존 | `bizaipro_shared.js` + `dual_eval_helpers.js` + 와이어프레임/샘플 HTML 그대로 |
| 디자인 | v2 토큰 기반 |
| 위험 | 매우 낮음 |
| 기간 | 3-4주 |

### 1.4 권장 — **옵션 1 (A 전면 + C 정리)**

```
삭제 대상 (재작성):
  web/bizaipro_home.html
  web/bizaipro_proposal_generator.html
  web/bizaipro_email_generator.html
  web/bizaipro_evaluation_result.html
  web/bizaipro_engine_compare.html
  web/bizaipro_changelog.html
  web/bizaipro_3menu_wireframe.html       ← legacy/ 이동
  web/bizaipro_exhibition_wireframe.html  ← legacy/ 이동
  web/bizaipro_report_page_sample.html    ← legacy/ 이동
  web/dual_engine_ui_sample.html          ← legacy/ 이동 (UI 샘플 폐기 정책)
  web/kcnc_simtos2026_sample.html         ← legacy/ 이동
  web/bizaipro_shared.css

이동 대상 (legacy/):
  web/mockup_exhibition_mode_plan.png     ← web/legacy/mockup/
  web/mockup_home_layout_plan.png         ← web/legacy/mockup/
  web/mockup_mode_connected_plan*.svg     ← web/legacy/mockup/

보존 대상 (그대로):
  web/bizaipro_shared.js                  (64KB — 비즈니스 로직)
  web/dual_eval_helpers.js                (1차 PR 산출물)
  web/index.html                          (FastAPI redirect 타깃)

신규 추가:
  web/bizaipro_engine_management.html     (엔진관리 탭 — 월간 보고서)
  web/styles/v2_tokens.css                (디자인 토큰 분리)
  web/styles/v2_components.css            (카드/배지/테이블 컴포넌트)
  web/legacy/README.md                    (legacy 보관 사유)
```

## 2. FastAPI 통합 — 영향 분석

### 2.1 라우팅 호환성

```python
# app.py 현 상태
app.mount("/web", StaticFiles(directory=WEB_DIR, html=True), name="web")  # line 3836

@app.get("/")
def root_redirect():
    return RedirectResponse(url="/web/bizaipro_home.html")  # line 3250

# bizaipro_evaluation_result.html?case_id=... 참조
"detail_url": f"/web/bizaipro_evaluation_result.html?case_id={case.get('id')}"  # line 2327
```

**호환 유지 조건**:
- 새 HTML도 동일 파일명 사용 (`bizaipro_home.html`, `bizaipro_evaluation_result.html` 등) — 또는 redirect 갱신
- `/web` StaticFiles 마운트 그대로
- `index.html`은 FastAPI `html=True` 옵션의 fallback이므로 보존

### 2.2 Backend API 변경 없음

본 재작업은 **frontend 전용**. 다음 모든 API는 변경 없이 새 HTML이 호출:

```
GET  /api/health
GET  /api/dashboard
POST /api/evaluate
POST /api/learning/evaluate
POST /api/evaluate/dual           ← 1차 PR
POST /api/learning/evaluate/dual  ← 1차 PR
GET  /api/engine/list             ← 1차 PR
POST /api/web-context/parse
POST /api/notion/auto-lookup-and-parse
POST /api/consulting/parse
... (총 30+ endpoints)
```

→ `bizaipro_shared.js`의 fetch 호출 패턴은 동일하게 유지, HTML/CSS만 신규.

## 3. 새 디자인 시스템 (v2 standalone 기반)

### 3.1 폴더 구조 (재작업 후)

```
web/
├── index.html                           (FastAPI fallback)
│
├── bizaipro_home.html                   (재작성)
├── bizaipro_evaluation_result.html      (재작성)
├── bizaipro_proposal_generator.html     (재작성)
├── bizaipro_email_generator.html        (재작성)
├── bizaipro_engine_compare.html         (재작성)
├── bizaipro_changelog.html              (재작성)
├── bizaipro_engine_management.html      (신규 — 월간 보고서)
│
├── styles/
│   ├── v2_tokens.css                    (디자인 토큰 — color/font/spacing)
│   ├── v2_base.css                      (reset + body + 다크 헤더)
│   ├── v2_components.css                (카드/배지/테이블/검색바)
│   └── v2_layouts.css                   (페이지별 grid)
│
├── bizaipro_shared.js                   (보존 — 비즈니스 로직)
├── dual_eval_helpers.js                 (보존 — 1차 PR helper)
│
└── legacy/
    ├── README.md                        (보관 사유)
    ├── bizaipro_3menu_wireframe.html
    ├── bizaipro_exhibition_wireframe.html
    ├── bizaipro_report_page_sample.html
    ├── dual_engine_ui_sample.html       (UI 샘플 폐기 정책)
    ├── kcnc_simtos2026_sample.html
    └── mockup/
        ├── mockup_exhibition_mode_plan.png
        ├── mockup_home_layout_plan.png
        ├── mockup_mode_connected_plan.svg
        ├── mockup_mode_connected_plan_v2.svg
        └── mockup_mode_connected_plan_v3.svg
```

### 3.2 CSS 분리 전략

| 파일 | 내용 | 라인 수 예상 |
|---|---|---|
| `v2_tokens.css` | CSS 변수 (color/font/spacing/radius) | ~80 |
| `v2_base.css` | reset, body, 다크 헤더, 사이드바 | ~150 |
| `v2_components.css` | 카드, 배지, 테이블, 검색바, 칩 | ~300 |
| `v2_layouts.css` | 페이지별 grid (홈/결과/제안서) | ~200 |
| **합계** | | **~730 lines** |

기존 `bizaipro_shared.css` (33,201 bytes / ~1500 lines) 대비 **약 절반**. 명확한 분리 + 반복 제거.

### 3.3 HTML 공통 헤드 템플릿

```html
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=1200">
  <title>FlowBizTool — <!-- 페이지명 --></title>

  <link rel="stylesheet" href="./styles/v2_tokens.css?v=20260501">
  <link rel="stylesheet" href="./styles/v2_base.css?v=20260501">
  <link rel="stylesheet" href="./styles/v2_components.css?v=20260501">
  <link rel="stylesheet" href="./styles/v2_layouts.css?v=20260501">
</head>
<body>
  <header class="fbu-header">
    <div class="fbu-header__brand">FlowBizTool</div>
    <nav class="fbu-header__nav">
      <a href="./bizaipro_home.html">홈</a>
      <a href="./bizaipro_evaluation_result.html">평가결과</a>
      <a href="./bizaipro_proposal_generator.html">제안서</a>
      <a href="./bizaipro_email_generator.html">이메일</a>
      <a href="./bizaipro_engine_compare.html">엔진비교</a>
      <a href="./bizaipro_changelog.html">changelog</a>
      <a href="./bizaipro_engine_management.html">엔진관리</a>
    </nav>
  </header>

  <main class="fbu-main">
    <!-- 페이지별 콘텐츠 -->
  </main>

  <!-- 1차 PR 산출물 — 듀얼 엔진 helper (보존 필수) -->
  <script src="./dual_eval_helpers.js?v=20260430-dual-v2-11"></script>
  <!-- 비즈니스 로직 (보존 필수) -->
  <script src="./bizaipro_shared.js"></script>

  <!-- 페이지별 inline 스크립트 -->
  <script>
    // 페이지별 초기화
  </script>
</body>
</html>
```

## 4. 페이지별 새 구조 (옵션 1 적용 시)

### 4.1 `bizaipro_home.html` (대시보드)

```
[fbu-header — 다크 헤더, 7 nav 항목]

[Hero Card — KPI Large 520x280]
  ┌────────────────────────────────────┐
  │ "82" (display 84px)                │
  │ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
  │ ▓▓▓▓▓▓▓▓▓▓▓░░░░░░░  진행도 67%   │
  │ ─────────────────────────────────  │
  │ ┌─────────────┐ ┌─────────────┐   │
  │ │FPE: 82      │ │APE: 85 (+3) │   │
  │ └─────────────┘ └─────────────┘   │
  │ [fbu-consensus-badge--both-go]     │
  └────────────────────────────────────┘

[KPI Medium ×2 — FPE 단독 기준]
  ┌──────────────┐ ┌──────────────┐
  │  5억원        │ │  2.4%         │
  │  한도         │ │  마진율       │
  └──────────────┘ └──────────────┘

[SourceQuality + 상담 family]
  기업리포트: 수집 완료  |  상담 family: 13건 (전화 7 / 직접 6)

[검색바 + chip]
  [🔍 기업명 / 사업자번호] [활성] [pending]

[최근 평가 테이블 — fbu-table]
  ID | 기업명 | 평가일 | FPE | APE | consensus | 액션
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 4.2 `bizaipro_evaluation_result.html`

```
[fbu-header]

[좌(FPE — 기준)]              [우(APE — 비교 전용)]
  fbu-kpi-display "82"          fbu-kpi-display "85"
  policy_source: 276holdings    policy_source: bizaipro_learning
  knockout: 없음                FPE 대비 +3 (학습 후보 저장됨)
  consensus: both_go            (선택 불가 — §3.3 #2 강제)

[FPE 기준값 — 5억/2.4%/60일]
  → 제안서/이메일에서 사용할 단일 진실 소스

[비교표 — fbu-table]
  | 항목       | FPE  | APE  | 차이 |
  | flow_score | 82   | 85   | +3   |
  | 한도       | 5억  | 4.8억| -0.2 |
  | 마진율     | 2.4% | 2.5% | +0.1 |
```

### 4.3 `bizaipro_proposal_generator.html`

```
[fbu-header]

[FPE snapshot 카드]
  flow_score 82 / 한도 5억 / 마진 2.4% / 결제 60일
  fbu-consensus-badge--both-go

[제안서 폼 — fieldset]
  (FPE knockout 시 disabled + fbu-blocked-banner)

  <fieldset disabled={!fpeGatePassed}>
    회사명: [_______________]
    제안 한도: [5억원]  ← FPE 값 자동 채움 (수정 불가)
    마진율: [2.4%]      ← FPE 값 자동 채움
    결제유예: [60일]    ← FPE 값 자동 채움
    [제안서 생성]
  </fieldset>

  (FPE 차단 시 표시)
  [차단] 본 영업건은 FPE 기준 미충족 — 제안서 생성 불가
  사유: 신용등급 CCC + 매출 감소 추세
```

### 4.4 `bizaipro_email_generator.html`

(`proposal_generator`와 동일 구조 + 이메일 본문 영역)

### 4.5 `bizaipro_engine_compare.html`

```
[fbu-header]

[FPE 카드]                    [APE 카드]
  engine_id: FPE                engine_id: APE
  engine_label: FPE_v.16.01     engine_label: APE_v1.01
  engine_locked: true           engine_locked: false
  engine_purpose:               engine_purpose:
    fixed_screening               learning_comparison ← 옵션 A 정정
  policy_source:                policy_source:
    276holdings_limit_policy_     bizaipro_learning_loop
    manual

[버전 차이 비교표]
  | 항목 | FPE_v.16.00 | FPE_v.16.01 | 변경 사유 |
```

### 4.6 `bizaipro_changelog.html`

```
[FPE 승격 이력]
  2026-04-30 13:00 KST  FPE_v.16.01 (관리자 승인)
  2026-03-30 13:00 KST  FPE_v.15.04 (자동 promote)

[APE 학습 이력]
  2026-04-29  bizaipro_learning_registry +12 후보
  2026-04-28  Notion 수집 +18 케이스

[월간 평가엔진고도화보고서 이력]
  UR-04-30  promoted
  UR-03-30  promoted
  UR-02-29  rejected
```

### 4.7 (신규) `bizaipro_engine_management.html` — 월간 보고서

```
[fbu-header]

[월간 보고서 상태 카드 ×3]
  [pending: 3]   [approved: 12]   [promoted: 5]

[상세 목록 — fbu-table]
  | 보고서 ID | 생성일 | 상태 | 후보 수 | 액션 |
  | UR-04-30  | 04-30  | pending | 12  | [승인] [반려] [상세] |
  | UR-03-30  | 03-30  | promoted | 8  | [상세]               |

[관리자 액션 footer]
  promote API 호출 시 → FPE_v.16.02 자동 빌드 + active_framework.json 갱신
```

## 5. 7 화면 + 7항 원칙 매핑 (3차 PR §3.3 + lifecycle plan §6)

| 화면 | §3.3 7항 적용 |
|---|---|
| home | #1 FPE 고정, #4 상담 family, #6 AppleGothic, #7 SourceQuality |
| evaluation_result | #1, #2 APE 선택 불가, #3 비교 전용 |
| proposal_generator | #1, FPE 차단 시 disabled |
| email_generator | #1, FPE 차단 시 disabled |
| engine_compare | #2, #3 (APE 비교 전용 명시) |
| changelog | #5 pending/approved/promoted 이력 |
| **engine_management (신규)** | **#5 월간 보고서 상태 + 관리자 워크플로우** |

→ 7 화면 모두 §3.3 7항 원칙 1:1 적용.

## 6. 마이그레이션 단계

### 6.1 진행 전 선행 조건

```
[지금 대기] 본 1차 PR 머지 (옵션 A — engine_purpose: learning_comparison)
   ↓
[자동] main pull + 8011 재시작 + verify_dual_engine.sh 통과
   ↓
[전제 충족] 본 재작업 PR 시작 가능
```

→ **1차 PR 머지 전 web/ 재작업 시작 시 충돌 발생**. 머지 후 진행이 안전.

### 6.2 6 Phase 로드맵 (총 5-6주)

| Phase | 기간 | 산출물 |
|---|---|---|
| **Phase 0: 1차 PR 머지 + 활성화 검증** | 1일 | main에 인프라 반영 + 8011 라이브 |
| **Phase 1: legacy 이동 + 새 폴더 구조** | 2일 | `web/legacy/` 생성, mockup/wireframe 이동, `web/styles/` 생성 |
| **Phase 2: 디자인 시스템 (v2_tokens + base + components)** | 1주 | 4 CSS 파일 + 글로벌 헤더 + 카드/배지/테이블 컴포넌트 |
| **Phase 3: 운영 6 화면 재작성** | 2주 | home, evaluation_result, proposal, email, engine_compare, changelog |
| **Phase 4: 엔진관리 탭 신규** | 1주 | engine_management.html + 월간 API 연동 |
| **Phase 5: 기존 CSS/HTML 삭제 + 회귀 검증** | 3-4일 | 구 파일 git rm + Playwright/E2E + a11y 검증 |
| **합계** | **5-6주** | |

### 6.3 Phase별 git 전략

```bash
# 새 브랜치 (1차 PR 머지된 main에서 분기)
git checkout main && git pull origin main
git checkout -b codex/web-redesign-v2-20260501

# Phase 1: legacy 이동
mkdir -p web/legacy/mockup
git mv web/bizaipro_3menu_wireframe.html web/legacy/
git mv web/bizaipro_exhibition_wireframe.html web/legacy/
git mv web/bizaipro_report_page_sample.html web/legacy/
git mv web/dual_engine_ui_sample.html web/legacy/
git mv web/kcnc_simtos2026_sample.html web/legacy/
git mv web/mockup_*.png web/legacy/mockup/
git mv web/mockup_*.svg web/legacy/mockup/

# Phase 2: 새 CSS 추가
mkdir -p web/styles
# v2_tokens.css, v2_base.css, v2_components.css, v2_layouts.css 신규

# Phase 3-4: 새 HTML 작성 (구 HTML 동시 보존 — diff 기반 리뷰)
# new HTML 작성 → 구 HTML과 병기

# Phase 5: 구 파일 삭제
git rm web/bizaipro_shared.css   # 새 styles/로 대체 후
# (8 HTML은 동일 파일명으로 덮어쓰기)
```

### 6.4 사용자 화면 영향 (Phase별)

| Phase | 사용자가 보는 화면 | 영향 |
|---|---|---|
| 0 | 기존 화면 그대로 + `engine_purpose: learning_comparison` 노출 (API만) | 무 |
| 1 | 기존 화면 그대로 (legacy 이동은 화면 영향 0) | 무 |
| 2 | 기존 화면 그대로 (새 CSS는 아직 미적용) | 무 |
| 3 | **사용자 화면 v2 디자인으로 전환** | 大 — 사용자 사전 안내 필수 |
| 4 | 엔진관리 탭 신규 노출 | 관리자만 |
| 5 | 구 자원 정리 (사용자 무관) | 무 |

**핵심**: Phase 3 진입 시 사용자 환경에서 큰 시각 변화. 사전 공지 + 베타 URL(`/web-v2/`) 등 검토.

## 7. Risk + Mitigation

| Risk | 영향 | 대응 |
|---|---|---|
| `bizaipro_shared.js` 의존성 깨짐 | 평가/제안서/이메일 무력화 | 본 PR에서 .js 미수정 (Phase 5 회귀 테스트) |
| 1차 PR 변경분 충돌 | 머지 conflict | **1차 PR 먼저 머지 후 본 PR 시작** (Phase 0 강제) |
| `dual_eval_helpers.js` window 노출 깨짐 | 듀얼 엔진 helper 미동작 | 새 HTML 헤더 템플릿에 동일 라인 보존 (`§3.3 헤드 템플릿`) |
| FastAPI redirect 깨짐 | `/` 진입 시 404 | `bizaipro_home.html` 파일명 유지 또는 redirect 갱신 |
| StaticFiles 마운트 호환 | 자원 경로 깨짐 | `/web/styles/...` 경로 명시 (상대경로 `./styles/`) |
| AppleGothic Windows/Linux 미지원 | 폰트 fallback | `--fbu-font-family: AppleGothic, BlinkMacSystemFont, sans-serif` |
| 기존 사용자 북마크 (`?case_id=...`) | URL 깨짐 | 동일 파일명 유지 (`bizaipro_evaluation_result.html?case_id=...`) |
| 회귀 테스트 부재 (UI E2E) | 시각 회귀 발견 어려움 | Phase 5에 Playwright 시나리오 신설 |
| 사용자 학습 곡선 | 익숙한 화면 사라짐 | Phase 3 진입 전 변경 안내 + 핵심 워크플로우 영상 |
| `/web/bizaipro_*.html` 외부 링크 | 외부 시스템 참조 | 모든 외부 참조 위치 사전 인벤토리 |

## 8. Rollback 전략

| 시점 | Rollback 방법 |
|---|---|
| Phase 1-2 (legacy 이동/CSS만) | `git revert <commit>` — 사용자 영향 0 |
| Phase 3 (HTML 재작성 진입) | 베타 URL 우선 (`/web-v2/`) → 문제 시 `/web/`로 재할당 안 함 |
| Phase 4 (엔진관리 탭) | 관리자 limited 노출 → 문제 시 `app.py` 라우팅 차단 |
| Phase 5 (구 파일 삭제) | git history 복구 가능 (force push 금지) |

**금지 명령** (재확인): `git reset --hard`, `git clean -fd`, `git checkout .`

## 9. 검증 계획

### 9.1 Phase별 회귀 검증

| Phase | 검증 방법 |
|---|---|
| 0 | `verify_dual_engine.sh` + 7 consensus PASSED |
| 1 | `pytest tests/ -q` (web 무관 — 회귀 0건 기대) |
| 2 | 브라우저 콘솔 에러 0 + CSS 변수 노출 확인 |
| 3 | E2E (Playwright) — 6 화면 진입 + API 호출 + FPE/APE 카드 표시 |
| 4 | 엔진관리 탭 — 월간 보고서 상태 전환 워크플로우 |
| 5 | 전체 사이트 a11y (대비 4.5:1 이상) + AppleGothic fallback |

### 9.2 디자인 픽셀 비교

```bash
# Playwright 스크린샷 기반 standalone vs 신규 화면 비교
npx playwright test design-comparison.spec.ts
# → standalone 시안 95-98% 일치 확인
```

## 10. 다음 액션 — 사용자 결정

| # | 결정 항목 | 옵션 | 권장 |
|---|---|---|:---:|
| 1 | "전부 삭제"의 정확한 범위 | A 전면 / A+B+C 전면 / A 일부 | **옵션 1 (A 전면 + C 정리)** |
| 2 | 1차 PR과의 순서 | 먼저 머지 / 통합 진행 | **먼저 머지** |
| 3 | 새 페이지 라우팅 | 동일 파일명 / 새 경로(`/web-v2/`) | 동일 파일명 (Phase 3까지) + 베타 URL 준비 |
| 4 | 시작 시점 | 즉시 / 1차 PR 머지 후 | **1차 PR 머지 후** |
| 5 | 기간 | 5-6주 (옵션 1) / 12-16주 (옵션 2) / 3-4주 (옵션 3) | **5-6주 (옵션 1)** |

## 11. 즉시 실행 가능 작업 (1차 PR 머지 무관)

다음 작업은 1차 PR 머지 전이라도 **시안 보기/디자인 확정 단계**로 진행 가능:

- [ ] standalone HTML을 `web/`에 그대로 복사 (`/web/dual_engine_v2_standalone.html`) — 시연용
- [ ] `web/styles/v2_tokens.css` 디자인 토큰 파일 작성 (CSS 변수만)
- [ ] 새 페이지별 와이어프레임 검토 (본 계획서 §4 매트릭스 기준)
- [ ] AppleGothic font stack 환경별 fallback 시뮬레이션 (Windows/Linux)

## 12. 핵심 메시지

**"기존 웹디자인 전부 삭제"의 안전한 의미는 옵션 1**:
- HTML 8개 + bizaipro_shared.css = 전면 재작성
- mockup/wireframe = legacy/로 이동 (보존)
- bizaipro_shared.js (64KB 비즈니스 로직) = **삭제 금지** (백엔드 직결)
- dual_eval_helpers.js (1차 PR 산출물) = **유지** (듀얼 엔진 helper)

**진행 순서**: 1차 PR 머지 → main 활성화 → 새 브랜치 분기 → Phase 1-5 (5-6주) → 7 화면 + 엔진관리 탭 v2 디자인 완성.

**시연용 즉시 가능 작업**: standalone HTML 그대로 web/에 복사 (1분).

---

## 부록 A. 삭제/유지/이동 파일 정확한 리스트

### A.1 삭제 (재작성 후 git rm)

```
web/bizaipro_home.html                  ← 같은 이름으로 새로 작성
web/bizaipro_proposal_generator.html    ← 같은 이름으로 새로 작성
web/bizaipro_email_generator.html       ← 같은 이름으로 새로 작성
web/bizaipro_evaluation_result.html     ← 같은 이름으로 새로 작성
web/bizaipro_engine_compare.html        ← 같은 이름으로 새로 작성
web/bizaipro_changelog.html             ← 같은 이름으로 새로 작성
web/bizaipro_shared.css                 ← web/styles/* 4 파일로 분리
```

### A.2 이동 (git mv → web/legacy/)

```
web/bizaipro_3menu_wireframe.html       → web/legacy/
web/bizaipro_exhibition_wireframe.html  → web/legacy/
web/bizaipro_report_page_sample.html    → web/legacy/
web/dual_engine_ui_sample.html          → web/legacy/ (UI 샘플 폐기 정책 — §3.3 출처)
web/kcnc_simtos2026_sample.html         → web/legacy/
web/mockup_exhibition_mode_plan.png     → web/legacy/mockup/
web/mockup_home_layout_plan.png         → web/legacy/mockup/
web/mockup_mode_connected_plan.svg      → web/legacy/mockup/
web/mockup_mode_connected_plan_v2.svg   → web/legacy/mockup/
web/mockup_mode_connected_plan_v3.svg   → web/legacy/mockup/
```

### A.3 신규 (git add)

```
web/bizaipro_engine_management.html     (엔진관리 탭 신규)
web/styles/v2_tokens.css                (디자인 토큰)
web/styles/v2_base.css                  (reset + 헤더)
web/styles/v2_components.css            (카드/배지/테이블)
web/styles/v2_layouts.css               (페이지별 grid)
web/legacy/README.md                    (보관 사유)
```

### A.4 보존 (그대로)

```
web/index.html                          (FastAPI fallback)
web/bizaipro_shared.js                  (64KB 비즈니스 로직)
web/dual_eval_helpers.js                (1차 PR 산출물)
```

## 부록 B. app.py 갱신 필요 여부

| 변경 내역 | app.py 갱신 |
|---|---|
| HTML 파일명 동일 유지 | ❌ 불필요 |
| StaticFiles 마운트 그대로 | ❌ 불필요 |
| `index.html` 보존 | ❌ 불필요 |
| 엔진관리 탭 추가 | ⚠ 필요 (`/api/engine/upgrade/list` 신설 — Phase 4) |
| 7 nav 항목 redirect | ❌ 불필요 (HTML이 직접 처리) |

→ **app.py는 Phase 4까지 무변경**, Phase 4에서 월간 보고서 API만 신설.

## 부록 C. 누적 계획 매트릭스

| 계획 | 본 계획과의 관계 |
|---|---|
| `[claude]flowbiz_dual_engine_pr_merge_activation_guide_v2_7_20260430.md` | **선행 조건** (1차 PR 머지 = 본 계획 Phase 0) |
| `[claude]flowbiz_ui_v2_standalone_design_implementation_plan_20260430.md` | **상위 계획** (디자인 토큰 + 옵션 A/B/C 비교) — 본 계획은 옵션 A 구체화 |
| `flowbiz_dual_engine_evaluation_and_upgrade_lifecycle_plan_20260430.md` | Phase 4 엔진관리 탭의 데이터 모델 출처 |
| `flowbiz_dual_engine_ui_sample_validation_direction_20260430.md` | UI 샘플 폐기 정책 (§3.3 7항) — 본 계획에서 legacy/로 이동 결정 |
| `flowbiztool_v2_standalone_based_production_plan_20260430.md` | v2 production 청사진 |

## 부록 D. 옵션 1 (권장) 단일 실행 블록 (Phase 0-5 TL;DR)

```bash
# === Phase 0: 1차 PR 머지 후 ===
cd /Users/appler/Documents/COTEX/FlowBiz_ultra
git checkout main && git pull origin main
DUAL_SERVER_URL=http://127.0.0.1:8011 ./scripts/verify_dual_engine.sh
# → [ALL OK] 9 항목 + 7 consensus PASSED 입증

# === Phase 1: 새 브랜치 + legacy 이동 ===
git checkout -b codex/web-redesign-v2-20260501
mkdir -p web/legacy/mockup web/styles
git mv web/bizaipro_3menu_wireframe.html web/legacy/
git mv web/bizaipro_exhibition_wireframe.html web/legacy/
git mv web/bizaipro_report_page_sample.html web/legacy/
git mv web/dual_engine_ui_sample.html web/legacy/
git mv web/kcnc_simtos2026_sample.html web/legacy/
git mv web/mockup_*.png web/mockup_*.svg web/legacy/mockup/
echo "# Legacy 보관" > web/legacy/README.md
git add web/legacy/README.md
git commit -m "phase 1: legacy 이동 (wireframe/sample/mockup)"

# === Phase 2: 디자인 시스템 ===
# (편집기로 4 CSS 작성 — v2_tokens / v2_base / v2_components / v2_layouts)
git add web/styles/
git commit -m "phase 2: v2 디자인 시스템 (tokens + base + components + layouts)"

# === Phase 3: 운영 6 화면 재작성 ===
# (각 HTML 새로 작성 — 동일 파일명 덮어쓰기)
git add web/bizaipro_home.html web/bizaipro_evaluation_result.html \
        web/bizaipro_proposal_generator.html web/bizaipro_email_generator.html \
        web/bizaipro_engine_compare.html web/bizaipro_changelog.html
git commit -m "phase 3: 운영 6 화면 v2 디자인 재작성 (FPE 고정 + APE 비교 전용)"

# === Phase 4: 엔진관리 탭 + API ===
git add web/bizaipro_engine_management.html
# app.py — /api/engine/upgrade/list 추가
git add app.py
git commit -m "phase 4: 엔진관리 탭 + 월간 보고서 API"

# === Phase 5: 구 CSS 삭제 + 회귀 ===
git rm web/bizaipro_shared.css
# (HTML은 동일 파일명으로 덮어쓰기 완료)
python3 -m pytest tests/ -q              # 회귀 0건 기대
DUAL_SERVER_URL=http://127.0.0.1:8011 ./scripts/verify_dual_engine.sh
# (E2E Playwright — 추가 신설)
git commit -m "phase 5: 구 CSS 삭제 + 회귀 검증 통과"

# === PR 생성 ===
git push origin codex/web-redesign-v2-20260501
# 웹 UI에서 PR 생성
```
