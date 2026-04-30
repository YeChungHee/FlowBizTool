# FlowBizTool v2 Standalone 디자인 구현 계획서 v2 [claude]

- 문서번호: FBU-PLAN-UI-V2-STANDALONE-IMPL-v2-20260430
- 작성일: 2026-04-30
- 작성자: [claude]
- 이전 버전: `[claude]flowbiz_ui_v2_standalone_design_implementation_plan_20260430.md` (v1)
- 검증: `[codex]flowbiz_ui_v2_standalone_design_implementation_plan_validation_20260430.md` (P1 3건 + P2 1건 — **조건부 보류**)
- 변경 사유: v1의 핵심 누락 4건 보강 — **전시회 참가기업 평가 Phase 신설** + **EvaluationSnapshot 서버 저장 API** + **월간 API 명칭 기존 계획과 일치 (upgrade-reports)** + **디자인 토큰 추출 rendered DOM 기준**

## 0. v1 → v2 변경 요약

| Finding | 우선순위 | v1 문제 | v2 반영 |
|---|---|---|---|
| F1 [codex] v1: 전시회 참가기업 평가 누락 | **P1** | 기존 `bizaipro_exhibition_wireframe.html`, `kcnc_simtos2026_sample.html` 있는데 v1에 미반영 | **§5 Phase 5 신설** "전시회 참가기업 평가" + **§4.8 신규 화면** `bizaipro_exhibition_evaluator.html` + 전시회 입력 필드 7항 고정 + 전시회 평가 → FPE → 콜드메일 흐름 |
| F2 [codex] v1: 평가보고서가 화면 표시 수준에 머묾 | **P1** | `EvaluationSnapshot`/`report_id`/서버 저장 API 누락 | **§7 신설** "EvaluationSnapshot 서버 저장 모델" + `POST /api/evaluation/report` + snapshot 11 필드 + 제안서/이메일 snapshot 기준 생성 |
| F3 [codex] v1: 월간 API 명칭 불일치 | **P1** | `/api/engine/upgrade/list` 사용 vs 기존 계획서의 `upgrade-reports` 계열 | **§8 신설** 월간 API 5종 정정 — `POST /monthly-upgrade-report` / `GET /upgrade-reports` / `GET /upgrade-reports/{id}` / `POST /upgrade-reports/{id}/decision` / `POST /promote-fpe` |
| F4 [codex] v1: 디자인 토큰 thumbnail 기준 | P2 | `#__bundler_thumbnail` SVG에서만 추출 → 실제 unpack 후 화면과 차이 가능 | **§3 보강** rendered DOM + computed style 비교 절차 + `outputs/reference/` 보관 검토 |

## 1. 핵심 운영 원칙 (codex 검증 §1 인용)

| 원칙 | 출처 |
|---|---|
| 평가엔진 = `FPE`, 학습엔진 = `APE` | flowbiz_dual_engine_evaluation_and_upgrade_lifecycle_plan §1 |
| 제안서·이메일 수치는 **항상 active FPE 기준 고정** | 3차 PR §3.3 #1 + codex 검증 §1 |
| APE는 비교/학습/고도화 후보 전용 | 3차 PR §3.3 #2-#3 |
| 상담보고서 + 미팅보고서 = **상담보고서 family** (전화/직접 subtype) | 3차 PR §3.3 #4 |
| 월간 엔진 관리 탭에서 평가엔진고도화보고서 다룸 | 3차 PR §3.3 #5 |
| AppleGothic Human Interface | 3차 PR §3.3 #6 |
| (신규) **전시회 참가기업 평가 흐름** 필수 포함 | codex 검증 F1 [P1] |
| (신규) **평가보고서 = 서버 snapshot** | codex 검증 F2 [P1] |
| (신규) **월간 API = upgrade-reports 계열로 통일** | codex 검증 F3 [P1] |

## 2. 원본 디자인 분석 (v1 §1 계승 + F4 보강)

### 2.1 파일 형식 — bundler standalone

(v1 §1.1 그대로 — 11 MB / 206 lines / base64 + gzip 임베드)

### 2.2 디자인 토큰 추출 절차 (F4 [codex] P2 — rendered DOM 기준 보강)

**v1 방식 (불충분)**: SVG thumbnail에서 색상/크기 추정.

**v2 방식 (보강)**:

```
1. standalone HTML을 outputs/reference/에 보관 (web/ 직접 노출 금지 검토)
2. headless Chrome으로 unpack 후 실제 DOM 렌더 (Playwright)
3. computed style 추출:
   - color, background-color, border-radius, font-size, line-height
   - padding/margin spacing, box-shadow
4. SVG thumbnail 토큰과 rendered DOM 토큰 비교
5. 차이 > 5% 시 rendered 값 우선
6. 최종 토큰을 web/styles/v2_tokens.css에 반영 (현재 v1 1차 추출 + Phase 1에서 검증)
```

**Phase 1 추가 작업**:

```javascript
// scripts/extract_v2_tokens_rendered.js (Phase 1 신설 예정)
const { chromium } = require('playwright');

async function extractTokens() {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto('file:///path/to/dual_engine_v2_standalone.html');
  await page.waitForFunction(() => !document.getElementById('__bundler_loading'));

  const tokens = await page.evaluate(() => {
    const computed = (sel, prop) => {
      const el = document.querySelector(sel);
      return el ? getComputedStyle(el).getPropertyValue(prop) : null;
    };
    return {
      bgPrimary: computed('body', 'background-color'),
      bgCard: computed('.kpi-card, [class*="card"]', 'background-color'),
      bgHeader: computed('header, [class*="header"]', 'background-color'),
      // ... 13 카테고리 모든 토큰
    };
  });

  await browser.close();
  return tokens;
}
```

→ Phase 1에서 thumbnail 토큰(이미 v2_tokens.css 반영) vs rendered DOM 토큰을 비교 후 정정.

### 2.3 standalone HTML 보관 위치 결정

| 옵션 | 경로 | 장단점 |
|---|---|---|
| A. `web/dual_engine_v2_standalone.html` | 현재 위치 (작업 1) | 즉시 시연 가능, **production route 노출 위험** |
| B. `outputs/reference/dual_engine_v2_standalone.html` | git outputs/ | git 추적 가능 + production route 분리 |
| C. `docs/reference/dual_engine_v2_standalone.html` | git docs/ | docs와 함께 관리 |

**v2 권장**: **B (`outputs/reference/`)** — codex 검증 F4 권고와 일치. Phase 1에서 web/에서 outputs/reference/로 이동.

## 3. 디자인 시스템 통합 (v1 §3 계승)

### 3.1 토큰 정의 (v1 §3.1 그대로)

`web/styles/v2_tokens.css` (작업 2 산출물 — 272 lines, 103 변수, 13 카테고리). Phase 1 rendered DOM 검증 후 미세 정정.

### 3.2 마이그레이션 규약 (v1 §3.2 그대로)

기존 `.bz-*` ↔ 신규 `.fbu-*` namespace 분리, 점진 전환.

## 4. 8 화면 + 엔진관리 탭 — v2 디자인 매핑 (v1 §4 + 신규 §4.8)

### 4.1-4.7 (v1 §4.1-§4.7 그대로 계승)

| 화면 | 역할 |
|---|---|
| `bizaipro_home.html` | 대시보드 (Hero + KPI + SourceQuality + 검색 + 테이블) |
| `bizaipro_evaluation_result.html` | 좌(FPE) / 우(APE) 듀얼 카드 + 비교표 |
| `bizaipro_proposal_generator.html` | FPE snapshot 기반 + 차단 배너 |
| `bizaipro_email_generator.html` | FPE snapshot 기반 + 차단 배너 |
| `bizaipro_engine_compare.html` | engine META 비교 (`learning_comparison` highlight) |
| `bizaipro_changelog.html` | FPE 승격 + APE 학습 + 월간 보고서 이력 |
| `bizaipro_engine_management.html` (신규) | 월간 보고서 pending/approved/promoted/rejected + promote 액션 |

### 4.8 (신규) `bizaipro_exhibition_evaluator.html` — 전시회 참가기업 평가 (F1 [codex] P1)

**기존 와이어프레임 참고**: `web/bizaipro_exhibition_wireframe.html`, `web/kcnc_simtos2026_sample.html` (Phase 1에서 legacy/로 이동, 본 화면이 후속 구현)

**입력 7 필드 (codex 검증 F1 권고)**:

```
1. 기업명          (필수)
2. 전시회명        (필수, 예: SIMTOS 2026)
3. 참가 연도        (필수)
4. 산업 / 품목      (필수)
5. 전시회정보 URL  (선택)
6. 홈페이지         (선택)
7. 담당자           (선택)
```

**평가 흐름 (codex 검증 §4 Phase 5)**:

```
[전시회 DB / URL 입력]
   ↓
[참가기업 추출 — 자동/수동]
   ↓
[홈페이지·품목·담당자 수집]
   ↓
[기업리포트 / FlowScore 연결 시도]
   ├─ 있음 → FPE 정식 평가 진행
   └─ 없음 → "전시회형 사전평가" 분리 (FPE 결과 없음)
   ↓
[FPE 평가 + APE 비교]
   ↓
[FPE 통과?]
   ├─ 통과 → 전시회형 제안서 + 콜드메일 생성
   └─ 차단 → 차단 배너 + 추가 심사 안내
```

### 4.8.1 와이어프레임

```
┌─[GLOBAL HEADER]──────────────────────────────────────────────────────────┐
└──────────────────────────────────────────────────────────────────────────┘
┌─[탭]──────────────────────────────────────────────────────────────────────┐
│  [DB 입력]  [참가기업 목록]  [평가 실행]  [전시회형 콜드메일]              │
└──────────────────────────────────────────────────────────────────────────┘
┌─[전시회 정보 입력]────────────────────────────────────────────────────────┐
│  전시회명         [SIMTOS 2026                              ]              │
│  참가 연도        [2026                                     ]              │
│  전시회정보 URL   [https://simtos.org/2026                   ]              │
│  [참가기업 추출 →]                                                         │
└──────────────────────────────────────────────────────────────────────────┘
┌─[참가기업 목록 — fbu-table]──────────────────────────────────────────────┐
│ ☐│ 기업명     │ 산업/품목     │ 홈페이지         │ 담당자  │ 보고서 연결 │
│ ☐│ ABC산업㈜ │ 공작기계       │ abc.co.kr        │ 김대표  │ ✓ 연결됨    │
│ ☐│ XYZ산업㈜ │ 절삭공구       │ xyz.co.kr        │ —       │ ⚠ 미연결    │
│ ☐│ ...                                                                   │
│  [선택 기업 평가 실행 →]                                                  │
└──────────────────────────────────────────────────────────────────────────┘
┌─[평가 결과 — 듀얼 카드 (4.2와 동일 구조)]──────────────────────────────┐
│  [FPE 카드]                  [APE 카드 — opacity 0.85]                  │
│  ● 양쪽 통과 / FPE 차단 등                                              │
└──────────────────────────────────────────────────────────────────────────┘
┌─[전시회형 콜드메일 (FPE 통과 시만)]──────────────────────────────────────┐
│  받는 사람     [purchasing@abc.co.kr]                                    │
│  제목         [[FlowPay] SIMTOS 2026 참가 ABC산업 — 거래 한도 안내]      │
│  본문          (전시회 정보 + FPE 기준 한도/마진/결제유예 자동 채움)     │
└──────────────────────────────────────────────────────────────────────────┘
```

### 4.8.2 §3.3 7항 적용

| 원칙 | 위치 |
|---|---|
| #1 FPE 고정 | 콜드메일 본문에 FPE 한도/마진/결제유예만 사용 |
| #2 APE 선택 불가 | 듀얼 카드에서 APE 표시만 (선택 액션 없음) |
| #3 APE 비교 전용 | 비교표 + 학습 후보 저장 |
| 전시회 정보는 **제안 메시지의 근거**로 사용, 한도/마진율은 **FPE 결과만** | codex 검증 §4 Phase 5 #5 직접 인용 |

## 5. 6 Phase 로드맵 (v1 5 Phase → v2 6 Phase, codex 권장 5 Phase 통합)

| Phase | 기간 | 산출물 | codex §4 매핑 |
|---|---|---|---|
| **Phase 0: 기준 정리** | 1주 (즉시) | 디자인 토큰(rendered DOM 검증) + standalone outputs/reference/ 이동 + bizaipro_shared.css 통합 | §4 Phase 0 |
| **Phase 1: 평가 실행 + Snapshot** | 2주 | EvaluationSnapshot 모델 + `POST /api/evaluation/report` + 결과 화면 snapshot 렌더링 | §4 Phase 1 |
| **Phase 2: 제안서/이메일 생성 (snapshot 기준)** | 1주 | proposal/email API가 evaluation snapshot 또는 proposal snapshot 사용 + FPE 차단 disabled | §4 Phase 2 |
| **Phase 3: 업데이트일지 + 엔진비교표** | 1주 | engine_compare + changelog (FPE 승격 / APE 학습 / 월간 보고서 ID 연결) | §4 Phase 3 |
| **Phase 4: 월간 엔진업데이트보고서** | 2주 | upgrade-reports 5 API + 매월 30일 13:00 KST 자동 + 관리자 promote | §4 Phase 4 |
| **Phase 5: 전시회 참가기업 평가** | 2주 | exhibition_evaluator + 7 필드 + 전시회형 콜드메일 + FPE 차단 분기 | §4 Phase 5 (신설) |
| **합계** | **9주** | | |

### 5.1 본 1차 PR과의 관계

| 본 1차 PR | v2 디자인 PR (본 계획) |
|---|---|
| 인프라 + API + helper (UI 변경 없음) | 8 화면 + 엔진관리 + EvaluationSnapshot + 전시회 평가 |
| `engine_purpose: learning_comparison` 라이브 | 화면 노출 + 비교 카드 시각화 |
| 회귀 0건 | 6 Phase 점진 마이그레이션으로 회귀 최소화 |

## 6. 우선순위 매트릭스 (v2 — 8 화면 + 4 신규 영역)

| 항목 | Phase 0 | Phase 1 | Phase 2 | Phase 3 | Phase 4 | Phase 5 |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| 디자인 토큰 (rendered DOM 검증) | ✅ | — | — | — | — | — |
| standalone outputs/reference/ 이동 | ✅ | — | — | — | — | — |
| EvaluationSnapshot 모델 | — | ✅ | — | — | — | — |
| `POST /api/evaluation/report` | — | ✅ | — | — | — | — |
| 8 화면 v2 디자인 적용 | — | ✅ | ✅ | ✅ | — | ✅ |
| FPE/APE 듀얼 카드 + 합의 배지 | — | ✅ | — | — | — | — |
| 제안서·이메일 snapshot 기반 | — | — | ✅ | — | — | — |
| FPE 차단 시 disabled | — | — | ✅ | — | — | ✅ |
| 엔진비교표 + changelog | — | — | — | ✅ | — | — |
| 월간 upgrade-reports 5 API | — | — | — | — | ✅ | — |
| 매월 30일 13:00 KST 자동 | — | — | — | — | ✅ | — |
| 관리자 promote 워크플로우 | — | — | — | — | ✅ | — |
| **전시회 참가기업 평가** | — | — | — | — | — | ✅ |
| **전시회형 콜드메일** | — | — | — | — | — | ✅ |
| 픽셀 검증 + a11y | — | — | — | — | — | ✅ (Phase 5 끝에 통합) |

## 7. EvaluationSnapshot 서버 저장 모델 (F2 [codex] P1 — 신설)

### 7.1 모델 정의

```python
# data models / api/evaluation/report 응답
class EvaluationSnapshot(BaseModel):
    report_id: str                  # ULID 또는 UUID
    created_at: datetime
    company_name: str
    state_key: str                  # bizaipro_shared.js의 stateKey
    server_input_hash: str          # SHA256 first 16 char (1차 PR 산출물)

    # 결정 근거
    decision_source: Literal["FPE"] = "FPE"   # 항상 FPE
    fpe_version: str                # "FPE_v.16.01"
    ape_version: str                # "APE_v1.01"

    # FPE 평가 결과 (제안서/이메일 기준)
    fpe_flow_score: int
    fpe_credit_limit: int           # 원 단위
    fpe_margin_rate: float          # 0.024
    fpe_payment_grace_days: int
    fpe_knockout_reasons: list[str]
    proposal_allowed: bool          # FPE 통과 여부
    blocked_reason: Optional[str]

    # APE 비교 결과 (참고만)
    ape_flow_score: int
    ape_credit_limit: int
    ape_margin_rate: float
    ape_diff_summary: dict          # FPE 대비 차이 요약

    # 합의
    consensus: Literal["both_go", "fpe_blocked", "ape_only_positive", "ape_blocked", "both_review"]

    # 입력 품질
    source_quality: dict            # {기업리포트, 상담_family, 심사보고서, 평가_반영_상태}
```

### 7.2 API 신설 명세

```python
# Phase 1 신설
@app.post("/api/evaluation/report")
async def create_evaluation_report(state: dict) -> EvaluationSnapshot:
    """
    1. /api/learning/evaluate/dual 내부 호출
    2. 응답을 EvaluationSnapshot으로 직렬화
    3. data/evaluation_reports/<report_id>.json에 저장
    4. report_id 반환
    """

@app.get("/api/evaluation/report/{report_id}")
async def get_evaluation_report(report_id: str) -> EvaluationSnapshot:
    """저장된 snapshot 조회 (제안서/이메일 화면이 호출)"""

@app.get("/api/evaluation/reports")
async def list_evaluation_reports(limit: int = 20) -> list[EvaluationSnapshot]:
    """홈 화면 최근 평가 테이블에서 호출"""
```

### 7.3 제안서/이메일 생성 — snapshot 기반 강제

```python
# 기존 /api/proposal/generate 변경 (또는 신규)
@app.post("/api/proposal/generate")
async def generate_proposal(report_id: str, **kwargs) -> ProposalSnapshot:
    snapshot = load_evaluation_snapshot(report_id)

    # decision_source 강제 검증
    if snapshot.decision_source != "FPE":
        raise HTTPException(400, "decision_source must be FPE")

    # FPE 차단 시 거부
    if not snapshot.proposal_allowed:
        raise HTTPException(403, f"FPE blocked: {snapshot.blocked_reason}")

    # 제안서는 FPE 값으로만 생성
    return ProposalSnapshot(
        report_id=report_id,
        proposal_id=str(ulid.new()),
        company_name=snapshot.company_name,
        credit_limit=snapshot.fpe_credit_limit,         # ← FPE만
        margin_rate=snapshot.fpe_margin_rate,           # ← FPE만
        payment_grace_days=snapshot.fpe_payment_grace_days,
        # APE 값은 절대 사용하지 않음 (E2E 테스트로 강제)
    )
```

### 7.4 화면 변경 (Phase 2)

| 화면 | snapshot 사용 |
|---|---|
| evaluation_result | URL `?report_id=...` 으로 진입, snapshot 렌더 |
| proposal_generator | URL `?report_id=...`, `POST /api/proposal/generate` 호출 시 snapshot 기준 |
| email_generator | `?report_id=...` 또는 `?proposal_id=...` |
| home | `/api/evaluation/reports` 응답으로 최근 평가 테이블 렌더 |

## 8. 월간 엔진업데이트보고서 API 정정 (F3 [codex] P1)

### 8.1 v1 → v2 API 명칭 매핑

| v1 잘못된 명칭 | v2 정정 (codex 권장 = 기존 월간 계획서 일치) |
|---|---|
| `GET /api/engine/upgrade/list` | **`GET /api/engine/upgrade-reports`** |
| (없음) | **`GET /api/engine/upgrade-reports/{report_id}`** |
| (관리자 액션 포함) | **`POST /api/engine/upgrade-reports/{report_id}/decision`** (approved/rejected/hold) |
| (자동 생성) | **`POST /api/engine/monthly-upgrade-report`** (매월 30일 13:00 KST) |
| (FPE 승격) | **`POST /api/engine/promote-fpe`** (관리자 승인 후 active FPE 갱신) |

### 8.2 상태값 4종 고정

| 상태 | 의미 | 컬러 |
|---|---|---|
| `pending` | 자동 생성 직후 — 관리자 검토 대기 | `--fbu-color-status-pending` (오렌지) |
| `approved` | 관리자 승인됨 — promote 대기 | `--fbu-color-status-approved` (블루) |
| `promoted` | FPE 다음 버전에 반영 완료 | `--fbu-color-status-promoted` (그린) |
| `rejected` | 관리자 반려 | `--fbu-color-status-rejected` (레드) |

### 8.3 engine_management 화면 갱신 (v1 §4.7 → v2 정정)

```
[pending: N]  → /api/engine/upgrade-reports?status=pending
[승인 액션]    → POST /api/engine/upgrade-reports/{id}/decision { decision: "approved" }
[반려 액션]    → POST /api/engine/upgrade-reports/{id}/decision { decision: "rejected" }
[promote]     → POST /api/engine/promote-fpe { report_id: ... }
```

### 8.4 changelog 화면 갱신 (v1 §4.6)

기존 v1: 단순 이력 표시.
v2 정정: **FPE 승격 이력의 `보고서 ID` 컬럼이 `upgrade-reports/{id}` 링크**.

```
| 일시       | 버전        | 승격 방식    | 보고서 ID    |
|------------|-------------|--------------|--------------|
| 04-30 13:00| FPE_v.16.01 | 관리자 승인  | UR-04-30 →  | ← 클릭 시 /api/engine/upgrade-reports/UR-04-30
```

## 9. 7항 원칙 매핑 (v1 §7 + v2 신규 항목)

| 원칙 | v2 디자인 매핑 |
|---|---|
| #1 FPE 고정 | snapshot.fpe_* 만 폼 바인딩 (서버 강제) |
| #2 APE 선택 불가 | proposal/email API가 ape_* 값 무시 (E2E 테스트로 강제) |
| #3 APE 비교 전용 | snapshot.ape_diff_summary 표시 |
| #4 상담 family | snapshot.source_quality.consultation_family |
| #5 엔진관리 | upgrade-reports 5 API + 4 상태 |
| #6 AppleGothic | --fbu-font-family |
| #7 SourceQuality | snapshot.source_quality 영역 |
| **(신규) #8 전시회 평가** | **exhibition_evaluator + 7 필드 + FPE 차단 분기** |
| **(신규) #9 snapshot 기준** | **모든 제안서/이메일이 report_id 진입 + decision_source=FPE 검증** |

## 10. 데이터 바인딩 — 본 1차 PR API + 신규 API 결합

### 10.1 EvaluationSnapshot 흐름

```javascript
// 평가결과 화면 진입
async function initEvaluationResultView() {
  const reportId = new URLSearchParams(location.search).get('report_id');

  let snapshot;
  if (reportId) {
    // 기존 snapshot 렌더 (Phase 1 산출물)
    snapshot = await fetch(`/api/evaluation/report/${reportId}`).then(r => r.json());
  } else {
    // 새 평가 실행 + snapshot 저장
    snapshot = await fetch('/api/evaluation/report', {
      method: 'POST',
      body: JSON.stringify(getCurrentState())
    }).then(r => r.json());

    // URL 갱신
    history.replaceState(null, '', `?report_id=${snapshot.report_id}`);
  }

  // 좌측 FPE 카드 (제안서/이메일 기준)
  document.querySelector('.fbu-kpi-display.is-fpe').textContent = snapshot.fpe_flow_score;

  // 우측 APE 카드 (비교 전용)
  document.querySelector('.fbu-kpi-display.is-ape').textContent = snapshot.ape_flow_score;

  // 합의 배지
  const badge = document.querySelector('.fbu-consensus-badge');
  badge.className = 'fbu-consensus-badge fbu-consensus-badge--' + snapshot.consensus.replace(/_/g, '-');
}
```

### 10.2 제안서 생성 — snapshot 기반 강제

```javascript
async function generateProposal(reportId) {
  // FPE 차단 시 클라이언트도 사전 차단 (UX), 서버도 강제 차단 (보안)
  const snapshot = await fetch(`/api/evaluation/report/${reportId}`).then(r => r.json());

  if (!snapshot.proposal_allowed) {
    showBlockedBanner(snapshot.blocked_reason);
    return;
  }

  // snapshot 기준 생성
  const proposal = await fetch('/api/proposal/generate', {
    method: 'POST',
    body: JSON.stringify({ report_id: reportId })
  }).then(r => r.json());

  // 폼에 FPE 값만 자동 채움
  document.querySelector('input[name="credit_limit"]').value = formatKRW(proposal.credit_limit);
  document.querySelector('input[name="margin_rate"]').value = (proposal.margin_rate * 100).toFixed(1) + '%';
  document.querySelector('input[name="payment_grace"]').value = proposal.payment_grace_days + '일';

  // ape_* 값이 폼 어디에도 들어가지 않음을 E2E 테스트로 검증 (Phase 2)
}
```

### 10.3 전시회 평가 흐름 (Phase 5)

```javascript
async function evaluateExhibitionCompany(exhibitionData, companyData) {
  // 1. 기업리포트/FlowScore 연결 시도
  const enrichment = await fetch('/api/exhibition/enrich-company', {
    method: 'POST',
    body: JSON.stringify(companyData)
  }).then(r => r.json());

  let snapshot;
  if (enrichment.has_full_report) {
    // 기존 평가 흐름 (FPE + APE)
    snapshot = await fetch('/api/evaluation/report', {
      method: 'POST',
      body: JSON.stringify({ ...companyData, ...enrichment })
    }).then(r => r.json());
  } else {
    // 전시회형 사전평가 (FPE 결과 없음 — 평가 보류)
    snapshot = {
      decision_source: "FPE",
      proposal_allowed: false,
      blocked_reason: "기업리포트 미연결 — 추가 자료 필요",
      ...
    };
  }

  return snapshot;
}

async function generateExhibitionColdEmail(snapshot, exhibitionData) {
  if (!snapshot.proposal_allowed) {
    showBlockedBanner(snapshot.blocked_reason);
    return;
  }

  // 콜드메일 본문 — 전시회 정보를 근거로 + FPE 한도/마진/결제유예만 사용
  const email = {
    subject: `[FlowPay] ${exhibitionData.exhibition_name} 참가 ${snapshot.company_name} — 거래 한도 안내`,
    body: `
      안녕하세요, ${snapshot.company_name} ${companyData.contact_name}님.

      ${exhibitionData.exhibition_name} 참가 기업 대상으로 FlowPay 평가 결과를 안내드립니다.

      • 거래 한도: ${formatKRW(snapshot.fpe_credit_limit)}      ← FPE 단독
      • 마진율: ${(snapshot.fpe_margin_rate * 100).toFixed(1)}%   ← FPE 단독
      • 결제유예: ${snapshot.fpe_payment_grace_days}일             ← FPE 단독
    `
  };
  // APE 값은 절대 사용 안 함
}
```

## 11. 검증 계획 (v1 §9 + 신규 E2E)

### 11.1 v1 §9.1-9.3 그대로 (Phase 1, 2-3, 4)

### 11.2 신규 E2E 테스트 (codex 검증 권고 #6, #7, #8)

```javascript
// tests/e2e/decision_source_fpe.spec.ts
test('proposal API rejects non-FPE decision_source', async ({ page }) => {
  const response = await page.request.post('/api/proposal/generate', {
    data: { report_id: 'fake-snapshot-with-ape-decision' }
  });
  expect(response.status()).toBe(400);
});

test('proposal form does NOT bind ape_* values', async ({ page }) => {
  await page.goto('/web/bizaipro_proposal_generator.html?report_id=R-001');

  const apeValueExposed = await page.evaluate(() => {
    const inputs = document.querySelectorAll('input, textarea');
    return Array.from(inputs).some(input =>
      input.value.includes(window.__test_ape_credit_limit) ||
      input.value.includes(window.__test_ape_margin_rate)
    );
  });
  expect(apeValueExposed).toBe(false);
});

test('exhibition evaluator blocks proposal when FPE knockout', async ({ page }) => {
  await page.goto('/web/bizaipro_exhibition_evaluator.html');

  // FPE 차단 케이스 입력 (CCC 등급)
  await page.fill('[name="company_name"]', 'TestCCC');
  await page.fill('[name="exhibition_name"]', 'SIMTOS 2026');
  await page.click('[data-action="evaluate"]');

  await expect(page.locator('.fbu-blocked-banner')).toBeVisible();
  await expect(page.locator('[data-action="generate-cold-email"]')).toBeDisabled();
});
```

### 11.3 디자인 토큰 rendered DOM 검증 (F4 [codex] P2)

```bash
# Phase 0 수행
node scripts/extract_v2_tokens_rendered.js \
  --input outputs/reference/dual_engine_v2_standalone.html \
  --output web/styles/v2_tokens_rendered.css

# diff
diff web/styles/v2_tokens.css web/styles/v2_tokens_rendered.css

# 차이 > 5% 시 v2_tokens.css 정정
```

## 12. Risk + Mitigation (v1 §10 + 신규)

| Risk | 영향 | 대응 |
|---|---|---|
| **(v1 동일)** AppleGothic Windows/Linux 미지원 | 폰트 깨짐 | font fallback 명시 |
| **(v1 동일)** 11MB git 비대화 | 저장소 부담 | outputs/reference/ 이동 (F4 권고) |
| **(v1 동일)** §3.3 #2 위반 | 정책 위반 | E2E 테스트 + lint rule |
| **(신규) snapshot 미저장 시 제안서 생성 시도** | 회귀 위험 | API 강제 검증 (Phase 2) |
| **(신규) 월간 API 명칭 혼선** | 클라이언트/서버 mismatch | v1 `/upgrade/list` 사용 금지, codebase 일괄 검색 후 정정 |
| **(신규) 전시회 평가 시 기업리포트 미연결** | 평가 미실행 → 사용자 혼란 | "전시회형 사전평가" 분리 + UI 안내 |
| **(신규) standalone 디자인 토큰과 rendered 차이** | UI 불일치 | Phase 0 rendered DOM 검증 |

## 13. 다음 액션 (codex §5 체크리스트 8건 통합)

- [ ] **(F1)** Phase 5 "전시회 참가기업 평가" 추가 — §5 6 Phase에 반영 완료
- [ ] **(F1)** `web/bizaipro_exhibition_evaluator.html` 신규 — §4.8 명세 완료
- [ ] **(F2)** `EvaluationSnapshot` + `report_id` 모델 — §7 정의 완료
- [ ] **(F2)** `POST /api/evaluation/report` 신설 — Phase 1
- [ ] **(F3)** 월간 API 명칭 정정 — §8 매핑표 완료 (`upgrade-reports` 계열)
- [ ] **(F4)** standalone 토큰 추출 rendered DOM 기준 — §2.2 절차 완료, Phase 0 실행
- [ ] **(테스트)** `decision_source=FPE` 검증 E2E — §11.2 spec
- [ ] **(테스트)** APE 값이 form input에 바인딩 안 됨 E2E — §11.2 spec
- [ ] **(테스트)** 전시회 평가 FPE 차단 E2E — §11.2 spec

## 14. 핵심 메시지

**v1 → v2 핵심 보강 4건**:
1. **전시회 참가기업 평가** Phase 5 신설 (codex F1)
2. **EvaluationSnapshot 서버 저장** 모델 + API 5종 (codex F2)
3. **월간 API 명칭** `upgrade-reports` 계열로 통일 (codex F3)
4. **디자인 토큰** rendered DOM 검증 절차 (codex F4)

이로써 v1의 "화면 표시 수준" 한계를 넘어 **평가→제안→이메일→고도화→전시회**까지 닫힌 운영 사이클로 전환.

> codex §6 인용: "위 세 가지가 보완되면 v2 standalone 디자인을 기준으로 학습, 평가, 제안, 이메일 생성, 고도화까지 이어지는 실제 운영 계획으로 전환 가능하다." → **v2에서 4건 모두 보완 완료**.

---

## 부록 A. v1 → v2 정정 위치

### A.1 신규 화면 (F1 P1)

| 파일 | v1 | v2 |
|---|---|---|
| `web/bizaipro_exhibition_evaluator.html` | (없음) | **§4.8 신규** — 7 필드 + 4 탭 + 전시회형 콜드메일 |
| `web/bizaipro_exhibition_wireframe.html` | legacy 이동 | legacy 보존 + 4.8 구현 시 참고 |
| `web/kcnc_simtos2026_sample.html` | legacy 이동 | legacy 보존 + 4.8 구현 시 참고 |

### A.2 신규 모델/API (F2 P1)

| 항목 | v1 | v2 |
|---|---|---|
| EvaluationSnapshot 모델 | (없음) | **§7.1 11+ 필드** |
| `POST /api/evaluation/report` | (없음) | **§7.2 신설** |
| `GET /api/evaluation/report/{id}` | (없음) | **§7.2 신설** |
| `GET /api/evaluation/reports` | (없음) | **§7.2 신설** |
| 제안서/이메일이 snapshot 기반 | 클라이언트 state | **§7.3 강제** |

### A.3 월간 API 명칭 정정 (F3 P1)

| v1 | v2 |
|---|---|
| `/api/engine/upgrade/list` | `GET /api/engine/upgrade-reports` |
| (없음) | `POST /api/engine/monthly-upgrade-report` |
| (없음) | `GET /api/engine/upgrade-reports/{id}` |
| (없음) | `POST /api/engine/upgrade-reports/{id}/decision` |
| (없음) | `POST /api/engine/promote-fpe` |
| 상태 (3종) | 상태 4종 (pending/approved/promoted/rejected) |

### A.4 디자인 토큰 추출 (F4 P2)

| 항목 | v1 | v2 |
|---|---|---|
| 추출 기준 | SVG thumbnail | **rendered DOM + computed style** |
| standalone 위치 | `web/dual_engine_v2_standalone.html` | **`outputs/reference/`로 이동 검토** (Phase 0) |
| 검증 절차 | (없음) | **§2.2 Playwright headless Chrome unpack + diff** |

## 부록 B. 누적 Finding 추적

| 단계 | 신규 Finding | 누적 |
|---|---|---|
| 본 계획 v1 | (자체 문제) | — |
| **본 계획 v2** | **0 (codex v1 검증 P1×3 + P2×1 4건 모두 반영)** | **4** |

**잔여 P0/P1**: 0건.

## 부록 C. 다른 계획서와의 관계

| 계획서 | 본 계획 v2와의 관계 |
|---|---|
| `[claude]flowbiz_dual_engine_pr_merge_activation_guide_v2_7_20260430.md` | **선행 조건** (1차 PR 머지) |
| `[claude]flowbiz_web_full_redesign_v2_plan_20260430.md` | **상위 6 Phase 로드맵** — 본 계획 v2의 Phase 1-3 직결 |
| `[claude]flowbiz_web_v2_wireframe_review_7_screens_20260430.md` | **8 화면 와이어프레임** (v2에서 #8 exhibition_evaluator 추가 필요) |
| `flowbiz_dual_engine_evaluation_and_upgrade_lifecycle_plan_20260430.md` | **EvaluationSnapshot + UpgradeReport 데이터 모델 출처** |
| `flowbiz_monthly_evaluation_engine_upgrade_plan_20260430.md` | **월간 API 명칭 출처** (F3 P1 정정 기준) |
| `flowbiztool_v2_standalone_based_production_plan_20260430.md` | v2 production 청사진 |
| `flowbiz_dual_engine_ui_sample_validation_direction_20260430.md` | §3.3 7항 원칙 (v2에서 #8 #9 추가) |

## 부록 D. 9 화면 매트릭스 (v1 7+1=8 → v2 8+1=9)

| # | 화면 | v1 | v2 |
|---|---|---|---|
| 1 | bizaipro_home.html | ✅ | ✅ (snapshot reports 테이블) |
| 2 | bizaipro_evaluation_result.html | ✅ | ✅ (URL `?report_id=...`) |
| 3 | bizaipro_proposal_generator.html | ✅ | ✅ (snapshot 기반) |
| 4 | bizaipro_email_generator.html | ✅ | ✅ (snapshot 기반) |
| 5 | bizaipro_engine_compare.html | ✅ | ✅ (변경 없음) |
| 6 | bizaipro_changelog.html | ✅ | ✅ (보고서 ID 링크) |
| 7 | bizaipro_engine_management.html | ✅ | ✅ (upgrade-reports 5 API) |
| **8 (신규)** | **bizaipro_exhibition_evaluator.html** | — | **✅** (전시회 7 필드 + 콜드메일) |

→ **v2 = 8 화면**. (참고: 본 계획 v1에서는 7 화면이었으나, 본 계획 v2에서 1 추가)

## 부록 E. 향후 와이어프레임 검토 후속 작업

본 v2는 codex 검증 4건 보강 + Phase 5 + EvaluationSnapshot에 집중. 다음 후속 검토 필요:

1. `bizaipro_exhibition_evaluator.html` 와이어프레임 상세 (본 §4.8 미니 버전 → 전체 ASCII 도식)
2. `EvaluationSnapshot` JSON 스키마 + 샘플 데이터 (Phase 1 진입 전 백엔드 모델 확정)
3. 월간 upgrade-reports 5 API의 OpenAPI 스펙 (Phase 4 진입 전)
4. E2E 테스트 시나리오 상세 (`tests/e2e/*.spec.ts` 초안)

→ Phase 1 진입 전 별도 문서로 작성 필요.
