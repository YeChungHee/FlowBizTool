/**
 * E2E — decision_source=FPE 정책 검증
 *
 * 문서번호: FBU-PLAN-UI-V2-STANDALONE-IMPL-v7 §11.2
 * 작성자:   [claude]
 *
 * 검증 대상 정책 (3차 PR §3.3 #1-#2):
 *  - 제안서/이메일 기준값은 항상 active FPE 결과로 고정
 *  - APE 결과/합의 평균은 제안서/이메일 기준값으로 선택 불가
 *  - decision_source != "FPE"인 snapshot은 proposal API에서 거부
 *
 * 누적 반영 codex Findings:
 *   v3 F1 P1: Content-Type 헤더 + body model
 *   v4 F2 P1: raw fixture (Pydantic 우회)
 *   v5 F4 P2: test 디렉토리 격리
 *   v6 F4 P2: 400/422 고정 (500 명시적 실패)
 *
 * 주의:
 *  본 spec은 Phase 1+ 단계에서 /api/proposal/generate 신설 후 작동.
 *  현 시점(1차 PR 머지 전)에는 backend API 미구현이므로 실행 시 fail 예상.
 *  Phase 0에서는 fixture/spec 파일 작성 자체가 산출물.
 */
import { test, expect } from './fixtures/snapshot_seeder';

test.describe('decision_source=FPE 정책 검증', () => {

  test('proposal API rejects non-FPE decision_source from raw legacy snapshot', async ({
    request, fakeApeBoundReportId
  }) => {
    // raw snapshot이 저장됨 (Pydantic 검증 우회 — UnsafeRawSnapshotForTest)
    // proposal API가 load 시점에서 raw dict 검증 → decision_source != "FPE" 거부
    const response = await request.post('/api/proposal/generate', {
      headers: { 'Content-Type': 'application/json' },
      data: {
        report_id: fakeApeBoundReportId,
        template_variant: 'standard'
      }
    });

    // F4 [codex] v6 P2 정정: 400/422 고정 (정책 오류 또는 body validation)
    expect([400, 422]).toContain(response.status());

    const body = await response.json();
    expect(body.detail).toContain('decision_source must be FPE');
  });

  test('proposal API rejects snapshot with missing FPE fields with 400/422', async ({
    request, fakeNoFpeFieldsReportId
  }) => {
    const response = await request.post('/api/proposal/generate', {
      headers: { 'Content-Type': 'application/json' },
      data: {
        report_id: fakeNoFpeFieldsReportId,
        template_variant: 'standard'
      }
    });

    // F3 [codex] v4 P2 + F4 [codex] v6 P2: 400/422 만 허용, 500은 명시적 실패
    expect([400, 422]).toContain(response.status());

    const body = await response.json();
    expect(body.detail).toContain('missing required fields');
  });

  test('proposal API succeeds with valid FPE snapshot', async ({
    request, testReportId
  }) => {
    const response = await request.post('/api/proposal/generate', {
      headers: { 'Content-Type': 'application/json' },
      data: {
        report_id: testReportId,
        template_variant: 'standard'
      }
    });

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body.proposal_id).toBeTruthy();
    expect(body.report_id).toBe(testReportId);
    // §3.3 #1-#2: 모든 수치가 FPE 단독 기준
    expect(body).toHaveProperty('credit_limit');
    expect(body).toHaveProperty('margin_rate');
    expect(body).toHaveProperty('payment_grace_days');
    // APE 값은 절대 포함되지 않음
    expect(body).not.toHaveProperty('ape_credit_limit');
    expect(body).not.toHaveProperty('ape_margin_rate');
  });
});

test.describe('proposal form 바인딩 검증 (§3.3 #1-#2)', () => {

  test('proposal form does NOT bind ape_* values', async ({
    page, testReportId, request
  }) => {
    // snapshot 응답 가져오기 (테스트 baseline)
    const snapshotResponse = await request.get(`/api/evaluation/report/${testReportId}`);
    const snapshot = await snapshotResponse.json();

    // proposal_generator 화면 진입
    await page.goto(`/web/bizaipro_proposal_generator.html?report_id=${testReportId}`);

    // 모든 input/textarea 값 수집
    const formValues = await page.evaluate(() => {
      const inputs = document.querySelectorAll('input, textarea');
      return Array.from(inputs).map(el => ({
        name: (el as HTMLInputElement).name,
        value: (el as HTMLInputElement).value
      }));
    });

    // FPE 값은 폼에 들어가야 함
    const fpeBound = formValues.some(v =>
      v.value.includes(String(snapshot.fpe_credit_limit))
    );
    expect(fpeBound).toBe(true);

    // APE 값은 폼에 들어가면 안 됨 (§3.3 #1-#2)
    const apeCreditLimitBound = formValues.some(v =>
      v.value.includes(String(snapshot.ape_credit_limit))
    );
    expect(apeCreditLimitBound).toBe(false);
  });
});
