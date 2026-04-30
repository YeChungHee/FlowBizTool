# [codex] FlowBizTool v2 Standalone 디자인 구현 계획서 v2 검증 보고서

- 문서번호: FBU-VAL-UI-V2-STANDALONE-v2-20260430
- 작성일: 2026-04-30
- 검증 대상: `docs/[claude]flowbiz_ui_v2_standalone_design_implementation_plan_v2_20260430.md`
- 이전 검증: `docs/[codex]flowbiz_ui_v2_standalone_design_implementation_plan_validation_20260430.md`
- 판정: **조건부 승인 가능**

## 1. 이전 Finding 반영 여부

| 이전 Finding | v2 반영 상태 | 판정 |
|---|---|---|
| 전시회 참가기업 평가 흐름 누락 | `bizaipro_exhibition_evaluator.html`, 7개 입력 필드, 전시회 평가 Phase 5 추가 | 종료 |
| 평가보고서 산출물 정의 부족 | `EvaluationSnapshot`, `report_id`, `/api/evaluation/report` 계열 API 추가 | 종료 |
| 월간 업그레이드 API 불일치 | `/api/engine/upgrade-reports` 계열로 정정 | 종료 |
| thumbnail 기준 토큰 추출 리스크 | rendered DOM + computed style 추출 절차 추가 | 종료 |

v2는 v1 대비 큰 방향을 제대로 보강했다. 특히 FPE는 제안서/이메일의 유일 기준, APE는 비교/학습/고도화 후보 전용이라는 운영 원칙은 유지된다.

## 2. 신규 Finding

### Finding 1 [P1] API 예시가 실제 FastAPI body 파싱과 어긋날 수 있음

문서는 `/api/evaluation/report`를 `state: dict`로 받고, `/api/proposal/generate`를 `report_id: str` 인자로 받는 예시를 제시한다. 하지만 JavaScript 예시는 `fetch(..., { body: JSON.stringify(...) })`만 사용하고 `Content-Type: application/json` 헤더가 없다. 또한 FastAPI에서 `report_id: str` 단순 파라미터는 기본적으로 JSON body가 아니라 query parameter로 해석될 수 있다.

영향:

- 클라이언트가 `{ report_id: "..." }` JSON body를 보내도 서버가 `report_id`를 못 받아 422가 날 수 있다.
- `state: dict`도 content-type 누락 시 정상 JSON body로 파싱되지 않을 수 있다.
- 제안서/이메일 snapshot 기반 강제라는 핵심 흐름이 첫 구현에서 깨질 가능성이 있다.

권고:

- `EvaluationReportRequest(BaseModel)`와 `ProposalGenerateRequest(BaseModel)`를 명시한다.
- 모든 fetch 예시에 `headers: { "Content-Type": "application/json" }`를 추가한다.
- `/api/proposal/generate`와 `/api/email/generate`는 query parameter가 아니라 body model 기준으로 통일한다.

### Finding 2 [P1] 전시회형 사전평가가 FPE 평가 snapshot처럼 보일 수 있음

전시회 평가 흐름에서 기업리포트/FlowScore가 없으면 `decision_source: "FPE"`와 `proposal_allowed: false`를 가진 임시 snapshot을 만든다. 그러나 이 케이스는 FPE가 실제로 평가한 결과가 아니라 `FPE 결과 없음` 상태다.

영향:

- `decision_source=FPE`가 “FPE 평가 완료”라는 기존 불변식과 충돌한다.
- 결과 화면이나 제안서 API가 `fpe_credit_limit`, `fpe_margin_rate`, `server_input_hash` 같은 필드를 기대하면 누락 필드로 실패할 수 있다.
- 운영자가 “FPE가 차단했다”고 오해할 수 있는데, 실제 사유는 “평가 자료 미연결”이다.

권고:

- 이 분기는 `EvaluationSnapshot`이 아니라 `ExhibitionLeadSnapshot` 또는 `evaluation_status: "not_evaluated"`로 분리한다.
- `decision_source`는 `null` 또는 `"none"`으로 두고, `proposal_allowed=false`, `blocked_reason="기업리포트/FlowScore 미연결"`을 표시한다.
- FPE가 실제 실행된 경우에만 `EvaluationSnapshot.report_id`를 생성한다.

### Finding 3 [P2] `outputs/reference/`는 git ignore 상태라 reference 보존 정책과 충돌

v2는 standalone HTML 보관 위치로 `outputs/reference/`를 권장하면서 “git 추적 가능”이라고 적고 있다. 하지만 현재 repo의 `.gitignore`는 `outputs/` 전체를 무시한다.

영향:

- 기준 디자인 원본을 `outputs/reference/`에만 두면 PR/다른 환경에서 사라질 수 있다.
- `scripts/extract_v2_tokens_rendered.js --input outputs/reference/...` 검증이 다른 작업자 환경에서 실패할 수 있다.

권고:

- 추적 가능한 기준 원본이 필요하면 `docs/reference/`를 사용한다.
- `outputs/reference/`는 로컬 렌더 산출물 전용으로 정의한다.
- 둘 다 사용할 경우 `docs/reference/`는 source artifact, `outputs/reference/`는 generated artifact로 역할을 분리한다.

### Finding 4 [P2] upgrade decision의 `hold`와 status 4종이 불일치

API 매핑에는 `POST /api/engine/upgrade-reports/{report_id}/decision`의 decision 값으로 `approved/rejected/hold`가 언급되지만, 상태값 표는 `pending/approved/promoted/rejected` 4종만 고정한다.

영향:

- 관리자가 보류를 선택했을 때 보고서 상태가 `hold`인지 `pending` 유지인지 모호하다.
- 엔진 관리 탭 필터와 changelog 표시에서 보류 보고서가 누락될 수 있다.

권고:

- 상태값을 `pending / approved / on_hold / rejected / promoted` 5종으로 확장하거나,
- decision `hold`는 status를 `pending`으로 유지하고 `admin_decision="hold"`로 별도 저장한다고 명시한다.

### Finding 5 [P2] E2E 테스트 예시가 fixture 준비 없이 실패할 수 있음

E2E 테스트는 `fake-snapshot-with-ape-decision`, `R-001` 같은 report_id를 바로 사용한다. 그러나 테스트 전에 해당 snapshot을 생성하거나 mock API를 설치하는 단계가 없다.

영향:

- 테스트가 의도한 정책 위반 검증이 아니라 404/fixture 없음으로 실패할 수 있다.
- APE 값 form 미바인딩 검증이 실제 UI 로딩 실패와 구분되지 않는다.

권고:

- 테스트 `beforeEach`에서 `/api/evaluation/report` fixture를 생성하거나, test-only fixture JSON을 `data/evaluation_reports/`에 임시 생성한다.
- negative case는 `decision_source != FPE`인 snapshot을 명시적으로 seed한다.
- `R-001` 같은 하드코딩 ID 대신 생성된 `report_id`를 사용한다.

## 3. 항목별 재검증

| 검증 항목 | v2 상태 | 판정 |
|---|---|---|
| 구현방식 | 6 Phase + 8 화면 + 엔진관리 + 전시회 화면 | 조건부 적합 |
| FPE/APE 역할 | FPE 기준, APE 비교 전용 유지 | 적합 |
| 평가보고서 생성 | EvaluationSnapshot/report_id 추가 | 적합, body model 보강 필요 |
| 제안서 생성 | report_id 기반, FPE 차단 시 거부 | 적합, request schema 보강 필요 |
| 이메일 생성 | report/proposal snapshot 기반 | 적합 |
| 업데이트일지 + 엔진비교표 | FPE 승격/APE 학습/월간 report link | 적합 |
| 월간 엔진업데이트보고서 | upgrade-reports 계열로 정정 | 조건부 적합, hold 상태 정리 필요 |
| 전시회 참가기업 평가 | Phase 5 + 신규 화면 추가 | 조건부 적합, 사전평가와 FPE snapshot 분리 필요 |
| 디자인 검증 | rendered DOM/computed style 추가 | 적합, reference 경로 정책 보강 필요 |

## 4. 실행 전 보완 체크리스트

- [ ] `EvaluationReportRequest`, `ProposalGenerateRequest`, `EmailGenerateRequest` request model 명시
- [ ] fetch 예시에 `Content-Type: application/json` 추가
- [ ] 전시회 사전평가를 `EvaluationSnapshot`과 분리
- [ ] `outputs/reference/`와 `docs/reference/` 보존 정책 정리
- [ ] 월간 보고서 보류 상태 처리 규칙 확정
- [ ] E2E 테스트용 snapshot fixture 생성 절차 추가

## 5. 결론

v2 계획서는 이전 4개 핵심 결함을 대부분 잘 해결했다. 이제 남은 문제는 방향성보다 **구현 디테일의 정확성**이다. 위 신규 Finding 5건을 반영하면 실제 구현 착수 계획으로 승인 가능하다.
