"""dart_researcher → RuleBasedExtractor/Scorer → scoring_engine 순서로 연결한다.

전부 무료다: dart_researcher(DART Open API, 무료) → 이 파이프라인(정규식/키워드,
API 없음) → scoring_engine(순수 계산, API 없음). ANTHROPIC_API_KEY도 anthropic
패키지도 필요 없다.

규칙 기반 점수를 scoring_engine의 confirmed_score 자리에 그대로 공급한다 —
결정론적 코드의 출력이므로(LLM의 비결정적 판단이 아니므로), 사람의 확인을 기다리지
않고 바로 최종 계산에 쓸 수 있다고 판단했다(DEC-014). 다만 confidence·
review_recommended로 "그래도 사람이 다시 봐야 하는 정도"는 계속 표시한다.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from prsti_common.rubric_loader import load_items
from scoring_engine.engine import compute_score
from scoring_engine.schema import ConfirmedItemScore

from .extractor import find_candidates
from .rules import load_rules
from .schema import EvidenceRef, RuleItemResult, RuleScoringReport
from .scorer import score_candidate

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUBRIC_PATH = REPO_ROOT / "rubric" / "rubric.yaml"
DEFAULT_RULES_PATH = REPO_ROOT / "rubric" / "rubric_rules.yaml"


def score_company_from_documents(
    *,
    company_name: str,
    documents: list[dict],
    rubric_path: Path = DEFAULT_RUBRIC_PATH,
    rules_path: Path = DEFAULT_RULES_PATH,
    rubric_version: str = "1.0",
) -> RuleScoringReport:
    """이미 수집된 dart_researcher 결과(documents)로 규칙 기반 채점만 실행한다.

    `_workspace/dart_*.json` 원본은 건드리지 않고, 이 함수의 반환값을 별도
    파생 파일(`_workspace/derived/`)로 저장하는 것은 호출자의 몫이다.
    """
    items = load_items(rubric_path)
    rules = load_rules(rules_path)

    item_results: list[RuleItemResult] = []
    confirmed_scores: list[ConfirmedItemScore] = []
    used_rcept_nos: set[str] = set()

    for item in items:
        rule = rules.get(item.id)
        if rule is None:
            continue

        best_candidate = None
        best_doc = None
        for doc in documents:
            candidate = find_candidates(rule, doc.get("raw_excerpt", ""))
            if candidate is None:
                continue
            if candidate.negative_matched or candidate.na_expression_matched:
                # 부정 표현이나 "조건 비해당 명시"는 다른 어떤 신호보다 결정적이므로
                # 즉시 채택하고 더 찾지 않는다.
                best_candidate = candidate
                best_doc = doc
                break
            if best_candidate is None or len(candidate.matched_patterns) > len(
                best_candidate.matched_patterns
            ):
                # 문서 목록 순서가 아니라 "패턴까지 매치된 더 구체적인 근거"를 우선한다 —
                # 그래야 리스트 앞쪽의 약한 키워드 매치가 뒤쪽의 강한 2점 근거를 가리지 않는다.
                best_candidate = candidate
                best_doc = doc

        outcome = score_candidate(rule, best_candidate)

        evidence: list[EvidenceRef] = []
        if best_candidate is not None and best_doc is not None:
            evidence.append(
                EvidenceRef(
                    text=best_candidate.excerpt,
                    source_document=best_doc.get("doc_name"),
                    receipt_no=best_doc.get("rcept_no"),
                    source_location=best_doc.get("section"),
                )
            )
            if best_doc.get("rcept_no"):
                used_rcept_nos.add(best_doc["rcept_no"])

        item_results.append(
            RuleItemResult(
                rubric_id=item.id,
                score=outcome.score,
                confidence=outcome.confidence,
                review_recommended=outcome.review_recommended,
                evidence=evidence,
                matched_rules=outcome.matched_rules,
                decision_reason=outcome.decision_reason,
                rule_basis=rule.rule_basis,
                rule_status=rule.rule_status,
            )
        )

        if outcome.na_confirmed:
            confirmed_scores.append(ConfirmedItemScore(item_id=item.id, na_confirmed=True))
        else:
            confirmed_scores.append(
                ConfirmedItemScore(item_id=item.id, confirmed_score=outcome.score)
            )

    scoring_result = compute_score(
        rubric_path=rubric_path,
        company=company_name,
        confirmed_scores=confirmed_scores,
        rubric_version=rubric_version,
    )

    considered = len(documents)
    # 후보로 들어왔으나 어떤 항목 규칙에도 채택되지 않은 문서(rcept_no) 수
    all_rcept_nos = {doc.get("rcept_no") for doc in documents if doc.get("rcept_no")}
    excluded = len(all_rcept_nos - used_rcept_nos)

    return RuleScoringReport(
        company=company_name,
        rubric_version=rubric_version,
        computed_at=datetime.now(timezone.utc).astimezone().isoformat(),
        items=item_results,
        total_score=scoring_result.total_score,
        max_score=scoring_result.max_total_score,
        # scoring_engine 자체의 is_provisional은 "미검토 항목 존재"를 뜻하지만, 이
        # 파이프라인은 모든 항목에 항상 confirmed_score를 채워 넣으므로 그 의미가
        # 없다. 여기서는 "1·2점 실사례가 없는 항목이 하나라도 있었는가"로 재정의해,
        # 총점에 여전히 확정되지 않은 부분이 섞여 있음을 정직하게 표시한다.
        is_provisional=any(r.rule_status == "insufficient_evidence" for r in item_results),
        recommended_met=scoring_result.recommended_met,
        recommended_total=scoring_result.recommended_total,
        candidates_considered=considered,
        candidates_excluded=excluded,
        excluded_reasons=(
            [f"{excluded}건은 문서 후보였으나 어떤 항목 규칙과도 매치되지 않아 채택되지 않음"]
            if excluded > 0
            else []
        ),
    )


def score_company_from_dart(
    *,
    company_name: str,
    bgn_de: str,
    end_de: str,
    rubric_path: Path = DEFAULT_RUBRIC_PATH,
    rules_path: Path = DEFAULT_RULES_PATH,
) -> RuleScoringReport:
    """DART 실시간 조회부터 규칙 기반 자동 채점까지 전부 무료로 실행한다.

    dart_researcher 자체가 소량 타겟 조회 전용(기업 1개·기간 1개)이므로, 이 함수도
    같은 제약을 그대로 물려받는다.
    """
    from dart_researcher.search import search_company  # 지연 임포트: DART_API_KEY 없이도

    # rule_based_extractor를 import할 수 있게(무과금 원칙 — §9 테스트가 이를 검증한다)
    dart_result = search_company(company_name=company_name, bgn_de=bgn_de, end_de=end_de)
    return score_company_from_documents(
        company_name=company_name,
        documents=dart_result["documents"],
        rubric_path=rubric_path,
        rules_path=rules_path,
    )
