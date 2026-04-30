# FlowBizTool v2 Standalone 디자인 구현 계획서 v3 [claude]

- 문서번호: FBU-PLAN-UI-V2-STANDALONE-IMPL-v3-20260430
- 작성일: 2026-04-30
- 작성자: [claude]
- 이전 버전: `[claude]flowbiz_ui_v2_standalone_design_implementation_plan_v2_20260430.md` (v2)
- 검증: `[codex]flowbiz_ui_v2_standalone_design_implementation_plan_v2_validation_20260430.md` (P1 2건 + P2 3건 — **조건부 승인 가능**)
- 변경 사유: v2 [codex] 검증 5건 반영 — **API request models (Pydantic BaseModel)** + **전시회 사전평가 EvaluationSnapshot 분리** + **standalone 보관을 docs/reference/로** + **upgrade decision hold 상태 처리** + **E2E fixture 생성 절차**

## 0. v2 → v3 변경 요약

| Finding | 우선순위 | v2 문제 | v3 반영 |
|---|---|---|---|
| F1 [codex] v2: API 예시가 FastAPI body 파싱 어긋남 | **P1** | `state: dict`, `report_id: str` 단순 인자 + fetch에 `Content-Type` 누락 → 422 위험 | **§7.2 Pydantic BaseModel 명시** (`EvaluationReportRequest`, `ProposalGenerateRequest`, `EmailGenerateRequest`) + 모든 fetch 예시 `Content-Type: application/json` 추가 + query param 대신 body model 강제 |
| F2 [codex] v2: 전시회 사전평가가 EvaluationSnapshot처럼 보임 | **P1** | `decision_source: "FPE" + proposal_allowed: false`로 임시 snapshot — FPE 평가 완료라는 불변식과 충돌 | **§7.5 ExhibitionLeadSnapshot 신규 모델** + `decision_source=null` + `evaluation_status="not_evaluated"` + FPE 실제 실행 시에만 `EvaluationSnapshot.report_id` 생성 |
| F3 [codex] v2: outputs/reference/는 .gitignore | P2 | "git 추적 가능"이라 적었으나 실제 .gitignore line 7에 `outputs/` 명시 — PR 다른 환경에서 사라짐 | **§2.3 docs/reference/로 변경 + outputs/reference/는 generated artifact 전용** + 본 세션에서 standalone 재이동 완료 |
| F4 [codex] v2: upgrade decision hold와 status 4종 불일치 | P2 | decision에 `hold` 있으나 status 4종에 `on_hold` 없음 → 보류 보고서 누락 | **§8.2 상태 5종으로 확장** (`pending/approved/on_hold/rejected/promoted`) + 색상 토큰 추가 |
| F5 [codex] v2: E2E 테스트 fixture 부재 | P2 | `R-001` 하드코딩, `fake-snapshot-with-ape-decision` 직접 사용 — 404로 실패 가능 | **§11.2 beforeEach fixture 생성 절차** + `data/evaluation_reports/test_fixtures/` 시드 데이터 + 동적 report_id 사용 |

### 0.1 본 세션에서 즉시 실행한 정정

| 항목 | 결과 |
|---|---|
| `outputs/reference/dual_engine_v2_standalone.html` → `docs/reference/dual_engine_v2_standalone.html` | ✅ **이동 완료** (11 MB) |
| `outputs/reference/` 빈 폴더 정리 | ✅ |
| `.gitignore` 확인 | line 7: `outputs/` (전체 무시) — `docs/reference/`는 git 추적 가능 |

## 1. 핵심 운영 원칙 (v2 §1 + 신규 #10 #11 #12)

| 원칙 | 출처 |
|---|---|
| (v2 #1-#9 모두 계승) | v2 §1 |
| (신규) **#10 모든 API는 Pydantic BaseModel 사용** | codex v2 F1 [P1] |
| (신규) **#11 전시회 사전평가 = ExhibitionLeadSnapshot (FPE 미실행)** | codex v2 F2 [P1] |
| (신규) **#12 디자인 reference = docs/reference/ (git 추적)** | codex v2 F3 [P2] |

## 2. 원본 디자인 분석 (v2 §2 계승 + F3 보강)

### 2.1, 2.2 (v2 §2.1, §2.2 그대로 계승)

### 2.3 standalone 보관 위치 — F3 [P2] 정정

**v2의 잘못된 표기**: "`outputs/reference/`로 이동 — git 추적 가능"
**실측**: `.gitignore` line 7 `outputs/` → 전체 무시, **PR/다른 환경에서 사라짐**

**v3 정정**:

| 폴더 | 역할 | git 추적 | 본 세션 처리 |
|---|---|:---:|---|
| **`docs/reference/`** | **source artifact** (디자인 진실 소스, standalone 원본) | ✅ | `dual_engine_v2_standalone.html` (11 MB) **여기로 이동 완료** |
| `outputs/reference/` | **generated artifact** (Phase 0 rendered DOM 추출 결과 등) | ❌ (gitignore) | 빈 폴더 정리 |

**대용량 파일 정책**:
- 11 MB는 GitHub 100MB 경고선 미만 → git lfs 없이 추적 가능
- 향후 standalone 갱신 시 동일 위치 덮어쓰기 (히스토리는 git이 관리)

**스크립트 경로 정정**:

```bash
# v2 (잘못된 경로 — outputs/reference 추적 불가)
node scripts/extract_v2_tokens_rendered.js \
  --input outputs/reference/dual_engine_v2_standalone.html

# v3 (정정 — docs/reference 추적 가능)
node scripts/extract_v2_tokens_rendered.js \
  --input docs/reference/dual_engine_v2_standalone.html \
  --output outputs/reference/v2_tokens_rendered.css   # generated artifact는 outputs/
```

→ `--input`은 `docs/reference/` (source), `--output`은 `outputs/reference/` (generated). 둘의 역할 분리.

## 3. 디자인 시스템 통합 (v2 §3 그대로)

## 4. 9 화면 매트릭스 (v2 §4 그대로 — 8 운영 화면 + 1 신규 전시회)

| # | 화면 | v3 변경 |
|---|---|---|
| 1 | bizaipro_home.html | (변경 없음) |
| 2 | bizaipro_evaluation_result.html | URL `?report_id=...` 진입 시 GET API 호출 — body model 무관 |
| 3 | bizaipro_proposal_generator.html | **F1 [P1] 정정**: POST body model 사용 |
| 4 | bizaipro_email_generator.html | **F1 [P1] 정정**: POST body model 사용 |
| 5 | bizaipro_engine_compare.html | (변경 없음) |
| 6 | bizaipro_changelog.html | **F4 [P2]**: `on_hold` 행 표시 추가 |
| 7 | bizaipro_engine_management.html | **F4 [P2]**: 5 상태 카드 (pending/approved/on_hold/rejected/promoted) |
| 8 | bizaipro_exhibition_evaluator.html | **F2 [P1] 정정**: 사전평가 케이스에 `evaluation_status="not_evaluated"` 표시 |

## 5. 6 Phase 로드맵 (v2 §5 그대로 — 9주)

| Phase | 기간 | v3 정정 |
|---|---|---|
| Phase 0 | 1주 | standalone 보관을 `docs/reference/`로 (F3 P2) |
| Phase 1 | 2주 | EvaluationSnapshot **+ Pydantic BaseModel** (F1 P1) |
| Phase 2 | 1주 | 제안서/이메일 API **body model 강제** (F1 P1) |
| Phase 3 | 1주 | (변경 없음) |
| Phase 4 | 2주 | upgrade decision **hold 상태 처리** (F4 P2) |
| Phase 5 | 2주 | 전시회 사전평가 **ExhibitionLeadSnapshot 분리** (F2 P1) |

## 6. 우선순위 매트릭스 (v2 §6 그대로)

## 7. EvaluationSnapshot — Pydantic BaseModel 명시 (F1 + F2 정정)

### 7.1 EvaluationSnapshot 모델 (v2 §7.1 + 명확화)

```python
from pydantic import BaseModel
from typing import Literal, Optional
from datetime import datetime

class EvaluationSnapshot(BaseModel):
    """FPE가 실제 실행된 평가 결과 — F2 [codex] P2 분리"""
    report_id: str
    created_at: datetime
    company_name: str
    state_key: str
    server_input_hash: str

    # 결정 근거 (F2 정정 — FPE 실제 실행 시에만 "FPE")
    decision_source: Literal["FPE"] = "FPE"
    evaluation_status: Literal["evaluated"] = "evaluated"
    fpe_version: str
    ape_version: str

    # FPE 평가 결과 (제안서/이메일 기준)
    fpe_flow_score: int
    fpe_credit_limit: int
    fpe_margin_rate: float
    fpe_payment_grace_days: int
    fpe_knockout_reasons: list[str]
    proposal_allowed: bool
    blocked_reason: Optional[str] = None

    # APE 비교 결과 (참고만)
    ape_flow_score: int
    ape_credit_limit: int
    ape_margin_rate: float
    ape_diff_summary: dict

    consensus: Literal[
        "both_go", "fpe_blocked", "ape_only_positive",
        "ape_blocked", "both_review"
    ]

    source_quality: dict
```

### 7.2 Request Models (F1 [P1] — Pydantic BaseModel 강제)

```python
# v2 잘못된 예시:
# @app.post("/api/evaluation/report")
# async def create_evaluation_report(state: dict): ...    ← Content-Type 모호

# v3 정정:
class EvaluationReportRequest(BaseModel):
    """평가보고서 생성 요청"""
    state: dict   # learning state 전체 (bizaipro_shared.js의 state)
    force_recreate: bool = False
    notes: Optional[str] = None

@app.post("/api/evaluation/report", response_model=EvaluationSnapshot)
async def create_evaluation_report(req: EvaluationReportRequest):
    # 1. /api/learning/evaluate/dual 내부 호출
    dual = await _evaluate_dual_internal(req.state)

    # 2. EvaluationSnapshot 직렬화
    snapshot = EvaluationSnapshot(
        report_id=str(ulid.new()),
        created_at=datetime.utcnow(),
        decision_source="FPE",
        evaluation_status="evaluated",
        # ... dual 응답에서 매핑
    )

    # 3. 저장
    save_snapshot(snapshot)
    return snapshot


class ProposalGenerateRequest(BaseModel):
    """제안서 생성 요청 (snapshot 기반)"""
    report_id: str
    template_variant: Literal["standard", "exhibition"] = "standard"
    notes: Optional[str] = None

@app.post("/api/proposal/generate")
async def generate_proposal(req: ProposalGenerateRequest):
    snapshot = load_evaluation_snapshot(req.report_id)
    if not snapshot:
        raise HTTPException(404, f"snapshot not found: {req.report_id}")

    # decision_source 강제 (§3.3 #1)
    if snapshot.decision_source != "FPE":
        raise HTTPException(400, "decision_source must be FPE")

    # FPE 차단 시 거부
    if not snapshot.proposal_allowed:
        raise HTTPException(403, f"FPE blocked: {snapshot.blocked_reason}")

    # FPE 값으로만 생성 (§3.3 #2)
    return ProposalSnapshot(
        report_id=req.report_id,
        proposal_id=str(ulid.new()),
        company_name=snapshot.company_name,
        credit_limit=snapshot.fpe_credit_limit,
        margin_rate=snapshot.fpe_margin_rate,
        payment_grace_days=snapshot.fpe_payment_grace_days,
        # APE 값 절대 사용 안 함
    )


class EmailGenerateRequest(BaseModel):
    """이메일 생성 요청"""
    report_id: Optional[str] = None        # 평가 snapshot 직접 사용
    proposal_id: Optional[str] = None      # 또는 제안서 snapshot 경유
    template_variant: Literal["standard", "exhibition_cold"] = "standard"
    recipient: str
    cc: list[str] = []

@app.post("/api/email/generate")
async def generate_email(req: EmailGenerateRequest):
    if not (req.report_id or req.proposal_id):
        raise HTTPException(400, "report_id 또는 proposal_id 필수")
    # ...
```

### 7.3 fetch 예시 — Content-Type 헤더 명시 (F1 [P1])

**v2 잘못된 예시**:
```javascript
// ❌ Content-Type 누락 — 서버에서 422 가능
const snapshot = await fetch('/api/evaluation/report', {
  method: 'POST',
  body: JSON.stringify(getCurrentState())
}).then(r => r.json());
```

**v3 정정**:
```javascript
// ✅ Content-Type 명시 + body는 BaseModel 스키마와 일치
const snapshot = await fetch('/api/evaluation/report', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    state: getCurrentState(),
    force_recreate: false
  })
}).then(r => r.json());

// 제안서 생성 — body model 사용
const proposal = await fetch('/api/proposal/generate', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    report_id: snapshot.report_id,
    template_variant: 'standard'
  })
}).then(r => {
  if (r.status === 403) throw new Error('FPE blocked');
  if (r.status === 400) throw new Error('decision_source not FPE');
  if (r.status === 404) throw new Error('snapshot not found');
  return r.json();
});

// 이메일 생성
const email = await fetch('/api/email/generate', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    report_id: snapshot.report_id,
    template_variant: 'standard',
    recipient: 'purchasing@abc.co.kr'
  })
}).then(r => r.json());
```

→ **모든 POST는 `Content-Type: application/json` + body model 스키마 일치 강제**.

### 7.4 GET endpoints (body 무관)

```python
@app.get("/api/evaluation/report/{report_id}", response_model=EvaluationSnapshot)
async def get_evaluation_report(report_id: str):
    """path parameter — body 무관"""
    snapshot = load_evaluation_snapshot(report_id)
    if not snapshot:
        raise HTTPException(404)
    return snapshot

@app.get("/api/evaluation/reports", response_model=list[EvaluationSnapshot])
async def list_evaluation_reports(
    limit: int = 20,
    company_name: Optional[str] = None
):
    """query parameters만 — body 무관"""
    return query_snapshots(limit=limit, company_name=company_name)
```

```javascript
// GET — Content-Type 헤더 불필요
const snapshot = await fetch(`/api/evaluation/report/${reportId}`).then(r => r.json());
const reports = await fetch('/api/evaluation/reports?limit=20').then(r => r.json());
```

### 7.5 ExhibitionLeadSnapshot — F2 [codex] P1 신설

**v2의 잘못된 패턴** (FPE 실제 실행 안 했는데 `decision_source: "FPE"`):
```python
# ❌ v2 — FPE 평가 완료라는 불변식과 충돌
snapshot = {
    "decision_source": "FPE",
    "proposal_allowed": False,
    "blocked_reason": "기업리포트 미연결",
    # fpe_credit_limit, server_input_hash 등 누락 — 클라이언트가 기대하면 실패
}
```

**v3 정정** — 별도 모델로 분리:
```python
class ExhibitionLeadSnapshot(BaseModel):
    """전시회 참가기업 사전 정보 — FPE 실제 실행 안 됨"""
    lead_id: str
    created_at: datetime
    company_name: str
    exhibition_name: str
    exhibition_year: int
    industry: str
    homepage: Optional[str] = None
    contact_name: Optional[str] = None

    # 평가 상태 (F2 정정)
    decision_source: None = None              # FPE 미실행
    evaluation_status: Literal["not_evaluated"] = "not_evaluated"
    proposal_allowed: bool = False
    blocked_reason: str = "기업리포트/FlowScore 미연결"

    # 후속 행동 안내
    required_actions: list[str] = [
        "기업리포트 업로드",
        "FlowScore 자동 조회 시도",
        "관리자에게 추가 심사 요청"
    ]
```

**API 흐름** (F2 [P1]):
```python
class ExhibitionEvaluateRequest(BaseModel):
    company_name: str
    exhibition_name: str
    exhibition_year: int
    industry: str
    homepage: Optional[str] = None
    contact_name: Optional[str] = None

@app.post("/api/exhibition/evaluate")
async def evaluate_exhibition_company(
    req: ExhibitionEvaluateRequest
) -> EvaluationSnapshot | ExhibitionLeadSnapshot:
    # 1. 기업리포트/FlowScore 연결 시도
    enrichment = try_enrich_company(req.company_name, req.homepage)

    if enrichment.has_full_report:
        # FPE 정식 평가 — EvaluationSnapshot
        return await create_evaluation_report(EvaluationReportRequest(
            state=build_state_from_exhibition(req, enrichment)
        ))
    else:
        # 사전평가 — ExhibitionLeadSnapshot (FPE 미실행)
        return ExhibitionLeadSnapshot(
            lead_id=str(ulid.new()),
            created_at=datetime.utcnow(),
            company_name=req.company_name,
            exhibition_name=req.exhibition_name,
            exhibition_year=req.exhibition_year,
            industry=req.industry,
            homepage=req.homepage,
            contact_name=req.contact_name,
            # decision_source는 None (FPE 미실행)
            evaluation_status="not_evaluated",
            blocked_reason="기업리포트/FlowScore 미연결"
        )
```

**클라이언트 분기** (F2 [P1]):
```javascript
const result = await fetch('/api/exhibition/evaluate', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    company_name: 'XYZ산업㈜',
    exhibition_name: 'SIMTOS 2026',
    exhibition_year: 2026,
    industry: '절삭공구',
    homepage: 'xyz.co.kr'
  })
}).then(r => r.json());

// 응답 분기 (F2 정정)
if (result.evaluation_status === 'evaluated') {
  // EvaluationSnapshot — 듀얼 카드 + 콜드메일 가능
  renderDualCards(result);
  if (result.proposal_allowed) {
    enableColdEmailButton();
  } else {
    showFpeBlockedBanner(result.blocked_reason);  // FPE 차단
  }
} else if (result.evaluation_status === 'not_evaluated') {
  // ExhibitionLeadSnapshot — 사전평가 (FPE 미실행)
  showLeadOnlyBanner(result.blocked_reason);     // "기업리포트 미연결"
  disableColdEmailButton();
  showRequiredActions(result.required_actions);
}
```

→ **운영자가 "FPE 차단"과 "FPE 미실행"을 명확히 구분 가능**.

## 8. 월간 엔진업데이트 — 5 상태 (F4 정정)

### 8.1 v2 → v3 상태 확장

| v2 (4 상태) | v3 (5 상태) |
|---|---|
| pending | pending |
| approved | approved |
| **(없음 — hold 모호)** | **on_hold (신설)** |
| rejected | rejected |
| promoted | promoted |

### 8.2 decision API 명세 (F4 정정)

```python
class UpgradeDecisionRequest(BaseModel):
    decision: Literal["approved", "rejected", "on_hold"]
    decision_reason: str
    admin_id: str

@app.post("/api/engine/upgrade-reports/{report_id}/decision")
async def submit_upgrade_decision(
    report_id: str,
    req: UpgradeDecisionRequest
):
    report = load_upgrade_report(report_id)

    if req.decision == "approved":
        report.status = "approved"      # promote 대기
    elif req.decision == "rejected":
        report.status = "rejected"      # 종료
    elif req.decision == "on_hold":
        report.status = "on_hold"       # 보류 — 다음 회차에 재검토
        # admin_decision_history에 누적 기록
        report.admin_decision_history.append({
            "decision": "on_hold",
            "reason": req.decision_reason,
            "admin_id": req.admin_id,
            "at": datetime.utcnow()
        })

    save_upgrade_report(report)
    return report
```

### 8.3 상태별 색상 토큰 (v2_tokens.css 갱신)

```css
/* v2_tokens.css 5 상태 (F4 정정) */
--fbu-color-status-pending:   #F57C00;  /* 검토 대기 — 오렌지 */
--fbu-color-status-approved:  #1976D2;  /* 승인됨 — 블루 */
--fbu-color-status-on-hold:   #6D4C41;  /* 보류 — 브라운 (신설) */
--fbu-color-status-rejected:  #C62828;  /* 반려 — 레드 */
--fbu-color-status-promoted:  #2E7D32;  /* 반영 완료 — 그린 */
```

### 8.4 화면 갱신 (F4 정정)

```
[engine_management.html — 5 상태 카드]
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│ pending  │ │ approved │ │ on_hold  │ │ rejected │ │ promoted │
│    3     │ │    12    │ │    2 ★   │ │    2     │ │    5     │
│ (orange) │ │ (blue)   │ │ (brown)★ │ │ (red)    │ │ (green)  │
└──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘
              ★ F4 신설 — 보류 카드 추가
```

### 8.5 changelog 화면 갱신 (F4 정정)

```
| 일시       | 보고서 ID  | 상태       | 액션 이력         |
|------------|------------|------------|-------------------|
| 04-30 13:00| UR-04-30   | promoted   | hold (1회) → 승인 |  ← 보류 이력 표시
| 03-30 13:00| UR-03-30   | promoted   | 승인              |
| 02-29 13:00| UR-02-29   | rejected   | 반려              |
```

## 9. 7항 원칙 매핑 (v2 §9 + 신규 #10 #11 #12)

| 원칙 | v3 디자인 매핑 |
|---|---|
| (#1-#9 v2 동일) | (계승) |
| #10 모든 API는 BaseModel | §7.2 Pydantic 명시 + Content-Type 헤더 강제 |
| #11 전시회 사전평가 = ExhibitionLeadSnapshot | §7.5 분리 모델 |
| #12 디자인 reference = docs/reference/ | §2.3 git 추적 가능 위치 |

## 10. 데이터 바인딩 (v2 §10 + Content-Type/body model 정정)

(v2 §10 그대로 + 모든 fetch 예시에 Content-Type 헤더 + body model 스키마 적용 — §7.3 참조)

## 11. 검증 계획 — E2E fixture 절차 신설 (F5 정정)

### 11.1 v2 §11.1-11.3 (그대로 계승)

### 11.2 신규 E2E 테스트 — fixture 생성 절차 (F5 [P2])

**v2의 잘못된 예시**:
```javascript
// ❌ R-001 하드코딩 — 404 가능
test('proposal form does NOT bind ape_* values', async ({ page }) => {
  await page.goto('/web/bizaipro_proposal_generator.html?report_id=R-001');
  // ...
});
```

**v3 정정** — `beforeEach`에서 fixture 생성:

```typescript
// tests/e2e/fixtures/snapshot_seeder.ts
import { test as base } from '@playwright/test';

export const test = base.extend<{
  testReportId: string;
  fakeApeBoundReportId: string;
}>({
  // 정상 snapshot fixture
  testReportId: async ({ request }, use) => {
    const response = await request.post('/api/evaluation/report', {
      headers: { 'Content-Type': 'application/json' },
      data: {
        state: {
          company_name: 'TestCorp',
          industry_profile: { code: 'C29', label: '기계' },
          financial_filter_signal: 'pass',
          // ... 표준 통과 케이스
        }
      }
    });
    const snapshot = await response.json();
    await use(snapshot.report_id);
    // teardown: 테스트 fixture 정리
    await request.delete(`/api/evaluation/report/${snapshot.report_id}`);
  },

  // negative case: decision_source != FPE인 jail snapshot
  fakeApeBoundReportId: async ({ request }, use) => {
    // test-only seed API (테스트 환경에서만 활성화)
    const response = await request.post('/api/test/seed-snapshot', {
      headers: { 'Content-Type': 'application/json' },
      data: {
        decision_source: 'APE',  // 정책 위반 케이스
        proposal_allowed: false,
      }
    });
    const snapshot = await response.json();
    await use(snapshot.report_id);
    await request.delete(`/api/evaluation/report/${snapshot.report_id}`);
  }
});
```

```typescript
// tests/e2e/decision_source_fpe.spec.ts
import { test } from './fixtures/snapshot_seeder';
import { expect } from '@playwright/test';

test('proposal API rejects non-FPE decision_source', async ({
  request, fakeApeBoundReportId
}) => {
  // F1 정정: Content-Type + body model
  const response = await request.post('/api/proposal/generate', {
    headers: { 'Content-Type': 'application/json' },
    data: { report_id: fakeApeBoundReportId, template_variant: 'standard' }
  });
  expect(response.status()).toBe(400);

  const body = await response.json();
  expect(body.detail).toContain('decision_source must be FPE');
});

test('proposal form does NOT bind ape_* values', async ({
  page, testReportId
}) => {
  // 동적 report_id 사용 (R-001 하드코딩 제거)
  await page.goto(`/web/bizaipro_proposal_generator.html?report_id=${testReportId}`);

  // snapshot 응답에서 ape 값을 표시 (테스트 setup)
  const snapshot = await page.evaluate(async (id) => {
    return fetch(`/api/evaluation/report/${id}`).then(r => r.json());
  }, testReportId);

  // ape 값이 form input에 들어가지 않음을 검증
  const apeValueExposed = await page.evaluate((apeValues) => {
    const inputs = document.querySelectorAll('input[type="text"], input[type="number"], textarea');
    return Array.from(inputs).some(input =>
      input.value.includes(apeValues.fpe_credit_limit) === false &&
      (input.value.includes(apeValues.ape_credit_limit) ||
       input.value.includes(apeValues.ape_margin_rate))
    );
  }, snapshot);

  expect(apeValueExposed).toBe(false);
});
```

### 11.3 test-only seed API 가드 (F5 보안)

```python
# app.py — 테스트 환경에서만 활성화
import os

if os.getenv("FLOWBIZ_ENV") == "test":
    @app.post("/api/test/seed-snapshot")
    async def seed_test_snapshot(snapshot: dict):
        """테스트 환경 전용 — production에서는 비활성화"""
        save_snapshot(EvaluationSnapshot(**snapshot))
        return snapshot

    @app.delete("/api/evaluation/report/{report_id}")
    async def delete_evaluation_report(report_id: str):
        delete_snapshot(report_id)
```

### 11.4 fixture 디렉토리 구조

```
tests/e2e/
├── fixtures/
│   ├── snapshot_seeder.ts          # Playwright fixture
│   └── seed_data/
│       ├── both_go_normal.json     # 정상 통과 케이스
│       ├── fpe_blocked_ccc.json    # FPE 차단 (CCC 등급)
│       ├── ape_only_positive.json
│       └── exhibition_lead.json    # ExhibitionLeadSnapshot 케이스
├── decision_source_fpe.spec.ts
├── proposal_form_no_ape.spec.ts
└── exhibition_evaluator.spec.ts
```

## 12. Risk + Mitigation (v2 §12 + 신규)

| Risk | 영향 | 대응 |
|---|---|---|
| (v2 동일) AppleGothic 미지원 | 폰트 깨짐 | font fallback |
| (v2 동일) 11MB git 비대화 | 저장소 부담 | docs/reference/ + git lfs 검토 |
| **(신규)** Pydantic body 미일치 | 422 오류 | request model 명시 + Content-Type 강제 (F1) |
| **(신규)** 전시회 lead가 EvaluationSnapshot로 잘못 분류 | 운영 혼선 | ExhibitionLeadSnapshot 분리 (F2) |
| **(신규)** outputs/reference/ 추적 안 됨 | PR 다른 환경 자료 사라짐 | docs/reference/로 변경 (F3) |
| **(신규)** upgrade hold 보고서 누락 | 관리 사각지대 | on_hold 5 상태 (F4) |
| **(신규)** E2E test fixture 부재 | 테스트 결과 신뢰 저하 | beforeEach fixture seed (F5) |

## 13. 다음 액션 (codex v2 §4 체크리스트 6건 통합)

- [x] **(F1)** EvaluationReportRequest, ProposalGenerateRequest, EmailGenerateRequest BaseModel — §7.2 명시
- [x] **(F1)** fetch 예시 Content-Type 추가 — §7.3 모든 예시 정정
- [x] **(F2)** 전시회 사전평가 ExhibitionLeadSnapshot 분리 — §7.5 신설
- [x] **(F3)** docs/reference/ 정책 — §2.3 + 본 세션 standalone 재이동 완료
- [x] **(F4)** 월간 hold 상태 처리 — §8 5 상태로 확장
- [x] **(F5)** E2E fixture 절차 — §11.2 beforeEach 신설

## 14. 핵심 메시지

**v2 → v3 핵심 보강 5건**:
1. **API request models** Pydantic BaseModel 강제 (codex F1) — FastAPI 422 오류 차단
2. **전시회 사전평가** ExhibitionLeadSnapshot 분리 (codex F2) — `decision_source=null` + `evaluation_status="not_evaluated"`
3. **standalone 보관** docs/reference/로 (codex F3) — git 추적 + 본 세션 즉시 이동 완료
4. **upgrade hold 상태** 5종으로 확장 (codex F4) — 보류 보고서 누락 차단
5. **E2E fixture** beforeEach seed 절차 (codex F5) — 하드코딩 ID 제거

→ codex v2 §5 인용: "위 신규 Finding 5건을 반영하면 실제 구현 착수 계획으로 승인 가능하다." → **v3에서 5건 모두 반영 완료**.

---

## 부록 A. v2 → v3 정정 위치

### A.1 API Pydantic BaseModel (F1 P1)

| 위치 | v2 | v3 |
|---|---|---|
| §7.2 `/api/evaluation/report` | `state: dict` 인자 | **`EvaluationReportRequest(BaseModel)`** + `state: dict` 필드 |
| §7.2 `/api/proposal/generate` | `report_id: str` 인자 | **`ProposalGenerateRequest(BaseModel)`** |
| (신규) `/api/email/generate` | (구체 미정의) | **`EmailGenerateRequest(BaseModel)`** |
| §10 fetch 예시 | `body: JSON.stringify(...)` 만 | **`headers: { 'Content-Type': 'application/json' }`** 추가 |

### A.2 ExhibitionLeadSnapshot 분리 (F2 P1)

| 위치 | v2 | v3 |
|---|---|---|
| §10.3 전시회 분기 | `{decision_source: "FPE", proposal_allowed: false}` 임시 snapshot | **§7.5 ExhibitionLeadSnapshot** + `decision_source=null` + `evaluation_status="not_evaluated"` |
| §4.8 화면 분기 | (단일 분기) | **`evaluation_status` 기준 2 분기** (evaluated / not_evaluated) |

### A.3 docs/reference/ (F3 P2)

| 위치 | v2 | v3 |
|---|---|---|
| §2.3 보관 위치 | "outputs/reference/ — git 추적 가능" (잘못) | **"docs/reference/ — git 추적, outputs/reference/는 generated 전용"** |
| §11.3 검증 명령 | `--input outputs/reference/...` | **`--input docs/reference/... --output outputs/reference/...`** |
| 본 세션 처리 | (없음) | **standalone 11MB 재이동 완료** |

### A.4 upgrade 5 상태 (F4 P2)

| 위치 | v2 | v3 |
|---|---|---|
| §8.2 상태값 | `pending/approved/promoted/rejected` (4종) | **`pending/approved/on_hold/rejected/promoted` (5종)** |
| §8.3 색상 | 4 토큰 | **5 토큰** (--fbu-color-status-on-hold #6D4C41 신설) |
| §8.4 화면 카드 | 4 카드 | **5 카드** |
| §4.7 engine_management | 4 상태 표시 | 5 상태 표시 |

### A.5 E2E fixture (F5 P2)

| 위치 | v2 | v3 |
|---|---|---|
| §11.2 spec 예시 | `report_id: 'R-001'` 하드코딩 | **`testReportId` Playwright fixture** |
| §11.2 negative case | `'fake-snapshot-with-ape-decision'` 하드코딩 | **`fakeApeBoundReportId` fixture + test-only seed API** |
| §11.3 (신규) | (없음) | **test-only `/api/test/seed-snapshot` + `FLOWBIZ_ENV=test` 가드** |
| §11.4 (신규) | (없음) | **fixture 디렉토리 구조 + 4 seed JSON** |

## 부록 B. 누적 Finding 추적

| 단계 | 신규 Finding | 누적 |
|---|---|---|
| 본 계획 v1 | 0 (자체) | 0 |
| 본 계획 v2 | 0 (codex v1 4건 반영) | 4 |
| **본 계획 v3** | **0 (codex v2 5건 반영)** | **9** |

**잔여 P0/P1**: 0건.

## 부록 C. 본 세션 즉시 실행 작업 로그

| 작업 | 결과 |
|---|---|
| `mkdir -p docs/reference/` | ✅ |
| `mv outputs/reference/dual_engine_v2_standalone.html docs/reference/` | ✅ (11 MB) |
| `rmdir outputs/reference/` (빈 폴더) | ✅ |
| `.gitignore` 확인 — `outputs/`는 line 7 무시 | ✅ |
| `docs/reference/` git 추적 가능 확인 | ✅ |

## 부록 D. v2_tokens.css 갱신 항목 (Phase 0)

```css
/* v2 → v3 변경 (F4 정정) */

/* 기존 4 토큰 */
--fbu-color-status-pending:   #F57C00;
--fbu-color-status-approved:  #1976D2;
--fbu-color-status-promoted:  #2E7D32;
--fbu-color-status-rejected:  #C62828;

/* v3 신설 — F4 P2 */
--fbu-color-status-on-hold:   #6D4C41;  /* 보류 — 브라운 (검토 보류 시각 구분) */
```

→ Phase 0에서 `web/styles/v2_tokens.css` 1줄 추가.
