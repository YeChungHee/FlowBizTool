# [codex] FlowBizTool v2 Standalone 디자인 구현 계획서 v6 검증 보고서

- 문서번호: FBU-VAL-UI-V2-STANDALONE-v6-20260430
- 작성일: 2026-04-30
- 검증 대상: `docs/[claude]flowbiz_ui_v2_standalone_design_implementation_plan_v6_20260430.md`
- 이전 검증: `docs/[codex]flowbiz_ui_v2_standalone_design_implementation_plan_v5_validation_20260430.md`
- 판정: **승인 가능**

## 1. 이전 Finding 반영 여부

| 이전 Finding | v6 반영 상태 | 판정 |
|---|---|---|
| E2E 실행 기반 파일 없음 | `package.json`, `playwright.config.ts`, `tests/run_e2e.sh` 산출물 명세 추가 | 종료 |
| 실패 시 서버와 test 디렉토리 정리 누락 | `cleanup()` + `trap cleanup EXIT` 추가 | 종료 |
| `.gitignore`에 test snapshot 경로 미반영 | `.gitignore`에 `data/test_evaluation_reports/`, `test-results/`, `playwright-report/`, `node_modules/` 실제 반영 확인 | 종료 |
| “400 고정” 문구와 코드 불일치 | `400/422 고정`으로 문구 통일 | 종료 |

v6는 v5 검증에서 남긴 4개 항목을 모두 반영했다. 특히 `.gitignore`는 실제 파일에 반영되어 있어 문서 주장과 repo 상태가 일치한다.

## 2. 신규 Finding

### Finding 1 [P2] 서버 준비 확인이 고정 `sleep 3`에 의존

`tests/run_e2e.sh` 예시는 uvicorn을 기동한 뒤 `sleep 3` 후 바로 `/openapi.json`을 호출한다. 로컬에서는 충분할 수 있지만, 느린 환경에서는 서버가 아직 준비되지 않아 OpenAPI 검증이 false fail로 끝날 수 있다.

권고:

- `sleep 3`만 두지 말고 `/api/health` 또는 `/openapi.json`을 최대 30초까지 재시도하는 readiness loop를 추가한다.
- 실패 시에는 지금처럼 `/tmp/uvicorn8012.log` 마지막 80줄을 출력하면 된다.

### Finding 2 [P2] `test:e2e:ui`는 서버 기동 경로가 없음

`package.json` 예시의 `test:e2e`는 `tests/run_e2e.sh`를 통해 uvicorn을 직접 띄운다. 반면 `test:e2e:ui`는 `FLOWBIZ_ENV=test ... playwright test --ui`만 실행하므로, 별도 서버가 떠 있지 않으면 UI 모드에서 바로 실패할 수 있다.

권고:

- `test:e2e:ui`도 `tests/run_e2e.sh --ui`처럼 서버 기동을 공유하게 하거나,
- 문서에 “UI 모드는 별도 터미널에서 test 서버를 먼저 실행”이라고 명시한다.

## 3. 재검증 요약

| 검증 항목 | v6 상태 | 판정 |
|---|---|---|
| Playwright 실행 기반 | package/config/run script 명세 완료 | 적합 |
| cleanup | EXIT trap으로 성공/실패/Ctrl+C 정리 | 적합 |
| test data ignore | `.gitignore` 실제 반영 | 적합 |
| 400/422 문구 | 문구와 코드 일치 | 적합 |
| 서버 readiness | 고정 sleep 의존 | P2 권고 |
| UI mode 실행 | 서버 기동 경로 별도 필요 | P2 권고 |

## 4. 결론

v6는 **계획서 기준 승인 가능**하다. 남은 두 건은 실행 안정성을 높이는 P2 권고이며, 구현 착수를 막는 P0/P1은 없다.

실제 구현 시에는 Phase 5 산출물 생성 단계에서 다음을 함께 반영하면 된다.

- `tests/run_e2e.sh`에 readiness retry loop 추가
- `test:e2e:ui` 실행 방식을 서버 기동 포함 또는 별도 서버 선기동 방식으로 명확화
