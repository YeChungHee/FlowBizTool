# 듀얼 엔진 PR 머지 → 라이브 활성화 가이드 v2.2 [claude]

- 문서번호: FBU-GUIDE-PR-MERGE-DUAL-v2_2-20260430
- 작성일: 2026-04-30
- 작성자: [claude]
- 이전 버전: `[claude]flowbiz_dual_engine_pr_merge_activation_guide_v2_1_20260430.md` (v2.1)
- 검증: `flowbiz_dual_engine_pr_merge_activation_guide_v2_1_validation_20260430.md` (P1 2건 / P2 1건 / P3 1건 — 조건부 승인)
- 변경 사유: v2.1 검증 4건 반영 (FPE 고정 원칙 명시 + APE engine_purpose 정정 + 상담보고서 family/AppleGothic 후속 조건 추가 + git diff 베이스를 origin/main으로 변경)

## 0. v2.1 → v2.2 변경 요약

| Finding | 우선순위 | v2.1 문제 | v2.2 반영 |
|---|---|---|---|
| F1: 3차 UI PR FPE 고정 원칙 미명시 | **P1** | 3차 PR을 "UI 듀얼 카드 + proposal/email gate"라고만 표기 → 기존 샘플의 "APE/합의 평균 선택 UI"가 재사용될 위험 | **§3.3 신설** "후속 UI PR의 운영 원칙" — FPE 고정 / APE 비교 전용 / 합의 평균 선택 금지 명시 |
| F2: APE engine_purpose 명칭 오해 | **P1** | `engine_purpose: "learning_proposal"` → APE가 제안 산출에 직접 관여하는 것처럼 읽힘 | **§2.2 META 예시 정정** + **§13 코드 동반 변경 권고** (`engines/_base.py`, `engines/ape/__init__.py`, `engines/ape/README.md` 3곳) `learning_proposal` → `learning_comparison` |
| F3: 상담보고서 family / 월간 고도화 / AppleGothic 후속 조건 누락 | P2 | 후속 PR을 "월간 자동화"로만 언급 | **§3.3 후속 PR 필수 조건 7항** + **§10 매트릭스에 6개 화면 + 엔진관리 탭** 명시 |
| F4: 실측 명령이 `main...HEAD` 의존 | P3 | 로컬 main이 stale일 때 수치 차이 가능 | **§0.1 + §부록 C** `git fetch origin && git diff origin/main...HEAD --stat`로 변경 |

### 0.1 실측 검증 명령 (v2.2 정정 — F4 P3)

```bash
cd /Users/appler/Documents/COTEX/FlowBiz_ultra

# v2.2 권장 — origin/main 기준 (로컬 main stale 안전)
git fetch origin
git diff origin/main...HEAD --stat | tail -3
# → 34 files changed, 15262 insertions(+), 55 deletions(-)

git log --oneline -2
# → e16b391 feat: dual engine v2.11 — engines/ separation + dual evaluation API + UI helper
# → 081b9e7 feat: meeting_report 독립 컴포넌트(0.10) + changelog 페이지 + T19갱신/T22추가
```

> v2.1까지는 `git diff main...HEAD`였으나, 로컬 main이 origin과 다를 수 있어 v2.2부터는 `origin/main` 기준 권장.

## 1. PR 생성 + 머지 단계

### 1.1 PR 생성 (필수)

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

3. PR 생성 후 본 문서를 **v2.3로 갱신** — placeholder 갱신:
   ```diff
   - PR URL: TBD (생성 후 갱신)
   - PR 번호: TBD
   + PR URL: https://github.com/YeChungHee/FlowBizTool/pull/<번호>
   + PR 번호: #<번호>
   ```

### 1.2 PR review 후 머지 — 34개 파일 변경

머지 방식 (검토자 결정):
- **Merge commit** (권장) — 작업 이력 보존
- **Squash merge** — **34개 파일 변경**을 단일 commit으로 압축
- **Rebase merge** — linear history

### 1.3 코드 저장소 기준 즉시 사용 가능 (재시작 무관)

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

**단**: 이미 떠 있는 라이브 서버는 메모리 상의 이전 코드 사용 → §2 재시작 후 반영.

## 2. 라이브 서버 재시작 (실행 중 서버에 새 API 반영)

### 2.1 macOS 호환 재시작 절차

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

### 2.2 재시작 후 활성화되는 API 3종 (F2 P1 — APE engine_purpose 정정)

**`/api/engine/list`** — 등록된 엔진 META 노출

```json
{"engines": [
  {"engine_id": "FPE", "engine_label": "FPE_v.16.01", "engine_locked": true,
   "engine_purpose": "fixed_screening", "policy_source": "276holdings_limit_policy_manual"},
  {"engine_id": "APE", "engine_label": "APE_v1.01", "engine_locked": false,
   "engine_purpose": "learning_comparison", "policy_source": "bizaipro_learning_loop"}
]}
```

> **v2.2 정정 [F2 P1]**: APE의 `engine_purpose`를 `learning_proposal` → `learning_comparison`으로 변경.
> APE는 제안서/이메일에 직접 관여하지 않으며, FPE와의 비교 및 고도화 후보 생성 전용임을 명칭에 반영.
> **코드 동반 변경 필요** (§13 참조): `engines/_base.py:20`, `engines/ape/__init__.py:37`, `engines/ape/README.md:12` — 3곳 일괄 정정.

**`/api/evaluate/dual`** — raw flowpay_underwriting 입력 듀얼 평가
- FPE first gate 실행 → APE 평가 → agreement 5케이스 분기
- 응답: `screening` + `ape` + `agreement.consensus` + `server_input_hash`

**`/api/learning/evaluate/dual`** — UI state 입력 듀얼 평가
- `build_learning_evaluation_payload(state)` 변환 후 듀얼 평가
- proposal/email 페이지에서 호출 예정 (gate cache 미신뢰)

### 2.3 force_ape 정책 (관리자 전용)

기본 거부. `ADMIN_OVERRIDE_TOKEN` 설정 + payload `admin_token` + `override_reason` 명시 시만 우회.

```bash
export ADMIN_OVERRIDE_TOKEN="<강력한_랜덤_토큰>"
```

미설정 시 모든 force_ape 우회 자동 거부.

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

→ helper API는 준비됐지만 호출하는 UI 코드는 별도 PR.

### 3.3 후속 UI PR의 운영 원칙 (v2.2 신설 — F1 P1 + F3 P2)

3차 UI PR은 `flowbiz_dual_engine_ui_sample_20260430.md`를 그대로 구현하지 **않는다**. UI 샘플 중 APE 또는 합의 평균을 제안서/이메일 기준으로 선택하는 구조는 **폐기**한다.

> 근거: `flowbiz_dual_engine_ui_sample_validation_direction_20260430.md` Finding 1 (P0)에서 확정된 운영 원칙 — "제안서와 이메일의 기준은 항상 active FPE로 고정, APE는 비교/고도화 후보 전용"

**후속 UI PR 필수 원칙 (7항)**:

1. **제안서·이메일 기준값은 항상 active FPE 결과로 고정**한다.
2. **APE 결과와 합의 평균은 제안서/이메일 기준값으로 선택할 수 없다.**
3. **APE는 비교표, 차이 설명, 고도화 후보 저장에만 사용**한다.
4. **상담보고서와 미팅보고서는 상담보고서 family로 집계**하고 전화상담/직접상담 subtype으로 표시한다.
5. **엔진 관리 화면에 매월 30일 13:00 평가엔진고도화보고서**와 관리자 승인/보류/반려 상태(pending/approved/promoted)를 표시한다.
6. **신규 웹 UI는 AppleGothic 기반** Human Interface 기준을 따른다.
7. **결과 패널에 SourceQuality** (기업리포트/상담보고서 family/심사보고서) 영역을 추가한다.

**후속 UI PR 화면 범위 (v2.1 "3개 화면" → v2.2 "6개 화면 + 엔진관리 탭" 확장)**:

| 화면 | 반영 내용 | FPE/APE 역할 |
|---|---|---|
| `bizaipro_home.html` | FPE 결과 카드 + APE 비교 카드 + SourceQuality + 상담 family 카운트 | FPE 기준, APE 비교 |
| `bizaipro_evaluation_result.html` | FPE 기준 결과 snapshot, APE 비교표 | FPE 기준, APE 차이만 |
| `bizaipro_proposal_generator.html` | FPE snapshot 기준 생성, FPE 차단 시 disabled | FPE 단독 기준 |
| `bizaipro_email_generator.html` | FPE/proposal snapshot 기준, FPE 차단 시 disabled | FPE 단독 기준 |
| `bizaipro_engine_compare.html` | FPE vs APE 차이, 버전 비교 | 비교 전용 |
| `bizaipro_changelog.html` | FPE 승격 이력 + APE 학습 이력 | 양쪽 이력 |
| (신규) 엔진 관리 탭 | 월간 평가엔진고도화보고서 (pending/approved/promoted) | 관리자 워크플로우 |

**금지 UI 패턴** (UI 샘플에서 폐기):
```text
[X] 제안서·이메일에 사용할 엔진 선택: ( ) FPE  ( ) APE  ( ) 합의 평균
[O] 제안서·이메일 기준: FPE 평가엔진 (고정)
    APE 학습엔진 결과는 비교 및 고도화 후보로만 사용됩니다.
```

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

### 5.1 현재 repo 기준 실측 수치

```text
전체 pytest:                                    106 passed, 7 skipped
engine registry + dual consensus (targeted):    24 passed, 7 skipped
Node helper test:                                16 passed, 0 failed
closure 3구역 disjoint:                          [OK]
```

**7 skipped** = `tests/test_dual_consensus.py`의 7 케이스 (라이브 서버 8012 부재 시 skip).

> 본 문서가 "이미 확인 완료"로 읽히지 않도록 표현 유지 (v2.1 정정 계승). 7 케이스는 **현재 세션에서 통과 확인된 상태가 아니며**, 8011 또는 8012 서버 기동 후 §7의 `DUAL_SERVER_URL=http://127.0.0.1:8011 ./scripts/verify_dual_engine.sh` 실행 시 통과 여부를 검증해야 합니다.

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

### 6.1 경로 A — Fast-forward 가능
PR 브랜치가 main 위에서 분기되었고 main에 추가 commit이 없으면 그대로 머지.

### 6.2 경로 B — Conflict 발생
main의 engine.py가 변경되었으면 머지 conflict 발생 가능.

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

# 3. health check (engine_purpose: learning_comparison 확인 — F2 P1)
curl -fsS http://127.0.0.1:8011/api/engine/list | python3 -m json.tool
# → APE의 engine_purpose가 "learning_comparison"인지 확인

# 4. 종합 검증
DUAL_SERVER_URL=http://127.0.0.1:8011 ./scripts/verify_dual_engine.sh
# → [ALL OK] 9 항목 + tests/test_dual_consensus.py 7 PASSED 기대

# 5. 듀얼 평가 1회 시도
curl -fsS -X POST http://127.0.0.1:8011/api/evaluate/dual \
  -H 'Content-Type: application/json' \
  -d @tests/fixtures/v_compare/both_go_normal.json \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print('consensus:', d['agreement']['consensus'], 'fpe_gate:', d['fpe_gate_passed'])"
# → consensus: both_go, fpe_gate: True
```

## 8. 권장 진행 순서

| # | 액션 | 비고 |
|---|---|---|
| 1 | 현재 dirty worktree 정리 | `data/bizaipro_learning_registry.json`, `web/bizaipro_shared.css`, `tests/test_regression.py`, `docs/flowbiz_ultra_validation_report_registry.md` 등 |
| 2 | **§13 코드 동반 변경 적용** (F2 P1) | `engines/_base.py`, `engines/ape/__init__.py`, `engines/ape/README.md` 3곳 `learning_proposal` → `learning_comparison` |
| 3 | 실제 PR 생성 | 웹 UI에서 §1.1 절차. PR URL/번호 확보 |
| 4 | 본 가이드 v2.3로 갱신 | PR URL 실제값으로 교체 |
| 5 | PR review 후 merge | engine.py conflict 시 6 필드 채택 |
| 6 | main pull + 8011 재시작 | §2.1 macOS 호환 명령 |
| 7 | 서버 기반 검증 | `verify_dual_engine.sh` [ALL OK] 확인 — **여기서 7 consensus 케이스 PASSED 입증** |
| 8 | 후속 PR 진행 | **§3.3 7항 원칙 + 6개 화면 + 엔진관리 탭** 범위로 (UI 샘플 그대로 구현 금지) |

## 9. Rollback 시점별

| 시점 | 명령 |
|---|---|
| 머지 직후 (8011 재시작 전) | `git revert <merge-commit>` + `git push origin main` |
| 8011 재시작 후 | 위 + 서버 종료 (§2.1 macOS 호환 명령) + 이전 코드로 재기동 |
| 라이브 사용 후 | `git revert` + 영향 받은 사용자 알림 |

**금지 명령**: `git reset --hard`, `git clean -fd`, `git checkout .`

## 10. 요약 매트릭스

| 영역 | 코드 저장소 즉시 | 8011 재시작 후 | 별도 PR 필요 |
|---|:---:|:---:|:---:|
| 코드 (import 경로) | ✅ | — | — |
| 테스트 인프라 | ✅ | — | — |
| API 3종 (`/api/engine/list`, dual evaluate × 2) | — | ✅ | — |
| force_ape gate | — | ✅ (env 설정 시) | — |
| `dual_eval_helpers.js` window 노출 | ✅ (브라우저 다음 페이지 로드 시) | — | — |
| **6 화면 듀얼 카드 + SourceQuality + 상담 family** (F1+F3) | — | — | **3차 PR (§3.3 원칙)** |
| **엔진 관리 탭 (월간 고도화보고서 pending/approved/promoted)** (F3) | — | — | **3차 PR (§3.3 원칙)** |
| **AppleGothic font stack** (F3) | — | — | **3차 PR** |
| proposal/email gate 호출 (FPE 단독 기준) | — | — | **3차 PR** |
| engine.py 본체 분리 | — | — | **2차 PR (선택)** |
| ape_blocked 케이스 | — | — | **v3 (정책 결정 후)** |
| 월간 평가엔진 고도화보고서 자동화 | — | — | **별도 PR (FBU-DUAL-LIFECYCLE-0001 §8)** |

> **PR 규모**: 34개 파일 변경, 15,262 insertions / 55 deletions (origin/main 기준)

## 11. 핵심 메시지

본 PR(1차)은 **인프라 + API + helper만 활성화**합니다. UI 사용자 경험은 변경 없음 (helper script만 백그라운드 로드). 듀얼 평가는 **API 호출로만** 가능, UI 통합은 후속 3차 PR.

회귀 0건 + 9 자동 검증 항목 + (메인 기준) **106 passed + 7 skipped** + (라이브 서버 기동 후 `verify_dual_engine.sh` 실행 시 — **현 세션에서는 미검증**) +7 듀얼 consensus 케이스 통과 예정으로 **머지 안전성은 코드/테스트 인프라 측면에서 확인됨**, 서버 측 통과 여부는 머지 후 §7 시퀀스에서 입증해야 함.

**v2.2의 핵심 보강**: 후속 3차 UI PR이 UI 샘플의 잘못된 "엔진 선택 UI"를 답습하지 않도록 §3.3에 7항 원칙 + 6 화면 + 엔진관리 탭 범위를 명시. APE engine_purpose 명칭도 `learning_comparison`으로 정정해 역할을 명확히 함.

## 12. 다음 액션 (사용자 결정)

| # | 액션 | 권장 순서 |
|---|---|:---:|
| 1 | 현재 dirty worktree 정리 | 1 |
| 2 | **§13 코드 정정 (`learning_proposal` → `learning_comparison`)** | 2 |
| 3 | 실제 PR 생성 (§1.1 웹 UI) | 3 |
| 4 | 본 가이드 v2.3으로 PR URL/번호 갱신 | 4 |
| 5 | PR review + 머지 (engine.py 6필드 채택) | 5 |
| 6 | 8011 재시작 + `verify_dual_engine.sh` 검증 → 7 consensus PASSED 입증 | 6 |
| 7 | 3차 PR — **§3.3 원칙대로** UI 듀얼 카드 + 6 화면 + 엔진관리 탭 | 7 |
| 8 | 2차 PR — engine.py 본체 점진 이전 (선택) | 8 |
| 9 | v3 — ape_blocked 정책 + 월간 평가엔진 고도화보고서 자동화 | 9 |

## 13. 코드 동반 변경 (F2 P1 — 본 PR에 포함 또는 후속 hotfix)

`engine_purpose` 명칭 일관성 확보를 위해 다음 3개 파일을 정정해야 합니다.

### 13.1 변경 위치

| 파일 | 라인 | Before | After |
|---|---|---|---|
| `engines/_base.py` | 20 | `engine_purpose: str     # "fixed_screening" \| "learning_proposal"` | `engine_purpose: str     # "fixed_screening" \| "learning_comparison"` |
| `engines/ape/__init__.py` | 37 | `engine_purpose="learning_proposal",` | `engine_purpose="learning_comparison",` |
| `engines/ape/README.md` | 12 | `\| engine_purpose \| ` + "`learning_proposal`" + ` \|` | `\| engine_purpose \| ` + "`learning_comparison`" + ` \|` |

### 13.2 적용 방식 선택지

**옵션 A — 본 1차 PR에 포함** (권장)
- 장점: 한 번의 머지로 모든 META 정합성 확보, `/api/engine/list` 응답 즉시 정정
- 단점: PR 변경 파일 수 35개로 1개 증가 (현재 34 → 35)
- 작업: 3 파일 sed 또는 Edit, 회귀 테스트 재실행

**옵션 B — 후속 hotfix PR**
- 장점: 본 PR scope 변경 없음, 머지 일정 영향 없음
- 단점: 라이브 서버에 잠시 `learning_proposal` 노출, 외부 연동 시점에 따라 재정정 필요
- 작업: 별도 PR 분기 → 3 파일 정정 → 머지

### 13.3 적용 검증 (옵션 A 채택 시)

```bash
cd /Users/appler/Documents/COTEX/FlowBiz_ultra
grep -rn "learning_proposal" engines/ app.py
# → 0 hit 기대

python3 -m pytest tests/test_engine_registry.py -q
# → 24 passed (META 필드 검증 테스트 통과 유지)

python3 -m pytest tests/ -q
# → 106 passed, 7 skipped (회귀 0건)
```

> **권장**: 옵션 A. 머지 직전 3 파일 정정 + 회귀 재실행 + commit 후 PR 갱신. 총 소요 5분 이내.

---

## 부록 A. v2.1 → v2.2 정정 위치

### A.1 FPE 고정 원칙 (F1 P1)

| 위치 | v2.1 | v2.2 |
|---|---|---|
| §3 UI 변화 | "3차 PR — UI 듀얼 카드 + proposal/email gate"만 언급 | **§3.3 신설** "후속 UI PR의 운영 원칙" 7항 + 6 화면 + 금지 UI 패턴 |
| §10 매트릭스 | "UI 듀얼 카드 (좌/우 분할 + 합의 배지)" 1줄 | **6 화면 + 엔진관리 탭 + AppleGothic** 3줄 분할 |
| §12 다음 액션 #6 | "3차 PR — UI 듀얼 카드 + proposal/email gate" | "3차 PR — **§3.3 원칙대로** 6 화면 + 엔진관리 탭" |

### A.2 APE engine_purpose 명칭 (F2 P1)

| 위치 | v2.1 | v2.2 |
|---|---|---|
| §2.2 META 예시 JSON | `"engine_purpose": "learning_proposal"` | `"engine_purpose": "learning_comparison"` |
| (신규) §13 | — | 코드 동반 변경 표 + 옵션 A/B + 검증 명령 |
| §7 머지 후 검증 #3 | `engine_purpose: "learning_proposal"` 기대 | `engine_purpose: "learning_comparison"` 확인 |

### A.3 후속 PR 추가 조건 (F3 P2)

| 항목 | v2.1 | v2.2 |
|---|---|---|
| 상담보고서 family | 미언급 | §3.3 #4 — 전화상담/직접상담 subtype 표시 |
| 엔진 관리 탭 (월간 pending/approved/promoted) | "월간 자동화"만 언급 | §3.3 #5 — 매월 30일 13:00 + 3 상태 표시 |
| AppleGothic font stack | 미언급 | §3.3 #6 — Human Interface 기준 |
| SourceQuality | 미언급 | §3.3 #7 — 결과 패널 영역 추가 |

### A.4 git diff base (F4 P3)

| 위치 | v2.1 | v2.2 |
|---|---|---|
| §0.1 실측 명령 | `git diff main...HEAD --stat` | `git fetch origin && git diff origin/main...HEAD --stat` |
| 부록 C TL;DR | `git diff main...HEAD --stat` | `git fetch origin && git diff origin/main...HEAD --stat` |

## 부록 B. v1 → v2 → v2.1 → v2.2 누적 변경 추적

| Finding | 우선순위 | v1 | v2 | v2.1 | v2.2 |
|---|---|---|---|---|---|
| F1 v1: PR URL 실제값 아님 | P1 | `pull/new/...` | §1.1 PR 생성 단계 신설 | (계승) | (계승) |
| F2 v1: macOS xargs -r | P1 | 실패 가능 | PID 변수 + `[ -n "$PID" ]` | (계승) | (계승) |
| F3 v1: 테스트 수치 | P2 | "129/76" | 106/24/16 | (계승) | (계승) |
| F4 v1: 재시작 문구 | P2 | 모호 | 코드/서버 분리 | (계승) | (계승) |
| F1 v2: 파일 수 35→34 | P2 | — | "35개" | "34개" 정정 | (계승) |
| F2 v2: consensus 통과 표현 | P2 | — | "이미 통과" | "현 세션 미검증" | (계승) |
| **F1 v2.1: FPE 고정 원칙** | **P1** | — | — | 미반영 | **§3.3 7항 + 6 화면 + 금지 UI** |
| **F2 v2.1: APE engine_purpose** | **P1** | — | — | `learning_proposal` | **`learning_comparison` + §13 코드 변경** |
| **F3 v2.1: 상담 family/AppleGothic** | **P2** | — | — | 미반영 | **§3.3 #4 #5 #6 #7** |
| **F4 v2.1: git diff base** | **P3** | — | — | `main...HEAD` | **`origin/main...HEAD`** |

**누적**: v1 4건 + v2 2건 + v2.1 4건 = **총 10 Finding 모두 v2.2까지 반영**, P0/P1 잔여 0건.

## 부록 C. v2.2 실행 즉시 명령 (TL;DR)

```bash
# 1. 현재 상태 확인 (origin/main 기준 — F4 P3 정정)
cd /Users/appler/Documents/COTEX/FlowBiz_ultra
git fetch origin
git diff origin/main...HEAD --stat | tail -1   # 34 files changed 확인
git log --oneline -2                             # e16b391, 081b9e7

# 2. (옵션 A 권장) 코드 동반 변경 적용 — F2 P1
grep -rn "learning_proposal" engines/ app.py    # 변경 전 위치 확인

# (Edit으로 3개 파일 정정 후)
grep -rn "learning_proposal" engines/ app.py    # 0 hit 확인
grep -rn "learning_comparison" engines/         # 3 hit 확인

# 3. 검증 (서버 무관, 60초)
python3 -m pytest tests/ -q                      # 106 passed, 7 skipped
node scripts/test_dual_eval_helpers.js           # 16 passed
python3 scripts/extract_engine_closures.py       # 3구역 disjoint OK

# 4. 머지 후 (서버 검증, 5분)
git checkout main && git pull origin main
PID="$(lsof -ti :8011 2>/dev/null || true)"; [ -n "$PID" ] && kill $PID && sleep 1
nohup python3 -m uvicorn app:app --host 127.0.0.1 --port 8011 > /tmp/uvicorn8011.log 2>&1 &
sleep 3

# 5. APE engine_purpose 정정 검증 (F2 P1)
curl -fsS http://127.0.0.1:8011/api/engine/list | python3 -m json.tool | grep engine_purpose
# → "fixed_screening" + "learning_comparison" 2건 기대

# 6. 종합 검증
DUAL_SERVER_URL=http://127.0.0.1:8011 ./scripts/verify_dual_engine.sh
# → 여기서 7 consensus 케이스 PASSED 입증
```

## 부록 D. 후속 3차 UI PR 작업 시작 시 체크리스트 (§3.3 7항 직결)

3차 PR 첫 commit 전 다음을 확인:

- [ ] `flowbiz_dual_engine_ui_sample_validation_direction_20260430.md` 읽음
- [ ] §3.3 7항 원칙 숙지 — 특히 #1 (FPE 고정), #2 (APE 선택 금지), #3 (APE 비교 전용)
- [ ] §3.3 6 화면 + 엔진관리 탭 범위 확정
- [ ] 금지 UI 패턴 (엔진 선택 라디오) 폐기 확인
- [ ] AppleGothic font stack 적용 계획 수립
- [ ] 상담보고서 family + 전화상담/직접상담 subtype 데이터 모델 확인
- [ ] 엔진 관리 탭의 pending/approved/promoted 상태 enum 정의
- [ ] `flowbiz_dual_engine_evaluation_and_upgrade_lifecycle_plan_20260430.md` §6 화면 매트릭스와 정합성 확인

위 8 항목 모두 [O] 처리 후 3차 PR 착수.
