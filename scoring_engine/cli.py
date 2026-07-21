"""CLI 진입점. API 호출이 전혀 없으므로 비용이 들지 않는다.

사용법:
    python -m scoring_engine.cli <confirmed_scores.json> <output.json> [--rubric PATH] [--company NAME]

confirmed_scores.json 형식:
    {
      "company": "한화솔루션",
      "items": [
        {"item_id": "필수-01", "confirmed_score": 2},
        {"item_id": "조건부-01", "na_confirmed": true}
      ]
    }
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .engine import compute_score
from .schema import ConfirmedItemScore

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUBRIC_PATH = REPO_ROOT / "rubric" / "rubric.yaml"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_json", type=Path)
    parser.add_argument("output_json", type=Path)
    parser.add_argument("--rubric", type=Path, default=DEFAULT_RUBRIC_PATH)
    args = parser.parse_args(argv)

    payload = json.loads(args.input_json.read_text(encoding="utf-8"))
    confirmed = [ConfirmedItemScore(**item) for item in payload["items"]]

    result = compute_score(
        rubric_path=args.rubric,
        company=payload["company"],
        confirmed_scores=confirmed,
    )
    args.output_json.write_text(result.model_dump_json(indent=2), encoding="utf-8")

    status = "잠정치(미검토 항목 있음)" if result.is_provisional else "확정"
    print(
        f"{result.company}: {result.total_score}/{result.max_total_score}점 [{status}], "
        f"권장 {result.recommended_met}/{result.recommended_total} 충족 -> {args.output_json}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
