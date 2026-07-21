"""AI/규칙 공용 유틸: 인용문이 원문에 실제로 존재하는지 검증한다(환각 방지 안전망).

Claude API 호출 로직은 `evidence_extractor.anthropic_extractor`로 옮겼다(선택적
비교 실험용, ALLOW_PAID_API 게이트 뒤에 있음). 이 파일은 provider와 무관한 순수
문자열 검증 함수만 남겨 `rule_based_extractor`와 `anthropic_extractor` 양쪽에서
공용으로 쓴다.
"""

from __future__ import annotations

from .schema import ExtractedItem


def verify_quotes(raw_excerpt: str, items: list[ExtractedItem]) -> list[ExtractedItem]:
    """quote가 raw_excerpt의 실제 부분문자열인지 전수 검증한다(환각 방지 안전망).

    prsti-auditor가 사후에 무작위 표본을 검증하지만, 이 함수는 매 호출마다 모든
    항목을 검증해 환각이 사용자 검토 단계까지 흘러가지 않도록 즉시 걸러낸다.
    suggested_score가 0보다 큰데 quote가 없거나(raw_excerpt에 없는 문자열이면)
    status="not_found"·suggested_score=0으로 강제 하향하고, rationale에 자동
    검증 실패 사실을 남긴다.
    """
    verified: list[ExtractedItem] = []
    for item in items:
        if item.suggested_score > 0:
            if not item.quote:
                reason = "quote가 비어 있음"
            elif item.quote not in raw_excerpt:
                reason = "quote가 raw_excerpt에서 발견되지 않음(환각 의심)"
            else:
                verified.append(item)
                continue
            verified.append(
                item.model_copy(
                    update={
                        "status": "not_found",
                        "suggested_score": 0,
                        "confidence": "high",
                        "rationale": (
                            f"[자동 검증 실패: {reason}] 원래 rationale: {item.rationale}"
                        ),
                    }
                )
            )
        else:
            verified.append(item)
    return verified
