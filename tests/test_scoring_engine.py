"""scoring_engine 테스트. Claude API를 전혀 쓰지 않으므로 mock도 필요 없다 — 전부 실제 실행."""

from __future__ import annotations

from pathlib import Path

import pytest

from prsti_common.rubric_loader import load_areas, load_items
from scoring_engine.engine import compute_score
from scoring_engine.schema import ConfirmedItemScore

REPO_ROOT = Path(__file__).resolve().parents[1]
RUBRIC_PATH = REPO_ROOT / "rubric" / "rubric.yaml"


def test_load_areas_weights_sum_to_100_excluding_recommended():
    areas = load_areas(RUBRIC_PATH)
    scored = [a for a in areas if a.weight is not None]
    assert sum(a.weight for a in scored) == 100
    recommended = [a for a in areas if a.weight is None]
    assert len(recommended) == 1
    assert recommended[0].id == "권장"


def test_no_confirmed_scores_gives_zero_and_marks_provisional():
    result = compute_score(rubric_path=RUBRIC_PATH, company="테스트기업", confirmed_scores=[])
    assert result.total_score == 0
    assert result.max_total_score == 100
    assert result.is_provisional is True
    # 19개 항목 중 권장 4개를 뺀 15개가 mandatory/conditional 미검토로 잡혀야 한다
    mandatory_conditional_unreviewed = [
        r for r in result.item_results if r.tier != "recommended" and r.item_score is None
    ]
    assert len(mandatory_conditional_unreviewed) == 15


def test_all_zero_scores_gives_zero_and_not_provisional():
    items = load_items(RUBRIC_PATH)
    confirmed = [
        ConfirmedItemScore(item_id=item.id, confirmed_score=0)
        for item in items
        if item.tier in ("mandatory", "conditional")
    ]
    result = compute_score(rubric_path=RUBRIC_PATH, company="테스트기업", confirmed_scores=confirmed)
    assert result.total_score == 0
    assert result.is_provisional is False
    # 권장항목은 이 테스트에서 confirmed_score를 주지 않았으므로 여전히 미검토로 남는다
    # (총점 계산에는 영향 없음 — is_provisional은 mandatory/conditional 기준)
    assert set(result.unreviewed_item_ids) == {"권장-01", "권장-02", "권장-03", "권장-04"}


def test_all_perfect_scores_gives_max_total():
    items = load_items(RUBRIC_PATH)
    confirmed = [
        ConfirmedItemScore(item_id=item.id, confirmed_score=2)
        for item in items
        if item.tier in ("mandatory", "conditional")
    ]
    result = compute_score(rubric_path=RUBRIC_PATH, company="테스트기업", confirmed_scores=confirmed)
    assert result.total_score == 100
    assert result.max_total_score == 100
    for area in result.areas:
        assert area.earned == area.max_possible


def test_na_confirmed_conditional_item_scores_as_max():
    items = {item.id: item for item in load_items(RUBRIC_PATH)}
    assert "auto_max" in items["조건부-01"].na_rule

    confirmed = [ConfirmedItemScore(item_id="조건부-01", na_confirmed=True)]
    result = compute_score(rubric_path=RUBRIC_PATH, company="테스트기업", confirmed_scores=confirmed)

    item_result = next(r for r in result.item_results if r.item_id == "조건부-01")
    assert item_result.na_applied is True
    assert item_result.confirmed_score == 2
    assert item_result.item_score == pytest.approx(5.0)  # proposed_weight 5 전액


def test_conflicting_na_confirmed_and_score_raises():
    confirmed = [ConfirmedItemScore(item_id="조건부-01", confirmed_score=1, na_confirmed=True)]
    with pytest.raises(ValueError, match="동시에 지정할 수 없습니다"):
        compute_score(rubric_path=RUBRIC_PATH, company="테스트기업", confirmed_scores=confirmed)


def test_na_confirmed_on_item_without_auto_max_raises():
    # 필수-01은 mandatory이며 na_rule이 없다 — na_confirmed를 쓸 수 없어야 한다
    confirmed = [ConfirmedItemScore(item_id="필수-01", na_confirmed=True)]
    with pytest.raises(ValueError, match="auto_max"):
        compute_score(rubric_path=RUBRIC_PATH, company="테스트기업", confirmed_scores=confirmed)


def test_unknown_item_id_raises():
    confirmed = [ConfirmedItemScore(item_id="존재하지-않음", confirmed_score=1)]
    with pytest.raises(ValueError, match="rubric.yaml에 없는"):
        compute_score(rubric_path=RUBRIC_PATH, company="테스트기업", confirmed_scores=confirmed)


def test_recommended_items_do_not_affect_total_score():
    confirmed = [
        ConfirmedItemScore(item_id="권장-01", confirmed_score=2),
        ConfirmedItemScore(item_id="권장-02", confirmed_score=1),
    ]
    result = compute_score(rubric_path=RUBRIC_PATH, company="테스트기업", confirmed_scores=confirmed)
    assert result.total_score == 0  # 권장 외에는 아무것도 확정 안 함
    assert result.recommended_met == 2
    assert result.recommended_total == 4


def test_suggested_score_is_never_used_in_calculation():
    # suggested_score만 있고 confirmed_score가 없으면 여전히 미검토로 취급돼야 한다
    confirmed = [ConfirmedItemScore(item_id="필수-01", suggested_score=2, confirmed_score=None)]
    result = compute_score(rubric_path=RUBRIC_PATH, company="테스트기업", confirmed_scores=confirmed)
    item_result = next(r for r in result.item_results if r.item_id == "필수-01")
    assert item_result.item_score is None
    assert "필수-01" in result.unreviewed_item_ids


def test_deterministic_given_same_input():
    items = load_items(RUBRIC_PATH)
    confirmed = [
        ConfirmedItemScore(item_id=item.id, confirmed_score=1)
        for item in items
        if item.tier in ("mandatory", "conditional")
    ]
    r1 = compute_score(rubric_path=RUBRIC_PATH, company="X", confirmed_scores=confirmed)
    r2 = compute_score(rubric_path=RUBRIC_PATH, company="X", confirmed_scores=confirmed)
    assert r1.total_score == r2.total_score
    assert r1.areas == r2.areas
