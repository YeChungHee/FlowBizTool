# [codex] FlowBizTool v2 B1 미리보기 검증 보고서

- 작성일: 2026-05-01
- 대상: `web/v2_preview.html`, `web/styles/v2_components.css`, `scripts/compare_v2_preview_vs_standalone.js`
- 기준 원본: `docs/reference/dual_engine_v2_standalone.html`
- 비교 URL: `http://127.0.0.1:8011/web/v2_preview.html`

## 1. 검증 결론

B1 산출물은 현재 서버에서 직접 확인 가능하다. `http://127.0.0.1:8011/web/v2_preview.html`은 200 OK로 응답했고, 브라우저에서도 `FlowBizTool v2 — 컴포넌트 미리보기` 페이지가 정상 로드되었다.

`scripts/compare_v2_preview_vs_standalone.js`를 재실행한 결과, 기준 standalone과 v2_preview의 핵심 computed style 비교는 10/10, 100% 일치했다.

다만 이 100%는 전체 화면 픽셀 정합이나 22개 컴포넌트 전체 검증이 아니라, body/card/header 중심의 10개 computed style 항목 기준이다. 사용자 안내 문구와 보고서에는 반드시 "핵심 10개 computed style 기준 100%"로 범위를 명시해야 한다.

## 2. 직접 확인 결과

### 2.1 URL 접근

```text
HTTP/1.1 200 OK
content-type: text/html; charset=utf-8
content-length: 14633
```

### 2.2 파일 존재

| 파일 | 상태 |
|---|---|
| `web/v2_preview.html` | 존재 |
| `web/styles/v2_components.css` | 존재 |
| `web/styles/v2_tokens.css` | 존재 |
| `docs/reference/dual_engine_v2_standalone.html` | 존재 |
| `scripts/compare_v2_preview_vs_standalone.js` | 존재 |

### 2.3 브라우저 확인

브라우저에서 `v2_preview.html`을 열었을 때 다음 요소가 표시되었다.

- `v2 컴포넌트 미리보기 — 22종`
- KPI 카드
- FPE/APE 듀얼 카드
- 합의 배지
- SourceQuality 영역

## 3. 비교 스크립트 재실행 결과

실행 명령:

```bash
node scripts/compare_v2_preview_vs_standalone.js
```

결과:

```text
일치율: 100% (10/10)
Standalone bg:    #F9FAFB
v2_preview bg:    #F9FAFB
Standalone card:  #FFFFFF radius=12px
v2_preview card:  #FFFFFF radius=12px
Standalone hdr:   #FFFFFF h=60px
v2_preview hdr:   #FFFFFF h=60px
```

생성 산출물:

| 산출물 | 상태 |
|---|---|
| `outputs/reference/comparison/standalone.png` | 생성됨 |
| `outputs/reference/comparison/v2_preview.png` | 생성됨 |
| `outputs/reference/comparison/v2_preview_comparison_report.md` | 생성됨 |

## 4. 검증된 computed style 범위

`scripts/compare_v2_preview_vs_standalone.js`가 비교하는 항목은 다음 10개다.

| 구분 | 항목 |
|---|---|
| body | bg, color, fontFamily, fontSize |
| card | bg, borderRadius, padding |
| header | bg, color, height |

따라서 다음 표현은 정확하다.

> 기준 standalone 대비 v2_preview의 핵심 10개 computed style 항목은 100% 일치한다.

다음 표현은 과하다.

> 정합성은 코드 레벨에서 100% 검증됨.

전체 22개 컴포넌트, 반응형 화면, 픽셀 단위 레이아웃, 인터랙션까지 검증한 것은 아니기 때문이다.

## 5. 잔여 Findings

### P2. "100% 검증" 표현 범위를 좁혀야 한다

`compare_v2_preview_vs_standalone.js`는 10개 computed style만 비교한다. 실제 비교 범위는 body/card/header 중심이므로, 사용자 안내와 보고서에서는 "핵심 10개 computed style 기준 100%"라고 써야 한다.

### P2. `v2_preview.html`은 1200px 데스크톱 기준 미리보기다

`web/v2_preview.html`은 `viewport width=1200` 기준으로 작성되어 있고, 좁은 브라우저 폭에서는 헤더 nav가 줄바꿈/클리핑될 수 있다. 운영 페이지 적용 전에는 1200px, 768px, 390px 기준 반응형 스크린샷 검증을 추가해야 한다.

### P2. 비교 산출물은 `outputs/` 아래에 있어 git 추적 대상이 아니다

비교 이미지와 comparison report는 `outputs/reference/comparison/`에 생성되며 `.gitignore` 대상이다. 리뷰 근거를 남기려면 본 `[codex]` 보고서처럼 `docs/` 아래 요약본을 유지하거나, 재실행 명령을 PR 검증 절차에 포함해야 한다.

## 6. 다음 단계 결정

현재 상태에서는 B1 미리보기 산출물 확인은 완료로 볼 수 있다.

다음 작업은 두 갈래로 나누는 것이 안전하다.

1. UI 쪽: `v2_preview.html`의 컴포넌트 클래스를 실제 운영 화면에 단계적으로 연결한다.
2. 백엔드 쪽: EvaluationSnapshot API를 신설한다.

권장 순서:

1. `v2_preview.html`은 사용자 확인용으로 유지
2. 운영 HTML에 `v2_tokens.css` + `v2_components.css` import 적용
3. 주요 화면별 컴포넌트 교체
4. EvaluationSnapshot API 연결
5. 1200/768/390px 반응형 스크린샷 검증

## 7. 최종 판정

B1 산출물은 검증 통과다. 다만 "100% 정합"은 핵심 10개 computed style 기준으로 한정해야 하며, 실제 사용 환경 적용 전에는 반응형 및 운영 페이지 연결 검증이 추가로 필요하다.
