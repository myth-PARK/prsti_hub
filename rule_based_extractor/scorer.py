"""RuleBasedScorer: 매치된 후보에 rubric_rules.yaml의 규칙을 적용해 점수를 정한다.

핵심 원칙(사용자 지시 그대로):
- 근거가 전혀 없으면 0점.
- rule_status=insufficient_evidence인 항목은 뭔가 애매하게 매치돼도 임의로
  1·2점을 만들지 않는다 — 0점을 유지하되 review_recommended=true로 사람이
  다시 봐야 함을 표시한다.
- 부정 표현(negative_keywords)이 매치되면 다른 신호와 무관하게 0점으로
  강제 하향한다.
- 신뢰도(confidence)는 점수 자체가 아니라 판정 근거의 안정성을 나타낸다:
  high(핵심 조건+출처 확인됨) / medium(핵심 조건은 있으나 보조조건 불명확) /
  low(간접 표현·상충 근거·미확정 규칙으로 판정).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .extractor import Candidate
from .rules import ItemRule


@dataclass
class RuleScoreOutcome:
    score: int
    confidence: str
    review_recommended: bool
    decision_reason: str
    matched_rules: list[str] = field(default_factory=list)
    na_confirmed: bool = False
    has_evidence: bool = False


def score_candidate(item_rule: ItemRule, candidate: Candidate | None) -> RuleScoreOutcome:
    if candidate is None:
        return RuleScoreOutcome(
            score=0,
            confidence="high",
            review_recommended=False,
            decision_reason="원문에 관련 키워드·패턴이 전혀 없어 0점(근거 없음)으로 판정",
        )

    if candidate.negative_matched:
        return RuleScoreOutcome(
            score=0,
            confidence="high",
            review_recommended=False,
            decision_reason="부정 표현(negative_keywords)이 매치되어 0점으로 강제 하향",
            matched_rules=["negative_keyword"],
            has_evidence=True,
        )

    if candidate.na_expression_matched:
        # 조건부 항목의 "조건 비해당 명시" — DEC-005에 따라 auto_max 대상.
        # 최종 만점 처리는 scoring_engine의 na_confirmed 경로에 맡긴다(여기서는 표시만).
        return RuleScoreOutcome(
            score=2,
            confidence="high",
            review_recommended=False,
            decision_reason="조건 비해당이 명시적으로 확인됨 → auto_max 처리 대상(DEC-005)",
            matched_rules=["na_expression"],
            na_confirmed=True,
            has_evidence=True,
        )

    if item_rule.rule_status == "insufficient_evidence":
        return RuleScoreOutcome(
            score=0,
            confidence="low",
            review_recommended=True,
            decision_reason=(
                "일부 키워드/패턴이 매치됐으나 이 항목은 rule_status=insufficient_evidence"
                "(1·2점 실사례 없음)이므로 임의로 점수를 올리지 않고 0점을 유지함. "
                f"missing_evidence: {item_rule.missing_evidence}"
            ),
            matched_rules=candidate.matched_keywords + candidate.matched_patterns,
            has_evidence=True,
        )

    # confirmed / provisional: 패턴(구체적 판정 기준) 매치 여부로 1점/2점을 가른다.
    # patterns가 애초에 정의되지 않은 항목(예: 필수-02)은 항상 1점 상한 —
    # 2점을 뒷받침할 실제 사례가 아직 없다는 rubric_rules.yaml의 판단을 그대로 반영한다.
    if item_rule.patterns and candidate.matched_patterns:
        score = 2
    else:
        score = 1

    confidence = "high" if item_rule.rule_status == "confirmed" else "medium"
    review_recommended = item_rule.rule_status == "provisional"

    return RuleScoreOutcome(
        score=score,
        confidence=confidence,
        review_recommended=review_recommended,
        decision_reason=(
            f"매치된 키워드: {candidate.matched_keywords}, 매치된 패턴: "
            f"{candidate.matched_patterns} (rule_status={item_rule.rule_status})"
        ),
        matched_rules=candidate.matched_keywords + candidate.matched_patterns,
        has_evidence=True,
    )
