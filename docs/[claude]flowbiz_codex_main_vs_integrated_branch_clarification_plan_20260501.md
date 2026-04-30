# FlowBiz codex 검증 환경 명확화 + 통합 브랜치 머지 가속 추가 계획서 [claude]

- 문서번호: FBU-PLAN-CODEX-MAIN-VS-INTEGRATED-CLARIFY-20260501
- 작성일: 2026-05-01
- 작성자: [claude]
- 검증: `[codex]flowbiz_comprehensive_findings_revalidation_20260501.md` (4 Finding **재판정 No-Go**)
- 결론: **codex가 main에서 검증 → 통합 브랜치 미머지로 인해 동일 4 Finding 반복**. 본질은 미해소 작업이 아니라 **PR 머지 대기 1건**.

## 0. 핵심 발견 — codex 검증 환경 vs 실제 구현 위치

### 0.1 검증 환경 격차

| 검증 위치 | 결과 |
|---|---|
| **`origin/main` (codex 기준)** | F1-F4 미해소 (No-Go) |
| **`origin/codex/integrated-final-20260501` (실제 구현)** | F1-F4 모두 해소 |

### 0.2 실측 격차 통계

```text
$ git rev-parse origin/main origin/codex/integrated-final-20260501
081b9e7d97e82aa636d98733c0ad2e4c37cf16de   ← origin/main (codex 검증 환경)
ee8a462a4607368ebad8d3388021ff18cfc0c70c   ← integrated-final (실제 구현)

$ git diff main...origin/codex/integrated-final-20260501 --stat | tail -1
87 files changed, 31482 insertions(+), 55 deletions(-)
```

### 0.3 codex 4 Finding 위치별 실측

| codex F# | main에서 | integrated-final에서 |
|---|---|---|
| **F1** 듀얼 엔진 소스 (engines/) | ❌ 미존재 | ✅ engines/{ape,fpe}/*.py 7 파일 |
| **F2** 듀얼 평가 API | ❌ 라우트 없음 | ✅ /api/engine/list, /api/evaluate/dual, /api/learning/evaluate/dual |
| **F3** v2 토큰/컴포넌트/preview | ❌ 미존재 | ✅ web/styles/v2_{tokens,components}.css + web/v2_preview.html |
| **F4** 6 HTML v2 import | ❌ bizaipro_shared.css만 | ✅ v2_tokens.css link 추가됨 |

**결론**: 본 세션에서 신규 작업 필요 ❌ — **codex 검증 환경을 통합 브랜치로 가리키도록 안내** + **사용자 PR 머지 가속**이 핵심.

## 1. 본 추가 계획서의 5 행동 항목

### 1.1 행동 1 — codex 검증 환경 명시 (본 문서 §0)

codex가 다음 검증부터는 **`codex/integrated-final-20260501` 브랜치를 기준으로 검증**해야 함.

**codex 실행 환경 가정 변경**:
```bash
# Before (No-Go 반복):
git checkout main
find engines -maxdepth 3 -type f -not -path '*/__pycache__/*'   # 결과 없음

# After (정확한 검증):
git fetch origin
git checkout codex/integrated-final-20260501   # 또는 origin/codex/...
find engines -maxdepth 3 -type f -not -path '*/__pycache__/*'   # 7 .py 파일
```

### 1.2 행동 2 — 통합 PR 명시적 생성 안내 (사용자 수동)

```
URL: https://github.com/YeChungHee/FlowBizTool/pull/new/codex/integrated-final-20260501
```

**PR Title**:
```
feat: v2 design system + dual engine + EvaluationSnapshot + 월간/이메일/전시회 (codex 종합검증 통합)
```

**PR Description (codex 검증 가이드 포함)**:
```markdown
## codex 검증 환경 안내

본 PR을 codex가 검증할 때는 다음 명령으로 실행해야 합니다:

```bash
git fetch origin
git checkout codex/integrated-final-20260501

# F1 듀얼 엔진 소스 검증
find engines -maxdepth 3 -type f -not -path '*/__pycache__/*'

# F2 듀얼 평가 API 검증
grep -E '@app\.(get|post)\("/api/(engine/list|evaluate/dual|learning/evaluate/dual)"' app.py

# F3 v2 산출물 검증
ls web/styles/v2_*.css web/v2_preview.html

# F4 6 HTML v2 import 검증
grep -l v2_tokens.css web/bizaipro_*.html | wc -l    # 6 기대

# 회귀 테스트
python3 -m pytest tests/ -q --ignore=tests/e2e
```

main 검증 결과는 No-Go이지만, 본 통합 브랜치 검증 결과는 모두 해소됨.

## 8 Finding 처리 매트릭스
(이전 세션 종합 완성 보고서 참조: docs/[claude]flowbiz_v2_comprehensive_completion_report_20260501.md)
```

### 1.3 행동 3 — 통합 브랜치 README 안내 (선택)

`codex/integrated-final-20260501` 브랜치에 codex 검증 가이드 추가:

| 위치 | 내용 |
|---|---|
| `docs/[codex]CODEX_REVALIDATION_GUIDE_20260501.md` (신규) | 본 §1.2의 `git checkout` + 검증 명령 매트릭스 |
| `README.md` (생략 — 본 PR scope 외) | 변경 안 함 |

### 1.4 행동 4 — main 머지 가속 옵션 (사용자 결정)

| 옵션 | 작업 | 위험 | 권장 |
|---|---|:---:|:---:|
| **A. 통합 PR review + merge commit** | GitHub 웹 UI에서 PR 생성 + 정상 review + Merge button | 낮음 | ⭐ |
| B. squash merge | 5 commits → 1 commit으로 main 머지 | 낮음 | (PR 옵션) |
| C. 직접 main에 fast-forward | `git push origin codex/integrated-final-20260501:main` | 매우 높음 (review 우회) | 비추천 |

→ **A 권장** — GitHub PR으로 정상 머지. codex 다음 검증 시 main에서 모든 항목 확인 가능.

### 1.5 행동 5 — 통합 PR 머지 후 재검증 절차

```bash
# 사용자가 머지 완료 후
git checkout main && git pull origin main

# 1. 듀얼 엔진 소스 확인
find engines -maxdepth 3 -type f -not -path '*/__pycache__/*' | wc -l   # 7+ 기대

# 2. 라우트 등록 확인
python3 -c "
from app import app
routes = sorted(set(r.path for r in app.routes if hasattr(r, 'path')))
key_routes = [r for r in routes if any(k in r for k in [
    '/engine/list', '/evaluate/dual', '/learning/evaluate/dual',
    '/evaluation/report', '/proposal/generate', '/email/generate',
    '/engine/upgrade-reports', '/engine/promote-fpe', '/exhibition/'
])]
print(f'필수 routes: {len(key_routes)}')
for r in sorted(key_routes): print(f'  {r}')
"

# 3. 회귀 테스트
python3 -m pytest tests/ -q --ignore=tests/e2e

# 4. 8011 활성화
PID="$(lsof -ti :8011 2>/dev/null || true)"
[ -n "$PID" ] && kill $PID && sleep 1
nohup python3 -m uvicorn app:app --host 127.0.0.1 --port 8011 > /tmp/uvicorn8011.log 2>&1 &
sleep 3

# 5. 핵심 API smoke test
curl http://127.0.0.1:8011/api/engine/list | python3 -m json.tool   # learning_comparison
curl http://127.0.0.1:8011/web/v2_preview.html -I | head -1          # HTTP 200
```

## 2. codex 보고서 §5 "다음 조치" 5 우선순위 → 본 추가 계획 매핑

| codex §5 우선순위 | 본 추가 계획 매핑 |
|---|---|
| 1. `engines/` 듀얼 엔진 소스 복구/재구현 | ✅ 통합 브랜치에 7 파일 존재 (위 §0.3) — main 머지 대기 |
| 2. v2 산출물 복구 | ✅ 통합 브랜치에 v2_tokens.css/v2_components.css/v2_preview.html 존재 |
| 3. `/api/engine/list`, dual eval API 구현 | ✅ 통합 브랜치 app.py에 3 라우트 등록 |
| 4. EvaluationSnapshot API 구현 | ✅ 통합 브랜치 app.py에 4 라우트 등록 |
| 5. 6 HTML v2 import + 화면 마이그레이션 | ✅ import 완료 (D1) / Phase 2 마이그레이션은 별도 PR |

→ **codex §5의 1-4 모두 통합 브랜치에 완료**. 5는 import만 완료, 본격 화면 마이그레이션은 별도 PR 예정.

## 3. 본 추가 계획의 결과물

### 3.1 즉시 산출물 (본 세션)

| 파일 | 내용 |
|---|---|
| 본 계획서 | codex 검증 환경 명시 + 통합 브랜치 머지 가속 |
| (선택) `docs/[codex]CODEX_REVALIDATION_GUIDE_20260501.md` | codex 다음 실행 가이드 (브랜치 명시) |

### 3.2 사용자 액션 (필수 1건)

```
[1단계 — 사용자 수동 머지]
  https://github.com/YeChungHee/FlowBizTool/pull/new/codex/integrated-final-20260501
  → Title + Description 작성 (본 §1.2 인용)
  → Review + Merge

[2단계 — Claude 자동 검증 가능]
  git checkout main && git pull origin main
  ./scripts/verify_dual_engine.sh   (또는 본 §1.5 절차)
```

## 4. 본 추가 계획이 신규 작업이 아닌 이유

codex 보고서 4 Finding의 본질:
- F1-F4는 **이전 세션에서 모두 해소된 Finding의 재출현**
- 재출현 사유 = **codex 검증 환경(main)이 실제 구현 위치(integrated-final)와 다름**
- 따라서 추가 코드 작성 ❌, **PR 머지 가속 + codex 검증 가이드** ✅

## 5. 핵심 메시지

**문제**: codex가 main에서 검증 → 통합 PR 미머지 → No-Go 반복
**원인**: 통합 브랜치 push 완료, PR 미생성/미머지 (사용자 수동 단계)
**해결**: 사용자 통합 PR 생성 + 머지 → main이 완성 상태로 전환 → codex 다음 검증 Go

**현 상태 정리**:
- 87 files / 31,482 insertions은 `origin/codex/integrated-final-20260501`에 완료
- main에 들어가려면 사용자 PR 머지 1단계만 남음
- 신규 코드 작성 작업 0

---

## 부록 A. codex 4 Finding의 실제 위치

### A.1 F1 듀얼 엔진 소스 (통합 브랜치 위치)

```
$ git ls-tree -r origin/codex/integrated-final-20260501 --name-only | grep "^engines"
engines/__init__.py
engines/_base.py
engines/common.py
engines/ape/__init__.py
engines/ape/eval.py
engines/ape/framework.py
engines/fpe/__init__.py
engines/fpe/eval.py
engines/fpe/policy.py
engines/fpe/view.py
engines/ape/README.md
engines/fpe/README.md
```

### A.2 F2 듀얼 평가 API (통합 브랜치 위치)

```
$ git show origin/codex/integrated-final-20260501:app.py | grep -E '@app\.(get|post)\("/api/(engine/list|evaluate/dual|learning/evaluate/dual)"'
@app.get("/api/engine/list")
@app.post("/api/evaluate/dual")
@app.post("/api/learning/evaluate/dual")
```

### A.3 F3 v2 산출물 (통합 브랜치 위치)

```
$ git ls-tree -r origin/codex/integrated-final-20260501 --name-only | grep -E "v2_(tokens|components|preview)"
web/styles/v2_components.css
web/styles/v2_tokens.css
web/v2_preview.html
```

### A.4 F4 6 HTML v2 import (통합 브랜치 위치)

```
$ for f in web/bizaipro_{home,proposal_generator,email_generator,evaluation_result,engine_compare,changelog}.html; do
    git show origin/codex/integrated-final-20260501:$f | grep -c "v2_tokens.css"
  done
1
1
1
1
1
1
```

→ 6/6 모두 v2_tokens.css link 포함.

## 부록 B. 통합 브랜치 commit 히스토리 (PR 검증용)

```
ee8a462 docs: v2 종합 완성 보고서 (codex No-Go → Go, 8 Finding 모두 처리)
d905001 feat: codex 종합검증 F6/F7/F8 미구현 추가
f0dff19 merge: v2 PR — design system + D1 6HTML import + D3 EvaluationSnapshot API
6d69698 merge: 1차 PR — dual engine + engines/ separation + dual eval API
f309c04 docs(D5-D4): 마스터 계획서 + 구현 보고서 추가
82bfd28 feat(D3): EvaluationSnapshot API 신설 (Phase 1 backend)
e5170f5 feat(D1): 운영 6 HTML에 v2_tokens.css import 추가
ca02f04 feat: v2 design system — Pretendard tokens + 22 components + E2E
89df1eb fix: APE engine_purpose learning_proposal → learning_comparison
e16b391 feat: dual engine v2.11 — engines/ separation + dual evaluation API
─── (origin/main: 081b9e7) ───
```

10 commits / 87 files / 31,482 insertions 통합. 단일 PR로 main 머지 가능.

## 부록 C. codex 다음 재검증 시 환경 변경 권장

codex 자동화 도구가 다음 재검증을 실행할 때:

```bash
# 환경 변수 또는 인자로 검증 대상 브랜치 명시
export CODEX_VALIDATION_BRANCH="codex/integrated-final-20260501"
git fetch origin
git checkout "$CODEX_VALIDATION_BRANCH"

# 또는 PR URL 기준
git fetch origin pull/<PR_NUMBER>/head:pr-validation
git checkout pr-validation
```

## 부록 D. 본 추가 계획의 codex No-Go → Go 전환 조건

본 통합 PR이 main에 머지되면:

| codex 보고서 §2 4 Finding | 머지 후 |
|---|:---:|
| F1 듀얼 엔진 소스 | ✅ Go |
| F2 듀얼 평가 API | ✅ Go |
| F3 v2 산출물 | ✅ Go |
| F4 6 HTML v2 import | ✅ Go |

**No-Go → Go 전환 단일 액션 = 사용자 PR 머지**.

## 부록 E. Phase 2-5 후속 작업 (통합 PR 머지 후 별도 PR)

| Phase | 내용 | 시점 |
|---|---|---|
| Phase 2 | 운영 6 화면 v2 컴포넌트 본격 마이그레이션 | 통합 머지 후 |
| Phase 3 | 제안서/이메일 화면이 EvaluationSnapshot API 호출 | Phase 2 후 |
| Phase 4 | 월간 30일 13:00 KST 자동 스케줄러 (cron) | 백엔드 운영 결정 후 |
| Phase 5 | 전시회 lead 화면 신설 (`bizaipro_exhibition_evaluator.html`) | Phase 2 후 |

본 계획서는 Phase 1까지 완료 (통합 PR 머지 시). Phase 2-5는 별도 PR로 진행.
