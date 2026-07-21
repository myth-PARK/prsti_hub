"""추출 프롬프트 구성.

.claude/agents/evidence-extractor.md의 "작업 원칙" 절을 그대로 시스템 프롬프트로
고정한다 — 에이전트 정의 문서와 실제 실행 코드가 서로 다른 원칙을 갖지 않도록.
"""

from __future__ import annotations

from .rubric_loader import RubricItem

PROMPT_VERSION = "extract-v1"

SYSTEM_PROMPT = """당신은 PRS(Price Return Swap) 공시 원문에서 루브릭 항목별 근거를 추출하는 전문가입니다.
당신은 최종 점수를 결정하지 않습니다 — 당신의 출력은 항상 "제안(suggested)"이며,
사용자가 검토한 뒤에만 확정 점수가 됩니다.

반드시 지킬 원칙:
1. suggested_score가 0보다 크면 반드시 quote(원문 그대로의 인용)가 있어야 한다. quote는
   raw_excerpt 안에 실제로 존재하는 문자열이어야 하며, 없는 문장을 지어내지 않는다.
2. 근거를 찾지 못하면 status="not_found", quote=null, suggested_score=0으로 표시한다.
   애매하면 낮은 점수와 낮은 confidence로 표시하되, 없는 것을 있다고 하지 않는다.
   그럴듯한 내용을 추정해서 채우는 것이 가장 위험한 실패 모드다.
3. "회계처리가 적정하다", "공시가 타당하다"처럼 감사의견이나 투자 추천처럼 들리는
   문장을 쓰지 않는다. rationale은 "~라고 명시함" / "~에 대한 언급이 없음"처럼
   사실만 기술한다.
4. 점수는 각 항목에 제시된 criteria(0/1/2점 기준)를 원문과 직접 대조해 판단한다.
   내용이 그럴듯해 보인다고 자동으로 2점을 주지 않는다 — criteria의 각 조건이
   실제로 충족되는지 하나씩 확인한다.
5. 조건부 항목(tier="conditional")은 trigger_condition이 원문에서 확인되지 않거나
   "조건 자체가 해당 없음"이 명시적으로 드러나면, 그 사실을 rationale에 정확히
   남긴다. 최종 처리(만점 자동 부여 등 na_rule 적용)는 별도 규칙 엔진이 하므로,
   당신은 사실만 정확히 보고한다.
6. 채점 대상 항목 전부에 대해 정확히 하나씩 결과를 생성한다 — 항목을 빠뜨리거나
   중복 생성하지 않는다.
"""


def build_user_prompt(
    *, company: str, source_doc: str, raw_excerpt: str, items: list[RubricItem]
) -> str:
    item_blocks = []
    for item in items:
        criteria_lines = "\n".join(
            f"    {score}점: {text}" for score, text in sorted(item.criteria.items())
        )
        trigger = ""
        if item.tier == "conditional" and item.na_rule:
            trigger = f"\n  N/A 처리 규칙: {item.na_rule}"
        item_blocks.append(
            f"- item_id: {item.id} ({item.label}, tier={item.tier})\n"
            f"  판정기준:\n{criteria_lines}{trigger}"
        )
    items_text = "\n".join(item_blocks)

    return f"""기업명: {company}
문서 종류: {source_doc}

## 원문 발췌 (raw_excerpt)
{raw_excerpt}

## 채점 대상 항목 (총 {len(items)}개)
{items_text}

위 raw_excerpt를 채점 대상 항목 전부에 대해 검토하고, 각 item_id마다 정확히 하나의
결과를 생성하라. 원문에 근거가 없는 항목은 status="not_found"로 표시하라."""
