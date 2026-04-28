# FlowBiz_ultra 전체 고도화 구현 결과 검증 보고서

- 일련번호: FBU-VAL-0008
- 작성일: 2026-04-28
- 검증 대상: `/Users/appler/Documents/COTEX/FlowBiz_ultra`
- 검증 목적: 사용자가 전달한 고도화 구현 완료 내역이 전체 고도화 계획 및 FBU-VAL-0006/FBU-VAL-0007 지적사항 개선 계획과 실제로 일치하는지 재검증
- 누적관리 기준: `docs/flowbiz_ultra_validation_report_registry.md`

## 1. 종합 결론

현재 구현은 FBU-VAL-0007에서 남아 있던 핵심 P0 2건을 코드 레벨에서 상당 부분 해소했다. 특히 `record_live_learning_case()`와 `merge_learning_case_entries()`가 URL/파일명 존재 기준 대신 SourceQuality flag 기반 가중치를 사용하도록 바뀌었고, `/api/evaluate`, `/api/learning/evaluate`는 매 호출마다 `load_active_framework()`를 통해 active framework를 다시 읽는다.

다만 전체 고도화 계획 기준의 최종 완료 판정은 아직 `조건부 Go`다. 이유는 다음과 같다.

1. `data_quality_warning`은 API 응답에는 추가되었지만 웹 결과 화면에는 아직 연결되지 않았다.
2. API 응답은 `framework_meta`를 내려주지만 계획상 요구한 `framework_version` 또는 registry의 `active_version`까지 명시하지는 않는다.
3. 현재 registry 상태가 `Qualified 0건`이라 update/promote/active framework 적용의 end-to-end 운영 검증은 수행되지 못했다.
4. FastAPI endpoint smoke test는 `httpx` 미설치로 실행하지 못했고, 현재 pytest는 함수 단위 회귀 검증 중심이다.

따라서 P0 코드 수정은 완료에 가깝지만, "전체 고도화 구현 완료"로 닫으려면 화면 연결, endpoint 검증, promote 운영 시나리오 검증이 추가되어야 한다.

## 2. 검증 요약

| 항목 | 계획/수정 목표 | 실제 확인 결과 | 판정 |
| --- | --- | --- | --- |
| `merged_components` SourceQuality 기반 재작성 | URL 존재만으로 update weight 부여 금지 | `_merged_components_from_sources()` 신설, `record_live_learning_case()`, `merge_learning_case_entries()`에 적용 | 완료 |
| quality flags 저장 | merge 이후에도 SourceQuality 판정 유지 | `sources`에 `flow_score_usable_for_update`, `consultation_usable_for_update`, `internal_review_usable_for_update`, `additional_usable_for_update` 저장 | 완료 |
| URL-only 기본값 강화 | Notion URL만 있고 본문 evidence 없으면 update 제외 | `_notion_body_accessible(..., for_update=True)`에서 summary 없으면 False | 완료 |
| active framework 매 호출 재로드 | promote 후 서버 재시작 없이 평가 반영 | `engine.load_active_framework()` 신설, 평가 API 2곳에서 사용 | 코드 기준 완료 |
| API 응답에 framework 정보 포함 | 평가 결과에 사용 framework 식별값 포함 | `framework_meta` 포함. 단, `framework_version`/`active_version`은 없음 | 부분 완료 |
| data_quality 결과 화면 경고 연결 | 결측 데이터 평가를 사용자가 인지 | `/api/learning/evaluate`에 `data_quality_warning` 추가. 웹 JS/HTML 표시는 미연결 | 부분 완료 |
| 회귀 테스트 추가 | 주요 회귀 시나리오 자동 검증 | pytest 33개 통과 | 완료 |
| update/promote 운영 검증 | 생성된 framework가 실제 평가에 반영되는지 확인 | 현재 registry가 update threshold 미달이라 산출물 생성 불가 | 미검증 |

## 3. 검증 명령 및 결과

### 3.1 컴파일 검증

명령:

```bash
python3 -m py_compile app.py engine.py report_extractors.py bizaipro_learning.py external_apis.py proposal_generator.py bizaipro_notion_ingest.py
```

결과:

- 통과

### 3.2 pytest 회귀 검증

명령:

```bash
python3 -m pytest -q
```

결과:

```text
33 passed in 0.23s
```

해석:

- 사용자가 전달한 T1~T4 및 기존 회귀 테스트는 현재 모두 통과한다.
- SourceQuality merge, URL-only Notion update 제외, active framework loader, data_quality warning 계산 로직은 함수 단위로 검증되었다.
- 단, 실제 FastAPI endpoint 호출 테스트와 브라우저 화면 표시 검증은 포함되지 않았다.

### 3.3 학습 업데이트 상태 검증

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

해석:

- 현재 데이터 기준으로는 업데이트 산출물이 생성되지 않는다.
- 따라서 `framework_snapshot.json` 생성, `promote`, `data/active_framework.json` 적용, promote 후 실제 API 평가 변화는 운영 데이터로 검증되지 않았다.
- 이 부분은 테스트 fixture 기반 end-to-end 검증 또는 적격 샘플 데이터 확보 후 재검증이 필요하다.

## 4. 구현 대조 상세

### 4.1 SourceQuality 기반 merged components

확인 위치:

- `app.py:1301-1329`
- `app.py:1725-1767`
- `app.py:1795-1840`

확인 내용:

- `_source_quality_flags_from_state()`가 `source_quality_from_state()` 결과에서 update 가능 여부 flag를 추출한다.
- `_merged_components_from_sources()`는 `merged_sources`의 quality flag만으로 update weight를 계산한다.
- flag가 없는 legacy source는 기본 `False`로 처리되어 URL/파일명 존재만으로 update weight를 받지 않는다.
- `record_live_learning_case()`는 incoming source에 quality flags를 저장하고, 기존 source와 merge한 뒤 `_merged_components_from_sources()`로 재계산한다.
- `merge_learning_case_entries()`도 동일 helper를 사용한다.

판정:

- FBU-VAL-0007의 P0 registry 저장 우회 문제는 코드 기준으로 해소되었다.

잔여 확인점:

- 기존 registry에 남아 있는 legacy source는 flag가 없으면 update weight 0으로 보수 처리된다. 이 방향은 안전하지만, 과거 정상 자료까지 재평가 전까지는 update eligible에서 제외될 수 있다.

### 4.2 URL-only SourceQuality 강화

확인 위치:

- `app.py:1192-1210`
- `app.py:1236-1244`
- `app.py:1284-1298`

확인 내용:

- `_notion_body_accessible()`에 `for_update` 인자가 추가되었다.
- 평가용(`for_update=False`)은 legacy 호환을 위해 summary가 없어도 blocking issue가 없으면 허용한다.
- update용(`for_update=True`)은 summary/parsing evidence가 없으면 False로 처리한다.
- 상담/미팅보고서와 내부심사보고서의 `usable_for_update`는 `for_update=True` 기준을 사용한다.

판정:

- Notion URL-only 자료가 update weight를 받는 문제는 해소되었다.

잔여 확인점:

- FlowScore는 `reportType`이 비어 있으면 파일 존재만으로 `usable_for_update=True`가 된다. 일반 웹 파싱 경로에서는 `reportType`이 저장되지만, legacy/비정상 입력에서 파일명만 있는 경우는 추가 보강 여지가 있다.

### 4.3 active framework 적용

확인 위치:

- `engine.py:15-19`
- `engine.py:41-64`
- `app.py:3249-3263`
- `app.py:3266-3294`

확인 내용:

- `load_active_framework()`는 매 호출 시 `data/active_framework.json` 존재 여부를 다시 확인한다.
- `/api/evaluate`와 `/api/learning/evaluate`는 import 시점의 `FRAMEWORK_PATH` 대신 `load_active_framework()`를 호출한다.
- API 응답에 `framework_meta`가 포함된다.

판정:

- 실행 중 서버에서 promote 후 다음 평가 호출부터 active framework를 읽을 수 있도록 코드 경로는 수정되었다.

잔여 확인점:

- `FRAMEWORK_PATH`는 여전히 하위 호환용 import-time 값으로 남아 있다.
- `bizaipro_learning.py run_update()`는 baseline 로드에 `FRAMEWORK_PATH`를 사용하는 경로가 남아 있어, 같은 CLI 프로세스 안에서 active file 생성 시점과 맞물리는 특수 상황은 완전히 동적이지 않다.
- 운영 end-to-end 검증은 현재 update threshold 미달로 미수행이다.

### 4.4 framework version/API 응답

확인 위치:

- `engine.py:52-64`
- `app.py:3262`
- `app.py:3292`

확인 내용:

- 응답에는 `framework_meta`가 포함된다.
- meta는 `framework_path`, `source`, `filename`을 제공한다.

판정:

- 계획의 "API 응답에 framework_version 포함"은 부분 완료다.

불일치:

- 실제 키가 `framework_version`이 아니다.
- registry의 `active_version`, update id, snapshot version, framework 내부 version을 명시하지 않는다.
- 운영 로그와 결과 화면에서 어느 학습 버전으로 평가했는지 추적하려면 version 필드가 별도로 필요하다.

### 4.5 data_quality 경고 연결

확인 위치:

- `app.py:3275-3294`
- `web/bizaipro_shared.js:1086-1110`
- `web/bizaipro_evaluation_result.html:484-486`

확인 내용:

- `/api/learning/evaluate`는 `data_confidence < 0.7`이면 `data_quality_warning`을 반환한다.
- `data_quality_warning`에는 `level`, `message`, `data_confidence`, `missing_fields`가 포함된다.

불일치:

- `web/bizaipro_shared.js`의 `evaluateLearningState()`는 `payload.data_quality_warning`을 반환하지 않는다.
- 결과 화면은 `learningEligible`, `learningWeight`, `updateStatus`만 표시하며 `data_quality_warning`을 표시하지 않는다.
- 따라서 "결과 화면 경고 연결"은 아직 완료되지 않았다.

판정:

- API 레벨 부분 완료, 웹 화면 연결 미완료.

## 5. 기존 Review Findings 재판정

| Finding | 기존 문제 | 현재 상태 | 재판정 |
| --- | --- | --- | --- |
| Finding 1 | URL 존재만으로 학습 적격 처리 | Notion update 기준은 summary evidence 필수. merge도 quality flag 기반 | 해소 |
| Finding 2 | 업데이트 산출물이 실제 평가엔진에 적용되지 않음 | 평가 API 2곳이 `load_active_framework()` 사용 | 코드 해소, 운영 미검증 |
| Finding 3 | CLI와 웹 학습 적격 기준 불일치 | 기준은 일부 수렴했으나 공통 SourceQuality 모듈은 아님 | 부분 해소 |
| Finding 4 | 결측 데이터가 0점/기본값으로 평가에 흡수됨 | `data_quality_warning` API 추가. 화면 표시는 없음 | 부분 해소 |
| Finding 5 | 결과 화면 localStorage 상태 혼입 | 이전 FBU-VAL-0007에서 대체로 해소 확인 | 해소 유지 |
| Finding 6 | registry 저장 시 SourceQuality 우회 | `_merged_components_from_sources()`로 재작성 | 해소 |
| Finding 7 | promote 후 running server active framework 미반영 | `load_active_framework()`로 API 경로 수정 | 코드 해소, 운영 미검증 |

## 6. 최종 판정

최종 판정: `조건부 Go`

고도화 계획의 P0 핵심 로직은 코드 기준으로 닫혔다. 특히 학습 registry의 SourceQuality 우회와 active framework import-time 고정 문제는 이번 구현으로 직접 수정되었다.

하지만 "전체 고도화 구현 완료"로 승인하려면 아래 4개 후속 조건을 충족해야 한다.

1. `web/bizaipro_shared.js`에서 `data_quality_warning`과 `framework_meta`를 반환하고 state 또는 UI 모델에 연결한다.
2. `web/bizaipro_home.html`과 `web/bizaipro_evaluation_result.html`에 자료 부족/조건부 평가 경고를 표시한다.
3. API 응답에 `framework_version` 또는 `active_version`을 명시한다.
4. 테스트 fixture로 update/promote/end-to-end 평가 API 검증을 추가한다.

## 7. 후속 실행 계획

우선순위 순서:

1. `data_quality_warning` 웹 표시 연결
2. `framework_meta`에 `framework_version`/`active_version` 추가
3. FastAPI endpoint test 환경 보강 또는 `httpx` 의존성 추가
4. 임시 registry/update fixture로 promote 후 `/api/evaluate` 반영 테스트 추가
5. FlowScore `reportType` 누락 입력의 update gate 보수화 검토

위 5개 작업 완료 후 다음 검증번호 `FBU-VAL-0009`로 최종 운영 검증을 수행한다.
