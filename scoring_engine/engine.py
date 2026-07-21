"""결정론적 점수 계산 규칙 엔진. Claude API를 전혀 호출하지 않는다.

계산 공식은 rubric.yaml 상단의 scoring_formula 필드(DEC-010 확정)를 그대로 구현한다:
    항목점수 = (raw_score / 2) × proposed_weight
    영역점수 = 그 영역 소속 항목점수의 합
    총점 = 모든 영역점수의 합(0~100)
    권장항목은 총점에 포함되지 않고 "n/4 충족" 배지로만 표시(raw_score>=1이면 충족)

`.claude/skills/prs-scoring-engine-spec/skill.md`가 제시했던 "(획득/최대)×영역배점"
비율식은 rubric.yaml 확정 당시(DEC-010) 항목별 가중치 방식으로 대체되었다 — 이
엔진은 더 최신이고 더 구체적인 rubric.yaml의 scoring_formula를 따른다.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from prsti_common.rubric_loader import load_areas, load_items

from .schema import AreaResult, ConfirmedItemScore, ItemResult, ScoringResult


def compute_score(
    *,
    rubric_path: Path,
    company: str,
    confirmed_scores: list[ConfirmedItemScore],
    rubric_version: str = "1.0",
) -> ScoringResult:
    """rubric.yaml + 사용자가 확정한 점수만으로 총점을 계산한다.

    suggested_score(AI 제안값)는 입력에 포함돼 있어도 계산에 쓰지 않는다 — 항상
    confirmed_score(또는 na_confirmed)만 본다. confirmed_score가 없는 항목은
    총점 계산에서 제외하고 unreviewed_item_ids로 명시한다(잠정치를 숨기지 않는다).
    """
    items = load_items(rubric_path)
    areas = load_areas(rubric_path)

    item_by_id = {item.id: item for item in items}
    confirmed_by_id = {c.item_id: c for c in confirmed_scores}

    for item_id in confirmed_by_id:
        if item_id not in item_by_id:
            raise ValueError(f"'{item_id}'는 rubric.yaml에 없는 item_id입니다.")

    area_id_by_item_id: dict[str, str] = {}
    for area in areas:
        for item_id in area.item_ids:
            area_id_by_item_id[item_id] = area.id

    item_results: list[ItemResult] = []
    for item in items:
        area_id = area_id_by_item_id.get(item.id)
        if area_id is None:
            raise ValueError(
                f"'{item.id}'가 어느 영역(area)에도 속해 있지 않습니다 — rubric.yaml 정합성 오류."
            )

        confirmed = confirmed_by_id.get(item.id)

        if item.tier == "recommended":
            score = confirmed.confirmed_score if confirmed else None
            item_results.append(
                ItemResult(
                    item_id=item.id,
                    area_id=area_id,
                    tier=item.tier,
                    weight=None,
                    confirmed_score=score,
                    item_score=None,
                    na_applied=False,
                )
            )
            continue

        if confirmed is not None and confirmed.na_confirmed and confirmed.confirmed_score is not None:
            raise ValueError(
                f"'{item.id}': na_confirmed=True와 confirmed_score를 동시에 지정할 수 없습니다."
            )

        if confirmed is None or (confirmed.confirmed_score is None and not confirmed.na_confirmed):
            item_results.append(
                ItemResult(
                    item_id=item.id,
                    area_id=area_id,
                    tier=item.tier,
                    weight=item.proposed_weight,
                    confirmed_score=None,
                    item_score=None,
                    na_applied=False,
                )
            )
            continue

        if confirmed.na_confirmed:
            if not item.na_rule or "auto_max" not in item.na_rule:
                raise ValueError(
                    f"'{item.id}': na_confirmed=True이지만 na_rule에 auto_max가 없어 처리할 수 없습니다."
                )
            raw = 2
            na_applied = True
        else:
            raw = confirmed.confirmed_score
            na_applied = False

        if item.proposed_weight is None:
            raise ValueError(f"'{item.id}': tier={item.tier}인데 proposed_weight가 없습니다 — rubric.yaml 오류.")

        item_score = round((raw / 2) * item.proposed_weight, 4)
        item_results.append(
            ItemResult(
                item_id=item.id,
                area_id=area_id,
                tier=item.tier,
                weight=item.proposed_weight,
                confirmed_score=raw,
                item_score=item_score,
                na_applied=na_applied,
            )
        )

    area_results: list[AreaResult] = []
    for area in areas:
        if area.weight is None:  # 권장 영역은 총점에 포함하지 않음
            continue
        area_items = [r for r in item_results if r.area_id == area.id]
        earned = sum(r.item_score for r in area_items if r.item_score is not None)
        max_possible = sum(r.weight for r in area_items if r.weight is not None)
        unreviewed = [r.item_id for r in area_items if r.item_score is None]
        area_results.append(
            AreaResult(
                area_id=area.id,
                area_name=area.name,
                weight=area.weight,
                earned=round(earned, 2),
                max_possible=round(max_possible, 2),
                unreviewed_item_ids=unreviewed,
            )
        )

    total_score = round(sum(a.earned for a in area_results), 2)
    max_total_score = round(sum(a.max_possible for a in area_results), 2)

    recommended_results = [r for r in item_results if r.tier == "recommended"]
    recommended_total = len(recommended_results)
    recommended_met = sum(
        1 for r in recommended_results if r.confirmed_score is not None and r.confirmed_score >= 1
    )

    mandatory_conditional_unreviewed = [
        r.item_id for r in item_results if r.tier != "recommended" and r.item_score is None
    ]
    recommended_unreviewed = [r.item_id for r in recommended_results if r.confirmed_score is None]

    return ScoringResult(
        company=company,
        rubric_version=rubric_version,
        computed_at=datetime.now(timezone.utc).astimezone().isoformat(),
        areas=area_results,
        total_score=total_score,
        max_total_score=max_total_score,
        is_provisional=len(mandatory_conditional_unreviewed) > 0,
        recommended_met=recommended_met,
        recommended_total=recommended_total,
        unreviewed_item_ids=mandatory_conditional_unreviewed + recommended_unreviewed,
        item_results=item_results,
    )
