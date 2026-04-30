# [codex] FlowBiz v2 Preview + PR Guide 재검증 보고서

- 문서번호: FBU-VAL-UIV2-RECHECK-20260501
- 작성일: 2026-05-01
- 검증 대상:
  - `scripts/compare_v2_preview_vs_standalone.js`
  - `web/v2_preview.html`
  - `web/styles/v2_components.css`
  - `docs/reference/v2_preview_comparison_summary_20260501.md`
  - `docs/[claude]flowbiz_dual_engine_pr_merge_activation_guide_v2_7_20260430.md`
- 검증 명령:
  - `node scripts/compare_v2_preview_vs_standalone.js`

## 1. 결론

이전 6개 Finding 중 5개는 현재 구현에서 해소된 것으로 확인했습니다.

다만 `docs/reference/v2_preview_comparison_summary_20260501.md`는 아직 이전 768px tablet 기준과 산출물 파일명을 유지하고 있어, D5 PR 분리 전 문서 갱신이 필요합니다.

## 2. Finding별 재검증

| # | 기존 Finding | 상태 | 근거 |
|---|---|:---:|---|
| 1 | 반응형 검증 수치가 desktop만 반영됨 | 해소 | 스크립트가 viewport별 `matchRate`, `matches`, `totalCmp`를 저장하고 보고서 표에 desktop/tablet/mobile 결과를 출력함 |
| 2 | 768px tablet 설명과 실제 CSS 동작 불일치 | 부분 해소 | 실행 스크립트와 generated report는 tablet을 820px로 변경했으나, `docs/reference/v2_preview_comparison_summary_20260501.md`는 아직 768px/5열→3열로 남음 |
| 3 | 모바일 390px 가로 오버플로우 | 해소 | `.fbu-*` box-sizing reset 추가, 비교 스크립트 overflow assertion 결과 mobile `scroll 390 <= viewport 390` |
| 4 | visible copy의 100% 정합 표현 과장 | 해소 | `web/v2_preview.html` 문구가 `핵심 10개 computed style 기준 100% 정합`으로 축소됨 |
| 5 | preflight grep 변수 대입이 clean 상태에서 실패 가능 | 해소 | v2.7 Preflight A가 `grep` 변수 대입을 제거하고 `git status --porcelain | awk` 기반으로 변경됨 |
| 6 | stash 복구가 `stash@{0}`에 의존 | 해소 | v2.7 복구 명령이 `git stash list | awk -F: '/pre-option-A/ {print $1; exit}'`로 stash id를 검색함 |

## 3. 실행 검증 결과

`node scripts/compare_v2_preview_vs_standalone.js` 실행 결과:

| Viewport | 결과 | Overflow |
|---|---:|---:|
| desktop 1200x900 | 100% (10/10) | ok, scroll 1200 = viewport 1200 |
| tablet 820x1180 | 100% (10/10) | ok, scroll 820 = viewport 820 |
| mobile 390x844 | 100% (10/10) | ok, scroll 390 = viewport 390 |

생성된 비교 보고서 `outputs/reference/comparison/v2_preview_comparison_report.md`는 820px tablet 기준을 정상 반영합니다.

## 4. 잔여 Finding

### Finding 1 [P2] reference summary 문서가 이전 viewport 기준을 유지

`docs/reference/v2_preview_comparison_summary_20260501.md`는 여전히 tablet을 `768 x 1024`, 산출물 파일을 `standalone_tablet.png (768x1024)`로 기록합니다. 현재 실행 스크립트와 generated report는 tablet을 `820 x 1180`으로 검증하므로, PR 추적용 요약 문서가 실제 검증 결과와 불일치합니다.

권장 수정:

- tablet 행을 `820 x 1180`으로 변경
- 설명을 `5열 -> 3열 reflow`로 유지하되 820px 기준이라고 명시
- 산출물 목록의 tablet 파일 설명도 `820x1180`으로 갱신

## 5. Go / No-Go

조건부 Go입니다.

코드와 실행 검증 기준으로는 D5 진행이 가능해졌습니다. 다만 PR에 포함되는 `docs/reference/v2_preview_comparison_summary_20260501.md`가 아직 stale이므로, 이 문서만 갱신한 뒤 D5 산출물 commit + PR 분리를 진행하는 것이 안전합니다.

