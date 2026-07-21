"""evidence_extractor 공용부 테스트 (rubric_loader/prompts/verify_quotes).

이 파일은 provider(anthropic vs rule_based)와 무관한 부분만 다룬다 — anthropic 패키지나
API 키 없이 그대로 실행된다. Claude API 호출 자체의 테스트는
tests/test_anthropic_extractor.py를 본다.
"""

from __future__ import annotations

from pathlib import Path

from evidence_extractor import extractor
from evidence_extractor.prompts import build_user_prompt
from evidence_extractor.schema import ExtractedItem
from prsti_common.rubric_loader import load_items as load_rubric

REPO_ROOT = Path(__file__).resolve().parents[1]
RUBRIC_PATH = REPO_ROOT / "rubric" / "rubric.yaml"


# ---------- rubric_loader ----------


def test_loads_all_19_items():
    items = load_rubric(RUBRIC_PATH)
    assert len(items) == 19


def test_item_04_criteria_parsed_correctly():
    items = {item.id: item for item in load_rubric(RUBRIC_PATH)}
    item = items["필수-04"]
    assert item.tier == "mandatory"
    assert item.source_table == "표6"
    assert set(item.criteria) == {0, 1, 2}
    assert "발행가액" in item.criteria[2]


def test_conditional_item_carries_na_rule():
    items = {item.id: item for item in load_rubric(RUBRIC_PATH)}
    item = items["조건부-01"]
    assert item.tier == "conditional"
    assert item.na_rule is not None
    assert "auto_max" in item.na_rule


# ---------- prompts ----------


def test_prompt_contains_company_and_excerpt_and_item_ids():
    items = load_rubric(RUBRIC_PATH)[:2]
    prompt = build_user_prompt(
        company="한화솔루션",
        source_doc="반기보고서",
        raw_excerpt="테스트 발췌문",
        items=items,
    )
    assert "한화솔루션" in prompt
    assert "테스트 발췌문" in prompt
    for item in items:
        assert item.id in prompt


# ---------- verify_quotes (환각 방지 안전망, AI/규칙 공용) ----------


def test_valid_quote_passes_through_unchanged():
    raw = "본 계약은 만기 시 재매입 의무가 없다."
    item = ExtractedItem(
        item_id="필수-12",
        status="found",
        quote="만기 시 재매입 의무가 없다",
        source_location="본문",
        suggested_score=1,
        confidence="medium",
        rationale="재매입 의무 없음이 명시됨",
    )
    result = extractor.verify_quotes(raw, [item])
    assert result[0].status == "found"
    assert result[0].suggested_score == 1
    assert result[0].rationale == "재매입 의무 없음이 명시됨"


def test_hallucinated_quote_is_downgraded_to_not_found():
    raw = "본 계약은 만기 시 재매입 의무가 없다."
    item = ExtractedItem(
        item_id="필수-12",
        status="found",
        quote="원문에 실제로 없는 문장입니다",
        source_location="본문",
        suggested_score=2,
        confidence="high",
        rationale="근거 있음(그러나 실제로는 없음)",
    )
    result = extractor.verify_quotes(raw, [item])
    assert result[0].status == "not_found"
    assert result[0].suggested_score == 0
    assert result[0].confidence == "high"
    assert "자동 검증 실패" in result[0].rationale


def test_positive_score_with_no_quote_is_downgraded():
    raw = "아무 내용이나 있는 발췌문"
    item = ExtractedItem(
        item_id="필수-01",
        status="found",
        quote=None,
        source_location=None,
        suggested_score=1,
        confidence="low",
        rationale="인용을 빠뜨림",
    )
    result = extractor.verify_quotes(raw, [item])
    assert result[0].suggested_score == 0
    assert result[0].status == "not_found"


def test_not_found_items_pass_through_untouched():
    raw = "아무 내용이나 있는 발췌문"
    item = ExtractedItem(
        item_id="필수-01",
        status="not_found",
        quote=None,
        source_location=None,
        suggested_score=0,
        confidence="high",
        rationale="언급 없음",
    )
    result = extractor.verify_quotes(raw, [item])
    assert result[0].rationale == "언급 없음"
    assert result[0].status == "not_found"
