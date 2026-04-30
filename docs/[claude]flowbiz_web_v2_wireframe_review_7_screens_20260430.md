# 웹 v2 디자인 — 7 화면 와이어프레임 검토 [claude]

- 문서번호: FBU-WF-V2-7-SCREENS-20260430
- 작성일: 2026-04-30
- 작성자: [claude]
- 디자인 토큰: `web/styles/v2_tokens.css` (작업 2 산출물)
- 디자인 시안: `web/dual_engine_v2_standalone.html` (작업 1 산출물 — 11MB standalone)
- 상위 계획:
  - `[claude]flowbiz_web_full_redesign_v2_plan_20260430.md` (재작업 6 Phase)
  - `[claude]flowbiz_ui_v2_standalone_design_implementation_plan_20260430.md` (디자인 토큰 추출)
- 결론: 7 화면(home / evaluation_result / proposal / email / engine_compare / changelog / engine_management) **와이어프레임 + 컴포넌트 명세 + 7항 원칙 매핑 + 데이터 바인딩 매핑**까지 단일 문서로 정리. Phase 3 진입 시 본 문서를 그대로 구현 명세로 사용.

## 0. 공통 요소

### 0.1 글로벌 헤더 (모든 화면 공통)

```
┌──────────────────────────────────────────────────────────────────────────┐
│ [DARK HEADER #0F1115, height 56px, padding-x 40px]                       │
│                                                                          │
│  FlowBizTool        홈    평가결과    제안서    이메일    엔진비교       │
│  (logo, white)     (현재 페이지는 underline + bold)      changelog       │
│                                                                  엔진관리 │
└──────────────────────────────────────────────────────────────────────────┘
```

- 폰트: `--fbu-font-family` (AppleGothic)
- 로고: `font-size 16px / weight 700`, 색 `--fbu-color-text-on-dark` (베이지)
- nav: `font-size 14px / weight 400`, 활성 페이지만 `weight 700 + underline`
- z-index: `--fbu-z-sticky` (100), position sticky

### 0.2 본문 컨테이너

- `max-width: 1200px` (--fbu-container-max-width)
- `padding: 40px` (--fbu-container-padding-x)
- 배경: `--fbu-color-bg-primary` (베이지)

### 0.3 카드 스타일

- 배경: `--fbu-color-bg-card` (흰색)
- 테두리: `1px solid --fbu-color-border` (밝은 베이지)
- radius: `--fbu-radius-lg` (8px)
- padding: `--fbu-space-8` (32px) 외측 / `--fbu-space-6` (24px) 내측

### 0.4 합의 배지 (5색 — 모든 결과 화면 공통)

| consensus | 배경 | 텍스트 | 의미 |
|---|---|---|---|
| both_go | `--fbu-color-consensus-both-go` (#2E7D32 green) | 흰색 | 양쪽 통과 |
| fpe_blocked | `--fbu-color-consensus-fpe-blocked` (#C62828 red) | 흰색 | FPE 차단 |
| ape_only_positive | `--fbu-color-consensus-ape-only-positive` (#F57C00 orange) | 흰색 | APE만 통과 |
| ape_blocked | `--fbu-color-consensus-ape-blocked` (#5E35B1 purple) | 흰색 | v3 정책 대기 |
| both_review | `--fbu-color-consensus-both-review` (#757575 grey) | 흰색 | 양쪽 보류 |

```
┌─────────────────┐
│ ● 양쪽 통과     │  height 24px, padding-x 12px, radius 9999px (--fbu-radius-full)
└─────────────────┘
```

## 1. `bizaipro_home.html` (대시보드)

### 1.1 와이어프레임

```
┌────────────────────────────────────────────────────────────────────────────┐
│ [GLOBAL HEADER]                                                            │
└────────────────────────────────────────────────────────────────────────────┘
┌────────────────────────────────────────────────────────────────────────────┐
│  [Hero Card — KPI Large 520x280]    [KPI Medium A 568x132]                 │
│  ┌─────────────────────────────┐   ┌──────────────────────────────────┐   │
│  │  통합 평가 — 합의 결과        │   │  거래 한도 (FPE 기준)             │   │
│  │                             │   │                                  │   │
│  │  82  ━━━━━━━━━━ 67%         │   │  5억원                            │   │
│  │ (display 84px, weight 700)  │   │  (title 36px, weight 700)        │   │
│  │                             │   │                                  │   │
│  │  ┌──────────┐ ┌──────────┐  │   │  플랜이 제안할 때 사용할 단일      │   │
│  │  │FPE: 82   │ │APE: 85   │  │   │  진실 소스                        │   │
│  │  └──────────┘ └─(+3)─────┘  │   └──────────────────────────────────┘   │
│  │                             │   ┌──────────────────────────────────┐   │
│  │  ● 양쪽 통과 (both_go)      │   │  마진율 (FPE 기준)                │   │
│  └─────────────────────────────┘   │                                  │   │
│                                    │  2.4%                             │   │
│                                    │  결제유예 60일                    │   │
│                                    └──────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────────┘
┌────────────────────────────────────────────────────────────────────────────┐
│  [SourceQuality + 상담 family]                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │  Source Quality                                                      │ │
│  │  ● 기업리포트 — 수집 완료     ● 심사보고서 — 5건 (품질 통과)          │ │
│  │  ● 상담 family — 13건 (전화 7건 / 직접 6건)                          │ │
│  │  ● 평가 반영 상태: FPE ✓  APE 학습 후보 +3                           │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────────┘
┌────────────────────────────────────────────────────────────────────────────┐
│  [검색바 + chip 필터 (height 44px)]                                        │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │  🔍 기업명 / 사업자번호 검색...    [활성 12]  [pending 3]  [반려 2] │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────────┘
┌────────────────────────────────────────────────────────────────────────────┐
│  [최근 평가 테이블 — fbu-table]                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │ ID    │ 기업명         │ 평가일       │ FPE │ APE │ 합의      │ 액션 │ │
│  ├──────────────────────────────────────────────────────────────────────┤ │
│  │ #023  │ ABC산업㈜      │ 2026-04-30  │ 82  │ 85  │ ● both_go │ 보기 │ │
│  │ #022  │ XYZ제조㈜      │ 2026-04-29  │ 45  │ 50  │ ● blocked │ 보기 │ │
│  │ #021  │ 한솥㈜         │ 2026-04-28  │ 78  │ 82  │ ● both_go │ 보기 │ │
│  │ ...                                                                  │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 컴포넌트 명세

| ID | 컴포넌트 | CSS 클래스 | 데이터 출처 |
|---|---|---|---|
| H1 | Hero Card | `.fbu-card .fbu-card--kpi-large` | `/api/dashboard` 최근 1건 |
| H2 | KPI Large 숫자 | `.fbu-kpi-display` | `agreement.consensus_score` |
| H3 | Progress bar | `.fbu-progress` | `flow_score / 100` |
| H4 | FPE/APE 비교 sub card | `.fbu-card--sub-pair` | `screening.flow_score`, `ape.flow_score` |
| H5 | 합의 배지 | `.fbu-consensus-badge--<consensus>` | `agreement.consensus` |
| M1 | KPI Medium A — 한도 | `.fbu-card--kpi-medium` | `screening.credit_limit` (**FPE 단독**) |
| M2 | KPI Medium B — 마진 | `.fbu-card--kpi-medium` | `screening.margin_rate` (**FPE 단독**) |
| S1 | Source Quality 영역 | `.fbu-source-quality` | `state.input_quality` |
| F1 | 검색바 | `.fbu-searchbar` | (URL query string) |
| F2 | chip 필터 | `.fbu-chip` | (필터 상태) |
| T1 | 테이블 | `.fbu-table` | `/api/learning/cases?limit=20` |

### 1.3 §3.3 7항 원칙 적용

| 원칙 | 위치 |
|---|---|
| #1 FPE 고정 | M1, M2 — 한도/마진율은 **FPE 단독 기준**만 표시 |
| #2 APE 선택 불가 | H4 우측 APE sub card — 시각만 표시, 클릭/선택 동작 없음 |
| #3 APE 비교 전용 | H4의 "+3" 차이 표시 = 비교 정보 |
| #4 상담 family | S1 "상담 family — 13건 (전화 7 / 직접 6)" |
| #5 엔진관리 탭 | 헤더 nav에서 진입 |
| #6 AppleGothic | 본문 전체 `--fbu-font-family` |
| #7 SourceQuality | S1 영역 (4 항목 표시) |

### 1.4 데이터 바인딩 의사 코드

```javascript
async function initHomeView() {
  // 듀얼 평가 호출
  const dual = await fetch('/api/learning/evaluate/dual', {
    method: 'POST',
    body: JSON.stringify(getCurrentState())
  }).then(r => r.json());

  // H2: 합의 점수
  document.querySelector('.fbu-kpi-display.is-agreement').textContent =
    Math.round((dual.screening.flow_score + dual.ape.flow_score) / 2);

  // H4: FPE/APE 비교
  document.querySelector('.is-fpe .fbu-kpi-sub').textContent = dual.screening.flow_score;
  document.querySelector('.is-ape .fbu-kpi-sub').textContent = dual.ape.flow_score;
  const diff = dual.ape.flow_score - dual.screening.flow_score;
  document.querySelector('.is-ape .fbu-kpi-diff').textContent =
    (diff >= 0 ? '+' : '') + diff;

  // H5: 합의 배지
  const consensus = dual.agreement.consensus;
  const badge = document.querySelector('.fbu-consensus-badge');
  badge.className =
    'fbu-consensus-badge fbu-consensus-badge--' + consensus.replace(/_/g, '-');
  badge.textContent =
    window.FlowBizDualEvalHelpers.CONSENSUS_LABELS[consensus].label;

  // M1, M2: FPE 단독 — APE 값 절대 사용 금지 (§3.3 #1)
  document.querySelector('.is-credit-limit .fbu-kpi-title').textContent =
    formatKRW(dual.screening.credit_limit);
  document.querySelector('.is-margin-rate .fbu-kpi-title').textContent =
    (dual.screening.margin_rate * 100).toFixed(1) + '%';

  // S1: SourceQuality
  renderSourceQuality(dual.state.input_quality);
}
```

## 2. `bizaipro_evaluation_result.html`

### 2.1 와이어프레임

```
┌────────────────────────────────────────────────────────────────────────────┐
│ [GLOBAL HEADER]                                                            │
└────────────────────────────────────────────────────────────────────────────┘
┌────────────────────────────────────────────────────────────────────────────┐
│  ABC산업㈜ — 평가결과 (2026-04-30 14:23 KST)                                │
│                                                                            │
│  ┌─[좌: FPE 카드 (기준)]──────┐  ┌─[우: APE 카드 (비교 전용)]─────┐         │
│  │ FPE_v.16.01 ⚓ locked      │  │ APE_v1.01 (learning)          │         │
│  │                            │  │ (opacity 0.85)                │         │
│  │  82                        │  │  85                            │         │
│  │  (display 84px)            │  │  (display 84px, secondary)    │         │
│  │                            │  │                                │         │
│  │  knockout: 없음             │  │  FPE 대비 +3                  │         │
│  │  policy_source:            │  │  policy_source:               │         │
│  │  276holdings_limit_policy  │  │  bizaipro_learning_loop       │         │
│  │                            │  │                                │         │
│  │  ● 양쪽 통과                │  │  학습 후보 저장됨 ✓            │         │
│  └────────────────────────────┘  └────────────────────────────────┘         │
└────────────────────────────────────────────────────────────────────────────┘
┌────────────────────────────────────────────────────────────────────────────┐
│  [FPE 단독 기준값 — 제안서/이메일에서 사용]                                 │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │  한도 5억원 │ 마진율 2.4% │ 결제유예 60일 │ 납품진행 가능              │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────────┘
┌────────────────────────────────────────────────────────────────────────────┐
│  [비교표 — fbu-table]                                                      │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │ 항목         │ FPE (기준)  │ APE (참고)  │ 차이      │ 사용 위치     │ │
│  ├──────────────────────────────────────────────────────────────────────┤ │
│  │ flow_score   │ 82          │ 85          │ +3        │ —             │ │
│  │ 한도         │ 5억원        │ 4.8억원     │ -0.2억    │ 제안서·이메일 │ │
│  │ 마진율       │ 2.4%         │ 2.5%        │ +0.1%p    │ 제안서·이메일 │ │
│  │ 결제유예     │ 60일         │ 65일        │ +5일      │ 제안서·이메일 │ │
│  │ 납품진행     │ 가능         │ 가능        │ 동일      │ 제안서        │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────────┘
┌────────────────────────────────────────────────────────────────────────────┐
│  [액션 버튼]                                                               │
│  [제안서 생성하기 →] (FPE 기준)   [이메일 작성 →] (FPE 기준)               │
└────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 §3.3 7항 적용

| 원칙 | 위치 |
|---|---|
| #1 FPE 고정 | "FPE 단독 기준값" 카드 + 비교표 "사용 위치" 컬럼 명시 |
| #2 APE 선택 불가 | 우측 APE 카드는 opacity 0.85 + 시각만, 액션 버튼 없음 |
| #3 APE 비교 전용 | 비교표 + "학습 후보 저장됨 ✓" 칩 |

### 2.3 핵심 시각 강조

- **좌 FPE 카드는 명도 100%, 우 APE 카드는 opacity 0.85** → 위계 시각화
- 비교표 "사용 위치" 컬럼에서 APE 행은 항상 "—" (사용 안 함 표시)
- 하단 액션 버튼은 "FPE 기준" 라벨 명시

## 3. `bizaipro_proposal_generator.html`

### 3.1 와이어프레임 — 정상 케이스 (FPE 통과)

```
┌────────────────────────────────────────────────────────────────────────────┐
│ [GLOBAL HEADER]                                                            │
└────────────────────────────────────────────────────────────────────────────┘
┌────────────────────────────────────────────────────────────────────────────┐
│  제안서 생성 — ABC산업㈜                                                    │
│                                                                            │
│  [FPE snapshot 카드 — 제안서 기준값 잠금 표시]                              │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │  FPE_v.16.01 기준 ⚓ (제안서·이메일에 동일하게 사용됨)                 │ │
│  │  한도 5억원 │ 마진 2.4% │ 결제유예 60일 │ ● 양쪽 통과                  │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────────┘
┌────────────────────────────────────────────────────────────────────────────┐
│  [제안서 폼]                                                               │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │  회사명         [ABC산업㈜              ]                              │ │
│  │  대표자         [김대표                ]                              │ │
│  │                                                                      │ │
│  │  제안 한도      [5억원                 ] 🔒 (FPE 자동 — 수정 불가)    │ │
│  │  마진율         [2.4%                  ] 🔒                          │ │
│  │  결제유예       [60일                  ] 🔒                          │ │
│  │                                                                      │ │
│  │  제안 사유                                                            │ │
│  │  [_________________________________________________________________] │ │
│  │  [_________________________________________________________________] │ │
│  │                                                                      │ │
│  │                                       [임시저장]  [제안서 생성 →]    │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 와이어프레임 — 차단 케이스 (FPE 미통과)

```
┌────────────────────────────────────────────────────────────────────────────┐
│  [차단 배너 — fbu-blocked-banner #C62828]                                  │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │  ⚠️  본 영업건은 FPE 기준 미충족 — 제안서 생성 불가                    │ │
│  │                                                                      │ │
│  │  사유:                                                                │ │
│  │   • 신용등급 CCC (D 이하 자동 차단)                                   │ │
│  │   • 매출 감소 추세 (최근 3분기 연속)                                  │ │
│  │                                                                      │ │
│  │  필요 조치:                                                           │ │
│  │   • 신용등급 개선 또는 보증 제공                                      │ │
│  │   • 추가 심사 요청 시 [관리자에게 문의 →]                            │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────────┘
┌────────────────────────────────────────────────────────────────────────────┐
│  [제안서 폼 — disabled]                                                    │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │  (모든 input fieldset disabled, opacity 0.5)                         │ │
│  │  회사명         [ABC산업㈜              ] (회색)                      │ │
│  │  ...                                                                  │ │
│  │                                       [임시저장] (활성)               │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────────┘
```

### 3.3 데이터 바인딩 핵심

```javascript
async function initProposalView() {
  const dual = await window.FlowBizDualEvalHelpers.evaluateDualFromState(
    getCurrentState()
  );

  if (!dual.fpe_gate_passed) {
    // 차단 배너 표시
    document.querySelector('.fbu-blocked-banner').classList.remove('is-hidden');
    document.querySelector('.fbu-blocked-reasons').innerHTML =
      dual.screening.knockout_reasons.map(r => `<li>${r}</li>`).join('');

    // 폼 disabled
    document.querySelector('form.proposal-form').setAttribute('disabled', '');
    return;
  }

  // FPE 값 자동 채움 (§3.3 #1)
  document.querySelector('input[name="credit_limit"]').value =
    formatKRW(dual.screening.credit_limit);
  document.querySelector('input[name="margin_rate"]').value =
    (dual.screening.margin_rate * 100).toFixed(1) + '%';
  document.querySelector('input[name="payment_grace"]').value =
    dual.screening.payment_grace_days + '일';

  // 🔒 readonly + visual lock
  ['credit_limit', 'margin_rate', 'payment_grace'].forEach(name => {
    document.querySelector(`input[name="${name}"]`)
      .setAttribute('readonly', '');
  });
}
```

### 3.4 §3.3 7항 적용

- #1 FPE 고정: 한도/마진/결제유예 input은 **FPE 값으로만 채워짐 + readonly**
- #2 APE 선택 불가: APE 값을 표시하는 영역 **자체가 없음**

## 4. `bizaipro_email_generator.html`

§3과 동일 구조 + 이메일 본문 영역 추가:

```
┌────────────────────────────────────────────────────────────────────────────┐
│  [FPE snapshot 카드] (§3과 동일)                                           │
└────────────────────────────────────────────────────────────────────────────┘
┌────────────────────────────────────────────────────────────────────────────┐
│  [이메일 본문 폼]                                                          │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │  받는 사람     [purchasing@abc.co.kr   ]                              │ │
│  │  제목         [[FlowPay] 거래 한도 안내 — 5억원 / 2.4%]               │ │
│  │                                                                      │ │
│  │  본문                                                                 │ │
│  │  [_________________________________________________________________] │ │
│  │  [안녕하세요, ABC산업㈜ 김대표님.                                    │ │
│  │  [FlowPay 평가 결과를 안내드립니다.                                  │ │
│  │  [- 거래 한도: 5억원   ← FPE 자동 채움                              │ │
│  │  [- 마진율: 2.4%       ← FPE 자동 채움                              │ │
│  │  [- 결제유예: 60일      ← FPE 자동 채움                              │ │
│  │  [_________________________________________________________________] │ │
│  │                                                                      │ │
│  │                                       [임시저장]  [이메일 발송 →]    │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────────┘
```

차단 케이스: §3.2와 동일.

## 5. `bizaipro_engine_compare.html`

### 5.1 와이어프레임

```
┌────────────────────────────────────────────────────────────────────────────┐
│ [GLOBAL HEADER]                                                            │
└────────────────────────────────────────────────────────────────────────────┘
┌────────────────────────────────────────────────────────────────────────────┐
│  엔진 비교 — FPE vs APE                                                     │
│                                                                            │
│  ┌─[FPE 카드]──────────────────┐  ┌─[APE 카드]────────────────────┐         │
│  │ engine_id: FPE              │  │ engine_id: APE                │         │
│  │ engine_label: FPE_v.16.01   │  │ engine_label: APE_v1.01       │         │
│  │ engine_locked: ⚓ true       │  │ engine_locked: 🔓 false       │         │
│  │ engine_purpose:             │  │ engine_purpose:               │         │
│  │   fixed_screening           │  │   learning_comparison ★       │         │
│  │ policy_source:              │  │ policy_source:                │         │
│  │   276holdings_limit_        │  │   bizaipro_learning_loop      │         │
│  │   policy_manual             │  │                                │         │
│  │                             │  │  (★ 옵션 A 정정 — v2.7 §13)   │         │
│  └─────────────────────────────┘  └────────────────────────────────┘         │
└────────────────────────────────────────────────────────────────────────────┘
┌────────────────────────────────────────────────────────────────────────────┐
│  [버전 차이 비교 — fbu-table]                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │ 항목                  │ FPE_v.16.00      │ FPE_v.16.01      │ 변경 사유 │ │
│  ├──────────────────────────────────────────────────────────────────────┤ │
│  │ flow_score 가중치 a   │ 0.45              │ 0.42              │ 학습     │ │
│  │ 한도 multiplier       │ 1.20              │ 1.18              │ 보수화   │ │
│  │ knockout 룰 추가      │ 8개               │ 9개               │ +CCC차단 │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────────┘
┌────────────────────────────────────────────────────────────────────────────┐
│  [APE 학습 통계]                                                           │
│  최근 30일 학습 케이스: 47건                                                │
│  FPE 대비 +3 이상 차이: 12건 (25.5%)                                       │
│  FPE 대비 -3 이하 차이: 5건 (10.6%)                                        │
│  FPE 대비 동일 (±2):    30건 (63.8%)                                       │
└────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 핵심 강조 — `learning_comparison` 노출

이 화면은 **옵션 A 적용 효과를 사용자에게 시각화하는 핵심 화면**.
- API `/api/engine/list` 응답을 직접 표시
- `engine_purpose: learning_comparison` (오렌지 highlight)

```javascript
async function initEngineCompareView() {
  const engines = await fetch('/api/engine/list').then(r => r.json());
  const ape = engines.engines.find(e => e.engine_id === 'APE');

  // engine_purpose가 learning_comparison인지 확인
  if (ape.engine_purpose !== 'learning_comparison') {
    console.warn('[engine_compare] APE engine_purpose 정정 미적용:', ape.engine_purpose);
  }

  document.querySelector('.is-ape .engine-purpose').textContent = ape.engine_purpose;
  // 'learning_comparison'이면 오렌지 highlight class 추가
  if (ape.engine_purpose === 'learning_comparison') {
    document.querySelector('.is-ape .engine-purpose').classList.add('is-highlight');
  }
}
```

## 6. `bizaipro_changelog.html`

### 6.1 와이어프레임

```
┌────────────────────────────────────────────────────────────────────────────┐
│ [GLOBAL HEADER]                                                            │
└────────────────────────────────────────────────────────────────────────────┘
┌────────────────────────────────────────────────────────────────────────────┐
│  Changelog — 엔진 / 학습 / 월간 보고서 이력                                  │
│                                                                            │
│  [탭]  [전체]  [FPE 승격]  [APE 학습]  [월간 보고서]                        │
└────────────────────────────────────────────────────────────────────────────┘
┌────────────────────────────────────────────────────────────────────────────┐
│  [FPE 승격 이력 — fbu-table]                                               │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │ 일시                │ 버전           │ 승격 방식    │ 보고서 ID       │ │
│  ├──────────────────────────────────────────────────────────────────────┤ │
│  │ 2026-04-30 13:00 KST│ FPE_v.16.01    │ 관리자 승인  │ UR-04-30        │ │
│  │ 2026-03-30 13:00 KST│ FPE_v.15.04    │ 자동 promote │ UR-03-30        │ │
│  │ 2026-02-29 13:00 KST│ FPE_v.15.03    │ 관리자 승인  │ UR-02-29        │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────────┘
┌────────────────────────────────────────────────────────────────────────────┐
│  [APE 학습 이력 — fbu-table]                                               │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │ 일시        │ 이벤트                                │ 영향 케이스    │ │
│  ├──────────────────────────────────────────────────────────────────────┤ │
│  │ 2026-04-29  │ bizaipro_learning_registry +12 후보   │ ABC, XYZ, ...  │ │
│  │ 2026-04-28  │ Notion 수집 +18 케이스                 │ —              │ │
│  │ 2026-04-27  │ APE_v1.01 framework 갱신               │ 전체 신규 평가 │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────────┘
┌────────────────────────────────────────────────────────────────────────────┐
│  [월간 평가엔진고도화보고서 이력]                                           │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │ 보고서 ID │ 생성일      │ 상태       │ 후보 수 │ 액션              │ │
│  ├──────────────────────────────────────────────────────────────────────┤ │
│  │ UR-04-30  │ 2026-04-30  │ ● promoted │ 12      │ [상세 →]          │ │
│  │ UR-03-30  │ 2026-03-30  │ ● promoted │ 8       │ [상세 →]          │ │
│  │ UR-02-29  │ 2026-02-29  │ ● rejected │ 5       │ [상세 →]          │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────────┘
```

### 6.2 §3.3 7항 적용

- #5 엔진관리: 월간 보고서 이력 표시 (관리자 화면 제외 시 사용자도 가시)
- 상태 컬러: pending(오렌지) / approved(블루) / promoted(그린) / rejected(레드) — `--fbu-color-status-*`

## 7. `bizaipro_engine_management.html` (신규)

### 7.1 와이어프레임 — 관리자 진입 시

```
┌────────────────────────────────────────────────────────────────────────────┐
│ [GLOBAL HEADER]                                                            │
└────────────────────────────────────────────────────────────────────────────┘
┌────────────────────────────────────────────────────────────────────────────┐
│  엔진 관리 — 관리자 워크플로우                                               │
│                                                                            │
│  [현재 운영 정보]                                                           │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │  현재 active FPE: FPE_v.16.01 (locked ⚓)                             │ │
│  │  현재 active APE: APE_v1.01 (learning 🔓)                             │ │
│  │  마지막 자동 보고서 생성: 2026-04-30 13:00 KST                         │ │
│  │  다음 자동 보고서 생성: 2026-05-30 13:00 KST                           │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────────┘
┌────────────────────────────────────────────────────────────────────────────┐
│  [상태 카드 ×4]                                                            │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐               │
│  │ ● pending  │ │ ● approved │ │ ● promoted │ │ ● rejected │               │
│  │     3      │ │    12      │ │     5      │ │     2      │               │
│  │ 검토 대기  │ │ 승인됨     │ │ 반영 완료  │ │ 반려       │               │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘               │
└────────────────────────────────────────────────────────────────────────────┘
┌────────────────────────────────────────────────────────────────────────────┐
│  [pending 보고서 상세 — 검토 대기 액션 포함]                                │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │ UR-04-30 — 2026-04-30 13:00 KST 자동 생성                             │ │
│  │  ─────────────────────────────────────────────────────────────       │ │
│  │  변경 후보 (12건):                                                    │ │
│  │   1. flow_score 가중치 a: 0.45 → 0.42 (학습 47건, 신뢰도 0.82)        │ │
│  │   2. 한도 multiplier: 1.20 → 1.18 (학습 47건, 신뢰도 0.78)            │ │
│  │   3. knockout +CCC차단 (Notion 12건 입증)                             │ │
│  │   ... (9개 더)                                                        │ │
│  │                                                                       │ │
│  │  영향 분석:                                                           │ │
│  │   • 기존 FPE_v.16.00 vs 후보 FPE_v.16.01 비교: 회귀 0건               │ │
│  │   • 한도 변경 합계: -2.3억원 (보수화 방향)                            │ │
│  │   • 마진율 변경 합계: +0.3%p (수익성 개선)                            │ │
│  │                                                                       │ │
│  │  ┌────────────────┐  ┌──────────────┐  ┌────────────────┐            │ │
│  │  │ ✓ 승인 (promote)│ │ 반려 (reject)│ │ 보류 (hold)    │            │ │
│  │  └────────────────┘  └──────────────┘  └────────────────┘            │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────────┘
┌────────────────────────────────────────────────────────────────────────────┐
│  [전체 보고서 목록 — fbu-table]                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │ 보고서 ID │ 생성일      │ 상태       │ 후보 │ 영향          │ 액션  │ │
│  ├──────────────────────────────────────────────────────────────────────┤ │
│  │ UR-04-30  │ 2026-04-30  │ ● pending  │ 12   │ -2.3억 / +0.3%│ [검토]│ │
│  │ UR-03-30  │ 2026-03-30  │ ● promoted │ 8    │ -1.8억 / +0.2%│ [상세]│ │
│  │ UR-02-29  │ 2026-02-29  │ ● rejected │ 5    │ +5.2억 / -0.5%│ [상세]│ │
│  └──────────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────────┘
```

### 7.2 일반 사용자 진입 시 (권한 분리)

```
┌────────────────────────────────────────────────────────────────────────────┐
│  엔진 관리 — 운영 정보 (읽기 전용)                                          │
│                                                                            │
│  [현재 운영 정보] (위와 동일)                                               │
│  [상태 카드 ×4] (위와 동일 — 읽기만)                                        │
│  [전체 보고서 목록] (액션 컬럼 = "[상세 →]"만)                              │
│                                                                            │
│  💡 변경 권한이 필요하면 관리자에게 문의                                     │
└────────────────────────────────────────────────────────────────────────────┘
```

### 7.3 §3.3 7항 적용

| 원칙 | 위치 |
|---|---|
| #5 엔진관리 탭 | **본 화면 자체** — 월간 보고서 + pending/approved/promoted 상태 |

### 7.4 데이터 바인딩 — 신규 API 필요

```javascript
async function initEngineManagementView() {
  // Phase 4에서 신설 예정
  const reports = await fetch('/api/engine/upgrade/list').then(r => r.json());

  // 상태별 카운트
  const counts = reports.reduce((acc, r) => {
    acc[r.status] = (acc[r.status] || 0) + 1;
    return acc;
  }, {});

  document.querySelector('.is-pending .count').textContent = counts.pending || 0;
  document.querySelector('.is-approved .count').textContent = counts.approved || 0;
  document.querySelector('.is-promoted .count').textContent = counts.promoted || 0;
  document.querySelector('.is-rejected .count').textContent = counts.rejected || 0;

  // pending 상세 (관리자만)
  if (isAdmin()) {
    const pending = reports.filter(r => r.status === 'pending');
    renderPendingDetail(pending[0]);
  }
}

async function approveReport(reportId) {
  const response = await fetch(`/api/engine/upgrade/${reportId}/promote`, {
    method: 'POST',
    headers: { 'X-Admin-Token': getAdminToken() }
  });
  // → FPE_v.16.02 자동 빌드 + active_framework.json 갱신
}
```

## 8. 7 화면 요약 매트릭스

| # | 화면 | 핵심 컴포넌트 | API 의존 | §3.3 적용 |
|---|---|---|---|---|
| 1 | home | Hero KPI + FPE/APE 비교 + SourceQuality + 검색 + 테이블 | `/api/dashboard`, `/api/learning/cases`, `/api/learning/evaluate/dual` | #1 #2 #3 #4 #6 #7 |
| 2 | evaluation_result | 좌(FPE) / 우(APE) 듀얼 카드 + 비교표 | `/api/evaluate/dual` | #1 #2 #3 |
| 3 | proposal_generator | FPE snapshot + 차단 배너 + 폼 | `/api/learning/evaluate/dual` | #1 #2 |
| 4 | email_generator | FPE snapshot + 본문 폼 | `/api/learning/evaluate/dual` | #1 #2 |
| 5 | engine_compare | 엔진 META 비교 + 버전 차이 | `/api/engine/list` | #2 #3 |
| 6 | changelog | FPE 승격 + APE 학습 + 월간 이력 | `/api/engine/changelog` (Phase 4) | #5 |
| 7 | engine_management (신규) | pending/approved/promoted + promote 액션 | `/api/engine/upgrade/list`, `.../promote` (Phase 4) | #5 |

## 9. 컴포넌트 라이브러리 (Phase 2 신설 예정)

`web/styles/v2_components.css`에 다음 컴포넌트 클래스 정의:

| 클래스 | 용도 | 7 화면 사용 |
|---|---|---|
| `.fbu-header` | 글로벌 다크 헤더 | 1-7 |
| `.fbu-card` | 기본 카드 | 1-7 |
| `.fbu-card--kpi-large` | 큰 KPI 카드 (520x280) | 1, 2 |
| `.fbu-card--kpi-medium` | 중형 KPI 카드 (568x132) | 1 |
| `.fbu-card--engine-fpe` | FPE 카드 (강조) | 2, 5 |
| `.fbu-card--engine-ape` | APE 카드 (opacity 0.85) | 2, 5 |
| `.fbu-kpi-display` | 84px 거대 숫자 | 1, 2 |
| `.fbu-kpi-title` | 36px 중형 숫자 | 1 |
| `.fbu-kpi-sub` | 작은 숫자 (sub card 내부) | 1, 2 |
| `.fbu-progress` | progress bar | 1 |
| `.fbu-consensus-badge` | 합의 배지 5색 | 1-4 |
| `.fbu-source-quality` | SourceQuality 영역 | 1 |
| `.fbu-source-item` | source 항목 (4개) | 1 |
| `.fbu-searchbar` | 검색바 | 1 |
| `.fbu-chip` | 필터 칩 | 1 |
| `.fbu-table` | 테이블 | 1, 2, 5, 6, 7 |
| `.fbu-blocked-banner` | 차단 배너 (#C62828) | 3, 4 |
| `.fbu-button` | 일반 버튼 | 2-7 |
| `.fbu-button--primary` | primary 버튼 (검정 bg) | 2-7 |
| `.fbu-status-card` | 상태 카드 (pending/approved/...) | 7 |
| `.fbu-tab` | 탭 컴포넌트 | 6 |
| `.fbu-input` | input 필드 | 3, 4 |
| `.fbu-input--readonly` | 🔒 readonly input | 3, 4 |

총 **22개 컴포넌트 클래스**.

## 10. 검증 체크리스트 (Phase 3 진입 전)

- [ ] 7 화면 와이어프레임 사용자 검토 완료
- [ ] §3.3 7항 원칙 1:1 매핑 확정
- [ ] 데이터 바인딩 의사코드 백엔드 응답과 일치 확인
- [ ] 컴포넌트 22개 목록 확정
- [ ] AppleGothic font stack 환경별 fallback 검증
- [ ] dual_eval_helpers.js의 `CONSENSUS_LABELS` 5종 확인
- [ ] `/api/engine/list` 응답에 `learning_comparison` 노출 확인 (1차 PR 머지 후)
- [ ] Phase 4 신설 API (`/api/engine/upgrade/*`) 명세 초안 작성

## 11. 다음 단계

```
[지금] 본 와이어프레임 검토 완료 + 사용자 confirm
   ↓
[1차 PR 머지 후] Phase 1: legacy 이동 + 폴더 구조
   ↓
[Phase 2] v2_components.css 작성 (22개 컴포넌트)
   ↓
[Phase 3] 7 화면 HTML 재작성 (본 와이어프레임을 그대로 구현 명세로 사용)
   ↓
[Phase 4] engine_management.html + 월간 API 신설
   ↓
[Phase 5] 픽셀 검증 + a11y + AppleGothic fallback
```

---

## 부록 A. 본 문서와 다른 계획서의 관계

| 계획서 | 본 문서와의 관계 |
|---|---|
| `[claude]flowbiz_web_full_redesign_v2_plan_20260430.md` | **상위 6 Phase 로드맵** — 본 문서는 Phase 3의 구현 명세 |
| `[claude]flowbiz_ui_v2_standalone_design_implementation_plan_20260430.md` | 디자인 토큰 출처 + 옵션 A/B/C 비교 |
| `[claude]flowbiz_dual_engine_pr_merge_activation_guide_v2_7_20260430.md` | 1차 PR 활성화 (선행 조건) |
| `flowbiz_dual_engine_evaluation_and_upgrade_lifecycle_plan_20260430.md` | 7 화면의 데이터 모델 출처 |
| `flowbiz_dual_engine_ui_sample_validation_direction_20260430.md` | §3.3 7항 원칙 출처 (P0/P1 정정) |

## 부록 B. 컴포넌트 클래스 → 화면 매트릭스 (반대 방향)

| 화면 | 사용 컴포넌트 클래스 |
|---|---|
| home | header, card, card--kpi-large, card--kpi-medium, kpi-display, kpi-title, kpi-sub, progress, consensus-badge, source-quality, source-item, searchbar, chip, table |
| evaluation_result | header, card, card--engine-fpe, card--engine-ape, kpi-display, consensus-badge, table, button, button--primary |
| proposal_generator | header, card, consensus-badge, blocked-banner, input, input--readonly, button, button--primary |
| email_generator | header, card, consensus-badge, blocked-banner, input, input--readonly, button, button--primary |
| engine_compare | header, card, card--engine-fpe, card--engine-ape, table |
| changelog | header, card, tab, table |
| engine_management | header, card, status-card (4개), table, button, button--primary |

## 부록 C. 7항 원칙 → 화면 적용 매트릭스 (반대 방향)

| 원칙 | 적용 화면 |
|---|---|
| #1 FPE 고정 | home (M1, M2), evaluation_result (단독 기준값 카드), proposal (input readonly), email (input readonly) |
| #2 APE 선택 불가 | home (H4 우측 시각만), evaluation_result (우측 카드 액션 없음), proposal/email (APE 영역 자체 없음) |
| #3 APE 비교 전용 | home (H4 "+3"), evaluation_result (비교표 + "학습 후보 저장됨"), engine_compare (학습 통계) |
| #4 상담 family | home (S1 "상담 family — 13건 (전화 7 / 직접 6)") |
| #5 엔진관리 탭 | changelog (월간 이력), engine_management (pending/approved/promoted/rejected 상태) |
| #6 AppleGothic | 7 화면 모두 (--fbu-font-family) |
| #7 SourceQuality | home (S1 4 항목 표시) |

→ **7항 모두 7 화면에 분산 적용, 빠진 항목 없음**.
