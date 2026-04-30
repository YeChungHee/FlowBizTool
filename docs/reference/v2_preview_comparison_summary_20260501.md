# v2 미리보기 vs Standalone 비교 결과 요약 (PR 추적용)

- 문서번호: FBU-CMP-V2-PREVIEW-SUMMARY-20260501
- 작성일: 2026-05-01
- 작성자: [claude]
- 출처: `outputs/reference/comparison/v2_preview_comparison_report.md` (gitignore — generated)
- 용도: P2-3 [codex] B1 정정 — outputs/는 git 추적 안 됨, 본 요약을 docs/에 보관
- 관련:
  - `scripts/compare_v2_preview_vs_standalone.js` (재실행 가능)
  - `web/v2_preview.html` (B1 산출물)
  - `web/styles/v2_components.css` (22 컴포넌트)
  - `[codex]flowbiz_ui_v2_b1_preview_validation_20260501.md` (본 요약 트리거)

## 1. 검증 범위 (P2-1 [codex] 정정)

본 비교는 **body/card/header 중심 10개 computed style 기준**입니다.

| 검증 항목 | 포함 |
|---|:---:|
| body bg/color/fontFamily/fontSize | ✅ (4 항목) |
| card bg/borderRadius/padding | ✅ (3 항목) |
| header bg/color/height | ✅ (3 항목) |
| **22 컴포넌트 전체** | ❌ (별도 검증 필요) |
| **픽셀 단위 정합** | ❌ (별도 검증 필요) |
| **인터랙션** | ❌ (별도 검증 필요) |
| **반응형 토큰 (P2-2 보강)** | ✅ desktop/tablet/mobile 3 viewport |

## 2. 결과 요약

### 2.1 핵심 토큰 일치율

**`핵심 10개 computed style 기준 100% 일치 (10/10)`** — desktop 1200×900

| # | 속성 | Standalone | v2_preview | 일치 |
|---|---|---|---|:---:|
| 1 | body bg | `#F9FAFB` | `#F9FAFB` | ✅ |
| 2 | body color | `#191F28` | `#191F28` | ✅ |
| 3 | body fontFamily | Pretendard, ... | Pretendard, ... | ✅ |
| 4 | body fontSize | `16px` | `16px` | ✅ |
| 5 | card bg | `#FFFFFF` | `#FFFFFF` | ✅ |
| 6 | card borderRadius | `12px` | `12px` | ✅ |
| 7 | card padding | `20px` | `20px` | ✅ |
| 8 | header bg | `#FFFFFF` | `#FFFFFF` | ✅ |
| 9 | header color | `#191F28` | `#191F28` | ✅ |
| 10 | header height | `60px` | `60px` | ✅ |

### 2.2 반응형 검증 (P2-2 [codex] B1 정정 + F1 [codex] B1-P2-fix 정정)

| Viewport | Width × Height | 검증 결과 |
|---|---|:---:|
| **desktop** | 1200 × 900 | ✅ 토큰 100% + 레이아웃 정상 |
| **tablet (iPad Air)** | **820 × 1180** | ✅ 토큰 100% + 5열→3열 reflow (1024px 미디어쿼리 적용) |
| **mobile (iPhone 14 Pro)** | 390 × 844 | ✅ 토큰 100% + 1열 reflow + nav 가로 스크롤 + overflow 0 |

> 토큰(컬러/폰트/radius)은 viewport 무관 100% 일치. 레이아웃은 미디어쿼리로 reflow 처리.
>
> **태블릿 viewport 820px 채택 사유** (codex B1-P2-fix F1 정정): 기존 768px은 모바일 미디어쿼리(`@media (max-width: 768px)`) 경계에 걸려 1열 reflow되어 1024px 미디어쿼리(`@media (max-width: 1024px)`) 검증이 불가능했음. 820px (iPad Air width)로 변경하여 1024px 미디어쿼리만 정상 적용 검증.

## 3. 본 검증으로 확인된 사항

1. **시각 정체성 일치**: 흰색-회색 톤 (`#F9FAFB` body, `#FFFFFF` card)
2. **폰트 일치**: Pretendard 1순위 (Toss/Pretendard 디자인 시스템)
3. **컴포넌트 메트릭 일치**: card 12px radius / 20px padding / header 60px height
4. **반응형 안정성**: 1200px/820px/390px 모두 핵심 토큰 100% 일치 + overflow 0
5. **모바일 horizontal overflow 차단**: box-sizing border-box + body overflow-x:hidden 보조 (codex B1-P2-fix F3 정정)

## 4. 본 검증으로 확인되지 않은 사항 (별도 검증 필요)

| 항목 | 검증 시점 | 방법 |
|---|---|---|
| 22 컴포넌트 전체 시각 정합 | Phase 2 마이그레이션 시 | 화면별 Playwright 스크린샷 |
| 픽셀 단위 정합 | Phase 5 픽셀 비교 단계 | `pixelmatch` 또는 `playwright-visual-comparison` |
| 인터랙션 (hover/focus/click) | Phase 2-3 | E2E spec |
| AppleGothic fallback (Windows/Linux) | Phase 5 | 환경별 스크린샷 |
| 다크모드 (향후) | (계획 외) | 현재 미정 |

## 5. 산출물 (재생성 가능)

```
outputs/reference/comparison/   ← gitignore (generated)
├── standalone_desktop.png      (1200×900)
├── standalone_tablet.png       (820×1180)   ← codex B1-P2-fix F1 정정 (768→820)
├── standalone_mobile.png       (390×844)
├── v2_preview_desktop.png      (1200×900)
├── v2_preview_tablet.png       (820×1180)   ← codex B1-P2-fix F1 정정
├── v2_preview_mobile.png       (390×844)
└── v2_preview_comparison_report.md  (3 viewport 통합 + viewport별 자동 비교 + overflow assertion)
```

**재생성 명령**:
```bash
cd /Users/appler/Documents/COTEX/FlowBiz_ultra
# 8011 서버 기동 상태에서:
node scripts/compare_v2_preview_vs_standalone.js
```

## 6. PR 검증 절차에 포함 권장

PR 리뷰 시 다음 명령으로 본 검증 재현 가능:

```bash
# 사전 조건
npm install                        # @playwright/test
npm run test:install               # chromium

# 8011 서버 기동
nohup python3 -m uvicorn app:app --host 127.0.0.1 --port 8011 \
  > /tmp/uvicorn8011.log 2>&1 &

# 비교 실행
node scripts/compare_v2_preview_vs_standalone.js

# 결과 확인 (gitignore 산출물)
ls outputs/reference/comparison/
cat outputs/reference/comparison/v2_preview_comparison_report.md
```

## 7. 관련 codex 검증 보고서 처리

| codex 검증 | 처리 결과 |
|---|---|
| `[codex]flowbiz_ui_v2_b1_preview_validation_20260501.md` §5 P2-1 (표현 범위) | ✅ 본 요약 §1 + 보고서 §0 명시 |
| 동 §5 P2-2 (반응형 768/390 추가) | ✅ compare 스크립트 3 viewport 보강 + v2_components.css 미디어쿼리 |
| 동 §5 P2-3 (outputs/ git 미추적) | ✅ 본 요약을 `docs/reference/`에 보관 + 재실행 명령 §6 |
| `[codex]flowbiz_ui_v2_b1_p2_fix_revalidation_20260501.md` F1 (768 vs CSS) | ✅ 태블릿 820×1180으로 변경 |
| 동 F2 (3 viewport 자동 비교) | ✅ viewport별 matchRate/matches/totalCmp 자동 출력 |
| 동 F3 (모바일 overflow 10px) | ✅ 14 컴포넌트 box-sizing + scrollWidth assertion 0 |
| 동 F4 (화면 문구 과함) | ✅ "핵심 10개 computed style 기준 100%" 정정 |
| `[codex]flowbiz_v2_preview_and_pr_guide_revalidation_20260501.md` §4 F1 P2 (summary stale) | ✅ **본 §2.2 + §5 viewport 768→820 갱신** (본 세션) |

→ **누적 P0/P1/P2 모두 처리 완료** + **본 stale 잔여 정정 완료** → D5 PR 분리 가능.

## 8. 갱신 정책

다음 조건에서 본 요약 갱신:
- `web/v2_preview.html` 또는 `web/styles/v2_components.css` 변경 시 `node scripts/compare_v2_preview_vs_standalone.js` 재실행 → 본 §2 동기화
- `docs/reference/dual_engine_v2_standalone.html` 갱신 시
- 검증 viewport 추가/변경 시 §2.2 갱신
