# FlowScore 추가 정보 리포트 준비

이 문서는 `추가 정보`로 제공되는 FlowScore 신용평가 PDF를 학습과 평가에 재사용하기 위해 어떤 형태로 준비했는지 정리합니다.

## 목적

FlowScore PDF는 화면용 보고서이기 때문에 그대로는 필드 추출이 불안정할 수 있습니다.  
그래서 아래 두 단계를 거쳐 재사용 가능한 구조로 바꿉니다.

1. PDF 텍스트를 추출한다.
2. 파싱용 정규화 텍스트로 바꾼 뒤 핵심 필드를 JSON으로 저장한다.

## 준비한 파일

1. 파서
   - [report_extractors.py](/Users/appler/Documents/COTEX/FlowBiz_ultra/report_extractors.py)
2. 정규화 샘플
   - [breedb_flowscore_additional_info.json](/Users/appler/Documents/COTEX/FlowBiz_ultra/sample_inputs/breedb_flowscore_additional_info.json)

## 현재 확인된 학습 가능 상태

대상 파일:
- `/Users/appler/Downloads/신용평가리포트_(주)브리드비인터내셔널_2026-03-20.pdf`

현재 파서가 안정적으로 읽는 값:
1. 기업명
2. 사업자번호
3. 신용등급
4. 종합점수
5. 부도확률(PD)
6. 월간 적정 신용한도
7. 평가일
8. 설립일
9. 5차원 점수 일부
10. 주요 긍정/부정 요인

현재 보정이 더 필요한 부분:
1. 재무 요약표를 연도별 구조로 더 안정적으로 읽는 부분

## 사용 방법

CLI로 바로 정규화 JSON을 만들 수 있습니다.

```bash
python3 report_extractors.py "/Users/appler/Downloads/신용평가리포트_(주)브리드비인터내셔널_2026-03-20.pdf" --out sample_inputs/breedb_flowscore_additional_info.json
```

API로도 바로 읽을 수 있습니다.

```bash
curl -X POST http://127.0.0.1:8011/api/report/flowscore-parse \
  -F "file=@/Users/appler/Downloads/신용평가리포트_(주)브리드비인터내셔널_2026-03-20.pdf"
```

## 현재 판단

이 리포트는 `학습 가능`입니다.  
다만 `재무 요약표 추출 보정 필요` 이슈가 있어, 자동 학습 시에는 아래 원칙으로 쓰는 것이 적절합니다.

1. 기업명, 사업자번호, 등급, 점수, PD, 적정 한도는 바로 사용
2. 재무표는 보조 근거로 사용
3. 평가 엔진 입력에 넣을 때는 `추가 정보 자료`로 연결
4. 자동 추출 결과가 비면 원문 PDF를 같이 보관
