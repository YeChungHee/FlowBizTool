#!/bin/bash
#
# FlowBiz_ultra E2E 테스트 실행 스크립트
#
# 문서번호: FBU-PLAN-UI-V2-STANDALONE-IMPL-v7 §11.3 + §11.6.3
# 작성자:   [claude]
# 출처:     [claude]flowbiz_ui_v2_standalone_design_implementation_plan_v7_20260430.md
#
# 사용법:
#   bash tests/run_e2e.sh        # default 모드
#   bash tests/run_e2e.sh --ui   # Playwright UI 모드 (F2 [codex] v6 P2)
#
# 누적 반영 codex Findings:
#   v3 F1 P1: API request models (Pydantic)
#   v3 F4 P2: docs/reference/ 보관
#   v4 F4 P2: test_evaluation_reports/ 격리
#   v5 F2 P1: OpenAPI + POST probe
#   v5 F4 P2: test 디렉토리 분리
#   v6 F2 P1: cleanup trap EXIT
#   v6 F4 P2: 400/422 고정
#   v7 F1 P2: readiness retry loop
#   v7 F2 P2: --ui 모드 분기

set -euo pipefail

# ============================================================
# F2 [codex] v6 P2: --ui 모드 분기
# ============================================================
PLAYWRIGHT_MODE="default"
if [ "${1:-}" = "--ui" ]; then
  PLAYWRIGHT_MODE="ui"
fi

# ============================================================
# F2 [codex] v5 P1: cleanup trap EXIT
# ============================================================
cleanup() {
  local exit_code=$?

  echo ""
  echo "=== cleanup 시작 (exit code: $exit_code, mode: $PLAYWRIGHT_MODE) ==="

  # 1. uvicorn 프로세스 종료 (SIGTERM → 1초 → SIGKILL fallback)
  if [ -n "${UVICORN_PID:-}" ]; then
    if kill -0 "$UVICORN_PID" 2>/dev/null; then
      kill "$UVICORN_PID" 2>/dev/null || true
      sleep 1
      kill -9 "$UVICORN_PID" 2>/dev/null || true
      echo "[OK] uvicorn PID $UVICORN_PID 종료"
    fi
  fi

  # 2. test 디렉토리 정리 (성공/실패 무관)
  if [ -n "${FLOWBIZ_TEST_SNAPSHOT_DIR:-}" ] && [ -d "$FLOWBIZ_TEST_SNAPSHOT_DIR" ]; then
    rm -rf "$FLOWBIZ_TEST_SNAPSHOT_DIR"
    echo "[OK] test 디렉토리 $FLOWBIZ_TEST_SNAPSHOT_DIR 정리"
  fi

  # 3. 실패 시에만 uvicorn 로그 출력 (마지막 80줄)
  if [ "$exit_code" -ne 0 ] && [ -f /tmp/uvicorn8012.log ]; then
    echo ""
    echo "=== uvicorn 로그 마지막 80줄 ==="
    tail -80 /tmp/uvicorn8012.log
  fi

  echo "=== cleanup 완료 (exit code: $exit_code) ==="
  exit "$exit_code"
}
trap cleanup EXIT

# ============================================================
# 환경 변수 + test 디렉토리 (F4 [codex] v4 P2 + F4 [codex] v5)
# ============================================================
export FLOWBIZ_ENV=test
export FLOWBIZ_TEST_SNAPSHOT_DIR="data/test_evaluation_reports"

# 시작 시 강제 정리 (이전 실행 잔재)
rm -rf "$FLOWBIZ_TEST_SNAPSHOT_DIR"
mkdir -p "$FLOWBIZ_TEST_SNAPSHOT_DIR"
echo "[OK] test 디렉토리 초기화: $FLOWBIZ_TEST_SNAPSHOT_DIR"

# ============================================================
# uvicorn 기동
# ============================================================
nohup python3 -m uvicorn app:app --host 127.0.0.1 --port 8012 \
  > /tmp/uvicorn8012.log 2>&1 &
UVICORN_PID=$!
echo "[INFO] uvicorn 기동 (PID: $UVICORN_PID, port: 8012)"

# ============================================================
# F1 [codex] v6 P2: readiness retry loop (최대 30초)
# ============================================================
HEALTH_URL="http://127.0.0.1:8012/api/health"
OPENAPI_URL="http://127.0.0.1:8012/openapi.json"
MAX_WAIT=30
INTERVAL_MS=500

echo "[INFO] uvicorn readiness 대기 (최대 ${MAX_WAIT}초)"
ELAPSED_MS=0
READY=0
while [ $ELAPSED_MS -lt $((MAX_WAIT * 1000)) ]; do
  # /api/health 우선
  if curl -fsS -o /dev/null --max-time 1 "$HEALTH_URL" 2>/dev/null; then
    READY=1
    break
  fi
  # /openapi.json fallback (api/health 미존재 환경 대비)
  if curl -fsS -o /dev/null --max-time 1 "$OPENAPI_URL" 2>/dev/null; then
    READY=1
    break
  fi

  sleep 0.5
  ELAPSED_MS=$((ELAPSED_MS + INTERVAL_MS))

  # 1초마다 진행 표시
  if [ $((ELAPSED_MS % 1000)) -eq 0 ]; then
    printf "."
  fi
done
echo ""

if [ $READY -eq 0 ]; then
  echo "[FAIL] uvicorn readiness 타임아웃 (${MAX_WAIT}초)"
  exit 1
fi

ELAPSED_S=$(awk "BEGIN { printf \"%.1f\", $ELAPSED_MS/1000 }")
echo "[OK] uvicorn ready in ${ELAPSED_S}s"

# ============================================================
# F2 [codex] v5 P1: seed API 등록 검증 (OpenAPI)
# ============================================================
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
  echo "[FAIL] $SEED_PATH 가 OpenAPI에 등록되지 않음"
  echo "       FLOWBIZ_ENV=test 미설정 또는 seed API 미구현"
  echo "       현재 FLOWBIZ_ENV: ${FLOWBIZ_ENV:-(unset)}"
  exit 1
fi
echo "[OK] OpenAPI에 seed API 등록 확인"

# ============================================================
# F2 [codex] v5 P1: 실제 POST probe (200 검증)
# ============================================================
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
curl -fsS -X DELETE "http://127.0.0.1:8012/api/test/raw-snapshot/$PROBE_REPORT_ID" \
  > /dev/null 2>&1 || true
echo "[OK] seed API POST probe 통과"

# ============================================================
# F2 [codex] v6 P2: --ui 모드 분기 실행
# ============================================================
if [ "$PLAYWRIGHT_MODE" = "ui" ]; then
  echo "[INFO] Playwright UI mode 실행 (Ctrl+C로 종료 시 cleanup 자동)"
  npx playwright test --ui
else
  echo "[INFO] Playwright default mode 실행"
  npx playwright test
fi

# 정상 종료 시 cleanup 자동 호출 (trap EXIT)
echo "[OK] E2E 통과"
