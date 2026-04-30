/**
 * v2.11 §2.1 Step 11: Dual evaluation helpers
 *
 * Classic script + IIFE — bizaipro_shared.js를 로드하는 모든 HTML에서 그것보다 먼저 로드.
 * 브라우저: window.FlowBizDualEvalHelpers / Node: module.exports (테스트용).
 */
(function () {
  function _stableInputSignature(payload) {
    if (!payload) return {};
    return {
      // 식별자 + 평가 핵심 입력 — v2.7 백엔드 build_learning_evaluation_payload 입력 정합
      creditGrade:
           payload.reportCreditGrade
        || payload.financialFilterSignal
        || (payload.screening && payload.screening.credit_grade)
        || "",
      annualSales:
           payload.recentRevenueValue
        || (payload.financials && payload.financials.annual_sales)
        || "",
      operatingProfit: payload.operatingProfitValue || "",
      netIncome: payload.netIncomeValue || "",
      requestedAmount:
           payload.requestedPurchaseAmount
        || payload.requested_purchase_amount_krw
        || "",
      requestedTenor:
           payload.requestedTenorDays
        || payload.requested_tenor_days
        || payload.requestedTenorMonths
        || payload.requested_tenor_months
        || "",
      creditEnhancement: payload.creditEnhancement || payload.credit_enhancement || "",
      cleanTransactions: payload.cleanTransactionCount || payload.clean_transaction_count || "",
      supplierName: payload.supplierName || "",
      buyerName: payload.buyerName || "",
      consultationDigest: payload.consultingValidationSummary ? "Y" : "",
      meetingDigest: payload.meetingValidationSummary ? "Y" : "",
      internalReviewDigest: payload.internalReviewValidationSummary ? "Y" : "",
    };
  }

  function _hashInputSignature(sig) {
    return JSON.stringify(sig);
  }

  function _stateKeyFromAnyPayload(payload) {
    if (!payload) {
      return { companyName: "", businessNumber: "", flowScoreFileName: "", inputHash: "" };
    }
    return {
      companyName:
           payload.companyName
        || payload.company_name
        || (payload.applicant && payload.applicant.company_name)
        || "",
      businessNumber:
           payload.businessNumber
        || payload.business_number
        || (payload.applicant && payload.applicant.business_number)
        || "",
      flowScoreFileName:
           payload.learningFlowScoreFileName
        || payload.flowScoreFileName
        || payload.flow_score_file_name
        || "",
      inputHash: _hashInputSignature(_stableInputSignature(payload)),
    };
  }

  function _stateKeyEqual(a, b) {
    if (!a || !b) return false;
    return a.companyName === b.companyName
        && a.businessNumber === b.businessNumber
        && a.flowScoreFileName === b.flowScoreFileName
        && a.inputHash === b.inputHash;
  }

  function _stateKeyReady(key) {
    // 모든 식별자가 빈 값이면 invalid. 최소 하나라도 있어야 valid.
    return !!(key && (key.companyName || key.businessNumber || key.flowScoreFileName));
  }

  const CONSENSUS_LABELS = {
    both_go: { color: "green", text: "✓ 양쪽 추천 · 신뢰도 ↑" },
    fpe_blocked: { color: "red", text: "✗ 심사 차단 · 거래 보류" },
    ape_only_positive: { color: "blue", text: "ⓘ 학습엔진 적극 제안 · 심사는 정규 경로" },
    ape_blocked: { color: "amber", text: "⚠ 학습엔진 비추천 · 영업담당자 검토" },
    both_review: { color: "gray", text: "REVIEW · 자료 보완 필요" },
  };

  const api = {
    _stableInputSignature,
    _hashInputSignature,
    _stateKeyFromAnyPayload,
    _stateKeyEqual,
    _stateKeyReady,
    CONSENSUS_LABELS,
  };

  if (typeof window !== "undefined") {
    window.FlowBizDualEvalHelpers = api;
  }
  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
})();
