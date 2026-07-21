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
