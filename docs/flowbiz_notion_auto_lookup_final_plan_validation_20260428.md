# FlowBiz_ultra Notion 자동조회 최종 계획서 검증 보고서

- 일련번호: FBU-VAL-0010
- 작성일: 2026-04-28
- 검증 대상 문서: `FlowBiz_Notion_자동조회_계획서_v2.0-Final.docx`
- 검증 대상 코드: `/Users/appler/Documents/COTEX/FlowBiz_ultra`
- 검증 목적: FBU-VAL-0009 보완 지시와 기존 Review Findings 1~7을 기준으로 v2.0-Final 계획서의 구현 가능성, 누락 리스크, 기존 로직 회귀 가능성을 검증

## 1. 종합 결론

v2.0-Final 계획서는 FBU-VAL-0009에서 지적한 핵심 보완사항을 대부분 반영했다. 특히 다음 5개가 명확해졌다.

1. URL 자동 주입만으로 끝내지 않고 found 이후 기존 parser를 실행한다.
2. `data_quality_warning`과 별도인 `notion_partial_evaluation_warning`을 둔다.
3. 팝업 decision 전에는 `evaluateLearningState()`와 registry 저장을 호출하지 않는다.
4. 사업자번호 exact match를 회사명 contains보다 우선한다.
5. 미팅보고서는 상담보고서 subtype으로 보고 consultation 가중치 0.35 상한을 유지한다.

따라서 구현 착수 판정은 `Go`다. 다만 계획서 내부에 한 가지 정정이 필요하다.

핵심 정정사항:

- `found_but_unreadable` 처리에서 "URL만 유지"와 "URL 빈값 확정"이 서로 다르게 적혀 있다.
- 구현 기준은 `평가 state의 primary URL 필드는 빈값 유지`, `발견된 page_url은 notion_lookup metadata에만 보존`으로 확정하는 것이 안전하다.

이 정정만 반영하면 v2.0-Final은 구현 계획으로 승인 가능하다.

## 2. FBU-VAL-0009 체크리스트 반영 검증

| 항목 | FBU-VAL-0009 요구 | v2.0-Final 반영 | 판정 |
| --- | --- | --- | --- |
| 1 | `/api/internal-review/parse`로 표기 통일 | 문서상 통일 반영 | 완료 |
| 2 | Notion DB schema 명시 | 제목, 보고서 유형, 사업자번호, 일자, 상태, 블록 본문 명시 | 완료 |
| 3 | 사업자번호 exact match 우선 | 사업자번호 exact → 회사명 exact → contains 순서 확정 | 완료 |
| 4 | found 후 기존 parser 실행 | URL → parser → enrichment → summary 주입 4단계 명시 | 완료 |
| 5 | `data_quality_warning`과 별도 상태 | `missingNotionReports`, `notion_partial_evaluation_warning` 신설 | 완료 |
| 6 | 평가엔진/registry 호출 전 팝업 gate | Promise resolve 후에만 `evaluateLearningState()` 호출 | 완료 |
| 7 | 미팅보고서 subtype 처리 | consultation 가중치 0.35 상한 유지 | 완료 |
| 8 | status enum 분리 | 6종 enum 명시 | 완료 |
| 9 | 취소 시 FlowScore state 유지 | DOM reset 금지, 평가 세션만 중단 | 완료 |

검증 결과:

- FBU-VAL-0009의 구현 전 필수 체크리스트는 문서상 반영되었다.
- 다만 `found_but_unreadable` URL 처리 기준만 문서 내 표현을 하나로 정리해야 한다.

## 3. 기존 Review Findings 1~7 대응 검증

| Finding | 기존 위험 | v2.0-Final 대응 | 판정 |
| --- | --- | --- | --- |
| Finding 1 | URL 존재만으로 학습 적격 처리 | found 후 parser 실행, summary 주입, SourceQuality 확인을 명시 | 해소 방향 적합 |
| Finding 2 | 업데이트 산출물이 실제 평가엔진에 미적용 | 자동조회 계획 범위 밖. 현재 코드의 `load_active_framework()` 경로 유지 필요 | 범위 외, 회귀 없음 |
| Finding 3 | CLI와 웹 학습 적격 기준 불일치 | 자동조회 결과를 웹 SourceQuality 경로에 태우는 설계 | 부분 대응 |
| Finding 4 | 결측 데이터가 기본값으로 흡수 | `data_quality_warning`과 `notion_partial_evaluation_warning` 분리 | 해소 방향 적합 |
| Finding 5 | localStorage 상태 혼입 | 계획서에서 직접 언급은 약함. 구현 시 fresh learning state 기준 merge 필요 | 구현 주의 |
| Finding 6 | registry 저장 시 SourceQuality 우회 | found_and_parsed만 primary state에 병합하면 기존 `_merged_components_from_sources()`와 호환 | 해소 방향 적합 |
| Finding 7 | promote 후 running server active framework 미반영 | 자동조회 계획 범위 밖. 현재 API active framework loader 유지 필요 | 범위 외, 회귀 없음 |

## 4. 현재 코드와의 일치성

### 4.1 기존 parser 재사용 가능

현재 코드에는 다음 parser 경로가 이미 존재한다.

- `/api/consulting/parse`
- `/api/meeting/parse`
- `/api/internal-review/parse`

이들은 모두 `parse_consulting_report_url()`을 통해 Notion official API/public/html snapshot fallback을 시도하고, 각 문서 유형에 맞는 enrichment를 생성한다. v2.0-Final의 "found 후 즉시 parser 실행" 설계는 현재 구조와 맞다.

### 4.2 SourceQuality와 호환 가능

현재 `source_quality_from_state()`는 상담/미팅의 summary가 있으면 consultation update weight를 허용하고, 내부심사 summary가 있으면 internal review update weight를 허용한다. `for_update=True`에서는 summary가 없으면 URL이 있어도 update weight를 주지 않는다.

따라서 자동조회 구현은 다음 원칙을 지켜야 한다.

- `found_and_parsed`: primary URL + summary/cross_checks/issues를 state에 병합
- `not_found`: primary URL 빈값, lookup metadata에만 status 기록
- `found_but_unreadable`: primary URL 빈값 또는 별도 metadata 보존, summary 없음, blocking issue 명시
- `ambiguous`: primary URL 확정 금지, 후보 목록 metadata만 보존

### 4.3 팝업 gate 위치가 맞다

현재 `web/bizaipro_home.html`은 모든 수동 파싱 후 바로 `evaluateLearningState(state)`를 호출한다. v2.0-Final은 이 호출 전 `requires_user_decision` gate를 두도록 명시한다. 이 위치가 맞다.

취소 시 반드시 막아야 하는 호출:

- `shared.evaluateLearningState(state)`
- `/api/learning/evaluate`
- `record_live_learning_case()`
- 결과 페이지 이동 및 평가결과서 생성

## 5. 잔여 정정사항

### 5.1 `found_but_unreadable` URL 처리 기준 통일

계획서에는 다음 두 표현이 공존한다.

1. `found_but_unreadable`: "URL만 유지, summary 없음"
2. `[평가 진행]`: "not_found / unreadable 항목 URL 빈값 명시 확정"

둘 중 구현 기준은 2번으로 통일해야 한다.

권장 확정안:

- 평가 state의 `consultingReportUrl`, `meetingReportUrl`, `internalReviewUrl`에는 unreadable URL을 넣지 않는다.
- 대신 `notion_lookup.<type>.page_url`에 발견 URL을 보존한다.
- UI에는 "페이지는 찾았지만 권한 또는 본문 문제로 평가 반영 제외"라고 표시한다.
- 사용자가 수동 오버라이드로 해당 URL을 다시 선택하거나 권한을 고친 뒤 재조회할 수 있게 한다.

이유:

- primary URL 필드에 unreadable URL을 넣으면 사용자는 보고서가 평가 반영된 것으로 오해할 수 있다.
- SourceQuality는 update weight를 막더라도, evaluation path에서는 issues 누락 시 legacy 호환 때문에 사용 가능으로 보일 여지가 있다.
- 평가결과서의 source link에도 미반영 자료가 섞일 수 있다.

### 5.2 localStorage stale merge 방지 명시 필요

Finding 5 재발 방지를 위해 자동조회 구현 시 state merge 기준을 명확히 해야 한다.

권장 기준:

- FlowScore PDF 업로드 시 `resetForLearningMode(getStoredState())` 이후 새 state를 만든다.
- 자동조회 결과는 현재 evaluation session state에만 merge한다.
- case detail/result page 진입 시에는 기존처럼 default state + 서버 state_patch 기준을 유지한다.
- 자동조회 metadata가 이전 기업의 `missingNotionReports` 또는 `notionLookupStatus`를 끌고 오지 않도록 reset 대상에 포함한다.

### 5.3 T11~T19 테스트 수와 완료 기준 정합성

v2.0-Final은 기존 33개 + 신규 9개 = 42개를 완료 기준으로 둔다. 현재 검증 시점에는 기존 33개만 존재하며 모두 통과한다.

검증 명령:

```bash
python3 -m pytest -q
```

결과:

```text
33 passed in 0.29s
```

구현 완료 후에는 반드시 42개 이상으로 증가해야 하며, 특히 T15/T16은 프론트엔드 또는 API 수준에서 "평가 미호출/registry 미저장"을 검증해야 한다.

## 6. 구현 착수 전 확정 규칙

구현 전 아래 규칙을 최종 기준으로 둔다.

1. `found_and_parsed`만 평가 state primary URL 필드에 반영한다.
2. `found_but_unreadable`, `not_found`, `token_missing`, `db_permission_error`, `ambiguous`는 primary URL을 비워 둔다.
3. 발견된 URL, 후보 목록, 권한 오류는 `notion_lookup` metadata에 보존한다.
4. 팝업에서 `[평가 취소]`를 선택하면 평가 API와 registry 저장은 절대 호출하지 않는다.
5. `[평가 진행]`을 선택해도 found_and_parsed 항목만 평가 보너스와 SourceQuality 가중치를 받는다.
6. `notion_partial_evaluation_warning`은 결과서에 별도 배너로 표시하고, `data_quality_warning`과 합치지 않는다.
7. 상담보고서와 미팅보고서가 모두 파싱되어도 consultation component는 0.35 상한을 유지한다.
8. 자동조회 결과 state는 fresh learning session state에만 병합한다.

## 7. Go/No-Go

| 구분 | 판정 | 사유 |
| --- | --- | --- |
| 계획 방향 | Go | 기존 수동 URL 입력 UX를 자동조회로 개선하고, 미발견 시 사용자 decision gate를 둠 |
| FBU-VAL-0009 반영 | Go | 체크리스트 대부분 문서상 반영 |
| 기존 Findings 재발 위험 | 조건부 Go | `found_but_unreadable` URL 처리만 정리하면 P0 재발 가능성 낮음 |
| 구현 착수 | Go | 단, 본 보고서의 `found_but_unreadable` 규칙을 구현 기준으로 적용 |

최종 판정: `Go — 단일 정정사항 반영 후 구현 착수 가능`

## 8. 후속 검증 계획

구현 완료 후 `FBU-VAL-0011`로 다음 항목을 재검증한다.

1. T11~T19 추가 여부와 총 테스트 수 42개 이상
2. Notion 자동조회 found_and_parsed의 parser/enrichment 정상 병합
3. not_found/found_but_unreadable/ambiguous의 평가 전 팝업 gate
4. 취소 시 `/api/learning/evaluate`와 registry 저장 미호출
5. 진행 시 found_and_parsed 항목만 평가 결과서에 반영
6. 결과서의 `notion_partial_evaluation_warning`과 `data_quality_warning` 독립 표시
7. 기존 수동 URL 입력 fallback 유지
