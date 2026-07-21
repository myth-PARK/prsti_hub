"""RuleBasedExtractor: 텍스트에서 항목별 후보 근거(키워드·패턴 매치)를 찾는다.

의미 이해가 아니라 키워드·정규식 탐지다 — dart_researcher.search.find_prs_passages와
같은 철학: "어디를 봐야 하는지"만 좁혀주고, 최종 판단(점수화)은 scorer.py가 한다.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .rules import ItemRule


@dataclass
class Candidate:
    item_id: str
    matched_keywords: list[str] = field(default_factory=list)
    matched_patterns: list[str] = field(default_factory=list)  # 매치된 패턴 이름들
    negative_matched: bool = False
    na_expression_matched: bool = False
    excerpt: str = ""


def find_candidates(item_rule: ItemRule, text: str) -> Candidate | None:
    """positive_keywords/patterns가 하나도 매치되지 않으면 None(=탐지된 것 없음)을 반환한다."""
    matched_keywords = [kw for kw in item_rule.positive_keywords if kw in text]
    matched_patterns = [
        name
        for name, regex_list in item_rule.patterns.items()
        if any(re.search(rx, text) for rx in regex_list)
    ]
    negative_matched = any(kw in text for kw in item_rule.negative_keywords)
    na_expression_matched = any(kw in text for kw in item_rule.na_expression_keywords)

    if not matched_keywords and not matched_patterns and not na_expression_matched:
        return None

    return Candidate(
        item_id=item_rule.item_id,
        matched_keywords=matched_keywords,
        matched_patterns=matched_patterns,
        negative_matched=negative_matched,
        na_expression_matched=na_expression_matched,
        excerpt=text,
    )
