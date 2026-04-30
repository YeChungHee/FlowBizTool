# [codex] FlowBizTool v2 Standalone 디자인 구현 계획서 검증 보고서

- 문서번호: FBU-VAL-UI-V2-STANDALONE-20260430
- 작성일: 2026-04-30
- 검증 대상: `docs/[claude]flowbiz_ui_v2_standalone_design_implementation_plan_20260430.md`
- 디자인 원본: `FlowBizTool _ v2 _standalone.html`
- 대조 기준:
  - `docs/flowbiztool_v2_standalone_based_production_plan_20260430.md`
  - `docs/flowbiz_monthly_evaluation_engine_upgrade_plan_20260430.md`
  - `docs/flowbiz_dual_engine_evaluation_and_upgrade_lifecycle_plan_20260430.md`
  - `web/bizaipro_exhibition_wireframe.html`
  - `web/kcnc_simtos2026_sample.html`

## 1. 종합 판정

현재 `[claude]` 계획서는 v2 standalone 디자인을 기존 6개 HTML 화면과 FPE/APE 듀얼 엔진 운영에 접목하는 큰 방향은 타당하다. 특히 다음 원칙은 기존 Codex 계획과 일치한다.

- 평가엔진은 `FPE`, 학습엔진은 `APE`로 분리한다.
- 제안서와 이메일에 들어가는 수치는 항상 active FPE 기준으로 고정한다.
- APE는 비교, 학습, 고도화 후보 생성에만 사용한다.
- 상담보고서와 미팅보고서는 하나의 `상담보고서 family`로 집계하고 전화상담/직접상담 subtype으로 나눈다.
- 월간 엔진 관리 탭에서 평가엔진고도화보고서를 다룬다.
- AppleGothic 기반 Human Interface 방향을 따른다.

다만 실제 사용 가능한 운영 환경으로 보려면 아직 **조건부 보류**다. 평가보고서 산출물, 월간 업그레이드 API 정합성, 전시회 참가기업 평가 흐름이 계획서 안에서 충분히 닫히지 않았다.

## 2. 핵심 Finding

### Finding 1 [P1] 전시회정보 기반 참가기업 평가방식 누락

사용자가 요구한 `전시회정보를 통해 참가기업 평가방식`이 현재 계획서의 Phase, 변경 파일 목록, 데이터 바인딩 범위에 없다. 기존 와이어프레임에는 전시회 DB 입력, 전시회형 제안서, 콜드메일 생성 흐름이 이미 존재한다. 따라서 v2 production 계획으로 승격하려면 전시회 참가기업 평가를 별도 Phase 또는 3차 PR 필수 범위에 넣어야 한다.

보강 방향:

- `전시회 DB/URL 입력 -> 참가기업 추출 -> 홈페이지/품목/담당자 수집 -> FlowScore 또는 기업리포트 연결 -> FPE 평가 -> APE 비교 -> FPE 기준 제안서/이메일 생성` 흐름을 추가한다.
- 기존 `web/bizaipro_exhibition_wireframe.html`, `web/kcnc_simtos2026_sample.html`을 참고 화면으로 명시한다.
- 전시회 평가 입력 최소 필드를 `기업명 / 전시회명 / 참가 연도 / 산업·품목 / 전시회정보 URL / 홈페이지 / 담당자`로 고정한다.

### Finding 2 [P1] 평가보고서 생성 방식이 화면 표시 수준에 머묾

계획서는 `bizaipro_evaluation_result.html`에 FPE/APE 카드와 비교표를 표시하는 방법은 설명하지만, 실제 평가보고서 산출물의 저장 구조가 없다. 실사용에서는 평가 결과를 제안서와 이메일의 근거로 재사용해야 하므로 `report_id`, `EvaluationSnapshot`, 서버 저장, HTML/PDF/MD 출력 중 하나가 명확해야 한다.

보강 방향:

- `POST /api/evaluation/report` 또는 기존 `/api/learning/evaluate/dual` 응답 기반 `EvaluationSnapshot` 저장 절차를 추가한다.
- 평가보고서에는 `decision_source=FPE`, `fpe_version`, `ape_version`, `server_input_hash`, `source_quality`, `FPE vs APE 비교표`, `proposal_allowed`, `blocked_reason`을 포함한다.
- 제안서와 이메일 생성 API는 클라이언트 localStorage가 아니라 서버 평가보고서 snapshot을 기준으로 삼는다.

### Finding 3 [P1] 월간 엔진업데이트보고서 API 명칭이 기존 계획과 불일치

현재 계획서는 Phase 4에서 `/api/engine/upgrade/list`를 신설한다고 적는다. 그러나 월간 엔진업데이트 계획서의 기준 API는 `POST /api/engine/monthly-upgrade-report`, `GET /api/engine/upgrade-reports`, `GET /api/engine/upgrade-reports/{report_id}`, `POST /api/engine/upgrade-reports/{report_id}/decision`, `POST /api/engine/promote-fpe`다.

보강 방향:

- `/api/engine/upgrade/list`는 제거하거나 `GET /api/engine/upgrade-reports`의 별칭으로만 둔다.
- 엔진 관리 탭은 월간 보고서 목록, 상세, 승인/보류/반려, 후보 생성, FPE 승격까지 기존 월간 계획서 API와 1:1로 연결한다.
- 상태값은 `pending / approved / rejected / promoted`로 고정한다.

### Finding 4 [P2] 디자인 토큰 추출 기준이 thumbnail 중심이라 실제 화면과 어긋날 수 있음

계획서는 `#__bundler_thumbnail`에서 토큰을 추출한 값을 즉시 기준으로 삼는다. 하지만 원본 HTML은 bundler standalone 형태로 실제 템플릿과 자원이 gzip/base64로 들어 있다. thumbnail은 로딩 미리보기일 수 있어 실제 unpack 후 화면의 CSS, spacing, component 상태를 모두 대표한다고 보기 어렵다.

보강 방향:

- Phase 1에서 standalone 원본을 `reference`로 보존하되, 토큰 확정 전 unpack 또는 브라우저 렌더 스크린샷 비교를 수행한다.
- 토큰 추출 스크립트는 thumbnail뿐 아니라 `__bundler/template`, runtime-rendered DOM, computed style을 함께 비교한다.
- `web/dual_engine_v2_standalone.html` 공개 배포보다는 `docs/reference/` 또는 `outputs/reference/` 보관을 우선 검토한다.

## 3. 항목별 검증

| 검증 항목 | 현재 계획 반영 | 판정 | 보완 필요 |
|---|---:|---|---|
| 구현방식 | 디자인 토큰 + 기존 6 HTML 마이그레이션 + 엔진 관리 탭 | 조건부 적합 | token source를 thumbnail-only에서 rendered DOM 기준으로 보강 |
| 평가엔진/학습엔진 역할 | FPE 기준, APE 비교 전용 | 적합 | 제안/이메일 API에서도 `decision_source=FPE` 강제 테스트 필요 |
| 평가보고서 생성 | 결과 화면 표시 중심 | 미흡 | 서버 snapshot/report_id/저장 API 추가 |
| 제안서 생성 | FPE snapshot 표시, FPE 차단 시 disabled | 적합 | 평가보고서 snapshot 기반 생성으로 명시 |
| 이메일 생성 | 제안서와 동일한 FPE 기준 | 적합 | proposal snapshot 또는 evaluation snapshot 기반 생성으로 명시 |
| 업데이트일지 | FPE 승격 이력 + APE 학습 이력 | 적합 | 실제 changelog data source 정의 필요 |
| 엔진비교표 | FPE_v16.01 vs APE 비교 | 적합 | report/version linkage 추가 |
| 월간 엔진업데이트보고서 | 엔진 관리 탭 방향 있음 | 조건부 적합 | API 명칭 및 상태 전환을 월간 계획서와 일치 |
| 전시회 참가기업 평가 | 없음 | 부적합 | 전시회 DB 기반 평가/제안/메일 흐름 추가 |

## 4. 실제 사용 환경 기준 권장 로드맵

### Phase 0. 기준 정리

1. `FlowBizTool _ v2 _standalone.html`은 디자인 기준 원본으로 보관한다.
2. 원본은 직접 production route로 쓰지 않고, rendered screenshot + computed style 기준으로 디자인 토큰을 확정한다.
3. 기존 v1.16.01/v1.18.02 혼재 UI는 `bizaipro_shared.css` 토큰으로 통합한다.

### Phase 1. 평가 실행과 보고서 snapshot

1. 기업리포트 또는 FlowScore 업로드 후 FPE와 APE를 동시에 실행한다.
2. 최종 판단은 FPE로 고정하고, APE는 비교표와 고도화 후보로만 저장한다.
3. `EvaluationSnapshot`과 `report_id`를 서버에 저장한다.
4. 평가결과 화면은 저장된 snapshot을 렌더링한다.

### Phase 2. 제안서/이메일 생성

1. 제안서 생성은 `EvaluationSnapshot.decision_source == FPE`를 확인한다.
2. FPE가 차단이면 제안서와 이메일 생성 버튼을 비활성화한다.
3. FPE 통과 또는 조건부 통과 시에만 제안서 snapshot을 생성한다.
4. 이메일은 평가 snapshot 또는 제안서 snapshot을 기준으로 생성한다.

### Phase 3. 업데이트일지 + 엔진비교표

1. `bizaipro_engine_compare.html`은 active FPE, latest APE, 차이 항목을 보여준다.
2. `bizaipro_changelog.html`은 FPE 승격 이력과 APE 학습 이력을 분리 표시한다.
3. 각 이력은 월간 보고서 ID 또는 learning registry case ID와 연결한다.

### Phase 4. 월간 엔진업데이트보고서

1. 매월 30일 13:00 KST에 `POST /api/engine/monthly-upgrade-report`로 보고서를 생성한다.
2. 보고서에는 FPE vs APE vs 실제 적용 결과 비교표를 포함한다.
3. 관리자가 승인해야 후보 FPE 생성과 검증을 진행한다.
4. 검증 통과 후에만 `POST /api/engine/promote-fpe`로 active FPE를 승격한다.

### Phase 5. 전시회 참가기업 평가

1. 전시회 정보 URL 또는 전시회 DB를 입력한다.
2. 참가기업, 산업/품목, 홈페이지, 담당자를 추출한다.
3. 기업리포트/FlowScore가 있으면 FPE 평가에 연결하고, 없으면 전시회형 사전평가로 분리한다.
4. FPE 통과 기업만 전시회형 제안서와 콜드메일 생성으로 진행한다.
5. 전시회 정보는 제안 메시지의 근거로 사용하되, 한도/마진율/결제유예기간은 FPE 결과만 사용한다.

## 5. 수정 권고 체크리스트

- [ ] 계획서 Phase 표에 `전시회 참가기업 평가` Phase 추가
- [ ] 변경 파일 목록에 `web/bizaipro_exhibition_wireframe.html` 계열 또는 신규 `web/bizaipro_exhibition_evaluator.html` 추가
- [ ] `EvaluationSnapshot`/`report_id` 생성과 저장 API 추가
- [ ] 월간 API를 `upgrade/list`가 아니라 `upgrade-reports` 계열로 정정
- [ ] standalone 디자인 토큰 추출 기준을 thumbnail-only에서 rendered DOM 검증으로 변경
- [ ] 제안서/이메일 생성 API에 `decision_source=FPE` 검증 테스트 추가
- [ ] APE 값이 form input에 바인딩되지 않는 E2E 테스트 추가
- [ ] 전시회 평가 케이스에 FPE 차단 시 제안서/이메일 차단 테스트 추가

## 6. 결론

이 계획서는 기존 Codex 방향성과 대부분 일치하지만, 현재 상태로는 **실제 사용 가능한 운영 계획서로 승인하기 전 보완 필요**다. 핵심은 세 가지다.

1. 평가 결과를 화면에 보여주는 것에서 끝내지 말고 `평가보고서 snapshot`으로 저장한다.
2. 월간 엔진업데이트보고서는 기존 월간 계획서 API와 명칭/상태를 통일한다.
3. 전시회 참가기업 평가 흐름을 독립 Phase로 추가한다.

위 세 가지가 보완되면 v2 standalone 디자인을 기준으로 학습, 평가, 제안, 이메일 생성, 고도화까지 이어지는 실제 운영 계획으로 전환 가능하다.
