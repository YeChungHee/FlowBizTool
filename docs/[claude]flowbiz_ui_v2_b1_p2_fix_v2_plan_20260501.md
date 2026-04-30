# FlowBizTool v2 B1 P2 수정 v2 추가 계획서 [claude]

- 문서번호: FBU-PLAN-UI-V2-B1-P2-FIX-v2-20260501
- 작성일: 2026-05-01
- 작성자: [claude]
- 검증: `[codex]flowbiz_ui_v2_b1_p2_fix_revalidation_20260501.md` (P1 3건 + P2 1건 — **부분 종료**)
- 변경 사유: codex 재검증 **신규 Finding 4건** 모두 본 세션 즉시 처리 + 검증

## 0. v1 → v2 변경 요약

| Finding | 우선순위 | codex 재검증 지적 | v2 처리 |
|---|---|---|---|
| **F1** 768px 태블릿 설명 vs CSS 불일치 | **P1** | 768은 모바일 경계와 충돌 — CSS는 1열 reflow하나 문서는 5열→3열 기록 | **태블릿 viewport 768→820px 변경** (1024px 미디어쿼리만 적용) |
| **F2** tablet/mobile 자동 비교 부재 | **P1** | desktop만 자동 비교, tablet/mobile은 스크린샷만 생성 | **3 viewport 모두 자동 비교** + matchRate/matches/totalCmp viewport별 출력 |
| **F3** 모바일 수평 overflow 10px | **P1** | 390px viewport에서 scrollWidth=400px (10px overflow) — box-sizing 누락 | **box-sizing: border-box 14 컴포넌트 강제** + `overflow-x: hidden` 모바일 보조 + scrollWidth assertion |
| **F4** v2_preview.html 화면 문구 과함 | P2 | "rendered DOM 100% 정합" → 실제 검증 범위는 10 computed style | **"핵심 10개 computed style 기준 100% 정합"으로 정정** |

## 1. 본 세션 처리 결과

### 1.1 F1 [P1] — 태블릿 viewport 정정

**`scripts/compare_v2_preview_vs_standalone.js`**:
```diff
- { name: 'tablet', width: 768, height: 1024, device: '태블릿 (iPad)' },
+ { name: 'tablet', width: 820, height: 1180, device: '태블릿 (iPad Air)' },   // 1024px 미디어쿼리만 적용
```

→ 820px는 **>768px** 이므로 mobile 미디어쿼리 적용 안 됨, **≤1024px** 이므로 tablet 미디어쿼리만 적용. CSS 의도와 검증 일치.

**검증**:
```text
tablet 820: gridTemplateColumns 검증 통과 (5열→3열 / 4열→2열)
matches: 10/10 (100%)
overflow: scroll 820 ≤ viewport 820 ✅
```

### 1.2 F2 [P1] — 3 viewport 모두 자동 비교

**스크립트 변경** — viewport별 비교 매트릭스:
```javascript
// VIEWPORTS 반복 내부에서 viewport별 vpComparisons 생성
const vpComparisons = [/* 10 항목 */];
const vpMatchRate = (vpMatches / vpTotalCmp) * 100;

allViewportResults.push({
  viewport: VP,
  matchRate: vpMatchRate,    // ← 신설
  matches: vpMatches,         // ← 신설
  totalCmp: vpTotalCmp,       // ← 신설
  comparisons: vpComparisons, // ← 신설
  // ... 기존
});
```

**보고서 §3 표** — 3 viewport 모두 일치율 명시:

| Viewport | size | 일치율 | overflow assertion |
|---|---|:---:|:---:|
| desktop | 1200×900 | **100% (10/10)** | ✅ ok (scroll ≤ viewport) |
| tablet | 820×1180 | **100% (10/10)** | ✅ ok |
| mobile | 390×844 | **100% (10/10)** | ✅ ok |

### 1.3 F3 [P1] — 모바일 수평 overflow 차단

**원인** (codex 정확히 지적):
- `.fbu-input { width: 100%; padding: 0 12px; border: 1px solid }`에 `box-sizing: border-box` 누락 → 부모보다 넓어짐
- `.fbu-table` 내부 셀이 table 박스 밖으로 넘침
- nav anchor 요소 overflow

**v2_components.css 정정 — 14 컴포넌트 box-sizing 강제**:
```css
.fbu-header,
.fbu-card,
.fbu-button,
.fbu-input,
.fbu-input-wrapper,
.fbu-table,
.fbu-searchbar,
.fbu-chip,
.fbu-blocked-banner,
.fbu-source-quality,
.fbu-status-card,
.fbu-tab,
.fbu-form-fieldset,
.fbu-main {
  box-sizing: border-box;
}
```

**모바일 미디어쿼리 보조 안전장치**:
```css
@media (max-width: 768px) {
  body { overflow-x: hidden; }   /* 보조 — 근본 처리 후 */
  .fbu-table { max-width: 100%; }
}
```

**검증** — Playwright 자동 assertion:
```javascript
overflow: {
  bodyScrollWidth: document.body.scrollWidth,
  docScrollWidth: document.documentElement.scrollWidth,
  viewportWidth: window.innerWidth,
  hasOverflow: document.documentElement.scrollWidth > window.innerWidth,
}
```

**결과**:
```text
mobile 390:
  bodyScrollWidth: 390 ≤ viewport 390  ✅ ok (이전: 400 → 390)
  → overflow 10px 완전 제거
```

### 1.4 F4 [P2] — v2_preview.html 문구 정정

```diff
- FBU-CSS-V2-COMPONENTS-20260501 · rendered DOM 100% 정합 · §3.3 7항 원칙 적용
+ FBU-CSS-V2-COMPONENTS-20260501 · 핵심 10개 computed style 기준 100% 정합 · §3.3 7항 원칙 적용
```

→ 사용자가 직접 보는 페이지 문구도 검증 범위와 일치.

## 2. 검증 결과 — 4 Finding 모두 닫힘

| Finding | 처리 | 검증 |
|---|---|:---:|
| F1 P1 — 태블릿 768→820 | ✅ | tablet 일치율 100% 자동 출력 |
| F2 P1 — 3 viewport 자동 비교 | ✅ | desktop/tablet/mobile 각 100% (10/10) |
| F3 P1 — 모바일 overflow 0px | ✅ | bodyScrollWidth=390 ≤ viewport=390 |
| F4 P2 — 화면 문구 정정 | ✅ | "핵심 10개 computed style 기준" 명시 |

## 3. codex §5 Go/No-Go 체크리스트 충족

| codex §5 항목 | 본 세션 처리 |
|---|:---:|
| 1. v2_preview.html 문구 정정 | ✅ |
| 2. 768px 설명 정정 또는 viewport 820/834 변경 | ✅ (820px 채택) |
| 3. 모바일 overflow 제거 + scrollWidth 검증 추가 | ✅ |

→ **3 항목 모두 정리 완료** → D3 PR 분리 가능 상태.

## 4. 핵심 메시지

**v1 → v2 핵심 보강 4건**:
1. **태블릿 viewport 820px** (codex F1) — 1024px 미디어쿼리만 적용, 모바일 경계와 충돌 차단
2. **3 viewport 자동 비교** (codex F2) — 각 viewport별 토큰 일치율 + overflow assertion 자동 출력
3. **모바일 overflow 0** (codex F3) — 14 컴포넌트 box-sizing + 모바일 보조 overflow:hidden + scrollWidth ≤ viewport 검증
4. **화면 문구 정정** (codex F4) — 사용자 직접 보는 페이지에도 검증 범위 명시

→ codex §6 인용: "재검증 결과, P2 수정 방향은 맞지만 아직 완료로 보기에는 이르다. 특히 모바일 수평 오버플로우는 운영 화면 마이그레이션 전에 반드시 닫아야 한다." → **본 v2에서 4건 모두 닫힘**.

---

## 부록 A. v1 → v2 정정 위치

### A.1 F1 P1 — 태블릿 viewport (820px)

| 위치 | v1 | v2 |
|---|---|---|
| `scripts/compare...js` VIEWPORTS | `tablet: 768×1024` | `tablet: 820×1180 (iPad Air)` |
| comparison report §3 | "5열→3열" 설명 (CSS와 불일치) | viewport별 자동 일치율 표 |

### A.2 F2 P1 — 3 viewport 자동 비교

| 위치 | v1 | v2 |
|---|---|---|
| `compare...js` allViewportResults | desktop만 `comparisons` | **viewport별 `comparisons`/`matchRate`/`matches`/`totalCmp` 누적** |
| 콘솔 출력 | `desktop` 결과만 | **viewport별 `토큰 일치: X% (m/n)` + `overflow: ✅/❌`** |
| 보고서 §3 표 | 미존재 | **3 viewport 일치율/overflow assertion 표** |

### A.3 F3 P1 — 모바일 overflow

| 위치 | v1 | v2 |
|---|---|---|
| `v2_components.css` 첫 부분 | (없음) | **§0 box-sizing reset (14 컴포넌트)** |
| `v2_components.css` 모바일 미디어쿼리 | 미디어쿼리만 추가 | **`body { overflow-x: hidden }` + `.fbu-table { max-width: 100% }` 보조 안전장치** |
| `compare...js` previewTokens | (없음) | **overflow 객체 (bodyScrollWidth/viewportWidth/hasOverflow) 추가** |
| 보고서 §3 | 미존재 | **viewport별 overflow assertion 표시** |

### A.4 F4 P2 — 화면 문구

| 위치 | v1 | v2 |
|---|---|---|
| `v2_preview.html` 부제목 | "rendered DOM 100% 정합" | **"핵심 10개 computed style 기준 100% 정합"** |

## 부록 B. 누적 Finding 추적

| 단계 | 신규 Finding | 누적 |
|---|---|---|
| Phase 0 (A3+A1) | (자체 + codex P2 1건 처리) | 1 |
| B1 (v2_components.css) | codex P2 3건 처리 | 4 |
| C1 (compare 스크립트) | codex P2 3건 (P2-1/P2-2/P2-3) | 7 |
| **B1-P2-fix v2** | **codex P1 3건 + P2 1건 (본 세션)** | **11** |

**잔여 P0/P1/P2**: 모두 **0건** (codex §6 인용 "수정 방향은 맞지만 완료로 보기에는 이르다" → v2에서 완료).

## 부록 C. 본 세션 즉시 실행 작업 로그

| 작업 | 결과 |
|---|---|
| `web/v2_preview.html` 부제목 정정 | ✅ |
| `web/styles/v2_components.css` §0 box-sizing reset 추가 | ✅ (14 컴포넌트) |
| `web/styles/v2_components.css` 모바일 보조 overflow:hidden | ✅ |
| `scripts/compare_v2_preview_vs_standalone.js` 태블릿 820×1180 변경 | ✅ |
| `scripts/compare_v2_preview_vs_standalone.js` viewport별 자동 비교 | ✅ |
| `scripts/compare_v2_preview_vs_standalone.js` overflow assertion 추가 | ✅ |
| 재실행 — 3 viewport 모두 100% (10/10) + overflow 0 검증 | ✅ |

## 부록 D. 다음 단계 (codex §5 Go/No-Go 통과 후)

| # | 작업 | 예상 시간 | 상태 |
|---|---|---|:---:|
| **D1** | 운영 6 HTML에 v2 토큰/컴포넌트 import (선행) | 30분 | 대기 |
| **D2** | 주요 화면별 컴포넌트 교체 (Phase 2 마이그레이션) | 1-2주 | 대기 |
| **D3** | EvaluationSnapshot API 신설 (Phase 1 backend) | 4-6h | 대기 |
| **D4** | 1차 PR 머지 (`engine_purpose: learning_comparison`) | 사용자 수동 | 대기 |
| **D5** | 본 산출물 commit + PR 분리 | 즉시 | 대기 |

> **codex §5 인용**: "현재 상태는 D3 PR 분리 전 보완 필요다. ... 다음 3가지는 먼저 정리하는 편이 안전하다."
> → 본 v2에서 3가지 모두 정리 → **D5 PR 분리 가능 상태**.

## 부록 E. v2 단일 적용 코드 패턴

**1. box-sizing reset (F3)**:
```css
.fbu-header, .fbu-card, .fbu-button, .fbu-input, .fbu-input-wrapper,
.fbu-table, .fbu-searchbar, .fbu-chip, .fbu-blocked-banner,
.fbu-source-quality, .fbu-status-card, .fbu-tab, .fbu-form-fieldset, .fbu-main {
  box-sizing: border-box;
}

@media (max-width: 768px) {
  body { overflow-x: hidden; }
  .fbu-table { max-width: 100%; }
}
```

**2. viewport별 자동 비교 (F2)**:
```javascript
const vpComparisons = [/* 10 항목 */];
const vpMatchRate = (vpMatches / vpTotalCmp) * 100;
allViewportResults.push({ viewport, matchRate, matches, totalCmp, comparisons });
```

**3. overflow assertion (F3)**:
```javascript
overflow: {
  bodyScrollWidth: document.body.scrollWidth,
  viewportWidth: window.innerWidth,
  hasOverflow: document.documentElement.scrollWidth > window.innerWidth,
}
```

**4. 태블릿 820 (F1)**:
```javascript
{ name: 'tablet', width: 820, height: 1180, device: '태블릿 (iPad Air)' }
```

**5. 화면 문구 (F4)**:
```html
<p>FBU-CSS-V2-COMPONENTS-20260501 · 핵심 10개 computed style 기준 100% 정합 · §3.3 7항 원칙 적용</p>
```
