"""PRSTI scoring-engine: rubric.yaml과 사용자가 확정한 점수만으로 결정론적으로 총점을 계산한다.

Claude API를 전혀 호출하지 않는다 — 순수 규칙 엔진이다(무과금 개발 원칙, DEC-013).
AI가 제안한 suggested_score는 이 엔진의 계산에 절대 쓰이지 않는다. 오직 사용자가
검토·확정한 confirmed_score만 총점에 반영된다 — 원 프로젝트의 AI/점수 분리 원칙을
코드 구조로 강제하는 지점이다.
"""

from .schema import AreaResult, ConfirmedItemScore, ScoringResult
from .engine import compute_score

__all__ = ["AreaResult", "ConfirmedItemScore", "ScoringResult", "compute_score"]
