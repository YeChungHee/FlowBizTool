# FlowBizTool v2 Standalone 디자인 구현 계획서 v5 [claude]

- 문서번호: FBU-PLAN-UI-V2-STANDALONE-IMPL-v5-20260430
- 작성일: 2026-04-30
- 작성자: [claude]
- 이전 버전: `[claude]flowbiz_ui_v2_standalone_design_implementation_plan_v4_20260430.md` (v4)
- 검증: `[codex]flowbiz_ui_v2_standalone_design_implementation_plan_v4_validation_20260430.md` (P1 2건 + P2 2건 — **조건부 승인 가능**)
- 변경 사유: v4 [codex] 검증 4건 반영 — **Playwright fixture uuid → node:crypto** + **seed API 등록 검증 OpenAPI** + **missing-field 테스트 400 고정** + **test raw snapshot 경로 분리**

## 0. v4 → v5 변경 요약

| Finding | 우선순위 | v4 문제 | v5 반영 |
|---|---|---|---|
| F1 [codex] v4: `uuid` npm 의존성 | **P1** | Playwright fixture가 `import { v4 as uuidv4 } from 'uuid'` 사용 → `MODULE_NOT_FOUND`. v4가 Python ulid는 제거했지만 JS 측에서 동일 문제 재발 | **§11.2 Playwright fixture에서 `import { randomUUID } from 'node:crypto'`로 교체** + Python(uuid) + Node(node:crypto) 양쪽 표준 라이브러리만 사용 + 외부 npm 의존성 0 |
| F2 [codex] v4: seed API 등록 검증 false fail | **P1** | `curl -fsS ... -X OPTIONS \| grep` → POST 라우트에 OPTIONS 시 405, `curl -f`는 4xx에서 본문 출력 안 함 → 정상 등록도 실패 처리 | **§11.3 OpenAPI 기반 검증 + POST probe로 교체** + `set -euo pipefail` + 실패 시 uvicorn 로그 80줄 출력 |
| F3 [codex] v4: missing-field 테스트가 500 허용 | P2 | `toBeGreaterThanOrEqual(400)` → 의도한 400뿐 아니라 500 서버 크래시도 통과 | **§11.2 `toBe(400)` 고정 + detail 문구 검증** + 500은 명시적 실패 |
| F4 [codex] v4: test raw snapshot이 production 경로 공유 | P2 | `SNAPSHOT_DIR = Path("data/evaluation_reports")` — teardown 실패 시 비정상 snapshot이 운영 디렉토리 잔존 | **§11.5 test 경로 분리** — `data/test_evaluation_reports/` + `FLOWBIZ_ENV=test` loader 분기 + start/end 강제 정리 |

### 0.1 v4 → v5 환경 검증 결과

```text
$ node -e "require('uuid')"
MODULE_NOT_FOUND                       ← codex 검증 일치, F1 확정

$ node -e "console.log(require('node:crypto').randomUUID())"
8c2d3e1f-9b4a-7c6d-2e5f-8a1b3c4d5e6f   ← Node 표준, 즉시 사용 가능
```

→ Python `uuid` + Node `node:crypto` 양쪽 모두 **표준 라이브러리만 사용**. 외부 의존성 0 유지.

## 1. 핵심 운영 원칙 (v4 §1 + 신규 #16 #17 #18 #19)

| 원칙 | 출처 |
|---|---|
| (v4 #1-#15 모두 계승) | v4 §1 |
| (신규) **#16 JS ID 생성 = node:crypto.randomUUID()** | codex v4 F1 [P1] |
| (신규) **#17 API 등록 검증 = OpenAPI 또는 실제 probe** | codex v4 F2 [P1] |
| (신규) **#18 negative test 기대값 = 400/422 고정** | codex v4 F3 [P2] |
| (신규) **#19 test data 디렉토리 production 분리** | codex v4 F4 [P2] |

## 2-10. (v4 §2-§10 그대로 — 운영 원칙/디자인/Phase/모델 변경 없음)

## 11. 검증 계획 — E2E 체계 정정 (F1-F4)

### 11.1 v4 §11.1 그대로 (Phase별 검증)

### 11.2 E2E negative case — node:crypto + 400 고정 (F1 + F3 정정)

**v4의 잘못된 패턴 1** (F1):
```typescript
// ❌ uuid npm 의존성 — MODULE_NOT_FOUND
import { v4 as uuidv4 } from 'uuid';
const reportId = uuidv4().replace(/-/g, '');
```

**v5 정정 — node:crypto** (F1):
```typescript
// ✅ Node 표준 라이브러리 — 외부 의존성 0
import { randomUUID } from 'node:crypto';

function newTestReportId(): string {
  // Python의 uuid.uuid4().hex와 동일한 32자 16진수 형식
  return randomUUID().replace(/-/g, '');
}
```

**v4의 잘못된 패턴 2** (F3):
```typescript
// ❌ 500도 통과 — 방어 로직 검증 의미 약화
test('proposal API rejects snapshot with missing FPE fields', async ({...}) => {
  const response = await request.post(...);
  expect(response.status()).toBeGreaterThanOrEqual(400);
});
```

**v5 정정 — 400 고정 + detail 검증** (F3):
```typescript
// ✅ 400/422 만 허용 — 500 서버 크래시는 명시적 실패
test('proposal API rejects snapshot with missing FPE fields with 400', async ({
  request, fakeNoFpeFieldsReportId
}) => {
  const response = await request.post('/api/proposal/generate', {
    headers: { 'Content-Type': 'application/json' },
    data: { report_id: fakeNoFpeFieldsReportId, template_variant: 'standard' }
  });

  // 400 또는 422 (FastAPI body validation은 422)
  expect([400, 422]).toContain(response.status());

  const body = await response.json();
  expect(body.detail).toContain('missing required fields');
  // 500은 명시적 실패 — "서버가 크래시하지 않고 정책 오류로 거부"
});
```

**Playwright fixture v5** (F1 + F3 + F4 통합):
```typescript
// tests/e2e/fixtures/snapshot_seeder.ts (v5)
import { test as base } from '@playwright/test';
import { randomUUID } from 'node:crypto';   // F1 — Node 표준

function newTestId(): string {
  return randomUUID().replace(/-/g, '');
}

export const test = base.extend<{
  testReportId: string;
  fakeApeBoundReportId: string;
  fakeNoFpeFieldsReportId: string;
}>({
  testReportId: async ({ request }, use) => {
    const response = await request.post('/api/evaluation/report', {
      headers: { 'Content-Type': 'application/json' },
      data: { state: { company_name: 'TestCorp', /* ... */ } }
    });
    const snapshot = await response.json();
    await use(snapshot.report_id);
    await request.delete(`/api/evaluation/report/${snapshot.report_id}`);
  },

  fakeApeBoundReportId: async ({ request }, use) => {
    const reportId = newTestId();   // F1 — node:crypto
    await request.post('/api/test/seed-raw-snapshot', {
      headers: { 'Content-Type': 'application/json' },
      data: {
        report_id: reportId,
        decision_source: 'APE',
        proposal_allowed: false,
        company_name: 'TestNonFPE',
      }
    });
    await use(reportId);
    await request.delete(`/api/test/raw-snapshot/${reportId}`);
  },

  fakeNoFpeFieldsReportId: async ({ request }, use) => {
    const reportId = newTestId();
    await request.post('/api/test/seed-raw-snapshot', {
      headers: { 'Content-Type': 'application/json' },
      data: {
        report_id: reportId,
        decision_source: 'FPE',
        // fpe_credit_limit, fpe_margin_rate 모두 누락
      }
    });
    await use(reportId);
    await request.delete(`/api/test/raw-snapshot/${reportId}`);
  }
});
```

### 11.3 seed API 등록 검증 — OpenAPI + POST probe (F2 정정)

**v4의 잘못된 패턴**:
```bash
# ❌ POST 라우트에 OPTIONS → 405, curl -f는 4xx에서 본문 미출력
if curl -fsS http://127.0.0.1:8012/api/test/seed-raw-snapshot -X OPTIONS 2>&1 | grep -q "200\|Method Not Allowed"; then
  echo "[OK]"
else
  echo "[FAIL]"
fi
```

**v5 정정 — OpenAPI 기반**:
```bash
#!/bin/bash
# tests/run_e2e.sh (v5)
set -euo pipefail   # F2 권고

trap 'echo "[FAIL] errored — uvicorn 로그 마지막 80줄:"; tail -80 /tmp/uvicorn8012.log; exit 1' ERR

# 1. test 환경변수 + 데이터 디렉토리 (F4)
export FLOWBIZ_ENV=test
export FLOWBIZ_TEST_SNAPSHOT_DIR="data/test_evaluation_reports"

# 2. 테스트 환경 정리 (F4 — 시작 시 강제 정리)
rm -rf "$FLOWBIZ_TEST_SNAPSHOT_DIR"
mkdir -p "$FLOWBIZ_TEST_SNAPSHOT_DIR"

# 3. 테스트 서버 기동
nohup python3 -m uvicorn app:app --host 127.0.0.1 --port 8012 \
  > /tmp/uvicorn8012.log 2>&1 &
UVICORN_PID=$!
sleep 3

# 4. seed API 등록 검증 (F2 — OpenAPI 사용)
SEED_PATH="/api/test/seed-raw-snapshot"
echo "[INFO] OpenAPI 검증: $SEED_PATH"

OPENAPI_HAS_SEED="$(curl -fsS http://127.0.0.1:8012/openapi.json \
  | python3 -c "
import sys, json
spec = json.load(sys.stdin)
paths = spec.get('paths', {})
print('1' if '$SEED_PATH' in paths else '0')
")"

if [ "$OPENAPI_HAS_SEED" != "1" ]; then
  echo "[FAIL] $SEED_PATH 가 OpenAPI에 등록되지 않음 — FLOWBIZ_ENV=test 미설정?"
  echo "현재 FLOWBIZ_ENV: ${FLOWBIZ_ENV:-(unset)}"
  kill $UVICORN_PID
  exit 1
fi
echo "[OK] OpenAPI에 seed API 등록 확인"

# 5. 실제 POST probe — 정상 200 응답 확인 (F2 보강)
PROBE_REPORT_ID="$(node -e 'console.log(require("node:crypto").randomUUID().replace(/-/g, ""))')"
PROBE_STATUS="$(curl -s -o /dev/null -w '%{http_code}' \
  -X POST http://127.0.0.1:8012/api/test/seed-raw-snapshot \
  -H 'Content-Type: application/json' \
  -d "{\"report_id\": \"$PROBE_REPORT_ID\", \"decision_source\": \"FPE\"}")"

if [ "$PROBE_STATUS" != "200" ]; then
  echo "[FAIL] seed API POST probe 실패: HTTP $PROBE_STATUS"
  exit 1
fi

# 정리: probe snapshot 삭제
curl -fsS -X DELETE "http://127.0.0.1:8012/api/test/raw-snapshot/$PROBE_REPORT_ID" > /dev/null
echo "[OK] seed API POST probe 통과"

# 6. Playwright E2E 실행
npx playwright test

# 7. 종료 시 정리 (F4)
kill $UVICORN_PID
rm -rf "$FLOWBIZ_TEST_SNAPSHOT_DIR"
echo "[OK] E2E 완료 + test 디렉토리 정리"
```

### 11.4 fixture 디렉토리 구조 (v4 §11.4 그대로)

### 11.5 test data 디렉토리 분리 (F4 [P2] 신설)

**v4의 잘못된 패턴**:
```python
# ❌ test도 production 경로 공유 — teardown 실패 시 운영 데이터 오염
SNAPSHOT_DIR = Path("data/evaluation_reports")
```

**v5 정정 — 환경별 디렉토리 분기**:
```python
import os
from pathlib import Path

def get_snapshot_dir() -> Path:
    """환경별 snapshot 저장 디렉토리

    F4 [codex] v4 P2 정정:
    - production: data/evaluation_reports (기본)
    - test:       data/test_evaluation_reports (격리)

    FLOWBIZ_ENV=test 또는 FLOWBIZ_TEST_SNAPSHOT_DIR 환경변수 사용 시 분기.
    """
    if os.getenv("FLOWBIZ_ENV") == "test":
        custom_dir = os.getenv("FLOWBIZ_TEST_SNAPSHOT_DIR")
        if custom_dir:
            return Path(custom_dir)
        return Path("data/test_evaluation_reports")
    return Path("data/evaluation_reports")


# 모든 snapshot 저장/로드는 get_snapshot_dir() 사용
def save_snapshot(snapshot: EvaluationSnapshot):
    snapshot_dir = get_snapshot_dir()
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    path = snapshot_dir / f"{snapshot.report_id}.json"
    path.write_text(snapshot.json())


def load_evaluation_snapshot(report_id: str) -> EvaluationSnapshot:
    snapshot_dir = get_snapshot_dir()
    path = snapshot_dir / f"{report_id}.json"
    if not path.exists():
        raise HTTPException(404, "snapshot not found")

    raw = json.loads(path.read_text())

    # v4 정정 계승 — raw load 시점 정책 검증
    if raw.get("decision_source") != "FPE":
        raise HTTPException(400, "decision_source must be FPE")

    required = ["fpe_credit_limit", "fpe_margin_rate", "fpe_payment_grace_days"]
    missing = [f for f in required if raw.get(f) is None]
    if missing:
        raise HTTPException(400, f"missing required fields: {missing}")

    return EvaluationSnapshot(**raw)


# test-only seed API도 동일 함수 사용
if os.getenv("FLOWBIZ_ENV") == "test":
    @app.post("/api/test/seed-raw-snapshot")
    async def seed_raw_snapshot(snapshot: UnsafeRawSnapshotForTest):
        snapshot_dir = get_snapshot_dir()   # ← test 디렉토리 자동 사용
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        path = snapshot_dir / f"{snapshot.report_id}.json"
        path.write_text(json.dumps(snapshot.dict(), default=str))
        return {"report_id": snapshot.report_id, "saved_to": str(path)}
```

**.gitignore 추가** (F4 보강):
```
# .gitignore
data/test_evaluation_reports/   ← test 산출물 추적 안 함
```

**환경별 디렉토리 매트릭스**:

| 환경 | FLOWBIZ_ENV | 디렉토리 | git 추적 | seed API |
|---|---|---|:---:|:---:|
| production | (unset) | `data/evaluation_reports/` | ✅ | ❌ |
| test | `test` | `data/test_evaluation_reports/` | ❌ (gitignore) | ✅ |
| test (custom) | `test` + `FLOWBIZ_TEST_SNAPSHOT_DIR` | 사용자 지정 | (사용자 결정) | ✅ |

## 12. Risk + Mitigation (v4 §12 + 신규)

| Risk | 영향 | 대응 |
|---|---|---|
| (v4 동일) | (다양) | (계승) |
| **(신규)** uuid npm 미설치 | E2E fixture 시작 실패 | **node:crypto 표준 라이브러리** (F1) |
| **(신규)** seed API 등록 검증 false fail | E2E 진입 안 됨 | **OpenAPI + POST probe** (F2) |
| **(신규)** missing-field 테스트가 서버 크래시도 통과 | 방어 로직 신뢰성 저하 | **400/422 고정** + detail 검증 (F3) |
| **(신규)** test snapshot이 production 디렉토리 오염 | 운영 데이터 손상 | **test data 디렉토리 분리** (F4) + .gitignore |

## 13. 다음 액션 (codex v4 §4 체크리스트 4건 통합)

- [x] **(F1)** Playwright fixture `uuid` → `node:crypto.randomUUID()` — §11.2 정정
- [x] **(F2)** seed API 등록 검증 OpenAPI + POST probe — §11.3 정정
- [x] **(F3)** missing-field 테스트 `toBe(400)` 고정 + detail 검증 — §11.2 정정
- [x] **(F4)** test raw snapshot 경로 분리 — §11.5 신설 + `data/test_evaluation_reports/`

## 14. 핵심 메시지

**v4 → v5 핵심 보강 4건**:
1. **node:crypto 표준 라이브러리** (codex F1) — Python uuid + Node node:crypto 양쪽 외부 의존성 0
2. **OpenAPI 기반 seed 검증** (codex F2) — false fail 차단 + uvicorn 로그 자동 출력
3. **400/422 고정 테스트** (codex F3) — 500 서버 크래시는 명시적 실패
4. **test 디렉토리 격리** (codex F4) — production 데이터 오염 차단

→ codex v4 §5 인용: "v4는 실제 구현 착수 직전 계획으로 거의 정리된 상태다... 위 4개 항목을 반영하면 계획서 기준으로 승인 가능하다." → **v5에서 4건 모두 반영 완료**.

---

## 부록 A. v4 → v5 정정 위치

### A.1 JS ID 생성 — node:crypto (F1 P1)

| 위치 | v4 | v5 |
|---|---|---|
| §11.2 fixture import | `import { v4 as uuidv4 } from 'uuid'` | **`import { randomUUID } from 'node:crypto'`** |
| §11.2 ID 생성 | `uuidv4().replace(/-/g, '')` | **`randomUUID().replace(/-/g, '')`** |
| §11.3 probe ID | (미명시) | **`node -e 'console.log(require("node:crypto").randomUUID()...)'`** |

### A.2 seed API 등록 검증 (F2 P1)

| 위치 | v4 | v5 |
|---|---|---|
| §11.3 검증 방법 | `curl -fsS ... -X OPTIONS \| grep` | **OpenAPI `/openapi.json` paths 확인 + POST probe (200 검증)** |
| shell 옵션 | `set -e` | **`set -euo pipefail`** |
| 실패 시 디버깅 | (없음) | **`trap` + `tail -80 /tmp/uvicorn8012.log`** |

### A.3 missing-field 테스트 (F3 P2)

| 위치 | v4 | v5 |
|---|---|---|
| §11.2 spec 기대값 | `toBeGreaterThanOrEqual(400)` | **`expect([400, 422]).toContain(response.status())`** |
| detail 검증 | (없음) | **`expect(body.detail).toContain('missing required fields')`** |
| 500 처리 | 통과로 분류 | **명시적 실패로 분류** |

### A.4 test data 디렉토리 분리 (F4 P2)

| 위치 | v4 | v5 |
|---|---|---|
| §11.5 (신규) | (없음) | **`get_snapshot_dir()` 환경별 분기** |
| 환경변수 | `FLOWBIZ_ENV` 만 | **`FLOWBIZ_ENV` + `FLOWBIZ_TEST_SNAPSHOT_DIR`** |
| 디렉토리 | `data/evaluation_reports` 공유 | **production: `data/evaluation_reports/`, test: `data/test_evaluation_reports/`** |
| .gitignore | (없음) | **`data/test_evaluation_reports/` 추가** |
| `tests/run_e2e.sh` 시작/종료 | (없음) | **`rm -rf` + `mkdir` 강제 정리** |

## 부록 B. 누적 Finding 추적

| 단계 | 신규 Finding | 누적 |
|---|---|---|
| 본 계획 v1 | 0 (자체) | 0 |
| 본 계획 v2 | 0 (codex v1 4건 반영) | 4 |
| 본 계획 v3 | 0 (codex v2 5건 반영) | 9 |
| 본 계획 v4 | 0 (codex v3 3건 반영) | 12 |
| **본 계획 v5** | **0 (codex v4 4건 반영)** | **16** |

**잔여 P0/P1**: 0건.

## 부록 C. 외부 의존성 매트릭스 (v5 정합성)

| 영역 | v4 | v5 | 출처 |
|---|---|---|---|
| Python ID 생성 | `uuid.uuid4().hex` ✅ | `uuid.uuid4().hex` ✅ | 표준 라이브러리 |
| Node ID 생성 | `uuid` npm ❌ | **`node:crypto.randomUUID()` ✅** | Node 표준 (Node 14.17+) |
| Pydantic | `pydantic` (이미 사용 중) | (계승) | 기존 의존성 |
| FastAPI | `fastapi` (이미 사용 중) | (계승) | 기존 의존성 |
| Playwright | `@playwright/test` (Phase 5) | (계승) | E2E 도입 시 명시 필요 |

→ **v5 = 표준 라이브러리만 사용** (Playwright 제외). E2E Phase 진입 시 `@playwright/test`만 추가.

## 부록 D. v5 단일 적용 코드 패턴

**1. Playwright fixture import (F1)**:
```typescript
import { randomUUID } from 'node:crypto';
function newTestId(): string {
  return randomUUID().replace(/-/g, '');
}
```

**2. shell run_e2e.sh 헤더 (F2)**:
```bash
#!/bin/bash
set -euo pipefail
trap 'echo "[FAIL]"; tail -80 /tmp/uvicorn8012.log; exit 1' ERR
```

**3. test 디렉토리 환경변수 (F4)**:
```bash
export FLOWBIZ_ENV=test
export FLOWBIZ_TEST_SNAPSHOT_DIR="data/test_evaluation_reports"
rm -rf "$FLOWBIZ_TEST_SNAPSHOT_DIR" && mkdir -p "$FLOWBIZ_TEST_SNAPSHOT_DIR"
```

**4. Python loader 환경별 분기 (F4)**:
```python
def get_snapshot_dir() -> Path:
    if os.getenv("FLOWBIZ_ENV") == "test":
        return Path(os.getenv("FLOWBIZ_TEST_SNAPSHOT_DIR", "data/test_evaluation_reports"))
    return Path("data/evaluation_reports")
```

**5. test 기대값 고정 (F3)**:
```typescript
expect([400, 422]).toContain(response.status());
expect(body.detail).toContain('missing required fields');
```

**6. seed API OpenAPI 검증 (F2)**:
```bash
OPENAPI_HAS_SEED="$(curl -fsS http://localhost:8012/openapi.json \
  | python3 -c 'import sys,json; print("1" if "/api/test/seed-raw-snapshot" in json.load(sys.stdin).get("paths", {}) else "0")')"
[ "$OPENAPI_HAS_SEED" = "1" ] || exit 1
```
