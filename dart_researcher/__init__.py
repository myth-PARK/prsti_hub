"""PRSTI dart-researcher: DART Open API로 PRS 관련 공시를 소량·타겟 조회한다.

원 프로젝트의 명시적 제약: 대량 수집(전체 상장사 순회, 업종 전체 조회, 자동 스케줄
수집) 절대 금지 — 사용자가 지정한 기업 하나·기간 하나에 대한 조회만 수행한다
(.claude/agents/dart-researcher.md, .claude/skills/dart-prs-search/skill.md).

이 패키지는 evidence-extractor에 넘길 raw_excerpt(원문 그대로)만 만든다 — 요약이나
채점은 하지 않는다.
"""

from .search import search_company

__all__ = ["search_company"]
