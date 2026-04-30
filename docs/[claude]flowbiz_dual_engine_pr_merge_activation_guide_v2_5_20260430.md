# 듀얼 엔진 PR 머지 → 라이브 활성화 가이드 v2.5 [claude]

- 문서번호: FBU-GUIDE-PR-MERGE-DUAL-v2_5-20260430
- 작성일: 2026-04-30
- 작성자: [claude]
- 이전 버전: `[claude]flowbiz_dual_engine_pr_merge_activation_guide_v2_4_20260430.md` (v2.4)
- 검증: `[codex]flowbiz_dual_engine_pr_merge_activation_guide_v2_4_validation_20260430.md` (P1 1건 / P2 1건 — **조건부 보류**)
- 변경 사유: v2.4 [codex] 검증 2건 반영 — **clean worktree preflight 신설** + **grep zero-hit exit-code 안전화** + 4 보완 후 승인 기준 충족

## 0. v2.4 → v2.5 변경 요약

| Finding | 우선순위 | v2.4 문제 | v2.5 반영 |
|---|---|---|---|
| F1 [codex] v2.4: clean worktree preflight 누락 | **P1** | 현재 작업트리에 unrelated tracked 변경 4건 + untracked 다수. §2.1 옵션 A sed 진입 + §5.1 main checkout 단계가 막힐 위험 | **§2.1 신설 — Preflight A** (옵션 A 직전 worktree 검증, 예상 외 tracked 변경 차단) + **§5.0 신설 — Preflight B** (main checkout 직전 worktree 비어있음 검증) |
| F2 [codex] v2.4: grep zero-hit이 exit code 1 반환 → set -e 환경에서 중단 | P2 | "0 hit이면 성공"이라고만 설명, exit code 처리 없음 | **모든 grep zero-hit 검증을 `if grep ...; then echo [FAIL]; exit 1; else echo [OK]; fi` 패턴으로 통일** + 부록 E에 패턴 표준화 명시 |

### 0.1 v2.4 [codex] 실측 dirty worktree 상태 (실행 전 보정 필요)

본 세션 재실측:
```text
$ git status --short
 M data/bizaipro_learning_registry.json
 M docs/flowbiz_ultra_validation_report_registry.md
 M tests/test_regression.py
 M web/bizaipro_shared.css
?? .docx_render_fbu_ntn_0001_ql/
?? FBU-*.docx (사용자 작성 .docx 9건)
?? FlowBizTool _ v2 _standalone.html
?? data/*.json (untracked 7건)
?? docs/[claude]flowbiz_*.md (v2.1~v2.5)
?? docs/[codex]flowbiz_*.md (v2.2~v2.4 검증)
```

→ **tracked modified 4건이 옵션 A pathspec 4 파일과 겹치지 않으므로 commit 범위는 안전**, 다만 **머지 후 `git checkout main`은 modified 파일 때문에 막힘 → §5.0 Preflight B 필수**.

## 1. 5개 승인 조건 체크리스트 (v2.4 §1 계승) + Preflight 2건 신규

```text
[ ] Preflight A: 옵션 A 직전 worktree 예상 외 tracked 변경 0 (§2.1)
[ ] 조건 1:     §2.2 옵션 A 4 파일 sed 변경 적용
[ ] 조건 2:     tests/test_engine_registry.py 24 passed 유지
[ ] 조건 3:     전체 테스트 통과 (또는 기존 skipped 사유 확인)
[ ] 조건 4:     PR 규모 재측정 후 v2.5/PR description 갱신
[ ] Preflight B: main checkout 직전 worktree 비어있음 (§5.0)
[ ] 조건 5:     머지 후 verify_dual_engine.sh 통과 + 7 consensus PASSED 입증
```

**완료 시점**: 7개 모두 [O] → v2.6 완료 보고서 생성 트리거.

## 2. 조건 1+2+3 — 옵션 A 적용 자동화 블록 (Preflight A 신설)

### 2.1 Preflight A — 옵션 A 직전 worktree 검증 (F1 [codex] P1 — 신설)

옵션 A는 4 파일만 수정합니다. **그 외 tracked 변경이 있으면 commit 범위가 흐려질 수 있어 사전 차단**합니다.

```bash
cd /Users/appler/Documents/COTEX/FlowBiz_ultra

# Preflight A: 옵션 A 예상 외 tracked 변경 차단
EXPECTED_PATHS="engines/_base.py engines/ape/__init__.py engines/ape/README.md tests/test_engine_registry.py"
DIRTY_TRACKED="$(git status --short | grep '^ M' | awk '{print $2}')"
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
  echo "  A. git stash push -u -m 'pre-option-A-\$(date +%Y%m%d-%H%M)' (보존, 권장)"
  echo "  B. git checkout -- <파일>                                   (버림 — 주의)"
  echo "  C. git add <파일> && git commit -m '...'                     (별도 commit)"
  echo ""
  echo "처리 후 본 Preflight A 재실행 후 §2.2 sed 단계 진입"
  exit 1
fi
echo "[OK] Preflight A 통과 — 옵션 A pathspec 외 tracked 변경 0"
```

**현재 세션 실측 결과 (예상되는 출력)**:
```text
[STOP] Preflight A 실패 — 옵션 A 예상 외 tracked 변경 존재:
  M data/bizaipro_learning_registry.json
  M docs/flowbiz_ultra_validation_report_registry.md
  M tests/test_regression.py
  M web/bizaipro_shared.css
```

**권장 처리** (옵션 A — stash 보존):
```bash
git stash push -u -m "pre-option-A-$(date +%Y%m%d-%H%M)" \
  data/bizaipro_learning_registry.json \
  docs/flowbiz_ultra_validation_report_registry.md \
  tests/test_regression.py \
  web/bizaipro_shared.css
# → stash 보존 후 옵션 A 종료 시점에 git stash pop 가능
```

> **untracked 파일**(.docx, data/*.json 신규, docs/[claude]*.md 등)은 commit 대상이 아니므로 Preflight A에서 차단 대상 아님. 다만 §5.0 Preflight B에서 main checkout 시 충돌 여부 재확인.

### 2.2 사전 상태 측정

```bash
# 현재 PR 규모 (옵션 A 적용 전)
git fetch origin
git diff origin/main...HEAD --stat | tail -1
# → 34 files changed, 15262 insertions(+), 55 deletions(-)  (예상)

# learning_proposal 잔존 4곳 확인 (F2 [codex] P2 — exit code 안전 패턴)
if ! grep -rqn "learning_proposal" engines tests app.py; then
  echo "[FAIL] learning_proposal 사전 0 hit — 이미 옵션 A 적용된 상태?"
  exit 1
else
  echo "[OK] learning_proposal 사전 4 hit 기대 — 옵션 A 미적용 상태 확인"
  grep -rn "learning_proposal" engines tests app.py
fi
```

### 2.3 4 파일 일괄 sed (macOS BSD sed 호환)

```bash
sed -i '' 's/learning_proposal/learning_comparison/g' \
  engines/_base.py \
  engines/ape/__init__.py \
  engines/ape/README.md \
  tests/test_engine_registry.py
```

### 2.4 변경 검증 (조건 2+3, F2 [codex] P2 — exit code 안전 패턴)

```bash
# learning_proposal 0 hit 확인 — exit code 안전
if grep -rqn "learning_proposal" engines tests app.py; then
  echo "[FAIL] learning_proposal 잔존 — sed 누락"
  grep -rn "learning_proposal" engines tests app.py
  exit 1
else
  echo "[OK] learning_proposal 0 hit"
fi

# learning_comparison 4 hit 확인 — 기대값 양수 hit
HIT="$(grep -rl "learning_comparison" engines tests | wc -l | tr -d ' ')"
if [ "$HIT" -ne 4 ]; then
  echo "[FAIL] learning_comparison hit count = $HIT (4 기대)"
  grep -rn "learning_comparison" engines tests
  exit 1
else
  echo "[OK] learning_comparison 4 파일 모두 정정"
fi

# 조건 2: registry 테스트 24 passed 유지
python3 -m pytest tests/test_engine_registry.py -q
# → 24 passed (조건 2 [O])

# 조건 3: 전체 회귀 테스트
python3 -m pytest tests/ -q
# → 106 passed, 7 skipped (조건 3 [O])

# 보조: Node helper + closure
node scripts/test_dual_eval_helpers.js
# → 16 passed, 0 failed
python3 scripts/extract_engine_closures.py
# → 3구역 disjoint OK
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

## 3. 조건 4 — PR 규모 재측정 + v2.5 갱신

### 3.1 재측정 명령

```bash
cd /Users/appler/Documents/COTEX/FlowBiz_ultra
git fetch origin
git diff origin/main...HEAD --stat | tail -1
```

### 3.2 측정 결과 기록 (placeholder)

| 측정 시점 | 결과 |
|---|---|
| v2.3 [codex] 측정 (옵션 A 적용 전) | `34 files changed, 15262 insertions(+), 55 deletions(-)` |
| v2.4 [codex] 재측정 (옵션 A 적용 전) | `34 files changed, 15262 insertions(+), 55 deletions(-)` (동일) |
| **본 v2.5 측정 (옵션 A 적용 후)** | **`<TBD: 옵션 A commit + push 후 위 명령 결과로 갱신>`** |

### 3.3 갱신 위치 (4곳)

옵션 A 적용 + push 후 다음 4곳에 새 수치 반영:

- [ ] 본 가이드 §3.2 측정 결과 기록표
- [ ] 본 가이드 §6 요약 매트릭스 끝 PR 규모
- [ ] `outputs/dual_engine_baseline_20260430/PR_DESCRIPTION.md`
- [ ] GitHub PR description (PR 생성 후)

> **예상**: v2.4 [codex]에 따르면 4 파일 모두 이미 PR 포함 → 파일 수 변동 없음. insertions/deletions만 미세 변동.

## 4. PR 생성 (조건 1~4 완료 후)

### 4.1 PR 생성 절차 (gh CLI 미설치 — 웹 UI 사용)

1. 브라우저에서 PR 생성 URL 접속:
   ```
   https://github.com/YeChungHee/FlowBizTool/pull/new/codex/dual-engine-execution-20260430
   ```

2. PR 작성:
   - **Title**: `feat: dual engine v2.11 — engines/ separation + dual evaluation API + UI helper (engine_purpose: learning_comparison)`
   - **Description**: `outputs/dual_engine_baseline_20260430/PR_DESCRIPTION.md` + §3.2 재측정 수치 반영
   - **Base**: `main`
   - **Head**: `codex/dual-engine-execution-20260430`

3. PR 생성 후 본 문서 placeholder 갱신 (v2.6):
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
PR 규모:   [TBD: 옵션 A 적용 후 재측정 결과]
PR Base:   main
PR Head:   codex/dual-engine-execution-20260430 (e16b391 + 옵션 A commit)
```

## 5. 조건 5 — 머지 후 8011 서버 검증 (Preflight B 신설)

### 5.0 Preflight B — main checkout 직전 worktree 검증 (F1 [codex] P1 — 신설)

머지 후 main checkout 시 modified 파일이 있으면 git이 차단합니다. 사전에 worktree 비어있음 확인 + stash 처리.

```bash
cd /Users/appler/Documents/COTEX/FlowBiz_ultra

# Preflight B: main checkout 직전 worktree clean 확인
DIRTY="$(git status --short | grep -E '^( M|A |D |R |C |MM)')"
if [ -n "$DIRTY" ]; then
  echo "[STOP] Preflight B 실패 — main checkout 차단될 수 있는 변경 존재:"
  echo "$DIRTY"
  echo ""
  echo "처리 옵션 (택 1):"
  echo "  A. git stash push -u -m 'pre-main-checkout-\$(date +%Y%m%d-%H%M)' (권장)"
  echo "  B. git commit -m 'wip: ...' (별도 commit)"
  echo ""
  exit 1
fi
echo "[OK] Preflight B 통과 — main checkout 안전"

# Preflight A에서 stash 한 경우 여기서 pop 하지 않음
# (main checkout + 검증 완료 후 별도 단계에서 pop)
```

### 5.1 macOS 호환 재시작 + 검증 자동화

```bash
# 1. 머지된 main 동기화 (Preflight B 통과 후 진입)
git checkout main && git pull origin main

# 2. macOS BSD xargs 호환 재시작
PID="$(lsof -ti :8011 2>/dev/null || true)"
if [ -n "$PID" ]; then
  kill $PID
  sleep 1
fi
nohup python3 -m uvicorn app:app --host 127.0.0.1 --port 8011 > /tmp/uvicorn8011.log 2>&1 &
sleep 3

# 3. health check + APE engine_purpose 정합성 (조건 5 핵심)
curl -fsS http://127.0.0.1:8011/api/engine/list | python3 -m json.tool

# 4. learning_comparison 노출 검증 (F2 [codex] P2 — exit code 안전 패턴)
ENGINE_LIST="$(curl -fsS http://127.0.0.1:8011/api/engine/list)"
if echo "$ENGINE_LIST" | grep -q '"engine_purpose": "learning_comparison"'; then
  echo "[OK] APE engine_purpose: learning_comparison 노출 확인"
else
  echo "[FAIL] learning_comparison 미노출 — 옵션 A 미적용 또는 서버 미재시작"
  echo "$ENGINE_LIST"
  exit 1
fi

# 5. 종합 검증 — 9 항목 [ALL OK] + 7 consensus PASSED 입증
DUAL_SERVER_URL=http://127.0.0.1:8011 ./scripts/verify_dual_engine.sh

# 6. 듀얼 평가 1회 시도 (both_go 케이스)
curl -fsS -X POST http://127.0.0.1:8011/api/evaluate/dual \
  -H 'Content-Type: application/json' \
  -d @tests/fixtures/v_compare/both_go_normal.json \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print('consensus:', d['agreement']['consensus'], 'fpe_gate:', d['fpe_gate_passed'])"
# → consensus: both_go, fpe_gate: True
```

### 5.2 조건 5 입증 체크 (실행 후 채움)

| 항목 | 결과 |
|---|---|
| Preflight B 통과 (worktree clean) | [TBD] |
| 8011 서버 기동 | [TBD] |
| `/api/engine/list` 응답에 `learning_comparison` 노출 | [TBD] |
| `verify_dual_engine.sh` [ALL OK] | [TBD] |
| `tests/test_dual_consensus.py` 7 PASSED | [TBD] |
| `/api/evaluate/dual` both_go 응답 정상 | [TBD] |

### 5.3 Stash 복구 (Preflight A에서 stash 했을 경우)

```bash
# stash 목록 확인
git stash list | grep "pre-option-A"

# stash pop (가장 최근 pre-option-A)
git stash pop "stash@{0}"

# 또는 명시적으로 메시지 일치 stash apply
# git stash apply <stash-id>
```

## 6. 요약 매트릭스 (v2.4 §6 계승)

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

> **PR 규모 (v2.5 — 옵션 A 적용 후 재측정 placeholder)**: **<TBD>** files changed, **<TBD>** insertions / **<TBD>** deletions

## 7. 핵심 메시지

v2.5는 **clean worktree 안전성 + exit-code 안전성을 갖춘 실행 승인 체크리스트**입니다.

- v2.4 [codex] 검증의 P1 (preflight 누락) + P2 (grep zero-hit exit code) 모두 반영
- §2.1 **Preflight A** + §5.0 **Preflight B** 신설로 worktree 충돌 차단
- 모든 grep zero-hit 검증을 `if grep ...; then [FAIL]; else [OK]; fi` 패턴으로 통일 → `set -e` / CI 환경 안전
- 7개 체크리스트 (Preflight A + 조건 1~4 + Preflight B + 조건 5) 모두 [O] 처리 후 v2.6 완료 보고서 생성

> v2.4 [codex] §5 인용: "위 1~3 보완 후 v2.4는 실행 승인 체크리스트로 사용할 수 있습니다." → **v2.5에서 1, 2, 3 모두 보완 완료**.

## 8. 다음 액션 흐름

```
[현재] v2.5 생성 (체크리스트 7개 모두 [ ])
   ↓
§2.1 Preflight A (worktree 검증, 필요 시 stash)
   ↓
§2.2-2.5 옵션 A 자동화 블록 (조건 1+2+3 [O])
   ↓
§3 PR 규모 재측정 → §3.3 4곳 수치 갱신 (조건 4 [O])
   ↓
§4 PR 생성 → §4.2 placeholder 채움
   ↓
PR review + 머지 (engine.py conflict 시 6 필드 채택)
   ↓
§5.0 Preflight B (main checkout 안전성 검증)
   ↓
§5.1-5.2 8011 재시작 + 서버 검증 (조건 5 [O])
   ↓
§5.3 Stash 복구 (필요 시)
   ↓
v2.6 완료 보고서 [claude] 생성:
  "[claude]flowbiz_dual_engine_pr_merge_activation_completion_report_20260430.md"
   ↓
3차 UI PR 진입 (§3.3 7항 + 6 화면 + 엔진관리 탭 — v2.2 §3.3 계승)
```

## 9. 누적 Finding 추적

| 단계 | 신규 Finding | 누적 | 잔여 P0/P1 |
|---|---|---|---|
| v1 | 4 (P1×2, P2×2) | 4 | — |
| v2 | 2 (P2×2) | 6 | — |
| v2.1 | 0 | 6 | — |
| v2.2 | 0 | 10 | — |
| v2.3 | 0 (v2.2 [codex] P1+P2 반영) | 12 | — |
| v2.4 | 0 (codex 신규 0건) | 12 | — |
| **v2.5** | **0 (v2.4 [codex] P1+P2 반영)** | **14** | **0** |

## 10. 변경되지 않은 항목 (v2.4 그대로 계승)

다음 섹션은 v2.4에서 변경 없이 계승합니다:

- §3.3 후속 UI PR 운영 원칙 7항 + 6 화면 + 엔진관리 탭 (v2.2 신설 → v2.5 계승)
- §6 engine.py 충돌 가능성 (경로 A/B + 6 필드 채택 권장)
- §9 Rollback 시점별
- 부록 D 후속 3차 UI PR 작업 시작 시 체크리스트 8 항목

---

## 부록 A. v2.4 → v2.5 정정 위치

### A.1 Preflight A 신설 (F1 [codex] P1)

| 위치 | v2.4 | v2.5 |
|---|---|---|
| §1 체크리스트 | 5 조건 | **7 항목** (Preflight A + 5 조건 + Preflight B) |
| §2.1 (신설) | 사전 상태 확인만 | **Preflight A — 옵션 A 예상 외 tracked 변경 차단 명령 블록** + 처리 옵션 3가지 |
| §2.1 사전 상태 (현 §2.2) | grep zero-hit 안전 패턴 미적용 | **`if ! grep -rqn ...; then [FAIL]; else [OK]; fi`** |

### A.2 Preflight B 신설 (F1 [codex] P1)

| 위치 | v2.4 | v2.5 |
|---|---|---|
| §5.0 (신설) | (없음) | **Preflight B — main checkout 직전 worktree clean 검증** + stash 가이드 |
| §5.1 진입 조건 | `git checkout main && git pull` 직접 | "Preflight B 통과 후 진입" 명시 |
| §5.3 (신설) | (없음) | **Stash 복구** (Preflight A에서 stash 한 경우) |

### A.3 grep zero-hit exit-code 안전 패턴 (F2 [codex] P2)

| 위치 | v2.4 | v2.5 |
|---|---|---|
| §2.4 검증 | `grep -rn ... # 0 hit 기대` | `if grep -rqn ...; then [FAIL]; exit 1; else [OK]; fi` |
| §2.4 신규 hit | `grep -rn "learning_comparison" # 4 hit` | `HIT=$(...); if [ "$HIT" -ne 4 ]; then [FAIL]; else [OK]; fi` |
| §5.1 #4 (신설) | `grep -q ...` 없음 | `ENGINE_LIST=$(...); if echo "$ENGINE_LIST" \| grep -q ...; then [OK]; else [FAIL]; fi` |
| 부록 E (신설) | (없음) | **grep 검증 패턴 표준 정의** |

## 부록 B. 누적 Finding 추적 상세 (v1 → v2.5)

| Finding | 우선순위 | v1 | v2 | v2.1 | v2.2 | v2.3 | v2.4 | v2.5 |
|---|---|---|---|---|---|---|---|---|
| F1 v1: PR URL | P1 | `pull/new/...` | §1.1 신설 | (계승) | (계승) | (계승) | (계승) | (계승) |
| F2 v1: macOS xargs -r | P1 | 실패 | PID 변수 | (계승) | (계승) | (계승) | (계승) | (계승) |
| F3 v1: 테스트 수치 | P2 | "129/76" | 106/24/16 | (계승) | (계승) | (계승) | (계승) | (계승) |
| F4 v1: 재시작 문구 | P2 | 모호 | 코드/서버 분리 | (계승) | (계승) | (계승) | (계승) | (계승) |
| F1 v2: 파일 수 | P2 | — | "35개" | "34개" | (계승) | "재측정" | placeholder | (계승) |
| F2 v2: consensus 표현 | P2 | — | "이미 통과" | "현 세션 미검증" | (계승) | (계승) | 조건 5 | (계승) |
| F1 v2.1: FPE 고정 원칙 | P1 | — | — | 미반영 | §3.3 7항 | (계승) | (계승) | (계승) |
| F2 v2.1: APE engine_purpose | P1 | — | — | `learning_proposal` | `learning_comparison` 권고 | 코드 명세 | sed 자동화 | sed + exit-code 안전 |
| F3 v2.1: 상담/AppleGothic | P2 | — | — | 미반영 | §3.3 #4-7 | (계승) | (계승) | (계승) |
| F4 v2.1: git diff base | P3 | — | — | `main...HEAD` | `origin/main...HEAD` | (계승) | (계승) | (계승) |
| F1 v2.2 [codex]: tests 누락 | P1 | — | — | — | 3 파일 | 4 파일 | sed 자동화 | (계승) |
| F2 v2.2 [codex]: PR 규모 재측정 | P2 | — | — | — | 34 고정 | §13.4 신설 | placeholder | (계승) |
| **F1 v2.4 [codex]: clean worktree preflight** | **P1** | — | — | — | — | — | 미반영 | **Preflight A + B 신설** |
| **F2 v2.4 [codex]: grep exit code** | **P2** | — | — | — | — | — | 미반영 | **모든 grep을 if/else 패턴** |

**누적 14 Finding 모두 v2.5까지 반영, P0/P1 잔여 0건**.

## 부록 C. v2.5 단일 실행 블록 (TL;DR — exit-code 안전)

```bash
cd /Users/appler/Documents/COTEX/FlowBiz_ultra

# === Preflight A: 옵션 A 직전 worktree 검증 ===
EXPECTED="engines/_base.py engines/ape/__init__.py engines/ape/README.md tests/test_engine_registry.py"
DIRTY="$(git status --short | grep '^ M' | awk '{print $2}')"
UNEXPECTED=""
for f in $DIRTY; do
  case " $EXPECTED " in *" $f "*) ;; *) UNEXPECTED="$UNEXPECTED $f" ;; esac
done
if [ -n "$UNEXPECTED" ]; then
  echo "[STOP] Preflight A: 예상 외 변경"; echo "$UNEXPECTED"; exit 1
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

# === 변경 검증 (exit-code 안전) ===
if grep -rqn "learning_proposal" engines tests app.py; then
  echo "[FAIL] 잔존"; exit 1; else echo "[OK] 0 hit"; fi

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

# === Preflight B: main checkout 직전 ===
DIRTY="$(git status --short | grep -E '^( M|A |D |R |C |MM)')"
if [ -n "$DIRTY" ]; then echo "[STOP] Preflight B"; echo "$DIRTY"; exit 1; fi
echo "[OK] Preflight B"

git checkout main && git pull origin main
PID="$(lsof -ti :8011 2>/dev/null || true)"; [ -n "$PID" ] && kill $PID && sleep 1
nohup python3 -m uvicorn app:app --host 127.0.0.1 --port 8011 > /tmp/uvicorn8011.log 2>&1 &
sleep 3

# === learning_comparison 노출 검증 ===
ENGINE_LIST="$(curl -fsS http://127.0.0.1:8011/api/engine/list)"
if echo "$ENGINE_LIST" | grep -q '"engine_purpose": "learning_comparison"'; then
  echo "[OK] learning_comparison 노출"
else
  echo "[FAIL] 미노출"; echo "$ENGINE_LIST"; exit 1
fi

DUAL_SERVER_URL=http://127.0.0.1:8011 ./scripts/verify_dual_engine.sh
# → 7 consensus PASSED 입증

curl -fsS -X POST http://127.0.0.1:8011/api/evaluate/dual \
  -H 'Content-Type: application/json' \
  -d @tests/fixtures/v_compare/both_go_normal.json \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print('consensus:', d['agreement']['consensus'], 'fpe_gate:', d['fpe_gate_passed'])"

# === 7 항목 모두 [O] → v2.6 완료 보고서 트리거 ===
```

## 부록 D. 후속 3차 UI PR 작업 시작 시 체크리스트 (v2.2 §3.3 직결)

(v2.4 부록 D 그대로 계승)

- [ ] `flowbiz_dual_engine_ui_sample_validation_direction_20260430.md` 읽음
- [ ] §3.3 7항 원칙 숙지 — #1 (FPE 고정), #2 (APE 선택 금지), #3 (APE 비교 전용)
- [ ] §3.3 6 화면 + 엔진관리 탭 범위 확정
- [ ] 금지 UI 패턴 (엔진 선택 라디오) 폐기 확인
- [ ] AppleGothic font stack 적용 계획 수립
- [ ] 상담보고서 family + 전화상담/직접상담 subtype 데이터 모델 확인
- [ ] 엔진 관리 탭의 pending/approved/promoted 상태 enum 정의
- [ ] `flowbiz_dual_engine_evaluation_and_upgrade_lifecycle_plan_20260430.md` §6 화면 매트릭스와 정합성 확인

## 부록 E. grep 검증 패턴 표준 (F2 [codex] P2 — 신설)

이후 모든 자동화 블록에서 grep 결과를 검증할 때 다음 패턴을 사용합니다.

### E.1 "0 hit이면 성공" 패턴 (잔존 차단용)

```bash
# 안전 (set -e 호환)
if grep -rqn "<TARGET>" <PATHS>; then
  echo "[FAIL] <TARGET> 잔존"
  grep -rn "<TARGET>" <PATHS>
  exit 1
else
  echo "[OK] <TARGET> 0 hit"
fi
```

대안:
```bash
! grep -rqn "<TARGET>" <PATHS> || { echo "[FAIL]"; exit 1; }
echo "[OK]"
```

### E.2 "정확히 N hit이면 성공" 패턴 (신규 정착 검증용)

```bash
HIT="$(grep -rl '<TARGET>' <PATHS> | wc -l | tr -d ' ')"
if [ "$HIT" -ne <EXPECTED_N> ]; then
  echo "[FAIL] hit count = $HIT (<EXPECTED_N> 기대)"
  grep -rn "<TARGET>" <PATHS>
  exit 1
else
  echo "[OK] <EXPECTED_N> 파일 모두 정정"
fi
```

### E.3 "응답에 특정 키워드 포함" 패턴 (서버 응답 검증용)

```bash
RESPONSE="$(curl -fsS <URL>)"
if echo "$RESPONSE" | grep -q '<KEYWORD>'; then
  echo "[OK] <KEYWORD> 노출 확인"
else
  echo "[FAIL] <KEYWORD> 미노출"
  echo "$RESPONSE"
  exit 1
fi
```

### E.4 안티패턴 (사용 금지)

```bash
# ❌ exit code 무시 — set -e 환경에서 0 hit 시 스크립트 중단
grep -rn "TARGET" .  # 0 hit 기대

# ❌ 결과 의미 모호 — 성공/실패 출력 없음
grep -c "TARGET" file
```

이 패턴 표준을 v2.6 이후 모든 [claude] 자동화 블록에 적용합니다.
