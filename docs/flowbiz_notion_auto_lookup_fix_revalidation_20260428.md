# FlowBiz_ultra Notion 자동조회 수정사항 재검증 보고서

- 일련번호: FBU-VAL-0012
- 작성일: 2026-04-28
- 검증 대상: FBU-VAL-0011 Finding 1~3 후속 수정 주장
- 주요 검증 파일:
  - `web/bizaipro_home.html`
  - `tests/test_regression.py`
  - `docs/flowbiz_notion_auto_lookup_implementation_validation_20260428.md`
- 검증 목적: 수동 URL 보완 후 `missingNotionReports` 오경고 방지 수정과 T20 테스트 추가 여부 확인

## 1. 종합 결론

이번 수정은 FBU-VAL-0011의 Finding 1을 해소했다.

확인된 사항:

1. 자동조회 직후 수동 URL이 있는 유형은 `missingNotionReports`에서 즉시 제거된다.
2. 수동 URL parser 실행 후 실제 summary가 주입된 유형은 최종적으로 `missingNotionReports`에서 제거된다.
3. 수동 URL이 있어도 summary가 없으면 missing 상태가 유지되어 결과서 경고 배너가 정상 표시된다.
4. T20 테스트 3개 메서드가 추가되었다.
5. 전체 pytest는 `61 passed`로 통과했다.

최종 판정: `부분 완료 — Finding 1 해소, Finding 2~4 잔여`

이번 수정 범위는 수동 보완 후 잘못된 결과서 경고를 막는 데 집중되어 있으며, FBU-VAL-0011의 나머지 이슈는 아직 남아 있다.

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
61 passed in 0.28s
```

해석:

- 이전 FBU-VAL-0011 검증 시점의 `58 passed`에서 3개 증가했다.
- 사용자가 언급한 T20 3개 메서드가 추가된 것과 일치한다.

## 3. 수정내용별 검증

### 3.1 Fix 1 — 자동조회 직후 수동 URL 보완 유형 즉시 제거

확인 위치:

- `web/bizaipro_home.html:774-788`

검증 결과:

- 수동 URL이 있는 유형은 자동조회 결과의 `missingNotionReports`에서 즉시 제거된다.
- 이 값은 `state.missingNotionReports`에 저장되므로 결과서 배너의 초기 상태가 개선된다.

판정:

- 완료

주의:

- 모달 표시 여부는 여전히 `stillMissing` 별도 계산을 사용하지만, 같은 수동 URL 조건을 사용하므로 현재 수정 의도와 일치한다.

### 3.2 Fix 2 — 수동 URL parser 완료 후 summary 기반 최종 재정리

확인 위치:

- `web/bizaipro_home.html:852-862`

검증 결과:

- 수동 URL parser 실행 후 `consultingSummary`, `meetingSummary`, `internalReviewSummary` 또는 `internalReviewValidationSummary`가 있으면 해당 유형을 `missingNotionReports`에서 제거한다.
- summary가 없으면 missing 상태가 유지된다.

판정:

- 완료

이 효과:

- 수동 URL을 입력했지만 Notion 권한 오류, 빈 본문, 파싱 실패가 발생한 경우에는 결과서 경고가 계속 표시된다.
- 수동 URL 파싱 성공 시에는 결과서의 "일부 보고서 미반영" 경고가 잘못 뜨는 문제를 막는다.

### 3.3 T20 테스트 추가

확인 위치:

- `tests/test_regression.py:807-877`

검증 결과:

- T20은 3개 메서드로 구성되어 있다.
- 검증 내용은 다음과 같다.
  - 수동 URL이 있는 유형 즉시 제거
  - summary 주입 후 최종 제거
  - summary 없음/파싱 실패 시 missing 유지

판정:

- 완료

## 4. FBU-VAL-0011 Findings 재판정

| Finding | 내용 | 이번 수정 후 상태 | 판정 |
| --- | --- | --- | --- |
| Finding 1 | 수동 보완 후 `missingNotionReports` 미재계산 | 즉시 제거 + summary 기반 최종 제거 구현 | 해소 |
| Finding 2 | 자동조회 오류가 decision gate 우회 | catch 블록에서 여전히 수동 URL 복원 후 계속 진행 | 미해소 |
| Finding 3 | FlowScore 없이 이전 companyName으로 자동조회 가능 | 조건이 여전히 `if (state.companyName)` | 미해소 |
| Finding 4 | `notionLookupStatus` shape 불일치 | 프론트에서 여전히 전체 lookup object 저장 | 미해소 |

## 5. 잔여 이슈

### 5.1 [P1] 자동조회 오류 시 decision gate 우회

확인 위치:

- `web/bizaipro_home.html:809-823`
- `web/bizaipro_home.html:871-874`

현재 상태:

- `/api/notion/auto-lookup-and-parse` 호출 실패 시 catch 블록에서 오류 로그와 수동 URL 복원만 수행한다.
- 수동 URL이 없는 경우에도 이후 `evaluateLearningState(state)`가 호출될 수 있다.

위험:

- Notion 자동조회가 실패했는데 사용자에게 `평가 취소 | 평가 진행`을 묻지 않고 FlowScore 단독 평가가 진행될 수 있다.

권고:

- 자동조회 transport/API 오류도 모달 gate 대상으로 처리한다.
- 수동 URL이 하나도 없으면 반드시 진행/취소 decision을 받아야 한다.

### 5.2 [P2] FlowScore 없이 이전 companyName으로 자동조회 가능

확인 위치:

- `web/bizaipro_home.html:736-750`

현재 상태:

- 자동조회 조건이 `if (state.companyName)`이다.
- FlowScore 파일이 없어도 이전 저장 state에 companyName이 있으면 자동조회가 실행될 수 있다.

권고:

- 자동조회 조건을 `if (flowScoreFile && state.companyName)`으로 강화한다.
- 또는 FlowScore 파일 미입력 시 학습 평가 자체를 차단한다.

### 5.3 [P2] `notionLookupStatus` shape 불일치

확인 위치:

- `app.py:716-722`
- `web/bizaipro_home.html:779-783`

현재 상태:

- 백엔드 patch의 `notionLookupStatus`는 status map이다.
- 프론트 state의 `notionLookupStatus`는 전체 lookup object로 덮인다.

권고:

- `notionLookupStatus`는 status map으로 유지한다.
- 전체 lookup object는 `notionLookupDetail` 같은 별도 필드에 저장한다.

## 6. 최종 판정

최종 판정: `부분 완료`

이번 수정으로 수동 URL 보완 후 결과서 경고가 잘못 남는 문제는 해소되었다. T20 테스트 3개도 추가되어 회귀 방지 근거가 생겼고, 전체 테스트도 `61 passed`로 통과했다.

다만 FBU-VAL-0011에서 지적한 자동조회 오류 gate, FlowScore 트리거 조건, `notionLookupStatus` shape 문제는 아직 남아 있다. 해당 3건을 수정한 뒤 `FBU-VAL-0013`으로 최종 재검증한다.
