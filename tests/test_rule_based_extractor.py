"""rule_based_extractor 테스트. Claude API를 전혀 쓰지 않으므로 mock 없이 전부 실제 실행한다.

비용 통제 검증(이 파일에서 가장 중요한 부분): 이 패키지를 import해도 anthropic
패키지가 전혀 로드되지 않아야 한다 — 무과금 개발 원칙(DEC-013/014)의 정적 증거.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

import rule_based_extractor
from prsti_common.rubric_loader import load_items
from rule_based_extractor.extractor import find_candidates
from rule_based_extractor.pipeline import score_company_from_documents
from rule_based_extractor.rules import ItemRule, load_rules
from rule_based_extractor.scorer import score_candidate

REPO_ROOT = Path(__file__).resolve().parents[1]
RUBRIC_PATH = REPO_ROOT / "rubric" / "rubric.yaml"
RULES_PATH = REPO_ROOT / "rubric" / "rubric_rules.yaml"


# ---------- 비용 통제: 가장 중요한 테스트 ----------


def test_rule_based_extractor_never_imports_anthropic():
    """다른 테스트 파일(test_anthropic_extractor.py)이 이미 같은 프로세스에서 anthropic을
    로드했을 수 있으므로, 격리된 서브프로세스에서 rule_based_extractor만 단독으로
    import했을 때 anthropic이 로드되는지를 확인한다 — 이게 진짜로 의미 있는 검증이다.
    """
    result = subprocess.run(
        [sys.executable, "-c", "import rule_based_extractor, sys; assert 'anthropic' not in sys.modules"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"rule_based_extractor만 import했는데 anthropic이 로드됐습니다.\nstdout={result.stdout}\nstderr={result.stderr}"
    )


def test_rule_based_extractor_source_never_calls_anthropic_sdk():
    """소스 코드 자체가 anthropic SDK를 참조하지 않는지 정적으로 확인한다."""
    pkg_dir = Path(rule_based_extractor.__file__).parent
    for py_file in pkg_dir.glob("*.py"):
        source = py_file.read_text(encoding="utf-8")
        assert "import anthropic" not in source, f"{py_file.name}이 anthropic을 import합니다"
        assert "anthropic.Anthropic(" not in source, f"{py_file.name}이 Claude API 클라이언트를 생성합니다"


# ---------- rules.py 로더 ----------


def test_all_19_rubric_items_have_a_rule():
    rubric_ids = {item.id for item in load_items(RUBRIC_PATH)}
    rules = load_rules(RULES_PATH)
    assert rubric_ids == set(rules.keys())


def test_rule_status_distribution_matches_documented_analysis():
    rules = load_rules(RULES_PATH)
    statuses = [r.rule_status for r in rules.values()]
    assert statuses.count("confirmed") == 2
    assert statuses.count("provisional") == 8
    assert statuses.count("insufficient_evidence") == 9


def test_insufficient_evidence_items_document_missing_evidence():
    rules = load_rules(RULES_PATH)
    for rule in rules.values():
        if rule.rule_status == "insufficient_evidence":
            assert rule.missing_evidence, f"{rule.item_id}: missing_evidence가 비어 있음"


# ---------- extractor.py: find_candidates ----------


def test_find_candidates_returns_none_when_nothing_matches():
    rule = ItemRule(item_id="필수-07", rule_status="insufficient_evidence", positive_keywords=["재분류"])
    assert find_candidates(rule, "아무 관련 없는 문장입니다.") is None


def test_find_candidates_detects_positive_keyword():
    rule = ItemRule(item_id="필수-10", rule_status="confirmed", positive_keywords=["셀다운"])
    candidate = find_candidates(rule, "본 계약은 셀다운이 가능하다.")
    assert candidate is not None
    assert "셀다운" in candidate.matched_keywords


def test_find_candidates_detects_negative_keyword():
    rule = ItemRule(
        item_id="필수-03",
        rule_status="confirmed",
        positive_keywords=["만기일"],
        negative_keywords=["추후 결정"],
    )
    candidate = find_candidates(rule, "만기일은 추후 결정될 예정입니다.")
    assert candidate is not None
    assert candidate.negative_matched is True


def test_maturity_extension_text_does_not_trigger_call_option_item():
    """필수-11(콜옵션) 회귀 테스트 — rubric_rules.yaml의 exclusion_rules가 문서화한 위험을
    실제로 막고 있는지 확인한다. '만기 연장'은 콜옵션(조기정산)과 다른 개념이므로
    positive_keywords(['조기 정산', '콜옵션'])에 아예 포함하지 않았다."""
    rules = load_rules(RULES_PATH)
    rule = rules["필수-11"]
    text = "매매수익 지급자의 재량으로 만기를 1년씩 반복적으로 연장 가능"  # 한화솔루션 실측
    assert find_candidates(rule, text) is None


# ---------- scorer.py ----------


def test_score_candidate_no_evidence_gives_zero_high_confidence():
    rule = ItemRule(item_id="필수-07", rule_status="insufficient_evidence")
    outcome = score_candidate(rule, None)
    assert outcome.score == 0
    assert outcome.confidence == "high"
    assert outcome.review_recommended is False


def test_score_candidate_insufficient_evidence_never_exceeds_zero_even_with_match():
    rules = load_rules(RULES_PATH)
    rule = rules["필수-12"]  # insufficient_evidence
    candidate = find_candidates(rule, "만기 시 재매입 조건이 있습니다.")
    assert candidate is not None  # positive_keyword("재매입")는 매치됨
    outcome = score_candidate(rule, candidate)
    assert outcome.score == 0, "insufficient_evidence 항목은 매치가 있어도 임의로 점수를 올리면 안 된다"
    assert outcome.review_recommended is True


def test_score_candidate_na_expression_maps_to_auto_max():
    rules = load_rules(RULES_PATH)
    rule = rules["조건부-01"]
    candidate = find_candidates(rule, "본 PRS 계약은 가격 보전 조건이 없으며 순수 기초자산 가격 변동에 따른 정산 구조입니다.")
    assert candidate is not None
    outcome = score_candidate(rule, candidate)
    assert outcome.na_confirmed is True
    assert outcome.score == 2


def test_score_candidate_confirmed_item_real_maturity_date_scores_2():
    rules = load_rules(RULES_PATH)
    rule = rules["필수-03"]
    text = "계약일 2025-06-24 만기일 2028-06-26 만기일에 대한 설명"  # 한화솔루션 실측
    candidate = find_candidates(rule, text)
    outcome = score_candidate(rule, candidate)
    assert outcome.score == 2
    assert outcome.confidence == "high"


def test_score_candidate_confirmed_item_real_celldown_text_scores_2():
    rules = load_rules(RULES_PATH)
    rule = rules["필수-10"]
    text = (
        "매매수익 지급자는 만기일 내 언제라도 기초자산을 처분할 수 있으며, "
        "매매수익 수령자(회사)는 매매수익 지급자가 기초자산 처분 시 기초자산 매각과 "
        "관련하여 이의 제기 또는 항변권을 행사할 수 없음"
    )  # 한화솔루션 실측
    candidate = find_candidates(rule, text)
    outcome = score_candidate(rule, candidate)
    assert outcome.score == 2


def test_score_candidate_provisional_item_without_pattern_caps_at_1():
    rules = load_rules(RULES_PATH)
    rule = rules["필수-02"]  # provisional, 2점 실사례 없음(patterns 미정의)
    candidate = find_candidates(rule, "거래상대방은 SPC입니다.")
    outcome = score_candidate(rule, candidate)
    assert outcome.score == 1, "2점 실사례가 없는 provisional 항목은 1점을 넘지 않아야 한다"
    assert outcome.review_recommended is True


# ---------- pipeline.py: 결정론성 + scoring_engine 연동 ----------


def _sample_documents() -> list[dict]:
    return [
        {
            "doc_name": "반기보고서 (2025.06)",
            "rcept_no": "20250814002909",
            "disclosure_date": "20250814",
            "section": "매칭 키워드: PRS",
            "raw_excerpt": "계약일 2025-06-24 만기일 2028-06-26",
        },
        {
            "doc_name": "반기보고서 (2025.06)",
            "rcept_no": "20250814002909",
            "disclosure_date": "20250814",
            "section": "매칭 키워드: 셀다운",
            "raw_excerpt": (
                "매매수익 지급자는 만기일 내 언제라도 기초자산을 처분할 수 있으며, "
                "매매수익 수령자(회사)는 이의 제기 또는 항변권을 행사할 수 없음"
            ),
        },
        {
            "doc_name": "분기보고서 (2025.03)",
            "rcept_no": "20250514000744",
            "disclosure_date": "20250514",
            "section": "매칭 키워드: 우발부채 및 약정사항",
            "raw_excerpt": "당좌차월 6,000 수입관련 Usance 370,000,000",  # PRS와 무관(위양성)
        },
    ]


def test_pipeline_scores_confirmed_items_from_real_style_documents():
    report = score_company_from_documents(company_name="테스트기업", documents=_sample_documents())
    by_id = {item.rubric_id: item for item in report.items}
    assert by_id["필수-03"].score == 2
    assert by_id["필수-10"].score == 2


def test_pipeline_insufficient_evidence_items_stay_zero():
    report = score_company_from_documents(company_name="테스트기업", documents=_sample_documents())
    by_id = {item.rubric_id: item for item in report.items}
    for item_id in ["필수-07", "필수-08", "필수-11", "필수-12", "조건부-03", "권장-02", "권장-03", "권장-04"]:
        assert by_id[item_id].score == 0
    assert report.is_provisional is True  # insufficient_evidence 항목이 존재하므로 항상 True


def test_pipeline_excludes_irrelevant_document_from_used_count():
    report = score_company_from_documents(company_name="테스트기업", documents=_sample_documents())
    # 3번째 문서(우발부채 무관 위양성)는 어떤 항목에도 채택되지 않아야 한다
    assert report.candidates_excluded >= 1


def test_pipeline_is_deterministic():
    docs = _sample_documents()
    r1 = score_company_from_documents(company_name="X", documents=docs)
    r2 = score_company_from_documents(company_name="X", documents=docs)
    assert r1.total_score == r2.total_score
    assert [i.score for i in r1.items] == [i.score for i in r2.items]


def test_pipeline_uses_scoring_engine_weighted_formula():
    # 필수-03 하나만 만점(2점)이도록 격리된 문서 하나만 넣는다 — '기초자산' 등 다른
    # 항목의 키워드와 우연히 겹치지 않는 문장으로 골라 교란 요인을 없앤다.
    docs = [
        {
            "doc_name": "반기보고서 (2025.06)",
            "rcept_no": "20250814002909",
            "disclosure_date": "20250814",
            "section": "매칭 키워드: PRS",
            "raw_excerpt": "만기일 2028-06-26",
        }
    ]
    report = score_company_from_documents(company_name="테스트기업", documents=docs)
    by_id = {item.rubric_id: item for item in report.items}
    assert by_id["필수-03"].score == 2

    # rubric.yaml DEC-010: 필수-03 weight=4.5 → 항목점수=(2/2)*4.5=4.5
    weights = {item.id: item.proposed_weight for item in load_items(RUBRIC_PATH)}
    expected_total = sum(
        (by_id[item_id].score / 2) * (weights[item_id] or 0)
        for item_id in by_id
        if weights.get(item_id) is not None
    )
    assert report.total_score == pytest.approx(expected_total)
    assert report.total_score == pytest.approx(4.5)
    assert report.max_score == 100.0
