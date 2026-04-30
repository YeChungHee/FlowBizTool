# [codex] FlowBizTool v2 Standalone 디자인 구현 계획서 v4 검증 보고서

- 문서번호: FBU-VAL-UI-V2-STANDALONE-v4-20260430
- 작성일: 2026-04-30
- 검증 대상: `docs/[claude]flowbiz_ui_v2_standalone_design_implementation_plan_v4_20260430.md`
- 이전 검증: `docs/[codex]flowbiz_ui_v2_standalone_design_implementation_plan_v3_validation_20260430.md`
- 판정: **조건부 승인 가능**

## 1. 이전 Finding 반영 여부

| 이전 Finding | v4 반영 상태 | 판정 |
|---|---|---|
| `ulid.new()` 의존성 누락 | Python 모델 예시는 `uuid.uuid4().hex`로 교체 | 종료 |
| negative snapshot seed가 모델 검증에 막힘 | `UnsafeRawSnapshotForTest` + `/api/test/seed-raw-snapshot` raw fixture 방식으로 변경 | 종료 |
| `v2_tokens.css` on_hold 토큰 미반영 | `web/styles/v2_tokens.css:93`에 실제 반영 확인 | 종료 |

v4는 v3의 핵심 문제를 잘 정리했다. 특히 Python 서버 측 ID 생성은 외부 의존성 없이 표준 라이브러리로 전환되었고, `on_hold` 토큰도 실제 CSS에 들어갔다.

## 2. 신규 Finding

### Finding 1 [P1] Playwright fixture가 `uuid` npm 패키지에 새로 의존

v4는 Python의 `ulid` 의존성은 제거했지만, Playwright fixture 예시에서 `import { v4 as uuidv4 } from 'uuid'`를 사용한다. 현재 repo에는 `package.json`, `node_modules`, Playwright config가 없고, 현재 Node 환경에서도 `require('uuid')`는 `MODULE_NOT_FOUND`다. 이대로 구현하면 E2E fixture가 시작 전에 실패한다.

확인 결과:

```text
node -e "require('uuid')"
MODULE_NOT_FOUND
```

권고:

- 외부 npm 의존성을 늘리지 않으려면 Node 표준 `crypto.randomUUID().replace(/-/g, '')`를 사용한다.
- 또는 E2E 도입 Phase에서 `package.json`을 만들고 `uuid`, `@playwright/test`를 명시한다.
- Python과 JS 모두 “외부 의존성 0”을 목표로 한다면 `node:crypto` 기준으로 통일한다.

### Finding 2 [P1] seed API 등록 검증이 `curl -f -X OPTIONS` 때문에 false fail 가능

v4의 `tests/run_e2e.sh`는 `curl -fsS ... -X OPTIONS | grep "200\|Method Not Allowed"`로 test seed API 등록 여부를 확인한다. 그러나 FastAPI의 POST 라우트에 OPTIONS를 보내면 405가 날 수 있고, `curl -f`는 4xx 응답에서 body를 출력하지 않거나 실패 코드로 종료한다. 결과적으로 라우트가 정상 등록되어 있어도 grep이 기대 문자열을 못 받아 실패할 수 있다.

권고:

- `/openapi.json`에서 `/api/test/seed-raw-snapshot` 경로 존재 여부를 확인한다.
- 또는 실제 POST probe를 최소 JSON body로 호출해 200을 확인한다.
- shell은 `set -euo pipefail`로 바꾸고, 실패 시 `/tmp/uvicorn8012.log` 마지막 80줄을 출력한다.

### Finding 3 [P2] missing-field 테스트가 500도 성공으로 허용

`proposal API rejects snapshot with missing FPE fields` 테스트는 `expect(response.status()).toBeGreaterThanOrEqual(400)`만 확인한다. 이 조건은 의도한 400 validation error뿐 아니라 500 서버 예외도 성공으로 처리한다. 방어 로직 검증 목적이라면 500은 실패여야 한다.

권고:

- 기대값을 `expect(response.status()).toBe(400)` 또는 `toBe(422)`로 고정한다.
- 응답 body의 `detail`에 `missing required fields`가 포함되는지 확인한다.
- 이 테스트는 “서버가 크래시하지 않고 정책 오류로 거부한다”를 검증해야 한다.

### Finding 4 [P2] raw test snapshot이 production data 경로를 공유

test-only seed API는 `SNAPSHOT_DIR = Path("data/evaluation_reports")`를 사용한다. `FLOWBIZ_ENV=test`로 라우트는 제한되지만, 테스트 실패나 teardown 누락 시 raw/비정상 snapshot이 운영 데이터 디렉토리에 남을 수 있다.

권고:

- 테스트 환경에서는 `data/test_evaluation_reports` 또는 `tmp/evaluation_reports_test`를 사용한다.
- 앱의 snapshot loader도 `FLOWBIZ_ENV=test`일 때 test directory를 보도록 분기한다.
- teardown 실패에 대비해 `tests/run_e2e.sh` 시작/종료 시 test snapshot directory를 정리한다.

## 3. 재검증 요약

| 검증 항목 | v4 상태 | 판정 |
|---|---|---|
| Python ID 생성 | `uuid.uuid4().hex`로 전환 | 적합 |
| JS/E2E ID 생성 | `uuid` npm 패키지 사용 | 보완 필요 |
| negative fixture | raw fixture로 Pydantic 우회 | 적합 |
| test seed API guard | `FLOWBIZ_ENV=test` 조건 있음 | 조건부 적합, 검증 커맨드 보강 필요 |
| on_hold CSS token | 실제 `web/styles/v2_tokens.css:93` 반영 | 적합 |
| missing-field 방어 테스트 | 500도 통과 | 보완 필요 |

## 4. 실행 전 보완 체크리스트

- [ ] Playwright fixture의 `uuid` import를 `node:crypto` `randomUUID()`로 교체하거나 npm 의존성 명시
- [ ] seed API 등록 검증을 OPTIONS+curl -f 방식에서 OpenAPI 또는 실제 POST probe로 변경
- [ ] missing-field 테스트 기대값을 400/422로 고정하고 detail 문구 검증
- [ ] test raw snapshot 저장 경로를 production `data/evaluation_reports`와 분리

## 5. 결론

v4는 **실제 구현 착수 직전 계획으로 거의 정리된 상태**다. 다만 E2E 테스트 체계가 아직 repo 현실과 맞지 않는 부분이 있어, 위 4개 항목을 반영하면 계획서 기준으로 승인 가능하다.
