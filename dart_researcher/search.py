"""PRS 관련 문단 탐색 + 기업 단위 소량 타겟 조회 오케스트레이션.

`.claude/agents/dart-researcher.md`의 출력 스키마를 그대로 만든다. 여기서 만든
raw_excerpt만 evidence-extractor의 입력이 된다 — 이 모듈은 근거를 요약·판단하지
않고 "어디를 봐야 하는지"만 좁혀준다.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from .client import DartClient
from .synonyms import DIRECT_TERMS, LOCATION_MARKERS, STRUCTURAL_GROUPS

# 검색 대상 공시유형(pblntf_ty). A=정기공시(사업/반기/분기보고서), B=주요사항보고서.
RELEVANT_PBLNTF_TY: list[str] = ["A", "B"]

RELEVANT_REPORT_KEYWORDS: list[str] = [
    "사업보고서",
    "반기보고서",
    "분기보고서",
    "타법인 주식",
    "출자증권",
    "유상증자",
]


@dataclass
class PrsPassageMatch:
    matched_terms: list[str] = field(default_factory=list)
    excerpt: str = ""
    start: int = 0
    end: int = 0


def find_prs_passages(text: str, window_size: int = 400, stride: int = 200) -> list[PrsPassageMatch]:
    """direct term 단독 등장 또는 structural group 전체 일치를 창(window) 단위로 찾는다.

    키워드 탐지이지 의미 이해가 아니다 — 찾은 구간은 반드시 evidence-extractor나
    사람이 다시 읽고 판단해야 한다.
    """
    hits: list[PrsPassageMatch] = []
    last_start = max(len(text) - window_size, 0)
    for start in range(0, last_start + 1, stride):
        window = text[start : start + window_size]
        matched: list[str] = [term for term in DIRECT_TERMS if term in window]
        for group in STRUCTURAL_GROUPS:
            if all(term in window for term in group):
                matched.extend(t for t in group if t not in matched)
        for marker in LOCATION_MARKERS:
            if marker in window and marker not in matched:
                matched.append(marker)
        if matched:
            hits.append(PrsPassageMatch(matched_terms=matched, excerpt=window.strip(), start=start, end=start + window_size))
    return _merge_overlapping(hits)


def _merge_overlapping(hits: list[PrsPassageMatch]) -> list[PrsPassageMatch]:
    if not hits:
        return []
    merged = [hits[0]]
    for hit in hits[1:]:
        last = merged[-1]
        if hit.start <= last.end:
            last.excerpt = (last.excerpt + " " + hit.excerpt).strip()
            last.end = max(last.end, hit.end)
            last.matched_terms = sorted(set(last.matched_terms) | set(hit.matched_terms))
        else:
            merged.append(hit)
    return merged


def is_relevant_report(report_nm: str) -> bool:
    return any(keyword in report_nm for keyword in RELEVANT_REPORT_KEYWORDS)


def search_company(*, company_name: str, bgn_de: str, end_de: str, client: DartClient | None = None) -> dict:
    """기업 하나 + 기간 하나에 대한 소량 타겟 조회. 여러 기업을 순회하지 않는다.

    여러 기업을 조회하려면 이 함수를 여러 번 호출하는 대신, 먼저 사용자에게 알리고
    승인받아야 한다(원 프롬프트의 "DART 대량 수집 금지" 제약).
    """
    client = client or DartClient()
    corp_code = client.find_corp_code(company_name)

    all_items = []
    for pblntf_ty in RELEVANT_PBLNTF_TY:
        all_items.extend(client.list_disclosures(corp_code, bgn_de, end_de, pblntf_ty=pblntf_ty))

    # rcept_no로 중복 제거(같은 공시가 여러 유형 질의에 겹쳐 잡히는 경우 대비)
    relevant_by_rcept_no = {
        item.rcept_no: item for item in all_items if is_relevant_report(item.report_nm)
    }

    documents: list[dict] = []
    for item in relevant_by_rcept_no.values():
        text = client.fetch_document_text(item.rcept_no)
        for passage in find_prs_passages(text):
            documents.append(
                {
                    "doc_name": item.report_nm,
                    "rcept_no": item.rcept_no,
                    "disclosure_date": item.rcept_dt,
                    "section": f"매칭 키워드: {', '.join(passage.matched_terms)}",
                    "raw_excerpt": passage.excerpt,
                }
            )

    not_found_keywords = list(DIRECT_TERMS) if not documents else []

    return {
        "company": company_name,
        "retrieved_at": datetime.now(timezone.utc).astimezone().isoformat(),
        "documents": documents,
        "not_found_keywords": not_found_keywords,
    }
