"""evidence-extractor의 출력 스키마.

AI(LLM)가 채우는 부분은 ExtractionResult뿐이다. company/rubric_version/model_version/
extracted_at 같은 출처 메타데이터는 모델이 스스로 보고하게 두지 않고 우리 코드가
직접 채운다 — 모델이 자기 버전이나 시각을 정확히 안다고 신뢰할 이유가 없기 때문이다.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel


class ExtractedItem(BaseModel):
    """루브릭 항목 하나에 대한 AI의 근거 추출 결과. 점수는 제안(suggested)일 뿐이다."""

    item_id: str
    status: Literal["found", "not_found"]
    quote: str | None = None
    source_location: str | None = None
    suggested_score: Literal[0, 1, 2]
    confidence: Literal["low", "medium", "high"]
    rationale: str


class ExtractionResult(BaseModel):
    """client.messages.parse(..., output_format=ExtractionResult)의 반환 스키마."""

    items: list[ExtractedItem]


class EvidenceReport(BaseModel):
    """_workspace/evidence_{기업명}_{연도}.json으로 저장되는 최종 산출물."""

    company: str
    rubric_version: str
    model_version: str
    prompt_version: str
    source_doc: str
    extracted_at: str
    items: list[ExtractedItem]

    @classmethod
    def build(
        cls,
        *,
        company: str,
        rubric_version: str,
        model_version: str,
        prompt_version: str,
        source_doc: str,
        items: list[ExtractedItem],
    ) -> "EvidenceReport":
        return cls(
            company=company,
            rubric_version=rubric_version,
            model_version=model_version,
            prompt_version=prompt_version,
            source_doc=source_doc,
            extracted_at=datetime.now(timezone.utc).astimezone().isoformat(),
            items=items,
        )
