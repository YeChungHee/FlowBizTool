# FlowPay 세일즈 자동화 엔진

국내 주요 자본시장용 신용평가사 공개 방법론과 플로우페이 거래 구조를 참고해 만든 `영업 참고용 거래 가설 평가 + 제안서/이메일 자동화 엔진`입니다.

현재 반영한 기관:

- 한국신용평가(KIS)
- NICE신용평가
- 한국기업평가(KR)

이 프로젝트는 실제 신용평가사의 내부 비공개 스코어카드를 복제한 것이 아니라, 공개된 평가 개요와 평가요소를 공통 프레임으로 통합해 `거래 가능성`, `예상 한도`, `예상 마진율`을 영업 관점에서 추정하는 설명 가능한 도구입니다.

중요:
- 이 도구는 `공식 심사 결과`를 확정하지 않습니다.
- 이 도구는 `세일즈 참고용 기업평가 보고서`, `제안서`, `이메일 초안`을 만드는 데 목적이 있습니다.

## 구성

- [docs/integrated_credit_rating_comparison.md](/Users/appler/Documents/COTEX/FlowBiz_ultra/docs/integrated_credit_rating_comparison.md)
  기관별 비교표와 통합 평가축 설명
- [docs/flowpay_service_learning.md](/Users/appler/Documents/COTEX/FlowBiz_ultra/docs/flowpay_service_learning.md)
  플로우페이 서비스 구조와 심사 포인트 학습 노트
- [docs/flowpay_3m_methodology.md](/Users/appler/Documents/COTEX/FlowBiz_ultra/docs/flowpay_3m_methodology.md)
  플로우페이 3개월 채권 생존성 평가 방법론
- [docs/flowpay_manual_reflection.md](/Users/appler/Documents/COTEX/FlowBiz_ultra/docs/flowpay_manual_reflection.md)
  플로우페이 심사 매뉴얼 학습 내용과 엔진 반영 사항
- [docs/flowpay_atude_sample.md](/Users/appler/Documents/COTEX/FlowBiz_ultra/docs/flowpay_atude_sample.md)
  에이튜드 상담내용과 기업 리포트를 반영한 샘플 케이스
- [docs/flowpay_atude_approval_path.md](/Users/appler/Documents/COTEX/FlowBiz_ultra/docs/flowpay_atude_approval_path.md)
  에이튜드 케이스를 APPROVE로 끌어올리기 위한 개선 경로
- [docs/flowpay_atude_underwriting_report.md](/Users/appler/Documents/COTEX/FlowBiz_ultra/docs/flowpay_atude_underwriting_report.md)
  에이튜드 케이스 내부 심사보고서 초안
- [docs/flowpay_atude_proposal_draft.md](/Users/appler/Documents/COTEX/FlowBiz_ultra/docs/flowpay_atude_proposal_draft.md)
  에이튜드 대상 외부 제안서 초안
- [data/integrated_credit_rating_framework.json](/Users/appler/Documents/COTEX/FlowBiz_ultra/data/integrated_credit_rating_framework.json)
  엔진이 읽는 평가축, 세부지표, 가중치, 등급구간
- [data/api_keys.example.json](/Users/appler/Documents/COTEX/FlowBiz_ultra/data/api_keys.example.json)
  ECOS/DART 연동용 로컬 설정 예시
- [docs/flowpay_api_enrichment.md](/Users/appler/Documents/COTEX/FlowBiz_ultra/docs/flowpay_api_enrichment.md)
  한국은행 ECOS와 DART를 심사엔진에 반영하는 규칙 설명
- [engine.py](/Users/appler/Documents/COTEX/FlowBiz_ultra/engine.py)
  CLI 실행용 평가엔진
- [external_apis.py](/Users/appler/Documents/COTEX/FlowBiz_ultra/external_apis.py)
  ECOS/DART 공식 API 조회와 점수화 로직
- [proposal_generator.py](/Users/appler/Documents/COTEX/FlowBiz_ultra/proposal_generator.py)
  BizAiPro 제안서 초안 생성 로직
- [report_extractors.py](/Users/appler/Documents/COTEX/FlowBiz_ultra/report_extractors.py)
  FlowScore 신용평가 PDF를 학습/평가용 정규화 JSON으로 바꾸는 파서
- [bizaipro_learning.py](/Users/appler/Documents/COTEX/FlowBiz_ultra/bizaipro_learning.py)
  BizAiPro 학습 후보 적재, 10건 단위 업데이트, 전후 비교 리포트 생성
- [docs/bizaipro_learning_loop.md](/Users/appler/Documents/COTEX/FlowBiz_ultra/docs/bizaipro_learning_loop.md)
  BizAiPro 학습 루프, 버전명 규칙, 가중치 기준 설명
- [sample_inputs/manufacturing_case.json](/Users/appler/Documents/COTEX/FlowBiz_ultra/sample_inputs/manufacturing_case.json)
  예시 입력 파일
- [sample_inputs/flowpay_3m_case.json](/Users/appler/Documents/COTEX/FlowBiz_ultra/sample_inputs/flowpay_3m_case.json)
  플로우페이 3개월 채권 생존성 예시 입력
- [sample_inputs/flowpay_underwriting_case.json](/Users/appler/Documents/COTEX/FlowBiz_ultra/sample_inputs/flowpay_underwriting_case.json)
  플로우페이 종합 심사용 예시 입력
- [sample_inputs/flowpay_atude_case.json](/Users/appler/Documents/COTEX/FlowBiz_ultra/sample_inputs/flowpay_atude_case.json)
  에이튜드 실제 상담/리포트 기반 샘플 입력
- [sample_inputs/flowpay_atude_approve_target.json](/Users/appler/Documents/COTEX/FlowBiz_ultra/sample_inputs/flowpay_atude_approve_target.json)
  에이튜드 승인목표 시뮬레이션 입력
- [sample_inputs/breedb_flowscore_additional_info.json](/Users/appler/Documents/COTEX/FlowBiz_ultra/sample_inputs/breedb_flowscore_additional_info.json)
  FlowScore 추가 정보 리포트를 정규화한 샘플 입력
- [docs/flowscore_additional_info_preparation.md](/Users/appler/Documents/COTEX/FlowBiz_ultra/docs/flowscore_additional_info_preparation.md)
  FlowScore PDF를 추가 정보 자료로 준비하는 기준과 사용법

## 빠른 실행

```bash
python3 engine.py --show-table
python3 engine.py --input sample_inputs/manufacturing_case.json
python3 engine.py --input sample_inputs/flowpay_3m_case.json
python3 engine.py --input sample_inputs/flowpay_underwriting_case.json
python3 engine.py --input sample_inputs/flowpay_atude_case.json
python3 engine.py --input sample_inputs/flowpay_atude_approve_target.json
python3 engine.py --input sample_inputs/flowpay_atude_case.json --bundle-out outputs/atude_bundle
python3 bizaipro_learning.py status
python3 bizaipro_learning.py record --input sample_inputs/flowpay_atude_case.json --label "에이튜드 1차"
python3 bizaipro_learning.py update
```

## ECOS / DART 설정

엔진은 아래 두 방식 중 하나로 공식 API 키를 읽습니다.

1. 환경변수

```bash
export ECOS_API_KEY="..."
export DART_API_KEY="..."
```

2. 로컬 설정 파일

`/Users/appler/Documents/COTEX/FlowBiz_ultra/data/api_keys.local.json`

```json
{
  "ecos_api_key": "YOUR_ECOS_KEY",
  "dart_api_key": "YOUR_DART_KEY"
}
```

`api_keys.local.json`은 로컬 전용 파일로 사용하고, 저장소 공유 대상에서는 제외하는 것을 권장합니다.

## FlowScore 추가 정보 리포트 파싱

추가 정보로 제공되는 FlowScore PDF는 아래 명령으로 정규화 JSON으로 바꿀 수 있습니다.

```bash
python3 report_extractors.py "/path/to/flowscore_report.pdf" --out sample_inputs/parsed_flowscore_report.json
```

FastAPI 서버를 띄운 경우 아래 API로도 바로 읽을 수 있습니다.

```bash
curl -X POST http://127.0.0.1:8011/api/report/flowscore-parse \
  -F "file=@/path/to/flowscore_report.pdf"
```

## 입력 형식

입력 파일은 JSON이며, 각 세부 평가요소를 `0~100` 범위로 넣습니다.

```json
{
  "company_name": "Sample Manufacturing Co.",
  "industry": "General Manufacturing",
  "modifiers": {
    "event_risk": -2,
    "support_uplift": 1
  },
  "scores": {
    "management_risk": {
      "governance": 70,
      "transparency": 74,
      "strategy_consistency": 76,
      "management_capability": 78,
      "internal_control": 72
    }
  }
}
```

## 출력 내용

- 통합 평가 점수
- 기관별 관점 점수
- 예비 등급
- 핵심 강점/약점
- 범주별 세부 점수

플로우페이 3개월 채권 입력의 경우:

- 3개월 생존성 점수
- 생존 판단 등급
- 암시적 생존확률 구간
- 중소기업 재무신뢰도 헤어컷
- 데이터 신뢰도 수준

플로우페이 종합 심사 입력의 경우:

- 신청사/매출처/거래구조 통합 평가
- ECOS 업황/금리/물가 및 DART 공시정보 기반 외부신호 보강
- 1~5개월 부도확률 곡선
- 예상 1회 거래 한도액
- 영업 참고용 마진율과 보수적 기준 마진율 비교
- 거래 가능성 추천 문구
- 추가 확인 신호와 위험 포인트
- 영업 참고 요약문
- BizAiPro 제안서 초안
- 고객 발송용 이메일 초안
- 거래 가설 평가 리포트

`--bundle-out` 옵션을 사용하면 아래 파일이 한 번에 저장됩니다.
- `sales_summary.txt`
- `sales_report.md`
- `proposal_draft.md`
- `sales_email_draft.txt`

## 페이지 샘플

`BizAiPro리포트 생성 페이지` 샘플은 아래 파일에서 바로 볼 수 있습니다.

- [web/bizaipro_report_page_sample.html](/Users/appler/Documents/COTEX/FlowBiz_ultra/web/bizaipro_report_page_sample.html)

이 샘플 페이지에는 아래 항목이 포함되어 있습니다.
- 플로우스코어 리포트, 상담보고서, 추가 정보, 내부심사리포트 입력폼
- 신청업체/매출처/거래구조/통합 점수의 해석 카드
- `왜 이 점수가 나왔는지`를 보여주는 계산식 섹션
- 점수별 등급과 등급의 의미
- 학습 적격 여부, 업데이트 생성 여부, 반영된 가중치
- 맥킨지 스타일 BizAiPro리포트 미리보기

## 한계

- 공식 공개 방법론 기반의 교육용/사내용 예비엔진입니다.
- 실제 위원회 판단, 비공개 내부 가중치, 업종별 세밀한 오버레이는 완전히 반영하지 못합니다.
- 최종 투자판단이나 공식 등급의 대체 수단이 아닙니다.
- `flowpay_3m_receivable` 모드는 장기 기업신용등급이 아니라, 플로우페이형 거래의 `3개월 단기 생존성`을 보기 위한 별도 모델입니다.
- `flowpay_underwriting` 모드는 심사 매뉴얼 분석 보고서의 권고를 반영했지만, 실제 목적은 `세일즈 자동화용 거래 가설 평가`입니다.
