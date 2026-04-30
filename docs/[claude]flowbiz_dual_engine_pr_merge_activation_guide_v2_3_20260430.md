# 듀얼 엔진 PR 머지 → 라이브 활성화 가이드 v2.3 [claude]

- 문서번호: FBU-GUIDE-PR-MERGE-DUAL-v2_3-20260430
- 작성일: 2026-04-30
- 작성자: [claude]
- 이전 버전: `[claude]flowbiz_dual_engine_pr_merge_activation_guide_v2_2_20260430.md` (v2.2)
- 검증: `[codex]flowbiz_dual_engine_pr_merge_activation_guide_v2_2_validation_20260430.md` (P1 1건 / P2 1건 — 조건부 승인)
- 변경 사유: v2.2 [codex] 검증 2건 반영 — 코드 변경 대상에 `tests/test_engine_registry.py` 추가 + PR 규모를 "34 고정값" → "현재 34, 옵션 A 적용 후 재측정"으로 정정

## 0. v2.2 → v2.3 변경 요약

| Finding | 우선순위 | v2.2 문제 | v2.3 반영 |
|---|---|---|---|
| F1 [codex]: 코드 변경 목록에서 테스트 누락 | **P1** | §13에 `engines/_base.py`, `engines/ape/__init__.py`, `engines/ape/README.md` 3 파일만 적시 → 실제로 `tests/test_engine_registry.py:65`도 `learning_proposal` 기대 → 3 파일만 변경 시 테스트 실패 | **§13.1 변경 위치 4 파일로 확장** + §13.3 검증 명령에 `rg -n "learning_proposal" engines tests app.py` 추가 (engines + **tests** 동시 검사) |
| F2 [codex]: 옵션 A 적용 시 PR 규모 재측정 누락 | P2 | §1.2 + §10에서 "34개 파일 변경"을 고정값처럼 사용 → 옵션 A 적용 후 35개 이상으로 바뀌면 v2.1에서 고친 "파일 수 불일치" 문제 재발 | **§1.2 + §10 + 부록 표기 정정** "현재 기준 34개, 옵션 A 포함 시 재측정 후 v2.4 갱신" + 최종 PR description은 `git diff origin/main...HEAD --stat \| tail -1` 결과 사용 명시 |

### 0.1 [codex] 실측으로 확정된 4 파일 위치

```text
engines/_base.py:20                       # META 주석
engines/ape/__init__.py:37                # engine_purpose="learning_proposal"
engines/ape/README.md:12                  # README META 표
tests/test_engine_registry.py:65          # assert ape.META.engine_purpose == "learning_proposal"
```

본 세션 재실측:
```bash
$ grep -rn "learning_proposal" engines tests app.py 2>/dev/null
engines/_base.py:20:    engine_purpose: str     # "fixed_screening" | "learning_proposal"
engines/ape/README.md:12:| engine_purpose | `learning_proposal` |
engines/ape/__init__.py:37:    engine_purpose="learning_proposal",
tests/test_engine_registry.py:65:        assert ape.META.engine_purpose == "learning_proposal"
# → 4 hit (engines 3 + tests 1) — [codex] 검증과 일치
```

### 0.2 실측 검증 명령 (origin/main 기준 — v2.2 §0.1 계승)

```bash
cd /Users/appler/Documents/COTEX/FlowBiz_ultra

# 현재 PR 규모 (옵션 A 미적용 상태)
git fetch origin
git diff origin/main...HEAD --stat | tail -3
# → 34 files changed, 15262 insertions(+), 55 deletions(-)

# 코드/테스트의 learning_proposal 잔존 (4 hit 기대)
grep -rn "learning_proposal" engines tests app.py
```

## 1. PR 생성 + 머지 단계

### 1.1 PR 생성

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
   - **Description**: `outputs/dual_engine_baseline_20260430/PR_DESCRIPTION.md` 내용 복사 + **옵션 A 적용 시 PR description의 파일 수 갱신**
   - **Base**: `main`
   - **Head**: `codex/dual-engine-execution-20260430`

3. PR 생성 후 본 문서를 **v2.4로 갱신** — placeholder + PR 규모 갱신:
   ```diff
   - PR URL: TBD (생성 후 갱신)
   - PR 번호: TBD
   - PR 규모: 현재 34개 (옵션 A 미적용 상태)
   + PR URL: https://github.com/YeChungHee/FlowBizTool/pull/<번호>
   + PR 번호: #<번호>
   + PR 규모: <옵션 A 적용 후 재측정 결과>
   ```

### 1.2 PR review 후 머지 (F2 [codex] P2 정정)

머지 방식 (검토자 결정):
- **Merge commit** (권장) — 작업 이력 보존
- **Squash merge** — 변경 파일을 단일 commit으로 압축
- **Rebase merge** — linear history

> **PR 규모 표기 (v2.3 정정)**: 현재 기준 **34개 파일 변경**. 단, §13 옵션 A를 본 PR에 포함하면 4 파일이 추가 수정되어 파일 수가 **재측정 필요**. 최종 PR 설명에는 다음 명령 결과를 사용:
> ```bash
> git fetch origin && git diff origin/main...HEAD --stat | tail -1
> ```
> 옵션 A 적용 후 결과를 v2.4 문서에 반영.

### 1.3 코드 저장소 기준 즉시 사용 가능

```python
# main 동기화 후 import 즉시 동작
from engines import get_engine, list_engines
from engines.fpe.eval import evaluate_fpe_v1601
from engines.ape.eval import evaluate_flowpay_underwriting
```

```bash
python3 -m pytest tests/test_engine_registry.py -v   # 24 passed
python3 scripts/extract_engine_closures.py           # 3구역 disjoint 검증
node scripts/test_dual_eval_helpers.js               # 16 passed
```

## 2. 라이브 서버 재시작

### 2.1 macOS 호환 재시작 절차

```bash
cd /Users/appler/Documents/COTEX/FlowBiz_ultra
git checkout main && git pull origin main

PID="$(lsof -ti :8011 2>/dev/null || true)"
if [ -n "$PID" ]; then
  kill $PID
  sleep 1
fi

nohup python3 -m uvicorn app:app --host 127.0.0.1 --port 8011 > /tmp/uvicorn8011.log 2>&1 &
sleep 3

curl -fsS http://127.0.0.1:8011/api/engine/list | python3 -m json.tool
```

### 2.2 재시작 후 활성화되는 API 3종

**`/api/engine/list`** — 옵션 A 적용 후 응답:

```json
{"engines": [
  {"engine_id": "FPE", "engine_label": "FPE_v.16.01", "engine_locked": true,
   "engine_purpose": "fixed_screening", "policy_source": "276holdings_limit_policy_manual"},
  {"engine_id": "APE", "engine_label": "APE_v1.01", "engine_locked": false,
   "engine_purpose": "learning_comparison", "policy_source": "bizaipro_learning_loop"}
]}
```

> APE의 `engine_purpose`가 **`learning_comparison`** (옵션 A 적용 시). 옵션 B 채택 시 잠시 `learning_proposal` 잔존 → 후속 hotfix 후 정정.

**`/api/evaluate/dual`** — raw 입력 듀얼 평가
**`/api/learning/evaluate/dual`** — UI state 입력 듀얼 평가

### 2.3 force_ape 정책 (관리자 전용)

기본 거부. `ADMIN_OVERRIDE_TOKEN` + payload `admin_token` + `override_reason` 명시 시만 우회.

## 3. UI 변화

### 3.1 즉시 활성화 — 6 HTML에 `dual_eval_helpers.js` 자동 로드

### 3.2 미활성화 — 별도 3차 PR 필요

### 3.3 후속 UI PR의 운영 원칙 (v2.2 신설 — 그대로 계승)

**필수 7항**:
1. 제안서·이메일 기준값은 항상 active **FPE 고정**
2. APE 결과/합의 평균은 **선택 불가**
3. APE는 **비교/고도화 후보 전용**
4. 상담보고서 family (전화상담/직접상담 subtype)
5. 엔진관리 탭 (월간 30일 13:00 KST + pending/approved/promoted)
6. **AppleGothic** Human Interface 기준
7. SourceQuality 영역

**6 화면 + 엔진관리 탭 범위**:

| 화면 | 반영 내용 | FPE/APE 역할 |
|---|---|---|
| `bizaipro_home.html` | FPE 결과 + APE 비교 + SourceQuality + 상담 family | FPE 기준, APE 비교 |
| `bizaipro_evaluation_result.html` | FPE 기준 snapshot + APE 비교표 | FPE 기준, APE 차이만 |
| `bizaipro_proposal_generator.html` | FPE snapshot 기준, FPE 차단 시 disabled | FPE 단독 |
| `bizaipro_email_generator.html` | FPE/proposal snapshot 기준 | FPE 단독 |
| `bizaipro_engine_compare.html` | FPE vs APE 차이, 버전 비교 | 비교 전용 |
| `bizaipro_changelog.html` | FPE 승격 + APE 학습 이력 | 양쪽 이력 |
| (신규) 엔진 관리 탭 | 월간 평가엔진고도화보고서 (pending/approved/promoted) | 관리자 워크플로우 |

**금지 UI 패턴**:
```text
[X] 엔진 선택 라디오 ( ) FPE  ( ) APE  ( ) 합의 평균
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

## 5. 회귀 안전성

### 5.1 현재 repo 기준 실측 수치

```text
전체 pytest:                                    106 passed, 7 skipped
engine registry + dual consensus (targeted):    24 passed, 7 skipped
Node helper test:                                16 passed, 0 failed
closure 3구역 disjoint:                          [OK]
```

> 옵션 A 적용 시 `tests/test_engine_registry.py:65` 동시 수정 필수. 미수정 시 1 케이스 실패로 24→23 passed로 떨어짐.

### 5.2 회귀 안전 검증 항목

| 항목 | 결과 |
|---|---|
| 기존 76 테스트 (pre-PR) | 통과 (회귀 0건) |
| T24 (FPE) 4 케이스 | PASSED 동일 결과 |
| 4가지 import 경로 | 모두 OK |
| view↛eval 단방향 | ✓ |
| 6 HTML 로드 순서 | dual_eval_helpers.js < bizaipro_shared.js |
| circular import | 4 경로 통과 |

## 6. ⚠ 머지 전 확인 — engine.py 충돌 가능성

(v2.2 §6 그대로 — 변경 없음)

- `get_active_framework_meta()` 6 필드 보강
- `compute_report_base_limit()` 신규
- conflict 발생 시 **6 필드 버전 채택 권장**

## 7. 머지 후 검증 시퀀스

```bash
cd /Users/appler/Documents/COTEX/FlowBiz_ultra
git checkout main && git pull origin main

PID="$(lsof -ti :8011 2>/dev/null || true)"
if [ -n "$PID" ]; then kill $PID && sleep 1; fi
nohup python3 -m uvicorn app:app --host 127.0.0.1 --port 8011 > /tmp/uvicorn8011.log 2>&1 &
sleep 3

# APE engine_purpose 정정 검증 (옵션 A 적용 시)
curl -fsS http://127.0.0.1:8011/api/engine/list | python3 -m json.tool | grep engine_purpose
# → "fixed_screening" + "learning_comparison" 2건 (옵션 A 적용 시)

# 종합 검증
DUAL_SERVER_URL=http://127.0.0.1:8011 ./scripts/verify_dual_engine.sh

# 듀얼 평가 1회
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
| 2 | **§13 코드 변경 적용 (4 파일)** | F1 [codex] P1 — `tests/test_engine_registry.py:65` 포함 |
| 3 | **§13.4 PR 규모 재측정** | F2 [codex] P2 — `git diff origin/main...HEAD --stat \| tail -1` 결과 → v2.4 |
| 4 | 실제 PR 생성 | 웹 UI에서 §1.1 절차 |
| 5 | v2.4로 갱신 | PR URL/번호 + 재측정한 PR 규모 |
| 6 | PR review 후 merge | engine.py 6필드 채택 |
| 7 | main pull + 8011 재시작 | §2.1 macOS 호환 |
| 8 | 서버 기반 검증 | `verify_dual_engine.sh` [ALL OK] + 7 consensus PASSED 입증 |
| 9 | 후속 PR | §3.3 7항 + 6 화면 + 엔진관리 탭 |

## 9. Rollback 시점별

| 시점 | 명령 |
|---|---|
| 머지 직후 (8011 재시작 전) | `git revert <merge-commit>` + `git push origin main` |
| 8011 재시작 후 | 위 + 서버 종료 (§2.1 macOS 명령) + 이전 코드로 재기동 |
| 라이브 사용 후 | `git revert` + 영향 받은 사용자 알림 |

**금지 명령**: `git reset --hard`, `git clean -fd`, `git checkout .`

## 10. 요약 매트릭스 (F2 [codex] P2 정정)

| 영역 | 코드 저장소 즉시 | 8011 재시작 후 | 별도 PR 필요 |
|---|:---:|:---:|:---:|
| 코드 (import 경로) | ✅ | — | — |
| 테스트 인프라 | ✅ | — | — |
| API 3종 | — | ✅ | — |
| force_ape gate | — | ✅ (env 설정 시) | — |
| `dual_eval_helpers.js` window 노출 | ✅ | — | — |
| 6 화면 듀얼 카드 + SourceQuality + 상담 family | — | — | **3차 PR (§3.3)** |
| 엔진 관리 탭 (월간 고도화) | — | — | **3차 PR (§3.3)** |
| AppleGothic font stack | — | — | **3차 PR** |
| proposal/email gate (FPE 단독 기준) | — | — | **3차 PR** |
| engine.py 본체 분리 | — | — | **2차 PR (선택)** |
| ape_blocked 케이스 | — | — | **v3** |
| 월간 평가엔진 고도화보고서 자동화 | — | — | **별도 PR** |

> **PR 규모 (v2.3 정정)**: **현재 기준 34개 파일 변경**, 15,262 insertions / 55 deletions (`origin/main` 기준).
> §13 옵션 A 적용 시 4 파일 추가 수정 → **재측정 필요**. 최종 수치는 v2.4에서 갱신.

## 11. 핵심 메시지

본 PR(1차)은 **인프라 + API + helper만 활성화**. UI 사용자 경험 변경 없음. 듀얼 평가는 API 호출로만, UI 통합은 후속 3차 PR.

회귀 0건 + 9 자동 검증 + (메인 기준) **106 passed + 7 skipped** + (옵션 A 적용 시) `learning_comparison` 정합성 확보 + (라이브 서버 기동 후 — 현 세션 미검증) +7 듀얼 consensus 케이스 통과 예정.

**v2.3의 핵심 보강**:
- F1 [codex] P1: 코드 변경 대상에 `tests/test_engine_registry.py:65` 추가 (3 → 4 파일)
- F2 [codex] P2: PR 규모를 "34 고정값" → "현재 34, 옵션 A 후 재측정"으로 표기 변경
- v2.1에서 고친 파일 수 정합성 문제가 옵션 A 적용 시 재발하지 않도록 **재측정 절차 명시**

## 12. 다음 액션 (사용자 결정)

| # | 액션 | 권장 순서 |
|---|---|:---:|
| 1 | 현재 dirty worktree 정리 | 1 |
| 2 | **§13 코드 정정 (4 파일 일괄)** | 2 |
| 3 | **§13.4 PR 규모 재측정** | 3 |
| 4 | 실제 PR 생성 | 4 |
| 5 | 본 가이드 v2.4로 PR URL/번호/규모 갱신 | 5 |
| 6 | PR review + 머지 | 6 |
| 7 | 8011 재시작 + 검증 | 7 |
| 8 | 3차 PR — §3.3 원칙대로 6 화면 + 엔진관리 탭 | 8 |
| 9 | 2차 PR — engine.py 본체 점진 이전 (선택) | 9 |
| 10 | v3 — ape_blocked 정책 + 월간 자동화 | 10 |

## 13. 코드 동반 변경 (F1 [codex] P1 — 테스트 포함)

`engine_purpose` 명칭 일관성 확보를 위해 **4개 파일**을 일괄 정정합니다.

### 13.1 변경 위치 (v2.3 정정 — 4 파일)

| 파일 | 라인 | Before | After |
|---|---|---|---|
| `engines/_base.py` | 20 | `engine_purpose: str     # "fixed_screening" \| "learning_proposal"` | `engine_purpose: str     # "fixed_screening" \| "learning_comparison"` |
| `engines/ape/__init__.py` | 37 | `engine_purpose="learning_proposal",` | `engine_purpose="learning_comparison",` |
| `engines/ape/README.md` | 12 | `\| engine_purpose \| ` + "`learning_proposal`" + ` \|` | `\| engine_purpose \| ` + "`learning_comparison`" + ` \|` |
| **`tests/test_engine_registry.py`** | **65** | `assert ape.META.engine_purpose == "learning_proposal"` | `assert ape.META.engine_purpose == "learning_comparison"` |

> **v2.2 → v2.3 차이**: 4번째 행 `tests/test_engine_registry.py:65`가 추가됨. v2.2처럼 3 파일만 변경하면 본 테스트가 실패하여 `24 passed` → `23 passed, 1 failed`로 회귀 발생.

### 13.2 적용 방식 선택지

**옵션 A — 본 1차 PR에 포함** (권장)
- 장점: 한 번의 머지로 모든 META 정합성 확보, `/api/engine/list` 응답 즉시 정정, 테스트 동시 통과
- 단점: PR 변경 파일 수가 34개에서 변동 — **재측정 필요** (3 파일은 PR에 이미 포함되어 있는지에 따라 +1~+4)
- 작업: 4 파일 Edit + 회귀 테스트 재실행 + `git diff origin/main...HEAD --stat` 재측정

**옵션 B — 후속 hotfix PR**
- 장점: 본 PR scope 변경 없음, 머지 일정 영향 없음
- 단점: 라이브 서버에 잠시 `learning_proposal` 노출, 외부 연동 시점에 따라 재정정 필요
- 작업: 별도 PR 분기 → 4 파일 정정 → 머지

### 13.3 적용 검증 (옵션 A 채택 시)

```bash
cd /Users/appler/Documents/COTEX/FlowBiz_ultra

# 변경 전 잔존 위치 확인 (4 hit 기대)
grep -rn "learning_proposal" engines tests app.py
# → engines/_base.py:20, engines/ape/__init__.py:37, engines/ape/README.md:12, tests/test_engine_registry.py:65

# (Edit으로 4 파일 정정 후)

# 변경 후 0 hit 기대 (engines + tests + app.py 전체)
grep -rn "learning_proposal" engines tests app.py
# → 0 hit

# learning_comparison 4 hit 기대
grep -rn "learning_comparison" engines tests
# → 4 hit

# 테스트 재실행 — 24 passed 유지 확인
python3 -m pytest tests/test_engine_registry.py -q
# → 24 passed (테스트 동시 수정으로 통과)

# 전체 회귀
python3 -m pytest tests/ -q
# → 106 passed, 7 skipped
```

### 13.4 PR 규모 재측정 (F2 [codex] P2 신설)

옵션 A 적용 후 반드시 PR 규모 재측정:

```bash
cd /Users/appler/Documents/COTEX/FlowBiz_ultra
git fetch origin
git diff origin/main...HEAD --stat | tail -1
# → "<N> files changed, <X> insertions(+), <Y> deletions(-)"
```

재측정 결과를 다음 위치에 반영:

| 갱신 위치 | 갱신 방법 |
|---|---|
| 본 가이드 §1.2 PR 규모 표기 | "<N>개 파일 변경"으로 갱신 (v2.4) |
| 본 가이드 §10 매트릭스 끝 PR 규모 | 동일 |
| `outputs/dual_engine_baseline_20260430/PR_DESCRIPTION.md` | 동일 |
| GitHub PR description (생성 후) | 동일 |

**중요**: v2.1에서 고친 "파일 수 35 → 34" 정합성 문제가 옵션 A 적용 후 재발하지 않도록, **재측정 후 모든 표기를 동일 수치로 통일**.

### 13.5 옵션 A 적용 단일 명령 (참고)

```bash
cd /Users/appler/Documents/COTEX/FlowBiz_ultra

# 4 파일 sed 일괄 (macOS BSD sed 호환 — -i '' 사용)
sed -i '' 's/learning_proposal/learning_comparison/g' \
  engines/_base.py \
  engines/ape/__init__.py \
  engines/ape/README.md \
  tests/test_engine_registry.py

# 검증
grep -rn "learning_proposal" engines tests app.py     # 0 hit
grep -rn "learning_comparison" engines tests          # 4 hit
python3 -m pytest tests/test_engine_registry.py -q    # 24 passed

# PR 규모 재측정
git add -u engines/_base.py engines/ape/__init__.py engines/ape/README.md tests/test_engine_registry.py
git diff --cached --stat | tail -1                    # 4 files changed (이번 변경분)
git fetch origin
git diff origin/main...HEAD --stat | tail -1          # 전체 PR 규모 재측정
```

> sed 명령 후 commit 전에 반드시 grep으로 0/4 hit 확인. macOS BSD sed는 `-i ''`(빈 백업 확장자)가 필수.

---

## 부록 A. v2.2 → v2.3 정정 위치

### A.1 코드 변경 대상 4 파일로 확장 (F1 [codex] P1)

| 위치 | v2.2 | v2.3 |
|---|---|---|
| §13.1 변경 위치 표 | 3 행 (engines 3 파일) | **4 행** — `tests/test_engine_registry.py:65` 추가 |
| §13.3 적용 검증 명령 | `grep -rn "learning_proposal" engines/ app.py` | `grep -rn "learning_proposal" engines tests app.py` (tests 포함) |
| §13.5 sed 일괄 명령 | (없음) | **신설** — 4 파일 sed + 검증 + PR 규모 재측정 단일 블록 |
| §5.1 회귀 안전성 주석 | (없음) | **추가** "옵션 A 적용 시 tests 동시 수정 필수, 미수정 시 24→23 passed" |

### A.2 PR 규모 표기 정정 (F2 [codex] P2)

| 위치 | v2.2 | v2.3 |
|---|---|---|
| §1.2 머지 방식 | "**34개 파일 변경**" 고정 | "**현재 기준 34개 파일 변경**. §13 옵션 A 포함 시 재측정 필요" + 명령 블록 |
| §10 매트릭스 끝 | "PR 규모: 34개 파일 변경, 15,262 insertions / 55 deletions" | "**현재 기준 34개 파일 변경**, ... §13 옵션 A 적용 시 4 파일 추가 수정 → **재측정 필요**. 최종 수치는 v2.4에서 갱신" |
| §13.4 (신설) | (없음) | **PR 규모 재측정 절차** + 4 갱신 위치 (가이드 §1.2/§10 + PR_DESCRIPTION.md + GitHub PR description) |
| §1.1 PR 생성 단계 #3 | "PR URL/번호 갱신" | "PR URL/번호 + **PR 규모** 갱신" |

## 부록 B. v1 → v2 → v2.1 → v2.2 → v2.3 누적 Finding 추적

| Finding | 우선순위 | v1 | v2 | v2.1 | v2.2 | v2.3 |
|---|---|---|---|---|---|---|
| F1 v1: PR URL 실제값 아님 | P1 | `pull/new/...` | §1.1 PR 생성 신설 | (계승) | (계승) | (계승) |
| F2 v1: macOS xargs -r | P1 | 실패 가능 | PID 변수 | (계승) | (계승) | (계승) |
| F3 v1: 테스트 수치 | P2 | "129/76" | 106/24/16 | (계승) | (계승) | (계승) |
| F4 v1: 재시작 문구 | P2 | 모호 | 코드/서버 분리 | (계승) | (계승) | (계승) |
| F1 v2: 파일 수 35→34 | P2 | — | "35개" | "34개" 정정 | (계승) | **재정의** "현재 34, 옵션 A 후 재측정" |
| F2 v2: consensus 통과 표현 | P2 | — | "이미 통과" | "현 세션 미검증" | (계승) | (계승) |
| F1 v2.1: FPE 고정 원칙 | P1 | — | — | 미반영 | §3.3 7항 | (계승) |
| F2 v2.1: APE engine_purpose | P1 | — | — | `learning_proposal` | `learning_comparison` 권고 | (계승, 코드 변경 명세 보강) |
| F3 v2.1: 상담 family/AppleGothic | P2 | — | — | 미반영 | §3.3 #4 #5 #6 #7 | (계승) |
| F4 v2.1: git diff base | P3 | — | — | `main...HEAD` | `origin/main...HEAD` | (계승) |
| **F1 v2.2 [codex]: 코드 변경에 tests 누락** | **P1** | — | — | — | 3 파일만 명시 | **§13.1 4 파일 + §13.5 sed 단일 명령** |
| **F2 v2.2 [codex]: 옵션 A 후 PR 규모 재측정 누락** | **P2** | — | — | — | 34 고정값 | **§13.4 신설 + §10 표기 정정** |

**누적**: v1 4건 + v2 2건 + v2.1 4건 + v2.2 [codex] 2건 = **총 12 Finding 모두 v2.3까지 반영**, P0/P1 잔여 0건.

## 부록 C. v2.3 실행 즉시 명령 (TL;DR)

```bash
# 1. 현재 상태 확인
cd /Users/appler/Documents/COTEX/FlowBiz_ultra
git fetch origin
git diff origin/main...HEAD --stat | tail -1   # 34 files (옵션 A 미적용)
grep -rn "learning_proposal" engines tests app.py    # 4 hit

# 2. 옵션 A 적용 (권장) — 4 파일 일괄 sed
sed -i '' 's/learning_proposal/learning_comparison/g' \
  engines/_base.py \
  engines/ape/__init__.py \
  engines/ape/README.md \
  tests/test_engine_registry.py

# 3. 검증
grep -rn "learning_proposal" engines tests app.py    # 0 hit
grep -rn "learning_comparison" engines tests         # 4 hit
python3 -m pytest tests/test_engine_registry.py -q   # 24 passed
python3 -m pytest tests/ -q                          # 106 passed, 7 skipped
node scripts/test_dual_eval_helpers.js               # 16 passed

# 4. PR 규모 재측정 — F2 [codex] P2
git add -u engines/_base.py engines/ape/__init__.py engines/ape/README.md tests/test_engine_registry.py
git commit -m "fix: APE engine_purpose learning_proposal → learning_comparison (F1 v2.1 + F1 [codex] v2.2)"
git push origin codex/dual-engine-execution-20260430
git fetch origin
git diff origin/main...HEAD --stat | tail -1   # 새 파일 수 — v2.4에 반영

# 5. 머지 후 (서버 검증, 5분)
git checkout main && git pull origin main
PID="$(lsof -ti :8011 2>/dev/null || true)"; [ -n "$PID" ] && kill $PID && sleep 1
nohup python3 -m uvicorn app:app --host 127.0.0.1 --port 8011 > /tmp/uvicorn8011.log 2>&1 &
sleep 3

# 6. APE engine_purpose 정정 검증 — learning_comparison 노출
curl -fsS http://127.0.0.1:8011/api/engine/list | python3 -m json.tool | grep engine_purpose
# → "fixed_screening" + "learning_comparison" 2건

# 7. 종합 검증
DUAL_SERVER_URL=http://127.0.0.1:8011 ./scripts/verify_dual_engine.sh
# → 7 consensus 케이스 PASSED 입증
```

## 부록 D. 후속 3차 UI PR 작업 시작 시 체크리스트 (v2.2 §3.3 7항 직결)

3차 PR 첫 commit 전 다음 확인:

- [ ] `flowbiz_dual_engine_ui_sample_validation_direction_20260430.md` 읽음
- [ ] §3.3 7항 원칙 숙지 — #1 (FPE 고정), #2 (APE 선택 금지), #3 (APE 비교 전용)
- [ ] §3.3 6 화면 + 엔진관리 탭 범위 확정
- [ ] 금지 UI 패턴 (엔진 선택 라디오) 폐기 확인
- [ ] AppleGothic font stack 적용 계획 수립
- [ ] 상담보고서 family + 전화상담/직접상담 subtype 데이터 모델 확인
- [ ] 엔진 관리 탭의 pending/approved/promoted 상태 enum 정의
- [ ] `flowbiz_dual_engine_evaluation_and_upgrade_lifecycle_plan_20260430.md` §6 화면 매트릭스와 정합성 확인

위 8 항목 모두 [O] 처리 후 3차 PR 착수.
