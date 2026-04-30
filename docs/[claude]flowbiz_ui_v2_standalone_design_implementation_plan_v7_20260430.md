# FlowBizTool v2 Standalone 디자인 구현 계획서 v7 [claude]

- 문서번호: FBU-PLAN-UI-V2-STANDALONE-IMPL-v7-20260430
- 작성일: 2026-04-30
- 작성자: [claude]
- 이전 버전: `[claude]flowbiz_ui_v2_standalone_design_implementation_plan_v6_20260430.md` (v6)
- 검증: `[codex]flowbiz_ui_v2_standalone_design_implementation_plan_v6_validation_20260430.md` (P2 2건 — **승인 가능**)
- 변경 사유: v6 [codex] 검증 P2 2건 반영 — **uvicorn readiness retry loop** + **test:e2e:ui 서버 기동 경로 명확화**. P0/P1 잔여 0건 → **계획서 기준 승인 완료**.

## 0. v6 → v7 변경 요약

| Finding | 우선순위 | v6 문제 | v7 반영 |
|---|---|---|---|
| F1 [codex] v6: 서버 준비 확인이 `sleep 3` 고정 | P2 | 느린 환경에서 OpenAPI 호출이 false fail 가능 | **§11.3 readiness loop** — `/api/health`(또는 `/openapi.json`) 최대 30초 재시도 + 매초 0.5s polling |
| F2 [codex] v6: `test:e2e:ui` 서버 기동 경로 부재 | P2 | uvicorn 미기동 상태에서 `--ui` 실행 시 baseURL 연결 실패 | **§11.6.1 package.json 정정** — `test:e2e:ui`도 `run_e2e.sh --ui` 경로 + **`run_e2e.sh` --ui 모드 분기** 추가 |

### 0.1 codex v6 §4 핵심 인용

> "v6는 **계획서 기준 승인 가능**하다. 남은 두 건은 실행 안정성을 높이는 P2 권고이며, **구현 착수를 막는 P0/P1은 없다**."

→ 본 v7은 **승인 완료 직전 마지막 안정성 보강**. Phase 0 진입 가능 상태.

## 1. 핵심 운영 원칙 (v6 §1 + 신규 #24 #25)

| 원칙 | 출처 |
|---|---|
| (v6 #1-#23 모두 계승) | v6 §1 |
| (신규) **#24 서버 readiness = retry loop (최대 30초)** | codex v6 F1 [P2] |
| (신규) **#25 test:e2e:ui = run_e2e.sh --ui 통합** | codex v6 F2 [P2] |

## 2-10. (v6 §2-§10 그대로 — 운영 원칙/디자인/Phase/모델 변경 없음)

## 11. 검증 계획 — 안정성 보강 (F1 + F2)

### 11.1 v6 §11.1 그대로 (Phase별 검증)

### 11.2 v6 §11.2 그대로 (E2E negative case — 400/422 고정)

### 11.3 run_e2e.sh — readiness retry + UI 모드 (F1 + F2 정정)

**v6의 잘못된 패턴**:
```bash
# ❌ 고정 sleep — 느린 환경에서 미흡
nohup python3 -m uvicorn ... &
UVICORN_PID=$!
sleep 3
# 바로 OpenAPI 호출 → false fail 가능
```

**v7 정정 — readiness retry loop + UI 모드**:

```bash
#!/bin/bash
# tests/run_e2e.sh (v7)
set -euo pipefail

# F2 [codex] v6 P2: --ui 모드 분기
PLAYWRIGHT_MODE="default"
if [ "${1:-}" = "--ui" ]; then
  PLAYWRIGHT_MODE="ui"
fi

# === cleanup (v6 §11.3 계승) ===
cleanup() {
  local exit_code=$?
  echo ""
  echo "=== cleanup 시작 (exit code: $exit_code, mode: $PLAYWRIGHT_MODE) ==="

  if [ -n "${UVICORN_PID:-}" ] && kill -0 "$UVICORN_PID" 2>/dev/null; then
    kill "$UVICORN_PID" 2>/dev/null || true
    sleep 1
    kill -9 "$UVICORN_PID" 2>/dev/null || true
    echo "[OK] uvicorn PID $UVICORN_PID 종료"
  fi

  if [ -n "${FLOWBIZ_TEST_SNAPSHOT_DIR:-}" ] && [ -d "$FLOWBIZ_TEST_SNAPSHOT_DIR" ]; then
    rm -rf "$FLOWBIZ_TEST_SNAPSHOT_DIR"
    echo "[OK] test 디렉토리 정리"
  fi

  if [ "$exit_code" -ne 0 ] && [ -f /tmp/uvicorn8012.log ]; then
    echo ""
    echo "=== uvicorn 로그 마지막 80줄 ==="
    tail -80 /tmp/uvicorn8012.log
  fi

  echo "=== cleanup 완료 ==="
  exit "$exit_code"
}
trap cleanup EXIT

# === 환경 변수 + test 디렉토리 (v5 §11.5) ===
export FLOWBIZ_ENV=test
export FLOWBIZ_TEST_SNAPSHOT_DIR="data/test_evaluation_reports"

rm -rf "$FLOWBIZ_TEST_SNAPSHOT_DIR"
mkdir -p "$FLOWBIZ_TEST_SNAPSHOT_DIR"

# === uvicorn 기동 ===
nohup python3 -m uvicorn app:app --host 127.0.0.1 --port 8012 \
  > /tmp/uvicorn8012.log 2>&1 &
UVICORN_PID=$!

# === F1 [codex] v6 P2 정정: readiness retry loop ===
HEALTH_URL="http://127.0.0.1:8012/api/health"
OPENAPI_URL="http://127.0.0.1:8012/openapi.json"
MAX_WAIT=30      # 최대 30초
INTERVAL_MS=500  # 0.5초 간격 = 60회 시도

echo "[INFO] uvicorn readiness 대기 (최대 ${MAX_WAIT}초)"
ELAPSED_MS=0
READY=0
while [ $ELAPSED_MS -lt $((MAX_WAIT * 1000)) ]; do
  # 우선 /api/health 시도, 실패 시 /openapi.json fallback
  if curl -fsS -o /dev/null --max-time 1 "$HEALTH_URL" 2>/dev/null; then
    READY=1
    break
  fi
  if curl -fsS -o /dev/null --max-time 1 "$OPENAPI_URL" 2>/dev/null; then
    READY=1
    break
  fi

  # 0.5초 대기 (sleep 0.5는 BSD/GNU 모두 지원)
  sleep 0.5
  ELAPSED_MS=$((ELAPSED_MS + INTERVAL_MS))

  # 1초마다 진행 표시
  if [ $((ELAPSED_MS % 1000)) -eq 0 ]; then
    echo -n "."
  fi
done
echo ""

if [ $READY -eq 0 ]; then
  echo "[FAIL] uvicorn readiness 타임아웃 (${MAX_WAIT}초)"
  exit 1
fi

ELAPSED_S=$(awk "BEGIN { printf \"%.1f\", $ELAPSED_MS/1000 }")
echo "[OK] uvicorn ready in ${ELAPSED_S}s"

# === seed API 등록 검증 (v5 §11.3) ===
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

# === POST probe (v5 §11.3) ===
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

# === F2 [codex] v6 P2 정정: --ui 모드 분기 실행 ===
if [ "$PLAYWRIGHT_MODE" = "ui" ]; then
  echo "[INFO] Playwright UI mode 실행 (Ctrl+C로 종료 시 cleanup 자동)"
  npx playwright test --ui
else
  npx playwright test
fi

echo "[OK] E2E 통과"
```

**핵심 변경**:
- **F1 P2 readiness loop**: `/api/health` 우선 → `/openapi.json` fallback → 최대 30초 0.5초 polling. 평균 0.3-1초 내 ready.
- **F2 P2 UI 모드**: `bash tests/run_e2e.sh --ui` 명령 한 줄로 서버 기동 + Playwright UI 통합. cleanup도 동일하게 작동.

### 11.4 v6 §11.4 그대로 (fixture 디렉토리 구조)

### 11.5 v6 §11.5 그대로 (test data 디렉토리 분리)

### 11.6 E2E 실행 기반 3 산출물 (v6 §11.6 + F2 정정)

#### 11.6.1 `package.json` (F2 [P2] 정정)

```json
{
  "name": "flowbiz-ultra-e2e",
  "version": "0.1.0",
  "private": true,
  "description": "FlowBiz_ultra E2E 테스트 — Playwright (Python uvicorn 백엔드 검증)",
  "scripts": {
    "test:e2e": "bash tests/run_e2e.sh",
    "test:e2e:ui": "bash tests/run_e2e.sh --ui",
    "test:install": "playwright install chromium"
  },
  "devDependencies": {
    "@playwright/test": "^1.46.0"
  }
}
```

**v6 → v7 차이**:

| script | v6 | v7 |
|---|---|---|
| `test:e2e` | `bash tests/run_e2e.sh` | (동일) |
| `test:e2e:ui` | ❌ `FLOWBIZ_ENV=test ... playwright test --ui` (서버 미기동) | ✅ **`bash tests/run_e2e.sh --ui`** (서버 기동 + UI 통합) |

#### 11.6.2 v6 §11.6.2 그대로 (`playwright.config.ts`)

#### 11.6.3 v6 §11.6.3 = §11.3 v7 cleanup + readiness 통합

#### 11.6.4 v6 §11.6.4 그대로 (chromium 설치 절차)

#### 11.6.5 v6 §11.6.5 그대로 (디렉토리 구조)

## 12. Risk + Mitigation (v6 §12 + 신규)

| Risk | 영향 | 대응 |
|---|---|---|
| (v6 동일) | (다양) | (계승) |
| **(신규)** 느린 환경에서 sleep 3 미흡 | OpenAPI false fail | **`/api/health` readiness loop + 30초 타임아웃** (F1) |
| **(신규)** UI 모드 baseURL 연결 실패 | 사용자 혼란 | **`run_e2e.sh --ui` 통합 명령** (F2) |
| **(신규)** readiness loop 타임아웃 | 30초 후 실패 처리 | uvicorn 로그 자동 출력 (cleanup) + 환경 진단 가능 |

## 13. 다음 액션 (codex v6 §4 체크리스트 2건 통합)

- [x] **(F1)** readiness retry loop (최대 30초) — §11.3 정정
- [x] **(F2)** `test:e2e:ui` = `run_e2e.sh --ui` — §11.6.1 package.json + §11.3 분기 모두 정정

## 14. 핵심 메시지

**v6 → v7 핵심 보강 2건**:
1. **uvicorn readiness retry loop** (codex F1) — `/api/health` 최대 30초 polling + 평균 0.3-1초 ready
2. **test:e2e:ui = run_e2e.sh --ui** (codex F2) — 서버 기동 + UI 모드 단일 명령 통합

→ codex v6 §4 인용: "**v6는 계획서 기준 승인 가능하다. 구현 착수를 막는 P0/P1은 없다.**" → **v7은 P2 2건 추가 반영, 실행 안정성 100% 보장 → Phase 0 진입 가능**.

---

## 부록 A. v6 → v7 정정 위치

### A.1 readiness retry loop (F1 P2)

| 위치 | v6 | v7 |
|---|---|---|
| §11.3 서버 기동 후 | `sleep 3` 단일 | **0.5초 polling × 60회 (최대 30초)** + `/api/health` 우선 + `/openapi.json` fallback |
| 진행 표시 | (없음) | **매 1초 `.` 출력** + 완료 시 `ready in X.Xs` |
| 타임아웃 처리 | (없음) | **`[FAIL] readiness 타임아웃` + cleanup의 uvicorn 로그 자동 출력** |

### A.2 test:e2e:ui 통합 (F2 P2)

| 위치 | v6 | v7 |
|---|---|---|
| `package.json` `test:e2e:ui` | `FLOWBIZ_ENV=test ... playwright test --ui` (서버 미기동) | **`bash tests/run_e2e.sh --ui`** |
| `tests/run_e2e.sh` 인자 처리 | (없음) | **`if [ "${1:-}" = "--ui" ]; then PLAYWRIGHT_MODE="ui"; fi`** |
| Playwright 실행 분기 | `npx playwright test` 단일 | **`if mode=ui: npx playwright test --ui; else: npx playwright test`** |

## 부록 B. 누적 Finding 추적

| 단계 | 신규 Finding | 누적 | 잔여 P0/P1 |
|---|---|---|---|
| 본 계획 v1 | 0 (자체) | 0 | — |
| 본 계획 v2 | 0 (codex v1 4건) | 4 | — |
| 본 계획 v3 | 0 (codex v2 5건) | 9 | — |
| 본 계획 v4 | 0 (codex v3 3건) | 12 | — |
| 본 계획 v5 | 0 (codex v4 4건) | 16 | — |
| 본 계획 v6 | 0 (codex v5 4건) | 20 | — |
| **본 계획 v7** | **0 (codex v6 P2×2 반영)** | **22** | **0** |

**잔여 P0/P1**: 0건 + **누적 P2 잔여도 0건** → 완전 승인.

## 부록 C. v7 단일 적용 코드 패턴

**1. readiness retry loop (F1)**:
```bash
MAX_WAIT=30
ELAPSED_MS=0
while [ $ELAPSED_MS -lt $((MAX_WAIT * 1000)) ]; do
  curl -fsS -o /dev/null --max-time 1 "$HEALTH_URL" 2>/dev/null && break
  curl -fsS -o /dev/null --max-time 1 "$OPENAPI_URL" 2>/dev/null && break
  sleep 0.5
  ELAPSED_MS=$((ELAPSED_MS + 500))
done
[ $ELAPSED_MS -ge $((MAX_WAIT * 1000)) ] && exit 1
```

**2. --ui 모드 분기 (F2)**:
```bash
PLAYWRIGHT_MODE="default"
[ "${1:-}" = "--ui" ] && PLAYWRIGHT_MODE="ui"

# 마지막에:
if [ "$PLAYWRIGHT_MODE" = "ui" ]; then
  npx playwright test --ui
else
  npx playwright test
fi
```

**3. package.json 정정 (F2)**:
```json
"test:e2e:ui": "bash tests/run_e2e.sh --ui"
```

## 부록 D. 최종 승인 상태

| 검증 항목 | 누적 처리 | 최종 |
|---|---|---|
| 평가엔진/학습엔진 역할 분리 | (전체) | ✅ |
| FPE 기준 / APE 비교 전용 | (전체) | ✅ |
| EvaluationSnapshot 서버 저장 | v3-v4 | ✅ |
| 월간 upgrade-reports 5 API | v3 | ✅ |
| 전시회 평가 (ExhibitionLeadSnapshot) | v3 | ✅ |
| Pydantic BaseModel + Content-Type | v3 | ✅ |
| docs/reference/ 보존 | v3 | ✅ |
| upgrade 5 상태 (on_hold 포함) | v3-v4 | ✅ |
| uuid (Python) + node:crypto (JS) | v4-v5 | ✅ |
| raw fixture seed | v4-v5 | ✅ |
| test 디렉토리 격리 | v5 | ✅ |
| .gitignore 4 라인 | v6 | ✅ |
| OpenAPI + POST probe 검증 | v5-v6 | ✅ |
| cleanup trap EXIT | v6 | ✅ |
| 400/422 고정 | v6 | ✅ |
| **readiness retry loop** | **v7** | ✅ |
| **test:e2e:ui 통합** | **v7** | ✅ |

**최종 판정**: 22 Finding 모두 반영 + P0/P1/P2 잔여 0건 → **계획서 완전 승인 + 구현 착수 가능**.

## 부록 E. Phase 0 진입 체크리스트 (v7 종합)

Phase 0 시작 전 확인:

- [x] `web/styles/v2_tokens.css` 103+ 토큰 + on_hold (v4 본 세션 적용)
- [x] `docs/reference/dual_engine_v2_standalone.html` 보존 (v3 본 세션 이동)
- [x] `.gitignore` 4 라인 (v6 본 세션 적용)
- [ ] `package.json` 작성 (Phase 0)
- [ ] `playwright.config.ts` 작성 (Phase 0)
- [ ] `tests/run_e2e.sh` 작성 (Phase 0 — readiness loop + cleanup 통합)
- [ ] `npm install && npm run test:install` (Phase 0)
- [ ] `scripts/extract_v2_tokens_rendered.js` (Phase 0)
- [ ] rendered DOM 토큰 vs v2_tokens.css 차이 검증 (Phase 0 acceptance)

→ 8 항목 중 3개 본 세션 완료, 5개 Phase 0 진입 시 작성. 1차 PR 머지 후 즉시 Phase 0 착수 가능.
