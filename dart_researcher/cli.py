"""CLI 진입점.

사용법:
    python -m dart_researcher.cli <기업명> <YYYYMMDD 시작> <YYYYMMDD 끝> <출력경로>

소량 타겟 조회 전용 — 기업 하나, 기간 하나만 조회한다. 여러 기업을 조회하려면
이 명령을 여러 번 실행하는 대신, 먼저 사용자에게 알리고 승인받아야 한다
(.claude/agents/dart-researcher.md의 "대량 수집 절대 금지" 원칙).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .search import search_company


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("company_name")
    parser.add_argument("bgn_de", help="조회 시작일 YYYYMMDD")
    parser.add_argument("end_de", help="조회 종료일 YYYYMMDD")
    parser.add_argument("output_json", type=Path)
    args = parser.parse_args(argv)

    result = search_company(company_name=args.company_name, bgn_de=args.bgn_de, end_de=args.end_de)
    args.output_json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    found = len(result["documents"])
    status = f"{found}건 발견" if found else "근거 없음(not_found_keywords 기록됨)"
    print(f"{args.company_name} ({args.bgn_de}~{args.end_de}): {status} -> {args.output_json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
