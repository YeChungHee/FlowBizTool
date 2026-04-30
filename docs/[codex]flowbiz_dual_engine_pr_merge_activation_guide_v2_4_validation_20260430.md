# [codex] 듀얼 엔진 PR 머지 활성화 가이드 v2.4 검증 보고서

- 문서번호: FBU-VAL-PR-MERGE-DUAL-v2_4-20260430
- 작성일: 2026-04-30
- 검증대상: `docs/[claude]flowbiz_dual_engine_pr_merge_activation_guide_v2_4_20260430.md`
- 검증자: Codex
- 결론: **조건부 보류**

## 1. 요약

v2.4 문서는 v2.3까지의 계획 검증을 실행 승인 체크리스트로 전환한 문서입니다. 핵심 방향인 `learning_proposal` → `learning_comparison` 옵션 A 적용, PR 규모 재측정, 머지 후 8011 서버 검증, FPE 기준 proposal/email 고정 원칙은 유지되어 있습니다.

다만 현재 로컬 작업트리는 이미 여러 tracked/untracked 변경을 포함하고 있어, 문서의 실행 블록을 그대로 수행하면 옵션 A 커밋 또는 머지 후 `main` 전환 단계에서 막히거나 unrelated local changes가 섞일 위험이 있습니다. 실행 체크리스트에는 **clean worktree preflight**와 **grep zero-hit 검증의 exit-code 처리**를 추가해야 합니다.

## 2. 검증 결과

| 항목 | 결과 | 판단 |
|---|---:|---|
| `learning_proposal` 현재 잔존 | 4곳 | 문서의 사전 상태와 일치 |
| `origin/main...HEAD` diff | 34 files changed, 15262 insertions, 55 deletions | 문서와 일치 |
| `tests/test_engine_registry.py` | 24 passed | 문서와 일치 |
| 전체 pytest | 106 passed, 7 skipped | 문서와 일치 |
| Node helper | 16 passed, 0 failed | 문서와 일치 |
| closure 분리 검증 | 3구역 disjoint OK | 문서와 일치 |

## 3. Findings

### Finding 1 [P1] clean worktree preflight 누락

- 위치: `docs/[claude]flowbiz_dual_engine_pr_merge_activation_guide_v2_4_20260430.md:51-64`, `194-195`
- 현상: v2.4 실행 블록은 옵션 A sed/commit 및 머지 후 `git checkout main && git pull origin main`을 안내하지만, 현재 작업트리에 이미 unrelated tracked 변경 4건과 다수 untracked 파일이 존재합니다.
- 영향: 옵션 A 커밋 범위는 pathspec으로 제한되어도, 이후 `main` 전환이 실패하거나 실행자가 unrelated 변경을 같이 정리하려다 PR/검증 상태가 흐려질 수 있습니다.
- 권고: §2.1에 `git status --short` 확인과 “예상 변경 외 tracked 변경이 있으면 중지” 조건을 추가하고, §5.1 전에도 `git status --short`가 비어 있거나 명시적으로 stash/commit된 상태에서만 `main` 전환하도록 보강해야 합니다.

### Finding 2 [P2] grep zero-hit 성공 검증이 exit-code와 충돌

- 위치: `docs/[claude]flowbiz_dual_engine_pr_merge_activation_guide_v2_4_20260430.md:78-85`, `378-379`
- 현상: 문서는 `grep -rn "learning_proposal" ...` 결과가 0 hit이면 성공이라고 설명합니다. 그러나 `grep`은 0 hit일 때 exit code 1을 반환합니다.
- 영향: v2.4가 “자동화 블록”으로 쓰이는 문서인 만큼, 실행자가 `set -e`나 CI shell에 넣으면 정상 성공 상태에서 스크립트가 중단될 수 있습니다.
- 권고: `if grep -rn "learning_proposal" engines tests app.py; then echo "[FAIL]"; exit 1; else echo "[OK]"; fi` 또는 `! grep -rn ...` 형태로 success/fail 의미를 명시해야 합니다.

## 4. 닫힌 항목 재확인

- v2.3에서 지적했던 옵션 A 대상 4파일은 모두 현재 PR diff에 포함되어 있어, 옵션 A 적용 후 파일 수가 증가하지 않을 가능성이 높습니다.
- `tests/test_engine_registry.py`는 옵션 A 변경 대상에 포함되어 있어 v2.2의 테스트 수정 누락 문제는 문서상 해소되었습니다.
- 서버 consensus는 아직 로컬 실행 조건상 skipped가 정상이며, v2.4가 §5에서 머지 후 8011 서버 검증을 별도 조건으로 분리한 점은 적절합니다.

## 5. 보완 후 승인 기준

1. §2.1에 clean worktree preflight 추가
2. §5.1 `main` checkout 전 clean/stash/commit 정책 추가
3. grep zero-hit 검증을 exit-code 안전 형태로 수정
4. 옵션 A 적용 후 `origin/main...HEAD` 재측정값을 §3.2, §6, PR description에 반영

위 1~3 보완 후 v2.4는 실행 승인 체크리스트로 사용할 수 있습니다.
