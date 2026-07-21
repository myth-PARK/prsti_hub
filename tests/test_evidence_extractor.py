"""evidence_extractor 테스트.

rubric_loader / prompts / verify_quotes는 anthropic 패키지나 ANTHROPIC_API_KEY 없이
그대로 실행된다. extract_evidence()의 API 호출부만 unittest.mock으로 anthropic
클라이언트를 대체해 검증한다 — 실제 네트워크 호출은 발생하지 않는다.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from evidence_extractor import extractor
from evidence_extractor.prompts import build_user_prompt
from evidence_extractor.rubric_loader import load_rubric
from evidence_extractor.schema import ExtractedItem, ExtractionResult

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


# ---------- verify_quotes (환각 방지 안전망) ----------


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


# ---------- extract_evidence: 에러 핸들링 ----------


def test_raises_missing_sdk_error_when_anthropic_not_installed():
    with patch.object(extractor, "anthropic", None):
        with pytest.raises(extractor.MissingSDKError):
            extractor.extract_evidence(
                company="테스트기업",
                source_doc="테스트문서",
                raw_excerpt="x",
                items=load_rubric(RUBRIC_PATH)[:1],
            )


def test_raises_missing_api_key_error_when_env_var_unset(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    fake_anthropic = MagicMock()
    with patch.object(extractor, "anthropic", fake_anthropic):
        with pytest.raises(extractor.MissingAPIKeyError):
            extractor.extract_evidence(
                company="테스트기업",
                source_doc="테스트문서",
                raw_excerpt="x",
                items=load_rubric(RUBRIC_PATH)[:1],
            )


# ---------- extract_evidence: API 호출 배선 + 환각 검증 통합 ----------


def test_extract_evidence_applies_hallucination_check_to_api_response(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-fake-key-not-real")

    raw_excerpt = "계약규모는 1조원이며 부채총계 대비 5%이다."
    fake_item = ExtractedItem(
        item_id="필수-01",
        status="found",
        quote="원문에 없는 인용문",
        source_location="본문",
        suggested_score=2,
        confidence="high",
        rationale="모델이 주장한 근거",
    )
    fake_response = MagicMock()
    fake_response.parsed_output = ExtractionResult(items=[fake_item])

    fake_client = MagicMock()
    fake_client.messages.parse.return_value = fake_response

    fake_anthropic_module = MagicMock()
    fake_anthropic_module.Anthropic.return_value = fake_client

    with patch.object(extractor, "anthropic", fake_anthropic_module):
        result = extractor.extract_evidence(
            company="테스트기업",
            source_doc="테스트문서",
            raw_excerpt=raw_excerpt,
            items=load_rubric(RUBRIC_PATH)[:1],
        )

    fake_client.messages.parse.assert_called_once()
    call_kwargs = fake_client.messages.parse.call_args.kwargs
    assert call_kwargs["output_format"] is ExtractionResult
    assert call_kwargs["model"] == extractor.DEFAULT_MODEL

    # raw_excerpt에 없는 quote이므로 not_found로 강제 하향되어야 한다
    assert result[0].status == "not_found"
    assert result[0].suggested_score == 0
    assert "자동 검증 실패" in result[0].rationale


def test_extract_evidence_raises_when_model_output_fails_schema(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-fake-key-not-real")

    fake_response = MagicMock()
    fake_response.parsed_output = None
    fake_response.stop_reason = "refusal"

    fake_client = MagicMock()
    fake_client.messages.parse.return_value = fake_response

    fake_anthropic_module = MagicMock()
    fake_anthropic_module.Anthropic.return_value = fake_client

    with patch.object(extractor, "anthropic", fake_anthropic_module):
        with pytest.raises(RuntimeError):
            extractor.extract_evidence(
                company="테스트기업",
                source_doc="테스트문서",
                raw_excerpt="x",
                items=load_rubric(RUBRIC_PATH)[:1],
            )
