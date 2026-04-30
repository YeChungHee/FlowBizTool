# [codex] FlowBizTool v2 Phase 0 토큰 추출/재정의 검증 보고서

- 작성일: 2026-05-01
- 대상: `scripts/extract_v2_tokens_rendered.js`, `web/styles/v2_tokens.css`, `outputs/reference/*`
- 기준 문서: `docs/[claude]flowbiz_ui_v2_standalone_design_implementation_plan_v7_20260430.md`
- 기준 디자인: `docs/reference/dual_engine_v2_standalone.html`

## 1. 검증 결론

Phase 0의 A3(렌더링 기반 토큰 추출)와 A1(`v2_tokens.css` 전면 재정의)은 현재 파일 기준으로 구현 완료로 판단한다.

핵심 토큰 수는 131개로 확인되었고, 별도 비교 스크립트로 body, card, primary color, status color, typography, header, radius 기준 15개 항목을 재검증한 결과 15/15 일치했다.

단, 현재 상태는 디자인 토큰 기반 완성 단계이며 기존 운영 HTML에는 아직 `web/styles/v2_tokens.css`가 연결되어 있지 않다. 따라서 다음 단계는 토큰을 실제 UI 컴포넌트로 연결하는 B1이 가장 적합하다.

## 2. 확인한 산출물

| 구분 | 경로 | 확인 결과 |
|---|---|---|
| 렌더링 추출 스크립트 | `scripts/extract_v2_tokens_rendered.js` | 존재, Playwright 기반 재실행 성공 |
| 기준 HTML | `docs/reference/dual_engine_v2_standalone.html` | 존재 |
| 추출 JSON | `outputs/reference/v2_tokens_rendered.json` | 재생성 성공 |
| 추출 CSS reference | `outputs/reference/v2_tokens_rendered.css` | 재생성 성공 |
| 분석 보고서 | `outputs/reference/v2_tokens_analysis_report.md` | 재생성 성공 |
| 운영 토큰 | `web/styles/v2_tokens.css` | 131개 CSS 변수 확인 |
| E2E 기반 | `package.json`, `playwright.config.ts`, `tests/run_e2e.sh` | v6 지적 사항 반영 확인 |

## 3. 재실행 결과

실행 명령:

```bash
npm run extract:tokens
```

결과:

```text
[OK] JSON: outputs/reference/v2_tokens_rendered.json
[OK] CSS: outputs/reference/v2_tokens_rendered.css
[OK] Report: outputs/reference/v2_tokens_analysis_report.md

Body bg:        #F9FAFB
Body color:     #191F28
Body font:      Pretendard, "Spoqa Han Sans Neo", -apple-system, "system-ui"...
전체 element:    338
Top 3 bg:       #FFFFFF, #2D54D6, #1FA45D
Top 3 text:     #191F28, #333D4B, #4E5968
Top 3 fontsize: 24px, 22px, 18px
KPI Display:    24px #FFFFFF
```

## 4. 15개 핵심 토큰 대조

| 항목 | CSS 토큰 | 실제 값 | 기대 값 | 결과 |
|---|---|---:|---:|:---:|
| body bg | `--fbu-color-bg-primary` | `#F9FAFB` | `#F9FAFB` | PASS |
| body color | `--fbu-color-text-primary` | `#191F28` | `#191F28` | PASS |
| card bg | `--fbu-color-bg-card` | `#FFFFFF` | `#FFFFFF` | PASS |
| card border | `--fbu-color-border` | `#E5E8EB` | `#E5E8EB` | PASS |
| primary action | `--fbu-color-primary` | `#2D54D6` | `#2D54D6` | PASS |
| success | `--fbu-color-success` | `#1FA45D` | `#1FA45D` | PASS |
| error | `--fbu-color-error` | `#E42939` | `#E42939` | PASS |
| warning | `--fbu-color-warning` | `#FAAD14` | `#FAAD14` | PASS |
| body font-size | `--fbu-font-size-base` | `16px` | `16px` | PASS |
| KPI display size | `--fbu-font-size-display` | `24px` | `24px` | PASS |
| header height | `--fbu-header-height` | `60px` | `60px` | PASS |
| header padding | `--fbu-header-padding-x` | `24px` | `24px` | PASS |
| card radius | `--fbu-radius-xl` | `12px` | `12px` | PASS |
| button radius | `--fbu-radius-lg` | `10px` | `10px` | PASS |
| pill radius | `--fbu-radius-full` | `999px` | `999px` | PASS |

결과: 15/15 통과.

## 5. 반영 완료로 보는 항목

1. 베이지 톤, 검정 헤더, 84px KPI 가정은 폐기되었다.
2. 흰색-회색 톤, 흰색 헤더, 24px KPI, Toss/Pretendard 계열 토큰이 실제 rendered DOM 기준으로 반영되었다.
3. `--fbu-color-status-on-hold`가 유지되어 월간 엔진 업데이트 상태 토큰 누락 문제도 닫혔다.
4. `tests/run_e2e.sh`는 `sleep 3` 대신 readiness retry loop를 사용한다.
5. `test:e2e:ui`는 `bash tests/run_e2e.sh --ui`를 통해 서버 기동 경로를 공유한다.

## 6. 잔여 확인 사항

### P2. generated reference 산출물은 git 추적 대상이 아니다

`.gitignore`가 `outputs/` 전체를 제외하므로 `outputs/reference/v2_tokens_rendered.json`, `outputs/reference/v2_tokens_rendered.css`, `outputs/reference/v2_tokens_analysis_report.md`는 PR에 포함되지 않는다. 재현 가능한 generated artifact로 운영할 수는 있지만, 리뷰 증거를 PR에 남기려면 핵심 요약을 `docs/reference/` 또는 별도 `[codex]` 보고서에 보관해야 한다.

### P2. AGENTS 기본 폰트 정책과 v2 rendered 토큰의 예외를 문서화해야 한다

프로젝트 기본 지침은 AppleGothic이지만, 이번 v2 standalone 기준 디자인은 실제 rendered DOM에서 Pretendard가 1순위다. 이번 토큰 선택은 기준 HTML과 맞지만, 후속 구현자가 다시 AppleGothic으로 되돌리지 않도록 "v2 standalone 디자인은 rendered 기준 Pretendard 우선, Apple 계열은 fallback"이라는 예외를 계획서나 컴포넌트 문서에 명시해야 한다.

### P2. 토큰은 아직 운영 HTML에 연결되지 않았다

현재 `web/*.html`에서 `web/styles/v2_tokens.css`를 import하는 흔적은 없다. 이는 Phase 0 기준으로는 정상이나, 사용자가 브라우저에서 보는 기존 페이지는 아직 바뀌지 않는다. 실제 사용 가능한 화면 전환은 B1의 `v2_components.css`와 HTML 연결 작업부터 시작된다.

## 7. 다음 단계 판단

권장 순서는 다음과 같다.

1. B1 `v2_components.css` 작성
   - 이유: 토큰이 잠겼으므로 바로 카드, 버튼, 배지, 입력, 헤더, 듀얼 엔진 비교 카드로 연결할 수 있다.
   - 결과: 기존 페이지와 standalone 디자인 사이의 시각 격차를 실제 화면에서 줄이기 시작한다.

2. B2 1차 PR 머지 및 8011 활성화 병행
   - 이유: FPE/APE dual engine backend가 안정적으로 올라와야 UI 비교 카드와 gate 표시가 실제 데이터로 동작한다.
   - 주의: 현재 작업트리에 unrelated 변경과 untracked 파일이 많으므로 PR/commit 범위는 반드시 분리해야 한다.

3. B3 EvaluationSnapshot API 신설
   - 이유: 평가 결과를 report_id 기준으로 고정 저장해야 제안서, 이메일, 업데이트일지, 엔진비교표가 같은 평가 근거를 공유할 수 있다.
   - 권장 시점: B1 시각 컴포넌트 골격과 B2 엔진 활성화 검증 이후.

4. B4 A3/A1 산출물 별도 PR
   - 이유: 현재 A3/A1만 떼어내면 작은 검증 PR로 관리 가능하다.
   - 주의: `data/bizaipro_learning_registry.json` 등 unrelated dirty 파일은 제외해야 한다.

## 8. 최종 판정

Phase 0 A3 + A1은 승인 가능하다. 구현 착수를 막는 P0/P1은 없다.

다음 실작업은 B1을 우선 진행하고, B2는 사용자의 PR 머지/서버 활성화 결정과 병행하는 방식이 가장 안전하다.
