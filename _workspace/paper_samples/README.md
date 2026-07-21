# 논문 인용 샘플 (paper_samples)

이 디렉터리의 JSON 파일들은 **실제 DART 공시를 조회한 결과가 아니다.** `dart-researcher`가
아직 가동되지 않은 상태(DEC-009)에서 `evidence-extractor` 파이프라인을 개발·테스트하기
위해, 논문에서 이미 실제로 인용된 문장만 그대로 옮겨 담은 임시 입력이다.

## 원칙

- `raw_excerpt`는 논문 또는 `rubric/rubric.yaml`의 `accepted_example` 필드에 실제로
  등장하는 문장만 담는다. 문맥을 매끄럽게 하려고 앞뒤로 문장을 지어 붙이지 않는다.
- `source_doc` 필드는 반드시 "논문 인용 샘플"임을 명시한다 — 실제 공시를 조회했다는
  오해를 낳지 않기 위해서다(`.claude/agents/evidence-extractor.md`의 명시적 요구사항).
- 발췌문이 한두 문장뿐이므로, 그 문장이 다루지 않는 나머지 루브릭 항목은 evidence-extractor가
  정당하게 `not_found`로 판정해야 한다. 이는 버그가 아니라 "근거 없으면 not_found"
  원칙이 정상 작동하는 증거다.

## 파일 목록

| 파일 | 출처 | 대응 항목 |
|---|---|---|
| `hanwha_solutions_04.json` | rubric.yaml 필수-04 accepted_example (논문 부록 A1) | 필수-04(기초자산 상세 정보) — 거래형태·거래량은 확인되나 발행가액은 없어 2점이 아닌 부분점수로 판정되어야 함 |
| `conditional_pricing_excerpt.json` | rubric.yaml 조건부-01 accepted_example (논문 5.2.1절) | 조건부-01(가격 보전 조건) — 지급방식은 드러나나 "IRR 보장" 명시 여부·스프레드(bp)는 불명확 |

## 실행 방법 (API 키·anthropic 패키지 준비 후)

```powershell
python -m evidence_extractor.cli `
  _workspace\paper_samples\hanwha_solutions_04.json `
  _workspace\evidence_hanwha_solutions_sample.json
```

`ANTHROPIC_API_KEY`가 설정되어 있지 않거나 `anthropic` 패키지가 설치되어 있지 않으면
`evidence_extractor.extractor.MissingAPIKeyError` / `MissingSDKError`가 명확한
안내 메시지와 함께 발생한다.
