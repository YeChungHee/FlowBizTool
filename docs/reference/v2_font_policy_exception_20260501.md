# v2 Standalone 폰트 정책 예외 (Pretendard 1순위 채택 근거)

- 작성일: 2026-05-01
- 작성자: [claude]
- 사유: P2-2 [codex] 정정 — AGENTS 기본 폰트 정책(AppleGothic) vs v2 rendered Pretendard
- 출처:
  - `[codex]flowbiz_ui_v2_phase0_token_validation_20260501.md` §6 P2-2
  - `outputs/reference/v2_tokens_rendered.json` (rendered DOM 실측)

## 1. 결론

**v2 standalone 디자인의 폰트 stack은 Pretendard 1순위, AppleGothic은 fallback로 유지**.

```css
--fbu-font-family:
  "Pretendard",                  /* ← 1순위 (rendered 채택) */
  "Spoqa Han Sans Neo",          /* ← 2순위 */
  -apple-system,                 /* ← 3순위 */
  "system-ui",
  "Apple SD Gothic Neo",
  "Malgun Gothic",
  "Segoe UI",
  Roboto,
  sans-serif;
```

## 2. 정책 충돌 검토

| 정책 출처 | 내용 |
|---|---|
| **AGENTS 기본 정책** (프로젝트 루트) | 한국어 UI는 **AppleGothic** 우선 |
| **3차 PR §3.3 #6** (UI 샘플 검증 origin) | "AppleGothic Human Interface 기준" |
| **v7 [claude] §3 (이전)** | AppleGothic 1순위 |
| **v2 standalone rendered DOM 실측** | **Pretendard 1순위 + Spoqa Han Sans Neo + AppleGothic-계열은 4순위 fallback** |

→ **3 정책 vs 1 실측**. 다수결로는 AppleGothic이지만, **본 v2 디자인 시스템은 Pretendard 기반으로 설계됨**.

## 3. 사용자 결정 (2026-05-01)

> "standalone 그대로 흰색으로"

→ standalone 디자인의 시각 정체성을 그대로 유지하라는 명시. Pretendard 채택의 근거.

## 4. 채택 근거 (rendered DOM 실측)

```text
$ npm run extract:tokens
[INFO] computed style 수집 (50+ 영역)...
Body font: Pretendard, "Spoqa Han Sans Neo", -apple-system, "system-ui",
           "Apple SD Gothic Neo", "Malgun Gothic", "Segoe UI", Roboto, sans-serif
```

→ `getComputedStyle(document.body).getPropertyValue('font-family')` 결과 — standalone HTML의 인텐션 디자인.

## 5. 적용 범위

| 영역 | 폰트 정책 |
|---|---|
| **v2 디자인 시스템 (`web/styles/v2_tokens.css`)** | **Pretendard 1순위** ✅ (본 예외 적용) |
| **v2 마이그레이션된 페이지** (Phase 2-3) | Pretendard 1순위 |
| **신규 v2 컴포넌트** (`v2_components.css`) | Pretendard 1순위 |
| 기존 페이지 (마이그레이션 전) | 기존 폰트 stack 유지 (`bizaipro_shared.css`) |
| 외부 시스템 / API 응답 | 영향 없음 |
| AGENTS 정책 적용 다른 도구 | AppleGothic 1순위 (그대로) |

## 6. Fallback 보장

Pretendard가 시스템에 미설치된 경우:
1. Spoqa Han Sans Neo (Toss/네이버 OSS 한글 폰트)
2. -apple-system (macOS/iOS Safari)
3. system-ui (브라우저 기본)
4. Apple SD Gothic Neo (macOS/iOS 한글)
5. Malgun Gothic (Windows 한글)
6. Segoe UI (Windows 영문)
7. Roboto (Android)
8. sans-serif (최종)

→ 모든 OS에서 적절한 한글 sans-serif fallback 보장.

## 7. 후속 구현자를 위한 가이드

**❌ 다음 패턴은 본 v2 디자인 시스템에서 사용 금지**:
```css
/* AppleGothic 1순위로 되돌리는 패턴 — v2에서 적용 금지 */
font-family: "AppleGothic", -apple-system, BlinkMacSystemFont, sans-serif;
```

**✅ v2 디자인 시스템에서는 다음 변수 사용**:
```css
font-family: var(--fbu-font-family);
```

**✅ 새 컴포넌트 작성 시**:
- `web/styles/v2_components.css`에 추가
- font-family는 `var(--fbu-font-family)` 또는 body 상속 (생략 가능)
- AGENTS 정책 인용으로 AppleGothic 1순위 강제 시 본 문서로 우선순위 검토

## 8. 본 예외의 검토 시점

다음 조건에서 본 예외 재검토:
- standalone HTML이 AppleGothic 우선 stack으로 갱신됨 (npm run extract:tokens 결과 변경)
- 사용자가 명시적으로 AppleGothic 1순위 환원 요청
- Pretendard 라이선스/배포 정책 변화

→ 그 외에는 본 정책(Pretendard 1순위) 유지.

## 9. 관련 문서

- `web/styles/v2_tokens.css` line 132-142 (font-family 정의)
- `outputs/reference/v2_tokens_rendered.json` `body.fontFamily` (실측 baseline)
- `docs/reference/v2_tokens_summary_20260501.md` §2 (본 예외와 정합 baseline)
- `[codex]flowbiz_ui_v2_phase0_token_validation_20260501.md` §6 P2-2 (본 문서 트리거)
