# FlowBiz_ultra Notion 자동조회 구현 완료 검증 보고서

- 일련번호: FBU-VAL-0011
- 작성일: 2026-04-28
- 검증 대상: Notion 자동조회 구현 완료 주장
- 검증 대상 파일:
  - `app.py`
  - `web/bizaipro_home.html`
  - `web/bizaipro_evaluation_result.html`
  - `web/bizaipro_shared.js`
  - `tests/test_regression.py`
- 기준 문서:
  - `docs/flowbiz_notion_auto_lookup_final_plan_validation_20260428.md`
  - FBU-VAL-0010 구현 착수 전 확정 규칙

## 1. 종합 결론

구현은 핵심 구조 기준으로 상당 부분 완료되었다.

확인된 완료 항목:

1. `/api/notion/auto-lookup-and-parse` 신규 API가 추가되었다.
2. 사업자번호 정규화, 사업자번호 exact match 우선, 회사명 exact/contains fallback이 구현되었다.
3. `found_and_parsed` 이후 기존 parser/enrichment를 실행해 summary를 state에 병합한다.
4. `found_but_unreadable`, `not_found`, `token_missing`, `db_permission_error`, `ambiguous`는 primary URL에 반영하지 않는 구조가 들어갔다.
5. 프론트엔드에서 FlowScore 파싱 후 Notion 자동조회 API를 호출한다.
6. 모달 gate에서 `[평가 취소]` 시 `return`으로 `evaluateLearningState()` 호출을 막는다.
7. 결과서에 `notion_partial_evaluation_warning` 배너가 추가되었다.
8. 테스트는 기존 33개에서 58개로 증가했고 전체 통과했다.

하지만 최종 완료 판정은 아직 `조건부 보류`다. 프론트엔드 상태 보정에서 아래 잔여 문제가 확인되었다.

핵심 잔여 문제:

1. 수동 URL로 누락 보고서를 보완해도 `state.missingNotionReports`가 자동조회 당시의 누락 목록으로 유지될 수 있다.
2. FlowScore 파일이 없어도 기존 저장 state에 `companyName`이 있으면 자동조회가 실행될 수 있다.
3. 자동조회 API/네트워크 오류 시 사용자 decision gate 없이 평가가 계속 진행될 수 있다.

따라서 현재 판정은 `부분 완료 — P1 보완 후 완료 가능`이다.

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
58 passed in 0.38s
```

해석:

- FBU-VAL-0010 완료 기준인 42개 이상 테스트는 충족했다.
- T11~T19 범주의 테스트가 추가되었고, 실제 총 테스트 메서드는 58개다.
- 다만 현재 테스트는 프론트엔드에서 수동 URL 보완 후 `missingNotionReports`를 재계산하는 시나리오를 직접 검증하지 않는다.

## 3. 구현 일치성 검증

| 기준 | 구현 확인 | 판정 |
| --- | --- | --- |
| 자동조회 API | `/api/notion/auto-lookup-and-parse` 추가 | 완료 |
| 사업자번호 우선 매칭 | `_normalize_biz_num()`, `_match_notion_page()` 구현 | 완료 |
| found 후 parser 실행 | `notion_lookup_one()`에서 `parse_consulting_report_url()` 및 enrichment 호출 | 완료 |
| found_and_parsed만 primary URL 반영 | `build_notion_lookup_state_patch()`에서 status별 분기 | 완료 |
| unreadable URL metadata 보존 | `notion_lookup_one()`의 `page_url` metadata 보존 | 완료 |
| modal gate | `showNotionLookupModal()` Promise + 취소 시 `return` | 대체로 완료 |
| 결과서 독립 경고 | `notion-partial-warning-banner` 추가 | 완료 |
| 수동 URL fallback | 수동 URL이 자동 URL을 덮어쓰고 재파싱 | 부분 완료 |
| stale state 방지 | 일부 reset은 있으나 신규 Notion metadata reset 불완전 | 부분 완료 |

## 4. 주요 Findings

### Finding 1 [P1] 수동 URL 보완 후에도 `missingNotionReports`가 남을 수 있음

확인 위치:

- `web/bizaipro_home.html:774-781`
- `web/bizaipro_home.html:791-798`
- `web/bizaipro_evaluation_result.html:548-560`

현재 흐름:

1. 자동조회 결과에서 `missingNotionReports`를 받는다.
2. 수동 URL이 있으면 `state.consultingReportUrl`, `state.meetingReportUrl`, `state.internalReviewUrl`을 덮어쓴다.
3. 모달 표시 여부는 `stillMissing`으로 보정한다.
4. 하지만 `state.missingNotionReports = missingNotionReports`는 원본 누락 목록 그대로 저장한다.

문제:

- 사용자가 수동 URL로 보고서를 보완하고 실제 parser가 성공해도 결과서에는 "일부 보고서가 평가에 미반영되었습니다" 배너가 뜰 수 있다.
- 이는 FBU-VAL-0010의 "수동 URL fallback 유지"와 "found/수동 보완 항목만 평가 반영" 의도와 어긋난다.

수정 권고:

- 수동 URL 보완 후 `resolvedMissingReports`를 재계산한다.
- 수동 URL이 있고 parser가 성공한 항목은 `missingNotionReports`에서 제거한다.
- parser 실패 시에만 해당 항목을 다시 missing 또는 unreadable로 유지한다.

권장 예:

```javascript
const resolvedMissing = missingNotionReports.filter(rtype => {
  if (rtype === "consultation" && state.consultingValidationSummary) return false;
  if (rtype === "meeting" && state.meetingValidationSummary) return false;
  if (rtype === "internal_review" && state.internalReviewValidationSummary) return false;
  return true;
});
state.missingNotionReports = resolvedMissing;
```

### Finding 2 [P1] 자동조회 오류 시 decision gate 없이 평가가 계속될 수 있음

확인 위치:

- `web/bizaipro_home.html:802-816`
- `web/bizaipro_home.html:852-855`

현재 흐름:

- `/api/notion/auto-lookup-and-parse` 호출 자체가 실패하면 catch에서 경고 로그와 처리 상태만 남긴 뒤 수동 URL을 복원하고 계속 진행한다.
- 수동 URL이 없는 경우에도 이후 `evaluateLearningState(state)`가 호출된다.

문제:

- Notion DB 권한 오류나 서버 오류처럼 자동조회가 수행되지 못한 경우에도 사용자에게 `평가 취소 | 평가 진행` decision을 받지 않고 FlowScore 단독 평가가 진행될 수 있다.
- 사용자의 요구사항은 Notion 데이터가 없거나 확인되지 않는 경우 팝업으로 취소/진행을 선택하게 하는 것이다.

수정 권고:

- 자동조회 transport/API 오류도 `requires_user_decision`과 동일하게 모달 gate를 통과하도록 한다.
- 최소한 수동 URL이 하나도 없으면 "Notion 자동조회 실패" 모달을 띄우고 사용자가 진행을 선택해야 평가로 넘어가게 한다.

### Finding 3 [P2] FlowScore 파일이 없어도 기존 companyName으로 자동조회가 실행될 수 있음

확인 위치:

- `web/bizaipro_home.html:736-750`
- `web/bizaipro_shared.js:658-712`

현재 흐름:

- 자동조회 조건이 `if (state.companyName)`이다.
- `resetForLearningMode()`는 mode가 이미 learning인 경우 기존 `companyName`을 유지한다.
- 따라서 FlowScore 파일을 새로 넣지 않아도 이전 저장 state의 companyName으로 자동조회가 실행될 수 있다.

문제:

- 요구사항의 트리거는 "기업리포트 PDF 입력 시"다.
- 이전 기업명이 남아 있으면 사용자는 새 PDF를 넣지 않았는데도 과거 기업 기준 Notion 조회와 평가 흐름이 진행될 수 있다.

수정 권고:

- 자동조회 조건을 `if (flowScoreFile && state.companyName)`으로 바꾼다.
- 또는 FlowScore 미입력 시 learning 평가 자체를 차단하고 "플로우스코어 리포트를 먼저 업로드해 주세요"로 안내한다.

### Finding 4 [P2] `notionLookupStatus`의 shape가 백엔드 patch와 프론트 state에서 달라짐

확인 위치:

- `app.py:716-722`
- `web/bizaipro_home.html:779-781`

현재 흐름:

- 백엔드 `build_notion_lookup_state_patch()`는 `notionLookupStatus`를 `{ consultation: "status", ... }` 형태로 만든다.
- 프론트엔드는 이후 `state.notionLookupStatus = notionLookup`으로 전체 lookup object를 덮어쓴다.

문제:

- 동일 필드가 status map과 full lookup object라는 두 형태를 가질 수 있다.
- 향후 결과서나 테스트에서 `notionLookupStatus.consultation === "found_and_parsed"` 같은 전제를 쓰면 깨질 수 있다.

수정 권고:

- `state.notionLookupStatus`는 status map으로 유지한다.
- full lookup metadata는 별도 `state.notionLookupDetail` 또는 `state.notionLookupMetadata`로 저장한다.

## 5. FBU-VAL-0010 확정 규칙 재검증

| 규칙 | 결과 |
| --- | --- |
| found_and_parsed만 primary URL 반영 | 통과 |
| unreadable/not_found/token_missing/db_permission/ambiguous primary URL 비움 | 백엔드 기준 통과 |
| 발견 URL은 metadata 보존 | 통과 |
| 평가 취소 시 평가 API/registry 저장 미호출 | 정상 cancel path에서는 통과 |
| 진행 시 found_and_parsed만 가중치 반영 | 백엔드 기준 통과 |
| `notion_partial_evaluation_warning`과 `data_quality_warning` 독립 | 구조상 통과 |
| 상담+미팅 가중치 0.35 상한 | 통과 |
| fresh learning session state merge | 일부 보완 필요 |

## 6. 최종 판정

최종 판정: `부분 완료 — P1 보완 후 완료 가능`

구현의 핵심 백엔드 구조와 테스트는 충분히 진전되었다. 특히 FBU-VAL-0010의 가장 중요한 정정사항이었던 `found_but_unreadable` primary URL 미반영은 코드와 테스트 모두에서 반영되었다.

다만 실제 사용자 흐름에서는 수동 보완과 자동조회 실패가 중요하다. 현재 상태로 배포하면 다음 문제가 남는다.

1. 수동으로 보고서를 보완했는데도 결과서가 "보고서 미확인"이라고 표시할 수 있다.
2. Notion 자동조회 호출 자체가 실패하면 취소/진행 팝업 없이 평가가 진행될 수 있다.
3. FlowScore 파일 없이 이전 기업명으로 자동조회가 실행될 수 있다.

따라서 위 P1 2건과 P2 2건을 수정한 뒤 `FBU-VAL-0012`로 재검증한다.

## 7. 수정 우선순위

1. 수동 URL parser 성공 후 `missingNotionReports` 재계산
2. 자동조회 API 오류 시에도 decision modal 표시
3. 자동조회 조건을 `flowScoreFile && state.companyName`으로 강화
4. `notionLookupStatus`와 full lookup metadata 필드 분리
5. 위 4개에 대한 프론트/회귀 테스트 추가
