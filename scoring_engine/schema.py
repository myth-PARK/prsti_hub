"""scoring_engine 입출력 스키마.

confirmed_score는 evidence-extractor가 만드는 것이 아니라, 사람이 evidence 파일을
검토한 뒤 별도로 입력하는 값이다 — 이 구분을 스키마 레벨에서 강제한다.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class ConfirmedItemScore(BaseModel):
    """사용자가 검토 후 확정한 항목 하나의 점수."""

    item_id: str
    confirmed_score: Literal[0, 1, 2] | None = None
    suggested_score: Literal[0, 1, 2] | None = None  # 참고 표시용. 계산에는 쓰이지 않는다.
    na_confirmed: bool = False
    """사용자가 '조건 비해당(예: 가격보전조건 없음)'임을 원문에서 직접 확인한 경우 True.
    조건부 항목의 na_rule=auto_max 처리 대상이며, confirmed_score와 동시에 쓰지 않는다."""


class ItemResult(BaseModel):
    item_id: str
    area_id: str
    tier: Literal["mandatory", "conditional", "recommended"]
    weight: float | None
    confirmed_score: int | None
    item_score: float | None  # None이면 미검토(총점 계산에서 제외)
    na_applied: bool


class AreaResult(BaseModel):
    area_id: str
    area_name: str
    weight: float | None
    earned: float
    max_possible: float
    unreviewed_item_ids: list[str]


class ScoringResult(BaseModel):
    company: str
    rubric_version: str
    computed_at: str
    areas: list[AreaResult]
    total_score: float
    max_total_score: float
    is_provisional: bool  # 미검토 항목이 하나라도 있으면 True — "잠정치"임을 숨기지 않는다.
    recommended_met: int
    recommended_total: int
    unreviewed_item_ids: list[str]
    item_results: list[ItemResult]
