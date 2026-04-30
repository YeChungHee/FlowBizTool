# v2 Standalone Rendered DOM 토큰 요약 (PR 추적용)

- 작성일: 2026-05-01
- 작성자: [claude]
- 출처: `outputs/reference/v2_tokens_rendered.json` (gitignore — generated artifact)
- 용도: PR 리뷰 증거 + 재생성 baseline (P2-1 [codex] 정정 — `outputs/`는 git 추적 안 됨)
- 관련:
  - `web/styles/v2_tokens.css` (운영 토큰 — 본 요약 기준)
  - `scripts/extract_v2_tokens_rendered.js` (재추출 스크립트)
  - `[claude]flowbiz_ui_v2_standalone_design_implementation_plan_v7_20260430.md`
  - `[codex]flowbiz_ui_v2_phase0_token_validation_20260501.md`

## 1. 추출 메타

| 항목 | 값 |
|---|---|
| 추출 일시 | 2026-04-30T15:03:01.112Z (UTC) |
| 출처 HTML | `docs/reference/dual_engine_v2_standalone.html` |
| viewport | 1200×800 |
| Engine | Chromium (Playwright 1.59.1) |
| 스크립트 | v2 (A3 selector 보강) |
| 전체 element 수 | 338 |

## 2. Body 기본

| 속성 | 값 |
|---|---|
| background | `#F9FAFB` |
| color | `#191F28` |
| font-family | `Pretendard, "Spoqa Han Sans Neo", -apple-system, "system-ui", "Apple SD Gothic Neo", "Malgun Gothic", "Segoe UI", Roboto, sans-serif` |
| font-size | `16px` |

## 3. Top 10 Background 색상 (사용 빈도)

| # | hex | 사용 횟수 | 용도 |
|---|---|---:|---|
| 1 | `#FFFFFF` | 22 | card / button / 흰 영역 |
| 2 | `#2D54D6` | 6 | primary action (blue) |
| 3 | `#1FA45D` | 6 | success (green) |
| 4 | `#F2F4F6` | 5 | section bg |
| 5 | `#6B7684` | 5 | muted bg |
| 6 | `#E8EDFE` | 4 | primary pale |
| 7 | `#FAAD14` | 3 | warning (orange) |
| 8 | `#F9FAFB` | 2 | body bg |
| 9 | `#191F28` | 2 | dark bg |
| 10 | `#F0FAF3` | 2 | success pale |

## 4. Top 10 Text 색상 (사용 빈도)

| # | hex | 사용 횟수 | 용도 |
|---|---|---:|---|
| 1 | `#191F28` | 134 | text-primary (gray-900) |
| 2 | `#333D4B` | 61 | text-secondary (gray-700) |
| 3 | `#4E5968` | 51 | text-tertiary (gray-600) |
| 4 | `#8B95A1` | 32 | text-muted (gray-400) |
| 5 | `#FFFFFF` | 28 | text on dark |
| 6 | `#E42939` | 4 | error |
| 7 | `#2D54D6` | 3 | primary link |
| 8 | `#1C327D` | 3 | primary dark |
| 9 | `#043EC4` | 3 | primary darker |
| 10 | `#0D5F36` | 3 | success dark |

## 5. Border Radius 분포

| radius | 사용 횟수 | 용도 |
|---|---:|---|
| `999px` | 23 | pill / 합의 배지 |
| `6px` | 16 | input / chip |
| `8px` | 15 | small card |
| `50%` | 12 | avatar |
| `10px` | 8 | button |
| `12px` | 7 | card primary |

## 6. Font-size 분포 (큰 → 작은)

| 크기 | 사용 횟수 | 용도 |
|---|---:|---|
| `24px` | 1 | KPI display (h3 weight 800) |
| `22px` | 4 | h1 |
| `18px` | 2 | h2 |
| `16px` | 139 | base 본문 (압도적) |
| `14px` | 5 | small |
| `13px` | 52 | xs (라벨/버튼) |
| `12px` | 83 | xxs (작은 버튼/칩) |
| `11px` | 39 | 3xs (메타) |
| `10px` | 9 | 4xs (부가) |

## 7. 컴포넌트별 실측

### 7.1 Card

| 속성 | 값 |
|---|---|
| 클래스 (rendered) | `.card` |
| background | `#FFFFFF` |
| border | `1px solid #E5E8EB` |
| border-radius | `12px` |
| padding | `20px` |

### 7.2 Header (`.topbar`)

| 속성 | 값 |
|---|---|
| tag | `<header>` |
| background | `#FFFFFF` (검정 아님 ✓ 사용자 확정) |
| color | `#191F28` |
| height | `60px` |
| padding | `0 24px` |

### 7.3 Primary Button

| 속성 | 값 |
|---|---|
| background | `#2D54D6` |
| color | `#FFFFFF` |
| border-radius | `10px` |
| padding | `6px 10px` (small) / `8px 14px` (large) |
| font-size | `12px` (small) / `13px` (large) |

### 7.4 Secondary Button

| 속성 | 값 |
|---|---|
| background | `#FFFFFF` |
| color | `#333D4B` |
| border | `1px solid #D1D6DB` |
| border-radius | `10px` |
| padding | `6px 10px` |

### 7.5 KPI Display

| 속성 | 값 |
|---|---|
| tag | `<h3>` |
| font-size | `24px` (84px 가정 폐기) |
| font-weight | `800` (heavy) |
| line-height | `32.4px` (1.35 ratio) |
| color | `#FFFFFF` (다크 배경 위) |

## 8. 폐기된 v1 가정 (사용자 결정 2026-05-01)

| v1 가정 (SVG thumbnail) | rendered 실측 | 채택 |
|---|---|---|
| 베이지 `#F5F4EE` | `#F9FAFB` (gray-50) | ✅ rendered |
| 검정 헤더 `#0F1115` | `#FFFFFF` (흰색 헤더) | ✅ rendered |
| AppleGothic 1순위 | Pretendard 1순위 | ✅ rendered |
| 84px KPI display | 24px KPI display | ✅ rendered |
| 8px card radius | 12px card radius | ✅ rendered |
| 6 nav 항목 다크 헤더 | `.topbar` 흰색 헤더 | ✅ rendered |

## 9. 재생성 명령

```bash
cd /Users/appler/Documents/COTEX/FlowBiz_ultra
npm install                # 1회
npm run test:install       # 1회 (chromium)
npm run extract:tokens     # 매회 재추출

# 결과
ls outputs/reference/
#   v2_tokens_rendered.json
#   v2_tokens_rendered.css
#   v2_tokens_analysis_report.md
```

## 10. 본 요약 갱신 정책

- standalone HTML 갱신 시 → `npm run extract:tokens` 재실행 → 본 요약 수동 갱신
- 토큰 변경 시 → v2_tokens.css 갱신 + 본 요약 §3-§7 동기화
- 새 컴포넌트 추가 시 → §7에 행 추가
