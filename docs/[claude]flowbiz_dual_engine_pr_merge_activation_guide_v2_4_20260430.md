# 듀얼 엔진 PR 머지 → 라이브 활성화 가이드 v2.4 [claude]

- 문서번호: FBU-GUIDE-PR-MERGE-DUAL-v2_4-20260430
- 작성일: 2026-04-30
- 작성자: [claude]
- 이전 버전: `[claude]flowbiz_dual_engine_pr_merge_activation_guide_v2_3_20260430.md` (v2.3)
- 검증: `[codex]flowbiz_dual_engine_pr_merge_activation_guide_v2_3_validation_20260430.md` (**추가 P0/P1 Finding 0건 — 승인 조건부 통과**)
- 변경 사유: v2.3 [codex] 검증에서 신규 Finding 0건 → **계획 단계 종료, 실행 단계 진입**. v2.4는 plan이 아닌 **실행 승인 체크리스트(Execution Approval Checklist)**로 framing 전환.

## 0. v2.3 → v2.4 전환 의의

v2.3 [codex] 검증의 핵심 결론:

> "현재 문서 기준으로는 추가 P0/P1 Finding이 없다. PR 머지 활성화 가이드로 사용 가능하다."
> "§13 옵션 A 대상 4파일은 `origin/main...HEAD` 기준 모두 PR에 이미 포함되어 있다."

따라서 v2.4의 역할은 **이전 plan 갱신이 아니라 실행 단계 진입 후 5개 승인 조건을 체계적으로 추적하는 체크리스트**입니다.

| 구분 | v2.0 ~ v2.3 | **v2.4** |
|---|---|---|
| 문서 성격 | 계획서 (Plan) | **실행 승인 체크리스트 (Execution Checklist)** |
| 주요 내용 | Findings 반영 + 절차 설명 | **명령 자동화 블록 + placeholder + 검증 결과 기록** |
| 다음 단계 | 다음 검증 보고서 대기 | **옵션 A 실행 → PR 생성 → 머지 → 서버 검증 → v2.5 완료 보고서** |

### 0.1 v2.3 [codex] 핵심 관찰 사항

| 항목 | v2.3 [codex] 측정값 |
|---|---|
| 옵션 A 4 파일 PR 포함 여부 | **모두 포함** (engines/_base.py, engines/ape/__init__.py, engines/ape/README.md, tests/test_engine_registry.py) |
| `origin/main...HEAD` diff | 34 files changed, 15262 insertions(+), 55 deletions(-) |
| 옵션 A 적용 후 파일 수 변동 예상 | **변동 없음** (4 파일 모두 이미 PR 포함, content modify only) |
| `learning_proposal` 잔존 | 4곳 (옵션 A 적용 전 상태) |
| stale gate / JS helper / common helper 과거 Finding | 모두 해소 — 재발 징후 없음 |

> 핵심: **옵션 A 적용 시 PR 파일 수는 34에서 변동 없을 가능성이 높음** (모두 이미 PR 포함된 파일의 content modify). 다만 정합성을 위해 v2.3 §13.4 재측정 절차는 그대로 수행.

## 1. 5개 승인 조건 체크리스트 (v2.3 [codex] §5 채택)

```text
[ ] 조건 1: §13 옵션 A 4 파일 변경 적용
[ ] 조건 2: tests/test_engine_registry.py 24 passed 유지
[ ] 조건 3: 전체 테스트 통과 (또는 기존 skipped 사유 확인)
[ ] 조건 4: PR 규모 재측정 후 v2.4/PR description 갱신
[ ] 조건 5: 머지 후 verify_dual_engine.sh 통과 + 7 consensus PASSED 입증
```

**완료 시점**: 5개 모두 [O] → v2.5 완료 보고서 생성 트리거.

## 2. 조건 1+2+3 — 옵션 A 적용 자동화 블록

### 2.1 사전 상태 확인

```bash
cd /Users/appler/Documents/COTEX/FlowBiz_ultra

# 현재 PR 규모 (옵션 A 적용 전)
git fetch origin
git diff origin/main...HEAD --stat | tail -1
# → 34 files changed, 15262 insertions(+), 55 deletions(-)  (예상)

# learning_proposal 잔존 4곳 확인
grep -rn "learning_proposal" engines tests app.py
# → 4 hit
```

### 2.2 4 파일 일괄 sed (macOS BSD sed 호환 — `-i ''` 필수)

```bash
sed -i '' 's/learning_proposal/learning_comparison/g' \
  engines/_base.py \
  engines/ape/__init__.py \
  engines/ape/README.md \
  tests/test_engine_registry.py
```

### 2.3 변경 검증 (조건 2+3)

```bash
# 잔존 0 hit 확인
grep -rn "learning_proposal" engines tests app.py
# → 0 hit (성공)

# 신규 4 hit 확인
grep -rn "learning_comparison" engines tests
# → 4 hit (성공)

# 조건 2: registry 테스트 24 passed 유지
python3 -m pytest tests/test_engine_registry.py -q
# → 24 passed (조건 2 [O])

# 조건 3: 전체 회귀 테스트
python3 -m pytest tests/ -q
# → 106 passed, 7 skipped (조건 3 [O])
#   skipped 7건 = test_dual_consensus.py (라이브 서버 부재, 정상)

# 보조: Node helper + closure
node scripts/test_dual_eval_helpers.js
# → 16 passed, 0 failed
python3 scripts/extract_engine_closures.py
# → 3구역 disjoint OK
```

### 2.4 commit + push (조건 1 완료)

```bash
git add -u engines/_base.py engines/ape/__init__.py engines/ape/README.md tests/test_engine_registry.py

git commit -m "fix: APE engine_purpose learning_proposal → learning_comparison (v2.1 F2 P1 + v2.2 [codex] F1 P1)

- engines/_base.py:20 META 주석 정정
- engines/ape/__init__.py:37 engine_purpose 값 정정
- engines/ape/README.md:12 README META 표 정정
- tests/test_engine_registry.py:65 테스트 기대값 동시 정정 (v2.2 [codex] 누락 사항)

검증:
- grep 0 hit (engines tests app.py 기준)
- pytest tests/test_engine_registry.py: 24 passed
- pytest tests/: 106 passed, 7 skipped
- node scripts/test_dual_eval_helpers.js: 16 passed"

git push origin codex/dual-engine-execution-20260430
```

## 3. 조건 4 — PR 규모 재측정 + v2.4 갱신

### 3.1 재측정 명령

```bash
cd /Users/appler/Documents/COTEX/FlowBiz_ultra
git fetch origin
git diff origin/main...HEAD --stat | tail -1
```

### 3.2 측정 결과 기록 (placeholder — 실행 후 채움)

| 측정 시점 | 결과 |
|---|---|
| v2.3 [codex] 측정 (옵션 A 적용 전) | `34 files changed, 15262 insertions(+), 55 deletions(-)` |
| **본 v2.4 측정 (옵션 A 적용 후)** | **`<TBD: 옵션 A commit + push 후 위 명령 결과로 갱신>`** |

### 3.3 갱신 위치 (4곳)

옵션 A 적용 + push 후 다음 4곳에 새 수치 반영:

- [ ] 본 가이드 §3.2 측정 결과 기록표
- [ ] 본 가이드 §6 요약 매트릭스 끝 PR 규모
- [ ] `outputs/dual_engine_baseline_20260430/PR_DESCRIPTION.md`
- [ ] GitHub PR description (PR 생성 후)

> **예상**: v2.3 [codex]에 따르면 4 파일 모두 이미 PR 포함이므로 파일 수는 34 유지 예상. insertions/deletions만 미세 변동 가능.

## 4. PR 생성 (조건 1~4 완료 후)

### 4.1 PR 생성 절차 (gh CLI 미설치 — 웹 UI 사용)

1. 브라우저에서 PR 생성 URL 접속:
   ```
   https://github.com/YeChungHee/FlowBizTool/pull/new/codex/dual-engine-execution-20260430
   ```

2. PR 작성:
   - **Title**: `feat: dual engine v2.11 — engines/ separation + dual evaluation API + UI helper (engine_purpose: learning_comparison)`
   - **Description**: `outputs/dual_engine_baseline_20260430/PR_DESCRIPTION.md` + **§3.2 재측정 수치 반영**
   - **Base**: `main`
   - **Head**: `codex/dual-engine-execution-20260430`

3. PR 생성 후 본 문서 placeholder 갱신:
   ```diff
   - PR URL: TBD (생성 후 갱신)
   - PR 번호: TBD
   - PR 규모: <TBD>
   + PR URL: https://github.com/YeChungHee/FlowBizTool/pull/<번호>
   + PR 번호: #<번호>
   + PR 규모: <옵션 A 후 재측정 결과>
   ```

### 4.2 PR placeholder (실행 후 채움)

```text
PR URL:    [TBD]
PR 번호:   [TBD]
PR 규모:   [TBD: 옵션 A 적용 후 재측정 결과]
PR Base:   main
PR Head:   codex/dual-engine-execution-20260430 (e16b391 + 옵션 A commit)
```

## 5. 조건 5 — 머지 후 8011 서버 검증

### 5.1 macOS 호환 재시작 + 검증 자동화

```bash
cd /Users/appler/Documents/COTEX/FlowBiz_ultra

# 1. 머지된 main 동기화
git checkout main && git pull origin main

# 2. macOS BSD xargs 호환 재시작
PID="$(lsof -ti :8011 2>/dev/null || true)"
if [ -n "$PID" ]; then
  kill $PID
  sleep 1
fi
nohup python3 -m uvicorn app:app --host 127.0.0.1 --port 8011 > /tmp/uvicorn8011.log 2>&1 &
sleep 3

# 3. health check + APE engine_purpose 정합성 (조건 5 핵심)
curl -fsS http://127.0.0.1:8011/api/engine/list | python3 -m json.tool
# → "engine_purpose": "fixed_screening" + "engine_purpose": "learning_comparison" 동시 확인

# 4. 종합 검증 — 9 항목 [ALL OK] + 7 consensus PASSED 입증
DUAL_SERVER_URL=http://127.0.0.1:8011 ./scripts/verify_dual_engine.sh

# 5. 듀얼 평가 1회 시도 (both_go 케이스)
curl -fsS -X POST http://127.0.0.1:8011/api/evaluate/dual \
  -H 'Content-Type: application/json' \
  -d @tests/fixtures/v_compare/both_go_normal.json \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print('consensus:', d['agreement']['consensus'], 'fpe_gate:', d['fpe_gate_passed'])"
# → consensus: both_go, fpe_gate: True
```

### 5.2 조건 5 입증 체크 (실행 후 채움)

| 항목 | 결과 |
|---|---|
| 8011 서버 기동 | [TBD] |
| `/api/engine/list` 응답에 `learning_comparison` 노출 | [TBD] |
| `verify_dual_engine.sh` [ALL OK] | [TBD] |
| `tests/test_dual_consensus.py` 7 PASSED | [TBD] |
| `/api/evaluate/dual` both_go 응답 정상 | [TBD] |

## 6. 요약 매트릭스 (v2.3 §10 계승)

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

> **PR 규모 (v2.4 — 옵션 A 적용 후 재측정 placeholder)**: **<TBD>** files changed, **<TBD>** insertions / **<TBD>** deletions (`origin/main` 기준)
> v2.3 [codex] 예측: 파일 수 변동 없음 (옵션 A 4 파일 모두 PR 이미 포함)

## 7. 핵심 메시지

v2.4는 **계획 종료, 실행 진입** 문서입니다.

- v2.3 [codex] 검증에서 **추가 P0/P1 Finding 0건** → 계획 단계 완료
- 5개 승인 조건 체크리스트 + 자동화 명령 블록으로 **머지까지 단일 흐름**으로 실행 가능
- 옵션 A 4 파일 변경은 모두 이미 PR 포함이므로 PR 규모 변동은 **insertions/deletions만 미세** 예상
- 5개 조건 모두 [O] 처리 후 **v2.5 완료 보고서** 생성으로 종결

> v2.3 [codex] §5 인용: "PR 머지 활성화 가이드로 사용 가능하다."

## 8. 다음 액션 흐름

```
[현재] v2.4 생성 (체크리스트 5개 모두 [ ])
   ↓
사용자 확인: 옵션 A 적용 결정
   ↓
§2 자동화 블록 실행 (조건 1+2+3 [O])
   ↓
§3 PR 규모 재측정 → §3.3 4곳 수치 갱신 (조건 4 [O])
   ↓
§4 PR 생성 → §4.2 placeholder 채움
   ↓
PR review + 머지 (engine.py conflict 시 6 필드 채택)
   ↓
§5 8011 재시작 + 서버 검증 (조건 5 [O])
   ↓
v2.5 완료 보고서 [claude] 생성:
  "[claude]flowbiz_dual_engine_pr_merge_activation_completion_report_20260430.md"
   ↓
3차 UI PR 진입 (§3.3 7항 + 6 화면 + 엔진관리 탭 — v2.2 §3.3 계승)
```

## 9. 누적 Finding 추적

| 단계 | 신규 Finding | 누적 | 잔여 P0/P1 |
|---|---|---|---|
| v1 | 4 (P1×2, P2×2) | 4 | — |
| v2 | 2 (P2×2) | 6 | — |
| v2.1 | 0 (v2 P2×2 반영) | 6 | — |
| v2.2 | 0 (v2.1 P1×2+P2+P3 반영) | 10 | — |
| v2.3 | 0 (v2.2 [codex] P1+P2 반영) | 12 | — |
| **v2.4** | **0 (v2.3 [codex] 신규 Finding 0건)** | **12** | **0** |

### 9.1 v2.3 [codex] 과거 Finding 재점검 결과 (참고)

| 카테고리 | 과거 Finding | 현재 상태 | 판단 |
|---|---|---|---|
| stale gate / server_input_hash | 클라이언트 inputHash 불일치, state_key 미구분 | `/api/evaluate/dual` 응답에 server_input_hash 포함, financialFilterSignal 변경 시 hash 변경 테스트 존재 | **해소** |
| JS helper 테스트 | Python 테스트가 실제 JS 미검증 | `scripts/test_dual_eval_helpers.js`가 web/dual_eval_helpers.js를 require — 16 passed | **해소** |
| common helper 검증 | dir(c) 기반 callable 검증의 false fail | `__all__` 명시 + ALLOWED_COMMON 별도 관리 | **해소 (재발 위험 낮음)** |

## 10. 변경되지 않은 항목 (v2.3 그대로 계승)

다음 섹션은 v2.3에서 변경 없이 계승합니다 — v2.3 문서를 직접 참조하세요:

- §3.3 후속 UI PR의 운영 원칙 7항 + 6 화면 + 엔진관리 탭 (v2.2 신설 → v2.3 계승)
- §6 engine.py 충돌 가능성 (경로 A/B + 6 필드 채택 권장)
- §9 Rollback 시점별
- 부록 D 후속 3차 UI PR 작업 시작 시 체크리스트 8 항목

---

## 부록 A. v2.3 → v2.4 변경 위치

### A.1 문서 framing 변경

| 항목 | v2.3 | v2.4 |
|---|---|---|
| 문서 성격 | 계획서 (Plan) | **실행 승인 체크리스트 (Execution Checklist)** |
| 핵심 구조 | §0 변경 요약 → §1 PR 생성 → ... → §13 코드 변경 | **§1 5 조건 체크리스트 → §2-5 조건별 자동화 블록 → §8 다음 액션 흐름도** |
| 명령 블록 | 분산된 절차 안내 | **§2/§3/§5에 단일 실행 가능 블록** (sed → 검증 → commit → push → 머지 → 검증) |

### A.2 신규 추가 섹션

- **§1 5 조건 체크리스트** — v2.3 [codex] §5 인용
- **§2.4 commit message 템플릿** — v2.1 F2 + v2.2 [codex] F1 cross-reference
- **§3.2 재측정 결과 placeholder 표** — 실행 후 직접 갱신
- **§5.2 조건 5 입증 체크** — 실행 후 직접 갱신
- **§8 다음 액션 흐름도** — v2.5 완료 보고서까지 단일 흐름

### A.3 v2.3 [codex] 핵심 인용

| v2.3 [codex] 위치 | v2.4 인용 위치 |
|---|---|
| §1 결론 "추가 P0/P1 Finding 없음" | §0 전환 의의 + §7 핵심 메시지 |
| §2 실측 "옵션 A 4 파일 모두 PR 포함" | §0.1 + §6 매트릭스 주석 |
| §3 과거 Findings 재점검 (3 카테고리 모두 해소) | §9.1 |
| §5 5 승인 조건 | **§1 체크리스트 직접 인용** |

## 부록 B. 누적 Finding 추적 상세 (v1 → v2.4)

| Finding | 우선순위 | v1 | v2 | v2.1 | v2.2 | v2.3 | v2.4 |
|---|---|---|---|---|---|---|---|
| F1 v1: PR URL 실제값 아님 | P1 | `pull/new/...` | §1.1 PR 생성 신설 | (계승) | (계승) | (계승) | (계승) |
| F2 v1: macOS xargs -r | P1 | 실패 가능 | PID 변수 | (계승) | (계승) | (계승) | (계승) |
| F3 v1: 테스트 수치 | P2 | "129/76" | 106/24/16 | (계승) | (계승) | (계승) | (계승) |
| F4 v1: 재시작 문구 | P2 | 모호 | 코드/서버 분리 | (계승) | (계승) | (계승) | (계승) |
| F1 v2: 파일 수 35→34 | P2 | — | "35개" | "34개" 정정 | (계승) | "현재 34, 옵션 A 후 재측정" 재정의 | **§3.2 placeholder + §6 주석** |
| F2 v2: consensus 통과 표현 | P2 | — | "이미 통과" | "현 세션 미검증" | (계승) | (계승) | **§5.2 조건 5 입증 체크 신설** |
| F1 v2.1: FPE 고정 원칙 | P1 | — | — | 미반영 | §3.3 7항 | (계승) | §10 계승 명시 |
| F2 v2.1: APE engine_purpose | P1 | — | — | `learning_proposal` | `learning_comparison` 권고 | 코드 변경 명세 | **§2 자동화 블록 — sed + commit** |
| F3 v2.1: 상담 family/AppleGothic | P2 | — | — | 미반영 | §3.3 #4-7 | (계승) | §10 계승 명시 |
| F4 v2.1: git diff base | P3 | — | — | `main...HEAD` | `origin/main...HEAD` | (계승) | (계승) |
| F1 v2.2 [codex]: 코드 변경에 tests 누락 | P1 | — | — | — | 3 파일만 명시 | 4 파일 + sed 단일 명령 | **§2.2 sed 4 파일 직접 명시** |
| F2 v2.2 [codex]: 옵션 A 후 PR 규모 재측정 누락 | P2 | — | — | — | 34 고정값 | §13.4 신설 + §10 정정 | **§3 재측정 자동화 블록** |
| **v2.3 [codex] 신규** | — | — | — | — | — | — | **0건 — 통과** |

**누적 12 Finding 모두 v2.4까지 반영 + v2.3 [codex] 신규 0건 → 실행 단계 진입 가능**

## 부록 C. v2.4 단일 실행 블록 (TL;DR)

```bash
cd /Users/appler/Documents/COTEX/FlowBiz_ultra

# === 조건 1+2+3: 옵션 A 적용 ===
git fetch origin
git diff origin/main...HEAD --stat | tail -1                  # 사전: 34 files
grep -rn "learning_proposal" engines tests app.py             # 사전: 4 hit

sed -i '' 's/learning_proposal/learning_comparison/g' \
  engines/_base.py \
  engines/ape/__init__.py \
  engines/ape/README.md \
  tests/test_engine_registry.py

grep -rn "learning_proposal" engines tests app.py             # 0 hit
grep -rn "learning_comparison" engines tests                  # 4 hit
python3 -m pytest tests/test_engine_registry.py -q            # 24 passed
python3 -m pytest tests/ -q                                   # 106 passed, 7 skipped
node scripts/test_dual_eval_helpers.js                        # 16 passed

git add -u engines/_base.py engines/ape/__init__.py engines/ape/README.md tests/test_engine_registry.py
git commit -m "fix: APE engine_purpose learning_proposal → learning_comparison"
git push origin codex/dual-engine-execution-20260430

# === 조건 4: PR 규모 재측정 + v2.4 갱신 ===
git fetch origin
git diff origin/main...HEAD --stat | tail -1                  # → §3.2 placeholder 채움

# === [수동] PR 생성 (웹 UI) → §4.2 placeholder 채움 ===
# https://github.com/YeChungHee/FlowBizTool/pull/new/codex/dual-engine-execution-20260430

# === [수동] PR review + 머지 ===

# === 조건 5: 머지 후 검증 ===
git checkout main && git pull origin main
PID="$(lsof -ti :8011 2>/dev/null || true)"; [ -n "$PID" ] && kill $PID && sleep 1
nohup python3 -m uvicorn app:app --host 127.0.0.1 --port 8011 > /tmp/uvicorn8011.log 2>&1 &
sleep 3

curl -fsS http://127.0.0.1:8011/api/engine/list | python3 -m json.tool | grep engine_purpose
# → "fixed_screening" + "learning_comparison" (조건 5 핵심)

DUAL_SERVER_URL=http://127.0.0.1:8011 ./scripts/verify_dual_engine.sh
# → [ALL OK] 9 항목 + 7 consensus PASSED

curl -fsS -X POST http://127.0.0.1:8011/api/evaluate/dual \
  -H 'Content-Type: application/json' \
  -d @tests/fixtures/v_compare/both_go_normal.json \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print('consensus:', d['agreement']['consensus'], 'fpe_gate:', d['fpe_gate_passed'])"
# → consensus: both_go, fpe_gate: True

# === 5 조건 모두 [O] → v2.5 완료 보고서 생성 트리거 ===
```
