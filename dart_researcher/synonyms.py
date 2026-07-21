"""PRS 검색 동의어 사전. 출처: 논문 4.2절·표4, `.claude/skills/dart-prs-search/skill.md`.

기업마다 PRS를 다르게 부르거나(직접 명칭) 아예 명칭 없이 구조만 서술한다(구조 서술형).
STRUCTURAL_GROUPS의 각 그룹은 "그룹 안의 단어가 전부 같은 구간에 있어야" 신호로
인정한다 — 단어 하나만으로는 너무 흔해서(예: "기초자산") 과다 탐지된다.
"""

from __future__ import annotations

DIRECT_TERMS: list[str] = [
    "PRS",
    "Price Return Swap",
    "주가수익스와프",
    "매매수익스왑",
    "가격수익스왑",
]

STRUCTURAL_GROUPS: list[list[str]] = [
    ["기초자산", "정산금액", "차액"],
    ["만기", "재매입"],
    ["만기", "재매수"],
    ["IRR", "보장"],
    ["목표 수익률", "보장"],
]

# 명칭·구조 서술이 모두 없어도, 이 문구가 있으면 PRS가 숨어 있을 가능성이 있어
# 사람이 다시 봐야 하는 약한 신호(예: 한화솔루션은 이 주석 항목 아래 PRS를 기재)
LOCATION_MARKERS: list[str] = ["우발부채 및 약정사항"]
