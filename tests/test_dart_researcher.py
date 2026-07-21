"""dart_researcher 테스트. 실제 DART API 호출 없이 클라이언트를 mock으로 대체한다."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from dart_researcher import client as client_module
from dart_researcher.client import DisclosureListItem
from dart_researcher.search import find_prs_passages, is_relevant_report, search_company


def test_missing_api_key_raises(monkeypatch):
    monkeypatch.delenv("DART_API_KEY", raising=False)
    with pytest.raises(client_module.MissingAPIKeyError):
        client_module.DartClient()


def test_find_prs_passages_direct_term():
    text = "본 계약은 매매수익스왑(Price Return Swap) 방식으로 체결되었다." + " " * 400
    hits = find_prs_passages(text, window_size=100, stride=50)
    assert any("Price Return Swap" in h.matched_terms for h in hits)


def test_find_prs_passages_structural_group_needs_all_terms():
    text_all = "기초자산 매각 시 정산금액과의 차액을 수수한다." + " " * 400
    hits = find_prs_passages(text_all, window_size=60, stride=30)
    assert hits, "세 단어가 모두 있으면 구조 서술형으로 탐지되어야 한다"

    text_partial = "기초자산에 대한 일반적인 설명입니다." + " " * 400
    hits_partial = find_prs_passages(text_partial, window_size=60, stride=30)
    assert not hits_partial, "핵심 단어 중 하나만 있으면 탐지되지 않아야 한다(과다 탐지 방지)"


def test_is_relevant_report():
    assert is_relevant_report("반기보고서")
    assert is_relevant_report("주요사항보고서(타법인 주식 및 출자증권 처분결정)")
    assert not is_relevant_report("임원ㆍ주요주주 특정증권등 소유상황보고서")


def test_search_company_returns_not_found_when_no_matches(monkeypatch):
    monkeypatch.setenv("DART_API_KEY", "test-fake-key-not-real")
    fake_client = MagicMock()
    fake_client.find_corp_code.return_value = "00123456"
    fake_client.list_disclosures.return_value = []

    result = search_company(
        company_name="테스트기업", bgn_de="20250101", end_de="20251231", client=fake_client
    )
    assert result["documents"] == []
    assert result["not_found_keywords"], "근거를 못 찾으면 반드시 채워야 한다(없는 것을 있다고 하지 않음)"


def test_search_company_extracts_matched_passage(monkeypatch):
    monkeypatch.setenv("DART_API_KEY", "test-fake-key-not-real")
    fake_item = DisclosureListItem(
        corp_code="00123456", corp_name="테스트기업", stock_code="000000",
        report_nm="반기보고서", rcept_no="20250814000123", flr_nm="테스트기업",
        rcept_dt="2025-08-14", rm="",
    )
    fake_client = MagicMock()
    fake_client.find_corp_code.return_value = "00123456"
    fake_client.list_disclosures.return_value = [fake_item]
    fake_client.fetch_document_text.return_value = (
        "회사는 매매수익스왑(Price Return Swap) 계약을 체결하였다." + " " * 400
    )

    result = search_company(
        company_name="테스트기업", bgn_de="20250101", end_de="20251231", client=fake_client
    )
    assert len(result["documents"]) == 1  # pblntf_ty A/B 양쪽 질의가 겹쳐도 rcept_no로 중복 제거됨
    assert result["documents"][0]["rcept_no"] == "20250814000123"
    assert "Price Return Swap" in result["documents"][0]["raw_excerpt"]
    assert result["not_found_keywords"] == []
