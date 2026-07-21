"""rubric/rubric_rules.yaml 로더.

rubric.yaml(배점·정의, 승인된 v1.0)은 건드리지 않는다 — 이 파일은 그 위에 얹는
기계 실행 규칙(키워드·패턴·rule_status)만 읽는다.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass(frozen=True)
class ItemRule:
    item_id: str
    rule_status: str  # "confirmed" | "provisional" | "insufficient_evidence"
    rule_basis: list[str] = field(default_factory=list)
    positive_keywords: list[str] = field(default_factory=list)
    negative_keywords: list[str] = field(default_factory=list)
    na_expression_keywords: list[str] = field(default_factory=list)
    patterns: dict[str, list[str]] = field(default_factory=dict)
    exclusion_rules: list[str] = field(default_factory=list)
    missing_evidence: str | None = None
    needed_examples: str | None = None


def load_rules(rules_path: Path) -> dict[str, ItemRule]:
    """rubric_rules.yaml의 items 전체를 {item_id: ItemRule} 딕셔너리로 반환한다."""
    data = yaml.safe_load(rules_path.read_text(encoding="utf-8"))
    rules: dict[str, ItemRule] = {}
    for item_id, raw in data["items"].items():
        rules[item_id] = ItemRule(
            item_id=item_id,
            rule_status=raw["rule_status"],
            rule_basis=raw.get("rule_basis", []),
            positive_keywords=raw.get("positive_keywords", []),
            negative_keywords=raw.get("negative_keywords", []),
            na_expression_keywords=raw.get("na_expression_keywords", []),
            patterns=raw.get("patterns", {}),
            exclusion_rules=raw.get("exclusion_rules", []),
            missing_evidence=raw.get("missing_evidence"),
            needed_examples=raw.get("needed_examples"),
        )
    return rules
