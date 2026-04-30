# FlowBiz v2 D5 → D4 통합 마스터 계획서 [claude]

- 문서번호: FBU-PLAN-V2-D5-D4-MASTER-20260501
- 작성일: 2026-05-01
- 작성자: [claude]
- 사용자 지시: "최종계획서대로 생성구현 진행하고 D5부터 ~ D4까지 구현 후 구현 보고서 생성"
- 결론: D5/D1/D3은 Claude 자동 구현, **D4(머지)는 사용자 수동**. 모두 완료 후 구현 보고서 생성.

## 0. 실행 순서

```
[Step 1] 최종 계획서 (본 문서)
   ↓
[Step 2] D5: v2 산출물 commit + push (새 브랜치)
   ↓
[Step 3] D1: 운영 6 HTML에 v2_tokens.css import (회귀 0)
   ↓
[Step 4] D3: EvaluationSnapshot API 신설 (Phase 1 backend)
   ↓
[Step 5] D4: 사용자 수동 머지 안내 (GitHub 웹 UI)
   ↓
[Step 6] 구현 보고서
```

## 1. D5 — 산출물 commit + push

### 1.1 작업 내역

**새 브랜치**: `codex/v2-design-system-20260501` (main 기반)

**포함 파일** (v2 산출물만):
```
web/styles/v2_tokens.css                        (A1)
web/styles/v2_components.css                    (B1 + B1-P2-fix)
web/v2_preview.html                              (B1 + B1-P2-fix)
scripts/extract_v2_tokens_rendered.js           (A3)
scripts/compare_v2_preview_vs_standalone.js     (C1 + B1-P2-fix)
package.json + package-lock.json                (Phase 0)
playwright.config.ts                             (Phase 0)
tests/run_e2e.sh                                 (Phase 0)
tests/e2e/fixtures/snapshot_seeder.ts            (Phase 0)
tests/e2e/decision_source_fpe.spec.ts            (Phase 0)
.gitignore                                       (4 라인 추가)
docs/reference/dual_engine_v2_standalone.html   (11MB 시안)
docs/reference/v2_tokens_summary_20260501.md    (P2-1)
docs/reference/v2_font_policy_exception_20260501.md (P2-2)
docs/reference/v2_preview_comparison_summary_20260501.md (P2-3 + F1 정정)
docs/[claude]*.md (계획서 17건)
docs/[codex]*.md (검증보고서 11건)
```

**제외 파일** (unrelated dirty):
```
data/bizaipro_learning_registry.json
docs/flowbiz_ultra_validation_report_registry.md
tests/test_regression.py
web/bizaipro_shared.css
```

### 1.2 검증

```bash
git diff --cached --stat | tail -3   # 통합 commit 통계
git log --oneline -1                  # 새 commit
git push origin codex/v2-design-system-20260501
```

## 2. D1 — 운영 6 HTML v2 토큰 import

### 2.1 작업 내역

각 6 HTML의 line 7 (`bizaipro_shared.css` link 직후)에 추가:
```html
<link rel="stylesheet" href="./styles/v2_tokens.css?v=20260501-d1">
```

**대상 파일**:
- `web/bizaipro_home.html`
- `web/bizaipro_proposal_generator.html`
- `web/bizaipro_email_generator.html`
- `web/bizaipro_evaluation_result.html`
- `web/bizaipro_engine_compare.html`
- `web/bizaipro_changelog.html`

### 2.2 회귀 0 보장

토큰만 노출 (`--fbu-*` CSS 변수). 기존 `.bz-*` 클래스 미적용 → **시각 변화 없음**.

### 2.3 검증

```bash
for f in web/bizaipro_{home,proposal_generator,email_generator,evaluation_result,engine_compare,changelog}.html; do
  grep -q "v2_tokens.css" "$f" && echo "[OK] $f" || echo "[FAIL] $f"
done

# 8011 서버 통해 접근 가능 확인
curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:8011/web/bizaipro_home.html"
```

## 3. D3 — EvaluationSnapshot API 신설

### 3.1 작업 내역

`app.py`에 다음 추가:

**Pydantic 모델** (v3 §7):
- `EvaluationSnapshot`
- `ExhibitionLeadSnapshot`
- `ProposalSnapshot`
- `EvaluationReportRequest`
- `ProposalGenerateRequest`
- `EmailGenerateRequest`
- `UnsafeRawSnapshotForTest` (test only)

**API 엔드포인트** (v3 §7.2):
- `POST /api/evaluation/report` — 평가보고서 생성 + EvaluationSnapshot 저장
- `GET /api/evaluation/report/{report_id}` — snapshot 조회
- `GET /api/evaluation/reports` — 목록
- `POST /api/proposal/generate` — snapshot 기반 제안서 (FPE 강제)
- `POST /api/test/seed-raw-snapshot` — test only (FLOWBIZ_ENV=test 가드)
- `DELETE /api/test/raw-snapshot/{report_id}` — test only

**저장 경로 분기** (v5 §11.5):
```python
def get_snapshot_dir() -> Path:
    if os.getenv("FLOWBIZ_ENV") == "test":
        return Path(os.getenv("FLOWBIZ_TEST_SNAPSHOT_DIR", "data/test_evaluation_reports"))
    return Path("data/evaluation_reports")
```

**ID 생성** (v4 §7):
```python
def _new_id() -> str:
    return uuid.uuid4().hex   # Python 표준 라이브러리
```

### 3.2 회귀 0 보장

기존 모든 endpoint 변경 없음. 신규 추가만. pytest 회귀 0건 기대.

### 3.3 검증

```bash
python3 -m pytest tests/ -q          # 100+ passed
python3 -c "from app import app; print([r.path for r in app.routes if '/api/evaluation' in r.path])"
```

## 4. D4 — 사용자 수동 머지 안내

### 4.1 1차 PR 머지 절차 (사용자 수동)

```
1. https://github.com/YeChungHee/FlowBizTool/pulls
2. PR `codex/dual-engine-execution-20260430` (1차 PR — engine_purpose: learning_comparison) 검토
3. Merge 클릭 (engine.py conflict 시 6 필드 채택)
```

### 4.2 v2 PR 생성 (D5 push 후 사용자 수동)

```
URL: https://github.com/YeChungHee/FlowBizTool/pull/new/codex/v2-design-system-20260501
Title: feat: v2 design system — Pretendard tokens + 22 components + E2E + 9 codex Findings 처리
Body: 본 마스터 계획서 §1-§3 인용
```

### 4.3 머지 후 확인

```bash
git checkout main && git pull origin main
DUAL_SERVER_URL=http://127.0.0.1:8011 ./scripts/verify_dual_engine.sh
```

## 5. 검증 매트릭스

| Step | 검증 명령 | 기대 결과 |
|---|---|---|
| D5 | `git log origin/codex/v2-design-system-20260501` | 1+ commit |
| D1 | `grep -l v2_tokens.css web/bizaipro_*.html \| wc -l` | 6 |
| D1 | 8011 통해 6 HTML 접근 | 모두 200 OK |
| D3 | `pytest tests/ -q` | 회귀 0건 |
| D3 | `python3 -c "from app import app"` | import OK |
| D3 | `/api/evaluation/report` import | 라우트 등록 |
| D4 | (사용자 수동) | PR 머지 완료 |

## 6. Risk + Mitigation

| Risk | 대응 |
|---|---|
| D5 commit에 unrelated dirty 포함 | pathspec으로 명시 add (Preflight A 패턴) |
| D1 시각 회귀 | 토큰만 노출 — 클래스 적용 안 함 |
| D3 import error | 신규 모델만 추가, 기존 변경 없음 |
| D3 pytest 깨짐 | 변경 직후 pytest 즉시 실행 |
| D4 1차 PR conflict | engine.py 6 필드 채택 권장 (v2.7) |

## 7. 구현 보고서 (Step 6 — 본 마스터 계획 종료 후 작성)

파일: `[claude]flowbiz_v2_d5_to_d4_implementation_report_20260501.md`

내용:
- D5/D1/D3 실행 결과
- 각 검증 통과 여부
- D4 사용자 액션 안내
- 누적 변경 통계
- 다음 단계 제안

---

## 부록 A. 누적 codex Findings (D5 PR 시 강조)

| 보고서 | Finding | 처리 |
|---|---|:---:|
| Phase 0 token validation | 1 | A3+A1 |
| B1 preview validation | 3 (P2) | C1 |
| B1 P2 fix revalidation | 4 (P1×3+P2) | B1-P2-fix v2 |
| v2 preview + PR guide recheck | 1 (P2) | summary stale fix |
| **누적** | **9** | **모두 처리** |

## 부록 B. v2 디자인 정체성 핵심 인용

- **Body**: `#F9FAFB` (gray-50) bg + `#191F28` (gray-900) text
- **Card**: `#FFFFFF` + `1px solid #E5E8EB` + `12px` radius + `20px` padding
- **Header**: `#FFFFFF` 흰색 + `60px` height (검정 헤더 폐기)
- **Font**: Pretendard 1순위 (AppleGothic fallback)
- **KPI**: `24px` h3 weight 800 (84px 가정 폐기)
- **합의 배지**: 5색 (both_go/fpe_blocked/ape_only_positive/ape_blocked/both_review)
- **22 컴포넌트**: `.fbu-*` namespace, box-sizing reset, 모바일 1열 reflow

## 부록 C. 본 작업 후 잔여

| 항목 | 상태 |
|---|---|
| Phase 1 EvaluationSnapshot 모델/API | ✅ D3 완료 |
| Phase 2 운영 화면 v2 마이그레이션 | ⏳ 별도 PR (D2) |
| Phase 4 월간 upgrade-reports API | ⏳ 별도 PR |
| Phase 5 전시회 평가 흐름 | ⏳ 별도 PR |
| 1차 PR 머지 | ⏳ D4 사용자 수동 |
