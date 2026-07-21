"""CLI 진입점 — 선택적 비교 실험용(Claude API 호출, 유료).

기본 채점 경로가 아니다. 무료 자동 채점은 `python -m rule_based_extractor.cli`를 쓴다.

사용법:
    ALLOW_PAID_API=true python -m evidence_extractor.cli <input.json> <output.json> [--rubric PATH] [--model ID]

input.json 형식:
    {"company": "...", "source_doc": "...", "raw_excerpt": "..."}

ANTHROPIC_API_KEY 환경변수·anthropic 패키지 설치·ALLOW_PAID_API=true가 모두 필요하다
(anthropic_extractor.py의 PaidApiDisabledError / MissingSDKError / MissingAPIKeyError 참고).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .anthropic_extractor import run_extraction

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUBRIC_PATH = REPO_ROOT / "rubric" / "rubric.yaml"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_json", type=Path, help="{company, source_doc, raw_excerpt} JSON")
    parser.add_argument("output_json", type=Path, help="추출 결과(EvidenceReport)를 저장할 경로")
    parser.add_argument("--rubric", type=Path, default=DEFAULT_RUBRIC_PATH)
    parser.add_argument("--model", default=None, help="기본값: PRSTI_EXTRACTOR_MODEL 또는 claude-opus-4-8")
    args = parser.parse_args(argv)

    payload = json.loads(args.input_json.read_text(encoding="utf-8"))
    for required_key in ("company", "source_doc", "raw_excerpt"):
        if required_key not in payload:
            parser.error(f"input_json에 '{required_key}' 필드가 없습니다.")

    kwargs = dict(
        company=payload["company"],
        source_doc=payload["source_doc"],
        raw_excerpt=payload["raw_excerpt"],
        rubric_path=args.rubric,
        output_path=args.output_json,
    )
    if args.model:
        kwargs["model"] = args.model

    report = run_extraction(**kwargs)
    found = sum(1 for item in report.items if item.status == "found")
    print(f"{len(report.items)}개 항목 중 {found}개 근거 발견 -> {args.output_json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
