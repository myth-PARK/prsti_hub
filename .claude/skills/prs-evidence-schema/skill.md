---
name: prs-evidence-schema
description: "공시 원문에서 루브릭 항목별 근거를 추출할 때 지켜야 할 JSON 스키마, 환각 방지 규칙, not_found 처리, 신뢰도 판정 기준. evidence-extractor 에이전트가 구조화된 근거를 생성할 때 사용."
---

# PRS 근거 추출 스키마

AI 추출 단계에서 가장 위험한 실패는 "그럴듯하지만 원문에 없는 근거"를 만들어내는 것이다. 이 스킬은 그 실패를 구조적으로 막기 위한 규칙을 정리한다.

## 1. 좋은 추출 vs 환각 추출

**좋은 추출** (원문에 실제로 있는 문장을 그대로 인용):

입력 원문(한화솔루션 반기보고서 발췌, 논문 표4):
> "회사는 종속기업인 Q Energy Solutions SE 보통주 2,784,293주(22.65%)를 제3자에 매각하였고... 회사는 양수인인 거래상대방과 Q Energy Solutions SE 보통주와 이익참여권을 기초자산으로 하는 매매수익스왑(Price Return Swap) 계약을 체결하였으며..."

올바른 추출 (항목4: 기초자산 상세정보):
```json
{
  "item_id": "필수-04",
  "status": "found",
  "quote": "종속기업인 Q Energy Solutions SE 보통주 2,784,293주(22.65%)를 제3자에 매각",
  "suggested_score": 2,
  "confidence": "high",
  "rationale": "거래 형태(주식매각), 수량, 지분율이 구체적 수치로 명시됨"
}
```

**환각 추출** (원문에 없는 내용을 그럴듯하게 채움) — 절대 이렇게 하지 않는다:
```json
{
  "item_id": "필수-06",
  "status": "found",
  "quote": "본 거래는 K-IFRS 제1109호에 따라 금융부채로 분류하였다",
  "suggested_score": 2
}
```
위 인용문이 실제 원문에 없는데도 만들어 넣으면 환각이다. 논문 4.2절이 정확히 이 사례(한화솔루션·SK이노베이션·LG화학 등 다수 기업이 회계처리 근거를 공시하지 않음)를 실증했으므로, "회계처리 근거가 없다"는 결과가 오히려 정상이다 — 채워 넣고 싶은 유혹을 근거 없음 자체가 유효한 발견이라는 사실로 억제한다.

## 2. not_found 처리

관련 문장을 못 찾으면:
```json
{
  "item_id": "필수-11",
  "status": "not_found",
  "quote": null,
  "source_doc": null,
  "source_location": null,
  "suggested_score": 0,
  "confidence": "high",
  "rationale": "콜옵션 조건에 대한 언급을 제공된 원문에서 찾지 못함"
}
```
`confidence: "high"`는 "못 찾았다는 판단에 대한 확신"이지 "점수에 대한 확신"이 아니다 — 두 confidence의 의미가 다르므로 rationale에 무엇에 대한 확신인지 분명히 적는다.

## 3. 부분 근거 처리 (1점 케이스)

항목은 언급하지만 투자 판단에 필요한 정보가 불완전한 경우:
```json
{
  "item_id": "필수-03",
  "status": "found",
  "quote": "본 계약의 만기는 계약 체결일로부터 3년으로 한다",
  "suggested_score": 1,
  "confidence": "medium",
  "rationale": "만기 기간(3년)은 명시되나 구체적 만기일(연월일)은 확인되지 않음"
}
```
0/1/2 경계를 나눌 때는 "정보가 있다/없다"가 아니라 "투자자가 검증 가능한 형태인가"를 기준으로 판단한다 — [prs-rubric-traceability](../prs-rubric-traceability/skill.md)에서 정의한 항목별 판정기준을 따른다.

## 4. 신뢰도(confidence) 판정 기준

| 신뢰도 | 기준 |
|--------|------|
| high | 원문 인용이 직접적이고, 다른 해석의 여지가 거의 없음 |
| medium | 원문에 관련 내용은 있으나, 다른 문서와 대조가 필요하거나 해석의 여지가 있음 |
| low | 간접적 언급이거나, 다른 공시(예: 모회사 공시)에서 유추해야 하는 경우(논문의 △ 판정과 유사) |

논문 4.2절의 SK이노베이션 사례("파생상품 자산·부채 금액이 자사 공시에는 없었고 모회사 사업보고서에 일부만 기재")처럼, 대상회사 공시가 아니라 관계회사 공시에서 유추한 근거는 `confidence: "low"`로 표시하고 `source_doc`에 어느 회사의 어느 문서인지 명확히 남긴다.

## 5. 감사의견 톤 금지

`rationale` 필드에 다음과 같은 표현을 쓰지 않는다:
- ❌ "회계처리가 적정하다고 판단됨"
- ❌ "이 공시는 타당하다"
- ❌ "투자하기에 안전한 수준이다"

대신 사실 기술로 쓴다:
- ✅ "K-IFRS 조항 인용 없이 회계처리 방식만 서술함"
- ✅ "부외부채 재분류 가능성에 대한 언급이 원문에 없음"

이 서비스는 공시의 충실도를 진단하는 연구·정보제공 도구이며 감사의견이나 투자 권고가 아니다.

## 6. 스키마 필드 요약

전체 JSON 구조는 `evidence-extractor` 에이전트 정의 파일의 예시를 표준으로 따른다. 핵심 필드: `item_id`, `status`(found/not_found), `quote`, `source_doc`, `source_location`, `suggested_score`, `confidence`, `rationale`, `model_version`, `prompt_version`.
