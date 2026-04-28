# FlowBiz_ultra 데이터 입력·평가출력 파이프라인 검증 보고서

- 일련번호: FBU-VAL-0006
- 작성일: 2026-04-27
- 검증 대상: `/Users/appler/Documents/COTEX/FlowBiz_ultra`
- 검증 범위: 데이터 입력 파이프라인, 학습 적격 판정, 평가 입력 변환, 평가 출력 반영, 업데이트 생성 및 실제 평가 적용 로직
- 누적관리 기준: `docs/flowbiz_ultra_validation_report_registry.md`

## 1. 결론

현재 구성은 즉시 실행을 막는 문법 오류 수준의 장애는 확인되지 않았다. `app.py`, `engine.py`, `report_extractors.py`, `bizaipro_learning.py`, `external_apis.py`, `proposal_generator.py`는 컴파일 검증을 통과했다.

다만 운영 로직 기준으로는 중요한 오류 가능성이 있다.

1. 데이터 입력 파이프라인은 실제 파싱 성공 여부가 아니라 파일명과 URL 존재 여부로 학습 적격을 계산한다.
2. 평가 출력 파이프라인은 입력 자료의 결측과 실제 저성과를 충분히 구분하지 못하고 기본값 또는 0점으로 흡수한다.
3. 업데이트 산출물은 생성되더라도 실제 웹 평가 API가 사용하는 평가 프레임워크로 자동 반영되지 않는다.
4. CLI 학습 루프와 웹 학습 루프의 적격 기준이 다르다.
5. 평가 결과 화면은 브라우저 저장 상태가 섞일 수 있어 다른 기업 결과가 잔존할 가능성이 있다.

따라서 현재 시스템은 "자료를 넣으면 평가 결과는 생성되는 상태"이지만, "자료 품질 검증 후 신뢰 가능한 학습·업데이트·재평가가 자동으로 이어지는 상태"는 아니다.

## 2. Review Findings 원문

### Finding 1. P0 URL 존재만으로 학습 적격 처리

- 위치: `app.py:1185-1199`
- 우선순위: P0

현재 학습자료 판정은 실제 파싱 성공 여부가 아니라 `learningFlowScoreFileName`, `consultingReportUrl`, `meetingReportUrl`, `internalReviewUrl` 문자열 존재 여부만 본다. 그래서 Notion 권한 오류, 빈 본문, 파싱 실패 자료도 평가 반영 또는 업데이트 적격 가중치로 계산될 수 있다.

검증 판정:

- 실제 코드상 `learning_material_components`는 state에 문자열이 있는지만 확인한다.
- `parse_consulting_report_url`과 `parse_supporting_text_block`이 issues를 생성하더라도 해당 issues가 학습 가중치 차감 또는 차단에 직접 연결되지 않는다.
- 이 문제는 잘못된 학습 케이스 누적으로 이어질 수 있으므로 최우선 수정 대상이다.

### Finding 2. P0 업데이트 산출물이 실제 평가엔진에 적용되지 않음

- 위치: `bizaipro_learning.py:279-322`
- 우선순위: P0

업데이트 로직은 새 framework를 메모리에서 만들고 비교 리포트와 요약만 저장한다. 반면 `/api/evaluate`와 `/api/learning/evaluate`는 계속 고정된 `FRAMEWORK_PATH`를 로드하므로, 업데이트가 생성돼도 실제 웹 평가 결과는 바뀌지 않는다.

검증 판정:

- `run_update`는 `updated_framework`를 만들지만 실제 `data/integrated_credit_rating_framework.json`을 교체하지 않는다.
- 버전별 framework 파일 또는 active framework pointer가 없다.
- 웹 평가 API는 항상 `FRAMEWORK_PATH`를 로드한다.
- 업데이트가 생성되는 순간 "업데이트 완료"와 "실제 평가 반영" 사이에 불일치가 발생할 수 있다.

### Finding 3. P1 CLI와 웹 학습 적격 기준 불일치

- 위치: `bizaipro_learning.py:59-75`
- 우선순위: P1

CLI 학습 루프는 FlowScore와 상담자료만 있으면 `qualified=True`로 보지만, 웹/라이브 registry는 내부심사까지 있어야 `qualified=True`로 정규화한다. 같은 케이스라도 CLI status와 웹 대시보드의 적격/가중치 해석이 달라질 수 있다.

검증 판정:

- CLI `compute_learning_weight`는 `flow_score and consultation`이면 qualified로 처리한다.
- 웹 `learning_status_from_components`는 `evaluation_ready and has_internal_review`여야 update eligible로 처리한다.
- 웹 registry 정규화에서는 `qualified = update_eligible`로 저장된다.
- 운영자가 CLI와 웹을 번갈아 확인하면 적격 건수와 update readiness가 다르게 보일 수 있다.

### Finding 4. P1 결측 데이터가 0점/기본값으로 평가에 흡수됨

- 위치: `app.py:2384-2461`
- 우선순위: P1

학습 평가 입력 생성 시 매출, 영업이익, 순이익, 등급 등이 없으면 0 또는 기본 점수로 치환된다. 파싱 실패와 실제 저성과가 구분되지 않아, 자료 부족 케이스가 정상 평가처럼 출력될 수 있다.

검증 판정:

- `annual_sales or 0`, `operating_profit or 0`, `net_profit or 0` 방식으로 결측이 0으로 들어간다.
- 결제유예기간 미입력 시 60일이 기본값으로 들어간다.
- 신용등급이 없으면 기본 점수 기반 신호가 생성될 수 있다.
- 평가 결과에는 자료 부족과 실제 위험이 분리 표시되지 않는다.

### Finding 5. P2 결과 화면에 이전 localStorage 상태가 섞일 수 있음

- 위치: `web/bizaipro_evaluation_result.html:519-522`
- 우선순위: P2

케이스 상세 화면은 서버의 `state_patch`를 빈 상태가 아니라 현재 저장된 브라우저 상태 위에 `Object.assign`으로 덮어쓴다. 서버가 내려주지 않은 이전 기업/제안 필드가 남아 평가 후 작성 결과가 다른 케이스 정보와 섞일 가능성이 있다.

검증 판정:

- 결과 화면은 `shared.getStoredState()`를 먼저 읽고 서버 `state_patch`를 덮어쓴다.
- 서버 patch에 없는 proposal, email, summary 일부 필드는 이전 상태가 남을 수 있다.
- 케이스 상세 조회 화면은 localStorage가 아니라 서버 snapshot 또는 빈 learning state에서 시작해야 한다.

## 3. 현재 파이프라인 구조

### 3.1 데이터 입력 파이프라인

웹 입력 흐름은 다음 순서로 구성되어 있다.

1. 기업리포트 PDF 업로드
2. 상담보고서 Notion 링크 입력
3. 미팅보고서 Notion 링크 입력
4. 상담보고서 파일 업로드
5. 내부심사보고서 Notion 링크 입력
6. 추가 정보 입력
7. 학습 평가 API 호출
8. 결과 저장 및 대시보드 반영

주요 API는 다음과 같다.

- `/api/report/flowscore-parse`: FlowScore 또는 기업리포트 PDF 파싱
- `/api/consulting/parse`: 상담보고서 Notion 링크 파싱
- `/api/meeting/parse`: 미팅보고서 Notion 링크 파싱
- `/api/internal-review/parse`: 내부심사보고서 Notion 링크 파싱
- `/api/supporting-document/parse`: 기타 PDF, DOCX, TXT 파일 파싱
- `/api/additional-info/parse`: 추가 텍스트 정보 파싱
- `/api/learning/evaluate`: 학습모드 평가 실행 및 registry 저장

프론트엔드 실행 흐름은 `web/bizaipro_home.html`의 학습 입력 버튼 이벤트에서 순차 실행된다. 각 자료를 읽은 뒤 `shared.evaluateLearningState(state)`를 호출해 `/api/learning/evaluate`로 전달한다.

### 3.2 평가 출력 파이프라인

평가 출력은 다음 흐름으로 구성되어 있다.

1. `build_learning_evaluation_payload(state)`가 화면 상태를 엔진 입력 JSON으로 변환한다.
2. `/api/learning/evaluate`가 `FRAMEWORK_PATH`에서 평가 프레임워크를 로드한다.
3. `evaluate_flowpay_underwriting(engine_input, framework)`가 평가를 실행한다.
4. `build_web_context(engine_input, result)`가 화면 표시용 컨텍스트를 만든다.
5. `apply_learning_engine_state_patch(state, context)`가 화면 표시값을 만든다.
6. `record_live_learning_case(...)`가 registry에 케이스를 저장한다.

일반 평가 API인 `/api/evaluate`도 동일하게 `FRAMEWORK_PATH`를 직접 로드한다.

## 4. 발견 오류 및 문제점

### P0. URL 또는 파일명 존재만으로 학습 적격이 계산됨

- 위치: `app.py` `learning_material_components`
- 관련 라인: 1185-1199

현재 로직은 다음 입력값이 존재하면 가중치를 준다.

- `learningFlowScoreFileName`
- `consultingReportUrl`
- `meetingReportUrl`
- `learningConsultingFileName`
- `internalReviewUrl`
- `learningExtraInfo`

문제는 실제 파싱 성공 여부, 본문 추출 길이, Notion 권한 오류, PDF OCR 실패, 필수 항목 추출 여부를 보지 않는다는 점이다.

예를 들어 Notion 링크가 integration에 공유되지 않아 본문이 0자인 경우에도 `internalReviewUrl`이 존재하면 내부심사 자료가 있는 것으로 계산될 수 있다. 상담보고서 URL도 실제 구조화 실패와 관계없이 존재만으로 상담자료 가중치를 받을 수 있다.

영향:

- 빈 Notion 링크 또는 권한 오류 자료가 평가 반영 완료로 표시될 수 있다.
- 학습 registry에 품질 낮은 케이스가 누적될 수 있다.
- 업데이트 조건 충족 시 잘못된 케이스가 엔진 고도화 재료가 될 수 있다.

권고:

- `SourceQuality` 객체를 도입한다.
- `usable_for_evaluation`과 `usable_for_update`를 분리한다.
- 학습 가중치는 URL/파일명 존재가 아니라 파싱 결과 품질 기준으로 계산한다.

예시 기준:

- FlowScore PDF: `learning_ready.usable == true`, 회사명, 등급, 재무 요약 중 최소 2개 이상 추출
- 상담보고서: `body_text` 길이, summary 존재, issues에 본문 비어 있음 또는 권한 오류 없음
- 내부심사보고서: official API 또는 public snapshot으로 본문 추출 성공, summary 또는 cross_checks 존재
- 추가자료: summary 또는 supplier/buyer/tenor 중 1개 이상 추출

### P0. 업데이트 산출물이 실제 평가 API에 자동 적용되지 않음

- 위치: `bizaipro_learning.py` `run_update`
- 관련 라인: 279-322
- 평가 API 위치: `app.py` `/api/evaluate`, `/api/learning/evaluate`
- 관련 라인: 3094-3118

업데이트 로직은 다음 산출물을 만든다.

- `outputs/updates/{version}/comparison_report.md`
- `outputs/updates/{version}/update_summary.json`
- registry의 `current_version` 변경

하지만 실제 웹 평가 API는 계속 `FRAMEWORK_PATH`를 로드한다.

- `FRAMEWORK_PATH = data/integrated_credit_rating_framework.json`
- `/api/evaluate`는 매번 `load_json(FRAMEWORK_PATH)` 실행
- `/api/learning/evaluate`도 매번 `load_json(FRAMEWORK_PATH)` 실행

즉, 업데이트가 생성되어도 실제 평가 프레임워크 파일은 바뀌지 않는다. registry의 버전명만 바뀌고 웹 평가 결과는 동일하게 유지될 수 있다.

영향:

- 사용자는 "업데이트 생성됨"으로 보지만 실제 평가 결과는 바뀌지 않을 수 있다.
- 업데이트 전후 비교 리포트와 운영 평가 결과가 불일치할 수 있다.
- 고도화된 엔진을 선택하거나 rollback하는 체계가 없다.

권고:

- 업데이트된 framework JSON을 버전별로 저장한다.
- active framework pointer를 둔다.
- `/api/evaluate`, `/api/learning/evaluate`가 active framework를 로드하도록 변경한다.
- promote 명령 또는 승인 API를 만들어 검증 통과 후 active 버전을 전환한다.
- 업데이트 전후 shadow evaluation 결과를 저장한다.

권장 구조:

```text
data/frameworks/
  v.local.learning.json
  v.1.18.01.json
data/active_framework.json
outputs/updates/{version}/comparison_report.md
outputs/updates/{version}/shadow_evaluation.json
```

### P1. CLI 학습 루프와 웹 학습 루프의 적격 기준이 다름

- CLI 위치: `bizaipro_learning.py` `compute_learning_weight`
- 관련 라인: 59-75
- 웹 위치: `app.py` `learning_status_from_components`
- 관련 라인: 1219-1231

CLI 기준:

- FlowScore 제출 + 상담자료 제출이면 `qualified = true`
- 내부심사는 가중치만 추가

웹 기준:

- FlowScore + 상담자료가 있으면 `evaluation_ready = true`
- 내부심사까지 있어야 `update_eligible = true`
- `qualified = update_eligible`

영향:

- 같은 케이스가 CLI에서는 학습 적격, 웹에서는 업데이트 적격 아님으로 표시될 수 있다.
- `python3 bizaipro_learning.py status`와 웹 대시보드의 숫자가 다르게 해석될 수 있다.
- 업데이트 생성 조건의 의미가 혼선된다.

권고:

- 공통 `learning_status` 모듈로 분리한다.
- `evaluation_ready`, `update_candidate`, `update_qualified`를 명확히 분리한다.
- CLI와 웹 모두 같은 함수로 판단한다.

### P1. 결측 데이터가 0점 또는 기본값으로 평가에 흡수됨

- 위치: `app.py` `build_learning_evaluation_payload`
- 관련 라인: 2384-2461

현재 변환 로직은 매출, 영업이익, 순이익, 신용등급, 결제유예기간 등이 없을 때 기본값을 사용한다.

예시:

- `annual_sales or 0`
- `operating_profit or 0`
- `net_profit or 0`
- 등급 미확인 시 `grade_to_signal_score(..., 55.0)`
- 결제유예기간 미입력 시 60일
- 영업이익 없거나 음수일 때 이자보상배율 0.8

이 방식은 평가 실행 안정성에는 도움이 되지만, 파싱 실패와 실제 저성과를 구분하지 못한다.

영향:

- 자료 부족 기업이 실제 부실 기업처럼 낮은 점수를 받을 수 있다.
- 반대로 일부 기본값은 실제 위험보다 완화된 평가를 만들 수 있다.
- 결과 보고서에서 "자료 미확인"과 "평가상 부정적 신호"가 혼재될 수 있다.

권고:

- `missing_fields`와 `derived_defaults`를 engine_input에 명시한다.
- 필수 필드 누락 시 평가 등급과 별도로 `data_confidence`를 출력한다.
- 자료 부족 시 한도 산출은 차단하거나 "조건부 산출"로 표시한다.

### P2. 결과 화면에서 이전 localStorage 상태가 섞일 수 있음

- 위치: `web/bizaipro_evaluation_result.html`
- 관련 라인: 519-522

케이스 상세 화면은 서버에서 받은 `state_patch`를 현재 브라우저 저장 상태에 덮어쓴다.

현재 방식:

```javascript
const state = shared.getStoredState();
Object.assign(state, payload.state_patch || {});
shared.saveState(state);
```

문제는 서버가 내려주지 않은 필드가 이전 기업 상태로 남을 수 있다는 점이다. 예를 들어 제안서 문구, 이메일 문구, 일부 요약 필드가 새 케이스에 맞게 완전히 덮이지 않으면 이전 케이스 정보가 결과 화면에 섞일 수 있다.

영향:

- 평가 후 작성된 결과가 다른 기업의 제안 문구와 섞일 수 있다.
- 이력에서 특정 케이스를 열 때 화면 신뢰도가 낮아진다.

권고:

- 케이스 상세 화면은 기본 상태 또는 서버 state로 초기화한 뒤 patch를 적용한다.
- `getStoredState()`가 아니라 `resetForLearningMode({})` 또는 서버 snapshot 기반으로 시작한다.
- 결과 화면 렌더링 전에 필수 표시 필드가 모두 현재 case_id 기준인지 검증한다.

## 5. 데이터 입력 파이프라인 상세 평가

### 5.1 기업리포트 PDF

장점:

- PDF 텍스트 추출 후 회사명, 사업자번호, 등급, 점수, PD, 한도, 재무 요약표를 추출한다.
- 스캔형 PDF는 `image_or_scan_pdf`로 분류하고 OCR 필요 이슈를 남긴다.
- `learning_ready`에 usability와 issues를 반환한다.

문제:

- `learning_ready` 결과가 실제 학습 가중치 계산에 연결되지 않는다.
- 파일명만 있으면 FlowScore 자료 존재로 계산된다.
- OCR 실패 또는 핵심 필드 누락이 평가 차단 조건으로 쓰이지 않는다.

판정:

- 파서 자체는 품질 신호를 만들고 있으나, 학습 게이트가 그 신호를 사용하지 않아 파이프라인 연결이 불완전하다.

### 5.2 상담보고서·미팅보고서 Notion 링크

장점:

- official Notion API, public page data, HTML snapshot 순서로 본문을 읽는다.
- API 권한 오류와 integration 미공유 오류를 메시지로 구분한다.
- 상담보고서와 미팅보고서는 같은 parser를 사용하며 state prefix만 다르게 반영한다.

문제:

- 파싱 실패해도 URL이 있으면 학습자료로 인정될 수 있다.
- 미팅보고서가 상담보고서 하위 유형인지, 별도 유형인지 UI와 데이터 모델이 완전히 정리되지 않았다.
- 권한 오류는 issues에 남지만 update eligibility에는 직접 반영되지 않는다.

판정:

- 입력 자체는 가능하지만, 품질 기반 차단이 없다. 상담보고서와 미팅보고서 taxonomy도 통합 정리가 필요하다.

### 5.3 내부심사보고서 Notion 링크

장점:

- 상담보고서와 같은 Notion 파서 경로를 사용한다.
- 내부심사 summary, cross_checks, issues를 별도 state 필드에 저장한다.

문제:

- `internalReviewUrl` 문자열만 있으면 update eligibility에 필요한 내부심사 자료로 계산될 수 있다.
- 실제 본문이 0자이거나 integration 미공유여도 적격으로 오인될 수 있다.

판정:

- 현재 가장 위험한 입력 지점이다. 업데이트 적격 조건에 내부심사가 들어가므로, 내부심사 링크는 반드시 본문 추출 성공과 구조화 성공 기준을 통과해야 한다.

### 5.4 기타 PDF, DOCX, TXT, 추가정보

장점:

- 보조자료와 추가정보에서 매입처, 매출처, 결제유예기간, 목적, 리스크 문장을 추출한다.
- 상담 파일 업로드와 추가 메모가 평가 문맥에 반영된다.

문제:

- DOCX 파일은 현재 `extract_report_text`에서 직접 구조화 파싱하지 못할 가능성이 높다. PDF 또는 UTF-8 텍스트 중심이다.
- 추가정보는 텍스트가 존재하면 가중치를 받을 수 있으나 실제 유효성 기준이 약하다.

판정:

- 기타자료 입력은 보조 신호로는 쓸 수 있으나, 업데이트 학습 가중치에는 최소 품질 기준이 필요하다.

## 6. 평가 적용 방식 검증

### 6.1 평가엔진 호출

평가엔진 호출 자체는 정상 구조다.

- `/api/evaluate`: 일반 FlowPay underwriting 평가
- `/api/learning/evaluate`: 학습모드 입력 변환 후 FlowPay underwriting 평가

두 API 모두 `evaluate_flowpay_underwriting`을 사용하므로 평가엔진 진입 경로는 일관적이다.

문제는 어떤 framework를 사용하는지다. 현재는 active version 개념 없이 고정 파일을 로드한다.

### 6.2 학습모드 평가 입력 변환

학습모드는 화면 state를 엔진 입력으로 변환한다. 이때 다음 요소가 평가에 들어간다.

- 기업명, 대표자명, 사업자번호
- 신용등급
- 매출, 영업이익, 순이익
- 결제유예기간
- 매입처, 매출처
- 상담/심사/추가자료 기반 structure bonus
- 이슈 텍스트 기반 체납·연체·가압류·소송 여부

문제는 자료 품질이 낮아도 평가 입력은 만들어진다는 점이다. 따라서 "평가 가능"과 "신뢰 가능한 평가"를 분리해야 한다.

### 6.3 결과 출력

결과 출력은 `build_web_context`, `state_patch_from_context`, `apply_learning_engine_state_patch`로 화면 표시값을 만든다.

문제는 결과 화면에서 서버 케이스 상태와 브라우저 저장 상태가 섞일 수 있다는 점이다. 이력에서 결과를 열 때는 localStorage를 배제하고 서버 snapshot을 기준으로 화면을 구성해야 한다.

## 7. 현재 학습·업데이트 상태

명령 결과:

```text
BizAiPro Learning Status
  Current version     : v.local.learning
  Total candidates    : 7
  Qualified cases     : 5
  Weighted total      : 4.30
  Ready for update    : False
  Remaining cases     : 5
  Remaining weight gap: 3.20
```

업데이트 실행 결과:

```json
{
  "update_generated": false,
  "current_version": "v.local.learning",
  "progress": {
    "total_candidates": 7,
    "qualified_cases": 5,
    "weighted_total": 4.3,
    "ready_for_update": false,
    "remaining_cases": 5,
    "remaining_weight_gap": 3.2
  },
  "reason": "학습 적격 10건과 최소 가중치 7.5를 충족해야 합니다."
}
```

현재는 업데이트 조건 미충족으로 인해 업데이트가 차단된다. 이 차단 자체는 정상이다. 그러나 업데이트 조건이 충족되는 순간에는 active framework 적용 경로 부재 문제가 발생한다.

## 8. 우선 개선 계획

### 1단계. SourceQuality 게이트 추가

목표:

- 자료 존재 여부와 자료 품질을 분리한다.
- 평가 가능, 업데이트 가능, 보류 사유를 명확히 저장한다.

작업:

- `SourceQuality` 구조 추가
- 각 parser가 `usable_for_evaluation`, `usable_for_update`, `confidence`, `issues`, `extracted_fields` 반환
- `learning_material_components`가 state 문자열이 아니라 quality 객체를 사용하도록 변경

### 2단계. 웹·CLI 학습 기준 통합

목표:

- CLI status, 웹 dashboard, registry의 적격 기준을 동일하게 만든다.

작업:

- 공통 `learning_status.py` 또는 shared helper 생성
- `evaluation_ready`, `update_candidate`, `update_qualified` 분리
- 기존 registry 7건은 migration 또는 재정규화 리포트 생성

### 3단계. active framework 적용 경로 구축

목표:

- 업데이트 산출물이 실제 평가 API에 반영되도록 만든다.

작업:

- `data/frameworks/{version}.json` 저장
- `data/active_framework.json` 생성
- `load_active_framework()` 구현
- `/api/evaluate`, `/api/learning/evaluate`에서 active framework 사용
- `promote_update(version)` 또는 승인 API 추가

### 4단계. 평가 전 결측·품질 차단

목표:

- 파싱 실패와 실제 낮은 평가를 구분한다.

작업:

- `build_learning_evaluation_payload`에 `missing_fields`, `defaulted_fields`, `data_confidence` 추가
- 핵심 필드 미확인 시 한도 산출을 "조건부"로 표시
- 결과 화면에 자료 품질 상태 표시

### 5단계. 결과 화면 상태 초기화

목표:

- 평가 후 작성 결과가 다른 케이스 정보와 섞이지 않도록 한다.

작업:

- case_id 결과 화면은 localStorage 대신 서버 state snapshot 기준으로 구성
- 화면 표시 전 필수 필드 검증
- 이전 state 잔존 필드 제거

### 6단계. 회귀 테스트 추가

목표:

- 잘못된 업데이트 반영과 빈 자료 학습을 자동으로 차단한다.

필수 테스트:

- Notion 권한 오류 링크는 update eligible이 되면 안 된다.
- 빈 PDF 또는 OCR 필요 PDF는 FlowScore 자료로 인정되면 안 된다.
- 상담 URL만 있고 본문이 없으면 consultation weight가 0이어야 한다.
- 업데이트 생성 후 promote 전에는 active framework가 바뀌면 안 된다.
- promote 후 `/api/evaluate` 결과가 새 framework 기준으로 바뀌어야 한다.
- 케이스 상세 화면은 이전 localStorage 필드를 섞으면 안 된다.

## 9. 최종 판정

| 항목 | 판정 | 근거 |
| --- | --- | --- |
| 데이터 입력 API 구성 | 조건부 정상 | 주요 입력 route는 존재하나 품질 게이트가 약함 |
| Notion 파싱 | 조건부 정상 | official API와 fallback은 있으나 권한 실패가 학습 차단으로 연결되지 않음 |
| PDF 파싱 | 부분 정상 | learning_ready를 만들지만 학습 적격 계산에 사용하지 않음 |
| 학습 적격 판정 | 수정 필요 | 파일명/URL 존재 중심 |
| 평가엔진 호출 | 정상 | `evaluate_flowpay_underwriting` 진입은 일관적 |
| 평가 입력 변환 | 수정 필요 | 결측과 실제 위험이 혼재 |
| 업데이트 생성 | 조건부 정상 | 조건 미충족 시 차단은 정상 |
| 업데이트 실제 적용 | 오류 | active framework 적용 경로 없음 |
| 결과 화면 출력 | 수정 필요 | localStorage 상태 혼입 가능 |

최종적으로, 현재 시스템의 가장 큰 리스크는 "잘못된 자료가 학습에 들어가는 문제"와 "업데이트가 실제 평가에 적용되지 않는 문제"다. 이 두 가지를 먼저 고쳐야 이후 고도화가 실제 엔진 품질 개선으로 이어진다.
