# [codex] 듀얼 엔진 PR 머지 활성화 가이드 v2.5 검증 보고서

- 문서번호: FBU-VAL-PR-MERGE-DUAL-v2_5-20260430
- 작성일: 2026-04-30
- 검증대상: `docs/[claude]flowbiz_dual_engine_pr_merge_activation_guide_v2_5_20260430.md`
- 검증자: Codex
- 결론: **조건부 보류**

## 1. 요약

v2.5는 v2.4 검증에서 나온 두 Finding을 대부분 반영했습니다. 옵션 A 실행 전 worktree preflight와 main checkout 전 preflight가 추가되었고, `learning_proposal` 잔존 확인처럼 0 hit가 성공인 grep 검증도 `if grep ...; then [FAIL]; else [OK]; fi` 형태로 바뀌었습니다.

다만 `set -e`/자동화 안전성을 목표로 한다면, 새로 추가된 preflight의 `DIRTY="$(... | grep ...)"` 변수 대입이 clean 상태에서 먼저 실패할 수 있습니다. 또한 stash 복구 단계가 `stash@{0}`에 의존해 다른 stash를 잘못 복구할 수 있습니다.

## 2. 실측 확인

| 항목 | 결과 | 판단 |
|---|---:|---|
| 최신 `[claude]` 문서 | v2.5 | 확인 |
| `learning_proposal` 현재 잔존 | 4곳 | 문서의 사전 상태와 일치 |
| `origin/main...HEAD` diff | 34 files changed, 15262 insertions, 55 deletions | 문서와 일치 |
| `tests/test_engine_registry.py` | 24 passed | 문서와 일치 |
| 전체 pytest | 106 passed, 7 skipped | 문서와 일치 |
| Node helper | 16 passed, 0 failed | 문서와 일치 |
| closure 분리 검증 | 3구역 disjoint OK | 문서와 일치 |

## 3. Findings

### Finding 1 [P1] preflight의 grep 변수 대입이 clean 상태에서 실패 가능

- 위치: `docs/[claude]flowbiz_dual_engine_pr_merge_activation_guide_v2_5_20260430.md:59-82`, `265-277`, `479-488`, `525-528`
- 현상: v2.5는 grep zero-hit 검증을 개선했지만, preflight에는 `DIRTY_TRACKED="$(git status --short | grep '^ M' | awk ...)"`, `DIRTY="$(git status --short | grep -E ...)"`가 남아 있습니다.
- 영향: 현재처럼 dirty worktree에서는 동작하지만, 실제로 clean 상태가 되면 `grep`이 0건으로 exit code 1을 반환합니다. 이 블록이 `set -e` 환경이나 CI shell에 들어가면 `if [ -n "$DIRTY" ]`까지 도달하지 못하고 중단될 수 있습니다. v2.5가 "set -e / CI 환경 안전"을 핵심 메시지로 내세우기 때문에 실행 체크리스트 기준으로는 아직 불완전합니다.
- 재현: 임시 clean git repo에서 `set -e; DIRTY="$(git status --short | grep -E '^( M|A |D |R |C |MM)')"` 실행 시 변수 대입 단계에서 종료됩니다.
- 권고:

```bash
DIRTY_TRACKED="$(git status --short | awk '/^ M/ {print $2}')"

DIRTY="$(git status --short | awk '/^( M|A |D |R |C |MM)/ {print}')"
```

또는 grep을 유지하려면 `... | grep ... || true`를 명시해야 합니다.

### Finding 2 [P2] stash 복구가 `stash@{0}`에 의존

- 위치: `docs/[claude]flowbiz_dual_engine_pr_merge_activation_guide_v2_5_20260430.md:333-344`
- 현상: §5.3은 `git stash list | grep "pre-option-A"`로 목록을 확인한 뒤 `git stash pop "stash@{0}"`을 실행합니다.
- 영향: Preflight B에서 `pre-main-checkout` stash를 추가했거나 사용자가 중간에 다른 stash를 만들면 `stash@{0}`이 `pre-option-A`가 아닐 수 있습니다. 이 경우 잘못된 변경을 복구하거나 충돌을 만들 수 있습니다.
- 권고: stash 생성 직후 ref를 기록하거나, 복구 시 메시지로 정확한 stash id를 추출해 사용해야 합니다.

```bash
PRE_OPTION_STASH="$(git stash list | awk -F: '/pre-option-A/ {print $1; exit}')"
if [ -z "$PRE_OPTION_STASH" ]; then
  echo "[STOP] pre-option-A stash 없음"
  exit 1
fi
git stash pop "$PRE_OPTION_STASH"
```

## 4. 닫힌 항목 재확인

- v2.4 Finding 1의 핵심이었던 worktree preflight 자체는 v2.5에서 A/B로 분리되어 반영되었습니다.
- v2.4 Finding 2의 핵심이었던 `learning_proposal` 0 hit 검증은 `if grep ...` 패턴으로 반영되었습니다.
- FPE 기준 proposal/email 고정, APE 비교/학습 전용, 상담보고서 family, AppleGothic, 월간 고도화 탭은 후속 3차 UI PR 체크리스트에 계속 남아 있습니다.

## 5. 보완 후 승인 기준

1. Preflight A/B의 `grep` 변수 대입을 `awk` 또는 `|| true` 방식으로 수정
2. 부록 C TL;DR의 동일 패턴도 함께 수정
3. stash 복구를 `stash@{0}` 고정이 아니라 메시지 기반 stash id 추출로 수정

위 3개 보완 후 v2.5는 실행 승인 체크리스트로 사용할 수 있습니다.
