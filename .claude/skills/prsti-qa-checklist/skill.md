---
name: prsti-qa-checklist
description: "PRSTI 파이프라인 산출물 간 경계면 정합성(rubric↔논문, evidence↔원문, schema↔schema)과 원 프롬프트 제약 준수를 검증하는 체크리스트와 절차. prsti-auditor 에이전트가 각 Phase 산출물 완성 직후 점진적으로 실행."
---

# PRSTI QA 체크리스트

이 프로젝트에서 QA의 핵심은 "파일이 존재하는가"가 아니라 "두 산출물이 만나는 지점에서 서로 맞는가"다. 개별 에이전트는 각자 맡은 일을 "올바르게" 했다고 보고하지만, 연결 지점에서 어긋나는 경우가 실제 결함의 대다수다.

## 1. 언제 실행하는가

전체 파이프라인이 끝난 뒤 한 번에 검증하지 않는다. 아래 표의 각 Phase가 산출물을 낼 때마다 즉시 해당 행을 검증한다.

| Phase 완료 시점 | 검증 항목 |
|-----------------|----------|
| rubric-architect 완료 | 2절 (루브릭↔논문 추적성) |
| dart-researcher 완료 | 4절의 출처 메타데이터 완전성만 우선 확인 |
| evidence-extractor 완료 | 3절 (근거↔원문 환각 검증) |
| scoring-engine-dev 완료 | 4절 (스키마 경계면), 5절 (재현성) |
| 문서/보고서 생성 시 | 6절 (톤 검증) |

## 2. 루브릭 ↔ 논문 추적성 검증

**양쪽을 동시에 연다**: `rubric/rubric.yaml`과 `prs-rubric-traceability` 스킬의 `references/paper-items.md`.

```
검증 단계:
1. rubric.yaml의 모든 item에서 source_table + source_item_id 추출
2. paper-items.md의 19개 항목(필수12+조건부3+권장4) 목록과 1:1 대조
3. rubric.yaml에는 있는데 paper-items.md에 없는 항목 → "미출처" 플래그
4. paper-items.md에는 있는데 rubric.yaml에 없는 항목 → "누락" 플래그
5. 두 플래그 모두 0이어야 통과
```

이미 알려진 위험 패턴: "PRS 명칭", "공시 위치", "진성매각 판단"이 승인 기록 없이 rubric.yaml에 나타나면 즉시 실패 처리하고 rubric-architect에게 반려한다(참고: [prs-rubric-traceability skill.md 4절](../prs-rubric-traceability/skill.md)).

## 3. 근거 ↔ 원문 환각 검증

**양쪽을 동시에 연다**: `_workspace/evidence_*.json`의 `quote` 필드와 `_workspace/dart_*.json`의 `raw_excerpt` 필드.

```
검증 단계:
1. evidence JSON에서 status="found"인 모든 항목의 quote 추출
2. 대응하는 dart JSON의 raw_excerpt 문자열에서 quote가 부분 문자열로 존재하는지 확인
3. 존재하지 않으면 → 환각으로 판정, 해당 항목 재작업 요청
4. status="not_found"인데 suggested_score > 0인 항목 → 즉시 실패(모순)
```
전수 검증이 비용 부담이면 최소 무작위 표본(항목의 20% 이상, 최소 5개)을 뽑아 확인하되, `suggested_score: 2`(최고점) 항목은 반드시 전수 확인한다 — 최고점 판정이 틀리면 총점 왜곡이 가장 크다.

## 4. 스키마 경계면 검증

**양쪽을 동시에 연다**: `evidence-extractor` 출력 JSON의 필드명과 `scoring-engine-dev`가 파싱하는 입력 코드.

```
검증 단계:
1. evidence JSON의 필드명 목록 추출 (item_id, suggested_score, confidence, ...)
2. scoring engine 입력 파서 코드에서 참조하는 필드명 목록 추출
3. 두 목록이 정확히 일치하는지 확인 (오탈자, snake_case/camelCase 혼용 등)
4. rubric.yaml의 item id 형식(예: "필수-01")과 evidence JSON의 item_id 형식이 일치하는지 확인
```

## 5. 재현성 검증

```
검증 단계:
1. 동일한 rubric_version + 동일한 confirmed_score 세트로 scoring engine을 2회 실행
2. 두 결과 JSON을 diff
3. computed_at(타임스탬프)을 제외하고 완전히 동일해야 통과
```

## 6. 톤 검증 (감사의견 금지)

생성된 모든 사용자 대면 산출물(scoring-methodology.md, 보고서, evidence rationale)에서 다음 패턴을 검색한다:

- "적정하다", "적정한 것으로 판단" — 감사의견 표현
- "타당하다고 판단됨", "문제없다고 확인됨" — 확정적 평가 표현
- "투자를 권장", "매수/매도 의견" — 투자 권고 표현

발견 시 "연구·정보제공 목적" 톤(사실 기술, "~라고 명시함"/"~에 대한 언급이 없음")으로 재작성을 요청한다.

## 7. 원 프롬프트 승인 게이트 검증

```
- [ ] rubric.yaml의 status가 "approved"로 바뀐 시점에 실제 사용자 승인 기록이 있는가 (없이 자동 전환되지 않았는가)
- [ ] scoring-engine-dev가 rubric status="draft" 상태에서 실제 코드(설계 메모 아님)를 작성하지 않았는가
- [ ] dart-researcher가 승인 없이 대량 수집을 시도한 흔적이 없는가 (조회 기업 수/문서 수 확인)
- [ ] evidence-extractor의 어떤 항목도 confirmed_score를 스스로 채우지 않았는가
```

## 8. 보고 형식

`_workspace/qa_report_{phase}.md`에 다음 형식으로 남긴다:

```markdown
# QA 리포트 — {phase}
검증일시: {timestamp}

## 통과
- {검증 항목}: 통과

## 실패
- {검증 항목}: {파일:항목 id} — {구체적으로 무엇이 왜 틀렸는지}

## 미검증
- {검증 항목}: {사유 — 예: 대조 대상 파일 없음}
```
