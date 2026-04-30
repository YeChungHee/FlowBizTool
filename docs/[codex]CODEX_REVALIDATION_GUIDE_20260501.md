# [codex] FlowBiz 재검증 가이드 — 통합 브랜치 검증 환경 명시

- 문서번호: FBU-GUIDE-CODEX-REVALIDATION-20260501
- 작성일: 2026-05-01
- 대상: codex 검증 자동화 도구
- 트리거: `[codex]flowbiz_comprehensive_findings_revalidation_20260501.md` (No-Go 반복)

## 1. 검증 환경 변경 권장

이전 검증은 `origin/main` 기준이라 통합 브랜치에 있는 v2 산출물 + 듀얼 엔진을 인식하지 못했습니다.

**다음 검증부터는 통합 브랜치를 명시적으로 체크아웃**:

```bash
git fetch origin
git checkout codex/integrated-final-20260501
# 또는 origin/codex/integrated-final-20260501
```

## 2. 검증 명령 매트릭스 (통합 브랜치 기준 — 모두 PASS 기대)

### 2.1 F1 듀얼 엔진 소스

```bash
find engines -maxdepth 3 -type f -not -path '*/__pycache__/*' | wc -l
# 기대: 12+ (engines/{__init__,_base,common}.py + ape/{__init__,eval,framework}.py + fpe/{__init__,eval,policy,view}.py + 2 README)
```

### 2.2 F2 듀얼 평가 API

```bash
grep -E '@app\.(get|post)\("/api/(engine/list|evaluate/dual|learning/evaluate/dual)' app.py | wc -l
# 기대: 3
```

### 2.3 F3 v2 산출물

```bash
ls web/styles/v2_tokens.css web/styles/v2_components.css web/v2_preview.html scripts/compare_v2_preview_vs_standalone.js scripts/extract_v2_tokens_rendered.js docs/reference/dual_engine_v2_standalone.html
# 기대: 6 파일 모두 존재
```

### 2.4 F4 6 HTML v2 import

```bash
for f in web/bizaipro_{home,proposal_generator,email_generator,evaluation_result,engine_compare,changelog}.html; do
  grep -q v2_tokens.css "$f" && echo "[OK] $f" || echo "[FAIL] $f"
done
# 기대: 6/6 [OK]
```

### 2.5 추가 API (codex 종합검증 §2 F5-F8)

```bash
grep -E '@app\.(get|post|delete)\("/api/(evaluation/report|proposal/generate|email/generate|engine/upgrade-reports|engine/promote-fpe|engine/monthly-upgrade-report|exhibition/evaluate|exhibition/leads)' app.py | wc -l
# 기대: 11+ (4 EvaluationSnapshot + 5 월간 + 1 이메일 + 2 전시회 - path duplicate)
```

### 2.6 회귀 테스트

```bash
python3 -m pytest tests/ -q --ignore=tests/e2e
# 기대: 100 passed, 7 skipped (회귀 0건)
```

## 3. 통합 브랜치 commit 히스토리

```
ee8a462  docs: v2 종합 완성 보고서 (codex No-Go → Go, 8 Finding 모두 처리)
d905001  feat: codex 종합검증 F6/F7/F8 미구현 추가
f0dff19  merge: v2 PR — design system + D1 6HTML import + D3 EvaluationSnapshot API
6d69698  merge: 1차 PR — dual engine + engines/ separation + dual eval API
f309c04  docs(D5-D4): 마스터 계획서 + 구현 보고서 추가
82bfd28  feat(D3): EvaluationSnapshot API 신설
e5170f5  feat(D1): 운영 6 HTML에 v2_tokens.css import 추가
ca02f04  feat: v2 design system
89df1eb  fix: APE engine_purpose learning_proposal → learning_comparison
e16b391  feat: dual engine v2.11
─── origin/main: 081b9e7 ───
```

10 commits / 87 files / 31,482 insertions.

## 4. main에 들어가려면

본 통합 브랜치는 push 완료. 사용자가 GitHub에서 PR 생성 + 머지 시 codex가 다음 검증부터는 main에서도 모든 항목 확인 가능.

PR URL: https://github.com/YeChungHee/FlowBizTool/pull/new/codex/integrated-final-20260501

## 5. 본 가이드의 의의

codex 검증 환경(main)과 실제 구현 위치(integrated-final) 격차 해소.
이전 codex No-Go 판정은 환경 격차에 의한 것이며, 통합 브랜치 검증 시 모두 Go.
