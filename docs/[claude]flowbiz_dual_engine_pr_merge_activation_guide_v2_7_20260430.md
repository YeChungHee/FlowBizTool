# 듀얼 엔진 PR 머지 → 라이브 활성화 가이드 v2.7 [claude]

- 문서번호: FBU-GUIDE-PR-MERGE-DUAL-v2_7-20260430
- 작성일: 2026-04-30
- 작성자: [claude]
- 이전 버전: `[claude]flowbiz_dual_engine_pr_merge_activation_guide_v2_6_20260430.md` (v2.6)
- 검증: 사용자 직접 피드백 (P1 1건)
- 변경 사유: **Preflight A가 unstaged modified(`'^ M'`)만 검사** — staged/삭제/rename/conflict의 unrelated tracked 변경이 통과할 수 있는 보안 구멍 차단. Preflight B처럼 tracked 상태 전체를 보되 옵션 A 4 파일만 허용하도록 보강.

## 0. v2.6 → v2.7 변경 요약

| Finding | 우선순위 | v2.6 문제 | v2.7 반영 |
|---|---|---|---|
| F1 사용자 피드백 v2.6: Preflight A unstaged-only | **P1** | `awk '/^ M/ {print $2}'` — staged(`M `), 삭제(`D `, ` D`), rename(`R  `), conflict(`UU/AA/DD/AU/UA/DU/UD`)의 unrelated tracked 변경이 차단되지 않음 | **§2.1 Preflight A를 `git status --porcelain \| awk '!/^\?\?/ {print $NF}'` 로 변경** + 4 파일 화이트리스트 필터 + 부록 E.7 신설 (porcelain 전체 상태 패턴 표준) |

### 0.1 git status --porcelain 상태 코드 전수 검사

| 코드 | 의미 | v2.6 (`^ M`) | v2.7 (`!/^\?\?/`) |
|---|---|:---:|:---:|
| `M ` | staged modified | ❌ 통과 | ✅ 차단 |
| `A ` | staged added | ❌ 통과 | ✅ 차단 |
| `D ` | staged deleted | ❌ 통과 | ✅ 차단 |
| `R ` | staged renamed | ❌ 통과 | ✅ 차단 |
| `C ` | staged copied | ❌ 통과 | ✅ 차단 |
| ` M` | unstaged modified | ✅ 차단 | ✅ 차단 |
| ` D` | unstaged deleted | ❌ 통과 | ✅ 차단 |
| `MM` | staged + unstaged 모두 modified | ❌ 통과 | ✅ 차단 |
| `AM` | staged add + unstaged modified | ❌ 통과 | ✅ 차단 |
| `UU` | both modified (conflict) | ❌ 통과 | ✅ 차단 |
| `AA` | both added (conflict) | ❌ 통과 | ✅ 차단 |
| `DD` | both deleted (conflict) | ❌ 통과 | ✅ 차단 |
| `AU/UA/DU/UD` | unmerged 변형 | ❌ 통과 | ✅ 차단 |
| `??` | untracked | (제외) | (제외) |

→ v2.6 패턴은 unstaged modified 1종만 차단했으나 v2.7은 untracked를 제외한 모든 tracked 상태를 검사.

## 1. 7개 승인 체크리스트 (v2.6 §1 계승)

```text
[ ] Preflight A: 옵션 A 직전 모든 tracked 상태 검사 + 4 파일 화이트리스트 (§2.1, v2.7 보강)
[ ] 조건 1:     §2.3 옵션 A 4 파일 sed 변경 적용
[ ] 조건 2:     tests/test_engine_registry.py 24 passed 유지
[ ] 조건 3:     전체 테스트 통과
[ ] 조건 4:     PR 규모 재측정 후 v2.7/PR description 갱신
[ ] Preflight B: main checkout 직전 worktree 비어있음 (§5.0)
[ ] 조건 5:     머지 후 verify_dual_engine.sh 통과 + 7 consensus PASSED 입증
```

## 2. 조건 1+2+3 — 옵션 A 적용 자동화 블록

### 2.1 Preflight A — 옵션 A 직전 모든 tracked 상태 검사 (v2.7 보강)

```bash
cd /Users/appler/Documents/COTEX/FlowBiz_ultra

# Preflight A v2.7: untracked(??) 제외, tracked 상태 전체 수집 + 4 파일 화이트리스트 필터
EXPECTED_PATHS="engines/_base.py engines/ape/__init__.py engines/ape/README.md tests/test_engine_registry.py"

# git status --porcelain의 모든 tracked 변경 (staged/unstaged/conflict 포함)
# awk: untracked(??) 제외, $NF로 마지막 필드(rename 시 새 경로) 추출
ALL_TRACKED_PATHS="$(git status --porcelain | awk '!/^\?\?/ {print $NF}')"

if [ -z "$ALL_TRACKED_PATHS" ]; then
  echo "[OK] Preflight A — tracked 변경 없음"
else
  UNEXPECTED=""
  for f in $ALL_TRACKED_PATHS; do
    case " $EXPECTED_PATHS " in
      *" $f "*) ;;  # expected — pass
      *) UNEXPECTED="$UNEXPECTED $f" ;;
    esac
  done

  if [ -n "$UNEXPECTED" ]; then
    echo "[STOP] Preflight A 실패 — 옵션 A 예상 외 tracked 변경 존재:"
    git status --porcelain | awk '!/^\?\?/ {print "  " $0}'
    echo ""
    echo "처리 옵션 (택 1):"
    echo "  A. git stash push -m 'pre-option-A-\$(date +%Y%m%d-%H%M)' [pathspec] (보존, 권장)"
    echo "  B. git restore <파일> 또는 git restore --staged <파일>            (버림 — 주의)"
    echo "  C. git add <파일> && git commit -m '...'                           (별도 commit)"
    echo ""
    echo "처리 후 Preflight A 재실행 후 §2.3 sed 단계 진입"
    exit 1
  fi
  echo "[OK] Preflight A 통과 — 옵션 A pathspec 외 tracked 변경 0"
fi
```

**v2.6 → v2.7 핵심 차이**:

```diff
- DIRTY_TRACKED="$(git status --short | awk '/^ M/ {print $2}')"   # unstaged M 만
+ ALL_TRACKED_PATHS="$(git status --porcelain | awk '!/^\?\?/ {print $NF}')"  # untracked 제외 전체
```

→ staged/삭제/rename/conflict 상태도 모두 검사하고 화이트리스트(4 파일)에 없으면 차단.

### 2.2 사전 측정 (v2.6과 동일)

```bash
git fetch origin
git diff origin/main...HEAD --stat | tail -1

if ! grep -rqn "learning_proposal" engines tests app.py; then
  echo "[FAIL] 사전 0 hit"; exit 1
fi
echo "[OK] 사전 4 hit 확인"
```

### 2.3 4 파일 일괄 sed (v2.6과 동일)

```bash
sed -i '' 's/learning_proposal/learning_comparison/g' \
  engines/_base.py \
  engines/ape/__init__.py \
  engines/ape/README.md \
  tests/test_engine_registry.py
```

### 2.4 변경 검증 (v2.6과 동일)

```bash
if grep -rqn "learning_proposal" engines tests app.py; then
  echo "[FAIL] 잔존"; exit 1
fi
echo "[OK] learning_proposal 0 hit"

HIT="$(grep -rl 'learning_comparison' engines tests | wc -l | tr -d ' ')"
[ "$HIT" -eq 4 ] && echo "[OK] learning_comparison 4 hit" || { echo "[FAIL] hit=$HIT"; exit 1; }

python3 -m pytest tests/test_engine_registry.py -q   # 24 passed
python3 -m pytest tests/ -q                          # 106 passed, 7 skipped
node scripts/test_dual_eval_helpers.js               # 16 passed
```

### 2.5 commit + push (v2.6과 동일)

```bash
git add -u engines/_base.py engines/ape/__init__.py engines/ape/README.md tests/test_engine_registry.py
git commit -m "fix: APE engine_purpose learning_proposal → learning_comparison"
git push origin codex/dual-engine-execution-20260430
```

## 3. 조건 4 — PR 규모 재측정 + v2.7 갱신 (v2.6과 동일 절차)

| 측정 시점 | 결과 |
|---|---|
| v2.3 [codex] | `34 files changed, 15262 insertions(+), 55 deletions(-)` |
| v2.4 [codex] | `34 files changed, 15262 insertions(+), 55 deletions(-)` |
| v2.5 [codex] | `34 files changed, 15262 insertions(+), 55 deletions(-)` |
| v2.6 [claude 추가계획] | (옵션 A 미적용) |
| **본 v2.7 측정 (옵션 A 적용 후 — 실행 로그 §11에 기록)** | **`<TBD>`** |

## 4. PR 생성 (v2.6과 동일 절차)

URL: `https://github.com/YeChungHee/FlowBizTool/pull/new/codex/dual-engine-execution-20260430`

## 5. 조건 5 — 머지 후 8011 서버 검증 (v2.6과 동일)

§5.0 Preflight B + §5.1 재시작 + §5.2 입증 + §5.3 Stash 복구 (메시지 기반 id 추출).

## 6~10. 변경 없는 항목 (v2.6 §6~§10 그대로 계승)

- §6 요약 매트릭스
- §7 핵심 메시지
- §8 다음 액션 흐름
- §9 누적 Finding 추적 (v2.7에서 +1 = 누적 17건)
- §10 변경 없는 항목 (§3.3 후속 UI PR 등)

## 11. 실행 로그 (Phase 2 진행 — 2026-04-30 19:11 KST)

### 11.1 Phase 1 — 옵션 A 적용 + Push (Claude 자동 실행 완료)

| 단계 | 결과 | 비고 |
|---|---|---|
| Preflight A v2.7 — 첫 실행 (탐지) | ✅ [STOP] 4 unrelated 차단 | data/bizaipro_learning_registry.json, docs/flowbiz_ultra_validation_report_registry.md, tests/test_regression.py, web/bizaipro_shared.css |
| Stash 처리 | ✅ `stash@{0}: pre-option-A-20260430-1911` | 4 파일 보존 |
| Preflight A 재실행 (clean 확인) | ✅ [OK] tracked 변경 없음 | — |
| 사전 PR 규모 측정 | ✅ `34 files / 15262 / 55` | v2.4 [codex] 예측과 일치 |
| 사전 learning_proposal 4 hit 확인 | ✅ 4곳 정확 | engines/_base.py:20, engines/ape/__init__.py:37, engines/ape/README.md:12, tests/test_engine_registry.py:65 |
| 옵션 A sed (4 파일) | ✅ 완료 | `4 files changed, 4 insertions(+), 4 deletions(-)` |
| grep learning_proposal 0 hit | ✅ [OK] | — |
| grep learning_comparison 4 hit | ✅ [OK] 4 파일 모두 정정 | — |
| pytest tests/test_engine_registry.py | ✅ **24 passed** | 조건 2 [O] |
| pytest tests/ (전체) | ✅ **100 passed, 7 skipped** | 조건 3 [O]. (test_regression.py stash로 6개 차감 — 옵션 A 회귀 0건) |
| node scripts/test_dual_eval_helpers.js | ✅ **16 passed, 0 failed** | — |
| git commit `89df1eb` | ✅ | "fix: APE engine_purpose learning_proposal → learning_comparison" |
| git push origin codex/dual-engine-execution-20260430 | ✅ `e16b391..89df1eb` | — |
| **PR 규모 재측정** | ✅ **`34 files changed, 15262 insertions(+), 55 deletions(-)` (변동 없음)** | 조건 4 [O]. 4 파일이 이미 PR 포함 + line-level change → diff stat 동일 |

### 11.2 Phase 2 — PR 생성 + 머지 (사용자 수동 단계)

| 단계 | 상태 | 명령/URL |
|---|---|---|
| GitHub PR 생성 (웹 UI) | ⏳ 사용자 수동 | https://github.com/YeChungHee/FlowBizTool/pull/new/codex/dual-engine-execution-20260430 |
| PR review + merge | ⏳ 사용자 수동 | merge commit 권장 (engine.py conflict 시 6 필드 채택) |

### 11.3 Phase 3 — 머지 후 8011 활성화 (Claude 자동 실행 가능, 사용자 트리거 필요)

| 단계 | 상태 |
|---|---|
| Preflight B (main checkout 직전) | ⏳ Phase 2 완료 후 |
| 8011 재시작 | ⏳ |
| `/api/engine/list` — learning_comparison 검증 | ⏳ |
| `verify_dual_engine.sh` + 7 consensus PASSED | ⏳ 조건 5 |

### 11.4 Stash 복구 (사용자 작업 환경 복원)

```bash
# 보존 stash id
stash@{0}: On codex/dual-engine-execution-20260430: pre-option-A-20260430-1911

# 복구 명령 (사용자 결정 시점에 실행)
PRE_OPTION_STASH="$(git stash list | awk -F: '/pre-option-A/ {print $1; exit}')"
git stash pop "$PRE_OPTION_STASH"
```

**복구 시점 권장**:
- Phase 2 PR 머지 후 main checkout 전에 복구하면 Preflight B에서 차단됨 → main checkout 후에 복구
- 또는 옵션 A 작업 종료 시점에 즉시 복구하고 main checkout 시 다시 stash

## 부록 E.7. set -e 안전 + 전체 tracked 상태 검사 패턴 (v2.7 신설)

### E.7.1 untracked 제외 + 모든 tracked 상태 수집

```bash
# Pure pattern — untracked(??) 제외, 나머지 모든 상태 수집
ALL_TRACKED="$(git status --porcelain | awk '!/^\?\?/ {print}')"

# 경로만 추출 (rename 시 마지막 필드 = 새 경로)
ALL_TRACKED_PATHS="$(git status --porcelain | awk '!/^\?\?/ {print $NF}')"
```

### E.7.2 화이트리스트 필터 패턴

```bash
EXPECTED_PATHS="path1 path2 path3"

UNEXPECTED=""
for f in $ALL_TRACKED_PATHS; do
  case " $EXPECTED_PATHS " in
    *" $f "*) ;;                        # expected — skip
    *) UNEXPECTED="$UNEXPECTED $f" ;;   # collect violations
  esac
done

if [ -n "$UNEXPECTED" ]; then
  echo "[STOP] unexpected: $UNEXPECTED"
  exit 1
fi
```

### E.7.3 git status --porcelain vs --short

| 명령 | 차이 | 사용처 |
|---|---|---|
| `git status --short` | 사람이 읽기 쉬운 형식, 일부 환경 의존 | 사람이 직접 보는 용도 |
| `git status --porcelain` | 스크립트 친화적, 안정 호환 (v1) | **자동화 권장** (v2.7 채택) |

### E.7.4 안티패턴

```bash
# ❌ unstaged modified 1종만 검사 — staged/삭제/rename/conflict 통과
git status --short | awk '/^ M/ {print $2}'

# ❌ untracked 포함 — preflight 의미 흐림
git status --short | awk '{print $NF}'
```

## 부록 F. v1 → v2.7 누적 Finding 추적

| Finding | 우선순위 | v2.6 → v2.7 변화 |
|---|---|---|
| (v1~v2.5 [codex] 16 Finding) | (다양) | (v2.6 계승) |
| **F1 사용자 피드백 v2.6: Preflight A unstaged-only** | **P1** | **§2.1 porcelain + 화이트리스트 + 부록 E.7 신설** |

**누적 17 Finding 모두 v2.7까지 반영, P0/P1 잔여 0건**.

## 부록 G. v2.7 단일 실행 블록 (TL;DR — set -e 완전 안전 + porcelain 전수 검사)

```bash
set -e

cd /Users/appler/Documents/COTEX/FlowBiz_ultra

# === Preflight A v2.7: porcelain 전수 검사 ===
EXPECTED="engines/_base.py engines/ape/__init__.py engines/ape/README.md tests/test_engine_registry.py"
ALL_TRACKED_PATHS="$(git status --porcelain | awk '!/^\?\?/ {print $NF}')"

if [ -n "$ALL_TRACKED_PATHS" ]; then
  UNEXPECTED=""
  for f in $ALL_TRACKED_PATHS; do
    case " $EXPECTED " in *" $f "*) ;; *) UNEXPECTED="$UNEXPECTED $f" ;; esac
  done
  if [ -n "$UNEXPECTED" ]; then
    echo "[STOP] Preflight A: 예상 외 변경"
    git status --porcelain | awk '!/^\?\?/ {print "  " $0}'
    exit 1
  fi
fi
echo "[OK] Preflight A v2.7"

# === 사전 측정 ===
git fetch origin
git diff origin/main...HEAD --stat | tail -1
if ! grep -rqn "learning_proposal" engines tests app.py; then
  echo "[FAIL]"; exit 1
fi
echo "[OK] 사전 4 hit"

# === 옵션 A sed ===
sed -i '' 's/learning_proposal/learning_comparison/g' \
  engines/_base.py engines/ape/__init__.py engines/ape/README.md tests/test_engine_registry.py

# === 변경 검증 ===
if grep -rqn "learning_proposal" engines tests app.py; then
  echo "[FAIL] 잔존"; exit 1
fi

HIT="$(grep -rl 'learning_comparison' engines tests | wc -l | tr -d ' ')"
[ "$HIT" -eq 4 ] || { echo "[FAIL] hit=$HIT"; exit 1; }
echo "[OK] grep 검증"

python3 -m pytest tests/test_engine_registry.py -q   # 24 passed
python3 -m pytest tests/ -q                          # 106 passed, 7 skipped
node scripts/test_dual_eval_helpers.js               # 16 passed

# === commit + push ===
git add -u engines/_base.py engines/ape/__init__.py engines/ape/README.md tests/test_engine_registry.py
git commit -m "fix: APE engine_purpose learning_proposal → learning_comparison"
git push origin codex/dual-engine-execution-20260430

# === PR 규모 재측정 ===
git fetch origin
git diff origin/main...HEAD --stat | tail -1

# === [수동] PR 생성 + merge ===
# === Preflight B + 8011 재시작 + 검증 (v2.6 §5 동일) ===
```
