"""rubric/rubric.yaml을 읽어 채점 항목 구조로 변환한다."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class RubricItem:
    id: str
    tier: str  # "mandatory" | "conditional" | "recommended"
    label: str
    source_table: str
    source_item_id: int
    criteria: dict[int, str]  # {0: "...", 1: "...", 2: "..."}
    na_rule: str | None
    proposed_weight: float | None


def load_rubric(rubric_path: Path) -> list[RubricItem]:
    """rubric.yaml의 items 전체를 RubricItem 리스트로 반환한다.

    areas/excluded_candidates 등 다른 최상위 키는 이 함수의 관심사가 아니다 —
    scoring-engine-dev가 배점 계산 시 별도로 읽는다.
    """
    data = yaml.safe_load(rubric_path.read_text(encoding="utf-8"))
    items: list[RubricItem] = []
    for raw in data["items"]:
        items.append(
            RubricItem(
                id=raw["id"],
                tier=raw["tier"],
                label=raw["label"],
                source_table=raw["source_table"],
                source_item_id=raw["source_item_id"],
                criteria={int(k): v for k, v in raw["criteria"].items()},
                na_rule=raw.get("na_rule"),
                proposed_weight=raw.get("proposed_weight"),
            )
        )
    return items
