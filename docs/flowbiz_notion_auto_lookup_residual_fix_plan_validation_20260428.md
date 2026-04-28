# FlowBiz_ultra Notion 자동조회 잔여 수정계획서 검증 보고서

- 일련번호: FBU-VAL-0013
- 작성일: 2026-04-28
- 검증 대상 문서: `FBU-FIX-0001_잔여수정계획서.docx`
- 검증 대상 코드:
  - `web/bizaipro_home.html`
  - `app.py`
  - `tests/test_regression.py`
- 기준 문서:
  - `docs/flowbiz_notion_auto_lookup_fix_revalidation_20260428.md`
  - FBU-VAL-0012 잔여 이슈

## 1. 종합 결론

FBU-FIX-0001은 FBU-VAL-0012에서 남은 3건을 정확히 겨냥한다.

대상:

1. 자동조회 API/네트워크 오류 시 decision gate 우회
2. FlowScore 파일 없이 이전 `companyName`으로 자동조회 실행
3. `notionLookupStatus` shape 불일치

계획의 방향은 타당하며 구현 착수는 가능하다. 다만 Finding 2 수정안의 `errorLookup` 예시는 현재 `showNotionLookupModal()`이 기대하는 구조와 완전히 맞지 않아, 구현 전 한 가지 보완이 필요하다.

최종 판정: `조건부 Go`

보완 조건:

- 자동조회 오류용 `errorLookup`에는 반드시 `missing_notion_reports`를 포함한다.
- 수동 URL로 보완된 유형을 `found_and_parsed`로 표시하기보다는, 현 모달이 처리 가능한 범위 안에서 오해가 적은 status/message를 사용하거나 `manual_override` 표시를 별도 처리한다.

이 보완만 반영하면 FBU-FIX-0001은 잔여 3건 해소 계획으로 승인 가능하다.

## 2. 현재 상태 재확인

검증 시점 현재 테스트:

```text
61 passed in 0.28s
```

컴파일:

- `python3 -m py_compile app.py engine.py report_extractors.py bizaipro_learning.py external_apis.py proposal_generator.py bizaipro_notion_ingest.py`
- 통과

현재 코드 기준 잔여 상태:

| 항목 | 현재 코드 | FBU-FIX-0001 수정 방향 |
| --- | --- | --- |
| 자동조회 오류 gate | catch 후 수동 URL 복원만 하고 평가 진행 가능 | 오류 후 uncovered 유형 있으면 모달 gate |
| FlowScore 없는 자동조회 | `if (state.companyName)` | `if (flowScoreFile && state.companyName)` |
| `notionLookupStatus` shape | 전체 lookup object로 덮어쓰기 | `notionLookupDetail`에 full object 저장 |

## 3. 수정계획별 검증

### 3.1 Finding 2 — 자동조회 오류 시 decision gate 우회

계획 내용:

- inner catch에서 자동조회 오류 발생 후 수동 URL로 보완되지 않은 유형을 `uncoveredAfterError`로 계산한다.
- uncovered 유형이 있으면 `showNotionLookupModal()`을 호출한다.
- 사용자가 취소하면 `NOTION_LOOKUP_CANCELLED`가 outer catch까지 전파되고, outer catch에서 취소 메시지로 처리한다.

판정:

- 방향은 맞다.
- 이 구조는 FBU-VAL-0012의 P1 이슈를 닫을 수 있다.

보완 필요:

현재 `showNotionLookupModal()`은 다음 값을 읽는다.

- `lookupResult.missing_notion_reports`
- `lookupResult.token_status`
- `lookupResult.consultation.status`
- `lookupResult.meeting.status`
- `lookupResult.internal_review.status`

하지만 계획서의 `errorLookup` 예시는 `missing_notion_reports`를 넣지 않는다. 그대로 구현하면 모달 메시지의 미발견 보고서명 부분이 비어 보일 수 있다.

권장 구현:

```javascript
const errorLookup = {
  token_status: "lookup_error",
  missing_notion_reports: uncoveredAfterError,
};
["consultation", "meeting", "internal_review"].forEach(r => {
  errorLookup[r] = {
    status: uncoveredAfterError.includes(r) ? "not_found" : "found_and_parsed",
    issues: uncoveredAfterError.includes(r) ? [`Notion 자동조회 오류: ${lookupErr.message}`] : [],
  };
});
await window.showNotionLookupModal(errorLookup);
```

더 좋은 구조:

- 수동 URL로 보완된 유형은 `found_and_parsed`가 아니라 `manual_override` 같은 별도 status가 더 정확하다.
- 다만 현재 status enum과 UI가 `manual_override`를 모르면 추가 UI 작업이 필요하므로, 이번 최소 수정에서는 `missing_notion_reports` 포함을 필수 조건으로 둔다.

### 3.2 Finding 3 — FlowScore 없이 이전 companyName으로 자동조회

계획 내용:

- `if (state.companyName)`을 `if (flowScoreFile && state.companyName)`으로 변경한다.

판정:

- 타당하다.
- 요구사항의 트리거가 "기업리포트 PDF 입력 시"이므로 FlowScore 파일 존재를 조건에 넣는 것이 맞다.
- 기존 정상 경로에는 영향이 작다.

주의:

- FlowScore 파일이 없고 수동 URL만 입력한 경우에는 자동조회 없이 기존 수동 parser 경로만 작동해야 한다.
- 이 동작은 현재 구조와도 맞다.

### 3.3 Finding 4 — `notionLookupStatus` shape 불일치

계획 내용:

- `state.notionLookupStatus = notionLookup`을 제거한다.
- 전체 lookup object는 `state.notionLookupDetail = notionLookup`에 저장한다.
- `notionLookupStatus`는 백엔드 `notionStatePatch`에서 온 status map을 유지한다.

판정:

- 타당하다.
- 이 수정은 타입 안정성과 결과서/후속 코드 예측 가능성을 높인다.

주의:

- 결과서나 다른 JS에서 `notionLookupStatus`를 full object로 쓰는 곳이 없는지 `rg`로 확인해야 한다.
- 현 검증 시점 검색 결과로는 결과서 배너는 `missingNotionReports`만 사용하므로 영향은 낮다.

## 4. 테스트 계획 검증

계획서의 T21 2개는 방향은 맞지만 최소 보강이 필요하다.

계획:

1. T21-1: 자동조회 오류 후 `uncoveredAfterError` 계산
2. T21-2: `flowScoreFile` 없을 때 자동조회 skip 조건

추가 권고:

3. T21-3: `errorLookup.missing_notion_reports`가 포함되는지 검증
4. T21-4: `notionLookupStatus`는 status map, `notionLookupDetail`은 full object로 분리되는지 검증

이유:

- 이번 계획의 가장 민감한 부분은 오류 모달이 실제로 사용자에게 올바른 메시지를 보여주는지다.
- `missing_notion_reports` 누락은 코드가 동작하더라도 UX에서 바로 드러나는 결함이므로 테스트로 막는 편이 좋다.

수정 후 기대 테스트 수:

- 현재: `61 passed`
- 계획서 최소: `63+ passed`
- 권장: `65+ passed`

## 5. Go/No-Go

| 항목 | 판정 | 비고 |
| --- | --- | --- |
| Finding 2 수정 방향 | 조건부 Go | `errorLookup.missing_notion_reports` 필수 |
| Finding 3 수정 방향 | Go | 1줄 조건 강화로 충분 |
| Finding 4 수정 방향 | Go | status map/full object 분리 적절 |
| T21 테스트 계획 | 조건부 Go | 최소 2개 가능, 권장 4개 |
| 구현 착수 | Go | 단, 오류 모달 payload 구조 보완 후 진행 |

## 6. 최종 권고 구현 기준

구현 시 다음 기준을 적용한다.

1. 자동조회 오류 catch에서도 수동 URL 없는 유형이 있으면 반드시 `showNotionLookupModal()`을 호출한다.
2. 오류용 lookup payload에는 `missing_notion_reports`를 반드시 포함한다.
3. `flowScoreFile && state.companyName` 조건에서만 자동조회한다.
4. `notionLookupStatus`는 status string map으로 유지한다.
5. full lookup object는 `notionLookupDetail`에 저장한다.
6. T21은 최소 2개가 아니라 가능하면 4개로 확장한다.

최종 판정: `조건부 Go — 오류 모달 payload 보완 후 구현 착수 가능`
