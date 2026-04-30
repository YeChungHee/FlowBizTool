# [codex] 듀얼 엔진 PR 머지 활성화 가이드 v2.3 검증 보고서

- 문서번호: FBU-CODEX-VAL-PR-MERGE-DUAL-v2_3-20260430
- 작성일: 2026-04-30
- 검증 트리거: 사용자 명령 `검증`
- 검증 대상: `docs/[claude]flowbiz_dual_engine_pr_merge_activation_guide_v2_3_20260430.md`
- 검증 기준:
  - 직전 `[codex]` v2.2 검증 Finding 2건
  - 과거 실행계획 v2.5/v2.6 계열 stale gate, JS helper, common helper 검증 Finding
  - 현재 FlowBiz_ultra repo 상태

## 1. 결론

`[claude]` v2.3 문서는 직전 `[codex]` v2.2 검증에서 제기한 2건을 반영했다.

| 직전 Finding | v2.3 반영 | 판단 |
|---|---|---|
| 코드 변경 목록에서 `tests/test_engine_registry.py` 누락 | §13.1 변경 위치를 4파일로 확장 | 해소 |
| 옵션 A 적용 후 PR 규모 재측정 필요 | §1.2, §10, §13.4, 부록 C에 재측정 절차 추가 | 해소 |

현재 문서 기준으로는 추가 P0/P1 Finding이 없다. PR 머지 활성화 가이드로 사용 가능하다.

단, 아직 코드에는 `learning_proposal`이 남아 있다. 이는 문서 오류가 아니라 v2.3이 명시한 “옵션 A 적용 전 상태”와 일치한다. 실제 머지 전에는 v2.3 §13의 4파일 변경을 적용하고 테스트/PR 규모 재측정을 수행해야 한다.

## 2. 실측 결과

| 항목 | 결과 |
|---|---|
| 최신 `[claude]` 문서 | `[claude]flowbiz_dual_engine_pr_merge_activation_guide_v2_3_20260430.md` |
| `origin/main...HEAD` diff | 34 files changed, 15262 insertions(+), 55 deletions(-) |
| §13 옵션 A 대상 4파일 | 모두 현재 PR 범위에 포함 |
| 현재 `learning_proposal` 잔존 | 4곳 |
| `tests/test_engine_registry.py -q` | 24 passed |
| `scripts/test_dual_eval_helpers.js` | 16 passed, 0 failed |

현재 `learning_proposal` 잔존 위치:

| 파일 | 위치 | 비고 |
|---|---:|---|
| `engines/_base.py` | 20 | META 주석 |
| `engines/ape/__init__.py` | 37 | APE META |
| `engines/ape/README.md` | 12 | README 표 |
| `tests/test_engine_registry.py` | 65 | 테스트 기대값 |

§13 옵션 A 대상 4파일은 `origin/main...HEAD` 기준 모두 PR에 이미 포함되어 있다.

```text
A engines/_base.py
A engines/ape/README.md
A engines/ape/__init__.py
A tests/test_engine_registry.py
```

따라서 옵션 A 적용 시 새 파일 수가 반드시 증가한다고 보기는 어렵다. 다만 최종 수치 정합성을 위해 v2.3이 지시한 재측정 절차는 유지해야 한다.

## 3. 과거 Findings 재점검

### 3.1 stale gate / server_input_hash 계열

과거 Finding:

- 클라이언트 `inputHash`가 백엔드 평가 입력과 불일치 가능
- 같은 기업의 입력 변경을 `state_key`가 구분하지 못함
- `stateKeyReady` 설명 문구 불일치

현재 상태:

- `/api/evaluate/dual`, `/api/learning/evaluate/dual` 응답에 `server_input_hash`가 포함된다.
- `server_input_hash`는 백엔드 `build_learning_evaluation_payload(state)` 이후 canonical `engine_input` 기준으로 생성된다.
- `tests/test_dual_consensus.py`에는 `financialFilterSignal` 변경 시 `server_input_hash`가 바뀌는 서버 테스트가 있다.
- `web/dual_eval_helpers.js`의 `_stateKeyReady()` 설명은 “모든 식별자가 빈 값이면 invalid. 최소 하나라도 있어야 valid.”로 실제 동작과 일치한다.

판단: 현재 코드/문서 기준으로 재발 징후 없음.

### 3.2 JS helper 테스트 계열

과거 Finding:

- Python 테스트가 실제 JS helper를 검증하지 않음

현재 상태:

- `scripts/test_dual_eval_helpers.js`가 실제 `web/dual_eval_helpers.js`를 `require()`해 검증한다.
- 실행 결과: 16 passed, 0 failed.
- 6개 HTML은 `dual_eval_helpers.js`를 `bizaipro_shared.js`보다 먼저 로드한다.

판단: 해소.

### 3.3 common helper 검증 계열

과거 Finding:

- `dir(c)` 기반 callable 검증은 `pathlib.Path` 같은 callable class import로 false fail 가능

현재 상태:

- `engines/common.py`는 `__all__`로 helper 목록을 명시한다.
- `scripts/extract_engine_closures.py`는 허용 common helper 목록을 별도로 관리한다.
- common.py에 `Path` import가 있지만, `__all__`에는 포함되지 않는다.

판단: 현재 구조에서는 false fail 리스크가 낮다. 향후 common 검증을 강화한다면 `__all__` 기준 또는 `inspect.isfunction(obj) and obj.__module__ == c.__name__` 기준을 유지하면 된다.

## 4. 남은 실행 전 체크

v2.3은 계획서로는 통과지만, 실제 머지 전에는 다음 작업이 필요하다.

1. v2.3 §13 옵션 A 적용

```bash
sed -i '' 's/learning_proposal/learning_comparison/g' \
  engines/_base.py \
  engines/ape/__init__.py \
  engines/ape/README.md \
  tests/test_engine_registry.py
```

2. 검증

```bash
grep -rn "learning_proposal" engines tests app.py
grep -rn "learning_comparison" engines tests
python3 -m pytest tests/test_engine_registry.py -q
python3 -m pytest tests/ -q
node scripts/test_dual_eval_helpers.js
```

3. PR 규모 재측정

```bash
git fetch origin
git diff origin/main...HEAD --stat | tail -1
```

4. v2.4 문서와 PR description의 파일 수 갱신

5. 머지 후 8011 서버 재시작 및 `verify_dual_engine.sh` 실행

## 5. 최종 판단

`[claude]` v2.3은 직전 검증의 주요 오류를 해소했다. 현재 추가 Finding은 없다.

다만 문서가 “실행 전 계획”이라는 점은 유지해야 한다. 특히 `learning_comparison` 변경은 아직 코드에 적용되지 않았고, 서버 기반 dual consensus는 라이브 서버 기동 후 검증해야 한다.

승인 조건:

- §13 옵션 A 4파일 변경 적용
- `tests/test_engine_registry.py` 24 passed 유지
- 전체 테스트 통과 또는 기존 skipped 사유 확인
- PR 규모 재측정 후 v2.4/PR description 갱신
- 머지 후 `verify_dual_engine.sh` 통과

