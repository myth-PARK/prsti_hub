---
name: prs-scoring-engine-spec
description: "rubric.yaml 스키마 정의, 영역점수 정규화 공식, 버전 관리 규칙, 결정론 테스트 방법을 규정하는 점수 엔진 명세. scoring-engine-dev 에이전트가 Python 규칙 엔진을 구현하거나 테스트를 작성할 때 사용. Phase 0 승인 전에는 설계 문서 작성에만 사용하고 실제 코드를 작성하지 않는다."
---

# PRS 점수 엔진 명세

## 1. 실행 전제조건

이 스킬을 근거로 실제 Python 코드를 작성하기 전에, 사용자가 `rubric/rubric.yaml`의 항목·배점을 승인했는지 먼저 확인한다. `rubric.yaml`의 `status`가 `draft`이면 코드 대신 설계 메모(입출력 스키마, 함수 시그니처 초안)까지만 작성하고 멈춘다. 승인 없이 배점을 코드에 반영하지 않는다 — 이는 원 프롬프트의 명시적 승인 게이트다.

## 2. rubric.yaml 스키마

```yaml
rubric_version: "1.0"
status: "draft"          # draft | approved
areas:
  - id: "가"
    name: "기본 거래 정보"
    weight: 15            # 사용자 승인 후 확정되는 영역 배점
    items: ["필수-01", "필수-02", "필수-03", "필수-04"]
items:
  - id: "필수-01"
    tier: "mandatory"      # mandatory | conditional | recommended
    label: "계약규모"
    source_table: "표6"
    source_item_id: 1
    criteria: { 0: "...", 1: "...", 2: "..." }
    na_rule: null           # conditional 항목만 사용. 예: "exclude_from_denominator" | "auto_max"
```

## 3. 영역점수 계산 공식

논문 기획초안이 제시한 정규화 공식을 그대로 구현한다:

```
영역점수 = (해당 영역 획득점수 ÷ 해당 영역 최대점수) × 영역배점
총점 = Σ 영역점수
```

**최대점수 계산 시 주의**: `na_rule: "exclude_from_denominator"`인 항목이 N/A로 판정되면, 그 항목은 분자·분모 모두에서 제외한다(항목 자체가 없었던 것처럼). `na_rule: "auto_max"`이면 만점(2점)으로 분자에 반영하되 사유를 결과에 남긴다. 이 규칙은 rubric.yaml에서 항목별로 읽어오는 것이지, 엔진 코드에 하드코딩하지 않는다.

## 4. 입력 데이터 분리 원칙

엔진의 입력은 두 종류의 점수를 명확히 구분해서 받는다:

| 필드 | 출처 | 최종 계산에 쓰이는가 |
|------|------|---------------------|
| `suggested_score` | evidence-extractor(AI) | 아니오 — 참고용으로만 결과에 표시 |
| `confirmed_score` | 사용자 검토 | 예 — 이것만 계산에 사용 |

`confirmed_score`가 없는 항목은 "미검토(unreviewed)"로 표시하고 총점 계산에서 제외하거나(설정에 따라) 명확히 "잠정치"임을 표시한다. `suggested_score`를 자동으로 `confirmed_score`에 복사하지 않는다 — 사람의 검토를 건너뛰는 것이므로 원 프롬프트의 AI/점수 분리 원칙 위반이다.

## 5. 결정론(재현성) 테스트

```python
def test_deterministic():
    result1 = compute_score(rubric, confirmed_scores)
    result2 = compute_score(rubric, confirmed_scores)
    assert result1 == result2

def test_rubric_version_pinned():
    result = compute_score(rubric_v1_0, confirmed_scores)
    assert result["rubric_version"] == "1.0"
```

같은 `rubric_version` + 같은 `confirmed_score` 집합이면 항상 같은 출력이 나와야 한다. 부동소수점 반올림 규칙(예: 소수점 둘째자리)도 rubric.yaml이나 엔진 설정에 고정해 버전 간에도 재현되게 한다.

## 6. 회귀 테스트 대상 기업

`prs-rubric-traceability` 스킬의 references/paper-items.md에 정리된 논문 표10의 10개 기업 중, 사용자와 함께 선정한 3~5곳을 기준기업으로 삼아 회귀 테스트를 만든다. 논문의 ○/△/✕ 척도(1/0.5/0)와 PRSTI의 0/1/2 척도는 다르므로, 표10 점수를 그대로 정답값으로 쓰지 않는다 — "표10에서 미공시(✕)였던 항목은 PRSTI에서도 0점이어야 한다"처럼 **방향성**만 회귀 검증에 쓴다(정확한 수치 일치가 아니라 순서·경향 일치를 확인).

## 7. 출력 스키마

```json
{
  "company": "string",
  "rubric_version": "string",
  "computed_at": "ISO8601",
  "areas": [{ "area": "string", "earned": 0, "max": 0, "weight": 0, "area_score": 0.0 }],
  "total_score": 0.0,
  "missing_items": ["item_id"],
  "unreviewed_items": ["item_id"]
}
```
