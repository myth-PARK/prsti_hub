"""프로젝트 전역 비용 통제 설정. 환경변수 파싱은 이 파일 한 곳에서만 한다.

무과금 개발 원칙(DEC-013)과 이번 규칙 기반 전환(DEC-014)에 따라:
- 기본 채점 방식은 rule_based(Claude API 미사용, 무료)다.
- 유료 생성형 AI API(AnthropicExtractor)는 ALLOW_PAID_API를 명시적으로 true로
  켜지 않는 한 절대 호출되지 않는다 — SDK 설치 여부·API 키 존재 여부와는 별개의
  독립된 게이트다.
"""

from __future__ import annotations

import os


def _parse_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


ALLOW_PAID_API: bool = _parse_bool(os.environ.get("ALLOW_PAID_API"), default=False)
"""true로 설정하지 않으면 evidence_extractor.anthropic_extractor는 어떤 함수도 실행하지 않는다."""

PRSTI_SCORING_PROVIDER: str = os.environ.get("PRSTI_SCORING_PROVIDER", "rule_based")
"""'rule_based'(기본, 무료) | 'anthropic'(ALLOW_PAID_API=true 필요)."""
