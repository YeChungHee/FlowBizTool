# FlowBizTool v2 Standalone 디자인 구현 계획서 [claude]

- 문서번호: FBU-PLAN-UI-V2-STANDALONE-IMPL-20260430
- 작성일: 2026-04-30
- 작성자: [claude]
- 디자인 원본: `FlowBizTool _ v2 _standalone.html` (11,046,793 bytes / 206 lines)
- 관련 계획:
  - `[claude]flowbiz_dual_engine_pr_merge_activation_guide_v2_7_20260430.md` (1차 PR 활성화 — 진행 중)
  - `flowbiz_dual_engine_evaluation_and_upgrade_lifecycle_plan_20260430.md` (듀얼 엔진 사이클)
  - `flowbiztool_v2_standalone_based_production_plan_20260430.md` (v2 production 계획)
- 결론: **v2 standalone 디자인은 self-contained "bundler" 형식 시안 → 디자인 토큰 추출 + FastAPI/web 6 HTML 마이그레이션 + 3차 PR §3.3 7항 원칙 통합으로 구현**.

## 1. 원본 디자인 분석

### 1.1 파일 형식 — Bundler standalone HTML

```
파일 크기: 11 MB / 206 lines (base64 임베드)
구조:
  ├── <head> CSS + 폰트 (baseline)
  ├── <body>
  │   ├── #__bundler_thumbnail (SVG loading 미리보기)
  │   ├── #__bundler_loading ("Unpacking..." 메시지)
  │   ├── <script type="__bundler/manifest"> (압축 base64 자원)
  │   ├── <script type="__bundler/template"> (DOM 템플릿)
  │   ├── <script type="__bundler/ext_resources"> (외부 자원 매핑)
  │   └── <script> 디코드 + DecompressionStream(gzip) + replaceWith
  └── 런타임 unpack → 실제 React/HTML 화면
```

→ **figma/Anthropic Artifacts 계열 디자인 export 형식**. 그대로 FastAPI에 넣을 수는 없으나 **시각 시안 + 디자인 토큰의 진실 소스**.

### 1.2 SVG thumbnail에서 추출한 디자인 토큰

```css
/* === Color tokens === */
--color-bg-primary:    #F5F4EE;  /* body 배경 (베이지) */
--color-bg-card:       #FFFFFF;  /* 카드 배경 (흰색) */
--color-bg-header:     #0F1115;  /* 다크 헤더 (검정) */

--color-text-primary:  #0F1115;  /* 본문 텍스트 (검정) */
--color-text-on-dark:  #F5F4EE;  /* 다크 헤더 위 텍스트 (베이지) */

--color-border:        #E5E2D6;  /* 카드/구분선 (밝은 베이지) */
--color-divider:       #E5E2D6;  /* 테이블 row divider */

/* === Typography === */
--font-family-base: -apple-system, BlinkMacSystemFont, "AppleGothic", sans-serif;
--font-size-display: 84px;    /* 큰 KPI 숫자 (예: "82") */
--font-size-title:   36px;    /* 중형 KPI (예: "5억원", "2.4%") */
--font-size-body:    14px;
--font-size-small:   12px;
--font-weight-bold:  700;
--font-weight-regular: 400;

/* === Layout === */
--header-height: 56px;
--card-radius:   8px;
--input-radius:  6px;
--chip-radius:   4px;
--gap-section:   24px;
--gap-card:      32px;

/* === Component metrics (SVG 기준) === */
--card-kpi-large-width:  520px;   /* 좌측 큰 KPI 카드 */
--card-kpi-large-height: 280px;
--card-kpi-medium-width: 568px;   /* 우측 중형 KPI 2개 */
--card-kpi-medium-height: 132px;
--searchbar-height: 44px;
--table-row-height: 44px;
```

### 1.3 화면 구조 (1200×800 기준)

```
┌──────────────────────────────────────────────────────────────────┐
│ [DARK HEADER #0F1115, height 56px]                               │
│  Logo(120x12)   Nav1   Nav2   Nav3                               │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌───────────────────────┐   ┌─────────────────────────────────┐ │
│  │  KPI LARGE (520x280)  │   │  KPI MEDIUM A (568x132)         │ │
│  │  "82" + progress bar  │   │  "5억원" (한도)                  │ │
│  │  + 2 sub cards        │   ├─────────────────────────────────┤ │
│  │                       │   │  KPI MEDIUM B (568x132)         │ │
│  │                       │   │  "2.4%" (마진)                   │ │
│  └───────────────────────┘   └─────────────────────────────────┘ │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────────┐│
│  │ [SEARCH BAR + 2 CHIPS, height 44px]                          ││
│  └──────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ┌──────────────────────────────────────────────────────────────┐│
│  │ TABLE (1120 wide, 6+ rows × 44px)                            ││
│  │  ─── divider lines ───                                       ││
│  │  Row 1                                                       ││
│  │  Row 2                                                       ││
│  │  Row 3 ...                                                   ││
│  └──────────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────────┘
```

### 1.4 시각 정체성 요약

| 특성 | 값 | 의미 |
|---|---|---|
| 무드 | Apple Human Interface 계열 미니멀 | 한국 영업도구의 "정보 가시성" 우선 |
| 컬러 팔레트 | 베이지(#F5F4EE) + 검정(#0F1115) + 흰카드(#FFFFFF) | 차분한 비즈니스 톤, 색약 친화적 |
| 타이포 | 작은 라벨 + 거대 KPI 숫자 (84px) | "결과를 한 눈에" 강조 |
| 레이아웃 | 카드 그리드 + 테이블 | 데이터-드리븐 워크플로우 |
| 인터랙션 | (시안에선 미동작) | 3차 PR에서 듀얼 엔진과 결합 |

## 2. 구현 전략 — 3 옵션 비교

### 2.1 옵션 A — 디자인 토큰만 추출 후 기존 6 HTML 마이그레이션 (**권장**)

| 항목 | 내용 |
|---|---|
| 작업 | `bizaipro_shared.css`에 v2 디자인 토큰 추가 + 6 HTML 클래스 매핑 갱신 |
| 장점 | 기존 라우팅/JS/state 보존 + AppleGothic + dual_eval_helpers 그대로 동작 |
| 단점 | standalone의 정확한 픽셀 재현은 다소 손실 |
| 위험 | 낮음 (CSS 단계 수정) |

### 2.2 옵션 B — standalone HTML 그대로 `web/`에 복사 (참고/시연용)

| 항목 | 내용 |
|---|---|
| 작업 | `web/dual_engine_v2_standalone.html` 추가, 사이드바 메뉴에서 "디자인 시안" 링크 |
| 장점 | 11MB 거대 파일이지만 시안 그대로 보존 |
| 단점 | FastAPI 서버 통합 안 됨, 듀얼 엔진 API와 분리 |
| 위험 | 매우 낮음 (별도 정적 파일) |

### 2.3 옵션 C — standalone bundler unpacking → React 컴포넌트 분해 → FastAPI 통합

| 항목 | 내용 |
|---|---|
| 작업 | manifest/template 디코드 → React 컴포넌트 추출 → FastAPI 라우팅 |
| 장점 | 픽셀 단위 일치 + 동적 데이터 바인딩 |
| 단점 | bundler 형식 역공학 + React/Vite 빌드 시스템 도입 |
| 위험 | 높음 (전체 frontend 스택 변경) |

### 2.4 권장 — 옵션 A + B 병행

```
[지금] standalone HTML 보존 (옵션 B) — 시각 진실 소스
   ↓
[3차 PR] 6 HTML을 v2 디자인 토큰으로 마이그레이션 (옵션 A)
   ↓
[Phase 5] 시안과 실제 화면 픽셀 비교 검증 → 차이 정정
   ↓
(향후 v3) 필요 시 옵션 C 검토 (현재 단계에서는 불필요)
```

## 3. 디자인 시스템 통합 (Phase 1 — 즉시 가능)

### 3.1 `bizaipro_shared.css` 디자인 토큰 신설

```css
/* === FlowBizTool v2 standalone 디자인 토큰 (FBU-UI-V2-20260430) === */
:root {
  /* Colors */
  --fbu-color-bg-primary:    #F5F4EE;
  --fbu-color-bg-card:       #FFFFFF;
  --fbu-color-bg-header:     #0F1115;
  --fbu-color-text-primary:  #0F1115;
  --fbu-color-text-on-dark:  #F5F4EE;
  --fbu-color-border:        #E5E2D6;
  --fbu-color-divider:       #E5E2D6;

  /* Consensus 5 colors (3차 PR §3.3 #1-#3) */
  --fbu-color-consensus-both-go:           #2E7D32;  /* green */
  --fbu-color-consensus-fpe-blocked:       #C62828;  /* red */
  --fbu-color-consensus-ape-only-positive: #F57C00;  /* orange */
  --fbu-color-consensus-ape-blocked:       #5E35B1;  /* purple (v3 정책 대기) */
  --fbu-color-consensus-both-review:       #757575;  /* grey */

  /* Typography (AppleGothic 우선 — §3.3 #6) */
  --fbu-font-family: "AppleGothic", -apple-system, BlinkMacSystemFont, sans-serif;
  --fbu-font-size-display: 84px;
  --fbu-font-size-title:   36px;
  --fbu-font-size-h1:      28px;
  --fbu-font-size-h2:      20px;
  --fbu-font-size-body:    14px;
  --fbu-font-size-small:   12px;
  --fbu-font-weight-bold:    700;
  --fbu-font-weight-regular: 400;

  /* Layout */
  --fbu-header-height: 56px;
  --fbu-card-radius:   8px;
  --fbu-input-radius:  6px;
  --fbu-chip-radius:   4px;
  --fbu-gap-section:   24px;
  --fbu-gap-card:      32px;
}

body {
  background: var(--fbu-color-bg-primary);
  color: var(--fbu-color-text-primary);
  font-family: var(--fbu-font-family);
  font-size: var(--fbu-font-size-body);
  margin: 0;
}

/* 글로벌 다크 헤더 */
.fbu-header {
  height: var(--fbu-header-height);
  background: var(--fbu-color-bg-header);
  color: var(--fbu-color-text-on-dark);
  padding: 0 40px;
  display: flex;
  align-items: center;
  gap: 32px;
  position: sticky;
  top: 0;
  z-index: 100;
}

/* 카드 */
.fbu-card {
  background: var(--fbu-color-bg-card);
  border: 1px solid var(--fbu-color-border);
  border-radius: var(--fbu-card-radius);
  padding: 24px 32px;
}

/* KPI 거대 숫자 */
.fbu-kpi-display {
  font-size: var(--fbu-font-size-display);
  font-weight: var(--fbu-font-weight-bold);
  line-height: 1;
}

.fbu-kpi-title {
  font-size: var(--fbu-font-size-title);
  font-weight: var(--fbu-font-weight-bold);
}

/* 합의 배지 */
.fbu-consensus-badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 12px;
  border-radius: 999px;
  font-size: var(--fbu-font-size-small);
  font-weight: var(--fbu-font-weight-bold);
  color: white;
}
.fbu-consensus-badge--both-go           { background: var(--fbu-color-consensus-both-go); }
.fbu-consensus-badge--fpe-blocked       { background: var(--fbu-color-consensus-fpe-blocked); }
.fbu-consensus-badge--ape-only-positive { background: var(--fbu-color-consensus-ape-only-positive); }
.fbu-consensus-badge--ape-blocked       { background: var(--fbu-color-consensus-ape-blocked); }
.fbu-consensus-badge--both-review       { background: var(--fbu-color-consensus-both-review); }

/* 검색바 */
.fbu-searchbar {
  height: 44px;
  background: var(--fbu-color-bg-card);
  border: 1px solid var(--fbu-color-border);
  border-radius: var(--fbu-input-radius);
  padding: 0 16px;
  display: flex;
  align-items: center;
  gap: 16px;
}

/* 테이블 */
.fbu-table {
  width: 100%;
  background: var(--fbu-color-bg-card);
  border: 1px solid var(--fbu-color-border);
  border-radius: var(--fbu-card-radius);
  border-collapse: separate;
  border-spacing: 0;
}
.fbu-table tr {
  border-bottom: 1px solid var(--fbu-color-divider);
}
.fbu-table th, .fbu-table td {
  height: 44px;
  padding: 0 24px;
  text-align: left;
  font-size: var(--fbu-font-size-body);
}
```

### 3.2 마이그레이션 규약

| 기존 클래스 | v2 클래스 | 비고 |
|---|---|---|
| `.bz-page-header` | `.fbu-header` | 다크 헤더 |
| `.bz-card` | `.fbu-card` | 카드 컨테이너 |
| `.bz-score-large` | `.fbu-kpi-display` | 거대 점수 (예: "82") |
| `.bz-table` | `.fbu-table` | 테이블 |
| (신규) | `.fbu-consensus-badge` | 합의 배지 (3차 PR §3.3) |
| (신규) | `.fbu-searchbar` | 검색바 |

이중 운영 (transition): 기존 클래스 유지 + v2 클래스 추가 → 한 페이지씩 마이그레이션 → 모두 전환 완료 후 기존 클래스 제거.

## 4. 6 화면 + 엔진 관리 탭 — v2 디자인 매핑

### 4.1 `bizaipro_home.html` (대시보드)

```
┌─[fbu-header]──────────────────────────────────────────┐
│ FlowBizTool   홈   제안서   이메일   엔진 비교        │
└───────────────────────────────────────────────────────┘
┌─[큰 KPI 카드 — 양옆 분할]──────────────────────────────┐
│ 좌: FPE 카드                  │ 우: APE 카드          │
│  fbu-kpi-display "82"         │  fbu-kpi-display "85" │
│  진행도 bar                    │  진행도 bar           │
│  fbu-consensus-badge--both-go │  (참고) APE 비교 차이│
└───────────────────────────────┴────────────────────────┘
┌─[중형 KPI 2개 — FPE 단독 기준]────────────────────────┐
│ "5억원" (한도)         │ "2.4%" (마진)                │
└───────────────────────────────────────────────────────┘
┌─[상담보고서 family + SourceQuality]──────────────────┐
│ 기업리포트: 수집 완료  상담 family 13(전화 7/직접 6) │
└───────────────────────────────────────────────────────┘
┌─[검색바 + 필터 chip]─────────────────────────────────┐
└─[최근 평가 테이블 — fbu-table]────────────────────────┘
```

### 4.2 `bizaipro_evaluation_result.html`

```
┌─[fbu-header]────────────────────────────────────────────┐
┌─[좌: FPE 결과 (기준)]    │ ┌─[우: APE 비교 (참고)]──┐ │
│  fbu-kpi-display "82"    │ │ fbu-kpi-display "85"   │ │
│  knockout 사유 X         │ │ FPE 대비 +3 차이       │ │
│  consensus: both_go      │ │ 학습 후보 저장 여부    │ │
└──────────────────────────┴──┴───────────────────────┘ │
┌─[FPE 단독 기준값 — 5억/2.4%]────────────────────────────┐
└─[비교표 — fbu-table]────────────────────────────────────┐
│ 항목         │ FPE         │ APE         │ 차이        │
│ flow_score   │ 82          │ 85          │ +3          │
│ 한도         │ 5억         │ 4.8억       │ -0.2억      │
│ 마진율       │ 2.4%        │ 2.5%        │ +0.1%p      │
└─────────────────────────────────────────────────────────┘
```

> **§3.3 #1-#2 원칙**: 제안서/이메일에 들어가는 값은 **좌측 FPE 카드만**. 우측 APE는 표시만, 선택/적용 불가.

### 4.3 `bizaipro_proposal_generator.html` / `bizaipro_email_generator.html`

```
┌─[fbu-header]────────────────────────────────────────┐
┌─[FPE 기준 snapshot 표시 — fbu-card]──────────────────┐
│  flow_score 82 / 한도 5억 / 마진 2.4% / 결제 60일   │
│  fbu-consensus-badge--both-go                       │
└─────────────────────────────────────────────────────┘
┌─[제안서/이메일 폼]──────────────────────────────────┐
│ (FPE knockout 시 fieldset disabled + 차단 배너)     │
│  [차단] 본 영업건은 FPE 기준 미충족 — 제안서 생성   │
│  불가. 사유: 신용등급 CCC                           │
└─────────────────────────────────────────────────────┘
```

### 4.4 `bizaipro_engine_compare.html`

| FPE_v.16.01 | APE_v1.01 | 차이 |
|---|---|---|
| engine_purpose: fixed_screening | engine_purpose: **learning_comparison** | 역할 분리 |
| engine_locked: true | engine_locked: false | 운영 정책 |
| policy_source: 276holdings_limit_policy_manual | policy_source: bizaipro_learning_loop | 정책 출처 |

> 옵션 A 적용 후 **APE의 engine_purpose가 `learning_comparison`으로 노출**되는 것이 1차 PR 검증 핵심.

### 4.5 `bizaipro_changelog.html`

```
┌─[FPE 승격 이력]──────────────────────────────────────┐
│ 2026-04-30 13:00 KST  FPE_v.16.01 (관리자 승인)      │
│ 2026-03-30 13:00 KST  FPE_v.15.04 (자동 promote)     │
└──────────────────────────────────────────────────────┘
┌─[APE 학습 이력]──────────────────────────────────────┐
│ 2026-04-29  bizaipro_learning_registry +12 후보      │
│ 2026-04-28  Notion 수집 +18 케이스                    │
└──────────────────────────────────────────────────────┘
```

### 4.6 (신규) **엔진 관리 탭** — 월간 평가엔진고도화보고서

```
┌─[fbu-header — 엔진 관리]──────────────────────────────┐
┌─[월간 보고서 상태]───────────────────────────────────┐
│  pending      [3건]   2026-04-30 13:00 자동 생성      │
│  approved     [12건]  관리자 승인 후 promote 대기     │
│  promoted     [5건]   FPE 다음 버전에 반영 완료        │
└──────────────────────────────────────────────────────┘
┌─[보고서 목록 — fbu-table]────────────────────────────┐
│ 보고서 ID  │ 생성일      │ 상태       │ 액션          │
│ UR-04-30   │ 2026-04-30  │ pending    │ [승인][반려]  │
│ UR-03-30   │ 2026-03-30  │ promoted   │ [상세]        │
└──────────────────────────────────────────────────────┘
```

→ FBU-DUAL-LIFECYCLE-0001 §6 "엔진 관리 화면" 매트릭스 직결.

## 5. 5 Phase 로드맵

| Phase | 기간 | 산출물 |
|---|---|---|
| **Phase 1: 디자인 토큰 + standalone 보존** | **1주 (즉시 가능)** | `bizaipro_shared.css` 토큰 추가, `web/dual_engine_v2_standalone.html` 복사 |
| **Phase 2: 홈 + 결과 화면 마이그레이션** | 2주 | `bizaipro_home.html`, `bizaipro_evaluation_result.html` v2 디자인 적용 + FPE/APE 듀얼 카드 + 합의 배지 |
| **Phase 3: 제안서/이메일/비교/changelog** | 1주 | 4 화면 v2 디자인 + FPE 차단 배너 + disabled 폼 |
| **Phase 4: 엔진 관리 탭 신규** | 2주 | 월간 보고서 화면 + `/api/engine/upgrade/list` (FBU-DUAL-LIFECYCLE-0001 §8 직결) |
| **Phase 5: 픽셀 검증 + 회귀 테스트** | 1주 | standalone vs 실제 화면 비교 + a11y/대비 비율/AppleGothic 폰트 fallback 검증 |

총 **7주**.

### 5.1 본 1차 PR과의 관계

| 본 1차 PR | v2 디자인 PR |
|---|---|
| 인프라 + API + helper (UI 변경 없음) | 6 화면 + 엔진관리 탭 v2 디자인 적용 |
| `dual_eval_helpers.js` window 노출 | helper를 사용한 듀얼 카드 호출 |
| `engine_purpose: learning_comparison` 라이브 | 화면에서 노출 + 비교 카드 시각화 |
| 회귀 0건 | CSS 변경만으로 회귀 0건 유지 |

**본 1차 PR 머지 + 8011 활성화 → v2 디자인 Phase 1 시작 가능**.

## 6. 우선 순위 매트릭스

| 항목 | 즉시 (Phase 1) | 단기 (Phase 2-3) | 중기 (Phase 4-5) |
|---|:---:|:---:|:---:|
| 디자인 토큰 정의 | ✅ | — | — |
| standalone HTML 보존 | ✅ | — | — |
| AppleGothic font stack | ✅ | — | — |
| 다크 헤더 (`.fbu-header`) | ✅ | — | — |
| KPI 카드 (large/medium) | — | ✅ | — |
| 합의 배지 5색 | — | ✅ | — |
| FPE/APE 듀얼 카드 | — | ✅ | — |
| 상담 family + SourceQuality | — | ✅ | — |
| FPE 차단 배너 + disabled | — | ✅ | — |
| 검색바 + chip 필터 | — | ✅ | — |
| 비교표 (FPE vs APE) | — | ✅ | — |
| 엔진 관리 탭 (월간) | — | — | ✅ |
| 픽셀 검증 + a11y | — | — | ✅ |

## 7. 7항 원칙 매핑 (3차 PR §3.3)

| 원칙 | v2 디자인 매핑 |
|---|---|
| #1 제안서·이메일 기준값은 항상 FPE 고정 | 좌측 큰 KPI 카드(FPE)만 폼에 바인딩 |
| #2 APE 결과/합의 평균 선택 불가 | 우측 APE 카드는 표시 전용, 라디오/버튼 없음 |
| #3 APE는 비교/고도화 후보 전용 | 비교표 + "학습 후보 저장" 칩 |
| #4 상담보고서 family (전화/직접 subtype) | 상담 family 카운트 표시 영역 |
| #5 엔진관리 탭 (pending/approved/promoted) | §4.6 신규 엔진 관리 탭 |
| #6 AppleGothic font stack | `--fbu-font-family` (CSS 변수) |
| #7 SourceQuality 영역 | 홈/결과 화면 좌측 패널 |

→ **7항 모두 v2 디자인 토큰/레이아웃에 1:1 매핑됨**.

## 8. 데이터 바인딩 — 1차 PR API와 v2 디자인 결합

```javascript
// 홈/결과 화면 진입 시 듀얼 평가 호출 (v2 디자인 + 1차 PR API)
async function loadDualEvaluationToV2View(state) {
  const response = await fetch('/api/learning/evaluate/dual', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(state)
  });
  const data = await response.json();

  // 좌측 FPE 카드 (제안서/이메일 기준)
  document.querySelector('.fbu-kpi-display.is-fpe').textContent = data.screening.flow_score;
  document.querySelector('.fbu-card.is-fpe .fbu-kpi-title.is-credit-limit')
    .textContent = formatKRW(data.screening.credit_limit);

  // 우측 APE 카드 (비교 전용 — 절대 폼 바인딩 금지)
  document.querySelector('.fbu-kpi-display.is-ape').textContent = data.ape.flow_score;
  document.querySelector('.fbu-kpi-display.is-ape-diff').textContent = 
    formatDiff(data.ape.flow_score - data.screening.flow_score);

  // 합의 배지
  const consensus = data.agreement.consensus;
  const badge = document.querySelector('.fbu-consensus-badge');
  badge.className = 'fbu-consensus-badge fbu-consensus-badge--' + consensus.replace(/_/g, '-');
  badge.textContent = window.FlowBizDualEvalHelpers.CONSENSUS_LABELS[consensus].label;

  // FPE 차단 시 폼 disabled
  if (!data.fpe_gate_passed) {
    document.querySelector('form.proposal-form, form.email-form')
      ?.setAttribute('disabled', '');
    document.querySelector('.fbu-blocked-banner')
      ?.classList.remove('is-hidden');
  }
}
```

> **핵심**: `data.screening.*`만 폼에 바인딩, `data.ape.*`는 표시만. §3.3 #1-#2 원칙 코드 강제.

## 9. 검증 계획

### 9.1 Phase 1 (디자인 토큰) 검증

```bash
# 토큰 추가 후 6 HTML 회귀 0건 확인
python3 -m pytest tests/ -q
# → 100+ passed, 7 skipped 유지

# 브라우저 콘솔 — 토큰 정의 확인
getComputedStyle(document.documentElement).getPropertyValue('--fbu-color-bg-primary')
# → "#F5F4EE"
```

### 9.2 Phase 2-3 (화면 마이그레이션) 검증

| 검증 항목 | 도구 |
|---|---|
| 픽셀 비교 | standalone HTML 스크린샷 vs 실제 화면 (Playwright/Puppeteer) |
| 색약 친화도 | WebAIM contrast checker (#0F1115 on #F5F4EE = 16.5:1, AAA 통과) |
| AppleGothic fallback | Windows/Linux 환경 BlinkMacSystemFont fallback 확인 |
| 1차 PR API 통합 | `/api/learning/evaluate/dual` 응답이 v2 카드에 정확히 바인딩 |
| §3.3 #1-#2 강제 | 폼에 APE 값이 들어가지 않음 (E2E 테스트) |

### 9.3 Phase 4 (엔진 관리 탭) 검증

| 검증 항목 | 명령 |
|---|---|
| 월간 보고서 API | `curl /api/engine/upgrade/list` (Phase 4에서 신설) |
| 상태 전환 | pending → approved → promoted 워크플로우 E2E |
| 권한 분리 | 일반 사용자는 보기만, 관리자만 승인/반려 가능 |

## 10. Risk + Mitigation

| Risk | 영향 | 대응 |
|---|---|---|
| AppleGothic이 Windows/Linux에 없음 | 폰트 깨짐 | `BlinkMacSystemFont, sans-serif` fallback 명시 |
| 11MB standalone HTML로 git 비대화 | 저장소 부담 | git LFS 검토 또는 별도 outputs/ 폴더 보관 |
| v2 디자인의 픽셀이 1200×800 기준 | 모바일 미고려 | Phase 5에서 반응형 추가 |
| 기존 6 HTML에 v2 클래스 적용 시 충돌 | 회귀 발생 | 이중 운영 transition (기존 + v2 병기 → 점진 제거) |
| §3.3 #2 위반 (APE 폼 바인딩) | 정책 위반 | E2E 테스트 + lint rule (`grep ape-input form` 차단) |

## 11. 다음 액션 (사용자 결정)

| # | 액션 | 권장 시점 |
|---|---|:---:|
| 1 | 본 1차 PR 머지 (옵션 A 활성화) | **지금** (대기 중) |
| 2 | 8011 재시작 + `verify_dual_engine.sh` 통과 | 1 완료 후 |
| 3 | **Phase 1 시작** — `bizaipro_shared.css` 디자인 토큰 추가 + standalone HTML 보존 | 2 완료 후 |
| 4 | Phase 2 — 홈 + 결과 화면 v2 디자인 + 듀얼 카드 | 3 완료 후 |
| 5 | Phase 3 — 제안서/이메일/비교/changelog | 4 완료 후 |
| 6 | Phase 4 — 엔진 관리 탭 (월간 보고서) | 5 완료 후 |
| 7 | Phase 5 — 픽셀 검증 + a11y | 6 완료 후 |

---

## 부록 A. standalone HTML 자원 분석 가이드 (옵션 C 검토 시)

```bash
# bundler 형식 unpack 시도 (Node.js 환경)
node -e "
const html = require('fs').readFileSync('/Users/appler/Documents/COTEX/FlowBiz_ultra/FlowBizTool _ v2 _standalone.html', 'utf-8');
const m = html.match(/<script type=\"__bundler\\/manifest\">([\\s\\S]*?)<\\/script>/);
if (m) {
  const manifest = JSON.parse(m[1]);
  console.log('Assets:', Object.keys(manifest).length);
  for (const [uuid, entry] of Object.entries(manifest)) {
    console.log(uuid, entry.mime, entry.compressed ? 'gzip' : 'raw', entry.data.length, 'b64');
  }
}
"
```

> 본 계획의 옵션 A에서는 unpack 불필요. 옵션 C 검토 시점에 본 절차 사용.

## 부록 B. 디자인 토큰 동기화 도구 (Phase 5 자동화)

향후 standalone HTML이 갱신될 때 토큰을 자동 추출하는 스크립트:

```bash
# scripts/extract_v2_design_tokens.py (Phase 5 신설 예정)
python3 scripts/extract_v2_design_tokens.py \
  --input "FlowBizTool _ v2 _standalone.html" \
  --output web/bizaipro_v2_tokens.css
```

manifest의 SVG/CSS에서 `fill`, `stroke`, `font-size` 값을 자동 추출 → CSS 변수로 변환.

## 부록 C. 변경 위치 사전 인덱스

| 파일 | Phase 1 | Phase 2-3 | Phase 4 |
|---|:---:|:---:|:---:|
| `web/bizaipro_shared.css` | ✅ 토큰 추가 | ✅ 클래스 정의 | — |
| `web/dual_engine_v2_standalone.html` | ✅ 신규 (참고용) | — | — |
| `web/bizaipro_home.html` | — | ✅ v2 마이그레이션 | — |
| `web/bizaipro_evaluation_result.html` | — | ✅ | — |
| `web/bizaipro_proposal_generator.html` | — | ✅ | — |
| `web/bizaipro_email_generator.html` | — | ✅ | — |
| `web/bizaipro_engine_compare.html` | — | ✅ | — |
| `web/bizaipro_changelog.html` | — | ✅ | — |
| `web/bizaipro_engine_management.html` | — | — | ✅ 신규 |
| `web/bizaipro_shared.js` | — | ✅ `loadDualEvaluationToV2View()` | ✅ 월간 API 호출 |
| `app.py` | — | — | ✅ `/api/engine/upgrade/list` 신규 |

## 부록 D. 누적 계획 매트릭스

| 계획 | 본 계획과의 관계 |
|---|---|
| `[claude]flowbiz_dual_engine_pr_merge_activation_guide_v2_7_20260430.md` | 본 계획의 **선행 조건** (1차 PR 머지) |
| `flowbiz_dual_engine_evaluation_and_upgrade_lifecycle_plan_20260430.md` | 본 계획 §4.6 엔진 관리 탭의 데이터 모델 출처 |
| `flowbiz_dual_engine_ui_sample_validation_direction_20260430.md` | 본 계획 §3.3 #1-#7 원칙의 출처 (P0/P1 정정) |
| `flowbiztool_v2_standalone_based_production_plan_20260430.md` | 본 계획의 **상위 production 청사진** |
| `flowbiz_monthly_evaluation_engine_upgrade_plan_20260430.md` | Phase 4 엔진 관리 탭의 백엔드 사이클 |
