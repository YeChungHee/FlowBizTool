# [codex] 듀얼 엔진 PR 머지 활성화 가이드 v2.7 검증 보고서

- 문서번호: FBU-VAL-PR-MERGE-DUAL-v2_7-20260430
- 작성일: 2026-04-30
- 검증대상: `docs/[claude]flowbiz_dual_engine_pr_merge_activation_guide_v2_7_20260430.md`
- 검증자: Codex
- 결론: **승인 가능 — 추가 P0/P1 Finding 없음**

## 1. 요약

v2.7은 v2.6에서 남은 Preflight A 범위 문제를 반영했습니다. 기존 `^ M` 기반 unstaged modified 검사에서 `git status --porcelain` 기반 전체 tracked 상태 검사로 바뀌었고, 옵션 A 대상 4개 파일만 화이트리스트로 허용하는 구조가 문서에 들어갔습니다.

현재 코드 상태와 실행 로그도 대체로 일치합니다. `learning_proposal`은 제거되고 `learning_comparison` 4곳으로 정정되었으며, 옵션 A 커밋 `89df1eb`이 현재 브랜치와 원격 브랜치에 반영되어 있습니다.

## 2. 실측 확인

| 항목 | 결과 | 판단 |
|---|---:|---|
| 최신 `[claude]` 문서 | v2.7 | 확인 |
| 옵션 A 커밋 | `89df1eb` | 문서와 일치 |
| `learning_proposal` 잔존 | 0곳 | 통과 |
| `learning_comparison` | 4곳 | 통과 |
| 현재 tracked 변경 | 0건 | Preflight A/B 기준 통과 가능 |
| 현재 untracked 파일 | 100건 | 문서 기준 Preflight A 차단 대상 아님 |
| `origin/main...HEAD` diff | 34 files changed, 15262 insertions, 55 deletions | 문서와 일치 |
| `tests/test_engine_registry.py` | 24 passed | 문서와 일치 |
| 전체 pytest | 100 passed, 7 skipped | 문서와 일치 |
| Node helper | 16 passed, 0 failed | 문서와 일치 |
| closure 분리 검증 | 3구역 disjoint OK | 문서와 일치 |

## 3. Findings

추가 P0/P1 Finding은 없습니다.

## 4. 닫힌 항목 재확인

- v2.6 Finding: Preflight A가 `^ M`만 검사하던 문제는 `git status --porcelain | awk '!/^\?\?/ {print $NF}'` 기반으로 보강되어 닫혔습니다.
- v2.5 Finding: `set -e` clean 상태에서 preflight 변수 대입이 중단될 수 있던 문제는 `awk` 패턴으로 유지되어 닫힌 상태입니다.
- v2.5 Finding: `stash@{0}` 고정 복구 위험은 메시지 기반 stash id 추출로 유지되어 닫힌 상태입니다.
- v2.4 Finding: grep zero-hit 검증은 `if grep ...` 패턴으로 유지되어 닫힌 상태입니다.

## 5. 남은 실행 단계

현재 v2.7은 **Phase 1 완료, Phase 2 대기** 상태로 보는 것이 맞습니다.

1. GitHub PR 생성
2. PR review 및 merge
3. merge 후 `main` checkout 전 Preflight B
4. 8011 서버 재시작
5. `/api/engine/list`에서 `learning_comparison` 확인
6. `verify_dual_engine.sh` 및 7 consensus PASSED 확인

위 단계는 코드/문서 Finding이 아니라 아직 실행되지 않은 운영 단계입니다.
