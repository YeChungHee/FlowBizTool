# FlowBiz_ultra Notion 자동조회 계획서 검증 보고서

- 일련번호: FBU-VAL-0009
- 작성일: 2026-04-28
- 검증 대상 문서:
  - `FlowBiz_Notion_자동조회_계획서_v1.0.docx`
  - `FlowBiz_Notion_자동조회_계획서_v1.1_추가.docx`
- 검증 대상 코드: `/Users/appler/Documents/COTEX/FlowBiz_ultra`
- 검증 목적: 기업리포트 PDF 업로드 후 Notion 상담·미팅·심사보고서를 자동 조회하고, 미발견 시 `평가 취소 | 평가 진행` 분기를 제공하는 계획이 현재 코드 구조와 일치하는지 확인

## 1. 종합 결론

계획의 방향은 타당하다. 현재 FlowBiz_ultra는 이미 다음 기반을 갖고 있다.

1. FlowScore PDF 파싱 엔드포인트: `/api/report/flowscore-parse`
2. Notion URL 파싱 엔드포인트: `/api/consulting/parse`, `/api/meeting/parse`, `/api/internal-review/parse`
3. Notion official API/public/html fallback 텍스트 추출 로직
4. SourceQuality 기반 update weight 판정
5. `data_quality_warning` API 응답 기반

하지만 v1.0/v1.1 계획서를 그대로 구현하면 평가 반영 누락 또는 잘못된 UX 분기가 발생할 수 있다. 가장 큰 문제는 자동 조회 결과를 `page_url`로만 주입하는 설계다. 현재 평가엔진은 URL 자체가 아니라 파싱된 `consultingValidationSummary`, `meetingValidationSummary`, `internalReviewValidationSummary` 등을 통해 평가 보너스와 결과 문구를 구성한다. 따라서 자동 조회는 "URL 찾기"에서 끝나면 안 되고, 찾은 Notion 페이지를 즉시 파싱해 state_patch까지 생성해야 한다.

최종 판정: `조건부 승인`

구현 전 필수 보완 조건:

1. 자동 조회 성공 시 URL만 주입하지 말고 기존 parser를 호출해 본문 파싱 결과까지 state에 병합한다.
2. `data_quality_warning`을 보고서 미발견 경고로 재사용한다는 v1.1 전제를 수정한다.
3. Notion DB schema, 보고서 유형 property, 회사명/사업자번호 매칭 기준을 명시한다.
4. 팝업은 평가엔진 호출 전 단계에서 반드시 띄워야 하며, 취소 시 registry 저장과 평가결과서 생성이 발생하지 않아야 한다.
5. 미팅보고서는 별도 0.35 가중치가 아니라 상담보고서 계열의 subtype으로 처리한다.

## 2. 현재 코드 기준 확인 사항

| 영역 | 현재 구현 | 계획과의 관계 |
| --- | --- | --- |
| FlowScore PDF 파싱 | `app.py`의 `/api/report/flowscore-parse`가 PDF를 읽고 `state_patch`를 반환 | 자동 조회 트리거로 사용 가능 |
| 상담보고서 파싱 | `/api/consulting/parse`가 URL을 받아 `parse_consulting_report_url()` 실행 | 자동 조회 후 재사용 필요 |
| 미팅보고서 파싱 | `/api/meeting/parse`가 상담 parser를 `source_label="미팅보고서"`로 재사용 | 미팅은 상담 subtype으로 유지 필요 |
| 심사보고서 파싱 | `/api/internal-review/parse`가 URL을 받아 `apply_internal_review_enrichment()` 실행 | 계획서의 `/api/internal/parse` 표기는 수정 필요 |
| Notion DB 조회 | `bizaipro_notion_ingest.py`에 심사보고서 batch 조회만 존재 | 상담/미팅/심사 공통 자동조회 API는 신규 개발 필요 |
| SourceQuality | URL만 있고 본문 evidence가 없으면 update weight 제외 | 자동 조회 후 본문 파싱 필수 |
| 평가 입력 | `build_learning_evaluation_payload()`가 상담/심사 validation summary로 보너스 산정 | URL 주입만으로는 평가 반영 불충분 |
| 웹 흐름 | `bizaipro_home.html`은 사용자가 URL을 입력했을 때만 parser 호출 | 자동조회·팝업 분기 신규 개발 필요 |

## 3. 계획서 v1.0 검증

### 3.1 타당한 항목

v1.0의 핵심 방향인 "FlowScore PDF 업로드 → 회사명 추출 → Notion DB 자동 조회"는 현재 UX 병목을 줄이는 방향으로 타당하다. 기존 수동 URL 입력 경로를 fallback으로 유지한다는 설계도 안전하다.

또한 Notion API 토큰은 현재 `data/api_keys.local.json`에 설정되어 있으므로, integration 공유만 맞으면 official API 경로를 사용할 수 있다.

### 3.2 수정이 필요한 항목

#### 3.2.1 자동 조회 결과를 URL만 state에 주입하면 평가 반영이 약하다

v1.0은 found 케이스에서 `page_url`을 `consultingReportUrl`, `meetingReportUrl`, `internalReviewUrl`에 자동 주입한다고 되어 있다. 하지만 현재 평가 로직은 URL 자체가 아니라 파싱된 요약·검증 결과를 사용한다.

확인 위치:

- `web/bizaipro_shared.js:950-1028`
- `app.py:3033-3116`
- `app.py:2540-2545`

현재 구조:

- 상담/미팅/심사 URL을 parser 엔드포인트에 보내야 state에 summary/cross_checks/issues가 생성된다.
- `build_learning_evaluation_payload()`는 `consultingValidationSummary`, `meetingValidationSummary`, `internalReviewValidationSummary`를 기준으로 구조 보너스를 준다.
- URL만 있으면 사용자가 보기에는 연결된 것처럼 보일 수 있지만, 평가 반영과 SourceQuality update weight는 충분하지 않다.

보완안:

- `/api/report/flowscore-parse`에서 자동 조회까지 수행한다면, 응답은 `notion_lookup`만이 아니라 `notion_parse` 또는 `notion_state_patch`를 포함해야 한다.
- 더 안전한 구조는 신규 API `/api/notion/auto-lookup-and-parse`를 만들고, FlowScore 파싱 후 프론트엔드가 이를 호출하는 방식이다.

#### 3.2.2 Notion DB schema가 부족하다

v1.0은 `NOTION_DB_ID`와 `보고서 유형`, `제목`, `상담(실사)일`을 전제로 한다. 현재 코드에서 DB 조회가 있는 곳은 `bizaipro_notion_ingest.py`이고, 이 파일은 심사보고서 batch ingest 전용이다.

확인 위치:

- `bizaipro_notion_ingest.py:27`
- `bizaipro_notion_ingest.py:89-111`

현재 구현:

- `NOTION_DB_ID = "20a16c59d686800c884cebb7816829ea"`
- filter는 `보고서 유형 = 심사보고서`에 고정
- 상담보고서/미팅보고서 자동 조회 함수는 없다.

보완안:

- 계획서에 실제 DB schema를 명시해야 한다.
- 최소 필요 property:
  - 제목 또는 Name
  - 보고서 유형
  - 업체명 또는 회사명
  - 사업자번호
  - 상담(실사)일 또는 작성일
  - 상태 또는 작성완료 여부
- 회사명 contains만으로는 오탐 위험이 있으므로 사업자번호가 있으면 사업자번호 exact match를 1순위로 둔다.

#### 3.2.3 엔드포인트 이름 불일치

v1.0 표에는 기존 심사보고서 파싱 경로가 `POST /api/internal/parse`로 되어 있다. 실제 코드는 `POST /api/internal-review/parse`다.

확인 위치:

- `app.py:3090-3116`
- `web/bizaipro_shared.js:1004-1028`

보완안:

- 계획서와 구현 지시에서는 `/api/internal-review/parse`를 기준으로 통일한다.

#### 3.2.4 미팅보고서 가중치 표현 수정 필요

v1.0 후속 고도화 제안에는 "상담(0.35)·미팅(0.35)"처럼 읽힐 수 있는 표현이 있다. 현재 프로젝트 기준에서 미팅보고서는 상담보고서의 subtype이며, 상담/미팅 중 하나 이상이 있으면 consultation component 0.35를 확보하는 구조다.

확인 위치:

- `app.py:1228-1237`
- `app.py:1294-1297`

보완안:

- `consultation_report` 가중치 0.35 안에서 상담보고서와 미팅보고서를 함께 처리한다.
- 둘 다 있을 때 0.70으로 누적하면 기존 학습 weight 계약이 깨진다.

## 4. 계획서 v1.1 검증

### 4.1 타당한 항목

`평가 취소 | 평가 진행` 팝업 분기는 필수에 가깝다. Notion 자동 조회가 실패했는데 조용히 FlowScore 단독 평가를 진행하면 사용자는 보고서가 반영된 것으로 오해할 수 있다.

또한 팝업을 보고서별로 여러 번 띄우지 않고 1회 모달에 미발견 항목을 모두 표시하는 설계는 UX 관점에서 적절하다.

### 4.2 수정이 필요한 항목

#### 4.2.1 `data_quality_warning` 재활용 전제는 현재 코드와 맞지 않는다

v1.1은 보고서 미확인 경고 배너를 기존 `data_quality_warning`으로 처리할 수 있다고 본다. 하지만 현재 `data_quality_warning`은 보고서 존재 여부가 아니라 핵심 입력 필드 결측률을 기준으로 한다.

확인 위치:

- `app.py:2566-2598`
- `app.py:3275-3294`

현재 `data_quality` 결측 기준:

- companyName
- representativeName
- businessNumber
- creditGrade
- annualSales
- buyerName
- supplierName
- requestedTenorDays
- reportIncorporatedDate

문제:

- 상담/미팅보고서와 심사보고서가 없다는 사실은 `missing_fields`에 직접 반영되지 않는다.
- FlowScore PDF가 충분한 기업정보를 제공하면 보고서가 없어도 `data_confidence`가 0.7 이상일 수 있다.
- 반대로 보고서가 모두 있어도 매입처/매출처 등이 비어 있으면 `data_quality_warning`이 발생할 수 있다.

보완안:

- 별도 상태값을 추가한다.
  - `notionLookupStatus`
  - `missingNotionReports`
  - `evaluationContinuationMode`
  - `conditionalEvaluationReason`
- 결과서 경고 배너는 `data_quality_warning`과 `missingNotionReports`를 함께 보도록 설계한다.

#### 4.2.2 팝업은 평가 호출 전에 떠야 한다

현재 웹 학습 흐름은 모든 입력/파싱 후 바로 `shared.evaluateLearningState(state)`를 호출한다.

확인 위치:

- `web/bizaipro_home.html:695-769`

v1.1 요구사항:

- 미발견 시 `[평가 취소]`는 평가결과서 작성을 취소해야 한다.
- 즉, 취소 전에 평가엔진 호출, registry 저장, 평가결과 state 저장이 발생하면 안 된다.

보완안:

- FlowScore 파싱 및 Notion 자동 조회 직후, `evaluateLearningState()` 호출 전 모달을 띄운다.
- `[평가 취소]` 선택 시:
  - 평가 호출 금지
  - registry 저장 금지
  - 결과 페이지 이동 금지
  - FlowScore 파일명/파싱 state는 유지
- `[평가 진행]` 선택 시:
  - found 항목의 파싱 state만 병합
  - missing 항목은 명시적으로 빈값 처리
  - 평가 호출

#### 4.2.3 취소 시 "입력 상태 초기화" 표현은 위험하다

v1.1은 취소 시 "입력 상태 초기화, FlowScore 파일 업로드 상태 유지"라고 쓴다. 브라우저 file input은 보안상 파일 경로를 programmatic하게 복원하기 어렵다. 또한 FlowScore 파싱 결과는 사용자가 직접 링크를 보완할 때 재사용되어야 한다.

보완안:

- "입력 상태 초기화" 대신 "평가 진행 세션만 중단, FlowScore 파싱 결과와 파일명은 유지"로 수정한다.
- file input 자체를 유지하려면 DOM reset을 하지 않아야 한다.

#### 4.2.4 Notion 미발견과 Notion 접근 실패를 분리해야 한다

v1.1은 not_found를 주로 "데이터 없음"으로 표현한다. 하지만 실제 운영에서는 다음 상태가 다르다.

1. DB에 해당 보고서가 없음
2. Notion API 토큰 없음
3. DB integration 공유 권한 없음
4. 페이지는 찾았지만 본문 추출 실패
5. 복수 후보가 있어 자동 확정 불가

보완안:

- `notion_lookup` status를 단순 boolean이 아니라 enum으로 설계한다.
  - `found_and_parsed`
  - `found_but_unreadable`
  - `not_found`
  - `token_missing`
  - `db_permission_error`
  - `ambiguous`
- 팝업 메시지도 status별로 다르게 표시한다.

## 5. 권장 수정 설계

### 5.1 백엔드 응답 구조

권장 응답:

```json
{
  "parsed_report": {},
  "state_patch": {},
  "notion_lookup": {
    "company_name_used": "해남참농가",
    "business_number_used": "000-00-00000",
    "consultation": {
      "status": "found_and_parsed",
      "report_family": "consultation",
      "subtype": "phone_or_direct",
      "page_id": "abc123",
      "page_url": "https://...",
      "title": "상담보고서 : 해남참농가",
      "state_patch": {}
    },
    "meeting": {
      "status": "not_found",
      "report_family": "consultation",
      "subtype": "meeting",
      "page_id": null,
      "page_url": null,
      "state_patch": {}
    },
    "internal_review": {
      "status": "found_but_unreadable",
      "page_id": "def456",
      "page_url": "https://...",
      "issues": ["Notion integration 공유 권한 필요"],
      "state_patch": {}
    }
  },
  "missing_notion_reports": ["meeting", "internal_review"],
  "requires_user_decision": true
}
```

### 5.2 처리 순서

권장 순서:

1. FlowScore PDF 파싱
2. 회사명/사업자번호 추출
3. Notion DB 자동 조회
4. found 후보의 본문 파싱
5. lookup 결과와 파싱 state_patch 생성
6. 미발견/본문실패/복수후보가 있으면 모달 표시
7. 취소 시 평가 중단
8. 진행 시 found_and_parsed 항목만 병합하고 평가엔진 호출
9. 결과서에 `missing_notion_reports` 경고 배너 표시

### 5.3 UI 상태값

권장 추가 state:

```json
{
  "notionLookupStatus": {
    "consultation": "found_and_parsed",
    "meeting": "not_found",
    "internal_review": "found_but_unreadable"
  },
  "missingNotionReports": ["meeting", "internal_review"],
  "evaluationContinuationMode": "flowscore_only_or_partial",
  "conditionalEvaluationReason": "상담·미팅보고서 및 심사보고서 미확인"
}
```

## 6. 테스트 계획 보완

v1.0/v1.1의 T11-T16은 방향은 맞지만 다음 테스트가 추가되어야 한다.

| 테스트 | 목적 |
| --- | --- |
| T11 | Notion DB exact match: 사업자번호 exact 우선 |
| T12 | 회사명 contains fallback 성공 |
| T13 | 복수 후보 ambiguous 처리 |
| T14 | found page를 즉시 parser에 태워 summary가 state_patch에 들어오는지 검증 |
| T15 | not_found 상태에서 모달 decision 없이는 `evaluateLearningState()`가 호출되지 않는지 검증 |
| T16 | 평가 취소 시 registry 저장이 발생하지 않는지 검증 |
| T17 | 평가 진행 시 found_and_parsed 항목만 state에 병합되는지 검증 |
| T18 | 결과서에 `missingNotionReports` 경고가 표시되는지 검증 |
| T19 | 기존 수동 URL 입력 fallback이 계속 동작하는지 검증 |

기존 33개 테스트 기준으로 최소 6개가 아니라 7~9개 추가가 적절하다.

## 7. Go/No-Go 판정

| 구분 | 판정 | 이유 |
| --- | --- | --- |
| 기능 방향 | Go | 수동 링크 입력 UX를 줄이고 자료 누락을 명시화하는 방향은 타당 |
| 현재 계획 그대로 구현 | No-Go | URL 주입만으로 평가 반영이 충분하지 않고, `data_quality_warning` 재활용 전제가 틀림 |
| 보완 후 구현 | Go | parser 재사용, 명시적 missing report state, 모달 선분기만 반영하면 현재 구조와 호환 가능 |

## 8. 구현 전 필수 수정 체크리스트

1. `/api/internal/parse` 표기를 `/api/internal-review/parse`로 수정한다.
2. Notion DB schema와 property명을 계획서에 고정한다.
3. 회사명 매칭보다 사업자번호 exact match를 우선한다.
4. 자동 조회 found 항목은 URL 저장 후 반드시 기존 parser를 실행한다.
5. `data_quality_warning`과 별도로 `missingNotionReports`를 둔다.
6. 팝업 decision 전에는 평가엔진과 registry 저장을 호출하지 않는다.
7. 미팅보고서는 상담보고서 subtype으로 처리하고 가중치를 중복 부여하지 않는다.
8. Notion 미발견, 권한 오류, 본문 미추출, 복수 후보를 서로 다른 status로 표현한다.
9. 취소 시 FlowScore 파싱 state는 유지하되 평가결과서 생성만 중단한다.

위 체크리스트 반영 후 구현을 시작하는 것이 안전하다.
