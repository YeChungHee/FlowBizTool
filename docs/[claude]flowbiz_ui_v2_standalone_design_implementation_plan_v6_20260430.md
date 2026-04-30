# FlowBizTool v2 Standalone 디자인 구현 계획서 v6 [claude]

- 문서번호: FBU-PLAN-UI-V2-STANDALONE-IMPL-v6-20260430
- 작성일: 2026-04-30
- 작성자: [claude]
- 이전 버전: `[claude]flowbiz_ui_v2_standalone_design_implementation_plan_v5_20260430.md` (v5)
- 검증: `[codex]flowbiz_ui_v2_standalone_design_implementation_plan_v5_validation_20260430.md` (P1 2건 + P2 2건 — **조건부 승인 가능**)
- 변경 사유: v5 [codex] 검증 4건 반영 — **E2E 실행 기반(package.json/playwright.config/run_e2e.sh) 산출물 명세** + **cleanup trap** + **.gitignore 즉시 적용** + **문구 "400/422 고정" 정정**

## 0. v5 → v6 변경 요약

| Finding | 우선순위 | v5 문제 | v6 반영 |
|---|---|---|---|
| F1 [codex] v5: E2E 실행 기반 부재 | **P1** | `npx playwright test` 전제 vs `package.json`/`playwright.config.*`/`run_e2e.sh` 모두 누락 | **§11.6 신설** — 3 산출물 골격 명세 (Phase 5 진입 전 필수) + Playwright 버전 고정 + baseURL 고정 + chromium 설치 절차 |
| F2 [codex] v5: run_e2e.sh 실패 시 cleanup 부재 | **P1** | trap이 로그만 출력 → uvicorn PID 미종료, test 디렉토리 미정리 | **§11.3 cleanup() 함수 + trap EXIT** — 실패/성공 모두 통합 정리 |
| F3 [codex] v5: .gitignore 미반영 | P2 | 계획만 명시, 실제 .gitignore에 없음 | **본 세션 즉시 적용 완료** (4 라인 추가) |
| F4 [codex] v5: "400 고정" 문구 vs 실제 [400, 422] | P2 | 문구가 실제 허용값과 불일치 | **§11.2 + §13 모두 "400/422 고정"으로 정정** |

### 0.1 본 세션에서 즉시 실행한 정정 (F3)

`.gitignore` 4 라인 추가:

```diff
  __pycache__/
  data/api_keys.local.json
  data/dart_corp_codes_cache.json
  .DS_Store
  *.pyc
  *.log
  outputs/
  tmp/
  .env
+
+ # v6 [codex] F3 P2 — E2E 테스트 산출물 (FBU-PLAN-UI-V2-STANDALONE-IMPL-v6)
+ data/test_evaluation_reports/
+ test-results/
+ playwright-report/
+ node_modules/
```

→ v6 작성 전 **선반영 완료**. test 디렉토리 + Playwright 산출물 + Node 패키지 모두 추적 차단.

## 1. 핵심 운영 원칙 (v5 §1 + 신규 #20 #21 #22 #23)

| 원칙 | 출처 |
|---|---|
| (v5 #1-#19 모두 계승) | v5 §1 |
| (신규) **#20 E2E 실행 기반 산출물 3종 명세** | codex v5 F1 [P1] |
| (신규) **#21 run_e2e.sh = cleanup trap EXIT** | codex v5 F2 [P1] |
| (신규) **#22 .gitignore = 테스트 산출물 추적 차단** | codex v5 F3 [P2] |
| (신규) **#23 negative test 기대값 = 400/422 고정** | codex v5 F4 [P2] |

## 2-10. (v5 §2-§10 그대로 — 운영 원칙/디자인/Phase/모델 변경 없음)

## 11. 검증 계획 — E2E 체계 완성 (F1-F4)

### 11.1 v5 §11.1 그대로 (Phase별 검증)

### 11.2 E2E negative case — 400/422 고정 (F4 [P2] 문구 정정)

```typescript
// tests/e2e/decision_source_fpe.spec.ts
import { test } from './fixtures/snapshot_seeder';
import { expect } from '@playwright/test';

test('proposal API rejects non-FPE decision_source from raw legacy snapshot', async ({
  request, fakeApeBoundReportId
}) => {
  const response = await request.post('/api/proposal/generate', {
    headers: { 'Content-Type': 'application/json' },
    data: { report_id: fakeApeBoundReportId, template_variant: 'standard' }
  });
  // F4 정정: 정책 오류는 400 (앱 검증), body validation은 422 (FastAPI/Pydantic)
  expect([400, 422]).toContain(response.status());

  const body = await response.json();
  expect(body.detail).toContain('decision_source must be FPE');
});

test('proposal API rejects snapshot with missing FPE fields with 400/422', async ({
  request, fakeNoFpeFieldsReportId
}) => {
  const response = await request.post('/api/proposal/generate', {
    headers: { 'Content-Type': 'application/json' },
    data: { report_id: fakeNoFpeFieldsReportId, template_variant: 'standard' }
  });
  // F4 정정: 명시적으로 400/422 만 허용 — 500은 명시적 실패
  expect([400, 422]).toContain(response.status());

  const body = await response.json();
  expect(body.detail).toContain('missing required fields');
});
```

> **핵심**: 500 (서버 내부 예외)은 명시적 실패. 정책 검증/스키마 검증은 모두 4xx로 처리.

### 11.3 run_e2e.sh — cleanup trap (F2 [P1] 정정)

**v5의 잘못된 패턴**:
```bash
# ❌ 실패 시 로그만 출력, 프로세스/디렉토리 미정리
trap 'echo "[FAIL] errored — uvicorn 로그:"; tail -80 /tmp/uvicorn8012.log; exit 1' ERR
```

**v6 정정 — cleanup 함수 + trap EXIT**:

```bash
#!/bin/bash
# tests/run_e2e.sh (v6)
set -euo pipefail

# F2 [codex] v5 P1 정정: cleanup 함수
cleanup() {
  local exit_code=$?

  echo ""
  echo "=== cleanup 시작 (exit code: $exit_code) ==="

  # 1. uvicorn 프로세스 종료
  if [ -n "${UVICORN_PID:-}" ]; then
    if kill -0 "$UVICORN_PID" 2>/dev/null; then
      kill "$UVICORN_PID" 2>/dev/null || true
      sleep 1
      # 강제 종료 (SIGKILL)
      kill -9 "$UVICORN_PID" 2>/dev/null || true
      echo "[OK] uvicorn PID $UVICORN_PID 종료"
    fi
  fi

  # 2. test 디렉토리 정리 (성공/실패 무관)
  if [ -n "${FLOWBIZ_TEST_SNAPSHOT_DIR:-}" ] && [ -d "$FLOWBIZ_TEST_SNAPSHOT_DIR" ]; then
    rm -rf "$FLOWBIZ_TEST_SNAPSHOT_DIR"
    echo "[OK] test 디렉토리 $FLOWBIZ_TEST_SNAPSHOT_DIR 정리"
  fi

  # 3. 실패 시에만 uvicorn 로그 출력
  if [ "$exit_code" -ne 0 ] && [ -f /tmp/uvicorn8012.log ]; then
    echo ""
    echo "=== uvicorn 로그 마지막 80줄 ==="
    tail -80 /tmp/uvicorn8012.log
  fi

  echo "=== cleanup 완료 ==="
  exit "$exit_code"
}

# F2 정정: trap EXIT (성공/실패/Ctrl+C 모두 cleanup 실행)
trap cleanup EXIT

# 1. test 환경변수 (v5 §11.5 계승)
export FLOWBIZ_ENV=test
export FLOWBIZ_TEST_SNAPSHOT_DIR="data/test_evaluation_reports"

# 2. 시작 시 강제 정리 (이전 실행 잔재)
rm -rf "$FLOWBIZ_TEST_SNAPSHOT_DIR"
mkdir -p "$FLOWBIZ_TEST_SNAPSHOT_DIR"

# 3. uvicorn 기동
nohup python3 -m uvicorn app:app --host 127.0.0.1 --port 8012 \
  > /tmp/uvicorn8012.log 2>&1 &
UVICORN_PID=$!
sleep 3

# 4. seed API 등록 검증 (v5 §11.3 계승 — OpenAPI + POST probe)
SEED_PATH="/api/test/seed-raw-snapshot"
OPENAPI_HAS_SEED="$(curl -fsS http://127.0.0.1:8012/openapi.json \
  | python3 -c "
import sys, json
spec = json.load(sys.stdin)
print('1' if '$SEED_PATH' in spec.get('paths', {}) else '0')
")"

if [ "$OPENAPI_HAS_SEED" != "1" ]; then
  echo "[FAIL] $SEED_PATH 미등록"
  exit 1
fi
echo "[OK] OpenAPI seed API 등록 확인"

# 5. 실제 POST probe
PROBE_REPORT_ID="$(node -e 'console.log(require("node:crypto").randomUUID().replace(/-/g, ""))')"
PROBE_STATUS="$(curl -s -o /dev/null -w '%{http_code}' \
  -X POST http://127.0.0.1:8012/api/test/seed-raw-snapshot \
  -H 'Content-Type: application/json' \
  -d "{\"report_id\": \"$PROBE_REPORT_ID\", \"decision_source\": \"FPE\"}")"

if [ "$PROBE_STATUS" != "200" ]; then
  echo "[FAIL] POST probe 실패: HTTP $PROBE_STATUS"
  exit 1
fi
curl -fsS -X DELETE "http://127.0.0.1:8012/api/test/raw-snapshot/$PROBE_REPORT_ID" > /dev/null
echo "[OK] POST probe 통과"

# 6. Playwright 실행
npx playwright test

# 7. 정상 종료 시 cleanup 자동 호출 (trap EXIT)
echo "[OK] E2E 통과"
```

**핵심 변경**:
- `trap cleanup EXIT` — 성공/실패/Ctrl+C 모두 동일 정리
- `kill -0` 프로세스 살아있는지 확인 후 종료
- SIGTERM → 1초 → SIGKILL fallback
- 실패 시에만 uvicorn 로그 출력 (성공 시 출력 안 해 stdout 깨끗)
- exit_code 보존 (`exit "$exit_code"`)

### 11.4 fixture 디렉토리 구조 (v5 §11.4 그대로)

### 11.5 test data 디렉토리 분리 (v5 §11.5 그대로)

### 11.6 E2E 실행 기반 3 산출물 (F1 [P1] 신설)

**v5의 누락**: `npx playwright test` 전제하나 실제 `package.json`/`playwright.config.*`/`run_e2e.sh` 모두 부재.

**v6 정정 — Phase 5 진입 전 3 산출물 명세**:

#### 11.6.1 `package.json` (Phase 5 신설)

```json
{
  "name": "flowbiz-ultra-e2e",
  "version": "0.1.0",
  "private": true,
  "description": "FlowBiz_ultra E2E 테스트 — Playwright (Python uvicorn 백엔드 검증)",
  "scripts": {
    "test:e2e": "bash tests/run_e2e.sh",
    "test:e2e:ui": "FLOWBIZ_ENV=test FLOWBIZ_TEST_SNAPSHOT_DIR=data/test_evaluation_reports playwright test --ui",
    "test:install": "playwright install chromium"
  },
  "devDependencies": {
    "@playwright/test": "^1.46.0"
  }
}
```

> Playwright 버전 고정 (`^1.46.0`) — minor 자동 업그레이드만 허용. major는 명시적 결정.

#### 11.6.2 `playwright.config.ts` (Phase 5 신설)

```typescript
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  timeout: 30_000,
  fullyParallel: false,            // FastAPI 단일 인스턴스 — 순차 실행
  forbidOnly: !!process.env.CI,    // CI에서 .only() 차단
  retries: process.env.CI ? 1 : 0,
  workers: 1,                      // 단일 worker (snapshot 충돌 방지)

  reporter: [
    ['html', { outputFolder: 'playwright-report', open: 'never' }],
    ['list']
  ],

  use: {
    baseURL: 'http://127.0.0.1:8012',  // F1 [codex] v5 — baseURL 고정
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],

  // run_e2e.sh가 uvicorn을 외부에서 기동하므로 webServer 미사용
  // (Playwright의 webServer가 아닌 shell 스크립트 통합)
});
```

#### 11.6.3 `tests/run_e2e.sh` (위 §11.3 cleanup 통합 버전)

#### 11.6.4 chromium 설치 절차 (Phase 5 진입 시 1회)

```bash
# Phase 5 진입 시 1회 실행
npm install
npm run test:install   # → playwright install chromium

# 이후 실행
npm run test:e2e       # → bash tests/run_e2e.sh
```

#### 11.6.5 디렉토리 구조 (Phase 5 산출물 종합)

```
FlowBiz_ultra/
├── package.json                            ← v6 신설 (F1)
├── playwright.config.ts                    ← v6 신설 (F1)
├── .gitignore                              ← v6 즉시 적용 (F3)
│   + node_modules/
│   + test-results/
│   + playwright-report/
│   + data/test_evaluation_reports/
│
├── tests/
│   ├── run_e2e.sh                          ← v6 신설 (F1 + F2 cleanup)
│   └── e2e/
│       ├── fixtures/
│       │   ├── snapshot_seeder.ts          (v5 §11.2 + node:crypto)
│       │   └── seed_data/
│       │       ├── both_go_normal.json
│       │       ├── fpe_blocked_ccc.json
│       │       └── exhibition_lead.json
│       ├── decision_source_fpe.spec.ts     (F4 정정 — 400/422 고정)
│       ├── proposal_form_no_ape.spec.ts
│       └── exhibition_evaluator.spec.ts
│
├── data/
│   ├── evaluation_reports/                 (production)
│   └── test_evaluation_reports/            (test, gitignore)
│
└── (기존 Python/web 구조 유지)
```

## 12. Risk + Mitigation (v5 §12 + 신규)

| Risk | 영향 | 대응 |
|---|---|---|
| (v5 동일) | (다양) | (계승) |
| **(신규)** Playwright 버전 drift | 환경별 다른 동작 | **package.json `^1.46.0` 고정** (F1) |
| **(신규)** chromium 미설치 | 첫 실행 실패 | **`npm run test:install` 절차** + Phase 5 acceptance criteria |
| **(신규)** test 실행 도중 Ctrl+C → uvicorn/디렉토리 잔존 | 다음 실행 충돌 | **`trap cleanup EXIT`** (F2) |
| **(신규)** test 산출물 git 추적 | 저장소 비대 | **`.gitignore` 4 라인** (F3 — 즉시 적용) |
| **(신규)** 문서 문구 vs 실제 코드 불일치 | 검토자 혼선 | **"400/422 고정"** 통일 (F4) |

## 13. 다음 액션 (codex v5 §4 체크리스트 4건 통합)

- [x] **(F1)** `package.json`, `playwright.config.ts`, `tests/run_e2e.sh` 산출물 명세 — §11.6 신설
- [x] **(F2)** `tests/run_e2e.sh` cleanup trap — §11.3 정정 (cleanup 함수 + trap EXIT)
- [x] **(F3)** `.gitignore` 추가 — **본 세션 즉시 적용 완료** (4 라인)
- [x] **(F4)** "400 고정" → "400/422 고정" — §11.2 + §13 + §A.4 통일

## 14. 핵심 메시지

**v5 → v6 핵심 보강 4건**:
1. **E2E 실행 기반 3 산출물** (codex F1) — package.json, playwright.config.ts, run_e2e.sh 명세 + chromium 설치 절차
2. **cleanup trap EXIT** (codex F2) — uvicorn PID 종료 + test 디렉토리 정리 (성공/실패/Ctrl+C 모두)
3. **.gitignore 4 라인** (codex F3) — `data/test_evaluation_reports/`, `test-results/`, `playwright-report/`, `node_modules/` 즉시 적용
4. **"400/422 고정"** 문구 통일 (codex F4) — 정책 오류(400) + body validation(422) 모두 허용, 500은 실패

→ codex v5 §5 인용: "v5는 설계 방향과 주요 정책은 거의 닫혔다. 다만 실제 실행 가능한 E2E 검증 체계로 만들려면 Playwright 실행 기반과 실패 시 cleanup을 계획서에 더 명확히 넣어야 한다." → **v6에서 4건 모두 반영 완료**.

---

## 부록 A. v5 → v6 정정 위치

### A.1 E2E 실행 기반 3 산출물 (F1 P1)

| 위치 | v5 | v6 |
|---|---|---|
| `package.json` | (없음) | **§11.6.1 명세** — `@playwright/test ^1.46.0` + `test:e2e`, `test:install` scripts |
| `playwright.config.ts` | (없음) | **§11.6.2 명세** — `baseURL: 'http://127.0.0.1:8012'`, `workers: 1`, `chromium` 단일 |
| `tests/run_e2e.sh` | (없음) | **§11.6.3 = §11.3 cleanup 버전** |
| chromium 설치 | (없음) | **§11.6.4 `npm run test:install`** |

### A.2 cleanup trap EXIT (F2 P1)

| 위치 | v5 | v6 |
|---|---|---|
| §11.3 trap | `trap '... ; exit 1' ERR` (실패 시만) | **`trap cleanup EXIT`** (성공/실패/Ctrl+C 모두) |
| cleanup 함수 | (없음) | **§11.3 신설** — `kill -0` 확인 + SIGTERM → SIGKILL fallback + `rm -rf` test dir + 실패 시 로그 |
| exit code 보존 | (없음) | **`local exit_code=$?` + `exit "$exit_code"`** |

### A.3 .gitignore (F3 P2)

| 위치 | v5 | v6 |
|---|---|---|
| .gitignore 명시 | 계획만 | **본 세션 즉시 적용 완료** (4 라인) |
| 추가 항목 | (없음) | **`data/test_evaluation_reports/`, `test-results/`, `playwright-report/`, `node_modules/`** |

### A.4 문구 정정 (F4 P2)

| 위치 | v5 | v6 |
|---|---|---|
| §11.2 missing-field | "400 고정" | **"400/422 고정"** + 명시적 [400, 422] |
| §0 변경 요약 | "400 고정 + detail 검증" | **"400/422 고정 + detail 검증"** |
| §13 체크리스트 | "missing-field 400" | **"missing-field 400/422"** |

## 부록 B. 누적 Finding 추적

| 단계 | 신규 Finding | 누적 |
|---|---|---|
| 본 계획 v1 | 0 (자체) | 0 |
| 본 계획 v2 | 0 (codex v1 4건) | 4 |
| 본 계획 v3 | 0 (codex v2 5건) | 9 |
| 본 계획 v4 | 0 (codex v3 3건) | 12 |
| 본 계획 v5 | 0 (codex v4 4건) | 16 |
| **본 계획 v6** | **0 (codex v5 4건)** | **20** |

**잔여 P0/P1**: 0건.

## 부록 C. 본 세션 즉시 실행 작업 로그

| 작업 | 결과 |
|---|---|
| `.gitignore`에 4 라인 추가 (data/test_evaluation_reports/, test-results/, playwright-report/, node_modules/) | ✅ |
| codex v5 검증 4 Finding 모두 v6에 반영 | ✅ |

## 부록 D. v6 단일 적용 코드 패턴

**1. cleanup trap (F2)**:
```bash
cleanup() {
  local exit_code=$?
  [ -n "${UVICORN_PID:-}" ] && kill -0 "$UVICORN_PID" 2>/dev/null && \
    { kill "$UVICORN_PID" 2>/dev/null; sleep 1; kill -9 "$UVICORN_PID" 2>/dev/null || true; }
  [ -n "${FLOWBIZ_TEST_SNAPSHOT_DIR:-}" ] && [ -d "$FLOWBIZ_TEST_SNAPSHOT_DIR" ] && \
    rm -rf "$FLOWBIZ_TEST_SNAPSHOT_DIR"
  [ "$exit_code" -ne 0 ] && [ -f /tmp/uvicorn8012.log ] && \
    tail -80 /tmp/uvicorn8012.log
  exit "$exit_code"
}
trap cleanup EXIT
```

**2. test 기대값 400/422 (F4)**:
```typescript
expect([400, 422]).toContain(response.status());
expect(body.detail).toContain('missing required fields');
```

**3. package.json minimal (F1)**:
```json
{
  "scripts": {
    "test:e2e": "bash tests/run_e2e.sh",
    "test:install": "playwright install chromium"
  },
  "devDependencies": { "@playwright/test": "^1.46.0" }
}
```

**4. playwright.config.ts (F1)**:
```typescript
export default defineConfig({
  use: { baseURL: 'http://127.0.0.1:8012' },
  workers: 1,
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }]
});
```

**5. .gitignore 추가 (F3 — 본 세션 적용 완료)**:
```
data/test_evaluation_reports/
test-results/
playwright-report/
node_modules/
```
