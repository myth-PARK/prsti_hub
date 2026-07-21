"""Claude API를 호출해 raw_excerpt로부터 루브릭 근거를 추출한다.

핵심 원칙(원 프로젝트 프롬프트의 하드 룰):
- AI는 절대 최종 점수를 정하지 않는다. 이 모듈의 출력은 전부 suggested_score이며,
  confirmed_score는 사용자 검토 후 별도 규칙 엔진이 채운다.
- suggested_score > 0인 항목은 quote가 raw_excerpt의 실제 부분문자열이어야 한다.
  이를 강제하기 위해 verify_quotes()가 모든 응답에 전수 검증을 적용한다 — AI가
  스스로 인용을 확인했다고 주장해도, 이 코드가 다시 한번 문자열 대조로 확인한다.

anthropic 패키지 미설치 / ANTHROPIC_API_KEY 미설정 상태에서도 이 모듈은 import되고
verify_quotes()·build_user_prompt() 등은 정상 동작한다 — 실제 API 호출 함수만 그
시점에 명확한 예외를 던진다.
"""

from __future__ import annotations

import os
from pathlib import Path

from .prompts import PROMPT_VERSION, SYSTEM_PROMPT, build_user_prompt
from .rubric_loader import RubricItem, load_rubric
from .schema import EvidenceReport, ExtractedItem, ExtractionResult

try:
    import anthropic
except ImportError:  # pragma: no cover - anthropic 미설치 환경에서만 실행되는 경로
    anthropic = None  # type: ignore[assignment]

DEFAULT_MODEL = os.environ.get("PRSTI_EXTRACTOR_MODEL", "claude-opus-4-8")


class MissingSDKError(RuntimeError):
    """anthropic 패키지가 설치되어 있지 않을 때."""


class MissingAPIKeyError(RuntimeError):
    """ANTHROPIC_API_KEY 환경변수가 설정되어 있지 않을 때."""


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


def _get_client() -> "anthropic.Anthropic":
    if anthropic is None:
        raise MissingSDKError(
            "anthropic 패키지가 설치되어 있지 않습니다. 이 프로젝트의 승인 규칙상 "
            "새 라이브러리 도입은 사용자 승인이 필요합니다 — 승인 후 "
            "`pip install anthropic`을 실행하세요."
        )
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise MissingAPIKeyError(
            "ANTHROPIC_API_KEY 환경변수가 설정되어 있지 않습니다. API 키는 이 "
            "코드베이스나 커밋에 절대 기록하지 않습니다 — 터미널에서 사용자 "
            "본인 계정으로 직접 환경변수를 설정하세요."
        )
    return anthropic.Anthropic()


def extract_evidence(
    *,
    company: str,
    source_doc: str,
    raw_excerpt: str,
    items: list[RubricItem],
    model: str = DEFAULT_MODEL,
) -> list[ExtractedItem]:
    """raw_excerpt 하나에 대해 items 전체의 근거를 추출하고 환각 검증까지 적용한다.

    실제 Claude API를 호출한다(비용 발생). output_format=ExtractionResult로
    구조화 출력을 강제해 스키마를 벗어난 응답 자체를 원천 차단한다.
    """
    client = _get_client()
    user_prompt = build_user_prompt(
        company=company, source_doc=source_doc, raw_excerpt=raw_excerpt, items=items
    )
    response = client.messages.parse(
        model=model,
        max_tokens=8000,
        thinking={"type": "adaptive"},
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
        output_format=ExtractionResult,
    )
    if response.parsed_output is None:
        raise RuntimeError(
            "모델 출력이 요청한 스키마를 만족하지 못해 파싱에 실패했습니다. "
            f"stop_reason={getattr(response, 'stop_reason', '알 수 없음')}"
        )
    return verify_quotes(raw_excerpt, response.parsed_output.items)


def run_extraction(
    *,
    company: str,
    source_doc: str,
    raw_excerpt: str,
    rubric_path: Path,
    output_path: Path,
    rubric_version: str = "1.0",
    model: str = DEFAULT_MODEL,
) -> EvidenceReport:
    """루브릭 로드 → 추출 → 환각 검증 → EvidenceReport 저장까지 전체 파이프라인."""
    items = load_rubric(rubric_path)
    extracted = extract_evidence(
        company=company,
        source_doc=source_doc,
        raw_excerpt=raw_excerpt,
        items=items,
        model=model,
    )
    report = EvidenceReport.build(
        company=company,
        rubric_version=rubric_version,
        model_version=model,
        prompt_version=PROMPT_VERSION,
        source_doc=source_doc,
        items=extracted,
    )
    output_path.write_text(report.model_dump_json(indent=2), encoding="utf-8")
    return report
