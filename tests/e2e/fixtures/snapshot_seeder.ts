/**
 * Playwright fixture — EvaluationSnapshot seed
 *
 * 문서번호: FBU-PLAN-UI-V2-STANDALONE-IMPL-v7 §11.2
 * 작성자:   [claude]
 * 출처:     [claude]flowbiz_ui_v2_standalone_design_implementation_plan_v7_20260430.md
 *
 * 누적 반영 codex Findings:
 *   v3 F1 P1: BaseModel + Content-Type 헤더
 *   v4 F2 P1: UnsafeRawSnapshotForTest (Pydantic 우회)
 *   v5 F1 P1: node:crypto.randomUUID() (uuid npm 의존성 제거)
 *   v5 F4 P2: test 디렉토리 격리
 *   v7 F1 P2: readiness retry loop (run_e2e.sh)
 *
 * 핵심:
 *  - 정상 fixture: /api/evaluation/report 정식 API 사용 (Pydantic 검증 통과)
 *  - negative fixture: /api/test/seed-raw-snapshot raw 저장 (Pydantic 우회)
 *  - 모든 fixture는 afterEach teardown으로 자동 정리
 *  - ID 생성: node:crypto.randomUUID() (외부 npm 의존성 0)
 */
import { test as base, expect } from '@playwright/test';
import { randomUUID } from 'node:crypto';

/**
 * v5 [codex] F1 P1 정정 — Node 표준 라이브러리 사용
 * Python의 uuid.uuid4().hex와 동일한 32자 16진수 형식
 */
function newTestId(): string {
  return randomUUID().replace(/-/g, '');
}

type Fixtures = {
  /** 정상 통과 케이스 — both_go */
  testReportId: string;
  /** decision_source="APE" 비정상 (legacy 잘못 저장 시뮬레이션) */
  fakeApeBoundReportId: string;
  /** FPE 필수 필드 누락 */
  fakeNoFpeFieldsReportId: string;
};

export const test = base.extend<Fixtures>({
  /**
   * 정상 snapshot — 정식 API 경로
   * 평가 통과 케이스로 EvaluationSnapshot 생성
   */
  testReportId: async ({ request }, use) => {
    const response = await request.post('/api/evaluation/report', {
      headers: { 'Content-Type': 'application/json' },
      data: {
        state: {
          company_name: 'TestCorp',
          industry_profile: { code: 'C29', label: '기계' },
          financial_filter_signal: 'pass',
          // ... Phase 1+에서 정상 통과 케이스 state 확장
        }
      }
    });
    expect(response.status()).toBe(200);
    const snapshot = await response.json();
    const reportId: string = snapshot.report_id;

    await use(reportId);

    // teardown — production API의 DELETE 사용
    await request.delete(`/api/evaluation/report/${reportId}`).catch(() => {
      // teardown 실패는 silent (cleanup는 run_e2e.sh가 디렉토리째 정리)
    });
  },

  /**
   * negative case 1 — decision_source="APE" 비정상
   * F2 [codex] v3 P1 정정: Pydantic 검증 우회 (raw seed)
   */
  fakeApeBoundReportId: async ({ request }, use) => {
    const reportId = newTestId();   // F1 [codex] v5 — node:crypto

    const response = await request.post('/api/test/seed-raw-snapshot', {
      headers: { 'Content-Type': 'application/json' },
      data: {
        report_id: reportId,
        decision_source: 'APE',     // ← 정책 위반 (Literal["FPE"] 우회)
        evaluation_status: 'evaluated',
        proposal_allowed: false,
        company_name: 'TestNonFPE',
      }
    });
    expect(response.status()).toBe(200);

    await use(reportId);

    await request.delete(`/api/test/raw-snapshot/${reportId}`).catch(() => {});
  },

  /**
   * negative case 2 — FPE 필수 필드 누락
   * F3 [codex] v4 P2 + F4 [codex] v5 P2: 400/422 고정 검증용
   */
  fakeNoFpeFieldsReportId: async ({ request }, use) => {
    const reportId = newTestId();

    const response = await request.post('/api/test/seed-raw-snapshot', {
      headers: { 'Content-Type': 'application/json' },
      data: {
        report_id: reportId,
        decision_source: 'FPE',
        evaluation_status: 'evaluated',
        // fpe_credit_limit, fpe_margin_rate, fpe_payment_grace_days 모두 누락
        company_name: 'TestNoFpeFields',
      }
    });
    expect(response.status()).toBe(200);

    await use(reportId);

    await request.delete(`/api/test/raw-snapshot/${reportId}`).catch(() => {});
  },
});

export { expect } from '@playwright/test';
