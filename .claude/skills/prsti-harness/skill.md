---
name: prsti-harness
description: "PRSTI(PRS 공시 투명성 지수) 프로젝트의 전체 파이프라인(Phase 0 루브릭 확정 → Phase 1 점수엔진 → Phase 2 DART수집 → Phase 3 AI근거추출 → QA)을 조율하는 오케스트레이터. '루브릭 만들어줘', 'PRSTI 다음 단계 진행해줘', 'PRS 공시 채점 파이프라인 돌려줘' 같은 요청 시 사용. 각 Phase는 사용자 승인 게이트로 분리되어 있어 자동으로 전체를 실행하지 않는다."
---

# PRSTI Orchestrator

PRSTI 프로젝트의 5개 전문 에이전트(rubric-architect, dart-researcher, evidence-extractor, scoring-engine-dev, prsti-auditor)를 조율해 논문의 PRS 통합 공시 지침을 실제 채점 파이프라인으로 만든다.

## 실행 모드: 서브 에이전트

**중요한 환경 제약**: 이 스킬을 설계한 harness 메타 스킬은 "에이전트 팀"(TeamCreate/TaskCreate 기반, 팀원 간 직접 SendMessage 통신)을 기본값으로 권장한다. 그러나 이 환경(Claude Code / VSCode 확장)에는 `TeamCreate`/`TaskCreate` 도구가 없다 — 사용 가능한 것은 `Agent`(서브에이전트 스폰), `SendMessage`(스폰된 에이전트와의 후속 대화), `TaskOutput`/`TaskStop`뿐이다. 따라서 이 오케스트레이터는 **서브 에이전트 모드**로 구성한다: 내(오케스트레이터)가 각 에이전트를 `Agent` 도구로 호출하고, 산출물은 `_workspace/` 파일로 주고받으며, 에이전트 간 직접 통신 대신 내가 산출물을 중계한다.

## 에이전트 구성

| 에이전트 | subagent_type | 역할 | 스킬 | 출력 |
|---------|--------------|------|------|------|
| rubric-architect | `rubric-architect`(커스텀, 미지원 시 `general-purpose`) | Phase 0: 논문→루브릭 변환 | prs-rubric-traceability | `docs/scoring-methodology.md`, `rubric/rubric.yaml`, `_workspace/rubric_gaps.md` |
| dart-researcher | `dart-researcher`(커스텀, 미지원 시 `general-purpose`) | Phase 2: DART 소량 조회 | dart-prs-search | `_workspace/dart_{기업}_{연도}.json` |
| evidence-extractor | `evidence-extractor`(커스텀, 미지원 시 `general-purpose`) | Phase 3: 근거 추출 | prs-evidence-schema | `_workspace/evidence_{기업}_{연도}.json` |
| scoring-engine-dev | `scoring-engine-dev`(커스텀, 미지원 시 `general-purpose`) | Phase 1: 점수 엔진 구현 | prs-scoring-engine-spec | `src/scoring/`, `tests/`, `_workspace/score_*.json` |
| prsti-auditor | `general-purpose` (항상 고정 — QA는 Explore 타입 금지) | 전 Phase QA | prsti-qa-checklist | `_workspace/qa_report_{phase}.md` |

> 커스텀 subagent_type이 이 환경에서 인식되지 않으면 `general-purpose`로 호출하고, 프롬프트 맨 앞에 "먼저 `.claude/agents/{name}.md`를 읽고 그 역할·원칙을 따르라"는 지시를 포함한다.

## 승인 게이트 (원 프롬프트 제약 반영)

이 오케스트레이터는 Phase를 자동으로 순서대로 실행하지 않는다. 각 Phase 진입에는 아래 조건이 필요하다.

| Phase | 진입 조건 |
|-------|----------|
| Phase 0 (rubric-architect) | 없음 — 문서 작업이라 바로 시작 가능 |
| Phase 1 (scoring-engine-dev, 실제 코드) | 사용자가 `rubric.yaml`을 명시적으로 승인(`status: approved`)했을 때 |
| Phase 2 (dart-researcher) | DART API 키 확인 + 조회 대상(기업/연도) 사용자 지정. 대량 수집은 별도 승인 |
| Phase 3 (evidence-extractor) | Phase 2 산출물 존재 + rubric.yaml 승인 |
| Phase 4 (웹 MVP) | 이 하네스에 아직 에이전트 미정의 — Phase 0~3 안정화 후 하네스 확장 필요 |

## 워크플로우

### Phase 1: 준비
1. `c:\Users\cpa12\Desktop\new world\PRSTI\_workspace\` 디렉토리 생성(없으면)
2. 사용자 요청이 어느 Phase를 겨냥하는지 판단 — 명시적으로 말하지 않으면 승인 게이트 표를 보여주고 확인

### Phase 2: 루브릭 설계 (Phase 0, 항상 먼저)

**실행 방식**: 순차 (rubric-architect → prsti-auditor)

1. `rubric-architect` 실행 (foreground 권장 — 다음 단계가 결과에 의존):
   - 입력: 논문 MD 원문 경로, `prs-rubric-traceability` 스킬
   - 출력: `docs/scoring-methodology.md`, `rubric/rubric.yaml`(status: draft), `_workspace/rubric_gaps.md`
2. `prsti-auditor` 실행 — `prsti-qa-checklist` 2절(루브릭↔논문 추적성) 검증
   - 실패 시 구체적 항목:id와 함께 rubric-architect에게 재작업 요청(1회 재시도)
3. `_workspace/rubric_gaps.md`를 사용자에게 제시하고 답변을 요청 — **여기서 오케스트레이터는 멈춘다.** 사용자 답변 없이 Phase 1로 넘어가지 않는다.

### Phase 3: 점수 엔진 (Phase 1, rubric.yaml 승인 후)

1. 사용자가 rubric.yaml을 승인했는지 확인(`status: approved`로 사용자가 직접 바꿨는지, 또는 "승인" 발화가 있었는지)
2. 승인 전이면: `scoring-engine-dev`를 설계 메모 모드로만 실행(코드 작성 금지)
3. 승인 후: `scoring-engine-dev` 실행 → `prsti-auditor`가 `prsti-qa-checklist` 4·5절(스키마 경계면, 재현성) 검증

### Phase 4: DART 수집 + 근거 추출 (Phase 2~3, 병렬 가능)

**실행 방식**: 병렬 (기업 단위로 dart-researcher를 여러 개 동시 호출 가능, 단 승인된 소량 범위 내)

| 에이전트 | 입력 | 출력 | run_in_background |
|---------|------|------|-------------------|
| dart-researcher | 기업명, 연도 | `_workspace/dart_{기업}_{연도}.json` | true (기업 수만큼 병렬) |

각 dart-researcher 완료 후 즉시:
1. `evidence-extractor` 실행(입력: 해당 dart JSON + 승인된 rubric.yaml)
2. `prsti-auditor` 실행 — `prsti-qa-checklist` 3절(환각 검증) — 이 단계는 반드시 evidence-extractor 직후 실행(점진적 QA, 누적 방지)

### Phase 5: 통합 및 보고
1. 모든 기업의 `_workspace/score_*.json`을 scoring-engine-dev로 계산
2. `prsti-auditor`가 6·7절(톤 검증, 승인 게이트 검증) 최종 확인
3. 사용자에게 결과 요약 + `_workspace/` 경로 안내(중간 산출물 보존 — 감사 추적용)

## 데이터 흐름

```
논문 MD ──→ [rubric-architect] ──→ rubric.yaml(draft) ──→ [auditor: 추적성] ──→ 사용자 승인 대기
                                                                                      │
                                                                    승인 후 ──────────┘
                                                                      │
기업/연도 지정 ──→ [dart-researcher]×N(병렬) ──→ dart_*.json
                                                    │
                                                    ▼
                          rubric.yaml(approved) + dart_*.json ──→ [evidence-extractor] ──→ evidence_*.json
                                                                        │
                                                          ──→ [auditor: 환각검증] ──┘
                                                                        │
                          rubric.yaml(approved) + confirmed_score ──→ [scoring-engine-dev] ──→ score_*.json
                                                                        │
                                                          ──→ [auditor: 스키마/재현성/톤/게이트 최종검증]
```

## 에러 핸들링

| 상황 | 전략 |
|------|------|
| rubric-architect가 논문 미출처 항목을 만듦 | auditor가 잡아 1회 재작업 요청. 재실패 시 사용자에게 해당 항목과 함께 보고, Phase 진행 중단 |
| dart-researcher가 대량 수집을 시도 | 즉시 중단하고 사용자에게 알림 — 원 프롬프트 제약이므로 재시도 대신 승인부터 받는다 |
| evidence-extractor 환각 발견 | 해당 항목만 재작업(전체 재작업 아님), auditor가 재검증 |
| scoring-engine-dev가 draft 상태에서 코드 작성 시도 | 즉시 중단, 설계 메모로 전환 요청 |
| 에이전트 실패/중지 | 1회 재시도 → 실패 시 해당 결과 없이 진행하되 최종 보고서에 누락 명시 |
| 여러 기업 중 일부 실패 | 성공한 기업만으로 진행, 실패 기업 목록을 보고서에 명시 |
| 타임아웃 | 현재까지 수집된 부분 결과 사용 |

## 테스트 시나리오

### 정상 흐름
1. 사용자가 "Phase 0부터 시작해줘"라고 요청
2. Phase 2(설계)에서 rubric-architect가 `rubric.yaml`(draft) + `rubric_gaps.md` 생성
3. auditor가 추적성 검증 통과
4. 오케스트레이터가 `rubric_gaps.md`를 사용자에게 제시하고 **멈춤**
5. 사용자가 답변 → 오케스트레이터가 rubric-architect에게 반영 요청 → rubric.yaml 갱신
6. 예상 결과: `docs/scoring-methodology.md`, `rubric/rubric.yaml`(사용자 결정 반영, 아직 draft 또는 approved)

### 에러 흐름
1. Phase 4에서 evidence-extractor가 존재하지 않는 문장을 인용(환각)
2. auditor가 3절 검증에서 quote가 raw_excerpt에 없음을 발견
3. 해당 항목만 evidence-extractor에게 재작업 요청(파일:item_id 명시)
4. 재작업 후 auditor 재검증 통과
5. 최종 보고서에는 재작업 이력이 남지 않아도 되나, `_workspace/qa_report_*.md`에는 최초 실패 기록이 보존됨(감사 추적)

## 지금 시점에서 권장하는 시작 지점

이 하네스가 방금 만들어진 시점 기준으로, 안전하게 바로 시작할 수 있는 것은 **Phase 0(rubric-architect)뿐**이다. Phase 1~3은 사용자의 루브릭 승인, DART API 키, 대량 수집 승인 등 아직 충족되지 않은 전제조건이 있다.
