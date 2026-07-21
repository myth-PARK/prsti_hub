# Development Log

새로운 사실이 최초로 기록되는 원본 로그입니다. `decision-log.md`·`troubleshooting-log.md`·`portfolio-evidence.md`는 이 로그를 가공한 결과물이며, 여기 없는 사실을 먼저 다른 파일에 적지 않습니다.

---

## DEV-20260720-01: 저장소 확인 및 프로젝트 이해 정리

- **일시**: 2026-07-20
- **한 일**: `PRSTI/` 폴더에서 논문 원문(MD), 프로젝트 기획초안(DOCX), 논문 PDF 확인. 논문 전문을 읽고 통합 공시 지침(표6~8, 19개 항목) 파악. ARIX 관련 전자신문 기사를 WebFetch로 확인해 공개된 내용만 정리.
- **산출물**: 없음(채팅 응답으로 프로젝트 이해·질문목록·개발계획 제시)
- **관련 커밋**: N/A — git 미도입
- **상태**: [구현됨] (분석·정리 작업 자체는 완료)
- **관련 항목**: TS-001

## DEV-20260720-02: 하네스(에이전트 팀) 구축

- **일시**: 2026-07-20
- **한 일**: `/harness` 요청에 따라 도메인 분석 후 에이전트 5개(rubric-architect, dart-researcher, evidence-extractor, scoring-engine-dev, prsti-auditor)와 스킬 6개(5개 전용 절차 스킬 + 오케스트레이터 prsti-harness) 설계·생성. 논문 19개 항목 원문 인용을 `references/paper-items.md`에 미리 추출.
- **산출물**: `PRSTI/.claude/agents/*.md`(5개), `PRSTI/.claude/skills/*/skill.md`(6개), `PRSTI/.claude/skills/prs-rubric-traceability/references/paper-items.md`
- **관련 커밋**: N/A
- **상태**: [설계완료·미구현] (에이전트/스킬 정의 자체는 완성됐으나, 이는 코드가 아니라 향후 세션이 따를 절차서)
- **관련 항목**: DEC-001, TS-002

## DEV-20260720-03: Phase 0 실작업 — 평가기준 초안

- **일시**: 2026-07-20
- **한 일**: 논문 표6~8의 19개 항목 전체에 0/1/2점 판정기준, 논문 근거 인용, 반례를 작성. 기계가 읽는 `rubric.yaml` 초안 작성(배점 전부 null). 사용자 결정이 필요한 6가지 쟁점을 정리.
- **산출물**: `docs/scoring-methodology.md`, `rubric/rubric.yaml`(status: draft), `_workspace/rubric_gaps.md`
- **관련 커밋**: N/A
- **상태**: [설계완료·미구현] (배점 미확정, 실행 코드 없음)
- **관련 항목**: DEC-002

## DEV-20260720-04: 진행상황 보고서 작성

- **일시**: 2026-07-20
- **한 일**: 지금까지의 작업과 그 이유를 사용자가 이해할 수 있도록 정리한 보고서 작성.
- **산출물**: `docs/progress-report-2026-07-20.md`
- **관련 커밋**: N/A
- **상태**: [구현됨]

## DEV-20260720-05: 포트폴리오 기록체계 설계 제안

- **일시**: 2026-07-20
- **한 일**: 자기소개서용 STAR 소재 기록체계(portfolio-evidence.md 등 4개 파일)와 `portfolio-curator` 에이전트의 템플릿·권한·실행시점·중복방지·신뢰성 검증 방법을 제안(이 시점에는 파일 미생성, 제안만).
- **산출물**: 없음(제안 텍스트)
- **관련 커밋**: N/A
- **상태**: [계획단계]

## DEV-20260720-06: 노션 활용 기준 반영해 설계 확장

- **일시**: 2026-07-20
- **한 일**: 노션 포트폴리오용 16개 프로젝트 정보 항목과 시각자료 후보 기록 방식을 추가 설계. `portfolio-evidence.md`를 Part A(프로젝트 개요, 16항목)/Part B(STAR 사례)로 구조화하고, 별도 `portfolio-assets-log.md` 신설을 제안. Notion 14섹션 매핑표 작성.
- **산출물**: 없음(제안 텍스트)
- **관련 커밋**: N/A
- **상태**: [계획단계]

## DEV-20260720-07: Notion 포트폴리오 페이지 실제 생성

- **일시**: 2026-07-20
- **한 일**: Notion MCP로 기존 포트폴리오 구조("MYTH's Portfolio" 페이지 > PROJECT 데이터베이스) 확인. 기존 프로젝트 항목("제조데이터 기반 불량·백오더 예측")과 동일한 형식으로 PRSTI 항목을 신규 생성. 현재 상태(Phase 0, 서비스 미구현)를 정직하게 반영.
- **산출물**: Notion 페이지 `PRSTI — PRS 공시 투명성 지수` (https://app.notion.com/p/3a3cca252874818bbad7cecb161806d5)
- **관련 커밋**: N/A
- **상태**: [구현됨] (Notion 페이지 생성 자체는 완료된 사실)
- **관련 항목**: DEC-003

## DEV-20260720-08: portfolio-curator 에이전트 및 로컬 기록 5종 생성

- **일시**: 2026-07-20
- **한 일**: 이 파일을 포함한 5개 로컬 기록 파일(development-log, decision-log, troubleshooting-log, portfolio-evidence, portfolio-assets-log) 생성. `portfolio-curator` 에이전트 정의 생성 — 로컬 기록 유지 + Notion PRSTI 페이지 동기화 역할.
- **산출물**: `docs/development-log.md`, `docs/decision-log.md`, `docs/troubleshooting-log.md`, `docs/portfolio-evidence.md`, `docs/portfolio-assets-log.md`, `.claude/agents/portfolio-curator.md`
- **관련 커밋**: N/A
- **상태**: [구현됨]
- **관련 항목**: DEC-003

## DEV-20260720-09: rubric_gaps.md 핵심 4개 질문에 대한 사용자 답변 반영

- **일시**: 2026-07-20
- **한 일**: 사용자에게 남은 결정사항 목록을 정리해 보여주고, 그중 4개(영역구조·미출처3항목·조건부항목 N/A처리·제3자자료 인정여부)를 AskUserQuestion으로 질문. 사용자가 4개 전부 AI 추천안을 선택. `rubric.yaml`의 `na_rule`(조건부-01/02/03)과 필수-08 `counter_example`을 갱신하고 `confirmed_decisions` 목록 추가.
- **산출물**: `rubric/rubric.yaml`(수정), `docs/decision-log.md`(DEC-002 상태 갱신, DEC-005~007 추가)
- **관련 커밋**: N/A
- **상태**: [구현됨]
- **관련 항목**: DEC-002, DEC-005, DEC-006, DEC-007

## DEV-20260720-10: "AI 활용 포트폴리오 요건 대조" 신설

- **일시**: 2026-07-20
- **한 일**: 사용자가 공유한 커리어 조언(회계법인 지원 시 "AI 활용" 2순위 강점 요건 3가지 + GitHub/Notion 산출물 조건)을 PRSTI 현재 상태와 대조하는 표를 `portfolio-evidence.md`에 추가. Agent/Harness/Skills 이해는 충족, AI Product 개발·생성형 AI API 활용 경험은 미충족, GitHub 산출물 부재를 확인.
- **산출물**: `docs/portfolio-evidence.md`(신규 섹션 + 14번 항목 링크 추가)
- **관련 커밋**: N/A
- **상태**: [구현됨]
- **관련 항목**: DEC-008

## DEV-20260720-11: git 설치 및 GitHub 준비 (목요일 마감 대응)

- **일시**: 2026-07-20
- **한 일**: 사용자가 "GitHub 산출물은 목요일(2026-07-23)까지만 나오면 된다, 순리대로 가자"고 확인 — winget으로 Git for Windows 2.55.0과 GitHub CLI 2.96.0 설치. git 전역 사용자 정보(이름·이메일) 설정. PRSTI 폴더에 `git init` 후 README.md·.gitignore 작성, 4개 커밋으로 정리(초기자료 → 하네스 → 루브릭/문서 → README). 작업 중 출처 불명 `record/` 폴더(jsPDF로 생성된 8페이지 PDF, VSCode 확장의 자체 내보내기로 추정)를 발견해 커밋에서 제외(.gitignore).
- **산출물**: `PRSTI/.git/`(로컬 저장소, 커밋 4개), `PRSTI/README.md`, `PRSTI/.gitignore`
- **관련 커밋**: a401779, ac98391, 4ef6989, 20fa9b6
- **상태**: [구현됨](로컬 git까지만. GitHub 원격 저장소는 `gh auth login` 인증이 필요해 사용자 몫으로 남김)
- **관련 항목**: DEC-004, DEC-008

## DEV-20260720-12: GitHub 원격 저장소 생성 및 푸시 완료

- **일시**: 2026-07-20
- **한 일**: 사용자가 VS Code 재시작 후 `gh auth login`을 직접 완료(계정 myth-PARK). 인증 확인 후 `gh repo create prsti_hub --public --source=. --remote=origin --push`로 원격 저장소 생성과 첫 푸시를 함께 수행. 커밋 5개(초기자료·하네스·루브릭문서·README·기록)가 그대로 반영됨.
- **산출물**: https://github.com/myth-PARK/prsti_hub (public)
- **관련 커밋**: 17fc9d9까지 전체
- **상태**: [구현됨]
- **관련 항목**: DEC-008

## DEV-20260720-13: "AI 활용 역량"을 포트폴리오 1순위로 재확정, 로드맵 재배열

- **일시**: 2026-07-20
- **한 일**: 사용자가 채용 요구사항 "② AI 활용 역량 — 생성형 AI API/오픈소스 LLM 기반 솔루션 기획|설계|개발 경험"을 1순위로 지정. `portfolio-evidence.md`에 최상단 우선순위 선언 추가, 기획/설계/개발 3단계로 충족 여부를 정직하게 분해(기획·설계는 충족, 개발만 미충족), 요건 대조표 갱신(GitHub 존재 반영), PE-002(환각 방지 설계 STAR 사례) 추가. `prsti-harness`와 `evidence-extractor` 에이전트에 로드맵 재배열(Phase 2를 기다리지 않고 논문 인용 샘플로 evidence-extractor 우선 개발) 반영.
- **산출물**: `docs/portfolio-evidence.md`, `.claude/skills/prsti-harness/skill.md`, `.claude/agents/evidence-extractor.md`
- **관련 커밋**: (다음 커밋에 포함 예정)
- **상태**: [구현됨](문서·설계 수준 — 실제 evidence-extractor 코드는 아직 다음 단계)
- **관련 항목**: DEC-009

## DEV-20260720-14: 배점 확정 및 표10 기반 검증 계산

- **일시**: 2026-07-20
- **한 일**: 사용자와 배점 논의. 조건부는 100점 포함·권장은 배점 없이 배지 표시, 카테고리 배분(논문 강조점 반영안), 카테고리 내 균등배분을 확정. 사용자 요청으로 "라"(재매입조건 1개 항목)의 20점 집중도를 10점으로 낮추고 차액을 "다"로 흡수(다 35→45). `rubric.yaml`의 area weight·item별 proposed_weight 전체 반영, status를 draft에서 approved-pending-validation으로 변경. 표10 데이터(○/△/✕)를 raw 0/1/2로 근사 변환해 10개 기업 조건부 제외 85점 만점 시범 채점 수행 — 점수 스프레드 확인, "다" 카테고리 절반 이상이 현재 표본에서 무변별(전원 0) 구간임을 발견.
- **산출물**: `rubric/rubric.yaml`(전체 배점 반영, v1.0), `docs/decision-log.md`(DEC-010)
- **관련 커밋**: (다음 커밋에 포함 예정)
- **상태**: [구현됨](배점 잠정 확정 + 검증 계산 완료. 실제 채점 코드는 여전히 미구현)
- **관련 항목**: DEC-010

## DEV-20260720-15: evidence-extractor 실제 코드 최초 구현

- **일시**: 2026-07-20
- **한 일**: `evidence_extractor/` 파이썬 패키지를 신규 작성 — `rubric_loader.py`(rubric.yaml → 19개 항목 구조체), `schema.py`(Pydantic 구조화 출력 모델), `prompts.py`(`.claude/agents/evidence-extractor.md`의 작업원칙을 그대로 시스템 프롬프트로 고정), `extractor.py`(Claude API 호출 + `verify_quotes()` 전수 환각 검증), `cli.py`(실행 진입점). 착수 전 진단으로 `ANTHROPIC_API_KEY` 미설정·`anthropic` 패키지 미설치를 확인(`pyyaml`·`pydantic`·`pytest`는 이미 설치돼 있어 추가 승인 불필요)했으며, 이는 별도 승인 대기 상태로 남김(DEC-012). `rubric.yaml`의 실제 `accepted_example` 인용문(한화솔루션 필수-04, 조건부-01)만 그대로 옮겨 `_workspace/paper_samples/`에 논문 인용 샘플 입력 2건을 생성 — 지어낸 문장은 전혀 포함하지 않음. `tests/test_evidence_extractor.py` 12개 테스트를 작성해 `pytest`로 실행, 전부 통과 확인(루브릭 로더·프롬프트 구성·환각 검증 로직은 실제 실행, API 호출부는 `unittest.mock`으로 배선만 검증 — 실제 네트워크 호출 없음).
- **산출물**: `evidence_extractor/__init__.py`, `evidence_extractor/rubric_loader.py`, `evidence_extractor/schema.py`, `evidence_extractor/prompts.py`, `evidence_extractor/extractor.py`, `evidence_extractor/cli.py`, `tests/test_evidence_extractor.py`, `_workspace/paper_samples/*.json`(2건)·`README.md`, `requirements.txt`, `requirements-dev.txt`, `.gitignore`(수정)
- **관련 커밋**: (다음 커밋에 포함 예정)
- **상태**: [구현됨](코드·테스트는 완성. 단, `anthropic` 미설치·API 키 미설정으로 실제 라이브 API 호출은 아직 한 번도 실행하지 못함 — mock 테스트로만 배선을 검증한 상태이며 이 한계를 숨기지 않고 명시함)
- **관련 항목**: DEC-009, DEC-011, DEC-012

## DEV-20260720-16: 무과금 개발 원칙 채택 + scoring_engine 구현(zero-cost, 실제 API 미사용)

- **일시**: 2026-07-20
- **한 일**: 사용자가 `anthropic` 패키지 설치를 승인해 실행(성공, anthropic 0.117.0). 이어서 `ANTHROPIC_API_KEY` 발급 관련 설명을 드렸으나, 사용자가 "무과금 개발 원칙으로 변경"을 명시적으로 지시(DEC-013). 이에 따라 라이브 API 검증은 보류하고, Claude API를 전혀 호출하지 않는 다음 컴포넌트인 `scoring_engine`을 실제로 구현. 리팩터링으로 `rubric_loader.py`를 `evidence_extractor` 전용에서 `prsti_common`(양쪽 컴포넌트 공유) 패키지로 이동하고 `areas` 로더(`load_areas`)를 추가. `scoring_engine/engine.py`가 `rubric.yaml`의 `scoring_formula`(항목점수=(raw/2)×proposed_weight, DEC-010)를 그대로 구현 — `confirmed_score`만 계산에 쓰고 `suggested_score`는 절대 쓰지 않음을 테스트로 강제(`test_suggested_score_is_never_used_in_calculation`). 조건부 항목의 `na_confirmed`(auto_max) 처리, 미검토 항목의 "잠정치" 표시(`is_provisional`), 권장항목의 "n/4 충족" 배지 계산까지 구현. `tests/test_scoring_engine.py` 10개 작성, 전체 테스트(evidence_extractor 12개 + scoring_engine 10개 + 로더 1개) 23개 전부 통과 확인 — **이번에는 mock이 아니라 전부 실제 실행 검증**(API를 안 쓰는 순수 로직이라 mock 자체가 필요 없음).
- **산출물**: `prsti_common/__init__.py`, `prsti_common/rubric_loader.py`(신규, `evidence_extractor/rubric_loader.py`에서 이관+확장), `scoring_engine/__init__.py`, `scoring_engine/schema.py`, `scoring_engine/engine.py`, `scoring_engine/cli.py`, `tests/test_scoring_engine.py`, `evidence_extractor/extractor.py`·`prompts.py`(import 경로 수정), `docs/decision-log.md`(DEC-013)
- **관련 커밋**: (다음 커밋에 포함 예정)
- **상태**: [구현됨](scoring_engine은 실제 API 호출이 전혀 없는 컴포넌트라 "코드 완성 + 실제 실행 검증"까지 완전히 도달함 — evidence-extractor와 달리 라이브/목 구분 자체가 필요 없음)
- **관련 항목**: DEC-013

## DEV-20260721-01: 논문 부록 사례 6개 기업 보완 (TS-001 완전 해결)

- **일시**: 2026-07-21
- **한 일**: 사용자가 `회계저널 6월호 - 추출본_박신화.pdf` 경로를 제시하며 논문 MD 추출본의 누락 사례 보완을 요청. `pypdf`·`pdfplumber`가 이미 설치돼 있음을 확인(1차 시도였던 TS-001 당시의 poppler 미설치 블로커가 더 이상 없음)하고 `pdfplumber`로 PDF 50페이지(=논문 p.280, 부록 끝) 전체를 재추출. 기존 MD 파일이 에코프로 사례 문장 중간("...공시의 투명성에는")에서 끊겨 있던 지점을 정확히 찾아, 그 이후 5~10번(효성화학·롯데케미칼·CJ ENM·넷마블·두산·금호건설) 서사를 원문 그대로(PDF 줄바꿈만 문단으로 재구성, 내용 재작성이나 요약 없음) 이어 붙임. `paper-items.md`의 "부록 사례 커버리지" 절도 "10개 기업 전원 확보 완료"로 갱신.
- **산출물**: `주가수익스와프(PRS)의 공시 투명성 제고 방안.md`(보완), `.claude/skills/prs-rubric-traceability/references/paper-items.md`(갱신), `docs/troubleshooting-log.md`(TS-001 완전 해결로 갱신)
- **관련 커밋**: (다음 커밋에 포함 예정)
- **상태**: [구현됨]
- **관련 항목**: TS-001

## DEV-20260721-02: dart-researcher 실제 구현 + 한화솔루션 실 데이터 최초 수집

- **일시**: 2026-07-21
- **한 일**: 사용자가 DART Open API 키를 발급받아 제공(무료 서비스, 과금 없음 — 무과금 개발 원칙과 상충하지 않음). 환경변수(`DART_API_KEY`)로만 저장하고 어떤 파일에도 기록하지 않음. `dart_researcher` 패키지를 신규 구현 — `client.py`(corpCode.xml·list.json·document.xml 3개 DART Open API 엔드포인트 래퍼), `synonyms.py`(논문 4.2절 동의어 사전을 코드로 옮김 — 직접 명칭 5개 + 구조 서술형 5개 그룹 + 위치 마커 1개), `search.py`(슬라이딩 윈도우 키워드 탐지로 raw_excerpt 후보를 찾는 `find_prs_passages`, 기업 1개·기간 1개로 한정된 `search_company` 오케스트레이션), `cli.py`. `tests/test_dart_researcher.py` 6개(mock 기반, 구조 서술형 그룹이 단어 일부만으로는 탐지되지 않는지 — 과다탐지 방지 — 를 포함) 작성, 전체 테스트 29/29 통과.

  이어서 한화솔루션 1개 기업(원 프롬프트의 "대량 수집 금지" 제약에 따라 소량 타겟 조회로 한정)에 대해 **실제 DART API를 처음으로 호출**해 파이프라인 전체(corp_code 조회 → 공시검색 → 원문 다운로드 → 키워드 탐지)를 검증. 2025년 반기보고서([기재정정]반기보고서, rcept_no 20250814003624)에서 "매매수익스왑(PRS) 약정에 대한 설명 회사는 종속기업인 Q Energy Solutions SE 보통주 2,78..."로 시작하는 실제 공시 원문을 확인 — 이는 `rubric.yaml` 필수-04 `accepted_example`이 이미 인용하고 있던 문장과 정확히 일치해, 논문 인용이 실제 공시와 부합함을 교차 검증한 셈이 됨. 총 29개 후보 구간을 `_workspace/dart_한화솔루션_2025.json`에 저장(dart-researcher.md 출력 스키마 그대로).
- **산출물**: `dart_researcher/__init__.py`, `client.py`, `synonyms.py`, `search.py`, `cli.py`, `tests/test_dart_researcher.py`, `_workspace/dart_한화솔루션_2025.json`(실제 DART 데이터, 논문 인용 샘플 아님)
- **관련 커밋**: (다음 커밋에 포함 예정)
- **상태**: [구현됨·실 데이터 검증 완료] — DART 연동은 evidence_extractor와 달리 무료라 라이브 검증까지 완료. 다음 단계(이 실제 raw_excerpt를 evidence_extractor에 넣어 근거를 추출하는 것)는 여전히 Claude API 호출이 필요해 무과금 원칙(DEC-013)상 보류 중.
- **관련 항목**: DEC-013
