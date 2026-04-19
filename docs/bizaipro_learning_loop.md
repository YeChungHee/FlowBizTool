# BizAiPro Learning Loop

## 목적
BizAiPro는 리포트 생성 결과를 단순 저장하지 않고, 누적된 자료를 바탕으로 주기적으로 엔진을 업데이트한다.

## 기본 규칙
1. 리포트 1건 생성 시 학습 후보 1건 적재
2. `플로우스코어 리포트 + 상담보고서`가 있어야 학습 적격으로 인정
3. 적격 학습 10건 이상일 때 업데이트 후보가 된다
4. 누적 학습 가중치 합계가 `7.5` 이상이어야 실제 업데이트가 생성된다
5. 버전명은 `v.1.주차수.순번` 형식이며 첫 업데이트는 보통 `v.1.주차수.01`

## 학습 가중치
한 건의 학습 가중치는 최대 `1.00`이다.

- 플로우스코어 리포트 제출: `0.35`
- 상담보고서 제출: `0.35`
- 내부심사리포트 링크 제출: `0.15`
- 추가 정보 제출: 최대 `0.15`
  - 링크/파일/메모 1개당 `0.05`
  - 최대 3개까지 인정

## 업데이트 생성 여부
업데이트는 아래 두 조건을 모두 만족해야 생성된다.

1. 학습 적격 건수 `10건 이상`
2. 누적 학습 가중치 `7.5 이상`

즉, 단순히 10건만 채우는 것이 아니라 자료 품질이 일정 수준 이상이어야 업데이트가 만들어진다.

## 업데이트 시 적용되는 가중치
최근 적격 10건의 결과를 보고 아래 항목에 가중치를 다시 준다.

- 신청업체 가중치
- 매출처 가중치
- 거래구조 가중치

원리:
- 최근 학습 데이터에서 점수가 상대적으로 낮은 축은 더 중요하게 반영
- 점수가 상대적으로 높은 축은 비중을 조금 낮춤
- 이렇게 해서 다음 버전은 더 취약한 부분에 민감하게 반응하도록 조정

추가로:
- 평균 학습 가중치가 낮으면 마진 상한도 조금 더 보수적으로 조정

## 업데이트 후 자동 작업
1. 기존 학습 데이터 재평가
2. 이전 버전 결과와 새 버전 결과 비교
3. 비교 리포트 생성
4. 적용된 가중치와 업데이트 생성 여부를 함께 기록

## 주요 파일
- [bizaipro_learning.py](/Users/appler/Documents/COTEX/FlowBiz_ultra/bizaipro_learning.py)
- [bizaipro_learning_registry.json](/Users/appler/Documents/COTEX/FlowBiz_ultra/data/bizaipro_learning_registry.json)

## CLI 사용 예시

```bash
python3 bizaipro_learning.py status
python3 bizaipro_learning.py record --input sample_inputs/flowpay_atude_case.json --label "에이튜드 1차"
python3 bizaipro_learning.py update
```

## 출력물
업데이트가 생성되면 아래가 저장된다.

- `outputs/bizaipro_updates/<version>/comparison_report.md`
- `outputs/bizaipro_updates/<version>/update_summary.json`

## 해석 기준
- `update_generated = false`
  - 아직 학습 데이터 수나 품질이 부족
- `update_generated = true`
  - 조건 충족으로 새 버전 생성
  - 전후 비교 리포트 제출 가능
