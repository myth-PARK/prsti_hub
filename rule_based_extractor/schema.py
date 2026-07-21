"""rule_based_extractor 출력 스키마."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from scoring_engine.schema import AreaResult


class EvidenceRef(BaseModel):
    text: str
    source_document: str | None = None
    receipt_no: str | None = None
    source_location: str | None = None


class RuleItemResult(BaseModel):
    rubric_id: str
    score: int
    confidence: Literal["high", "medium", "low"]
    review_recommended: bool
    evidence: list[EvidenceRef]
    matched_rules: list[str]
    decision_reason: str
    rule_basis: list[str]
    rule_status: Literal["confirmed", "provisional", "insufficient_evidence"]


class RuleScoringReport(BaseModel):
    company: str
    rubric_version: str
    scoring_method: Literal["rule_based"] = "rule_based"
    computed_at: str
    items: list[RuleItemResult]
    areas: list[AreaResult]
    total_score: float
    max_score: float
    is_provisional: bool
    recommended_met: int
    recommended_total: int
    candidates_considered: int
    candidates_excluded: int
    excluded_reasons: list[str]
