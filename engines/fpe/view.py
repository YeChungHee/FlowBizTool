"""FPE 결과 view/draft — 메인 engine.py로부터 4개 view 함수 re-export.

v2.11 단방향 룰: view는 .eval import 금지. eval만 view import 가능.

v2.11 마이그레이션 단계:
  1차 (현 PR): engine.py에서 본체 re-export.
  2차 (후속 PR): 함수 본체를 본 파일로 점진 이동.
"""
from __future__ import annotations

# v2.11 1차: 메인 engine.py에서 본체 import. 2차에서 본체 이동 예정.
from engine import (
    build_fpe_sales_view,
    generate_fpe_sales_summary,
    generate_fpe_sales_report,
    generate_fpe_sales_email,
)
