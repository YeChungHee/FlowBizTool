# [codex] FlowBizTool v2 Standalone 디자인 구현 계획서 v3 검증 보고서

- 문서번호: FBU-VAL-UI-V2-STANDALONE-v3-20260430
- 작성일: 2026-04-30
- 검증 대상: `docs/[claude]flowbiz_ui_v2_standalone_design_implementation_plan_v3_20260430.md`
- 이전 검증: `docs/[codex]flowbiz_ui_v2_standalone_design_implementation_plan_v2_validation_20260430.md`
- 판정: **조건부 승인 가능**

## 1. 이전 Finding 반영 여부

| 이전 Finding | v3 반영 상태 | 판정 |
|---|---|---|
| FastAPI body 파싱 불일치 가능 | `EvaluationReportRequest`, `ProposalGenerateRequest`, `EmailGenerateRequest` BaseModel과 `Content-Type` 헤더 추가 | 종료 |
| 전시회 사전평가가 FPE snapshot처럼 보임 | `ExhibitionLeadSnapshot`, `evaluation_status="not_evaluated"`, `decision_source=None` 분리 | 종료 |
| `outputs/reference/`는 git ignore됨 | source artifact는 `docs/reference/`, generated artifact는 `outputs/reference/`로 분리 | 종료 |
| hold decision 상태 정의 불명확 | `on_hold` 상태를 추가해 5종 상태로 확장 | 종료 |
| E2E 테스트 fixture 부재 | Playwright fixture, seed API, seed data 구조 추가 | 종료 |

v3는 v2 검증에서 나온 5개 지적을 모두 문서상 반영했다. 이제 남은 문제는 구현 예시를 실제 코드로 옮길 때 생기는 런타임/테스트 세부 리스크다.

## 2. 신규 Finding

### Finding 1 [P1] `ulid.new()` 의존성이 현재 repo에 없음

v3 예시는 `report_id`, `proposal_id`, `lead_id` 생성에 `ulid.new()`를 사용한다. 그러나 현재 repo에는 dependency manifest가 없고, 현재 Python 환경에서도 `import ulid`가 실패한다. 계획서대로 구현하면 평가보고서 생성 API가 첫 실행에서 `NameError` 또는 `ModuleNotFoundError`로 막힐 수 있다.

확인 결과:

```text
python3 -c "import ulid"
ModuleNotFoundError: No module named 'ulid'
```

권고:

- 외부 의존성을 늘리지 않으려면 `uuid.uuid4().hex` 또는 `uuid.uuid4()` 기반 ID로 바꾼다.
- ULID가 꼭 필요하면 dependency 파일을 먼저 만들고 `python-ulid` 또는 `ulid-py` 중 하나를 명시한다.
- 계획서의 예시 코드에는 `from uuid import uuid4` 또는 `import ulid` + 설치 계획을 반드시 포함한다.

### Finding 2 [P1] negative snapshot seed가 `EvaluationSnapshot` 검증에 막힐 수 있음

E2E fixture는 `decision_source='APE'`인 비정상 snapshot을 seed해서 proposal API가 거부하는지 검증하려고 한다. 하지만 v3의 `EvaluationSnapshot` 모델은 `decision_source: Literal["FPE"]`로 정의되어 있다. 따라서 test-only seed API가 `save_snapshot(EvaluationSnapshot(**snapshot))`를 호출하면, 비정상 snapshot은 저장되기 전에 Pydantic validation에서 실패한다.

영향:

- `proposal API rejects non-FPE decision_source` 테스트가 의도한 400 거부 경로까지 도달하지 못한다.
- 테스트 실패 원인이 정책 검증이 아니라 fixture 생성 실패가 된다.
- 실제로 “잘못 저장된 legacy snapshot 방어”를 검증하려면 정상 모델을 우회하는 별도 raw fixture가 필요하다.

권고:

- negative case seed API는 `EvaluationSnapshot` 모델로 검증하지 말고, test-only raw JSON 파일을 직접 저장하거나 `UnsafeSnapshotForTest` 모델을 별도로 둔다.
- 더 안전한 방식은 proposal API에서 snapshot load 후 raw dict를 검증하는 테스트와, 일반 저장 API는 `decision_source="FPE"`만 허용하는 테스트를 분리하는 것이다.
- seed API 이름도 `/api/test/seed-raw-snapshot`처럼 위험성을 드러내고 `FLOWBIZ_ENV=test`에서만 활성화한다.

### Finding 3 [P2] `v2_tokens.css` on_hold 토큰은 계획에는 있으나 현재 파일에는 없음

v3는 `--fbu-color-status-on-hold`를 Phase 0에서 추가한다고 정리했다. 현재 `web/styles/v2_tokens.css`에는 아직 `on_hold`/`on-hold` 관련 토큰이 없다. 이는 계획 자체의 결함이라기보다 실행 체크 항목이므로, 구현 착수 시 빠지지 않게 파일 영향 목록에 명시해야 한다.

권고:

- 변경 파일 목록에 `web/styles/v2_tokens.css`를 명시하고, `--fbu-color-status-on-hold` 추가를 Phase 0 acceptance criteria에 넣는다.
- engine management/changelog 화면 CSS도 해당 토큰을 실제로 참조하는지 확인한다.

## 3. 재검증 요약

| 검증 항목 | v3 상태 | 판정 |
|---|---|---|
| 구현방식 | docs/reference 보관, rendered DOM 토큰, 8 화면 + 전시회 화면 | 적합 |
| 평가엔진/학습엔진 역할 | FPE 기준, APE 비교 전용 유지 | 적합 |
| 평가보고서 생성 | BaseModel + EvaluationSnapshot 추가 | 조건부 적합, ID 생성 방식 보강 필요 |
| 제안서 생성 | ProposalGenerateRequest + FPE 강제 | 적합 |
| 이메일 생성 | EmailGenerateRequest 추가 | 적합 |
| 업데이트일지 + 엔진비교표 | on_hold 포함 5 상태로 확장 | 적합 |
| 월간 엔진업데이트보고서 | upgrade-reports 계열 + on_hold 처리 | 적합 |
| 전시회 참가기업 평가 | ExhibitionLeadSnapshot으로 FPE 미실행 구분 | 적합 |
| E2E 테스트 | fixture 구조 추가 | 조건부 적합, negative seed 방식 보강 필요 |

## 4. 실행 전 보완 체크리스트

- [ ] `ulid.new()`를 `uuid.uuid4()`로 바꾸거나 ULID dependency 설치 계획 추가
- [ ] test-only negative snapshot seed는 `EvaluationSnapshot` 검증을 우회하는 raw fixture로 설계
- [ ] `web/styles/v2_tokens.css`에 `--fbu-color-status-on-hold` 추가를 Phase 0 필수 작업으로 명시
- [ ] `FLOWBIZ_ENV=test`가 실제 테스트 실행 스크립트에서 설정되는지 검증

## 5. 결론

v3는 방향성과 구조 측면에서 **실제 구현 착수 가능한 수준**에 가까워졌다. 다만 `ulid` 의존성과 negative fixture 설계는 그대로 구현하면 바로 실패할 수 있으므로, 이 두 가지는 착수 전 반드시 수정해야 한다.
