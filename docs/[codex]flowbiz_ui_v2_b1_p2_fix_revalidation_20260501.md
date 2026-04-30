# [codex] FlowBizTool v2 B1 P2 수정 재검증 보고서

- 작성일: 2026-05-01
- 대상:
  - `scripts/compare_v2_preview_vs_standalone.js`
  - `web/v2_preview.html`
  - `web/styles/v2_components.css`
  - `docs/reference/v2_preview_comparison_summary_20260501.md`
- 이전 검증: `docs/[codex]flowbiz_ui_v2_b1_preview_validation_20260501.md`

## 1. 검증 결론

이전 P2 두 건은 일부 반영되었다.

반영된 점:

1. 비교 스크립트에 3개 viewport가 추가되었다.
2. 생성 보고서가 "핵심 10개 computed style 기준"이라고 범위를 명시한다.
3. `web/v2_preview.html`의 viewport meta가 `width=device-width, initial-scale=1`로 변경되었다.
4. `web/styles/v2_components.css`에 1024px/768px 미디어쿼리가 추가되었다.
5. `docs/reference/v2_preview_comparison_summary_20260501.md`가 추가되어 `outputs/` 미추적 문제를 보완한다.

하지만 아직 실행 승인 전 보완이 필요하다. 현재 상태에서는 "3 P2 모두 처리 완료"라고 보기 어렵다.

## 2. 재실행 결과

실행 명령:

```bash
node scripts/compare_v2_preview_vs_standalone.js
```

결과:

```text
=== 데스크톱 (1200×900) ===
  └ screenshot: standalone_desktop.png
  └ screenshot: v2_preview_desktop.png

=== 태블릿 (iPad) (768×1024) ===
  └ screenshot: standalone_tablet.png
  └ screenshot: v2_preview_tablet.png

=== 모바일 (iPhone 14 Pro) (390×844) ===
  └ screenshot: standalone_mobile.png
  └ screenshot: v2_preview_mobile.png

일치율: 100% (10/10)
Standalone bg:    #F9FAFB
v2_preview bg:    #F9FAFB
Standalone card:  #FFFFFF radius=12px
v2_preview card:  #FFFFFF radius=12px
Standalone hdr:   #FFFFFF h=60px
v2_preview hdr:   #FFFFFF h=60px
```

스크립트 실행 자체는 성공했다.

## 3. Findings

### Finding 1 [P1] 768px 태블릿 설명이 실제 CSS와 불일치

`docs/reference/v2_preview_comparison_summary_20260501.md`는 768×1024 태블릿에서 "5열→3열 reflow"라고 기록한다. 그러나 CSS는 `@media (max-width: 768px)`에서 모든 grid를 1열로 바꾼다. 실제 측정 결과도 768px에서 `.fbu-grid--cols-2`가 `736px` 단일 컬럼으로 계산되었다.

검증 데이터:

```text
tablet 768:
gridTemplateColumns: "736px"
navOverflowX: "auto"
```

해결 방향:

- 태블릿 검증 viewport를 820px 또는 834px로 바꾸어 1024px 이하 태블릿 룰만 검증하거나,
- 768px을 모바일 경계로 보고 문서의 "5열→3열" 설명을 "1열 reflow"로 수정한다.

### Finding 2 [P1] 반응형 검증은 스크린샷 생성에 가깝고, tablet/mobile 토큰 비교는 자동 판정하지 않음

`scripts/compare_v2_preview_vs_standalone.js`는 3개 viewport 스크린샷을 생성하지만, 최종 `matches/totalCmp` 계산은 `allViewportResults[0]`, 즉 desktop 결과만 사용한다. 그런데 `docs/reference/v2_preview_comparison_summary_20260501.md`는 desktop/tablet/mobile 모두 "토큰 100%"라고 적고 있다.

현재 검증 범위:

- desktop 10개 computed style: 자동 비교
- tablet/mobile: 스크린샷 생성
- tablet/mobile 토큰 일치율: 보고서 표에는 없음
- tablet/mobile 레이아웃 정상 여부: 자동 assertion 없음

해결 방향:

- viewport별 `comparisons`와 `matchRate`를 모두 계산하여 보고서에 `desktop/tablet/mobile` 각각의 10개 항목 결과를 출력한다.
- 최소한 `document.documentElement.scrollWidth <= viewport.width` 같은 horizontal overflow assertion을 추가한다.

### Finding 3 [P1] 모바일에서 페이지 수평 오버플로우가 남아 있음

390px viewport에서 `document.body.scrollWidth`와 `document.documentElement.scrollWidth`가 400px로 측정되었다. 즉 모바일에서 10px 수평 스크롤이 생긴다.

실측:

```text
mobile 390:
bodyScrollWidth: 400
docScrollWidth: 400
viewport: 390
```

주요 원인 후보:

- `.fbu-input { width: 100%; padding: 0 12px; border: 1px ... }`에 `box-sizing: border-box`가 없어 입력 필드가 부모보다 넓어진다.
- 모바일 테이블 내부 셀이 table 박스 밖으로 넘친다.
- nav 자체는 `overflow-x:auto`로 처리됐지만, anchor 요소의 overflow가 검증에서 함께 잡힌다.

해결 방향:

```css
.fbu-input,
.fbu-button,
.fbu-card,
.fbu-table,
.fbu-searchbar {
  box-sizing: border-box;
}

.fbu-table {
  max-width: 100%;
}

@media (max-width: 768px) {
  .fbu-main {
    overflow-x: hidden;
  }
}
```

다만 `overflow-x:hidden`은 근본 수정 후 보조 안전장치로만 쓰는 것이 좋다.

### Finding 4 [P2] 미리보기 화면 내 문구가 아직 과함

`web/v2_preview.html`의 화면 문구에는 아직 `rendered DOM 100% 정합`이라고 표시된다. 비교 스크립트와 보고서는 범위를 좁혔지만, 사용자가 직접 보는 페이지에는 여전히 전체 정합처럼 읽히는 표현이 남아 있다.

수정 권장:

```text
현재: rendered DOM 100% 정합
권장: 핵심 10개 computed style 기준 100% 정합
```

## 4. 이전 Findings 처리 상태

| 이전 Finding | 현재 상태 | 판정 |
|---|---|---|
| 100% 검증 범위가 10개 스타일 항목으로 한정됨 | 스크립트/보고서는 범위 명시. 미리보기 화면 문구는 잔존 | 부분 종료 |
| 미리보기는 1200px 데스크톱 기준 | 3 viewport 스크린샷 추가. 단 tablet/mobile 자동 판정 부족 + 모바일 overflow 발견 | 부분 종료 |

## 5. Go/No-Go

현재 상태는 **D3 PR 분리 전 보완 필요**다.

차단 수준의 P0는 없지만, D3는 "작은 검증 PR"로 남겨야 하므로 다음 3가지는 먼저 정리하는 편이 안전하다.

1. `web/v2_preview.html` 문구를 "핵심 10개 computed style 기준 100%"로 수정
2. 768px 문서 설명을 실제 CSS와 맞추거나 viewport를 820/834px로 조정
3. 모바일 수평 오버플로우 제거 후 `scrollWidth <= viewport.width` 검증 추가

## 6. 최종 판정

재검증 결과, P2 수정 방향은 맞지만 아직 "완료"로 보기에는 이르다. 특히 모바일 수평 오버플로우는 운영 화면 마이그레이션 전에 반드시 닫아야 한다.
