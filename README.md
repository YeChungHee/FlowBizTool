# FlowBizTool

`BizAiPro` 평가엔진을 기반으로 만든 플로우페이 세일즈 자동화 도구입니다.  
기업리포트, 상담보고서, 심사보고서, 전시회 공개정보를 읽어 `평가 결과`, `제안서`, `이메일 초안`까지 한 흐름으로 만드는 것을 목표로 합니다.

## 프로젝트 성격

- 이 저장소는 `공식 심사 확정 시스템`이 아닙니다.
- 목적은 `세일즈 참고용 평가`, `예상 한도/마진`, `제안서`, `이메일 자동화`입니다.
- 국내 주요 신용평가사 공개 방법론과 플로우페이 거래 구조를 참고해 설명 가능한 엔진 형태로 구현했습니다.

핵심 학습 대상:
- 한국신용평가(KIS)
- NICE신용평가
- 한국기업평가(KR)

## 핵심 기능

- 기업리포트 PDF 파싱
- 상담보고서/심사보고서 Notion 링크 읽기
- 학습모드 / 전시회모드 입력 분기
- 플로우페이 거래 가설 평가
- 예상 한도액 / 예상 마진율 / 결제유예기간 표시
- BizAiPro 제안서 초안 생성
- 이메일 템플릿 6종 자동 생성
- 최근 실제 학습 데이터 대시보드

## 주요 파일

### 백엔드

- [`app.py`](./app.py)
  FastAPI 서버, 웹앱 API, 학습모드/전시회모드 처리
- [`engine.py`](./engine.py)
  통합 평가엔진 및 플로우페이 종합 평가 로직
- [`external_apis.py`](./external_apis.py)
  ECOS / DART 연동 로직
- [`report_extractors.py`](./report_extractors.py)
  FlowScore 계열 PDF 파서
- [`proposal_generator.py`](./proposal_generator.py)
  제안서 초안 생성
- [`bizaipro_learning.py`](./bizaipro_learning.py)
  학습 후보 적재, 10건 단위 업데이트, 비교 리포트 생성

### 웹 화면

- [`web/bizaipro_home.html`](./web/bizaipro_home.html)
  메인 홈 / 입력 시작
- [`web/bizaipro_evaluation_result.html`](./web/bizaipro_evaluation_result.html)
  평가 결과 페이지
- [`web/bizaipro_proposal_generator.html`](./web/bizaipro_proposal_generator.html)
  제안서 생성 페이지
- [`web/bizaipro_email_generator.html`](./web/bizaipro_email_generator.html)
  이메일 생성 페이지
- [`web/bizaipro_engine_compare.html`](./web/bizaipro_engine_compare.html)
  엔진 버전 비교 페이지
- [`web/bizaipro_shared.js`](./web/bizaipro_shared.js)
  공통 상태/렌더링 로직
- [`web/bizaipro_shared.css`](./web/bizaipro_shared.css)
  공통 UI 스타일

### 데이터 / 문서

- [`data/integrated_credit_rating_framework.json`](./data/integrated_credit_rating_framework.json)
  통합 평가축, 세부지표, 가중치
- [`data/exhibition_company_db_schema.json`](./data/exhibition_company_db_schema.json)
  전시회 기업 DB 스키마
- [`docs/integrated_credit_rating_comparison.md`](./docs/integrated_credit_rating_comparison.md)
  3사 비교 및 통합 프레임
- [`docs/flowpay_api_enrichment.md`](./docs/flowpay_api_enrichment.md)
  ECOS / DART 반영 규칙
- [`docs/bizaipro_learning_loop.md`](./docs/bizaipro_learning_loop.md)
  학습 루프 / 버전 규칙

## 빠른 시작

### 1. 로컬 서버 실행

```bash
python3 -m uvicorn app:app --host 127.0.0.1 --port 8011
```

브라우저:

- [http://127.0.0.1:8011/web/bizaipro_home.html](http://127.0.0.1:8011/web/bizaipro_home.html)

### 2. CLI 평가엔진 실행

```bash
python3 engine.py --show-table
python3 engine.py --input sample_inputs/manufacturing_case.json
python3 engine.py --input sample_inputs/flowpay_underwriting_case.json
python3 engine.py --input sample_inputs/flowpay_atude_case.json
python3 engine.py --input sample_inputs/flowpay_atude_case.json --bundle-out outputs/atude_bundle
```

### 3. 학습 루프 실행

```bash
python3 bizaipro_learning.py status
python3 bizaipro_learning.py record --input sample_inputs/flowpay_atude_case.json --label "에이튜드 1차"
python3 bizaipro_learning.py update
```

## API 키 설정

엔진은 ECOS / DART API 키를 두 방식 중 하나로 읽습니다.

### 환경변수

```bash
export ECOS_API_KEY="..."
export DART_API_KEY="..."
export NOTION_API_TOKEN="..."
```

### 로컬 설정 파일

`data/api_keys.local.json`

```json
{
  "ecos_api_key": "YOUR_ECOS_KEY",
  "dart_api_key": "YOUR_DART_KEY"
}
```

`data/api_keys.local.json`은 `.gitignore`에 포함되어 있습니다.

## 입력 모드

### 학습모드

아래 자료를 기준으로 평가 결과를 만듭니다.

- 플로우스코어 리포트
- 상담리포트(Notion 링크)
- 상담보고서 파일
- 내부심사보고서(Notion 링크)
- 추가 정보

현재 기준:
- `플로우스코어리포트 + 상담보고서`  
  평가에는 반영되지만 엔진 업데이트 건수에는 반영되지 않음
- `플로우스코어리포트 + 상담보고서 + 심사보고서`  
  엔진 학습 데이터로 인정되고 업데이트 건수에 반영

### 전시회모드

아래 공개정보를 기준으로 콜드세일즈형 평가를 만듭니다.

- 전시회 정보 제공 URL
- 기업 홈페이지 URL
- 기업리포트(선택)
- 플로우스코어 리포트(선택)
- 추가 정보

## 샘플 입력

- [`sample_inputs/manufacturing_case.json`](./sample_inputs/manufacturing_case.json)
- [`sample_inputs/flowpay_3m_case.json`](./sample_inputs/flowpay_3m_case.json)
- [`sample_inputs/flowpay_underwriting_case.json`](./sample_inputs/flowpay_underwriting_case.json)
- [`sample_inputs/flowpay_atude_case.json`](./sample_inputs/flowpay_atude_case.json)
- [`sample_inputs/exhibition_company_sample.json`](./sample_inputs/exhibition_company_sample.json)
- [`sample_inputs/exhibition_kcnc_2026.json`](./sample_inputs/exhibition_kcnc_2026.json)

## 현재 구현 상태

현재 저장소에서 비교적 안정적으로 동작하는 부분:

- FlowScore 계열 리포트 일부 포맷 파싱
- 학습모드 입력 저장 및 결과 화면 반영
- 상담/심사보고서 Notion 링크 읽기 구조
- 제안서 / 이메일 생성 화면
- 실제 학습 데이터 대시보드

아직 계속 고도화가 필요한 부분:

- 리포트 포맷 다양성 대응
- 상담/심사보고서 구조화 품질
- 업황분석/외부신호 반영 정밀도
- 결제유예기간 최적화 로직
- 평가 결과와 문서 생성의 회귀 테스트 체계

## 한계

- 공개 방법론 기반의 내부 참고용 엔진입니다.
- 실제 신용평가사의 비공개 스코어카드나 위원회 판단을 복제하지 않습니다.
- 최종 투자판단, 심사확정, 공식 신용등급의 대체 수단이 아닙니다.

## 참고 문서

- [`docs/integrated_credit_rating_comparison.md`](./docs/integrated_credit_rating_comparison.md)
- [`docs/flowpay_service_learning.md`](./docs/flowpay_service_learning.md)
- [`docs/flowpay_3m_methodology.md`](./docs/flowpay_3m_methodology.md)
- [`docs/flowpay_manual_reflection.md`](./docs/flowpay_manual_reflection.md)
- [`docs/bizaipro_report_page_plan.md`](./docs/bizaipro_report_page_plan.md)
- [`docs/bizaipro_exhibition_coldsales_wireframe.md`](./docs/bizaipro_exhibition_coldsales_wireframe.md)
