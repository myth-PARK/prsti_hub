"""evidence_extractor.anthropic_extractor 테스트 — 선택적 비교 실험용 경로.

실제 네트워크 호출은 없다(전부 unittest.mock). 이 파일이 검증하는 것 중 가장
중요한 항목은 ALLOW_PAID_API 게이트 자체다 — 기본값(false)에서는 SDK가 설치돼
있고 API 키가 있어도 절대 호출되지 않아야 한다(무과금 개발 원칙, DEC-013/014).
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from evidence_extractor import anthropic_extractor
from evidence_extractor.schema import ExtractedItem, ExtractionResult
from prsti_common.rubric_loader import load_items as load_rubric

REPO_ROOT = Path(__file__).resolve().parents[1]
RUBRIC_PATH = REPO_ROOT / "rubric" / "rubric.yaml"


# ---------- ALLOW_PAID_API 게이트 (최우선 검증 대상) ----------


def test_raises_paid_api_disabled_by_default(monkeypatch):
    monkeypatch.setattr(anthropic_extractor, "ALLOW_PAID_API", False)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-fake-key-not-real")
    fake_anthropic_module = MagicMock()
    with patch.object(anthropic_extractor, "anthropic", fake_anthropic_module):
        with pytest.raises(anthropic_extractor.PaidApiDisabledError):
            anthropic_extractor.extract_evidence(
                company="테스트기업",
                source_doc="테스트문서",
                raw_excerpt="x",
                items=load_rubric(RUBRIC_PATH)[:1],
            )
    # ALLOW_PAID_API가 꺼져 있으면 SDK가 설치돼 있고 키가 있어도 절대 호출되지 않는다
    fake_anthropic_module.Anthropic.assert_not_called()


# ---------- SDK/키 확인 (ALLOW_PAID_API=true인 경우에만 의미가 있음) ----------


def test_raises_missing_sdk_error_when_anthropic_not_installed(monkeypatch):
    monkeypatch.setattr(anthropic_extractor, "ALLOW_PAID_API", True)
    with patch.object(anthropic_extractor, "anthropic", None):
        with pytest.raises(anthropic_extractor.MissingSDKError):
            anthropic_extractor.extract_evidence(
                company="테스트기업",
                source_doc="테스트문서",
                raw_excerpt="x",
                items=load_rubric(RUBRIC_PATH)[:1],
            )


def test_raises_missing_api_key_error_when_env_var_unset(monkeypatch):
    monkeypatch.setattr(anthropic_extractor, "ALLOW_PAID_API", True)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    fake_anthropic = MagicMock()
    with patch.object(anthropic_extractor, "anthropic", fake_anthropic):
        with pytest.raises(anthropic_extractor.MissingAPIKeyError):
            anthropic_extractor.extract_evidence(
                company="테스트기업",
                source_doc="테스트문서",
                raw_excerpt="x",
                items=load_rubric(RUBRIC_PATH)[:1],
            )


# ---------- API 호출 배선 + 환각 검증 통합 (ALLOW_PAID_API=true) ----------


def test_extract_evidence_applies_hallucination_check_to_api_response(monkeypatch):
    monkeypatch.setattr(anthropic_extractor, "ALLOW_PAID_API", True)
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

    with patch.object(anthropic_extractor, "anthropic", fake_anthropic_module):
        result = anthropic_extractor.extract_evidence(
            company="테스트기업",
            source_doc="테스트문서",
            raw_excerpt=raw_excerpt,
            items=load_rubric(RUBRIC_PATH)[:1],
        )

    fake_client.messages.parse.assert_called_once()
    call_kwargs = fake_client.messages.parse.call_args.kwargs
    assert call_kwargs["output_format"] is ExtractionResult
    assert call_kwargs["model"] == anthropic_extractor.DEFAULT_MODEL

    # raw_excerpt에 없는 quote이므로 not_found로 강제 하향되어야 한다
    assert result[0].status == "not_found"
    assert result[0].suggested_score == 0
    assert "자동 검증 실패" in result[0].rationale


def test_extract_evidence_raises_when_model_output_fails_schema(monkeypatch):
    monkeypatch.setattr(anthropic_extractor, "ALLOW_PAID_API", True)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-fake-key-not-real")

    fake_response = MagicMock()
    fake_response.parsed_output = None
    fake_response.stop_reason = "refusal"

    fake_client = MagicMock()
    fake_client.messages.parse.return_value = fake_response

    fake_anthropic_module = MagicMock()
    fake_anthropic_module.Anthropic.return_value = fake_client

    with patch.object(anthropic_extractor, "anthropic", fake_anthropic_module):
        with pytest.raises(RuntimeError):
            anthropic_extractor.extract_evidence(
                company="테스트기업",
                source_doc="테스트문서",
                raw_excerpt="x",
                items=load_rubric(RUBRIC_PATH)[:1],
            )
