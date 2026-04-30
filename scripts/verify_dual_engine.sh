#!/usr/bin/env bash
# v2.11 Step 12: 종합 검증 (set -euo pipefail + 모든 검증 명시 실패 처리)
set -euo pipefail

cd "$(dirname "$0")/.."

DATE=$(date +%Y%m%d)
OUT_DIR="outputs/dual_engine_$DATE"
mkdir -p "$OUT_DIR"

echo "=== 1. 서버 health check ==="
SERVER_URL="${DUAL_SERVER_URL:-http://127.0.0.1:8012}"
if ! curl -fsS "$SERVER_URL/api/engine/list" -o /dev/null 2>&1; then
  echo "[FAIL] $SERVER_URL not ready"
  echo "  서버 기동: python3 -m uvicorn app:app --host 127.0.0.1 --port 8012 &"
  exit 1
fi

ENGINE_IDS=$(curl -fsS "$SERVER_URL/api/engine/list" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(' '.join(e.get('engine_id','') for e in d.get('engines',[])))")
ENGINE_IDS_UP=$(echo "$ENGINE_IDS" | tr '[:lower:]' '[:upper:]')
if ! echo "$ENGINE_IDS_UP" | grep -qw "FPE" || ! echo "$ENGINE_IDS_UP" | grep -qw "APE"; then
  echo "[FAIL] 듀얼 엔진 미적용 (engines: '$ENGINE_IDS')"
  exit 1
fi
echo "[OK] $SERVER_URL ready (engines: $ENGINE_IDS)"

echo ""
echo "=== 2. 전체 pytest ==="
python3 -m pytest tests/ -q 2>&1 | tee "$OUT_DIR/pytest_full.log"
PYTEST_STATUS=${PIPESTATUS[0]}
[ "$PYTEST_STATUS" -eq 0 ] || { echo "[FAIL] pytest"; exit 1; }

echo ""
echo "=== 3. closure 3구역 disjoint ==="
python3 scripts/extract_engine_closures.py | tee "$OUT_DIR/closures.log"
CLOSURE_STATUS=${PIPESTATUS[0]}
[ "$CLOSURE_STATUS" -eq 0 ] || { echo "[FAIL] closure"; exit 1; }
grep -q '\[FAIL\]' "$OUT_DIR/closures.log" && { echo "[FAIL] closure 출력에 [FAIL]"; exit 1; } || true

echo ""
echo "=== 4. Node helper test ==="
node scripts/test_dual_eval_helpers.js | tee "$OUT_DIR/node_helper.log"
NODE_STATUS=${PIPESTATUS[0]}
[ "$NODE_STATUS" -eq 0 ] || { echo "[FAIL] Node helper"; exit 1; }

echo ""
echo "=== 5. 듀얼 평가 4 consensus pytest ==="
python3 -m pytest tests/test_dual_consensus.py -v 2>&1 | tee "$OUT_DIR/consensus.log"
CONSENSUS_STATUS=${PIPESTATUS[0]}
[ "$CONSENSUS_STATUS" -eq 0 ] || { echo "[FAIL] consensus"; exit 1; }

echo ""
echo "=== 6. server_input_hash 변경 감지 ==="
H1=$(curl -fsS -X POST "$SERVER_URL/api/learning/evaluate/dual" \
  -H 'Content-Type: application/json' \
  -d '{"state": {"companyName":"X", "reportCreditGrade":"BB+"}}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin).get('server_input_hash',''))")
H2=$(curl -fsS -X POST "$SERVER_URL/api/learning/evaluate/dual" \
  -H 'Content-Type: application/json' \
  -d '{"state": {"companyName":"X", "financialFilterSignal":"CCC-"}}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin).get('server_input_hash',''))")
if [ -z "$H1" ] || [ -z "$H2" ] || [ "$H1" = "$H2" ]; then
  echo "[FAIL] server_input_hash: H1='$H1' H2='$H2'"
  exit 1
fi
echo "[OK] H1=$H1 H2=$H2 (다름)" | tee -a "$OUT_DIR/api_smoke.log"

echo ""
echo "=== 7. 6 HTML helper 로드 순서 ==="
HTMLS=$(grep -l 'bizaipro_shared\.js' web/*.html)
ALL_OK=1
for f in $HTMLS; do
  result=$(awk '
    /dual_eval_helpers\.js/ { dual=NR }
    /bizaipro_shared\.js/ { shared=NR }
    END {
      if (!dual) print "FAIL_NO_DUAL"
      else if (dual > shared) print "FAIL_ORDER"
      else print "OK"
    }
  ' "$f")
  if [ "$result" != "OK" ]; then
    echo "[FAIL] $f: $result" | tee -a "$OUT_DIR/html_load_order.log"
    ALL_OK=0
  fi
done
[ $ALL_OK -eq 1 ] || { echo "[FAIL] HTML helper 로드 순서"; exit 1; }
echo "[OK] 6 HTML helper 로드 정상" | tee -a "$OUT_DIR/html_load_order.log"

echo ""
echo "=== 8. circular import (4 경로) ==="
for cmd in \
  "import engine; from engines import list_engines" \
  "from engines import list_engines; import engine" \
  "from engines.fpe.eval import evaluate_fpe_v1601" \
  "from engines.ape.eval import evaluate_flowpay_underwriting" \
; do
  python3 -c "$cmd; print('OK')" || { echo "[FAIL] circular: $cmd"; exit 1; }
done
echo "[OK] 4 import 경로 통과"

echo ""
echo "=== 9. T24 baseline 회귀 (PASSED 라인만 비교, 실행 시간 제외) ==="
T24_BEFORE="$(find outputs -path '*/fpe_t24_before.log' -type f 2>/dev/null | sort -r | head -1 || true)"
[ -n "$T24_BEFORE" ] && [ -f "$T24_BEFORE" ] || { echo "[FAIL] T24 baseline log 부재"; exit 1; }

# 결과 라인만 비교 (실행 시간 줄 제외)
EXTRACT='grep -E "PASSED|FAILED|ERROR" | sort'
BEFORE_PASSED=$(grep -E "PASSED|FAILED|ERROR" "$T24_BEFORE" | sort)
NOW_PASSED=$(python3 -m pytest tests/test_regression.py::TestFPEV1601Engine -v 2>&1 | grep -E "PASSED|FAILED|ERROR" | sort)
if [ "$BEFORE_PASSED" != "$NOW_PASSED" ]; then
  echo "[FAIL] T24 결과 라인 다름:"
  echo "  before:"; echo "$BEFORE_PASSED" | sed 's/^/    /'
  echo "  now:";    echo "$NOW_PASSED"   | sed 's/^/    /'
  exit 1
fi
echo "$NOW_PASSED" | tee "$OUT_DIR/t24_diff.log" >/dev/null
echo "[OK] T24 4 케이스 모두 baseline과 동일 결과 (PASSED)"

echo ""
echo "[ALL OK] 9개 자동 검증 모두 통과 — 수동 체크리스트 5항목 진행 권장"
