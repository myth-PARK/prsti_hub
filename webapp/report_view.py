"""RuleScoringReport를 화면 표시용으로 가공하고, DART 조회+채점을 실행하는 로직.

Streamlit을 import하지 않는다 — UI 프레임워크 없이 단위 테스트하기 위함이다.
webapp/app.py는 이 모듈의 함수만 호출하는 얇은 화면 레이어로 유지한다.
"""

from __future__ import annotations

from dataclasses import dataclass

from dart_researcher.client import DartApiError, MissingAPIKeyError
from rule_based_extractor.pipeline import score_company_from_dart
from rule_based_extractor.schema import RuleScoringReport


@dataclass
class ScoringOutcome:
    report: RuleScoringReport | None
    error: str | None


def run_scoring(*, company_name: str, bgn_de: str, end_de: str) -> ScoringOutcome:
    """DART 조회 + 규칙 기반 채점을 실행하고, 예외를 화면에 보여줄 오류 메시지로 변환한다.

    기준기업을 미리 정해두지 않고 어떤 기업명이든 조회할 수 있어야 한다는 것이
    제품의 핵심 목적이다(DEC-017) — 이 함수는 company_name을 그대로 DART에 넘긴다.
    """
    try:
        report = score_company_from_dart(company_name=company_name, bgn_de=bgn_de, end_de=end_de)
    except MissingAPIKeyError:
        return ScoringOutcome(
            report=None,
            error=(
                "DART_API_KEY 환경변수가 설정돼 있지 않습니다. "
                "https://opendart.fss.or.kr 에서 발급받아 환경변수로 설정한 뒤 다시 실행하세요."
            ),
        )
    except DartApiError as exc:
        return ScoringOutcome(report=None, error=f"DART 조회 오류: {exc}")
    except Exception as exc:  # noqa: BLE001 — 실 DART 호출 경계이므로 예상 못한 오류도 안전하게 화면에 표시
        return ScoringOutcome(report=None, error=f"예상하지 못한 오류가 발생했습니다: {exc}")
    return ScoringOutcome(report=report, error=None)


def build_summary(report: RuleScoringReport) -> dict:
    """총점/영역별/권장/검토필요 요약을 화면 표시용 딕셔너리로 만든다.

    19개 항목 상세는 여기서 다루지 않는다 — 첫 버전은 요약 화면만 제공하기로 확정했다.
    """
    percent = round((report.total_score / report.max_score) * 100, 1) if report.max_score else 0.0
    review_needed = sum(1 for item in report.items if item.review_recommended)
    areas = [
        {
            "area_id": area.area_id,
            "area_name": area.area_name,
            "earned": area.earned,
            "max_possible": area.max_possible,
            "percent": round((area.earned / area.max_possible) * 100, 1) if area.max_possible else 0.0,
        }
        for area in report.areas
    ]
    return {
        "company": report.company,
        "total_score": report.total_score,
        "max_score": report.max_score,
        "percent": percent,
        "is_provisional": report.is_provisional,
        "recommended_met": report.recommended_met,
        "recommended_total": report.recommended_total,
        "review_needed_count": review_needed,
        "candidates_considered": report.candidates_considered,
        "candidates_excluded": report.candidates_excluded,
        "no_evidence_found": report.candidates_considered == 0,
        "areas": areas,
    }
