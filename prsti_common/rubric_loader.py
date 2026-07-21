"""rubric/rubric.yaml을 읽어 채점 항목·영역 구조로 변환한다.

evidence_extractor(항목별 근거 추출)와 scoring_engine(영역·총점 계산) 양쪽이
공유하는 로더다 — rubric.yaml의 실제 구조가 유일한 출처(source of truth)이며,
이 모듈은 그 구조를 그대로 파이썬 객체로 옮길 뿐 배점·규칙을 스스로 판단하지 않는다.
"""

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
    proposed_weight: float | None  # None: 권장항목(배점 없음)


@dataclass(frozen=True)
class AreaDef:
    id: str
    name: str
    weight: float | None  # None: 권장 영역(총점에 미포함, n/4 배지로만 표시)
    item_ids: list[str]


def load_items(rubric_path: Path) -> list[RubricItem]:
    """rubric.yaml의 items 전체를 RubricItem 리스트로 반환한다."""
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


def load_areas(rubric_path: Path) -> list[AreaDef]:
    """rubric.yaml의 areas 전체를 AreaDef 리스트로 반환한다."""
    data = yaml.safe_load(rubric_path.read_text(encoding="utf-8"))
    areas: list[AreaDef] = []
    for raw in data["areas"]:
        areas.append(
            AreaDef(
                id=raw["id"],
                name=raw["name"],
                weight=raw.get("weight"),
                item_ids=list(raw["items"]),
            )
        )
    return areas


# 하위 호환: evidence_extractor가 기존에 쓰던 이름
def load_rubric(rubric_path: Path) -> list[RubricItem]:
    return load_items(rubric_path)
