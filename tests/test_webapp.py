"""webapp 테스트.

Claude API는 물론 실제 DART 네트워크 호출도 하지 않는다 — dart_researcher.search.search_company를
monkeypatch로 대체해 순수 로직(오류 변환, 요약 가공)과 페이지 초기 렌더링만 검증한다.
"""

from __future__ import annotations

from pathlib import Path

import dart_researcher.search as dart_search
from dart_researcher.client import DartApiError, MissingAPIKeyError
from rule_based_extractor.pipeline import score_company_from_documents
from webapp.report_view import build_summary, run_scoring

REPO_ROOT = Path(__file__).resolve().parents[1]


def _fake_dart_result(company_name: str) -> dict:
    return {
        "company": company_name,
        "retrieved_at": "2026-07-21T00:00:00+09:00",
        "documents": [
            {
                "doc_name": "반기보고서 (2025.06)",
                "rcept_no": "20250814002909",
                "disclosure_date": "20250814",
                "section": "매칭 키워드: PRS",
                "raw_excerpt": "계약일 2025-06-24 만기일 2028-06-26",
            }
        ],
        "not_found_keywords": [],
    }


def test_run_scoring_success(monkeypatch):
    monkeypatch.setattr(dart_search, "search_company", lambda **kwargs: _fake_dart_result(kwargs["company_name"]))
    outcome = run_scoring(company_name="테스트기업", bgn_de="20250101", end_de="20251231")
    assert outcome.error is None
    assert outcome.report is not None
    assert outcome.report.company == "테스트기업"


def test_run_scoring_missing_api_key(monkeypatch):
    def _raise(**kwargs):
        raise MissingAPIKeyError("DART_API_KEY 없음")

    monkeypatch.setattr(dart_search, "search_company", _raise)
    outcome = run_scoring(company_name="테스트기업", bgn_de="20250101", end_de="20251231")
    assert outcome.report is None
    assert "DART_API_KEY" in outcome.error


def test_run_scoring_dart_api_error(monkeypatch):
    def _raise(**kwargs):
        raise DartApiError("'없는회사'에 해당하는 corp_code를 찾지 못했습니다.")

    monkeypatch.setattr(dart_search, "search_company", _raise)
    outcome = run_scoring(company_name="없는회사", bgn_de="20250101", end_de="20251231")
    assert outcome.report is None
    assert "DART 조회 오류" in outcome.error


def test_run_scoring_unexpected_error_is_caught(monkeypatch):
    def _raise(**kwargs):
        raise ValueError("무언가 예상 못한 문제")

    monkeypatch.setattr(dart_search, "search_company", _raise)
    outcome = run_scoring(company_name="테스트기업", bgn_de="20250101", end_de="20251231")
    assert outcome.report is None
    assert "예상하지 못한 오류" in outcome.error


def test_build_summary_reports_no_evidence_when_no_candidates():
    report = score_company_from_documents(company_name="테스트기업", documents=[])
    summary = build_summary(report)
    assert summary["no_evidence_found"] is True
    assert summary["candidates_considered"] == 0


def test_build_summary_areas_have_percent():
    report = score_company_from_documents(
        company_name="테스트기업",
        documents=[
            {
                "doc_name": "반기보고서 (2025.06)",
                "rcept_no": "20250814002909",
                "disclosure_date": "20250814",
                "section": "매칭 키워드: PRS",
                "raw_excerpt": "계약일 2025-06-24 만기일 2028-06-26",
            }
        ],
    )
    summary = build_summary(report)
    area_ids = {a["area_id"] for a in summary["areas"]}
    assert "가" in area_ids
    area_ga = next(a for a in summary["areas"] if a["area_id"] == "가")
    assert area_ga["percent"] >= 0


def test_app_renders_without_exception():
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file(str(REPO_ROOT / "webapp" / "app.py"))
    at.run()
    assert not at.exception
    assert "PRSTI" in at.title[0].value
