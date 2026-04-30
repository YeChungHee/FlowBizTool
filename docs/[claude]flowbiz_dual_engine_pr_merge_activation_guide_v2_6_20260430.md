# 듀얼 엔진 PR 머지 → 라이브 활성화 가이드 v2.6 [claude]

- 문서번호: FBU-GUIDE-PR-MERGE-DUAL-v2_6-20260430
- 작성일: 2026-04-30
- 작성자: [claude]
- 이전 버전: `[claude]flowbiz_dual_engine_pr_merge_activation_guide_v2_5_20260430.md` (v2.5)
- 검증: `[codex]flowbiz_dual_engine_pr_merge_activation_guide_v2_5_validation_20260430.md` (P1 1건 / P2 1건 — **조건부 보류**)
- 변경 사유: v2.5 [codex] 검증 2건 반영 — **preflight grep 변수 대입을 awk로 전환** + **stash 복구를 stash@{0} 고정 → 메시지 기반 id 추출**

## 0. v2.5 → v2.6 변경 요약

| Finding | 우선순위 | v2.5 문제 | v2.6 반영 |
|---|---|---|---|
| F1 [codex] v2.5: preflight grep 변수 대입이 clean 상태에서 실패 | **P1** | `DIRTY="$(... \| grep -E ...)"` — clean 상태에서 grep exit code 1 → set -e 환경에서 변수 대입 단계 중단. v2.5의 "set -e 안전" 핵심 메시지와 모순 | **§2.1 + §5.0 + 부록 C 모든 preflight grep을 `awk '/pattern/ {print ...}'` 패턴으로 전환** + 부록 E.5 신설 ("`set -e` 안전 변수 대입 패턴") |
| F2 [codex] v2.5: stash 복구가 `stash@{0}` 고정 | P2 | Preflight B에서 추가 stash를 만들거나 사용자가 중간에 다른 stash 생성 시 `stash@{0}`이 `pre-option-A`가 아닐 수 있음 → 잘못된 변경 복구 위험 | **§5.3 stash 복구를 메시지 기반 id 추출로 변경** — `PRE_OPTION_STASH="$(git stash list \| awk -F: '/pre-option-A/ {print $1; exit}')"` + 미존재 시 차단 |

### 0.1 변경 효과 검증 (set -e 환경 시뮬레이션)

```bash
# v2.5 (실패 가능 — clean 상태)
set -e
DIRTY="$(git status --short | grep -E '^( M|A )')"   # ← clean 시 exit 1 → set -e 중단
echo "도달 못함"

# v2.6 (안전 — clean 상태)
set -e
DIRTY="$(git status --short | awk '/^( M|A |D |R |C |MM)/ {print}')"  # ← awk는 0 hit여도 exit 0
[ -z "$DIRTY" ] && echo "[OK] clean"
```

`awk`는 매칭 0건일 때도 exit code 0을 반환하므로 `set -e` 환경에서 변수 대입이 안전합니다.

## 1. 7개 승인 체크리스트 (v2.5 §1 계승)

```text
[ ] Preflight A: 옵션 A 직전 worktree 예상 외 tracked 변경 0 (§2.1)
[ ] 조건 1:     §2.3 옵션 A 4 파일 sed 변경 적용
[ ] 조건 2:     tests/test_engine_registry.py 24 passed 유지
[ ] 조건 3:     전체 테스트 통과
[ ] 조건 4:     PR 규모 재측정 후 v2.6/PR description 갱신
[ ] Preflight B: main checkout 직전 worktree 비어있음 (§5.0)
[ ] 조건 5:     머지 후 verify_dual_engine.sh 통과 + 7 consensus PASSED 입증
```

## 2. 조건 1+2+3 — 옵션 A 적용 자동화 블록

### 2.1 Preflight A — 옵션 A 직전 worktree 검증 (F1 [codex] v2.5 P1 — awk 패턴)

```bash
cd /Users/appler/Documents/COTEX/FlowBiz_ultra

# Preflight A: 옵션 A 예상 외 tracked 변경 차단 (set -e 안전)
EXPECTED_PATHS="engines/_base.py engines/ape/__init__.py engines/ape/README.md tests/test_engine_registry.py"

# F1 [codex] v2.5 정정: grep → awk (0 hit여도 exit 0)
DIRTY_TRACKED="$(git status --short | awk '/^ M/ {print $2}')"

UNEXPECTED=""
for f in $DIRTY_TRACKED; do
  case " $EXPECTED_PATHS " in
    *" $f "*) ;;  # expected — pass
    *) UNEXPECTED="$UNEXPECTED $f" ;;
  esac
done

if [ -n "$UNEXPECTED" ]; then
  echo "[STOP] Preflight A 실패 — 옵션 A 예상 외 tracked 변경 존재:"
  for f in $UNEXPECTED; do echo "  M $f"; done
  echo ""
  echo "처리 옵션 (택 1):"
  echo "  A. git stash push -u -m 'pre-option-A-\$(date +%Y%m%d-%H%M)' [pathspec...] (보존, 권장)"
  echo "  B. git checkout -- <파일>                                   (버림 — 주의)"
  echo "  C. git add <파일> && git commit -m '...'                     (별도 commit)"
  echo ""
  echo "처리 후 본 Preflight A 재실행 후 §2.3 sed 단계 진입"
  exit 1
fi
echo "[OK] Preflight A 통과 — 옵션 A pathspec 외 tracked 변경 0"
```

**현재 세션 실측 (v2.5와 동일)**:
```text
[STOP] Preflight A 실패 — 옵션 A 예상 외 tracked 변경 존재:
  M data/bizaipro_learning_registry.json
  M docs/flowbiz_ultra_validation_report_registry.md
  M tests/test_regression.py
  M web/bizaipro_shared.css
```

**권장 처리** (stash — pathspec 제한 사용):
```bash
git stash push -u -m "pre-option-A-$(date +%Y%m%d-%H%M)" \
  data/bizaipro_learning_registry.json \
  docs/flowbiz_ultra_validation_report_registry.md \
  tests/test_regression.py \
  web/bizaipro_shared.css
# → stash 메시지에 'pre-option-A' 포함 (§5.3 메시지 기반 복구용)
```

### 2.2 사전 측정

```bash
# PR 규모 사전 측정
git fetch origin
git diff origin/main...HEAD --stat | tail -1
# → 34 files changed, 15262 insertions(+), 55 deletions(-)  (예상)

# learning_proposal 사전 4 hit 확인 (exit-code 안전)
if ! grep -rqn "learning_proposal" engines tests app.py; then
  echo "[FAIL] 사전 0 hit — 이미 옵션 A 적용된 상태"
  exit 1
fi
echo "[OK] 사전 4 hit 기대 — 옵션 A 미적용 확인"
grep -rn "learning_proposal" engines tests app.py
```

### 2.3 4 파일 일괄 sed (macOS BSD sed 호환)

```bash
sed -i '' 's/learning_proposal/learning_comparison/g' \
  engines/_base.py \
  engines/ape/__init__.py \
  engines/ape/README.md \
  tests/test_engine_registry.py
```

### 2.4 변경 검증 (조건 2+3)

```bash
# learning_proposal 0 hit 확인
if grep -rqn "learning_proposal" engines tests app.py; then
  echo "[FAIL] learning_proposal 잔존"
  grep -rn "learning_proposal" engines tests app.py
  exit 1
fi
echo "[OK] learning_proposal 0 hit"

# learning_comparison 4 hit 확인
HIT="$(grep -rl "learning_comparison" engines tests | wc -l | tr -d ' ')"
if [ "$HIT" -ne 4 ]; then
  echo "[FAIL] learning_comparison hit count = $HIT (4 기대)"
  grep -rn "learning_comparison" engines tests
  exit 1
fi
echo "[OK] learning_comparison 4 파일 정정"

# 조건 2: registry 테스트 24 passed
python3 -m pytest tests/test_engine_registry.py -q

# 조건 3: 전체 회귀
python3 -m pytest tests/ -q
# → 106 passed, 7 skipped

# 보조
node scripts/test_dual_eval_helpers.js                # 16 passed
python3 scripts/extract_engine_closures.py            # 3구역 disjoint
```

### 2.5 commit + push (조건 1 완료)

```bash
git add -u engines/_base.py engines/ape/__init__.py engines/ape/README.md tests/test_engine_registry.py

git commit -m "fix: APE engine_purpose learning_proposal → learning_comparison (v2.1 F2 P1 + v2.2 [codex] F1 P1)

- engines/_base.py:20 META 주석
- engines/ape/__init__.py:37 engine_purpose 값
- engines/ape/README.md:12 README META 표
- tests/test_engine_registry.py:65 테스트 기대값

검증:
- grep learning_proposal: 0 hit
- grep learning_comparison: 4 hit
- pytest tests/test_engine_registry.py: 24 passed
- pytest tests/: 106 passed, 7 skipped"

git push origin codex/dual-engine-execution-20260430
```

## 3. 조건 4 — PR 규모 재측정 + v2.6 갱신

### 3.1 재측정 명령

```bash
cd /Users/appler/Documents/COTEX/FlowBiz_ultra
git fetch origin
git diff origin/main...HEAD --stat | tail -1
```

### 3.2 측정 결과 기록 (placeholder)

| 측정 시점 | 결과 |
|---|---|
| v2.3 [codex] | `34 files changed, 15262 insertions(+), 55 deletions(-)` |
| v2.4 [codex] | `34 files changed, 15262 insertions(+), 55 deletions(-)` (동일) |
| v2.5 [codex] | `34 files changed, 15262 insertions(+), 55 deletions(-)` (동일) |
| **본 v2.6 측정 (옵션 A 적용 후)** | **`<TBD: 옵션 A commit + push 후 갱신>`** |

### 3.3 갱신 위치 (4곳)

옵션 A 적용 + push 후 4곳 갱신:
- [ ] 본 가이드 §3.2
- [ ] 본 가이드 §6 매트릭스 끝
- [ ] `outputs/dual_engine_baseline_20260430/PR_DESCRIPTION.md`
- [ ] GitHub PR description (PR 생성 후)

> **예상**: v2.4/v2.5 [codex]에 따르면 4 파일 모두 이미 PR 포함 → 파일 수 변동 없음.

## 4. PR 생성 (조건 1~4 완료 후)

### 4.1 PR 생성 절차 (gh CLI 미설치 — 웹 UI)

1. 브라우저에서 PR 생성 URL 접속:
   ```
   https://github.com/YeChungHee/FlowBizTool/pull/new/codex/dual-engine-execution-20260430
   ```

2. PR 작성:
   - **Title**: `feat: dual engine v2.11 — engines/ separation + dual evaluation API + UI helper (engine_purpose: learning_comparison)`
   - **Description**: `outputs/dual_engine_baseline_20260430/PR_DESCRIPTION.md` + §3.2 재측정 수치
   - **Base**: `main`
   - **Head**: `codex/dual-engine-execution-20260430`

3. PR 생성 후 v2.7 갱신:
   ```diff
   - PR URL: TBD
   - PR 번호: TBD
   - PR 규모: TBD
   + PR URL: https://github.com/YeChungHee/FlowBizTool/pull/<번호>
   + PR 번호: #<번호>
   + PR 규모: <옵션 A 후 재측정 결과>
   ```

### 4.2 PR placeholder

```text
PR URL:    [TBD]
PR 번호:   [TBD]
PR 규모:   [TBD]
PR Base:   main
PR Head:   codex/dual-engine-execution-20260430 (e16b391 + 옵션 A commit)
```

## 5. 조건 5 — 머지 후 8011 서버 검증

### 5.0 Preflight B — main checkout 직전 worktree 검증 (F1 [codex] v2.5 P1 — awk 패턴)

```bash
cd /Users/appler/Documents/COTEX/FlowBiz_ultra

# F1 [codex] v2.5 정정: grep -E → awk (0 hit여도 exit 0)
DIRTY="$(git status --short | awk '/^( M|A |D |R |C |MM)/ {print}')"

if [ -n "$DIRTY" ]; then
  echo "[STOP] Preflight B 실패 — main checkout 차단 가능 변경 존재:"
  echo "$DIRTY"
  echo ""
  echo "처리 옵션 (택 1):"
  echo "  A. git stash push -u -m 'pre-main-checkout-\$(date +%Y%m%d-%H%M)' (권장)"
  echo "  B. git commit -m 'wip: ...' (별도 commit)"
  exit 1
fi
echo "[OK] Preflight B 통과 — main checkout 안전"
```

### 5.1 macOS 호환 재시작 + 검증 자동화

```bash
# 1. 머지된 main 동기화 (Preflight B 통과 후)
git checkout main && git pull origin main

# 2. macOS BSD 호환 재시작
PID="$(lsof -ti :8011 2>/dev/null || true)"
if [ -n "$PID" ]; then
  kill $PID
  sleep 1
fi
nohup python3 -m uvicorn app:app --host 127.0.0.1 --port 8011 > /tmp/uvicorn8011.log 2>&1 &
sleep 3

# 3. health check
curl -fsS http://127.0.0.1:8011/api/engine/list | python3 -m json.tool

# 4. learning_comparison 노출 검증 (exit-code 안전)
ENGINE_LIST="$(curl -fsS http://127.0.0.1:8011/api/engine/list)"
if echo "$ENGINE_LIST" | grep -q '"engine_purpose": "learning_comparison"'; then
  echo "[OK] APE engine_purpose: learning_comparison 노출 확인"
else
  echo "[FAIL] learning_comparison 미노출"
  echo "$ENGINE_LIST"
  exit 1
fi

# 5. 종합 검증 — 9 항목 [ALL OK] + 7 consensus PASSED
DUAL_SERVER_URL=http://127.0.0.1:8011 ./scripts/verify_dual_engine.sh

# 6. 듀얼 평가 1회
curl -fsS -X POST http://127.0.0.1:8011/api/evaluate/dual \
  -H 'Content-Type: application/json' \
  -d @tests/fixtures/v_compare/both_go_normal.json \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print('consensus:', d['agreement']['consensus'], 'fpe_gate:', d['fpe_gate_passed'])"
# → consensus: both_go, fpe_gate: True
```

### 5.2 조건 5 입증 체크 (실행 후 채움)

| 항목 | 결과 |
|---|---|
| Preflight B 통과 | [TBD] |
| 8011 서버 기동 | [TBD] |
| `/api/engine/list` 응답에 `learning_comparison` | [TBD] |
| `verify_dual_engine.sh` [ALL OK] | [TBD] |
| `tests/test_dual_consensus.py` 7 PASSED | [TBD] |
| `/api/evaluate/dual` both_go 응답 정상 | [TBD] |

### 5.3 Stash 복구 — 메시지 기반 id 추출 (F2 [codex] v2.5 P2 정정)

**v2.5의 `stash@{0}` 고정 방식**은 중간에 다른 stash가 생기면 잘못된 stash를 복구할 수 있음. v2.6은 메시지 기반 id 추출로 변경.

```bash
# F2 [codex] v2.5 정정: 메시지 기반 stash id 추출
PRE_OPTION_STASH="$(git stash list | awk -F: '/pre-option-A/ {print $1; exit}')"

if [ -z "$PRE_OPTION_STASH" ]; then
  echo "[INFO] pre-option-A stash 없음 — Preflight A에서 stash 안 했거나 이미 복구"
  # exit 1로 끊지 않고 INFO만 — Preflight A가 통과했을 수도 있으므로
else
  echo "[INFO] pre-option-A stash 발견: $PRE_OPTION_STASH"
  git stash show -p "$PRE_OPTION_STASH" | head -20   # 사전 미리보기
  echo ""
  read -p "위 변경을 복구하려면 'yes' 입력: " ANS
  if [ "$ANS" = "yes" ]; then
    git stash pop "$PRE_OPTION_STASH"
    echo "[OK] stash 복구 완료"
  else
    echo "[INFO] stash 복구 건너뜀 (수동으로 git stash pop $PRE_OPTION_STASH 실행 가능)"
  fi
fi
```

**Preflight B에서 추가 stash 한 경우 동시 복구**:
```bash
PRE_MAIN_STASH="$(git stash list | awk -F: '/pre-main-checkout/ {print $1; exit}')"
if [ -n "$PRE_MAIN_STASH" ]; then
  echo "[INFO] pre-main-checkout stash 발견: $PRE_MAIN_STASH"
  git stash show -p "$PRE_MAIN_STASH" | head -20
  read -p "복구하려면 'yes' 입력: " ANS
  [ "$ANS" = "yes" ] && git stash pop "$PRE_MAIN_STASH"
fi
```

> **순서**: Preflight A stash 먼저 복구, Preflight B stash 다음. 두 stash가 같은 파일을 건드리면 충돌 가능 — 충돌 시 수동 머지.

## 6. 요약 매트릭스 (v2.5 §6 계승)

| 영역 | 코드 저장소 즉시 | 8011 재시작 후 | 별도 PR 필요 |
|---|:---:|:---:|:---:|
| 코드 (import 경로) | ✅ | — | — |
| 테스트 인프라 | ✅ | — | — |
| API 3종 | — | ✅ | — |
| force_ape gate | — | ✅ (env 설정 시) | — |
| `dual_eval_helpers.js` window 노출 | ✅ | — | — |
| 6 화면 듀얼 카드 + SourceQuality + 상담 family | — | — | **3차 PR (§3.3)** |
| 엔진 관리 탭 (월간 고도화) | — | — | **3차 PR (§3.3)** |
| AppleGothic font stack | — | — | **3차 PR** |
| proposal/email gate (FPE 단독 기준) | — | — | **3차 PR** |
| engine.py 본체 분리 | — | — | **2차 PR (선택)** |
| ape_blocked 케이스 | — | — | **v3** |
| 월간 평가엔진 고도화보고서 자동화 | — | — | **별도 PR** |

> **PR 규모 (v2.6 — 옵션 A 적용 후 재측정 placeholder)**: **<TBD>** files changed, **<TBD>** insertions / **<TBD>** deletions

## 7. 핵심 메시지

v2.6은 **`set -e` 환경 완전 안전성 + stash id 정확성**을 갖춘 실행 승인 체크리스트입니다.

- v2.5 [codex] 검증의 P1 (preflight grep 변수 대입) + P2 (stash@{0} 고정) 모두 반영
- **모든 worktree 검사를 `awk '/pattern/ {print ...}'` 패턴으로 통일** → clean 상태에서도 exit code 0
- **stash 복구를 메시지 기반 id 추출**로 변경 → 다른 stash와 충돌 안 함
- 7개 체크리스트 모두 [O] 처리 후 **v2.7 완료 보고서** 생성

> v2.5 [codex] §5 인용: "위 3개 보완 후 v2.5는 실행 승인 체크리스트로 사용할 수 있습니다." → **v2.6에서 1, 2, 3 모두 보완 완료**.

## 8. 다음 액션 흐름

```
[현재] v2.6 생성 (체크리스트 7개 모두 [ ])
   ↓
§2.1 Preflight A (awk 안전 — 필요 시 pre-option-A stash)
   ↓
§2.2-2.5 옵션 A 자동화 블록 (조건 1+2+3 [O])
   ↓
§3 PR 규모 재측정 → §3.3 4곳 수치 갱신 (조건 4 [O])
   ↓
§4 PR 생성 → §4.2 placeholder 채움
   ↓
PR review + 머지 (engine.py conflict 시 6 필드 채택)
   ↓
§5.0 Preflight B (awk 안전 — 필요 시 pre-main-checkout stash)
   ↓
§5.1-5.2 8011 재시작 + 서버 검증 (조건 5 [O])
   ↓
§5.3 Stash 복구 (메시지 기반 id 추출)
   ↓
v2.7 완료 보고서 [claude] 생성:
  "[claude]flowbiz_dual_engine_pr_merge_activation_completion_report_20260430.md"
   ↓
3차 UI PR (§3.3 7항 + 6 화면 + 엔진관리 탭)
```

## 9. 누적 Finding 추적

| 단계 | 신규 Finding | 누적 | 잔여 P0/P1 |
|---|---|---|---|
| v1 | 4 | 4 | — |
| v2 | 2 | 6 | — |
| v2.1~v2.3 | 0 | 12 | — |
| v2.4 | 0 | 12 | — |
| v2.5 | 0 (v2.4 [codex] P1+P2 반영) | 14 | — |
| **v2.6** | **0 (v2.5 [codex] P1+P2 반영)** | **16** | **0** |

## 10. 변경되지 않은 항목 (v2.5 그대로 계승)

- §3.3 후속 UI PR 운영 원칙 7항 + 6 화면 + 엔진관리 탭
- §6 engine.py 충돌 가능성 (경로 A/B + 6 필드 채택)
- §9 Rollback 시점별
- 부록 D 후속 3차 UI PR 작업 시작 시 체크리스트 8 항목

---

## 부록 A. v2.5 → v2.6 정정 위치

### A.1 preflight grep → awk 전환 (F1 [codex] v2.5 P1)

| 위치 | v2.5 | v2.6 |
|---|---|---|
| §2.1 Preflight A | `DIRTY_TRACKED="$(git status --short \| grep '^ M' \| awk '{print $2}')"` | `DIRTY_TRACKED="$(git status --short \| awk '/^ M/ {print $2}')"` |
| §5.0 Preflight B | `DIRTY="$(git status --short \| grep -E '^( M\|A \|D \|R \|C \|MM)')"` | `DIRTY="$(git status --short \| awk '/^( M\|A \|D \|R \|C \|MM)/ {print}')"` |
| 부록 C TL;DR | grep 패턴 동일 | awk 패턴 동일 적용 |

### A.2 stash 복구 메시지 기반 id 추출 (F2 [codex] v2.5 P2)

| 위치 | v2.5 | v2.6 |
|---|---|---|
| §5.3 stash 복구 | `git stash list \| grep "pre-option-A"; git stash pop "stash@{0}"` | `PRE_OPTION_STASH="$(git stash list \| awk -F: '/pre-option-A/ {print $1; exit}')"; ... git stash pop "$PRE_OPTION_STASH"` |
| §5.3 미존재 처리 | (없음) | `if [ -z "$PRE_OPTION_STASH" ]; then echo "[INFO] 없음"; fi` |
| §5.3 사전 미리보기 | (없음) | `git stash show -p "$PRE_OPTION_STASH" \| head -20` + `read -p` 확인 |
| §5.3 Preflight B stash 동시 복구 | (없음) | `PRE_MAIN_STASH` 별도 추출 + 순서대로 복구 |

### A.3 부록 E.5 신설

부록 E에 새 항목 추가 — "set -e 안전 변수 대입 패턴".

## 부록 B. 누적 Finding 추적 상세 (v1 → v2.6)

| Finding | 우선순위 | v2.5 → v2.6 변화 |
|---|---|---|
| F1 v1: PR URL | P1 | (계승) |
| F2 v1: macOS xargs -r | P1 | (계승) |
| F3 v1: 테스트 수치 | P2 | (계승) |
| F4 v1: 재시작 문구 | P2 | (계승) |
| F1 v2: 파일 수 | P2 | placeholder 계승 |
| F2 v2: consensus 표현 | P2 | 조건 5 계승 |
| F1 v2.1: FPE 고정 원칙 | P1 | §3.3 계승 |
| F2 v2.1: APE engine_purpose | P1 | sed 자동화 + exit-code 안전 계승 |
| F3 v2.1: 상담/AppleGothic | P2 | (계승) |
| F4 v2.1: git diff base | P3 | (계승) |
| F1 v2.2 [codex]: tests 누락 | P1 | (계승) |
| F2 v2.2 [codex]: PR 규모 재측정 | P2 | (계승) |
| F1 v2.4 [codex]: clean worktree preflight | P1 | Preflight A/B 계승 + **awk 안전화** |
| F2 v2.4 [codex]: grep exit code | P2 | if/else 패턴 계승 |
| **F1 v2.5 [codex]: preflight 변수 대입 grep 실패** | **P1** | **Preflight A/B awk 패턴 + 부록 E.5 신설** |
| **F2 v2.5 [codex]: stash@{0} 고정** | **P2** | **§5.3 메시지 기반 id 추출** |

**누적 16 Finding 모두 v2.6까지 반영, P0/P1 잔여 0건**.

## 부록 C. v2.6 단일 실행 블록 (TL;DR — set -e 완전 안전)

```bash
set -e   # ← v2.6은 이 한 줄과 완전 호환

cd /Users/appler/Documents/COTEX/FlowBiz_ultra

# === Preflight A: awk 패턴 (set -e 안전) ===
EXPECTED="engines/_base.py engines/ape/__init__.py engines/ape/README.md tests/test_engine_registry.py"
DIRTY="$(git status --short | awk '/^ M/ {print $2}')"
UNEXPECTED=""
for f in $DIRTY; do
  case " $EXPECTED " in *" $f "*) ;; *) UNEXPECTED="$UNEXPECTED $f" ;; esac
done
if [ -n "$UNEXPECTED" ]; then
  echo "[STOP] Preflight A: 예상 외 변경: $UNEXPECTED"; exit 1
fi
echo "[OK] Preflight A"

# === 사전 측정 ===
git fetch origin
git diff origin/main...HEAD --stat | tail -1
if ! grep -rqn "learning_proposal" engines tests app.py; then
  echo "[FAIL] 사전 0 hit"; exit 1
fi
echo "[OK] 사전 4 hit 확인"

# === 옵션 A sed ===
sed -i '' 's/learning_proposal/learning_comparison/g' \
  engines/_base.py engines/ape/__init__.py engines/ape/README.md tests/test_engine_registry.py

# === 변경 검증 ===
if grep -rqn "learning_proposal" engines tests app.py; then
  echo "[FAIL] 잔존"; exit 1
fi
echo "[OK] 0 hit"

HIT="$(grep -rl 'learning_comparison' engines tests | wc -l | tr -d ' ')"
[ "$HIT" -eq 4 ] && echo "[OK] 4 hit" || { echo "[FAIL] hit=$HIT"; exit 1; }

python3 -m pytest tests/test_engine_registry.py -q   # 24 passed
python3 -m pytest tests/ -q                          # 106 passed, 7 skipped
node scripts/test_dual_eval_helpers.js               # 16 passed

# === commit + push ===
git add -u engines/_base.py engines/ape/__init__.py engines/ape/README.md tests/test_engine_registry.py
git commit -m "fix: APE engine_purpose learning_proposal → learning_comparison"
git push origin codex/dual-engine-execution-20260430

# === PR 규모 재측정 → §3.2 갱신 ===
git fetch origin
git diff origin/main...HEAD --stat | tail -1

# === [수동] PR 생성 → §4.2 placeholder 채움 → review + 머지 ===

# === Preflight B: awk 패턴 (set -e 안전) ===
DIRTY="$(git status --short | awk '/^( M|A |D |R |C |MM)/ {print}')"
if [ -n "$DIRTY" ]; then echo "[STOP] Preflight B"; echo "$DIRTY"; exit 1; fi
echo "[OK] Preflight B"

git checkout main && git pull origin main
PID="$(lsof -ti :8011 2>/dev/null || true)"; [ -n "$PID" ] && kill $PID && sleep 1
nohup python3 -m uvicorn app:app --host 127.0.0.1 --port 8011 > /tmp/uvicorn8011.log 2>&1 &
sleep 3

# === 응답 검증 ===
ENGINE_LIST="$(curl -fsS http://127.0.0.1:8011/api/engine/list)"
if echo "$ENGINE_LIST" | grep -q '"engine_purpose": "learning_comparison"'; then
  echo "[OK] learning_comparison 노출"
else
  echo "[FAIL]"; echo "$ENGINE_LIST"; exit 1
fi

DUAL_SERVER_URL=http://127.0.0.1:8011 ./scripts/verify_dual_engine.sh

# === Stash 복구 — 메시지 기반 id 추출 ===
PRE_OPTION_STASH="$(git stash list | awk -F: '/pre-option-A/ {print $1; exit}')"
if [ -n "$PRE_OPTION_STASH" ]; then
  echo "[INFO] pre-option-A stash: $PRE_OPTION_STASH (수동으로 git stash pop 실행)"
fi
PRE_MAIN_STASH="$(git stash list | awk -F: '/pre-main-checkout/ {print $1; exit}')"
if [ -n "$PRE_MAIN_STASH" ]; then
  echo "[INFO] pre-main-checkout stash: $PRE_MAIN_STASH (수동으로 git stash pop 실행)"
fi

# === 7 항목 모두 [O] → v2.7 완료 보고서 트리거 ===
```

## 부록 D. 후속 3차 UI PR 작업 시작 시 체크리스트 (v2.2 §3.3 직결)

(v2.5 부록 D 그대로 계승)

- [ ] `flowbiz_dual_engine_ui_sample_validation_direction_20260430.md` 읽음
- [ ] §3.3 7항 원칙 숙지
- [ ] §3.3 6 화면 + 엔진관리 탭 범위 확정
- [ ] 금지 UI 패턴 폐기 확인
- [ ] AppleGothic font stack 적용 계획
- [ ] 상담보고서 family + 전화상담/직접상담 subtype 데이터 모델
- [ ] 엔진 관리 탭의 pending/approved/promoted 상태 enum
- [ ] `flowbiz_dual_engine_evaluation_and_upgrade_lifecycle_plan_20260430.md` §6 화면 매트릭스 정합성

## 부록 E. grep 검증 패턴 표준 + set -e 안전 변수 대입 (F1+F2 [codex] v2.5)

### E.1 "0 hit이면 성공" (잔존 차단용)

```bash
if grep -rqn "<TARGET>" <PATHS>; then
  echo "[FAIL] <TARGET> 잔존"
  grep -rn "<TARGET>" <PATHS>
  exit 1
fi
echo "[OK] <TARGET> 0 hit"
```

### E.2 "정확히 N hit이면 성공"

```bash
HIT="$(grep -rl '<TARGET>' <PATHS> | wc -l | tr -d ' ')"
if [ "$HIT" -ne <EXPECTED_N> ]; then
  echo "[FAIL] hit count = $HIT (<EXPECTED_N> 기대)"
  exit 1
fi
echo "[OK] <EXPECTED_N> 파일 정정"
```

### E.3 "응답에 키워드 포함"

```bash
RESPONSE="$(curl -fsS <URL>)"
if echo "$RESPONSE" | grep -q '<KEYWORD>'; then
  echo "[OK] <KEYWORD> 노출"
else
  echo "[FAIL]"
  echo "$RESPONSE"
  exit 1
fi
```

### E.4 안티패턴 (사용 금지)

```bash
# ❌ exit code 무시 — set -e 환경 중단
grep -rn "TARGET" .

# ❌ 결과 의미 모호
grep -c "TARGET" file
```

### E.5 set -e 안전 변수 대입 패턴 (v2.6 신설 — F1 [codex] v2.5 P1)

**목적**: `DIRTY="$(git status --short | grep ...)"` 처럼 변수 대입 우변에서 grep이 0 hit 시 exit code 1을 반환하면 `set -e` 환경에서 변수 대입 자체가 실패합니다.

**해결책 1 — `awk` 사용 (권장)**:

```bash
# 안전 — awk는 매칭 0건일 때도 exit 0
DIRTY="$(git status --short | awk '/^ M/ {print $2}')"
DIRTY_ALL="$(git status --short | awk '/^( M|A |D |R |C |MM)/ {print}')"
```

**해결책 2 — `|| true` 명시**:

```bash
# 안전 — grep 실패 시 강제 0 exit code
DIRTY="$(git status --short | grep '^ M' || true)"
```

**해결책 3 — `|| :`** (`:`는 noop):

```bash
DIRTY="$(git status --short | grep '^ M' || :)"
```

**안티패턴**:

```bash
# ❌ set -e 환경에서 0 hit 시 변수 대입 실패 → 스크립트 중단
DIRTY="$(git status --short | grep '^ M')"
```

### E.6 stash id 추출 패턴 (v2.6 신설 — F2 [codex] v2.5 P2)

**목적**: `git stash pop "stash@{0}"`은 가장 최근 stash를 pop하지만, 중간에 다른 stash가 생기면 의도와 다른 변경을 복구할 위험.

**해결책 — 메시지 기반 id 추출**:

```bash
# 메시지 'pre-option-A' 포함 stash의 id를 추출
STASH_ID="$(git stash list | awk -F: '/pre-option-A/ {print $1; exit}')"

if [ -z "$STASH_ID" ]; then
  echo "[INFO] 매칭 stash 없음"
else
  echo "[INFO] stash id: $STASH_ID"
  git stash show -p "$STASH_ID" | head -20   # 사전 미리보기
  git stash pop "$STASH_ID"
fi
```

**stash 생성 시 메시지 규약**:
- Preflight A 진입 전: `pre-option-A-<timestamp>`
- Preflight B 진입 전: `pre-main-checkout-<timestamp>`
- 기타 임시: `pre-<context>-<timestamp>`

타임스탬프 포함으로 동일 메시지 stash가 복수 생성되어도 `awk ... ; exit` 사용 시 가장 첫 매칭만 반환 (목록 상단이 가장 최근).
