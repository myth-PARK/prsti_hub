"""PRSTI rule_based_extractor: 무료·결정론적 규칙으로 19개 항목을 자동 채점한다.

Claude API를 전혀 호출하지 않는다 — 기본 실행 경로(PRSTI_SCORING_PROVIDER=rule_based,
기본값)이며 ANTHROPIC_API_KEY 없이도 처음부터 끝까지 실행된다.

이 패키지는 rubric.yaml(배점, 승인됨)과 rubric_rules.yaml(이번에 추가된 기계 실행
규칙)을 논문·실제 DART 조회로 확보한 사례에서 도출한다. 19개 항목 중 실제 1·2점
사례가 없는 항목(rule_status=insufficient_evidence)은 임의로 점수를 만들지 않고
0점 + review_recommended=true로 정직하게 표시한다 — plans/parallel-orbiting-axolotl.md
§3 참고.
"""

from .pipeline import score_company_from_dart, score_company_from_documents
from .schema import RuleItemResult, RuleScoringReport

__all__ = [
    "score_company_from_dart",
    "score_company_from_documents",
    "RuleItemResult",
    "RuleScoringReport",
]
