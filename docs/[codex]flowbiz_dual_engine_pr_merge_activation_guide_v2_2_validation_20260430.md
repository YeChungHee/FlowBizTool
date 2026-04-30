# [codex] 듀얼 엔진 PR 머지 활성화 가이드 v2.2 검증 보고서

- 문서번호: FBU-CODEX-VAL-PR-MERGE-DUAL-v2_2-20260430
- 작성일: 2026-04-30
- 검증 트리거: 사용자 명령 `검증`
- 검증 대상: `docs/[claude]flowbiz_dual_engine_pr_merge_activation_guide_v2_2_20260430.md`
- 기준 원칙:
  - 평가엔진 FPE는 평가/제안서/이메일의 기준값
  - 학습엔진 APE는 비교/학습/고도화 후보 전용
  - 상담보고서와 미팅보고서는 상담보고서 family로 집계하고 subtype으로 분리
  - 월간 FPE 승격은 매월 30일 13:00 보고서와 관리자 승인 후에만 진행
  - 신규 웹 UI는 AppleGothic 기반 Human Interface 기준 적용

## 1. 결론

`[claude]` v2.2 문서는 v2.1 검증에서 제기한 핵심 4건을 대부분 반영했다. 특히 FPE 고정 원칙, APE 비교 전용 원칙, 상담보고서 family, AppleGothic, 월간 고도화 탭, `origin/main...HEAD` 기준 변경은 문서에 명확히 들어갔다.

다만 실행 계획으로 쓰기 전 보완해야 할 항목이 2건 남아 있다.

1. `learning_proposal`을 `learning_comparison`으로 바꾸는 코드 동반 변경 목록에 `tests/test_engine_registry.py`가 빠져 있다.
2. 옵션 A로 코드 변경을 본 PR에 포함하면 PR 규모가 34개에서 35개 파일로 바뀌는데, 문서 여러 곳은 여전히 34개를 고정값처럼 사용한다.

현재 상태 기준 `tests/test_engine_registry.py`는 24 passed로 통과한다. 그러나 이는 아직 코드가 `learning_proposal` 상태이기 때문이다. 문서의 권장안대로 `learning_comparison`으로 실제 변경하면 테스트도 같이 수정해야 한다.

## 2. 실측 결과

| 항목 | 결과 |
|---|---|
| 최신 `[claude]` 문서 | `[claude]flowbiz_dual_engine_pr_merge_activation_guide_v2_2_20260430.md` |
| `origin/main...HEAD` diff | 34 files changed, 15262 insertions(+), 55 deletions(-) |
| `learning_proposal` 실제 잔존 | 4곳 |
| `tests/test_engine_registry.py -q` | 24 passed |
| 서버 기반 consensus | 현재 검증하지 않음. 문서와 동일하게 서버 기동 후 `verify_dual_engine.sh` 필요 |

실제 `learning_proposal` 잔존 위치:

| 파일 | 위치 | 현재 내용 |
|---|---:|---|
| `engines/_base.py` | 20 | META 주석 |
| `engines/ape/__init__.py` | 37 | `engine_purpose="learning_proposal"` |
| `engines/ape/README.md` | 12 | README META 표 |
| `tests/test_engine_registry.py` | 65 | `assert ape.META.engine_purpose == "learning_proposal"` |

## 3. Findings

### Finding 1. 코드 동반 변경 목록에서 테스트 수정이 빠짐

- 위치: `docs/[claude]flowbiz_dual_engine_pr_merge_activation_guide_v2_2_20260430.md:364-399`
- 우선순위: P1
- 현상: 문서는 `learning_proposal` → `learning_comparison` 변경 대상으로 `engines/_base.py`, `engines/ape/__init__.py`, `engines/ape/README.md` 3개 파일만 적는다.
- 실제 확인: `tests/test_engine_registry.py:65`가 여전히 `learning_proposal`을 기대한다.
- 영향: 문서대로 3개 파일만 수정하면 `tests/test_engine_registry.py`가 실패한다. 문서의 “24 passed 유지” 조건이 깨질 수 있다.
- 보완: 변경 대상에 `tests/test_engine_registry.py`를 포함한다.

권장 수정:

```text
변경 대상 4곳:
- engines/_base.py
- engines/ape/__init__.py
- engines/ape/README.md
- tests/test_engine_registry.py
```

검증 명령:

```bash
rg -n "learning_proposal" engines tests app.py
# 문서 내 Before 예시를 제외한 코드/테스트 0 hit 기대

python3 -m pytest tests/test_engine_registry.py -q
# 24 passed 기대
```

### Finding 2. 옵션 A 선택 시 PR 규모 수치가 다시 달라짐

- 위치: `docs/[claude]flowbiz_dual_engine_pr_merge_activation_guide_v2_2_20260430.md:68-72`, `docs/[claude]flowbiz_dual_engine_pr_merge_activation_guide_v2_2_20260430.md:340`, `docs/[claude]flowbiz_dual_engine_pr_merge_activation_guide_v2_2_20260430.md:378-381`
- 우선순위: P2
- 현상: 문서는 현재 PR 규모를 34개 파일로 정리하면서, 동시에 옵션 A로 `learning_comparison` 코드 변경을 본 PR에 포함하라고 권장한다.
- 문제: 옵션 A를 적용하면 최소 4개 기존 파일이 수정되며, 그중 일부가 현재 PR에 이미 포함되지 않은 파일이라면 PR 파일 수가 35개 이상으로 바뀔 수 있다. 문서도 `34 → 35` 가능성을 §13.2에서 인정하지만, §1.2와 §10은 여전히 34개를 고정값처럼 말한다.
- 영향: v2.1에서 고친 “파일 수 불일치” 문제가 옵션 A 적용 후 다시 발생할 수 있다.
- 보완: PR 규모 표기는 “현재 기준 34개, 옵션 A 적용 후 재측정”으로 바꾼다.

권장 문구:

```text
PR 규모: 현재 기준 34개 파일 변경.
단, §13 옵션 A를 본 PR에 포함하면 파일 수는 재측정 후 v2.3에 갱신한다.
최종 PR 설명에는 `git fetch origin && git diff origin/main...HEAD --stat | tail -1` 결과를 사용한다.
```

## 4. 이전 Findings 반영 상태

| 이전 Finding | v2.2 반영 상태 | 판단 |
|---|---|---|
| 3차 UI PR의 FPE 고정 원칙 누락 | 반영 | §3.3 7항 원칙으로 해소 |
| APE purpose 명칭이 proposal로 오해 가능 | 문서 반영, 코드 미반영 | 코드/테스트 동반 변경 필요 |
| 후속 UI 필수 조건 누락 | 반영 | 상담 family, 월간 탭, AppleGothic, SourceQuality 포함 |
| diff 기준은 origin/main 권장 | 반영 | §0.1과 부록 C에 반영 |

## 5. 실행 권장 순서

1. `learning_comparison` 변경을 본 PR에 포함할지 결정한다.
2. 포함한다면 변경 대상 4곳에 `tests/test_engine_registry.py`를 추가한다.
3. 변경 후 다음 명령으로 실측 수치를 다시 갱신한다.

```bash
git fetch origin
git diff origin/main...HEAD --stat | tail -1
rg -n "learning_proposal" engines tests app.py
python3 -m pytest tests/test_engine_registry.py -q
```

4. PR 규모가 34에서 바뀌면 v2.3 문서의 PR 규모와 PR description 수치를 갱신한다.
5. 서버 기반 consensus는 문서대로 8011 또는 8012 서버 기동 후 `verify_dual_engine.sh`로 확인한다.

## 6. 최종 판단

v2.2는 방향성 측면에서 조건부 승인 가능하다. FPE/APE 역할 분리, UI 원칙, 상담보고서 family, 월간 고도화 방식은 이전보다 명확하다.

다만 실행 전에는 `learning_comparison` 코드 변경 대상에 테스트 파일을 추가하고, 옵션 A 적용 후 PR 규모를 다시 측정해야 한다. 이 두 보완 후 v2.3으로 갱신하면 PR 머지 가이드로 사용할 수 있다.

