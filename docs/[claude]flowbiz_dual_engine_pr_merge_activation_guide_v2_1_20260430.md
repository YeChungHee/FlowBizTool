# 듀얼 엔진 PR 머지 → 라이브 활성화 가이드 v2.1 [claude]

- 문서번호: FBU-GUIDE-PR-MERGE-DUAL-v2_1-20260430
- 작성일: 2026-04-30
- 작성자: [claude]
- 이전 버전: `flowbiz_dual_engine_pr_merge_activation_guide_v2_20260430.md` (v2)
- 검증: `flowbiz_dual_engine_pr_merge_activation_guide_v2_validation_20260430.md` (P2 2건 — 조건부 승인)
- 변경 사유: v2 검증의 P2 두 건 반영 (파일 수 34개 정정 + 서버 기반 consensus 문구 “재시작 후 검증 필요”로 명확화)

## 0. v2 → v2.1 변경 요약

| Finding | 우선순위 | v2 문제 | v2.1 반영 |
|---|---|---|---|
| F1: 변경 파일 수 표기 불일치 | P2 | "35개 파일 변경" 표기 vs 실제 `git diff main...HEAD` 결과 `34 files changed` | **§1.2 + §10 모두 34개로 정정** + §0.1에 실측 명령 추가 |
| F2: 서버 기반 consensus 문구가 "이미 확인 완료"로 읽힘 | P2 | "서버 기동 후 실행 시 모두 PASSED", "+7 듀얼 consensus 통과" 표현 | **§5.1 + §11 문구 변경** — "서버 기동 후 `verify_dual_engine.sh` 통과 확인 필요"로 명확화 |

### 0.1 실측 검증 (현재 세션)

```bash
cd /Users/appler/Documents/COTEX/FlowBiz_ultra
git diff main...HEAD --stat | tail -3
# → 34 files changed, 15262 insertions(+), 55 deletions(-)

git log --oneline -2
# → e16b391 feat: dual engine v2.11 — engines/ separation + dual evaluation API + UI helper
# → 081b9e7 feat: meeting_report 독립 컴포넌트(0.10) + changelog 페이지 + T19갱신/T22추가
```

## 1. PR 생성 + 머지 단계

### 1.1 PR 생성 (필수, v2 검증 §6 1단계)

현재 push 완료 상태:
```text
브랜치: codex/dual-engine-execution-20260430 → origin/codex/dual-engine-execution-20260430
HEAD: e16b391
base: main (현 origin/main: 081b9e7)
```

**실제 PR 생성 절차** (gh CLI 미설치 — 웹 UI 사용):

1. 브라우저에서 PR 생성 URL 접속:
   ```
   https://github.com/YeChungHee/FlowBizTool/pull/new/codex/dual-engine-execution-20260430
   ```

2. PR 작성:
   - **Title**: `feat: dual engine v2.11 — engines/ separation + dual evaluation API + UI helper`
   - **Description**: `outputs/dual_engine_baseline_20260430/PR_DESCRIPTION.md` 내용 복사
   - **Base**: `main`
   - **Head**: `codex/dual-engine-execution-20260430`

3. PR 생성 후 본 문서를 **v2.2로 갱신** — placeholder 갱신:
   ```diff
   - PR URL: TBD (생성 후 갱신)
   - PR 번호: TBD
   + PR URL: https://github.com/YeChungHee/FlowBizTool/pull/<번호>
   + PR 번호: #<번호>
   ```

### 1.2 PR review 후 머지

머지 방식 (검토자가 결정):
- **Merge commit** (권장) — 작업 이력 보존
- **Squash merge** — **34개 파일 변경**(v2.1 정정)을 단일 commit으로 압축
- **Rebase merge** — linear history

### 1.3 코드 저장소 기준 즉시 사용 가능 (재시작 무관)

머지 후 main에 코드가 들어오면 다음은 즉시 사용 가능:

```python
# main 동기화 후 import 즉시 동작
from engines import get_engine, list_engines
from engines.fpe.eval import evaluate_fpe_v1601
from engines.ape.eval import evaluate_flowpay_underwriting
```

```bash
# 회귀 테스트 + 검증 스크립트 즉시 동작 (서버 무관)
python3 -m pytest tests/test_engine_registry.py -v   # 24 passed
python3 scripts/extract_engine_closures.py           # 3구역 disjoint 검증
node scripts/test_dual_eval_helpers.js               # 16 passed
```

**단**: 이미 떠 있는 라이브 서버는 메모리 상의 이전 코드를 사용 중 → §2 재시작 후 반영.

## 2. 라이브 서버 재시작 (실행 중 서버에 새 API 반영)

### 2.1 macOS 호환 재시작 절차 (v2 §2.1 유지)

```bash
cd /Users/appler/Documents/COTEX/FlowBiz_ultra

# 1. main 동기화
git checkout main && git pull origin main

# 2. macOS BSD xargs 호환 — -r 옵션 사용 안 함
PID="$(lsof -ti :8011 2>/dev/null || true)"
if [ -n "$PID" ]; then
  kill $PID
  sleep 1
fi

# 3. 신규 코드로 기동
nohup python3 -m uvicorn app:app --host 127.0.0.1 --port 8011 > /tmp/uvicorn8011.log 2>&1 &
sleep 3

# 4. health check
curl -fsS http://127.0.0.1:8011/api/engine/list | python3 -m json.tool
```

### 2.2 재시작 후 활성화되는 API 3종

**`/api/engine/list`** — 등록된 엔진 META 노출
```json
{"engines": [
  {"engine_id": "FPE", "engine_label": "FPE_v.16.01", "engine_locked": true,
   "engine_purpose": "fixed_screening", "policy_source": "276holdings_limit_policy_manual"},
  {"engine_id": "APE", "engine_label": "APE_v1.01", "engine_locked": false,
   "engine_purpose": "learning_proposal", "policy_source": "bizaipro_learning_loop"}
]}
```

**`/api/evaluate/dual`** — raw flowpay_underwriting 입력 듀얼 평가
- FPE first gate 실행 → APE 평가 → agreement 5케이스 분기
- 응답: `screening` + `ape` + `agreement.consensus` + `server_input_hash`

**`/api/learning/evaluate/dual`** — UI state 입력 듀얼 평가
- `build_learning_evaluation_payload(state)` 변환 후 듀얼 평가
- proposal/email 페이지에서 호출 예정 (gate cache 미신뢰)

### 2.3 force_ape 정책 (관리자 전용)

기본 거부. 환경변수 `ADMIN_OVERRIDE_TOKEN` 설정 + payload에 `admin_token` + `override_reason` 명시 시만 우회.

```bash
# 운영 시작 전 (선택)
export ADMIN_OVERRIDE_TOKEN="<강력한_랜덤_토큰>"
```

미설정 시 모든 force_ape 우회 자동 거부 (기본 안전).

## 3. UI 변화 (브라우저 사용자 시점)

### 3.1 즉시 활성화 (다음 페이지 로드 시)
- **6 HTML에 `dual_eval_helpers.js` 자동 로드** (`bizaipro_shared.js` 직전)
- `window.FlowBizDualEvalHelpers` 네임스페이스 사용 가능
- 브라우저 콘솔 에러 없음 — 회귀 안전

### 3.2 미활성화 (별도 3차 PR 필요)
- 결과 패널 좌(FPE)/우(APE) 듀얼 카드
- 합의 배지 5케이스 (both_go / fpe_blocked / ape_only_positive / ape_blocked / both_review)
- proposal/email 페이지 진입 시 `ensureDualEvaluation()` 가드 호출
- 차단 배너 + 폼 disabled

→ helper API는 준비됐지만 호출하는 UI 코드는 별도 PR에서 추가.

## 4. 데이터 변화

```
data/
├── fpe_v1601_policy.json           ← legacy 그대로 (1개월 보존)
├── active_framework.json           ← 운영 그대로
└── engines/                        ← 신규
    ├── fpe/policy.json             (legacy copy, dual-read 우선)
    └── ape/
        ├── frameworks/_baseline.json
        └── learning_registry.json  (legacy copy)
```

`engines/fpe/policy.py`가 신규 경로 우선 → legacy fallback. 기존 코드 동작 무영향.

## 5. 회귀 안전성 (현재 repo 기준 실측)

### 5.1 현재 repo 기준 실측 수치 (F2 P2 — 문구 명확화)

```text
전체 pytest:                                    106 passed, 7 skipped
engine registry + dual consensus (targeted):    24 passed, 7 skipped
Node helper test:                                16 passed, 0 failed
closure 3구역 disjoint:                          [OK]
```

**7 skipped** = `tests/test_dual_consensus.py`의 7 케이스 (라이브 서버 8012 부재 시 skip).

> **v2.1 정정**: 본 문서가 "이미 확인 완료"로 읽히지 않도록 표현을 변경합니다. 7 케이스는 **현재 세션에서 통과 확인된 상태가 아니며**, 8011 또는 8012 서버 기동 후 §7의 `DUAL_SERVER_URL=http://127.0.0.1:8011 ./scripts/verify_dual_engine.sh` 실행 시 통과 여부를 검증해야 합니다.

### 5.2 회귀 안전 검증 항목

| 항목 | 결과 |
|---|---|
| 기존 76 테스트 (pre-PR) | 통과 (회귀 0건) |
| T24 (FPE) 4 케이스 | PASSED 동일 결과 |
| 4가지 import 경로 | engine first / engines first / fpe direct / ape direct 모두 OK |
| view↛eval 단방향 | engines/fpe/view.py에 `from .eval` 부재 ✓ |
| 6 HTML 로드 순서 | dual_eval_helpers.js < bizaipro_shared.js 통과 |
| circular import | 4 경로 모두 통과 |

## 6. ⚠ 머지 전 확인 필요 — engine.py 충돌 가능성

본 PR은 `engine.py`에 다음 변경 포함:
- `get_active_framework_meta()` 6 필드로 보강 (3 → 6: version/engine_id/engine_label 추가)
- `compute_report_base_limit()` 신규 함수 추가

**메인 main의 `engine.py` 상태가 baseline(3 필드, compute_report_base_limit 부재)로 되돌아가 있다면** 머지 시 두 경로:

### 6.1 경로 A — Fast-forward 가능
PR 브랜치가 main 위에서 분기되었고 main에 추가 commit이 없으면 그대로 머지. 단순.

### 6.2 경로 B — Conflict 발생
main의 engine.py가 변경되었으면 머지 conflict 발생 가능. 해결:

```bash
git checkout main
git merge codex/dual-engine-execution-20260430
# conflict 발생 시 engine.py 수동 병합 → 6 필드 버전 채택 권장
```

**6 필드 버전 채택 권장 이유**:
- `tests/test_engine_registry.py`의 `test_get_active_framework_meta_includes_version`이 6 필드 가정
- 3 필드로 되돌리면 24개 registry 테스트 중 일부 실패
- `compute_report_base_limit` 부재 시 `test_compute_report_base_limit_works` 실패

## 7. 머지 후 검증 시퀀스 (macOS 호환)

```bash
cd /Users/appler/Documents/COTEX/FlowBiz_ultra

# 1. 머지된 main 동기화
git checkout main && git pull origin main

# 2. 서버 재시작 (macOS 호환)
PID="$(lsof -ti :8011 2>/dev/null || true)"
if [ -n "$PID" ]; then
  kill $PID
  sleep 1
fi
nohup python3 -m uvicorn app:app --host 127.0.0.1 --port 8011 > /tmp/uvicorn8011.log 2>&1 &
sleep 3

# 3. health check
curl -fsS http://127.0.0.1:8011/api/engine/list | python3 -m json.tool
# → FPE + APE 양쪽 META 확인

# 4. 종합 검증 (DUAL_SERVER_URL=8011 override) — 7 consensus 케이스 통과 확인
DUAL_SERVER_URL=http://127.0.0.1:8011 ./scripts/verify_dual_engine.sh
# → [ALL OK] 9 항목 + tests/test_dual_consensus.py 7 PASSED 기대

# 5. 듀얼 평가 1회 시도
curl -fsS -X POST http://127.0.0.1:8011/api/evaluate/dual \
  -H 'Content-Type: application/json' \
  -d @tests/fixtures/v_compare/both_go_normal.json \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print('consensus:', d['agreement']['consensus'], 'fpe_gate:', d['fpe_gate_passed'])"
# → consensus: both_go, fpe_gate: True
```

## 8. 권장 진행 순서 (v2 검증 §6 채택)

| # | 액션 | 비고 |
|---|---|---|
| 1 | 현재 dirty worktree 정리 | `data/bizaipro_learning_registry.json`, `web/bizaipro_shared.css`, `tests/test_regression.py`, `docs/flowbiz_ultra_validation_report_registry.md` 등 |
| 2 | 실제 PR 생성 | 웹 UI에서 §1.1 절차. PR URL/번호 확보 |
| 3 | 본 가이드 v2.2로 갱신 | PR URL 실제값으로 교체 |
| 4 | PR review 후 merge | engine.py conflict 시 6 필드 채택 |
| 5 | main pull + 8011 재시작 | §2.1 macOS 호환 명령 |
| 6 | 서버 기반 검증 | `verify_dual_engine.sh` [ALL OK] 확인 — **여기서 비로소 7 consensus 케이스 PASSED 입증** |
| 7 | 후속 PR 진행 | UI 듀얼 카드, proposal/email gate, 월간 평가엔진 고도화보고서 자동화 |

## 9. Rollback 시점별

| 시점 | 명령 |
|---|---|
| 머지 직후 (8011 재시작 전) | `git revert <merge-commit>` + `git push origin main` |
| 8011 재시작 후 | 위 + 서버 종료 (§2.1 macOS 호환 명령) + 이전 코드로 재기동 |
| 라이브 사용 후 | `git revert` + 영향 받은 사용자 알림 (회귀 0건이므로 영향 작음) |

**금지 명령** (재확인): `git reset --hard`, `git clean -fd`, `git checkout .`

## 10. 요약 매트릭스

| 영역 | 코드 저장소 즉시 | 8011 재시작 후 | 별도 PR 필요 |
|---|:---:|:---:|:---:|
| 코드 (import 경로) | ✅ | — | — |
| 테스트 인프라 | ✅ | — | — |
| API 3종 (`/api/engine/list`, dual evaluate × 2) | — | ✅ | — |
| force_ape gate | — | ✅ (env 설정 시) | — |
| `dual_eval_helpers.js` window 노출 | ✅ (브라우저 다음 페이지 로드 시) | — | — |
| UI 듀얼 카드 (좌/우 분할 + 합의 배지) | — | — | **3차 PR** |
| proposal/email gate 호출 | — | — | **3차 PR** |
| engine.py 본체 분리 | — | — | **2차 PR (선택)** |
| ape_blocked 케이스 | — | — | **v3 (정책 결정 후)** |
| 월간 평가엔진 고도화보고서 자동화 | — | — | **별도 PR (FBU-DUAL-LIFECYCLE-0001 §8)** |

> **PR 규모**: **34개 파일 변경**(v2.1 정정), 15,262 insertions / 55 deletions

## 11. 핵심 메시지 (F2 P2 문구 정정)

본 PR(1차)은 **인프라 + API + helper만 활성화**합니다. UI 사용자 경험은 변경 없음 (helper script만 백그라운드 로드). 듀얼 평가는 **API 호출로만** 가능, UI 통합은 후속 3차 PR.

회귀 0건 + 9 자동 검증 항목 + (메인 기준) **106 passed + 7 skipped** + (라이브 서버 기동 후 `verify_dual_engine.sh` 실행 시 — **현 세션에서는 미검증**) +7 듀얼 consensus 케이스 통과 예정으로 **머지 안전성은 코드/테스트 인프라 측면에서 확인됨**, 서버 측 통과 여부는 머지 후 §7 시퀀스에서 입증해야 함.

v2 검증보고서 §7 명시: *"v2 가이드는 실행용 문서로 거의 정리되었다. 남은 문제는 치명적인 설계 오류가 아니라 문구/수치 정합성이다."* — v2.1에서 그 문구/수치 정합성을 마무리합니다.

## 12. 다음 액션 (사용자 결정)

| # | 액션 | 권장 순서 |
|---|---|:---:|
| 1 | 현재 dirty worktree 정리 (사용자 진행 중 작업) | 1 |
| 2 | 실제 PR 생성 (§1.1 웹 UI) | 2 |
| 3 | 본 가이드 v2.2로 PR URL/번호 갱신 | 3 |
| 4 | PR review + 머지 (engine.py 6필드 채택) | 4 |
| 5 | 8011 재시작 + `verify_dual_engine.sh` 검증 → 7 consensus 케이스 PASSED 입증 | 5 |
| 6 | 3차 PR — UI 듀얼 카드 + proposal/email gate | 6 |
| 7 | 2차 PR — engine.py 본체 점진 이전 (선택) | 7 |
| 8 | v3 — ape_blocked 정책 + 월간 평가엔진 고도화보고서 자동화 | 8 |

---

## 부록 A. v2 → v2.1 정정 위치

### A.1 파일 수 (35 → 34)

| 위치 | v2 | v2.1 |
|---|---|---|
| §1.2 머지 방식 | "Squash merge — 35개 파일 변경" | "Squash merge — **34개 파일 변경**(v2.1 정정)" |
| §10 요약 매트릭스 끝 | (없음) | "**PR 규모**: 34개 파일 변경, 15,262 insertions / 55 deletions" 추가 |
| §11 핵심 메시지 | (없음) | (변경 없음 — 파일 수 표기 없음) |

### A.2 서버 기반 consensus 문구

| 위치 | v2 | v2.1 |
|---|---|---|
| §5.1 끝 | "서버 기동 후 실행 시 모두 PASSED" | "현재 세션에서 통과 확인된 상태가 아니며, 서버 기동 후 verify_dual_engine.sh 실행 시 통과 여부를 검증해야 합니다" |
| §11 핵심 메시지 | "(라이브 서버 기동 시) +7 듀얼 consensus 통과로 머지 안전성 검증 완료" | "(라이브 서버 기동 후 verify_dual_engine.sh 실행 시 — 현 세션에서는 미검증) +7 듀얼 consensus 케이스 통과 예정으로 머지 안전성은 코드/테스트 인프라 측면에서 확인됨, 서버 측 통과 여부는 머지 후 §7 시퀀스에서 입증해야 함" |

## 부록 B. v1 → v2 → v2.1 누적 변경 추적

| Finding | 우선순위 | v1 | v2 반영 | v2.1 반영 |
|---|---|---|---|---|
| F1 PR URL 실제값 아님 | P1 | `pull/new/...` | §1.1 PR 생성 단계 신설 | (그대로) |
| F2 macOS xargs -r 미지원 | P1 | `lsof -i :8011 -t \| xargs -r kill` | `lsof -ti` + PID 변수 + `[ -n "$PID" ]` | (그대로) |
| F3 테스트 수치 불일치 | P2 | "129/76" | 106/24/16으로 갱신 | (그대로) |
| F4 재시작 문구 모호 | P2 | "서버 재시작 불필요" | 코드 저장소 vs 실행 중 서버 분리 | (그대로) |
| F1 (v2) 변경 파일 수 (35 vs 34) | P2 | — | "35개" 표기 | **§1.2 + §10 모두 34개로 정정** |
| F2 (v2) consensus 통과가 "이미 확인 완료"로 읽힘 | P2 | — | "서버 기동 후 모두 PASSED" | **§5.1 + §11 "현 세션 미검증, 머지 후 §7에서 입증"으로 명확화** |

## 부록 C. v2.1 실행 즉시 명령 (TL;DR)

```bash
# 1. 현재 상태 확인 (실측 수치 재확인 — 30초)
cd /Users/appler/Documents/COTEX/FlowBiz_ultra
git diff main...HEAD --stat | tail -1   # 34 files changed 확인
git log --oneline -2                     # e16b391, 081b9e7 확인

# 2. 검증 (서버 무관, 60초)
python3 -m pytest tests/ -q              # 106 passed, 7 skipped
node scripts/test_dual_eval_helpers.js   # 16 passed
python3 scripts/extract_engine_closures.py  # 3구역 disjoint OK

# 3. 머지 후 (서버 검증, 5분)
git checkout main && git pull origin main
PID="$(lsof -ti :8011 2>/dev/null || true)"; [ -n "$PID" ] && kill $PID && sleep 1
nohup python3 -m uvicorn app:app --host 127.0.0.1 --port 8011 > /tmp/uvicorn8011.log 2>&1 &
sleep 3
curl -fsS http://127.0.0.1:8011/api/engine/list | python3 -m json.tool
DUAL_SERVER_URL=http://127.0.0.1:8011 ./scripts/verify_dual_engine.sh
# → 여기서 비로소 7 consensus 케이스 PASSED 입증
```
