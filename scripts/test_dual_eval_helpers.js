#!/usr/bin/env node
/**
 * v2.11 §2.3 Step 11: 실제 web/dual_eval_helpers.js를 require해 동작 검증.
 * 0 FAIL이면 종료 코드 0.
 */

const path = require("path");
const helpers = require(path.join(__dirname, "..", "web", "dual_eval_helpers.js"));

let passed = 0, failed = 0;

function assertEq(label, actual, expected) {
  const match = JSON.stringify(actual) === JSON.stringify(expected);
  if (match) { console.log(`  PASS: ${label}`); passed++; }
  else {
    console.log(`  FAIL: ${label}`);
    console.log(`    expected: ${JSON.stringify(expected)}`);
    console.log(`    actual:   ${JSON.stringify(actual)}`);
    failed++;
  }
}

console.log("=== _stateKeyFromAnyPayload ===");
const k1 = helpers._stateKeyFromAnyPayload({ companyName: "A", businessNumber: "111" });
assertEq("UI camelCase companyName", k1.companyName, "A");
assertEq("UI camelCase businessNumber", k1.businessNumber, "111");

const k2 = helpers._stateKeyFromAnyPayload({ company_name: "B", business_number: "222" });
assertEq("raw snake_case companyName", k2.companyName, "B");
assertEq("raw snake_case businessNumber", k2.businessNumber, "222");

// nested applicant fallback (v2.6 누락 케이스, v2.7에서 추가)
const k3 = helpers._stateKeyFromAnyPayload({ applicant: { company_name: "C", business_number: "333" } });
assertEq("nested applicant companyName", k3.companyName, "C");
assertEq("nested applicant businessNumber", k3.businessNumber, "333");

console.log("\n=== inputHash changes on key field changes ===");
const a = helpers._stateKeyFromAnyPayload({ companyName: "X", reportCreditGrade: "BB+" });
const b = helpers._stateKeyFromAnyPayload({ companyName: "X", reportCreditGrade: "CCC-" });
assertEq("credit_grade change", a.inputHash !== b.inputHash, true);

// F2 v2.7: financialFilterSignal 변경 감지
const c = helpers._stateKeyFromAnyPayload({ companyName: "X", financialFilterSignal: "BB+" });
const d = helpers._stateKeyFromAnyPayload({ companyName: "X", financialFilterSignal: "CCC-" });
assertEq("financialFilterSignal change", c.inputHash !== d.inputHash, true);

const e = helpers._stateKeyFromAnyPayload({ companyName: "X", operatingProfitValue: "1000000" });
const f = helpers._stateKeyFromAnyPayload({ companyName: "X", operatingProfitValue: "2000000" });
assertEq("operatingProfitValue change", e.inputHash !== f.inputHash, true);

console.log("\n=== _stateKeyReady ===");
assertEq("all empty -> invalid", helpers._stateKeyReady({ companyName: "", businessNumber: "", flowScoreFileName: "", inputHash: "" }), false);
assertEq("companyName only -> valid", helpers._stateKeyReady({ companyName: "A", businessNumber: "", flowScoreFileName: "", inputHash: "" }), true);
assertEq("inputHash only (no identifier) -> invalid", helpers._stateKeyReady({ companyName: "", businessNumber: "", flowScoreFileName: "", inputHash: "{...}" }), false);

console.log("\n=== _stateKeyEqual ===");
const g = { companyName: "X", businessNumber: "1", flowScoreFileName: "", inputHash: "h1" };
const h = { companyName: "X", businessNumber: "1", flowScoreFileName: "", inputHash: "h1" };
const i = { companyName: "X", businessNumber: "1", flowScoreFileName: "", inputHash: "h2" };
assertEq("identical -> true", helpers._stateKeyEqual(g, h), true);
assertEq("inputHash diff -> false", helpers._stateKeyEqual(g, i), false);

console.log("\n=== CONSENSUS_LABELS ===");
assertEq("both_go label exists", typeof helpers.CONSENSUS_LABELS.both_go.text, "string");
assertEq("fpe_blocked color red", helpers.CONSENSUS_LABELS.fpe_blocked.color, "red");

console.log(`\n=== ${passed} passed, ${failed} failed ===`);
process.exit(failed > 0 ? 1 : 0);
