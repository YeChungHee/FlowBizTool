# FlowBiz_ultra 고도화 계획서 실행 검증

- 검증일: 2026-04-27
- 대상: `FlowBiz_ultra_고도화계획서_20260427.docx`
- 목적: 계획서가 실제 현재 코드 상태에서 바로 실행 가능한지 검증하고, 구현 착수 순서를 확정한다.

## 1. 실행 검증 결론

고도화 계획서의 방향은 맞다. 다만 현재 저장소 상태 기준으로는 계획서의 핵심 기능 대부분이 아직 미구현이므로, 곧바로 2~4단계 작업에 들어가면 기준 불일치가 커질 수 있다. 먼저 1단계의 `SourceQuality`와 학습 적격 게이트를 고정한 뒤, 그 결과로 registry 7건을 재정규화하는 것이 안전하다.

현재 바로 착수 가능한 작업은 다음 3개다.

1. 자료 품질 모델(`SourceQuality`) 추가
2. `learning_material_components()`를 품질 기반으로 전환
3. 기존 registry 7건의 재계산/비교 리포트 생성

반대로 `active framework`, `promote`, `pytest 전체 회귀검증`은 선행 구조가 필요하다. 먼저 학습 적격 기준을 안정화하지 않으면 promote 후보 모델의 입력 데이터 품질이 흔들린다.

## 2. 현재 코드 상태

| 항목 | 현재 상태 | 판정 |
|---|---|---|
| SourceQuality 구조 | 코드에 없음 | 미구현 |
| quality.usable_for_update | 코드에 없음 | 미구현 |
| 학습 가중치 기준 | 파일명/URL 문자열 존재 기준 | 변경 필요 |
| Notion 본문 추출 | 공식 API + public fallback 구현 | 일부 구현 |
| Notion 오류 반영 | issues에는 기록되나 update weight 차단에는 미반영 | 변경 필요 |
| CLI 학습 기준 | `flow_score + consultation`이면 qualified | 웹 기준과 불일치 |
| 웹 학습 기준 | `flow_score + consultation + internal_review`이면 update eligible | 품질 기준 미반영 |
| update 명령 | 조건 미충족 시 update 미생성 | 정상 |
| update 산출물 | `comparison_report.md`, `update_summary.json` 중심 | framework snapshot 없음 |
| active framework registry | 없음 | 미구현 |
| promote 명령 | 없음 | 미구현 |
| tests/pytest | 테스트 디렉터리 및 설정 파일 없음 | 미구현 |

## 3. 실제 검증 명령 결과

### 3.1 컴파일 및 학습 상태

다음 명령은 성공했다.

```bash
python3 -m py_compile app.py engine.py report_extractors.py bizaipro_learning.py external_apis.py proposal_generator.py
python3 bizaipro_learning.py status
python3 bizaipro_learning.py update
```

현재 학습 상태:

- current_version: `v.local.learning`
- 전체 후보: 7건
- 업데이트 적격: 5건
- 누적 weight: 4.30
- 업데이트 가능 여부: false
- 미충족 사유: 적격 10건, 누적 가중치 7.5 조건 미달
- registry updates: 0건

### 3.2 registry 상태

현재 7건 중 5건이 update eligible이다.

| 케이스 | 평가 준비 | 업데이트 적격 | update weight | 비고 |
|---|---:|---:|---:|---|
| 씨랩 | true | true | 0.85 | 심사보고서 URL 있음 |
| 쿳션 | true | true | 0.85 | 심사보고서 URL 있음 |
| 갑산메탈 | false | false | 0.00 | 상담/심사 없음 |
| 성가런 | true | true | 0.85 | 심사보고서 URL 있음 |
| 테스토닉 | true | true | 0.85 | 심사보고서 URL 있음 |
| 프레스코 | true | true | 0.90 | 추가정보 포함 |
| 캠버 | true | false | 0.00 | 심사보고서 없음 |

문제는 씨랩/쿳션처럼 심사보고서 URL은 있지만 본문 추출이 실패했던 케이스도 현재 구조상 update eligible로 남는다는 점이다. 이 때문에 계획서의 1단계는 선택 과제가 아니라 선행 필수 과제다.

## 4. 계획서 항목별 실행 가능성

### 4.1 1단계: 학습 적격 게이트 정비

판정: 즉시 착수 가능

필요 작업:

- `SourceQuality` 타입/헬퍼 추가
- PDF 파서 결과에 quality 포함
- Notion parser 결과에 quality 포함
- supporting/additional parser 결과에 quality 포함
- `learning_material_components()`를 state 문자열 기준이 아니라 quality 기준으로 변경
- 기존 registry를 새 기준으로 재계산

주의:

- `usable_for_evaluation`과 `usable_for_update`를 분리해야 한다.
- 상담보고서는 본문 일부만 읽혀도 평가 보조자료로 쓸 수 있지만, 엔진 업데이트용 학습 데이터는 더 엄격해야 한다.

### 4.2 2단계: 평가 입력 변환 고도화

판정: 1단계 완료 후 착수

이유:

- 현재 `build_learning_evaluation_payload()`는 문서 추출 결과를 주로 structure bonus와 키워드 플래그로 반영한다.
- SourceQuality가 없으면 어떤 evidence를 점수에 반영해도 신뢰도 기준이 없다.

선행조건:

- parser별 normalized field schema
- evidence/confidence 저장 구조
- 결과 페이지 표시 구조

### 4.3 3단계: 업데이트 적용 경로 구축

판정: 1단계와 registry 재정규화 후 착수

이유:

- 현재 `run_update()`는 업데이트 조건을 만족하지 못해 산출물을 만들지 않는다.
- 업데이트 후보를 만들더라도 품질 기준이 정비되지 않으면 부정확한 학습 케이스가 promote 후보에 섞인다.

필요 작업:

- `outputs/bizaipro_updates/{version}/framework_snapshot.json` 생성
- `data/active_framework_version.json` 추가
- active framework loader 추가
- `bizaipro_learning.py promote {version}` 추가
- promote 전 shadow evaluation 리포트 생성

### 4.4 4단계: 결과 검증 자동화

판정: 병행 준비 가능, 본격 적용은 1~3단계 후

현재 저장소에는 테스트 디렉터리, pytest 설정, requirements 파일이 없다. 우선 최소 검증 스크립트부터 두는 것이 좋다.

최소 시작 세트:

- `tests/test_source_quality.py`
- `tests/test_learning_status.py`
- `tests/test_update_promotion.py`
- `tests/fixtures/`
- `pytest.ini`

## 5. 계획서 보완 권고

고도화 계획서 본문에 다음 문장을 추가하면 실행 문서로 더 강해진다.

1. `SourceQuality`는 `usable_for_evaluation`과 `usable_for_update`를 분리한다.
2. 기존 registry 7건은 재정규화 전후 비교표를 생성하고, update weight 변화를 기록한다.
3. Notion 권한 오류는 UI에서 “자료 있음”이 아니라 “본문 미확인”으로 표시한다.
4. promote 기준에는 decision 변화율, 한도 변화율, P0 오류 0건을 포함한다.
5. 각 단계 완료 기준에 실행 명령을 포함한다.

## 6. 즉시 실행 순서

추천하는 실제 작업 순서는 다음과 같다.

1. `app.py`에 SourceQuality helper와 quality normalization 추가
2. `report_extractors.py`의 FlowScore parser에 quality 필드 추가
3. Notion/supporting/additional parser에 quality 필드 추가
4. `learning_material_components()`와 registry normalize 로직을 quality 기반으로 변경
5. 기존 registry 7건을 백업한 뒤 재정규화
6. 재정규화 전후 비교 리포트 생성
7. 그 다음에 promote/active framework 작업 착수

## 7. Go / No-Go

| 항목 | 판정 |
|---|---|
| 계획서 내용 기준으로 고도화 착수 | Go |
| 원본 DOCX를 최종 승인본으로 배포 | No-Go |
| 1단계 SourceQuality 구현 착수 | Go |
| promote 구현을 바로 먼저 착수 | No-Go |
| 테스트 체계 스캐폴드 작성 | Go |

최종 판단: 계획서의 기술 방향은 유효하다. 단, 실행은 반드시 `SourceQuality -> registry 재정규화 -> active framework/promote -> 회귀검증` 순서로 진행해야 한다.
