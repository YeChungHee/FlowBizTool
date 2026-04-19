const BIZAIPRO_STORAGE_KEY = "bizaipro.currentState.v2";

const BIZAIPRO_DEFAULT_STATE = {
  mode: "exhibition",
  engineVersion: "최신 엔진 v.1.16.01",
  companyName: "케이씨엔씨(주)",
  shortName: "KCNC",
  representativeName: "김형주",
  businessNumber: "755-88-02028",
  exhibitionName: "SIMTOS 2026",
  exhibitionYear: 2026,
  exhibitionInfoUrl: "https://simtos.org/eng/bizmatching/exhibitor_Company_detail.do?bidx=719",
  website: "https://kcnc.co.kr",
  industryItem: "제조장비용 CNC 제어시스템 / TENUX / 스마트 제어시스템",
  companyOverview:
    "KCNC는 CNC 제어기, 구동계, TORUS 플랫폼을 소개하는 제조장비 제어시스템 기업으로 읽히며, 전시회 이후 수주 확대 타이밍에 조달 자금 연결 제안이 가능한 유형입니다.",
  recentRevenueLabel: "2024년 매출액",
  recentRevenueValue: "확인 필요",
  operatingProfitLabel: "2024년 영업이익",
  operatingProfitValue: "-563,240천원",
  netIncomeLabel: "2024년 당기순이익",
  netIncomeValue: "-423,427천원",
  estimatedLimitLabel: "예상 한도",
  estimatedLimitValue: "5천만~1억원",
  estimatedMarginLabel: "예상 마진율",
  estimatedMarginValue: "약 6%대",
  requestedTenorDays: 60,
  requestedTenorMonths: 2,
  proposalPriority: "중상",
  financialFilterSignal: "BB+",
  cashflowSignal: "보수적 접근",
  nextAction: "자료 확인 후<br />제안서 발송",
  heroNextAction: "제안서 발송 후 15분 미팅 제안",
  currentProposalState: "추가 확인 필요",
  recommendedTenorText: "1~2개월 우선 검토",
  recentRevenueYear: 2024,
  operatingProfitYear: 2024,
  learningEligible: "학습 적격",
  learningWeight: "0.85",
  learningCount: "10 / 10",
  updateStatus: "생성됨",
  consultingSummary: "",
  consultingCrossChecks: [],
  consultingIssues: [],
  consultingValidationSummary: "",
  internalReviewSummary: "",
  internalReviewCrossChecks: [],
  internalReviewIssues: [],
  internalReviewValidationSummary: "",
  supportingDocumentSummary: "",
  supportingDocumentCrossChecks: [],
  supportingDocumentIssues: [],
  additionalInfoSummary: "",
  additionalInfoIssues: [],
  supplierName: "",
  buyerName: "",
  overviewSummary:
    "KCNC 홈페이지, SIMTOS 2026 참가사 정보, 플로우스코어 리포트 공개 내용을 기준으로 `재무는 제공 가능 여부를 거르는 필터`, `비재무는 제안 메시지를 만드는 근거`라는 원칙에 맞춰 정리한 결과입니다.",
  websiteSummary:
    "KCNC는 제조장비용 제어시스템 TENUX, 구동계, TORUS 플랫폼을 소개하고 있으며, 제조장비 제어시스템 글로벌 리더를 지향한다고 밝히고 있습니다.",
  exhibitionSummary:
    "SIMTOS 참가사 페이지에는 Development/Service 기업으로 표시되며, 주요 고객사로 SMEC, 위아공작기계, 화천기공, DN솔루션즈, CSCAM, 대성하이텍이 기재되어 있습니다.",
  financialSummary:
    "공개 리포트 기준 기업 신용등급은 BB+, 현금흐름 등급은 불량으로 확인되며, 2024년 영업손실과 순손실이 기재되어 있습니다. 이 정보는 우선 플로우페이 제공 기준에 미달하는지를 가르는 재무 필터 역할로 사용합니다.",
  whyNow:
    "전시회 참가 시점은 데모, 파일럿, 공급 논의가 늘어나는 시기라 부품 조달과 외주 가공 자금 공백을 먼저 연결하는 제안이 자연스럽습니다.",
  useCase:
    "제어 모듈, 드라이브 부품, 외주 가공비, 시제품·초기 공급 물량을 대상으로 단기 선매입 구조를 제안할 수 있습니다.",
  checks: [
    "최근 발주서 또는 공급계약 유무",
    "주요 매입처와 주요 고객사 결제 조건",
    "외주 가공 및 부품 매입의 실제 회전 주기",
  ],
  proposal: {
    executive:
      "KCNC는 SIMTOS 2026 참가를 통해 시장 접점을 넓히고 있는 제조장비 제어시스템 기업으로 해석됩니다. 공개 정보 기준으로는 제어기, 구동계, 데이터 플랫폼을 모두 다루는 구조여서 부품 조달과 외주 가공, 선행 제작 물량에 대한 자금 연결 수요가 발생할 가능성이 있습니다.",
    company:
      "KCNC 홈페이지는 TENUX 제어기, 구동계, TORUS 플랫폼을 중심으로 기술 포트폴리오를 설명하고 있으며, SIMTOS 참가사 정보에는 2022년 설립, 20~49명 규모, Development/Service 기업으로 표시되어 있습니다.",
    exhibition:
      "SIMTOS는 대한민국 최대 생산제조기술 전시회로 소개되고 있으며, KCNC는 해당 공식 참가사 상세 페이지에 등록된 기업입니다.",
    opportunity:
      "FlowPay는 대출이 아니라 필요한 매입 시점의 공급대금을 먼저 연결하는 방식으로 제안할 수 있습니다. KCNC의 경우 핵심 부품, 제어 모듈, 외주 가공비, 초기 공급 물량을 대상으로 단기 선매입 구조를 먼저 검토하는 접근이 적절합니다.",
    structure:
      "실거래 자료 확인 전 단계에서는 5천만~1억원 수준의 파일럿 범위를 가설로 제시하고, 1~2개월 회전형 구조를 먼저 검토하는 것이 무리가 적습니다.",
    risks:
      "플로우스코어 리포트 공개 내용상 BB+와 현금흐름 등급 불량, 2024년 영업손실·순손실이 확인되어 재무 필터를 보수적으로 적용할 필요가 있습니다.",
    next:
      "첫 단계에서는 전시회 참가 맥락을 활용한 소개 메일을 발송하고, 회신이 오면 최근 거래 자료를 받아 맞춤 구조 제안서로 전환하는 것이 좋습니다.",
  },
  email: {
    subject: "케이씨엔씨(주)의 매출성장 타이밍을 지키는 방법",
    bodyLines: [
      "케이씨엔씨(주) 김형주 대표님 귀중,",
      "",
      "안녕하세요. 276홀딩스 FlowPay 영업이사 예충희입니다.",
      "",
      "SIMTOS 2026 참여부스를 통해 알게된 'KCNC'의 비지니스에 대한 열정을 보고 연락드립니다.",
      "KCNC가 소개하고 있는 TENUX 제어기, 구동계, TORUS 플랫폼과 같은 제조장비용 핵심 모듈 사업은 부품 조달과 외주 가공, 초기 공급 준비가 먼저 나가고 매출 회수는 뒤따르는 경우가 많아 운영자금 공백이 생기기 쉬운 구조라고 봤습니다.",
      "",
      "FlowPay는 대출이 아니라 필요한 매입 시점에 공급대금을 먼저 연결해 생산과 납품 일정을 지키도록 돕는 구조입니다. KCNC의 경우에도 핵심 부품, 외주 가공, 초기 공급 물량을 대상으로 1~2개월 회전형 구조가 맞는지 먼저 검토해볼 수 있다고 판단했습니다.",
      "",
      "괜찮으시다면 15분 정도 통화로 KCNC에 맞는 활용 가능성을 짧게 공유드리고 싶습니다.",
      "",
      "감사합니다.",
      "예충희 드림",
      "영업이사 / 010-4815-1411",
    ],
  },
};

const BIZAIPRO_ENGINE_PRESETS = {
  latest: {
    key: "latest",
    label: "최신 엔진 v.1.16.01",
    engineVersion: "v.1.16.01",
    proposalPriority: "중상",
    currentProposalState: "추가 확인 필요",
    heroNextAction: "제안서 발송 후 15분 미팅 제안",
    nextAction: "자료 확인 후<br />제안서 발송",
    recommendedTenorText: "1~2개월 우선 검토",
    requestedTenorMonths: 2,
    requestedTenorDays: 60,
    financialFilterSignal: "BB+",
    cashflowSignal: "보수적 접근",
    estimatedLimitValue: "5천만~1억원",
    estimatedMarginValue: "약 6%대",
    updateStatus: "생성됨",
    learningWeight: "0.85",
    changeNotes: [
      "재무 필터는 BB+를 유지하되, 전시회/홈페이지 기반 메시지 설계를 더 강화했습니다.",
      "추천 첫 액션을 '제안서 발송 후 15분 미팅 제안'으로 구체화했습니다.",
      "결제유예기간은 60일 기준 1~2개월 우선 검토로 고정했습니다.",
    ],
  },
  previous: {
    key: "previous",
    label: "업데이트 전 엔진 v.1.0.00",
    engineVersion: "v.1.0.00",
    proposalPriority: "중",
    currentProposalState: "추가 확인 필요",
    heroNextAction: "기본 소개 메일 우선 발송",
    nextAction: "기본 소개 메일<br />우선 발송",
    recommendedTenorText: "1개월부터 확인",
    requestedTenorMonths: 1,
    requestedTenorDays: 30,
    financialFilterSignal: "BB",
    cashflowSignal: "주의 필요",
    estimatedLimitValue: "보수 검토",
    estimatedMarginValue: "협의 필요",
    updateStatus: "이전 기준",
    learningWeight: "0.70",
    changeNotes: [
      "재무 기준을 더 보수적으로 해석했습니다.",
      "제안서보다 소개 메일 우선 접근을 권장했습니다.",
      "결제유예기간도 30일 수준에서 먼저 탐색하도록 안내했습니다.",
    ],
  },
  base: {
    key: "base",
    label: "기본 KCNC 샘플",
    engineVersion: "base",
    proposalPriority: "중상",
    currentProposalState: "샘플 기준",
    heroNextAction: "샘플 문구 확인",
    nextAction: "샘플 구조<br />검토",
    recommendedTenorText: "1~2개월 참고",
    requestedTenorMonths: 2,
    requestedTenorDays: 60,
    financialFilterSignal: "BB+",
    cashflowSignal: "보수적 접근",
    estimatedLimitValue: "5천만~1억원",
    estimatedMarginValue: "약 6%대",
    updateStatus: "샘플",
    learningWeight: "0.00",
    changeNotes: [
      "샘플 기본값입니다.",
    ],
  },
};

const BIZAIPRO_EMAIL_TEMPLATES = [
  { key: "growth-hormone", titleTemplate: "기업에도 ‘매출성장호르몬’이 필요합니다" },
  { key: "growth-timing", titleTemplate: "매출성장 타이밍을 지키는 방법" },
  { key: "material-burden", titleTemplate: "원자재 매입 부담, FlowPay로 완화할 수 있습니다" },
  { key: "gap-bridge", titleTemplate: "생산 확대와 매출 회수 사이의 공백을 메워드립니다" },
  { key: "tailored-supply", titleTemplate: "맞춤 원자재 선공급 구조를 제안드립니다" },
  { key: "alt-working-capital", titleTemplate: "대출이 아닌 운영자금 대안, FlowPay를 소개드립니다" },
];

const BIZAIPRO_SALESPEOPLE = [
  { name: "예충희", title: "영업이사", phone: "010-4815-1411" },
  { name: "박진용", title: "전략이사", phone: "010-9600-1630" },
];

const BIZAIPRO_DEFAULT_DASHBOARD = {
  engine_name: "BizAiPro",
  current_version: "v.1.16.01",
  learning_cards: {
    company_reports: 0,
    consultation_reports: 0,
    internal_reviews: 0,
  },
  engine_traits: [
    "전시회 URL과 기업 웹주소 URL을 함께 읽어 핵심 정보를 자동 추출합니다.",
    "재무는 제공 가능 여부를 거르는 필터로, 비재무는 제안 메시지 근거로 해석합니다.",
    "평가 결과에서 제안서와 이메일 초안까지 한 흐름으로 연결합니다.",
  ],
  latest_update: {
    version: "v.1.16.01",
    qualified_cases: 0,
    weighted_total: 0,
    update_generated: false,
  },
  recent_learning_cases: [],
  total_learning_cases: 0,
};

const BIZAIPRO_WINDOW_NAME_KEY = "__BIZAIPRO_STATE__";
const BIZAIPRO_LOCAL_LEARNING_LABEL = "업로드 실시간 평가(업데이트용)";

function cloneValue(value) {
  return JSON.parse(JSON.stringify(value));
}

function getMergeBaseState(currentState = {}) {
  if (currentState && typeof currentState === "object" && Object.keys(currentState).length > 0) {
    return cloneValue(currentState);
  }
  return getStoredState();
}

function deepMerge(target, source) {
  Object.keys(source || {}).forEach((key) => {
    const sourceValue = source[key];
    if (
      sourceValue &&
      typeof sourceValue === "object" &&
      !Array.isArray(sourceValue) &&
      typeof target[key] === "object" &&
      target[key] !== null &&
      !Array.isArray(target[key])
    ) {
      deepMerge(target[key], sourceValue);
    } else {
      target[key] = sourceValue;
    }
  });
  return target;
}

function ensureStateShape(state) {
  if (!state.proposal || typeof state.proposal !== "object" || Array.isArray(state.proposal)) {
    state.proposal = {};
  }
  if (!state.email || typeof state.email !== "object" || Array.isArray(state.email)) {
    state.email = {};
  }

  const defaultProposal = BIZAIPRO_DEFAULT_STATE.proposal || {};
  const defaultEmail = BIZAIPRO_DEFAULT_STATE.email || {};

  Object.keys(defaultProposal).forEach((key) => {
    if (state.proposal[key] === undefined || state.proposal[key] === null) {
      state.proposal[key] = defaultProposal[key];
    }
  });

  Object.keys(defaultEmail).forEach((key) => {
    if (state.email[key] === undefined || state.email[key] === null) {
      state.email[key] = cloneValue(defaultEmail[key]);
    }
  });

  return state;
}

function formatKrw(value) {
  if (value === null || value === undefined || value === "") {
    return "확인 필요";
  }
  const numeric = Number(value);
  if (Number.isNaN(numeric)) {
    return String(value);
  }
  return `${numeric.toLocaleString("ko-KR")}원`;
}

function formatPercent(value, digits = 2) {
  if (value === null || value === undefined || value === "") {
    return "확인 필요";
  }
  const numeric = Number(value);
  if (Number.isNaN(numeric)) {
    return String(value);
  }
  return `${numeric.toFixed(digits)}%`;
}

function formatTenorText(months, days) {
  if (months !== null && months !== undefined && months !== "") {
    const numericMonths = Number(months);
    if (!Number.isNaN(numericMonths) && numericMonths > 0) {
      return `${numericMonths}개월 우선 검토`;
    }
  }
  if (days !== null && days !== undefined && days !== "") {
    const numericDays = Number(days);
    if (!Number.isNaN(numericDays) && numericDays > 0) {
      return `${numericDays}일 기준 검토`;
    }
  }
  return "결제기간 확인 필요";
}

function formatTenorMeta(days) {
  if (days === null || days === undefined || days === "") {
    return "결제유예기간 확인 필요";
  }
  return `결제유예기간 (${Number(days).toLocaleString("ko-KR")}일)`;
}

function getApiBaseUrl() {
  if (window.location.protocol.startsWith("http")) {
    return window.location.origin;
  }
  return "http://127.0.0.1:8011";
}

function formatEngineVersionLabel(engineVersion) {
  const normalized = String(engineVersion || "").trim();
  if (!normalized) return "확인 필요";
  if (normalized === "v.local.learning") return BIZAIPRO_LOCAL_LEARNING_LABEL;
  return normalized;
}

function inferEngineTraits(engineVersion) {
  const normalized = String(engineVersion || "");
  if (normalized.includes("local.learning")) {
    return [
      "업로드된 리포트·노션 링크·추가정보를 즉시 읽어 실시간 평가 결과로 반영합니다.",
      "정식 엔진 버전은 유지하되, 현재 입력 자료를 기준으로 한도·마진·결제기간을 다시 계산합니다.",
      "업데이트 후보 검토용 실시간 평가 결과이므로 입력 자료 품질에 따라 값이 달라집니다.",
    ];
  }
  if (normalized.includes("1.16.01")) {
    return [
      "전시회 URL과 기업 웹주소 URL을 함께 읽어 핵심 정보를 자동 추출합니다.",
      "재무는 제공 가능 여부를 거르는 필터로, 비재무는 제안 메시지 근거로 해석합니다.",
      "평가 결과에서 제안서와 이메일 초안까지 한 흐름으로 연결합니다.",
    ];
  }
  if (normalized.includes("1.0.00")) {
    return [
      "재무 필터를 더 보수적으로 보는 초기 기준입니다.",
      "기본 소개 메일 우선 접근 흐름을 사용합니다.",
      "결제유예기간과 초기 한도를 더 보수적으로 제안합니다.",
    ];
  }
  return [
    "화면 구조와 자동 문장 흐름을 확인하는 기본 샘플 기준입니다.",
    "업로드 결과에 맞춰 카드와 문구를 다시 그립니다.",
  ];
}

async function fetchDashboardSummary() {
  try {
    const response = await fetch(`${getApiBaseUrl()}/api/dashboard`);
    if (!response.ok) {
      throw new Error("dashboard fetch failed");
    }
    const payload = await response.json();
    return payload;
  } catch (error) {
    return cloneValue(BIZAIPRO_DEFAULT_DASHBOARD);
  }
}

async function fetchLearningCases(offset = 0, limit = 5) {
  try {
    const params = new URLSearchParams({
      offset: String(offset),
      limit: String(limit),
    });
    const response = await fetch(`${getApiBaseUrl()}/api/learning/cases?${params.toString()}`);
    if (!response.ok) {
      throw new Error("learning cases fetch failed");
    }
    return await response.json();
  } catch (error) {
    return {
      items: [],
      offset,
      limit,
      total: 0,
      has_more: false,
    };
  }
}

async function fetchLearningCase(caseId) {
  if (!caseId) {
    throw new Error("case id is required");
  }
  const response = await fetch(`${getApiBaseUrl()}/api/learning/cases/${encodeURIComponent(caseId)}`);
  if (!response.ok) {
    throw new Error("learning case fetch failed");
  }
  return await response.json();
}

function priorityTone(priority) {
  const normalized = String(priority || "").trim();
  if (normalized === "최상" || normalized === "상") {
    return { tone: "ok", label: "가능" };
  }
  if (normalized === "중상") {
    return { tone: "hope", label: "희망" };
  }
  return { tone: "warning", label: "주의" };
}

function extractLatestFinancialDisplay(financialSummary) {
  if (!financialSummary || typeof financialSummary !== "object") {
    return null;
  }
  const years = Object.keys(financialSummary)
    .filter((key) => /^\d{4}$/.test(String(key)))
    .sort((a, b) => Number(b) - Number(a));
  if (!years.length) {
    return null;
  }
  const latestYear = years[0];
  const latest = financialSummary[latestYear] || {};
  return {
    year: latestYear,
    sales: latest.sales || null,
    operatingProfit: latest.operating_profit || null,
    netIncome: latest.net_income || null,
  };
}

function buildLearningModeContent(state) {
  const company = state.companyName || "업로드 기업";
  const reportDate = state.reportEvaluationDate || "확인 필요";
  const grade = state.financialFilterSignal || "확인 필요";
  const totalScore = state.reportTotalScore || "확인 필요";
  const pd = state.reportPdPct || "확인 필요";
  const limit = state.reportMonthlyCreditLimit || state.estimatedLimitValue || "확인 필요";
  const consultationLinked = state.consultingReportUrl
    ? "상담리포트 노션 링크가 연결되어 있습니다."
    : "상담리포트 노션 링크는 아직 연결되지 않았습니다.";
  const internalLinked = state.internalReviewUrl
    ? "내부심사보고서 링크가 연결되어 있습니다."
    : "내부심사보고서 링크는 아직 없습니다.";
  const supportingLinked = state.learningConsultingFileName
    ? `상담보고서 파일 '${state.learningConsultingFileName}'이 연결되어 있습니다.`
    : "상담보고서 파일은 아직 없습니다.";
  const extraInfoLinked = state.learningExtraInfo
    ? "추가 정보 메모가 연결되어 있습니다."
    : "추가 정보 메모는 아직 없습니다.";
  const combinedCrossChecks = [
    ...(state.consultingCrossChecks || []),
    ...(state.internalReviewCrossChecks || []),
    ...(state.supportingDocumentCrossChecks || []),
  ];
  const combinedIssues = [
    ...(state.consultingIssues || []),
    ...(state.internalReviewIssues || []),
    ...(state.supportingDocumentIssues || []),
    ...(state.additionalInfoIssues || []),
  ];

  state.heroPillText = "학습 평가 결과";
  state.heroTitleText = `${company} 평가 결과 리포트`;
  state.heroSubcopyText = state.overviewSummary;
  state.publicInfoSectionTitle = "리포트 및 상담 요약";
  state.summaryCard1Title = "리포트 기준 기업 정보";
  state.summaryCard2Title = "상담/심사자료 연결 상태";
  state.summaryCard3Title = "재무 필터 해석";
  state.actionSectionTitle = "평가 포인트와 추가 확인 항목";
  state.whyNowTitle = "현재 평가 해석";
  state.useCaseTitle = "추정 활용 범위";
  state.checksTitle = "추가 확인할 점";
  state.proposalHeroPill = "학습모드 제안서";
  state.proposalHeroTitle = "리포트와 상담자료를 바탕으로 제안서를 생성합니다";
  state.proposalHeroSubcopy =
    "현재 저장된 리포트, 상담리포트, 내부심사자료를 기준으로 기업평가 해석과 제안 포인트를 짧은 비즈니스 톤으로 정리합니다.";
  state.proposalContextLabel = "상담리포트 / 평가기준";
  state.proposalContextValue = `${state.consultingReportUrl ? "노션 링크 연결" : "노션 링크 없음"} / ${reportDate}`;
  state.emailHeroPill = "학습모드 이메일";
  state.emailHeroTitle = "학습 평가 핵심 내용을 메일 문안으로 바꿉니다";
  state.emailHeroSubcopy =
    "리포트와 상담자료 기반 해석을 바탕으로, 후속 제안과 자료 요청에 맞는 이메일 문안을 생성합니다.";

  const latestFinancialDisplay = extractLatestFinancialDisplay(state.reportFinancialSummary);
  if (latestFinancialDisplay) {
    state.recentRevenueLabel = state.recentRevenueLabel || `${latestFinancialDisplay.year}년 매출액`;
    state.recentRevenueValue = state.recentRevenueValue || latestFinancialDisplay.sales || "확인 필요";
    state.operatingProfitLabel = state.operatingProfitLabel || `${latestFinancialDisplay.year}년 영업이익`;
    state.operatingProfitValue = state.operatingProfitValue || latestFinancialDisplay.operatingProfit || "확인 필요";
    state.netIncomeLabel = state.netIncomeLabel || `${latestFinancialDisplay.year}년 당기순이익`;
    state.netIncomeValue = state.netIncomeValue || latestFinancialDisplay.netIncome || "확인 필요";
  }

  state.recentRevenueLabel = state.recentRevenueLabel || "리포트 매출액";
  state.recentRevenueValue = state.recentRevenueValue || "확인 필요";
  state.operatingProfitLabel = state.operatingProfitLabel || "리포트 영업이익";
  state.operatingProfitValue = state.operatingProfitValue || "확인 필요";
  state.estimatedLimitLabel = state.estimatedLimitLabel || "예상 한도";
  state.estimatedMarginLabel = state.estimatedMarginLabel || "예상 마진율";
  state.cashflowSignal = state.reportPdPct ? `PD ${state.reportPdPct}` : "추가 확인 필요";
  state.heroNextAction =
    state.consultingValidationSummary || state.internalReviewValidationSummary || state.supportingDocumentSummary
      ? "리포트·상담·심사 교차검증 후 제안 정리"
      : "리포트 검토 후 상담 내용 반영";
  state.nextAction =
    state.consultingValidationSummary || state.internalReviewValidationSummary || state.supportingDocumentSummary
      ? "교차검증 완료 후<br />제안서 생성"
      : "상담 확인 후<br />제안서 생성";
  state.recommendedTenorText = state.recommendedTenorText || "결제기간 추가 확인";

  state.websiteSummary = `${company} 리포트를 기준으로 ${state.businessNumber ? `사업자번호 ${state.businessNumber}, ` : ""}평가기준일 ${reportDate} 정보를 정리했습니다.`;
  state.exhibitionSummary =
    [
      state.consultingValidationSummary,
      state.internalReviewValidationSummary,
      state.supportingDocumentSummary,
      state.additionalInfoSummary,
    ]
      .filter(Boolean)
      .join(" ")
      .trim() || `${consultationLinked} ${internalLinked} ${supportingLinked} ${extraInfoLinked}`;
  state.financialSummary = `재무 필터 신호는 ${grade}이며, 종합점수는 ${totalScore}, 월간 적정 신용한도는 ${limit}, 부도확률(PD)은 ${pd} 기준으로 해석합니다.`;
  state.whyNow =
    state.consultingSummary ||
    state.internalReviewSummary ||
    state.supportingDocumentSummary ||
    state.additionalInfoSummary ||
    "업로드한 리포트와 상담자료를 기준으로 현재 거래 가능성과 보완 필요 항목을 먼저 정리하는 단계입니다.";
  state.useCase =
    `${company}의 실제 자금 수요와 거래 구조를 상담 내용에 맞춰 다시 해석한 뒤 제안 범위와 우선순위를 정리합니다.`;
  state.checks = combinedCrossChecks.length
    ? combinedCrossChecks.slice(0, 5)
    : combinedIssues.length
    ? combinedIssues.slice(0, 5)
    : [
        "상담리포트에 적힌 실제 거래 구조와 최근 발주 여부",
        "내부심사보고서 또는 추가 자료에 기재된 보완 항목",
        "리포트 기준 한도와 실제 거래 규모의 적합성",
      ];

  state.proposal.executive = `${company}는 업로드한 리포트와 상담자료를 기준으로 현재 제안 상태가 '${state.currentProposalState}'로 해석됩니다.`;
  state.proposal.company = `${company}의 재무 필터 신호는 ${grade}, 종합점수는 ${totalScore}, 월간 적정 신용한도는 ${limit} 수준으로 읽힙니다.`;
  state.proposal.exhibition = `${consultationLinked} ${internalLinked} ${supportingLinked} ${extraInfoLinked}`;
  state.proposal.opportunity =
    "학습모드에서는 업로드한 자료를 바탕으로 실제 거래 구조와 자금 수요를 다시 정리하고, 제안 가능한 범위를 보수적으로 설명하는 접근이 적절합니다.";
  state.proposal.structure =
    `현재 기준 예상 한도는 ${state.estimatedLimitValue}, 예상 마진율은 ${state.estimatedMarginValue} 수준이며, 결제유예기간은 ${state.recommendedTenorText}로 검토합니다.`;
  state.proposal.risks = combinedIssues.length
    ? combinedIssues.join(" ")
    : `우선 확인할 항목은 실제 발주 여부, 회수 구조, 상담자료와 리포트 사이의 불일치 여부입니다.`;
  state.proposal.next = "상담 내용을 다시 확인한 뒤 조건부 제안서와 후속 이메일로 연결하는 것이 좋습니다.";

  state.email.subject = `${company} 관련 후속 검토 제안드립니다`;
  return state;
}

function buildExhibitionModeContent(state) {
  const company = state.companyName || state.shortName || "전시회 기업";
  const exhibitionLabel = state.exhibitionName
    ? `${state.exhibitionName}${state.exhibitionYear ? ` / ${state.exhibitionYear}` : ""}`
    : "전시회 정보 확인 필요";
  const websiteLabel = state.website || "홈페이지 확인 필요";

  state.heroPillText = "평가 결과 허브";
  state.heroTitleText = "평가 결과 리포트";
  state.heroSubcopyText = state.overviewSummary;
  state.publicInfoSectionTitle = "공개 정보 요약";
  state.summaryCard1Title = "홈페이지 기준 사업 내용";
  state.summaryCard2Title = "전시회/상담 맥락";
  state.summaryCard3Title = "재무 필터 해석";
  state.actionSectionTitle = "제안 포인트와 먼저 확인할 점";
  state.whyNowTitle = "왜 지금 제안할 수 있는가";
  state.useCaseTitle = "FlowPay 활용 가설";
  state.checksTitle = "먼저 확인할 점";
  state.proposalHeroPill = "제안서 생성하기";
  state.proposalHeroTitle = "맥킨지 보고서 스타일 제안서를 바로 생성합니다";
  state.proposalHeroSubcopy =
    "현재 저장된 평가 결과를 기준으로 신청업체명, 사업자번호, 대표자명, 전시회/상담 맥락을 자동 채워 짧고 단정한 비즈니스 톤 제안서를 만듭니다.";
  state.proposalContextLabel = "전시회명 / 참여 연도";
  state.proposalContextValue = exhibitionLabel;
  state.emailHeroPill = "이메일 컨텐츠 생성하기";
  state.emailHeroTitle = "제안서 핵심 내용을 메일 문안으로 바로 바꿉니다";
  state.emailHeroSubcopy =
    "평가 결과와 제안서 핵심 수치를 바탕으로, 선택한 영업담당자와 제목 템플릿에 맞는 이메일 본문을 바로 만듭니다.";

  state.websiteSummary =
    state.websiteSummary ||
    `${company} 홈페이지(${websiteLabel}) 기준으로 ${state.industryItem || "사업 내용"}을 소개하는 기업으로 읽힙니다.`;
  state.exhibitionSummary =
    state.exhibitionSummary ||
    `${exhibitionLabel} 참가 공개 정보와 URL을 기준으로 기업 기본정보와 제안 맥락을 정리했습니다.`;
  state.financialSummary =
    state.financialSummary ||
    `공개 리포트 기준 재무 필터 신호는 ${state.financialFilterSignal}이며, 예상 한도는 ${state.estimatedLimitValue}, 예상 마진율은 ${state.estimatedMarginValue} 수준으로 읽힙니다.`;
  state.whyNow =
    state.whyNow ||
    "전시회 참가 시점은 데모, 파일럿, 공급 논의가 늘어나는 시기라 부품 조달과 외주 가공 자금 공백을 먼저 연결하는 제안이 자연스럽습니다.";
  state.useCase =
    state.useCase ||
    "제어 모듈, 드라이브 부품, 외주 가공비, 시제품·초기 공급 물량을 대상으로 단기 선매입 구조를 제안할 수 있습니다.";
  state.checks =
    state.checks && state.checks.length
      ? state.checks
      : ["최근 발주서 또는 공급계약 유무", "주요 매입처와 주요 고객사 결제 조건", "외주 가공 및 부품 매입의 실제 회전 주기"];
  state.estimatedLimitLabel = state.estimatedLimitLabel || "예상 한도";
  state.estimatedMarginLabel = state.estimatedMarginLabel || "예상 마진율";
  return state;
}

function resetForLearningMode(state) {
  const wasMode = state.mode;
  state.mode = "learning";
  if (wasMode !== "learning") {
    state.companyName = "업로드 기업";
    state.shortName = "업로드 기업";
    state.representativeName = "확인 필요";
    state.businessNumber = "확인 필요";
  }
  state.exhibitionName = "";
  state.exhibitionYear = "";
  state.exhibitionInfoUrl = "";
  state.website = "";
  state.industryItem = "";
  state.companyOverview = "";
  state.recentRevenueLabel = "리포트 매출액";
  state.recentRevenueValue = "확인 필요";
  state.operatingProfitLabel = "리포트 영업이익";
  state.operatingProfitValue = "확인 필요";
  state.estimatedLimitValue = "추가 확인 필요";
  state.estimatedMarginValue = "추가 확인 필요";
  state.financialFilterSignal = "확인 필요";
  state.cashflowSignal = "추가 확인 필요";
  state.proposalPriority = "중";
  state.currentProposalState = "추가 확인 필요";
  state.reportTotalScore = "";
  state.reportPdPct = "";
  state.reportEvaluationDate = "";
  state.reportIncorporatedDate = "";
  state.reportMonthlyCreditLimit = "";
  state.reportFinancialSummary = null;
  state.reportCreditGrade = "";
  state.reportType = "";
  state.reportSourceFileName = "";
  state.learningFlowScoreFileName = "";
  state.learningConsultingFileName = "";
  state.consultingSummary = "";
  state.consultingCrossChecks = [];
  state.consultingIssues = [];
  state.consultingValidationSummary = "";
  state.internalReviewSummary = "";
  state.internalReviewCrossChecks = [];
  state.internalReviewIssues = [];
  state.internalReviewValidationSummary = "";
  state.supportingDocumentSummary = "";
  state.supportingDocumentCrossChecks = [];
  state.supportingDocumentIssues = [];
  state.additionalInfoSummary = "";
  state.additionalInfoIssues = [];
  return state;
}

function resetForExhibitionMode(state) {
  const wasMode = state.mode;
  state.mode = "exhibition";
  if (wasMode !== "exhibition") {
    state.companyName = "전시회 기업";
    state.shortName = "전시회 기업";
    state.representativeName = "담당자 확인";
    state.businessNumber = "확인 필요";
  }
  state.consultingReportUrl = "";
  state.internalReviewUrl = "";
  state.learningExtraInfo = "";
  return state;
}

function applyModeSpecificContent(state) {
  if (state.mode === "learning") {
    return buildLearningModeContent(state);
  }
  return buildExhibitionModeContent(state);
}

function normalizeState(state) {
  const normalized = ensureStateShape(cloneValue(state));
  normalized.estimatedMarginMeta = formatTenorMeta(normalized.requestedTenorDays);
  normalized.recommendedTenorText = formatTenorText(normalized.requestedTenorMonths, normalized.requestedTenorDays);
  const priority = priorityTone(normalized.proposalPriority);
  normalized.proposalPriorityTone = priority.tone;
  normalized.proposalPriorityState = priority.label;
  return applyModeSpecificContent(normalized);
}

function getDefaultState() {
  return normalizeState(cloneValue(BIZAIPRO_DEFAULT_STATE));
}

function readBrowserStorage() {
  const candidates = [];
  try {
    candidates.push(window.localStorage.getItem(BIZAIPRO_STORAGE_KEY));
  } catch (error) {
    // ignore
  }
  try {
    candidates.push(window.sessionStorage.getItem(BIZAIPRO_STORAGE_KEY));
  } catch (error) {
    // ignore
  }
  try {
    if (window.name && window.name.startsWith(BIZAIPRO_WINDOW_NAME_KEY)) {
      candidates.push(window.name.slice(BIZAIPRO_WINDOW_NAME_KEY.length));
    }
  } catch (error) {
    // ignore
  }
  return candidates.filter(Boolean);
}

function getStoredState() {
  const candidates = readBrowserStorage();
  for (const raw of candidates) {
    try {
      if (!raw) continue;
      return normalizeState(JSON.parse(raw));
    } catch (error) {
      // try next storage
    }
  }
  return getDefaultState();
}

function saveState(state) {
  const normalized = normalizeState(state);
  const serialized = JSON.stringify(normalized);
  try {
    window.localStorage.setItem(BIZAIPRO_STORAGE_KEY, serialized);
  } catch (error) {
    // ignore
  }
  try {
    window.sessionStorage.setItem(BIZAIPRO_STORAGE_KEY, serialized);
  } catch (error) {
    // ignore
  }
  try {
    window.name = `${BIZAIPRO_WINDOW_NAME_KEY}${serialized}`;
  } catch (error) {
    // ignore
  }
  return normalized;
}

function resetState() {
  return saveState(getDefaultState());
}

function getPresetOptions() {
  return Object.values(BIZAIPRO_ENGINE_PRESETS).map((preset) => ({
    value: preset.key,
    label: preset.label,
  }));
}

function applyPreset(key) {
  const base = getDefaultState();
  deepMerge(base, BIZAIPRO_ENGINE_PRESETS[key] || BIZAIPRO_ENGINE_PRESETS.latest);
  return saveState(base);
}

function applyWebContext(context) {
  const base = getDefaultState();
  const proposalContext = context.proposal_context || {};
  const salesView = context.sales_view || {};
  const riskNotes = salesView.risk_notes || [];

  base.engineVersion = context.engine_version ? `${context.engine_version}` : base.engineVersion;
  base.companyName = context.company_name || base.companyName;
  base.shortName = proposalContext.sales_destination_name || base.shortName;
  base.representativeName = proposalContext.representative_name || base.representativeName;
  base.proposalPriority = salesView.recommendation || base.proposalPriority;
  base.currentProposalState = salesView.recommendation || base.currentProposalState;
  base.heroNextAction = salesView.next_action || base.heroNextAction;
  base.nextAction = salesView.next_action ? String(salesView.next_action).replace(/\n/g, "<br />") : base.nextAction;
  base.requestedTenorMonths = context.requested_tenor_months ?? base.requestedTenorMonths;
  base.requestedTenorDays =
    context.industry_fit?.requested_tenor_days ??
    (context.requested_tenor_months ? Number(context.requested_tenor_months) * 30 : base.requestedTenorDays);
  base.estimatedLimitValue = formatKrw(salesView.estimated_limit_krw) || base.estimatedLimitValue;
  base.estimatedMarginValue = formatPercent(salesView.estimated_margin_rate_pct) || base.estimatedMarginValue;
  base.financialFilterSignal = context.applicant?.grade || context.overall?.grade || base.financialFilterSignal;
  base.cashflowSignal = riskNotes[0] || base.cashflowSignal;
  base.overviewSummary =
    context.sales_summary ||
    `${context.company_name || base.shortName} 관련 영업 참고 결과는 ${salesView.recommendation || "추가 확인 필요"}입니다.`;
  base.proposal.executive =
    `${context.company_name || base.companyName} 관련 영업 참고 결과는 '${salesView.recommendation || "추가 확인 필요"}'입니다. ` +
    `예상 한도는 ${formatKrw(salesView.estimated_limit_krw)} 수준이며, 추가 자료를 받으면 실제 제안 조건을 더 구체화할 수 있습니다.`;
  base.proposal.company =
    `신청업체 참고등급은 ${context.applicant?.grade || "-"}, 매출처 참고등급은 ${context.buyer?.grade || "-"}, ` +
    `거래구조 참고등급은 ${context.transaction?.grade || "-"}, 통합 참고등급은 ${context.overall?.grade || "-"}입니다.`;
  base.proposal.structure =
    `예상 한도는 ${formatKrw(salesView.estimated_limit_krw)} 수준이고, 예상 마진율은 ${formatPercent(salesView.estimated_margin_rate_pct)} 수준입니다. ` +
    `요청 결제기간 ${context.requested_tenor_months || "-"}개월 기준으로 구조를 먼저 설명하는 접근이 적절합니다.`;
  base.proposal.risks = riskNotes.length ? riskNotes.join(" ") : base.proposal.risks;
  base.proposal.next = salesView.next_action || base.proposal.next;
  if (context.sales_email_draft) {
    base.email.bodyLines = String(context.sales_email_draft).split("\n");
  }
  base.email.subject = `${context.company_name || base.companyName} 관련 제안드립니다`;
  return saveState(base);
}

async function parseContextFile(file) {
  const text = await file.text();
  const raw = JSON.parse(text);
  if (window.location.protocol.startsWith("http") || window.location.protocol === "file:") {
    try {
      const formData = new FormData();
      formData.append("file", new Blob([text], { type: "application/json" }), file.name);
      const response = await fetch(`${getApiBaseUrl()}/api/web-context/parse`, {
        method: "POST",
        body: formData,
      });
      if (response.ok) {
        const payload = await response.json();
        if (payload.state_patch) {
          const base = getDefaultState();
          deepMerge(base, payload.state_patch);
          return saveState(base);
        }
      }
    } catch (error) {
      // Local fallback below.
    }
  }
  applyWebContext(raw);
  return getStoredState();
}

async function extractExhibitionContext({ exhibitionInfoUrl, websiteUrl, reportFile }) {
  const formData = new FormData();
  formData.append("exhibition_info_url", exhibitionInfoUrl || "");
  formData.append("website_url", websiteUrl || "");
  if (reportFile) {
    formData.append("report_file", reportFile, reportFile.name);
  }

  const response = await fetch(`${getApiBaseUrl()}/api/exhibition/extract`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.detail || "전시회 정보를 자동 추출하지 못했습니다.");
  }

  const payload = await response.json();
  const base = getMergeBaseState({
    exhibitionInfoUrl,
    website: websiteUrl,
  });
  deepMerge(base, payload.state_patch || {});
  const next = saveState(base);
  return {
    state: next,
    extracted: payload.extracted || {},
  };
}

async function parseFlowscoreReport(file, currentState = {}) {
  const formData = new FormData();
  formData.append("file", file, file.name);

  const response = await fetch(`${getApiBaseUrl()}/api/report/flowscore-parse`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.detail || "리포트를 읽지 못했습니다.");
  }

  const payload = await response.json();
  const base = getMergeBaseState(currentState);
  deepMerge(base, payload.state_patch || {});
  const next = saveState(base);
  return {
    state: next,
    parsed: payload.parsed_report || {},
  };
}

async function parseConsultingReport(url, currentState = {}) {
  const formData = new FormData();
  formData.append("consulting_url", url || "");
  formData.append("company_name", currentState.companyName || "");
  formData.append("business_number", currentState.businessNumber || "");
  formData.append("representative_name", currentState.representativeName || "");

  const response = await fetch(`${getApiBaseUrl()}/api/consulting/parse`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.detail || "상담보고서 링크를 읽지 못했습니다.");
  }

  const payload = await response.json();
  const base = getMergeBaseState(currentState);
  deepMerge(base, payload.state_patch || {});
  const next = saveState(base);
  return {
    state: next,
    parsed: payload.parsed_consulting_report || {},
  };
}

async function parseInternalReview(url, currentState = {}) {
  const formData = new FormData();
  formData.append("review_url", url || "");
  formData.append("company_name", currentState.companyName || "");
  formData.append("business_number", currentState.businessNumber || "");
  formData.append("representative_name", currentState.representativeName || "");

  const response = await fetch(`${getApiBaseUrl()}/api/internal-review/parse`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.detail || "심사보고서 링크를 읽지 못했습니다.");
  }

  const payload = await response.json();
  const base = getMergeBaseState(currentState);
  deepMerge(base, payload.state_patch || {});
  const next = saveState(base);
  return {
    state: next,
    parsed: payload.parsed_internal_review || {},
  };
}

async function parseSupportingDocument(file, label, currentState = {}) {
  const formData = new FormData();
  formData.append("label", label || "보조자료");
  formData.append("company_name", currentState.companyName || "");
  formData.append("business_number", currentState.businessNumber || "");
  formData.append("representative_name", currentState.representativeName || "");
  formData.append("file", file, file.name);

  const response = await fetch(`${getApiBaseUrl()}/api/supporting-document/parse`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.detail || "보조자료 파일을 읽지 못했습니다.");
  }

  const payload = await response.json();
  const base = getMergeBaseState(currentState);
  deepMerge(base, payload.state_patch || {});
  const next = saveState(base);
  return {
    state: next,
    parsed: payload.parsed_document || {},
  };
}

async function parseAdditionalInfoText(text, currentState = {}) {
  const formData = new FormData();
  formData.append("text", text || "");
  formData.append("company_name", currentState.companyName || "");
  formData.append("business_number", currentState.businessNumber || "");
  formData.append("representative_name", currentState.representativeName || "");

  const response = await fetch(`${getApiBaseUrl()}/api/additional-info/parse`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.detail || "추가 정보를 읽지 못했습니다.");
  }

  const payload = await response.json();
  const base = getMergeBaseState(currentState);
  deepMerge(base, payload.state_patch || {});
  const next = saveState(base);
  return {
    state: next,
    parsed: payload.parsed_additional_info || {},
  };
}

async function evaluateLearningState(currentState = {}) {
  const response = await fetch(`${getApiBaseUrl()}/api/learning/evaluate`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ state: currentState }),
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.detail || "학습 평가 엔진을 실행하지 못했습니다.");
  }

  const payload = await response.json();
  const base = getMergeBaseState(currentState);
  deepMerge(base, payload.state_patch || {});
  const next = saveState(base);
  return {
    state: next,
    result: payload.result || {},
    engineInput: payload.engine_input || {},
    dashboardSummary: payload.dashboard_summary || null,
  };
}

function buildProposalText(state) {
  const sections = [
    ["Executive Summary", state.proposal.executive],
    ["Company Snapshot", state.proposal.company],
    [state.proposalContextLabel || "Context", state.proposal.exhibition],
    ["Opportunity Assessment", state.proposal.opportunity],
    ["Suggested Initial Structure", state.proposal.structure],
    ["Risks And Checks", state.proposal.risks],
    ["Next Actions", state.proposal.next],
  ];
  return sections.map(([title, body]) => `${title}\n${body}`).join("\n\n");
}

function parseKrwDisplay(value) {
  const text = String(value || "");
  const digits = text.replace(/[^0-9-]/g, "");
  if (!digits) return null;
  const numeric = Number(digits);
  return Number.isNaN(numeric) ? null : numeric;
}

function parsePercentDisplay(value) {
  const text = String(value || "");
  const matched = text.match(/-?\d+(?:\.\d+)?/);
  if (!matched) return null;
  const numeric = Number(matched[0]);
  return Number.isNaN(numeric) ? null : numeric;
}

function gradeToFitScore(grade, fallback = null) {
  if (fallback !== null && fallback !== undefined && fallback !== "") {
    const numeric = Number(String(fallback).replace(/[^0-9.]/g, ""));
    if (!Number.isNaN(numeric) && numeric > 0) return numeric;
  }
  const normalizedRaw = String(grade || "").trim().toUpperCase();
  if (!normalizedRaw) return null;
  let modifier = 0;
  let normalized = normalizedRaw;
  if (normalized.endsWith("+")) {
    modifier = 3;
    normalized = normalized.slice(0, -1);
  } else if (normalized.endsWith("-")) {
    modifier = -3;
    normalized = normalized.slice(0, -1);
  }
  const scoreMap = { AAA: 92, AA: 88, A: 82, BBB: 72, BB: 62, B: 52, CCC: 38, CC: 30, C: 22, D: 10 };
  const base = scoreMap[normalized];
  return base ? Math.max(0, Math.min(100, base + modifier)) : null;
}

function deriveRotationCount(days) {
  const numericDays = Number(days || 0);
  if (!numericDays || Number.isNaN(numericDays) || numericDays <= 0) return 0;
  return Math.max(1, Math.floor(360 / numericDays));
}

function formatEok(krw) {
  const numeric = Number(krw || 0);
  if (!numeric || Number.isNaN(numeric)) return "0.0";
  return (numeric / 100000000).toFixed(1);
}

function buildEmailTemplateMetrics(state) {
  const company = state.companyName || "귀사";
  const representative = state.representativeName || "대표";
  const grade = state.financialFilterSignal || "확인 필요";
  const fitScore = gradeToFitScore(grade, state.reportTotalScore);
  const tenorDays = Number(state.requestedTenorDays || 0) || (Number(state.requestedTenorMonths || 0) * 30);
  const marginRate = parsePercentDisplay(state.estimatedMarginValue);
  const limitKrw = parseKrwDisplay(state.estimatedLimitValue);
  const marginAmountKrw = limitKrw !== null && marginRate !== null ? Math.round(limitKrw * (marginRate / 100)) : null;
  const rotationCount = deriveRotationCount(tenorDays);
  const annualSalesIncreaseKrw =
    limitKrw !== null && marginAmountKrw !== null && rotationCount > 0 ? (limitKrw + marginAmountKrw) * rotationCount : null;
  const revenueKrw = parseKrwDisplay(state.recentRevenueValue);
  const operatingProfitKrw = parseKrwDisplay(state.operatingProfitValue);
  const operatingMarginPct =
    revenueKrw && operatingProfitKrw !== null && revenueKrw > 0 && operatingProfitKrw > 0
      ? Number(((operatingProfitKrw / revenueKrw) * 100).toFixed(2))
      : 4.94;
  const annualOperatingProfitIncreaseKrw =
    annualSalesIncreaseKrw !== null ? Math.round(annualSalesIncreaseKrw * (operatingMarginPct / 100)) : null;

  const annualSummarySentence =
    marginRate !== null && rotationCount > 0 && annualSalesIncreaseKrw !== null
      ? `현재 제안드릴 내용은 ‘신용등급 ${grade}, 적합도 ${fitScore !== null ? fitScore : "확인 필요"}점, ${tenorDays || "확인 필요"}일 기준 권장 마진율 ${marginRate.toFixed(
          2
        )}%를 바탕으로 작성되었고, 연 ${rotationCount}회 회전 기준 약 ${formatEok(
          annualSalesIncreaseKrw
        )}억원 규모의 추가 매출과 영업이익 약 ${formatEok(annualOperatingProfitIncreaseKrw)}억원의 가능성’을 전제로 하고 있습니다.`
      : `현재 제안드릴 내용은 ‘신용등급 ${grade}, 적합도 ${fitScore !== null ? fitScore : "확인 필요"}점, 결제유예기간 ${tenorDays || "확인 필요"}일 기준 권장 마진율 ${String(
          state.estimatedMarginValue || "확인 필요"
        )}를 바탕으로 작성되었습니다.’`;

  return {
    company,
    representative,
    grade,
    fitScoreText: fitScore !== null ? `${fitScore}점` : "확인 필요",
    tenorDays,
    marginRateText: marginRate !== null ? `${marginRate.toFixed(2)}%` : String(state.estimatedMarginValue || "확인 필요"),
    rotationCount,
    annualSalesIncreaseEok: formatEok(annualSalesIncreaseKrw),
    annualOperatingProfitIncreaseEok: formatEok(annualOperatingProfitIncreaseKrw),
    annualSummarySentence,
  };
}

function renderEmailSubject(state, templateIndex = 0) {
  const template = BIZAIPRO_EMAIL_TEMPLATES[Number(templateIndex) || 0] || BIZAIPRO_EMAIL_TEMPLATES[0];
  return template.titleTemplate;
}

function buildEmailBody(state, salesperson, templateIndex = 0) {
  const person = salesperson || BIZAIPRO_SALESPEOPLE[0];
  const metrics = buildEmailTemplateMetrics(state);
  const salutation = `${metrics.company} 귀중,`;
  const greeting = `안녕하세요, ${metrics.representative}님.`;
  const signer = `${person.title} ${person.name}\n${person.phone}`;
  const bodies = [
    [
      salutation,
      greeting,
      "사람의 성장호르몬이 성장기 동안 몸의 성장과 대사에 관여하듯, 기업도 성장 구간에서는 자금과 원자재가 제때 공급되어야 성장 속도를 유지할 수 있습니다.",
      `${metrics.company}처럼 수주 기회가 늘어나는 구간에서는 원자재 매입 시점과 매출 회수 시점 사이의 공백이 실제 성장 속도를 늦추는 요인이 되곤 합니다.`,
      "플로우페이는 그 공백을 메우기 위해 설계된 기업 전용 SNPL 서비스로, 원자재를 먼저 결제·납품하고 이후 협의된 시점에 정산할 수 있도록 지원합니다.",
      `첨부된 제안서 기준으로 보면 ${metrics.company}에는 “수주는 늘었는데 원자재 구입 자금이 부족한 상황”에 대응하는 구조가 중요합니다.`,
      metrics.annualSummarySentence,
      "즉, 플로우페이는 기업이 자금 경색 때문에 생산 확대와 매출 성장을 늦추지 않도록 돕는 운영형 대안이라고 말씀드릴 수 있습니다.",
      "괜찮으시다면 15분만 시간을 주시면, 분석 대상 기업에 맞는 활용 방식만 간단히 공유드리겠습니다.",
      "감사합니다.",
      signer,
    ],
    [
      salutation,
      greeting,
      `${metrics.company}의 성장 타이밍을 지키기 위해서는 수주 확대 시점에 필요한 자금과 원자재가 함께 연결되는 구조가 중요합니다.`,
      "특히 원자재 선매입 자금이 부족하면 생산 시작과 납기 대응이 늦어지면서, 확보 가능한 매출 기회를 실제 실적으로 전환하기 어려워질 수 있습니다.",
      "플로우페이는 담보 중심의 대출이 아니라, 실제 거래 흐름에 맞춰 원자재를 먼저 공급하는 방식으로 운영되기 때문에 보다 실무적인 대응이 가능합니다.",
      `첨부된 제안서 기준으로 보면 ${metrics.company}에는 “수주는 늘었는데 원자재 구입 자금이 부족한 상황”에 대응하는 구조가 중요합니다.`,
      metrics.annualSummarySentence,
      `${metrics.company} 기준으로 적용 가능한 운영 구조를 짧게 정리해 공유드릴 수 있으니, 편하신 시간 15분만 주시면 감사하겠습니다.`,
      "감사합니다.",
      signer,
    ],
    [
      salutation,
      greeting,
      "원자재 매입 부담이 커질수록 생산 확대 계획은 있어도 실행 타이밍을 늦출 수밖에 없습니다.",
      `${metrics.company}도 원자재 매입 시점에 자금이 집중되면 납기 대응과 회전 속도에 부담이 생길 수 있습니다.`,
      "플로우페이는 필요한 원자재를 먼저 결제·납품하고 이후 정산하는 구조라, 매입 부담을 나눠서 운영할 수 있도록 돕습니다.",
      `첨부된 제안서 기준으로 보면 ${metrics.company}에는 “수주는 늘었는데 원자재 구입 자금이 부족한 상황”에 대응하는 구조가 중요합니다.`,
      metrics.annualSummarySentence,
      "즉, 플로우페이는 기업이 자금 경색 때문에 생산 확대와 매출 성장을 늦추지 않도록 돕는 운영형 대안이라고 말씀드릴 수 있습니다.",
      "현재 운영 구조 기준으로 어느 구간에서 부담이 줄어들 수 있는지, 간단한 예시 중심으로 설명드리겠습니다.",
      "감사합니다.",
      signer,
    ],
    [
      salutation,
      greeting,
      "생산 확대가 가능한 기업이라도 매출 회수 시점까지의 공백이 길면 실제로는 성장 속도를 조절할 수밖에 없습니다.",
      `${metrics.company}에 필요한 것은 단순 대출 한도보다, 생산 시작 시점에 바로 연결되는 매입자금 구조일 수 있습니다.`,
      "플로우페이는 생산 확대와 매출 회수 사이의 시차를 메우는 방식으로 설계되어, 자금 공백 때문에 수주를 늦추지 않도록 지원합니다.",
      `첨부된 제안서 기준으로 보면 ${metrics.company}에는 “수주는 늘었는데 원자재 구입 자금이 부족한 상황”에 대응하는 구조가 중요합니다.`,
      metrics.annualSummarySentence,
      "즉, 플로우페이는 기업이 자금 경색 때문에 생산 확대와 매출 성장을 늦추지 않도록 돕는 운영형 대안이라고 말씀드릴 수 있습니다.",
      "운영 현황을 기준으로 가장 현실적인 적용 범위를 15분 정도로 간단히 공유드리겠습니다.",
      "감사합니다.",
      signer,
    ],
    [
      salutation,
      greeting,
      `${metrics.company}에 맞는 원자재 선공급 구조를 짧게 제안드리고자 연락드렸습니다.`,
      "기업마다 자금 수요가 발생하는 시점과 매출이 회수되는 시점이 다르기 때문에, 동일한 대출 구조보다 거래 흐름에 맞는 방식이 더 유효할 수 있습니다.",
      "플로우페이는 기업별 발주 구조와 정산 시점에 맞춰 자금을 연결하는 BNPL 형태로 운영되어, 실제 현업에서 활용 가능한 대안이 될 수 있습니다.",
      `첨부된 제안서 기준으로 보면 ${metrics.company}에는 “수주는 늘었는데 원자재 구입 자금이 부족한 상황”에 대응하는 구조가 중요합니다.`,
      metrics.annualSummarySentence,
      "즉, 플로우페이는 기업이 자금 경색 때문에 생산 확대와 매출 성장을 늦추지 않도록 돕는 운영형 대안이라고 말씀드릴 수 있습니다.",
      `${metrics.company} 상황에 맞춘 조건 예시를 간단히 설명드릴 수 있으니, 검토 가능하신 시간을 알려주시면 맞춰서 안내드리겠습니다.`,
      "감사합니다.",
      signer,
    ],
    [
      salutation,
      greeting,
      "운영자금이 필요할 때 꼭 대출만이 해답은 아닐 수 있습니다.",
      "특히 원자재를 먼저 확보해야 하는 기업은 현금 대출보다 거래 구조에 맞춘 선결제 방식이 더 적합한 경우가 많습니다.",
      "플로우페이는 대출이 아닌 원자재 선결제·후정산 구조로, 담보와 복잡한 서류 부담을 낮추면서도 구매력과 현금흐름 개선을 지원합니다.",
      `첨부된 제안서 기준으로 보면 ${metrics.company}에는 “수주는 늘었는데 원자재 구입 자금이 부족한 상황”에 대응하는 구조가 중요합니다.`,
      metrics.annualSummarySentence,
      "즉, 플로우페이는 기업이 자금 경색 때문에 생산 확대와 매출 성장을 늦추지 않도록 돕는 운영형 대안이라고 말씀드릴 수 있습니다.",
      "기존 금융 방식과 어떤 점이 다른지, 분석 대상 기업에 적용 가능한 방식 위주로 짧게 설명드리겠습니다.",
      "감사합니다.",
      signer,
    ],
  ];

  return (bodies[Number(templateIndex) || 0] || bodies[0]).join("\n\n");
}

function copyText(text) {
  if (navigator.clipboard?.writeText) {
    return navigator.clipboard.writeText(text);
  }
  const textarea = document.createElement("textarea");
  textarea.value = text;
  document.body.appendChild(textarea);
  textarea.select();
  document.execCommand("copy");
  document.body.removeChild(textarea);
  return Promise.resolve();
}

function renderTopNav(activeKey) {
  const nav = document.getElementById("top-nav");
  if (!nav) return;
  const links = [
    ["home", "홈", "bizaipro_home.html"],
    ["evaluation", "평가 결과", "bizaipro_evaluation_result.html"],
    ["proposal", "제안서 생성", "bizaipro_proposal_generator.html"],
    ["email", "이메일 생성", "bizaipro_email_generator.html"],
    ["compare", "엔진 버전 비교", "bizaipro_engine_compare.html"],
  ];
  nav.innerHTML = `
    <div class="top-brand-stack">
      <div class="product-lockup">
        <div class="product-title-box">FlowBizTool</div>
        <div class="engine-group">
          <div class="engine-box">Engine : <strong>BizAiPro</strong></div>
          <div class="engine-subtitle">AI 평가엔진을 도입하여 기업평가와 제안서를 자동으로 생성하는 도구</div>
        </div>
      </div>
    </div>
    <div class="nav-links">
      ${links
        .map(
          ([key, label, href]) =>
            `<a class="nav-link ${key === activeKey ? "active" : ""}" href="${href}">${label}</a>`
        )
        .join("")}
    </div>
  `;
}

function populateEngineSelect(select, activeKey) {
  if (!select) return;
  select.innerHTML = getPresetOptions()
    .map((item) => `<option value="${item.value}" ${item.value === activeKey ? "selected" : ""}>${item.label}</option>`)
    .join("");
}

function setupEngineControls(config = {}) {
  const {
    selectId = "engine-version-select",
    displayId = "engine-version-display",
    fileInputId = "web-context-file",
    onUpdate,
    defaultPreset = "latest",
  } = config;
  const select = document.getElementById(selectId);
  const display = document.getElementById(displayId);
  const fileInput = document.getElementById(fileInputId);
  const currentState = getStoredState();
  const currentPreset =
    Object.values(BIZAIPRO_ENGINE_PRESETS).find((preset) => {
      if (preset.engineVersion === "base") {
        return currentState.engineVersion === "base" || currentState.engineVersion === preset.label;
      }
      return String(currentState.engineVersion || "").includes(preset.engineVersion);
    })?.key || defaultPreset;

  populateEngineSelect(select, currentPreset);
  if (display) {
    display.textContent = formatEngineVersionLabel(currentState.engineVersion || BIZAIPRO_ENGINE_PRESETS[defaultPreset].label);
  }

  if (select) {
    select.addEventListener("change", () => {
      const state = applyPreset(select.value);
      if (display) display.textContent = formatEngineVersionLabel(state.engineVersion);
      if (typeof onUpdate === "function") onUpdate(state, { source: "preset", preset: select.value });
    });
  }

  if (fileInput) {
    fileInput.addEventListener("change", async (event) => {
      const file = event.target.files?.[0];
      if (!file) return;
      try {
        const state = await parseContextFile(file);
        if (display) display.textContent = formatEngineVersionLabel(state.engineVersion);
        if (typeof onUpdate === "function") onUpdate(state, { source: "upload", fileName: file.name });
      } catch (error) {
        window.alert("web_context.json을 읽는 중 오류가 발생했습니다.");
      }
    });
  }
}

function getCompareState(presetKey) {
  const base = getDefaultState();
  deepMerge(base, BIZAIPRO_ENGINE_PRESETS[presetKey] || BIZAIPRO_ENGINE_PRESETS.latest);
  return normalizeState(base);
}

window.BizAiProShared = {
  getDefaultState,
  getStoredState,
  saveState,
  resetForLearningMode,
  resetForExhibitionMode,
  resetState,
  applyPreset,
  applyWebContext,
  parseContextFile,
  extractExhibitionContext,
  parseFlowscoreReport,
  parseConsultingReport,
  parseInternalReview,
  parseSupportingDocument,
  parseAdditionalInfoText,
  evaluateLearningState,
  fetchDashboardSummary,
  fetchLearningCases,
  fetchLearningCase,
  getApiBaseUrl,
  inferEngineTraits,
  formatKrw,
  formatPercent,
  formatTenorText,
  formatTenorMeta,
  priorityTone,
  buildProposalText,
  buildEmailBody,
  copyText,
  renderTopNav,
  setupEngineControls,
  getPresetOptions,
  getCompareState,
  salespeople: BIZAIPRO_SALESPEOPLE,
  emailSubjects: BIZAIPRO_EMAIL_TEMPLATES.map((template) => template.titleTemplate),
  emailTemplates: BIZAIPRO_EMAIL_TEMPLATES,
  renderEmailSubject,
  formatEngineVersionLabel,
  presets: BIZAIPRO_ENGINE_PRESETS,
};
