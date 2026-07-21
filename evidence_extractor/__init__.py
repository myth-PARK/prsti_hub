"""PRSTI evidence-extractor: 공시 원문에서 루브릭 항목별 근거를 구조화된 JSON으로 추출한다.

이 패키지는 점수를 확정하지 않는다. 모든 출력은 suggested_score(AI 제안)이며,
confirmed_score는 사용자 검토 후 별도 규칙 엔진(scoring-engine-dev)이 채운다.
"""

from .schema import EvidenceReport, ExtractedItem, ExtractionResult

__all__ = ["EvidenceReport", "ExtractedItem", "ExtractionResult"]
