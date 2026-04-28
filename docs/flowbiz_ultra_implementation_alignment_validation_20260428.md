# FlowBiz_ultra 고도화 구현-계획 일치성 검증 보고서

- 일련번호: FBU-VAL-0007
- 작성일: 2026-04-28
- 검증 대상: `/Users/appler/Documents/COTEX/FlowBiz_ultra`
- 검증 목적: "고도화 구현 완료" 상태가 기존 고도화 계획서 및 FBU-VAL-0006 Review Findings 개선 계획과 일치하는지 확인
- 누적관리 기준: `docs/flowbiz_ultra_validation_report_registry.md`

## 1. 결론

구현은 상당 부분 진행되었으나, 계획서 기준으로는 "완료"가 아니라 "부분 완료"다.

확인된 완료 또는 부분 완료 항목:

1. `SourceQuality` helper가 추가되었다.
2. FlowScore PDF의 `reportType`이 state에 저장된다.
3. CLI 학습 적격 기준이 웹 기준과 유사하게 조정되었다.
4. `framework_snapshot.json`과 `promote` 명령이 추가되었다.
5. `data_quality` 필드가 평가 입력에 추가되었다.
6. 결과 상세 화면의 stale localStorage 혼입 문제는 대부분 수정되었다.
7. `tests/`와 pytest 기반 회귀 테스트가 추가되었고 현재 21개 테스트가 통과한다.

하지만 핵심 P0 문제 2건은 아직 남아 있다.

1. `record_live_learning_case()`에서 SourceQuality를 계산한 뒤, registry 저장 직전에 다시 URL/파일명 존재 기준으로 `merged_components`를 계산한다. 이 때문에 Notion 권한 오류, 본문 없음, 스캔 PDF 같은 품질 실패 자료가 기존 source와 merge되는 순간 다시 학습 가중치를 받을 수 있다.
2. active framework 적용은 `FRAMEWORK_PATH`를 import 시점에 결정하는 방식이다. 서버 실행 중 `promote`로 `data/active_framework.json`이 생성되어도 이미 떠 있는 웹 서버는 baseline framework를 계속 사용할 수 있다.

따라서 현재 판정은 다음과 같다.

| 항목 | 판정 |
| --- | --- |
| SourceQuality 도입 | 부분 완료 |
| 웹 학습 registry 품질 게이트 | 미완료 |
| CLI·웹 기준 통합 | 부분 완료 |
| active framework/promote | 부분 완료 |
| 업데이트 후 실제 웹 평가 반영 | 미검증/불완전 |
| data_quality 기록 | 부분 완료 |
| 결과 화면 localStorage 혼입 방지 | 대체로 완료 |
| 회귀 테스트 | 부분 완료 |

최종 판정: `조건부 No-Go`. 구현 완료로 간주하기 전에 P0 잔여 2건을 수정해야 한다.

## 2. 검증 명령 및 결과

### 2.1 컴파일 검증

명령:

```bash
python3 -m py_compile app.py engine.py report_extractors.py bizaipro_learning.py external_apis.py proposal_generator.py bizaipro_notion_ingest.py
```

결과:

- 통과

### 2.2 pytest 검증

명령:

```bash
python3 -m pytest -q
```

결과:

```text
21 passed in 0.46s
```

테스트 자체는 통과했지만, 현재 테스트는 운영상 가장 중요한 "registry merge 후 SourceQuality 유지"와 "promote 후 running server 평가 API 반영"을 검증하지 않는다.

### 2.3 학습 상태 검증

명령:

```bash
python3 bizaipro_learning.py status
python3 bizaipro_learning.py update
```

결과:

```text
BizAiPro Learning Status
  Current version     : v.local.learning
  Total candidates    : 100
  Qualified cases     : 0
  Weighted total      : 0.00
  Ready for update    : False
  Remaining cases     : 10
  Remaining weight gap: 7.50
```

업데이트 실행 결과:

```json
{
  "update_generated": false,
  "current_version": "v.local.learning",
  "progress": {
    "total_candidates": 100,
    "qualified_cases": 0,
    "weighted_total": 0,
    "ready_for_update": false,
    "remaining_cases": 10,
    "remaining_weight_gap": 7.5
  },
  "reason": "학습 적격 10건과 최소 가중치 7.5를 충족해야 합니다."
}
```

검증 시점 registry 상태:

- 총 케이스: 100건
- 업데이트 적격: 0건
- 업데이트 내역: 0건
- active_version: 없음
- `data/active_framework.json`: 없음

즉 현재는 업데이트가 생성되지 않는 상태다. promote 적용 경로는 코드상 생겼지만 실제 업데이트 산출물과 active framework 적용은 아직 운영 검증되지 않았다.

## 3. 계획서 항목별 일치성 검증

### 3.1 SourceQuality 도입

계획:

- 자료 존재 여부와 자료 품질을 분리한다.
- `usable_for_evaluation`, `usable_for_update`를 분리한다.
- 파서 결과의 issues, summary, reportType 등을 이용해 학습 가중치를 결정한다.

구현 확인:

- `app.py`에 `source_quality_from_state()`가 추가되었다.
- `flow_score`, `consultation`, `internal_review`, `additional` 단위로 `present`, `usable_for_evaluation`, `usable_for_update`, `issues`를 반환한다.
- `learning_material_components()`가 SourceQuality 결과를 사용하도록 수정되었다.

불일치:

- `source_quality_from_state()`는 summary와 issues가 모두 없으면 Notion URL만 있어도 사용 가능으로 판단한다.
- `record_live_learning_case()`는 SourceQuality 기반 components를 계산한 뒤, 기존 source와 merge하면서 다시 URL/파일명 존재 기준으로 `merged_components`를 계산한다.
- 따라서 실제 registry 저장 결과는 SourceQuality 기준을 완전히 보장하지 않는다.

판정:

- 부분 완료

### 3.2 웹 학습 registry 품질 게이트

계획:

- 본문 추출 실패 자료는 update weight에서 제외한다.
- Notion 권한 오류 또는 본문 0자 자료는 내부심사/상담 자료로 인정하지 않는다.

구현 확인:

- `learning_material_components(state)` 단독 호출 시에는 SourceQuality 기준이 적용된다.

불일치:

- `record_live_learning_case()`의 `merged_components`가 URL/파일명 존재 기준이다.
- 기존 registry source가 남아 있는 케이스는 품질 실패 자료도 다시 양수 가중치를 받을 수 있다.
- `merge_learning_case_entries()`에도 유사한 문자열 존재 기준 계산이 남아 있을 가능성이 있다.

판정:

- 미완료

### 3.3 CLI·웹 학습 기준 통합

계획:

- CLI와 웹 모두 같은 적격 기준을 사용한다.
- `evaluation_ready`, `update_eligible`, `qualified` 의미를 통일한다.

구현 확인:

- CLI `compute_learning_weight()`는 `qualified = update_eligible`로 수정되었다.
- FlowScore + 상담 + 내부심사 조건이 맞아야 qualified가 된다.

불일치:

- CLI는 여전히 `learning_context`의 boolean과 link 존재를 기반으로 판단한다.
- 웹의 SourceQuality 객체와 CLI의 학습 품질 판단은 공통 모듈로 통합되어 있지 않다.
- CLI 입력 JSON에 Notion 본문 추출 실패, OCR 실패, parser issues가 있어도 이를 공통 품질 기준으로 처리하지 않는다.

판정:

- 부분 완료

### 3.4 active framework 및 promote

계획:

- 업데이트 산출물을 framework snapshot으로 저장한다.
- promote 후 active framework가 실제 `/api/evaluate`, `/api/learning/evaluate`에 적용된다.
- promote 전후 shadow evaluation을 수행한다.

구현 확인:

- `run_update()`가 `framework_snapshot.json`을 저장하도록 수정되었다.
- `run_promote()` 명령이 추가되었다.
- promote 시 `data/active_framework.json`을 쓰고 `active_version`을 registry에 저장한다.
- shadow evaluation을 최대 3건 수행한다.

불일치:

- `engine.py`의 `FRAMEWORK_PATH`는 import 시점에 `data/active_framework.json` 존재 여부로 결정된다.
- 이미 실행 중인 웹 서버에서 promote가 실행되면 `FRAMEWORK_PATH` 값은 자동 갱신되지 않는다.
- `/api/evaluate`와 `/api/learning/evaluate`는 매 호출마다 active pointer를 다시 읽지 않고 import된 `FRAMEWORK_PATH`를 사용한다.
- shadow evaluation은 최대 3건만 수행하며, decision 변화율, 한도 변화율, P0 오류 0건 같은 promote 차단 기준은 없다.

판정:

- 부분 완료

### 3.5 data_quality 및 결측 데이터 처리

계획:

- 결측 필드와 기본값 치환 필드를 기록한다.
- `data_confidence`를 평가 결과와 분리해서 표시한다.
- 자료 부족과 실제 위험을 구분한다.

구현 확인:

- `build_learning_evaluation_payload()`에 `data_quality`가 추가되었다.
- `missing_fields`, `defaulted_fields`, `data_confidence`가 생성된다.
- CLI `ensure_data_quality()`가 추가되었다.

불일치:

- 평가 결과 화면이나 제안서 출력에서 `data_quality`를 사용자에게 명확히 표시하지 않는다.
- `data_confidence`가 낮아도 평가 실행 또는 한도 산출을 차단하지 않는다.
- 결측 데이터는 여전히 `0`, 기본 결제유예기간 60일, 기본 업체명 등으로 엔진 입력에 흡수된다.

판정:

- 부분 완료

### 3.6 결과 화면 localStorage 혼입 방지

계획:

- case_id 결과 화면은 localStorage가 아니라 서버 snapshot 또는 기본 learning state에서 시작한다.

구현 확인:

- `web/bizaipro_evaluation_result.html`에서 `shared.getStoredState()` 대신 `shared.getDefaultState()`를 사용하도록 변경되었다.
- stale localStorage 혼입 가능성은 크게 줄었다.

잔여 확인:

- `Object.assign(shared.getDefaultState(), payload.state_patch || {})` 방식이므로 서버 patch에 없는 제안서 세부 필드는 기본 KCNC 샘플 값으로 채워질 수 있다.
- 완전한 해결은 서버가 case별 full state snapshot을 내려주거나, 결과 화면이 case state만으로 렌더링되도록 하는 것이다.

판정:

- 대체로 완료

### 3.7 테스트 체계

계획:

- pytest 기반 회귀검증을 추가한다.
- SourceQuality, learning status, active framework promote, 결과 화면 상태를 검증한다.

구현 확인:

- `tests/`, `tests/conftest.py`, `tests/test_regression.py`가 추가되었다.
- 21개 테스트가 통과한다.

불일치:

- `pytest.ini`, `pyproject.toml`, `requirements.txt`는 아직 없다.
- active framework promote 후 웹 API 반영 테스트가 없다.
- `record_live_learning_case()`가 registry 저장 시 SourceQuality를 유지하는지 검증하는 테스트가 없다.
- localStorage 혼입 방지 테스트가 없다.

판정:

- 부분 완료

## 4. Review Findings

### Finding 1. P0 registry 저장 시 SourceQuality 우회

- 위치: `app.py:1770-1808`
- 상태: 미완료

`record_live_learning_case()`는 처음에는 `learning_material_components(state)`로 SourceQuality 기반 components를 계산한다. 하지만 이후 기존 source와 병합하면서 `merged_components`를 다시 파일명/URL 문자열 존재 기준으로 계산한다.

문제 코드 흐름:

1. `components = learning_material_components(state)`
2. `learning_status = learning_status_from_components(components)`
3. `merged_sources = merge_non_empty_dict(...)`
4. `merged_components = { "flow_score_report": 0.35 if flow_score_file_name else 0.0, ... }`

이 구조에서는 SourceQuality가 실패로 판단한 자료도 기존 source에 URL이나 파일명이 있으면 registry 저장 시 다시 학습 가중치를 받을 수 있다.

영향:

- FBU-VAL-0006의 P0 문제인 "URL 존재만으로 학습 적격 처리"가 완전히 해결되지 않았다.
- Notion 권한 오류 자료나 본문 미추출 자료가 업데이트 후보로 되살아날 수 있다.

권고:

- `merged_sources`를 state 형태로 복원한 뒤 `learning_material_components(merged_state)`를 사용한다.
- 또는 source별 quality snapshot을 registry에 저장하고, merge 시 quality 기준으로 components를 재계산한다.

### Finding 2. P0 active framework가 실행 중 서버에 즉시 반영되지 않음

- 위치: `engine.py:15-17`, `app.py:3216-3235`
- 상태: 미완료

`FRAMEWORK_PATH`는 `engine.py` import 시점에 결정된다.

```python
ACTIVE_FRAMEWORK_PATH = BASE_DIR / "data" / "active_framework.json"
FRAMEWORK_PATH = ACTIVE_FRAMEWORK_PATH if ACTIVE_FRAMEWORK_PATH.exists() else BASE_DIR / "data" / "integrated_credit_rating_framework.json"
```

웹 서버가 시작될 때 `active_framework.json`이 없으면 `FRAMEWORK_PATH`는 baseline 파일로 고정된다. 이후 promote가 `active_framework.json`을 만들어도 이미 실행 중인 `/api/evaluate`, `/api/learning/evaluate`는 기존 `FRAMEWORK_PATH` 값을 계속 사용한다.

영향:

- promote를 실행해도 서버 재시작 전까지 실제 웹 평가 결과가 바뀌지 않을 수 있다.
- "업데이트 후 실제 평가 적용" 계획 요건을 충족하지 못한다.

권고:

- `load_active_framework()` 함수를 만들고 매 평가 호출 시 active pointer를 다시 읽는다.
- active metadata에 version, promoted_at, source snapshot path를 저장한다.
- `/api/evaluate` 응답에 실제 사용한 framework path/version을 포함한다.

### Finding 3. P1 SourceQuality 기본값이 URL-only 자료를 허용함

- 위치: `app.py:1190-1203`, `app.py:1218-1235`
- 상태: 부분 완료

`_notion_body_accessible()`은 summary가 없고 issues도 없으면 True를 반환한다. 또한 FlowScore는 `reportType`이 없으면 파일명만으로 usable 처리한다.

영향:

- legacy state 또는 parser를 거치지 않은 state가 들어오면 여전히 자료 존재만으로 update weight를 받을 수 있다.
- "자료 품질 기준"이 아니라 "문제 없음으로 간주"하는 fallback이 된다.

권고:

- update 기준에서는 summary, body length, parsed fields, reportType 중 최소 하나 이상의 실제 parsing evidence를 요구한다.
- legacy 호환이 필요하면 `usable_for_evaluation`만 True로 두고 `usable_for_update`는 False로 둔다.

### Finding 4. P1 data_quality가 출력/차단 로직으로 연결되지 않음

- 위치: `app.py:2533-2699`
- 상태: 부분 완료

`data_quality`는 engine input에 기록되지만, 웹 결과 화면이나 한도 산출 차단 기준에는 연결되지 않는다.

영향:

- 사용자 화면에서는 여전히 자료 부족과 실제 위험이 섞여 보일 수 있다.
- `data_confidence`가 낮아도 정상 평가처럼 한도와 제안 문구가 생성된다.

권고:

- `data_confidence < 0.7`이면 "조건부 평가" 또는 "자료 보완 필요" 상태를 표시한다.
- 평가 결과 화면 KPI에 자료 신뢰도와 누락 필드를 노출한다.
- 한도 산출 또는 promote 후보 포함 기준에 `data_confidence` 하한을 둔다.

### Finding 5. P2 테스트가 핵심 운영 경로를 아직 커버하지 않음

- 위치: `tests/test_regression.py`
- 상태: 부분 완료

현재 테스트는 SourceQuality helper, CLI weight, data_quality, 엔진 스모크를 검증한다. 그러나 이번 고도화의 핵심 운영 리스크였던 registry merge, active framework promote, 웹 API 반영은 테스트하지 않는다.

권고:

- `record_live_learning_case()`에 권한 오류 Notion 링크를 넣고 update_weight가 0인지 검증한다.
- promote 후 같은 프로세스에서 `/api/evaluate`가 active framework를 읽는지 검증한다.
- case_id 결과 화면이 default sample field를 섞지 않는지 프론트 단위 테스트 또는 최소 DOM smoke test를 추가한다.

## 5. Go / No-Go 판정

| 항목 | 판정 | 근거 |
| --- | --- | --- |
| 구현 완료 선언 | No-Go | P0 잔여 2건 |
| SourceQuality 방향성 | Go | helper와 기본 테스트는 추가됨 |
| registry 저장 로직 | No-Go | merged_components가 문자열 존재 기준으로 회귀 |
| promote 기능 | 조건부 Go | 명령은 있으나 running server 반영이 불완전 |
| 실제 평가 적용 검증 | No-Go | active framework 사용 여부가 API 응답과 테스트로 검증되지 않음 |
| 회귀 테스트 | 조건부 Go | 21개 통과하나 핵심 운영 테스트 누락 |
| 결과 화면 상태 초기화 | 조건부 Go | localStorage 혼입은 줄었으나 full snapshot 방식은 아님 |

## 6. 즉시 수정 순서

1. `record_live_learning_case()`의 `merged_components`를 SourceQuality 기반으로 재작성한다.
2. `merge_learning_case_entries()`의 components 재계산도 동일하게 SourceQuality 기반으로 수정한다.
3. `engine.py`의 import-time `FRAMEWORK_PATH` 대신 `load_active_framework()`를 구현한다.
4. `/api/evaluate`, `/api/learning/evaluate`, 상세 리포트 생성 함수가 active framework를 매 호출 기준으로 읽게 한다.
5. API 응답에 `framework_version`, `framework_path`, `active_version`을 포함한다.
6. `data_confidence`를 결과 화면에 표시하고, 낮은 신뢰도에서는 "조건부 평가"로 표시한다.
7. pytest에 registry merge, promote same-process, low data confidence 테스트를 추가한다.

## 7. 최종 판단

현재 구현은 계획서의 방향을 따라가기 시작했고 테스트도 추가되었지만, 핵심 운영 경로 2곳이 아직 계획과 일치하지 않는다.

특히 registry 저장 시 SourceQuality를 우회하는 문제와 active framework가 실행 중 서버에 즉시 적용되지 않는 문제는 고도화의 핵심 목표를 직접 훼손한다. 이 두 항목을 먼저 수정한 뒤 다시 `FBU-VAL-0008` 검증을 진행하는 것이 좋다.
