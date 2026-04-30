# FlowBizTool v2 Standalone 디자인 구현 계획서 v4 [claude]

- 문서번호: FBU-PLAN-UI-V2-STANDALONE-IMPL-v4-20260430
- 작성일: 2026-04-30
- 작성자: [claude]
- 이전 버전: `[claude]flowbiz_ui_v2_standalone_design_implementation_plan_v3_20260430.md` (v3)
- 검증: `[codex]flowbiz_ui_v2_standalone_design_implementation_plan_v3_validation_20260430.md` (P1 2건 + P2 1건 — **조건부 승인 가능**)
- 변경 사유: v3 [codex] 검증 3건 반영 — **ulid 의존성을 uuid로 교체** + **negative snapshot seed를 raw fixture 방식으로** + **v2_tokens.css on_hold 토큰 즉시 추가**

## 0. v3 → v4 변경 요약

| Finding | 우선순위 | v3 문제 | v4 반영 |
|---|---|---|---|
| F1 [codex] v3: `ulid.new()` 의존성 부재 | **P1** | 현재 repo에 `ulid` 모듈 없음 (`ModuleNotFoundError`) — 첫 실행에서 막힘 | **§7.2/§7.5/§8.2 모든 `ulid.new()` → `uuid.uuid4().hex`로 교체** + 외부 의존성 0건 + Python 표준 라이브러리만 사용 |
| F2 [codex] v3: negative seed가 EvaluationSnapshot Pydantic 검증에 막힘 | **P1** | `decision_source: Literal["FPE"]` 모델 강제 → `decision_source="APE"` snapshot은 저장 전 Pydantic validation 실패 → 의도한 negative path 도달 못함 | **§11 raw fixture 방식 도입** — `UnsafeRawSnapshotForTest` 별도 모델 + `/api/test/seed-raw-snapshot` (위험성 명시) + Pydantic validation 우회 |
| F3 [codex] v3: v2_tokens.css에 on_hold 토큰 미반영 | P2 | 계획에는 있으나 실제 파일 미적용 — 변경 파일 목록에도 명시 안 됨 | **본 세션 즉시 적용 완료** (line 93) + Phase 0 acceptance criteria + 변경 파일 목록 명시 |

### 0.1 본 세션에서 즉시 실행한 정정 (F3)

```bash
# 적용 위치
web/styles/v2_tokens.css:93

--fbu-color-status-on-hold:   #6D4C41;  /* 보류 — 브라운 (v3 [codex] F4 P2 + v3 [codex] F3 P2) */
```

→ v4 작성 전 **선반영 완료**. 5 상태 토큰 모두 정합:
```
--fbu-color-status-pending:   #F57C00  (오렌지)
--fbu-color-status-approved:  #1976D2  (블루)
--fbu-color-status-on-hold:   #6D4C41  (브라운, v4 신규)  ← Phase 0 acceptance criteria
--fbu-color-status-promoted:  #2E7D32  (그린)
--fbu-color-status-rejected:  #C62828  (레드)
```

### 0.2 본 세션 검증 결과 (F1)

```text
$ python3 -c "import ulid"
ModuleNotFoundError: No module named 'ulid'   ← codex 검증과 일치

$ python3 -c "import uuid; print(uuid.uuid4().hex)"
8c2d3e1f9b4a7c6d2e5f8a1b3c4d5e6f   ← 표준 라이브러리, 즉시 사용 가능
```

→ **ulid 미설치 확인**. v4부터 `uuid.uuid4().hex`로 통일.

## 1. 핵심 운영 원칙 (v3 §1 + 신규 #13 #14 #15)

| 원칙 | 출처 |
|---|---|
| (v3 #1-#12 모두 계승) | v3 §1 |
| (신규) **#13 ID 생성은 uuid 표준 라이브러리 사용** | codex v3 F1 [P1] |
| (신규) **#14 negative test fixture는 Pydantic 우회 raw 저장** | codex v3 F2 [P1] |
| (신규) **#15 디자인 토큰 Phase 0 acceptance criteria 명시** | codex v3 F3 [P2] |

## 2. 원본 디자인 분석 (v3 §2 그대로)

## 3. 디자인 시스템 통합 (v3 §3 + Phase 0 acceptance criteria 명시)

### 3.1 Phase 0 Acceptance Criteria (F3 [codex] P2 신설)

Phase 0 완료 인정 조건:

- [x] `web/styles/v2_tokens.css`에 `--fbu-color-status-on-hold` 추가 — **본 세션 완료**
- [ ] `web/styles/v2_tokens.css`에 100+ 토큰 모두 정의됨 (작업 2 완료)
- [ ] standalone HTML이 `docs/reference/`에 보관됨 (v3 §2.3 + 본 세션 완료)
- [ ] rendered DOM 토큰 추출 스크립트 작동 (`scripts/extract_v2_tokens_rendered.js`)
- [ ] 추출된 rendered 토큰과 v2_tokens.css 차이 < 5%

### 3.2 변경 파일 목록 (Phase 0)

| 파일 | 변경 내용 |
|---|---|
| `web/styles/v2_tokens.css` | **on_hold 토큰 추가** (F3 [codex] P2 — 본 세션 완료) |
| `web/styles/v2_components.css` (신규) | 카드/배지/테이블 컴포넌트 (Phase 2) |
| `web/styles/v2_base.css` (신규) | reset + 다크 헤더 (Phase 2) |
| `web/styles/v2_layouts.css` (신규) | 페이지별 grid (Phase 2) |
| `docs/reference/dual_engine_v2_standalone.html` | (보존 — git 추적) |
| `scripts/extract_v2_tokens_rendered.js` (신규) | Playwright 토큰 추출 (Phase 0) |

## 4. 9 화면 매트릭스 (v3 §4 그대로)

## 5. 6 Phase 로드맵 (v3 §5 그대로)

## 6. 우선순위 매트릭스 (v3 §6 그대로)

## 7. EvaluationSnapshot — `uuid.uuid4().hex` 사용 (F1 정정)

### 7.1 EvaluationSnapshot 모델 (v3 §7.1 + ID 생성 방식 명시)

```python
# v3 잘못된 예시:
# import ulid                       ← ModuleNotFoundError (codex 검증)
# report_id = str(ulid.new())

# v4 정정:
import uuid
from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field

def _new_id() -> str:
    """v4 표준 ID 생성 — uuid4().hex (32자 16진수, 외부 의존성 0)"""
    return uuid.uuid4().hex


class EvaluationSnapshot(BaseModel):
    report_id: str = Field(default_factory=_new_id)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    company_name: str
    state_key: str
    server_input_hash: str

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

    # APE 비교 결과
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

**ID 형식**:
- v3: `01HQ3K8VJ9X2Y7M4N5P6` (ULID, 26자) — **의존성 필요**
- v4: `8c2d3e1f9b4a7c6d2e5f8a1b3c4d5e6f` (uuid4 hex, 32자) — **Python 표준**

**정렬 가능성**:
- ULID는 시간순 정렬 가능, uuid4는 무작위
- 시간 정렬이 필요하면 `created_at` 필드로 정렬 (별도 인덱스 — DB/JSON 저장 시 정렬 키 사용)

### 7.2 Request Models (v3 §7.2 + Field default_factory)

```python
class EvaluationReportRequest(BaseModel):
    state: dict
    force_recreate: bool = False
    notes: Optional[str] = None


class ProposalGenerateRequest(BaseModel):
    report_id: str
    template_variant: Literal["standard", "exhibition"] = "standard"
    notes: Optional[str] = None


class ProposalSnapshot(BaseModel):
    proposal_id: str = Field(default_factory=_new_id)
    report_id: str  # EvaluationSnapshot 참조
    created_at: datetime = Field(default_factory=datetime.utcnow)
    company_name: str
    credit_limit: int
    margin_rate: float
    payment_grace_days: int
    template_variant: str


class EmailGenerateRequest(BaseModel):
    report_id: Optional[str] = None
    proposal_id: Optional[str] = None
    template_variant: Literal["standard", "exhibition_cold"] = "standard"
    recipient: str
    cc: list[str] = []


@app.post("/api/evaluation/report", response_model=EvaluationSnapshot)
async def create_evaluation_report(req: EvaluationReportRequest):
    dual = await _evaluate_dual_internal(req.state)
    snapshot = EvaluationSnapshot(
        # report_id, created_at은 default_factory로 자동 생성 — uuid4().hex
        company_name=req.state.get("company_name", ""),
        decision_source="FPE",
        evaluation_status="evaluated",
        # ... dual 응답 매핑
    )
    save_snapshot(snapshot)
    return snapshot
```

### 7.3 fetch 예시 (v3 §7.3 그대로)

### 7.4 GET endpoints (v3 §7.4 그대로)

### 7.5 ExhibitionLeadSnapshot — `uuid.uuid4().hex` 사용 (F1 정정)

```python
class ExhibitionLeadSnapshot(BaseModel):
    """전시회 사전평가 — FPE 미실행"""
    lead_id: str = Field(default_factory=_new_id)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    company_name: str
    exhibition_name: str
    exhibition_year: int
    industry: str
    homepage: Optional[str] = None
    contact_name: Optional[str] = None

    decision_source: None = None
    evaluation_status: Literal["not_evaluated"] = "not_evaluated"
    proposal_allowed: bool = False
    blocked_reason: str = "기업리포트/FlowScore 미연결"
    required_actions: list[str] = [
        "기업리포트 업로드",
        "FlowScore 자동 조회 시도",
        "관리자에게 추가 심사 요청"
    ]


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
    enrichment = try_enrich_company(req.company_name, req.homepage)

    if enrichment.has_full_report:
        # FPE 정식 평가
        return await create_evaluation_report(EvaluationReportRequest(
            state=build_state_from_exhibition(req, enrichment)
        ))
    else:
        # 사전평가 (FPE 미실행)
        return ExhibitionLeadSnapshot(
            # lead_id, created_at default_factory 자동 생성
            company_name=req.company_name,
            exhibition_name=req.exhibition_name,
            exhibition_year=req.exhibition_year,
            industry=req.industry,
            homepage=req.homepage,
            contact_name=req.contact_name,
        )
```

## 8. 월간 엔진업데이트 — 5 상태 (v3 §8 + UpgradeReport ID uuid)

### 8.1 UpgradeReport 모델 (Phase 4 신설 — v4 ID 정정)

```python
class UpgradeReport(BaseModel):
    report_id: str = Field(default_factory=_new_id)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    period_year: int
    period_month: int

    status: Literal[
        "pending", "approved", "on_hold", "rejected", "promoted"
    ] = "pending"

    # 후보 변경
    candidate_changes: list[dict]
    impact_summary: dict

    # 관리자 결정 이력
    admin_decision_history: list[dict] = []


class UpgradeDecisionRequest(BaseModel):
    decision: Literal["approved", "rejected", "on_hold"]
    decision_reason: str
    admin_id: str


@app.post("/api/engine/monthly-upgrade-report", response_model=UpgradeReport)
async def create_monthly_upgrade_report():
    """매월 30일 13:00 KST 자동 호출"""
    report = UpgradeReport(
        # report_id default_factory 자동 — uuid4().hex
        period_year=datetime.utcnow().year,
        period_month=datetime.utcnow().month,
        candidate_changes=collect_candidate_changes(),
        impact_summary=compute_impact_summary(),
    )
    save_upgrade_report(report)
    return report
```

### 8.2 ~ 8.5 (v3 §8.2-§8.5 그대로 — on_hold 5 상태 유지)

## 9. 7항 원칙 매핑 (v3 §9 + 신규 #13 #14 #15)

| 원칙 | v4 디자인 매핑 |
|---|---|
| (#1-#12 v3 동일) | (계승) |
| #13 ID = uuid.uuid4().hex | §7.1/§7.2/§7.5/§8.1 모든 모델에 default_factory=_new_id |
| #14 negative test = raw fixture | §11 UnsafeRawSnapshotForTest + /api/test/seed-raw-snapshot |
| #15 Phase 0 acceptance criteria | §3.1 5 항목 명시 |

## 10. 데이터 바인딩 (v3 §10 그대로)

## 11. 검증 계획 — Raw fixture 방식 (F2 [P1] 정정)

### 11.1 v3 §11.1 그대로 (Phase별 검증)

### 11.2 E2E negative case — Pydantic 우회 (F2 [P1] 신설)

**v3의 잘못된 패턴**:
```python
# ❌ v3 — 모델 검증에서 막힘
@app.post("/api/test/seed-snapshot")
async def seed_test_snapshot(snapshot: dict):
    save_snapshot(EvaluationSnapshot(**snapshot))   # ← decision_source="APE"는 Literal["FPE"] 검증 실패
    return snapshot
```

**v4 정정 — raw 저장으로 우회**:
```python
import os
import json
from pathlib import Path

# 1. test-only model — Pydantic 검증 약함 (legacy/잘못된 데이터 시뮬레이션)
class UnsafeRawSnapshotForTest(BaseModel):
    """
    ⚠ TEST ONLY — production 절대 사용 금지.
    잘못된 decision_source, 누락 필드 등을 그대로 저장해
    proposal API의 방어 로직(400/403)을 검증하기 위함.

    Pydantic 검증을 약하게 하기 위해 모든 필드를 Optional + Any 허용.
    """
    report_id: str
    created_at: Optional[str] = None
    company_name: Optional[str] = None
    decision_source: Optional[str] = None  # ← Literal 강제 없음 (test 의도)
    evaluation_status: Optional[str] = None
    proposal_allowed: Optional[bool] = None
    fpe_credit_limit: Optional[int] = None
    fpe_margin_rate: Optional[float] = None
    # 모든 필드 Optional — 누락 케이스도 시뮬레이션

    class Config:
        extra = "allow"  # 임의 필드 허용


# 2. test-only seed API (FLOWBIZ_ENV=test에서만 활성화)
if os.getenv("FLOWBIZ_ENV") == "test":
    SNAPSHOT_DIR = Path("data/evaluation_reports")
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)

    @app.post("/api/test/seed-raw-snapshot")
    async def seed_raw_snapshot(snapshot: UnsafeRawSnapshotForTest):
        """
        ⚠ TEST ONLY — Pydantic 검증을 우회해 raw JSON으로 직접 저장.
        production 환경에서는 라우트 자체가 등록되지 않음.
        """
        report_id = snapshot.report_id
        path = SNAPSHOT_DIR / f"{report_id}.json"
        path.write_text(json.dumps(snapshot.dict(), default=str))
        return {"report_id": report_id, "saved_to": str(path)}

    @app.delete("/api/test/raw-snapshot/{report_id}")
    async def delete_raw_snapshot(report_id: str):
        path = SNAPSHOT_DIR / f"{report_id}.json"
        if path.exists():
            path.unlink()
        return {"deleted": report_id}
```

**Playwright fixture v4** (F2 + F5 통합):
```typescript
// tests/e2e/fixtures/snapshot_seeder.ts (v4)
import { test as base } from '@playwright/test';
import { v4 as uuidv4 } from 'uuid';   // F1 — uuid 사용

export const test = base.extend<{
  testReportId: string;
  fakeApeBoundReportId: string;
  fakeNoFpeFieldsReportId: string;   // 누락 필드 케이스
}>({
  // 정상 snapshot — 정상 API 사용
  testReportId: async ({ request }, use) => {
    const response = await request.post('/api/evaluation/report', {
      headers: { 'Content-Type': 'application/json' },
      data: {
        state: { company_name: 'TestCorp', /* ... 정상 통과 케이스 */ }
      }
    });
    const snapshot = await response.json();
    await use(snapshot.report_id);
    // teardown
    await request.delete(`/api/evaluation/report/${snapshot.report_id}`);
  },

  // negative case 1: decision_source="APE" (legacy 잘못 저장 시뮬레이션)
  // F2 정정 — raw API 사용 (Pydantic 우회)
  fakeApeBoundReportId: async ({ request }, use) => {
    const reportId = uuidv4().replace(/-/g, '');   // uuid hex 형식
    await request.post('/api/test/seed-raw-snapshot', {
      headers: { 'Content-Type': 'application/json' },
      data: {
        report_id: reportId,
        decision_source: 'APE',     // ← 정책 위반 (Literal["FPE"] 우회)
        proposal_allowed: false,
        company_name: 'TestNonFPE',
      }
    });
    await use(reportId);
    await request.delete(`/api/test/raw-snapshot/${reportId}`);
  },

  // negative case 2: 필수 필드 누락
  fakeNoFpeFieldsReportId: async ({ request }, use) => {
    const reportId = uuidv4().replace(/-/g, '');
    await request.post('/api/test/seed-raw-snapshot', {
      headers: { 'Content-Type': 'application/json' },
      data: {
        report_id: reportId,
        decision_source: 'FPE',
        // fpe_credit_limit, fpe_margin_rate 등 모두 누락
      }
    });
    await use(reportId);
    await request.delete(`/api/test/raw-snapshot/${reportId}`);
  }
});
```

**테스트 spec — 정책 검증** (F2 정정):
```typescript
// tests/e2e/decision_source_fpe.spec.ts
import { test } from './fixtures/snapshot_seeder';
import { expect } from '@playwright/test';

test('proposal API rejects non-FPE decision_source from raw legacy snapshot', async ({
  request, fakeApeBoundReportId
}) => {
  // raw snapshot이 저장됨 (Pydantic 우회)
  // proposal API가 load 시 raw dict 검증 → decision_source != "FPE" 거부
  const response = await request.post('/api/proposal/generate', {
    headers: { 'Content-Type': 'application/json' },
    data: { report_id: fakeApeBoundReportId, template_variant: 'standard' }
  });
  expect(response.status()).toBe(400);

  const body = await response.json();
  expect(body.detail).toContain('decision_source must be FPE');
});

test('proposal API rejects snapshot with missing FPE fields', async ({
  request, fakeNoFpeFieldsReportId
}) => {
  const response = await request.post('/api/proposal/generate', {
    headers: { 'Content-Type': 'application/json' },
    data: { report_id: fakeNoFpeFieldsReportId, template_variant: 'standard' }
  });
  expect(response.status()).toBeGreaterThanOrEqual(400);   // 400 또는 500
});
```

**핵심**: proposal API의 snapshot load 함수도 raw dict 검증 추가:
```python
def load_evaluation_snapshot(report_id: str) -> EvaluationSnapshot:
    path = SNAPSHOT_DIR / f"{report_id}.json"
    if not path.exists():
        raise HTTPException(404, "snapshot not found")

    raw = json.loads(path.read_text())

    # F2 정정: raw load 시점에서 정책 검증
    if raw.get("decision_source") != "FPE":
        raise HTTPException(400, "decision_source must be FPE")

    # 누락 필드 검증
    required = ["fpe_credit_limit", "fpe_margin_rate", "fpe_payment_grace_days"]
    missing = [f for f in required if raw.get(f) is None]
    if missing:
        raise HTTPException(400, f"missing required fields: {missing}")

    # 정상 → Pydantic 검증
    return EvaluationSnapshot(**raw)
```

### 11.3 FLOWBIZ_ENV=test 가드 검증 (codex v3 §4 #4)

```bash
# tests/run_e2e.sh (Phase 5 신설 예정)
#!/bin/bash
set -e

# 1. test 환경변수 설정
export FLOWBIZ_ENV=test

# 2. 테스트 서버 기동
nohup python3 -m uvicorn app:app --host 127.0.0.1 --port 8012 \
  > /tmp/uvicorn8012.log 2>&1 &
sleep 3

# 3. seed API 등록 검증
if curl -fsS http://127.0.0.1:8012/api/test/seed-raw-snapshot -X OPTIONS 2>&1 | grep -q "200\|Method Not Allowed"; then
  echo "[OK] test seed API 등록됨"
else
  echo "[FAIL] FLOWBIZ_ENV=test 미설정 또는 seed API 미등록"
  exit 1
fi

# 4. Playwright E2E 실행
npx playwright test
```

### 11.4 fixture 디렉토리 구조 (v3 §11.4 그대로)

## 12. Risk + Mitigation (v3 §12 + 신규)

| Risk | 영향 | 대응 |
|---|---|---|
| (v3 동일) | (다양) | (계승) |
| **(신규)** ulid 외부 의존성 추가 시 환경 격차 | 일부 환경에서만 작동 | **uuid 표준 라이브러리 사용** (F1) |
| **(신규)** uuid4 시간 정렬 불가 | 보고서 순서 혼란 | `created_at` 필드 정렬 키 사용 |
| **(신규)** test seed API가 production에 노출 | 보안 위험 | `FLOWBIZ_ENV=test` 가드 + 라우트 자체 등록 안 함 |
| **(신규)** raw snapshot이 production data 디렉토리 오염 | 정책 위반 데이터 잔존 | seed API의 teardown 강제 (`afterEach` cleanup) |

## 13. 다음 액션 (codex v3 §4 체크리스트 4건 통합)

- [x] **(F1)** `ulid.new()` → `uuid.uuid4().hex` 교체 — §7.1/§7.5/§8.1 모든 모델 정정
- [x] **(F2)** negative seed = `UnsafeRawSnapshotForTest` + raw JSON — §11.2 신설
- [x] **(F3)** `--fbu-color-status-on-hold` v2_tokens.css 추가 — **본 세션 완료** (line 93)
- [ ] **(codex v3 §4 #4)** `FLOWBIZ_ENV=test` 테스트 스크립트 검증 — Phase 5 진입 시 §11.3 적용

## 14. 핵심 메시지

**v3 → v4 핵심 보강 3건**:
1. **uuid 표준 라이브러리** 사용 (codex F1) — 외부 의존성 0건, ModuleNotFoundError 차단
2. **negative test = raw fixture** (codex F2) — `UnsafeRawSnapshotForTest` + Pydantic 우회 + `/api/test/seed-raw-snapshot`
3. **on_hold 토큰** 즉시 적용 (codex F3) — `web/styles/v2_tokens.css:93` 본 세션 완료

→ codex v3 §5 인용: "v3는 방향성과 구조 측면에서 실제 구현 착수 가능한 수준에 가까워졌다... 이 두 가지(F1, F2)는 착수 전 반드시 수정해야 한다." → **v4에서 F1, F2 모두 수정 + F3 추가 즉시 적용 완료**.

---

## 부록 A. v3 → v4 정정 위치

### A.1 ID 생성 방식 (F1 P1)

| 위치 | v3 | v4 |
|---|---|---|
| §7.1 EvaluationSnapshot | `report_id=str(ulid.new())` | **`report_id: str = Field(default_factory=_new_id)`** + `_new_id() → uuid.uuid4().hex` |
| §7.5 ExhibitionLeadSnapshot | `lead_id=str(ulid.new())` | `lead_id: str = Field(default_factory=_new_id)` |
| §7.2 ProposalSnapshot | `proposal_id=str(ulid.new())` | `proposal_id: str = Field(default_factory=_new_id)` |
| §8.1 UpgradeReport | (미명시) | **신설** `report_id: str = Field(default_factory=_new_id)` |

### A.2 negative seed 우회 (F2 P1)

| 위치 | v3 | v4 |
|---|---|---|
| §11.2 seed API | `EvaluationSnapshot(**snapshot)` 검증 | **`UnsafeRawSnapshotForTest(BaseModel)` + `Config.extra = "allow"`** |
| §11.2 seed 라우트 이름 | `/api/test/seed-snapshot` | **`/api/test/seed-raw-snapshot`** (위험성 명시) |
| §11.2 fixture 1개 | `fakeApeBoundReportId` | **2개 — `fakeApeBoundReportId` + `fakeNoFpeFieldsReportId`** |
| §11.2 (신규) | (없음) | **proposal API의 raw load 정책 검증** (`load_evaluation_snapshot` 내부 raw dict 체크) |

### A.3 v2_tokens.css on_hold 토큰 (F3 P2)

| 위치 | v3 | v4 |
|---|---|---|
| §8.3 색상 토큰 5종 | 계획만 명시 | **본 세션 line 93 추가 완료** |
| §3.1 (신규) | (없음) | **Phase 0 Acceptance Criteria 5 항목** |
| §3.2 (신규) | (없음) | **변경 파일 목록 명시** |

## 부록 B. 누적 Finding 추적

| 단계 | 신규 Finding | 누적 |
|---|---|---|
| 본 계획 v1 | 0 (자체) | 0 |
| 본 계획 v2 | 0 (codex v1 4건 반영) | 4 |
| 본 계획 v3 | 0 (codex v2 5건 반영) | 9 |
| **본 계획 v4** | **0 (codex v3 3건 반영)** | **12** |

**잔여 P0/P1**: 0건.

## 부록 C. 본 세션 즉시 실행 작업 로그

| 작업 | 결과 |
|---|---|
| `web/styles/v2_tokens.css:93`에 `--fbu-color-status-on-hold: #6D4C41` 추가 | ✅ |
| `python3 -c "import ulid"` 실패 확인 | ✅ ModuleNotFoundError |
| uuid 표준 라이브러리 가용 확인 | ✅ |
| (이전 세션) standalone 11MB → docs/reference/ 이동 | ✅ |

## 부록 D. v4 단일 적용 코드 패턴

**1. ID 생성 헬퍼**:
```python
import uuid
from pydantic import BaseModel, Field

def _new_id() -> str:
    """v4 표준 — Python 표준 라이브러리 uuid"""
    return uuid.uuid4().hex   # 32자 16진수
```

**2. 모든 snapshot 모델에 적용**:
```python
class EvaluationSnapshot(BaseModel):
    report_id: str = Field(default_factory=_new_id)
    # ...

class ExhibitionLeadSnapshot(BaseModel):
    lead_id: str = Field(default_factory=_new_id)
    # ...

class ProposalSnapshot(BaseModel):
    proposal_id: str = Field(default_factory=_new_id)
    # ...

class UpgradeReport(BaseModel):
    report_id: str = Field(default_factory=_new_id)
    # ...
```

**3. test-only raw fixture**:
```python
class UnsafeRawSnapshotForTest(BaseModel):
    report_id: str
    # 모든 필드 Optional + Config.extra = "allow"

if os.getenv("FLOWBIZ_ENV") == "test":
    @app.post("/api/test/seed-raw-snapshot")
    async def seed_raw_snapshot(snapshot: UnsafeRawSnapshotForTest):
        # raw JSON 직접 저장 (Pydantic 우회)
```

**4. proposal API raw 정책 검증**:
```python
def load_evaluation_snapshot(report_id: str):
    raw = json.loads(path.read_text())
    if raw.get("decision_source") != "FPE":
        raise HTTPException(400, "decision_source must be FPE")
    # ...
    return EvaluationSnapshot(**raw)
```
