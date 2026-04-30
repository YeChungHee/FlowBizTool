# [codex] 듀얼 엔진 PR 머지 활성화 가이드 v2.6 검증 보고서

- 문서번호: FBU-VAL-PR-MERGE-DUAL-v2_6-20260430
- 작성일: 2026-04-30
- 검증대상: `docs/[claude]flowbiz_dual_engine_pr_merge_activation_guide_v2_6_20260430.md`
- 검증자: Codex
- 결론: **조건부 보류**

## 1. 요약

v2.6은 v2.5 검증에서 나온 두 Finding을 대부분 반영했습니다. Preflight A/B의 `grep` 변수 대입은 `awk`로 바뀌어 `set -e` clean 상태에서도 안전해졌고, stash 복구도 `stash@{0}` 고정에서 메시지 기반 id 추출 방식으로 개선되었습니다.

다만 Preflight A가 “예상 외 tracked 변경 차단”을 목표로 하면서도 실제 구현은 `^ M` 상태만 검사합니다. staged 변경, 삭제, rename, conflict 상태의 unrelated tracked 변경은 놓칠 수 있으므로 옵션 A 실행 체크리스트로 쓰려면 tracked 상태 전체를 보도록 한 번 더 보강해야 합니다.

## 2. 실측 확인

| 항목 | 결과 | 판단 |
|---|---:|---|
| 최신 `[claude]` 문서 | v2.6 | 확인 |
| `set -e` clean repo preflight | `[OK] clean awk preflight under set -e` | v2.5 Finding 1 해소 |
| 현재 Preflight A 감지 대상 | unrelated tracked 4건 감지 | 현재 상태에서는 동작 |
| `learning_proposal` 현재 잔존 | 4곳 | 문서의 사전 상태와 일치 |
| `origin/main...HEAD` diff | 34 files changed, 15262 insertions, 55 deletions | 문서와 일치 |
| `tests/test_engine_registry.py` | 24 passed | 문서와 일치 |
| 전체 pytest | 106 passed, 7 skipped | 문서와 일치 |
| Node helper | 16 passed, 0 failed | 문서와 일치 |
| closure 분리 검증 | 3구역 disjoint OK | 문서와 일치 |

## 3. Findings

### Finding 1 [P1] Preflight A가 unstaged modified만 검사

- 위치: `docs/[claude]flowbiz_dual_engine_pr_merge_activation_guide_v2_6_20260430.md:52-78`, `484-493`
- 현상: Preflight A의 목적은 “옵션 A 예상 외 tracked 변경 차단”이지만, 실제 코드는 `git status --short | awk '/^ M/ {print $2}'`로 unstaged modified 상태만 수집합니다.
- 영향: unrelated 파일이 staged 상태(`M `), 삭제(` D`, `D `), rename(`R `), conflict(`UU`, `MM`)이면 Preflight A를 통과할 수 있습니다. 이후 `git commit`은 pathspec 4개만 stage하므로 바로 섞이지는 않더라도, 실행자가 이미 staged해 둔 unrelated 변경이 남아 있는 상태에서 push/PR 정리나 main checkout 단계가 혼탁해질 수 있습니다. v2.6이 “worktree 예상 외 tracked 변경 차단”을 승인 조건으로 삼는 만큼 검사 범위를 문구와 맞춰야 합니다.
- 권고: Preflight A도 Preflight B처럼 tracked 상태 전체를 수집하되, 옵션 A 대상 4파일만 허용해야 합니다.

```bash
DIRTY_TRACKED="$(git status --short | awk '
  /^( M|M |A | D|D |R |C |MM|UU)/ {print $2}
')"
```

또는 더 안전하게 porcelain v1을 파싱해 status code와 path를 분리하고, path가 옵션 A 4파일 외이면 중지하도록 정리하는 편이 좋습니다.

## 4. 닫힌 항목 재확인

- v2.5 Finding 1: preflight 변수 대입의 `grep` 실패 문제는 `awk` 전환으로 해소되었습니다.
- v2.5 Finding 2: stash 복구의 `stash@{0}` 고정 문제는 메시지 기반 id 추출로 해소되었습니다.
- v2.4의 `learning_proposal` zero-hit 검증은 여전히 `if grep ...` 패턴으로 유지되어 있습니다.

## 5. 보완 후 승인 기준

1. Preflight A가 `^ M`만이 아니라 staged/deleted/renamed/conflict tracked 변경까지 검사
2. 부록 C TL;DR의 Preflight A도 동일하게 수정
3. 수정 후 `set -e` clean repo 시뮬레이션과 현재 dirty worktree 감지 결과 재확인

위 3개 보완 후 v2.6은 실행 승인 체크리스트로 사용할 수 있습니다.
