# FlowBiz_ultra Notion 자동조회 잔여 수정 구현 검증 보고서

- 일련번호: `FBU-VAL-0014`
- 작성일: 2026-04-28
- 검증 대상: Notion 자동조회 잔여 Finding 3건 구현 반영분
- 관련 이전 보고서: `FBU-VAL-0012`, `FBU-VAL-0013`
- 결론: 완료 승인

## 1. 검증 목적

본 검증은 `FBU-VAL-0012`와 `FBU-VAL-0013`에서 남았던 Notion 자동조회 잔여 이슈가 실제 코드와 테스트에 반영되었는지 확인하기 위한 최종 구현 검증이다.

검증 범위는 다음 세 가지이다.

1. FlowScore 파일 없이 이전 세션의 `companyName`만으로 Notion 자동조회가 실행되는지 여부
2. 자동조회 결과 전체 객체가 `notionLookupStatus`를 덮어써 상태 구조가 깨지는지 여부
3. Notion 자동조회 API 오류 시 사용자 decision gate 없이 FlowScore 단독 평가로 진행되는지 여부

## 2. 검증 명령

```bash
python3 -m py_compile app.py engine.py report_extractors.py bizaipro_learning.py external_apis.py proposal_generator.py bizaipro_notion_ingest.py
python3 -m pytest -q
```

검증 결과:

- Python 주요 모듈 컴파일: 통과
- 회귀 테스트: `72 passed in 0.35s`

## 3. Finding 재판정

| 기존 Finding | 기존 위험도 | 확인 위치 | 재검증 결과 | 판정 |
| --- | --- | --- | --- | --- |
| 자동조회 오류가 decision gate를 우회 | P1 | `web/bizaipro_home.html:809-847`, `web/bizaipro_home.html:917-924` | API 오류 시 수동 URL로 보완되지 않은 유형을 `uncoveredAfterError`로 계산하고, `missing_notion_reports` 포함 모달을 호출한다. 취소 시 `NOTION_LOOKUP_CANCELLED`가 outer catch까지 전파되어 평가 API 호출로 이어지지 않는다. | 해소 |
| FlowScore 없이 이전 `companyName`으로 자동조회 가능 | P2 | `web/bizaipro_home.html:749` | 자동조회 조건이 `flowScoreFile && state.companyName`으로 변경되어 새 FlowScore 파일이 없으면 이전 상태의 기업명만으로 조회하지 않는다. | 해소 |
| `notionLookupStatus` 구조 오염 | P2 | `web/bizaipro_home.html:782` | 백엔드 `state_patch`의 status map은 `notionLookupStatus`로 유지하고, full lookup object는 `notionLookupDetail`에 분리 저장한다. | 해소 |

## 4. 구현 확인

### 4.1 FlowScore 파일 기반 자동조회 가드

`web/bizaipro_home.html`의 자동조회 조건이 다음 형태로 수정되어 있다.

```javascript
if (flowScoreFile && state.companyName) {
```

따라서 learning mode에 과거 `companyName`이 남아 있어도 새 PDF 입력이 없으면 Notion 자동조회가 실행되지 않는다.

### 4.2 상태 구조 분리

자동조회 응답 반영 후 full lookup object는 다음 필드에 저장된다.

```javascript
state.notionLookupDetail = notionLookup;
```

이로 인해 `notionLookupStatus`는 백엔드 `notionStatePatch`가 제공하는 status map 형태를 유지한다. 결과서와 후속 로직에서 status string map과 상세 객체를 혼동할 가능성이 제거되었다.

### 4.3 API 오류 시 decision gate

자동조회 API 오류 발생 시 로직은 다음 순서로 동작한다.

1. 수동 URL을 state에 복원한다.
2. 수동 URL로도 보완되지 않은 유형을 `uncoveredAfterError`로 계산한다.
3. `missing_notion_reports`를 포함한 `errorLookup` 객체를 구성한다.
4. 누락 유형이 있으면 `showNotionLookupModal(errorLookup)`을 호출한다.
5. 사용자가 취소하면 `NOTION_LOOKUP_CANCELLED`가 outer catch까지 전달되어 평가가 중단된다.

이 구조는 `FBU-VAL-0013`의 핵심 조건인 "자동조회 실패도 누락 보고서 decision gate를 반드시 통과해야 한다"는 요구와 일치한다.

## 5. 테스트 확인

`tests/test_regression.py`에 `TestNotionErrorGateAndGuards` 클래스가 추가되어 있으며, T21-1부터 T21-4까지 총 11개 메서드로 다음 내용을 검증한다.

- 자동조회 오류 후 수동 URL 보완 여부에 따른 `uncoveredAfterError` 계산
- `flowScoreFile && companyName` 자동조회 조건
- `errorLookup.missing_notion_reports` 필수 포함
- `notionLookupStatus`와 `notionLookupDetail`의 구조 분리

전체 회귀 테스트 결과는 `72 passed`로 확인되었다.

## 6. 잔여 리스크

차단 이슈는 없다.

다만 현재 검증은 코드 경로와 회귀 테스트 중심이다. 실제 운영 배포 직전에는 브라우저에서 다음 2개 시나리오를 한 번 더 스모크 테스트하는 것이 좋다.

1. Notion API 오류 + 수동 URL 없음: 모달 표시 후 `평가 취소` 선택 시 결과서 작성 중단
2. Notion API 오류 + 수동 URL 없음: 모달 표시 후 `평가 진행` 선택 시 FlowScore 단독 평가 결과서 작성

이는 승인 차단 조건이 아니라 UI 이벤트 연결 확인을 위한 운영 전 점검 항목이다.

## 7. 최종 판정

`FBU-VAL-0014` 기준으로 Notion 자동조회 잔여 수정 구현은 계획 및 이전 검증 요구사항과 일치한다.

- P1 잔여 Finding: 없음
- P2 잔여 Finding: 없음
- 자동조회 오류 decision gate: 반영 완료
- FlowScore 없는 자동조회 차단: 반영 완료
- 상태 구조 분리: 반영 완료
- 테스트 기준: `72 passed`

최종 판정: 완료 승인.
