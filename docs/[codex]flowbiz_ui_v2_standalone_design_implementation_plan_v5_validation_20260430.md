# [codex] FlowBizTool v2 Standalone 디자인 구현 계획서 v5 검증 보고서

- 문서번호: FBU-VAL-UI-V2-STANDALONE-v5-20260430
- 작성일: 2026-04-30
- 검증 대상: `docs/[claude]flowbiz_ui_v2_standalone_design_implementation_plan_v5_20260430.md`
- 이전 검증: `docs/[codex]flowbiz_ui_v2_standalone_design_implementation_plan_v4_validation_20260430.md`
- 판정: **조건부 승인 가능**

## 1. 이전 Finding 반영 여부

| 이전 Finding | v5 반영 상태 | 판정 |
|---|---|---|
| Playwright fixture가 `uuid` npm 패키지에 의존 | `node:crypto.randomUUID()`로 변경. 현재 Node 환경에서 동작 확인 | 종료 |
| seed API 등록 검증 false fail 가능 | OpenAPI 확인 + 실제 POST probe 방식으로 변경 | 종료 |
| missing-field 테스트가 500도 허용 | 400/422만 허용하고 detail 문구 검증 추가 | 종료 |
| raw test snapshot이 production data 경로 공유 | `data/test_evaluation_reports/`로 분리 계획 추가 | 종료 |

v5는 v4 검증의 4개 Finding을 모두 문서상 반영했다. `node:crypto.randomUUID()`도 현재 환경에서 정상 동작한다.

## 2. 신규 Finding

### Finding 1 [P1] E2E 실행 기반이 아직 repo에 없음

v5는 `npx playwright test`를 기준으로 E2E를 실행한다. 하지만 현재 repo에는 `package.json`, `playwright.config.*`, `tests/run_e2e.sh`가 없다. 계획서대로 바로 구현하면 E2E 명령이 환경별로 달라지고, Playwright 버전/브라우저 설치/테스트 baseURL이 고정되지 않는다.

확인 결과:

```text
find . -maxdepth 3 -name package.json -o -name 'playwright.config.*' -o -name 'run_e2e.sh'
# 결과 없음
```

권고:

- Phase 5 전에 `package.json`, `playwright.config.ts`, `tests/run_e2e.sh`를 명시적으로 산출물에 추가한다.
- `@playwright/test` 버전과 `baseURL=http://127.0.0.1:8012`를 고정한다.
- `npx playwright install chromium` 또는 브라우저 설치 확인 절차를 실행 순서에 넣는다.

### Finding 2 [P1] run_e2e.sh 실패 시 서버와 test 디렉토리 정리가 안 됨

v5의 `trap`은 실패 시 로그를 출력하고 `exit 1`만 수행한다. `UVICORN_PID`를 kill하거나 `data/test_evaluation_reports`를 삭제하지 않는다. `npx playwright test` 실패, OpenAPI 검증 실패, POST probe 실패 시 uvicorn 프로세스와 raw test snapshot이 남을 수 있다.

권고:

- `cleanup()` 함수를 만들고 `trap cleanup EXIT`으로 등록한다.
- cleanup에서 `kill "${UVICORN_PID:-}" 2>/dev/null || true`, `rm -rf "$FLOWBIZ_TEST_SNAPSHOT_DIR"`를 실행한다.
- 실패 로그 출력은 `trap 'status=$?; ...; cleanup; exit $status' ERR` 또는 EXIT trap 안에서 처리한다.

### Finding 3 [P2] `.gitignore`에 test snapshot 경로가 아직 반영되지 않음

v5는 `.gitignore`에 `data/test_evaluation_reports/`를 추가하라고 명시하지만, 현재 `.gitignore`에는 아직 해당 항목이 없다. 구현 중 테스트 디렉토리가 생성되면 untracked 파일로 남을 수 있다.

확인 결과:

```text
.gitignore:
1 __pycache__/
...
7 outputs/
8 tmp/
9 .env
```

권고:

- Phase 5 산출물에 `.gitignore` 수정 항목을 포함한다.
- `data/test_evaluation_reports/`와 필요 시 `test-results/`, `playwright-report/`도 함께 ignore한다.

### Finding 4 [P2] “400 고정” 문구와 실제 허용값이 다름

v5 변경 요약은 missing-field 테스트를 `400 고정`이라고 설명하지만, 실제 테스트 예시는 `[400, 422]`를 허용한다. 의도는 FastAPI body validation 422와 앱 정책 오류 400을 모두 허용하는 것이므로 문구를 `400/422 고정`으로 정리하는 편이 좋다.

권고:

- 변경 요약과 체크리스트의 `400 고정` 표현을 `400/422 고정`으로 수정한다.
- 단, 서버 내부 예외인 500은 실패로 유지한다.

## 3. 재검증 요약

| 검증 항목 | v5 상태 | 판정 |
|---|---|---|
| JS ID 생성 | `node:crypto.randomUUID()` 사용 | 적합 |
| seed API 검증 | OpenAPI + POST probe | 적합 |
| missing-field 테스트 | 400/422 + detail 검증 | 적합, 문구 정리 필요 |
| test data 경로 | `data/test_evaluation_reports` 분리 | 조건부 적합, .gitignore 반영 필요 |
| E2E 실행 환경 | `npx playwright test` 전제 | 보완 필요 |
| 실패 시 cleanup | 미흡 | 보완 필요 |

## 4. 실행 전 보완 체크리스트

- [ ] `package.json`, `playwright.config.ts`, `tests/run_e2e.sh` 산출물 추가
- [ ] `tests/run_e2e.sh`에 cleanup trap 추가
- [ ] `.gitignore`에 `data/test_evaluation_reports/`, `test-results/`, `playwright-report/` 추가
- [ ] `400 고정` 문구를 `400/422 고정`으로 정정

## 5. 결론

v5는 설계 방향과 주요 정책은 거의 닫혔다. 다만 실제 실행 가능한 E2E 검증 체계로 만들려면 Playwright 실행 기반과 실패 시 cleanup을 계획서에 더 명확히 넣어야 한다. 이 보강이 끝나면 계획서 기준으로 승인 가능하다.
