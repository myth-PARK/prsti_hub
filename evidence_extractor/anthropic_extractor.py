"""Claude API를 호출해 raw_excerpt로부터 루브릭 근거를 추출한다 — 선택적 비교 실험용.

기본 실행 경로가 아니다. 이 모듈의 함수는 `prsti_common.config.ALLOW_PAID_API`가
명시적으로 true가 아니면 즉시 `PaidApiDisabledError`를 던지고 아무것도 호출하지
않는다 — anthropic 패키지 설치 여부·API 키 존재 여부와는 별개의 3번째 게이트다.
기본 파이프라인(`rule_based_extractor`)은 이 모듈을 import하지 않는다.

핵심 원칙(원 프로젝트 프롬프트의 하드 룰, 이 모듈에서도 유지):
- AI는 절대 최종 점수를 정하지 않는다. 이 모듈의 출력은 전부 suggested_score이며,
  confirmed_score는 사용자 검토 후 별도 규칙 엔진이 채운다.
- suggested_score > 0인 항목은 quote가 raw_excerpt의 실제 부분문자열이어야 한다.
  `evidence_extractor.extractor.verify_quotes()`(AI/규칙 공용 유틸)로 강제한다.
"""

from __future__ import annotations

import os
from pathlib import Path

from prsti_common.config import ALLOW_PAID_API
from prsti_common.rubric_loader import RubricItem, load_items

from .extractor import verify_quotes
from .prompts import PROMPT_VERSION, SYSTEM_PROMPT, build_user_prompt
from .schema import EvidenceReport, ExtractedItem, ExtractionResult

try:
    import anthropic
except ImportError:  # pragma: no cover - anthropic 미설치 환경에서만 실행되는 경로
    anthropic = None  # type: ignore[assignment]

DEFAULT_MODEL = os.environ.get("PRSTI_EXTRACTOR_MODEL", "claude-opus-4-8")


class PaidApiDisabledError(RuntimeError):
    """ALLOW_PAID_API가 true로 설정되지 않았을 때. 무과금 개발 원칙(DEC-013/014)의 게이트."""


class MissingSDKError(RuntimeError):
    """anthropic 패키지가 설치되어 있지 않을 때."""


class MissingAPIKeyError(RuntimeError):
    """ANTHROPIC_API_KEY 환경변수가 설정되어 있지 않을 때."""


def _get_client() -> "anthropic.Anthropic":
    if not ALLOW_PAID_API:
        raise PaidApiDisabledError(
            "ALLOW_PAID_API가 꺼져 있어 유료 Claude API 호출이 차단됩니다. "
            "이 프로젝트의 기본 실행 경로는 무료 규칙 기반(rule_based)입니다 — "
            "의도적으로 라이브 비교 실험을 하려면 환경변수 ALLOW_PAID_API=true를 "
            "명시적으로 설정한 뒤 다시 실행하세요."
        )
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

    실제 Claude API를 호출한다(비용 발생, ALLOW_PAID_API=true 필요). output_format=
    ExtractionResult로 구조화 출력을 강제해 스키마를 벗어난 응답 자체를 원천 차단한다.
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
    """루브릭 로드 → 추출 → 환각 검증 → EvidenceReport 저장까지 전체 파이프라인(선택적 비교 실험용)."""
    items = load_items(rubric_path)
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
