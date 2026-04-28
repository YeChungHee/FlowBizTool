# FlowBiz_ultra 전체 구성 검증 보고서

- 검증일: 2026-04-27
- 검증 위치: `/Users/appler/Documents/COTEX/FlowBiz_ultra`
- 검증 범위: 학습엔진, 학습방식, 업데이트 구조, 웹 데이터 입력 파이프라인, 기업리포트/PDF/Notion 자료 추출, 평가엔진 로직, 업데이트 후 실제 평가 반영, 평가 결과 산출물
- 주의: 현재 작업트리에 기존 수정 파일이 있어 코드 수정은 하지 않고, 읽기 검증과 새 보고서 작성만 수행했다.

## 1. 종합 결론

현재 구성은 `기업리포트 PDF -> 상담/미팅/심사 Notion 링크 또는 보조자료 -> 학습모드 평가 -> 결과/제안서/이메일 화면`까지 이어지는 기본 파이프라인은 갖춰져 있다. FastAPI 라우트와 프론트엔드 호출 경로도 존재하고, 샘플 평가 실행과 Python 컴파일 검증은 통과했다.

다만 운영 기준으로 보면 아직 `학습 데이터로 인정할 수 있는 품질 검증`, `업데이트 산출물이 실제 평가엔진에 적용되는 경로`, `평가 결과 사후 검증`이 약하다. 특히 현재 로직은 Notion 링크의 본문 추출 성공 여부가 아니라 링크 문자열 존재 여부로 학습 가중치와 업데이트 적격 여부를 계산한다. 이 때문에 실제 심사보고서 본문을 읽지 못했는데도 업데이트 적격으로 표시될 수 있다.

## 2. 검증 실행 요약

| 항목 | 결과 |
|---|---|
| Python 컴파일 | `python3 -m py_compile app.py engine.py report_extractors.py bizaipro_learning.py external_apis.py proposal_generator.py` 통과 |
| 샘플 평가 | `python3 engine.py --input sample_inputs/flowpay_atude_case.json` 실행 성공 |
| 학습 상태 | 총 7건, 적격 5건, 누적 가중치 4.30, 업데이트 미준비 |
| 업데이트 실행 | `python3 bizaipro_learning.py update` 결과 `update_generated=false` |
| API 키 상태 | 환경변수 Notion 토큰은 없지만 `data/api_keys.local.json`을 통해 앱은 Notion 토큰을 읽을 수 있음 |
| 실제 Notion 재확인 | 상담보고서 2건은 official API로 본문 추출 성공, 심사보고서 2건은 integration 공유 권한 문제로 본문 추출 실패 |
| 테스트 체계 | 별도 `requirements.txt`, `pyproject.toml`, `pytest.ini` 등 테스트/의존성 선언 파일은 확인되지 않음 |

## 3. 현재 구성 확인

### 3.1 웹 데이터 입력 파이프라인

프론트엔드 공통 스크립트는 다음 API를 호출한다.

- 기업리포트: `/api/report/flowscore-parse`
- 상담보고서: `/api/consulting/parse`
- 미팅보고서: `/api/meeting/parse`
- 심사보고서: `/api/internal-review/parse`
- 보조 PDF/문서: `/api/supporting-document/parse`
- 추가 텍스트: `/api/additional-info/parse`
- 학습모드 평가: `/api/learning/evaluate`

백엔드는 이 입력을 state patch로 합친 뒤 `/api/learning/evaluate`에서 `build_learning_evaluation_payload()`를 통해 평가엔진 입력으로 변환하고 `evaluate_flowpay_underwriting()`을 실행한다. 평가 결과는 `data/bizaipro_learning_registry.json`에 저장되어 대시보드와 결과 상세 페이지가 읽는다.

### 3.2 기업리포트/PDF 추출

`report_extractors.py`는 `pypdf.PdfReader`로 텍스트를 추출하고, 정규식 기반으로 회사명, 사업자번호, 신용등급, 종합점수, PD, 월간 적정 신용한도, 재무 요약표를 찾는다. 텍스트가 거의 없는 스캔 PDF는 `image_or_scan_pdf`로 분류하며 OCR 필요 이슈를 표시한다.

장점은 FlowScore 계열 문서의 주요 필드를 빠르게 구조화한다는 점이다. 단점은 OCR, 표 레이아웃 변화, 신용평가 리포트가 아닌 일반 회사소개서, 비정형 PDF에 약하다. 현재 추출 결과가 평가 입력으로 넘어가지만, 추출 confidence가 낮을 때 자동 평가를 차단하거나 수기 검증 큐로 보내는 강한 게이트는 없다.

### 3.3 Notion 링크 추출

`parse_consulting_report_url()`은 Notion URL이면 page id를 추출하고, 로컬 토큰이 있으면 공식 Notion API로 본문을 읽는다. 실패하면 public page data, HTML snapshot 순서로 fallback한다. 본문을 못 읽으면 issues에 이유를 넣는다.

실제 확인 결과:

- 씨랩 상담보고서: official API 사용, 본문 4,431자 추출, issues 없음
- 씨랩 심사보고서: API 토큰은 있으나 page가 integration에 공유되지 않아 본문 0자, issues 2개
- 쿳션 상담보고서: official API 사용, 본문 4,253자 추출, issues 없음
- 쿳션 심사보고서: API 토큰은 있으나 page가 integration에 공유되지 않아 본문 0자, issues 2개

즉 Notion 연결 자체는 가능하지만, 심사보고서 권한 공유 상태가 현재 학습 적격 판단에 충분히 반영되지 않는다.

## 4. 주요 오류 및 리스크

### P0. 업데이트 산출물이 실제 평가엔진에 자동 적용되지 않는다

`bizaipro_learning.py update`는 조건을 만족하면 `outputs/bizaipro_updates/{version}/comparison_report.md`와 `update_summary.json`을 만들고 registry의 current_version을 변경한다. 그러나 `/api/evaluate`와 `/api/learning/evaluate`는 계속 `data/integrated_credit_rating_framework.json`을 읽는다. 즉 업데이트 산출물은 비교 리포트로는 남지만, 별도의 promotion 단계가 없으면 실제 평가엔진에는 반영되지 않는다.

영향:

- 사용자는 “업데이트 완료”로 보더라도 실제 웹 평가 결과가 바뀌지 않을 수 있다.
- 업데이트 전후 비교 보고서와 운영 평가 결과가 분리된다.
- 버전명만 바뀌고 모델 본체가 그대로인 상태가 생길 수 있다.

개선:

- 업데이트 산출물에 `framework.json`을 함께 저장한다.
- 검증 통과 후 `data/integrated_credit_rating_framework.json`으로 승격하는 명시적 promote 명령을 만든다.
- `/api/evaluate`가 요청한 engine version 또는 active version registry를 기준으로 프레임워크를 로드하도록 분리한다.

### P0. 학습 적격 판단이 자료 품질이 아니라 자료 존재 여부에 의존한다

`learning_material_components()`는 `learningFlowScoreFileName`, `consultingReportUrl`, `meetingReportUrl`, `internalReviewUrl`, `learningExtraInfo`의 문자열 존재 여부만 본다. 실제 파싱 성공, 본문 길이, issues, cross-check 일치 여부는 가중치 계산에 들어가지 않는다.

재현 검증:

- 더미 FlowScore 파일명, 더미 상담 URL, 더미 심사 URL만 넣어도 components는 `0.85`, `evaluation_ready=true`, `update_eligible=true`가 된다.
- 이 상태의 engine input은 매입처/매출처가 `확인 필요`로 남고, tax arrears도 false로 계산된다.

영향:

- 읽을 수 없는 심사보고서도 update weight 0.15를 받을 수 있다.
- 권한 오류, 빈 본문, 회사명 불일치가 학습 적격을 막지 못한다.
- 현재 registry의 씨랩/쿳션 심사보고서처럼 본문 추출 실패가 있어도 update eligible로 유지될 위험이 있다.

개선:

- 자료별 `source_quality`를 도입한다: `present`, `parsed`, `min_text_length`, `identity_match`, `issues`, `confidence`.
- update eligible은 `parsed=true`, `critical_issues=[]`, `identity_match!=fail`일 때만 인정한다.
- 본문 추출 실패 자료는 `evaluation_ready` 보조자료로만 표시하고 `update_weight`에는 제외한다.

### P1. CLI 학습 루프와 웹 학습 루프의 적격 기준이 다르다

`bizaipro_learning.py`의 `compute_learning_weight()`는 `flow_score_report_submitted`와 `consultation_report_submitted`만 있으면 qualified로 본다. 반면 웹앱의 live registry는 `flow_score + consultation + internal_review`를 update eligible로 본다.

영향:

- CLI로 적재한 학습 케이스와 웹으로 적재한 학습 케이스의 적격 기준이 달라질 수 있다.
- README는 `기업리포트 + 상담보고서 + 심사보고서`를 업데이트 건수 반영 기준으로 설명하지만, CLI 기록 경로는 이 기준과 어긋난다.

개선:

- 학습 상태 산정 로직을 하나의 모듈로 통합한다.
- CLI record/update와 웹 record가 같은 `learning_status_from_components()`를 사용하도록 바꾼다.

### P1. 학습 고도화 로직이 매우 제한적이다

현재 업데이트 로직은 최근 적격 10건의 applicant/buyer/transaction 평균 점수를 보고 overall weight를 약간 조정하고, 평균 learning weight가 낮으면 margin cap을 0.5%p 올리는 방식이다.

한계:

- subfactor weight, knockout rule, EWS, limit factor, 업종 threshold는 학습으로 개선되지 않는다.
- 실제 사후 결과값, 부실/정상 라벨, 회수 여부, 승인/거절 사유 같은 supervised label이 없다.
- holdout 검증, drift 검증, 전후 오류율 검증이 없다.

개선:

- 학습 케이스에 `outcome_label`을 추가한다: 승인, 거절, 회수 정상, 연체, 손실, 매출처 이슈, 서류 불일치 등.
- 업데이트는 1단계로 calibration만 수행하고, 2단계에서 요인별 가중치 후보를 생성한다.
- 후보 모델은 shadow evaluation으로 registry 전체에 재평가한 뒤 오차/안정성 기준을 통과해야 promote한다.

### P1. Notion/문서 추출 결과가 점수에 반영되는 폭이 좁다

상담/미팅/심사에서 추출되는 매입처, 매출처, 결제유예기간, 리스크 문구는 state에 반영된다. 그러나 평가 입력 변환에서는 대부분 다음 형태로만 반영된다.

- 상담/미팅 validation summary가 있으면 `structure_bonus +8`
- 심사 validation summary가 있으면 `structure_bonus +6`
- 보조문서 summary가 있으면 `structure_bonus +5`
- 추가정보 summary가 있으면 `structure_bonus +4`
- 이슈 텍스트에 체납/연체/가압류/소송이 있으면 tax arrears true
- 매입처/매출처 이름은 buyer signal에 간접 반영

즉 문서의 세부 항목이 점수표의 구체 subfactor로 세밀하게 매핑되지는 않는다.

개선:

- 상담/심사 템플릿별 필드를 표준화한다: 거래 증빙, 발주서, 세금계산서, 납품검수, 매출처 신용도, 상계 위험, 회수주기, 재고/물류 리스크.
- 추출 필드를 `transaction.structure`, `buyer.payment`, `applicant.compliance` 세부 점수로 명시 매핑한다.
- 각 점수에는 `source`, `evidence`, `confidence`를 함께 저장한다.

### P2. 결과 검증 체계가 부족하다

현재 결과는 `result_snapshot`, `web_context_snapshot`, `state_snapshot`으로 저장되고 상세 페이지에서 볼 수 있다. 하지만 결과가 타당한지 검증하는 자동 규칙은 부족하다.

필요한 검증:

- 기업명/사업자번호/대표자명이 기업리포트, 상담보고서, 심사보고서에서 일치하는지
- 신용등급과 engine grade가 급격히 벌어질 때 사유가 있는지
- 법정 한도 초과 마진율이 사용자 화면에서 오해 없이 표시되는지
- 매출액이 없거나 PDF 추출 실패인데도 한도/마진이 산출되지 않는지
- 업데이트 전후 같은 케이스의 decision이 과도하게 흔들리지 않는지

## 5. 현재 학습 상태 진단

현재 registry 기준:

- 전체 케이스: 7건
- 평가 준비: 6건
- 업데이트 적격: 5건
- 누적 update weight: 4.30
- 업데이트 조건: 적격 10건 이상, 누적 가중치 7.5 이상
- 현재 업데이트 가능 여부: 불가

케이스별 결과는 모두 `REVIEW / C+` 근처에 모여 있다. 한도는 약 22,927,000원부터 512,356,000원까지 다양하지만, decision 분포가 한쪽으로 몰려 있어 실제 운영 데이터가 늘어나면 grade/decision calibration이 필요하다.

## 6. 고도화 계획

### 1단계. 학습 적격 게이트 정비

- `SourceQuality` 구조를 추가한다.
- PDF/Notion/추가자료 파서가 모두 `quality`를 반환하게 한다.
- `learning_material_components()`를 문자열 존재 기준에서 `quality.usable_for_update` 기준으로 변경한다.
- 현재 registry를 재계산해 본문 추출 실패 심사보고서의 update weight를 제거한다.

완료 기준:

- 빈 Notion 본문, 권한 오류, OCR 필요 PDF는 update eligible이 되지 않는다.
- 상담보고서만 있으면 `평가 반영 완료`, 심사보고서까지 품질 통과 시 `엔진 업데이트 적격`으로 표시된다.

### 2단계. 평가 입력 변환 고도화

- 상담/미팅/심사 공통 parser schema를 정리한다.
- 미팅보고서는 상담보고서의 subtype으로 유지하되 `전화상담`, `직접상담`, `미팅` 라벨만 분리한다.
- 추출 필드를 score subfactor로 명시 매핑한다.
- 매핑 결과에 evidence 문장을 붙여 결과 페이지에서 근거를 확인하게 한다.

완료 기준:

- 특정 문서 문구가 어떤 점수 항목을 몇 점 올리거나 낮췄는지 추적 가능하다.
- 권한 실패/본문 공백/회사명 불일치가 결과 페이지와 registry에 명확히 표시된다.

### 3단계. 업데이트 산출물의 실제 적용 경로 구축

- `run_update()`가 `framework.json`, `comparison_report.md`, `update_summary.json`, `validation_report.json`을 생성하게 한다.
- active framework registry를 추가한다.
- promote 전 shadow evaluation을 수행한다.
- promote 후 `/api/evaluate`와 `/api/learning/evaluate`가 active framework를 읽는지 회귀 테스트한다.

완료 기준:

- 업데이트 전후 같은 케이스를 재평가했을 때 결과 차이가 기록된다.
- promote하지 않은 업데이트는 웹 평가에 반영되지 않고, promote한 업데이트만 반영된다.

### 4단계. 결과 검증 자동화

- 최소 회귀 테스트를 추가한다.
- 샘플 PDF/샘플 Notion 텍스트/샘플 state를 fixture로 만든다.
- 결과 검증 규칙을 추가한다: 필수 필드, 법정 한도 표시, decision 안정성, 추출 품질, identity match.

완료 기준:

- `python3 -m pytest` 또는 단일 검증 스크립트로 파서, 평가, 학습, 결과 페이지 데이터 구조를 확인한다.
- 새 업데이트를 적용하기 전 검증 실패 시 promote가 중단된다.

## 7. 권장 우선순위

1. `SourceQuality`와 학습 적격 게이트부터 수정한다. 현재 가장 위험한 문제는 자료가 읽히지 않았는데 업데이트 적격이 되는 것이다.
2. 업데이트 산출물 promotion 경로를 만든다. 지금은 업데이트가 생성되어도 실제 평가엔진 적용이 자동 보장되지 않는다.
3. 상담/심사 추출 필드와 점수 subfactor 매핑표를 만든다.
4. registry 재계산 및 기존 7건 결과 재검증을 수행한다.
5. 마지막으로 결과 페이지에 source/evidence/confidence를 보여준다.

## 8. 다음 작업 제안

바로 코드 고도화에 들어간다면 다음 순서가 안전하다.

1. `app.py`에 source quality 구조와 품질 기반 학습 가중치 계산을 추가한다.
2. `data/bizaipro_learning_registry.json`을 백업한 뒤 기존 케이스를 재정규화한다.
3. `bizaipro_learning.py`와 웹앱의 학습 상태 산정 함수를 통합한다.
4. 업데이트 산출물에 framework snapshot을 저장하고 promote 명령을 추가한다.
5. 검증 스크립트 또는 pytest fixture를 만든다.
