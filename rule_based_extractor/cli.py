"""CLI 진입점 — 기본 채점 경로. Claude API를 전혀 쓰지 않으므로 비용이 들지 않는다.

사용법 (DART 실시간 조회 + 채점, DART_API_KEY만 필요):
    python -m rule_based_extractor.cli <기업명> <YYYYMMDD 시작> <YYYYMMDD 끝> <출력경로>

사용법 (이미 저장된 dart_researcher 결과로 파생 채점만 실행, API 키 전혀 불필요):
    python -m rule_based_extractor.cli --from-file <dart_결과.json> <출력경로>
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .pipeline import score_company_from_dart, score_company_from_documents


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--from-file", type=Path, default=None, help="dart_researcher 결과 JSON(재조회 없이 파생 채점만)")
    parser.add_argument("args", nargs="*", help="--from-file 없으면: 기업명 시작일 종료일 출력경로 / 있으면: 출력경로")
    parsed = parser.parse_args(argv)

    if parsed.from_file:
        if len(parsed.args) != 1:
            parser.error("--from-file 사용 시 출력경로 1개만 지정하세요.")
        payload = json.loads(parsed.from_file.read_text(encoding="utf-8"))
        report = score_company_from_documents(
            company_name=payload["company"], documents=payload["documents"]
        )
        output_path = parsed.args[0]
    else:
        if len(parsed.args) != 4:
            parser.error("기업명, 시작일(YYYYMMDD), 종료일(YYYYMMDD), 출력경로 4개를 지정하세요.")
        company_name, bgn_de, end_de, output_path = parsed.args
        report = score_company_from_dart(company_name=company_name, bgn_de=bgn_de, end_de=end_de)

    output_path = Path(output_path)
    output_path.write_text(report.model_dump_json(indent=2), encoding="utf-8")

    status = "잠정치(일부 항목 rule_status=insufficient_evidence)" if report.is_provisional else "확정"
    print(
        f"{report.company}: {report.total_score}/{report.max_score}점 [{status}], "
        f"권장 {report.recommended_met}/{report.recommended_total} 충족, "
        f"검토 권고 {sum(1 for i in report.items if i.review_recommended)}개 항목 -> {output_path}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
