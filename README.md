# PRSTI — PRS 공시 투명성 지수 (PRS Transparency Index)

> **현재 상태: 규칙 기반 자동 채점 파이프라인 + 웹 애플리케이션 공개 배포 완료.** ([바로 써보기](https://prstiapp-xhvlnxkiyczgg46bluu7qu.streamlit.app/))
> 이 저장소는 진행 중인 개인 프로젝트이며, 아래 "현재 상태"를 있는 그대로 표시합니다.

## 한 줄 소개

한국회계학회지에 게재된 연구논문(최아리·고민서·박신화·이규진·현정훈, 2026)이 제안한 「PRS(주가수익스와프) 통합 공시 지침」을, 논문 원문과 항목 단위로 추적 가능한 평가 루브릭 그리고 재사용 가능한 다중 에이전트 개발 체계로 구조화하는 프로젝트입니다.

## 🖥️ 지금 바로 실행해보기 (웹 애플리케이션)

### 🔗 공개 링크: **[prstiapp-xhvlnxkiyczgg46bluu7qu.streamlit.app](https://prstiapp-xhvlnxkiyczgg46bluu7qu.streamlit.app/)**

클릭 한 번으로 바로 써볼 수 있습니다. 기업명을 입력하면 실제 DART 공시를 조회해서, 논문이 제안한 기준으로 자동 채점한 결과를 보여줍니다. Claude API·`anthropic` 패키지는 전혀 필요 없습니다 — 규칙 기반(정규식·키워드) 엔진이라 무료로 동작합니다.

**사용 예시**: 기업명 "한화솔루션", 조회 기간 2025-01-01~2025-12-31을 입력하면 총점 30.75/100(잠정치)과 함께, 필수-03(만기일)·필수-10(셀다운) 항목이 실제 공시 원문 근거와 함께 자동으로 2점 판정되는 것을 볼 수 있습니다.

### 로컬에서 직접 실행하고 싶다면

```bash
git clone https://github.com/myth-PARK/prsti_hub.git
cd prsti_hub
pip install -r requirements.txt
export DART_API_KEY=본인이_발급받은_키   # https://opendart.fss.or.kr 에서 무료 발급
streamlit run webapp/app.py
```

실행하면 터미널에 `Local URL: http://localhost:8501`이 뜹니다 — 그 주소를 브라우저로 열면 됩니다. 내부 구조는 [`webapp/app.py`](webapp/app.py)·[`webapp/report_view.py`](webapp/report_view.py)·[`rule_based_extractor/`](rule_based_extractor/)를 참고하세요.

## 배경

국내 PRS 계약 규모는 2022년 약 992억 원에서 2025년 9월 10조 8,598억 원으로 급증했지만, 기업마다 공시 항목·명칭·상세도가 달라 투자자가 거래의 경제적 실질(부채성 여부, 잠재적 현금유출)을 비교하기 어렵습니다. 기반 논문은 10개 기업의 실제 PRS 공시를 심층 분석해 이 문제를 실증했고, 필수 12·조건부필수 3·권장 4개 항목으로 구성된 통합 공시 지침을 제안했습니다.

이 저장소는 그 지침을 실제로 채점 가능한 시스템으로 옮기는 작업입니다.

## 이 프로젝트의 원칙

- **AI와 점수 계산을 분리**한다. AI는 근거 후보를 추출·제안할 뿐, 최종 점수는 사람이 검토한 값만으로 결정론적으로 계산한다.
- **근거 없는 항목을 만들지 않는다.** 모든 루브릭 항목은 논문 원문의 표·문장으로 추적 가능해야 한다.
- **구현 사실과 계획을 구분한다.** `[구현완료]` `[설계완료·미구현]` `[계획단계]` 태그를 일관되게 사용한다.
- **의사결정과 그 이유를 기록한다.** `docs/decision-log.md`에 모든 주요 판단과 대안·근거·결정 주체를 남긴다.

## 현재 상태 (2026-07-21 기준)

| 구성요소 | 상태 |
|---|---|
| 논문 → 루브릭 19개 항목 추적성 매핑 | 완료 (19/19, 100%) |
| 다중 에이전트 하네스(에이전트 5개·스킬 6개) | 설계 완료 |
| 루브릭(`rubric/rubric.yaml`) | 승인(v1.0) — 항목 구조·N/A 규칙·근거 인정기준·배점(잠정) 전부 확정 |
| 점수 계산 엔진(`scoring_engine`) | 구현 완료·실행 검증됨(API 미사용) |
| DART 공시 수집(`dart_researcher`) | 구현 완료·실 데이터 검증됨(무료) |
| 규칙 기반 자동 채점(`rule_based_extractor`) | 구현 완료·실행 검증됨(Claude API 미사용, 임의 기업 입력 지원 — DEC-017) |
| AI 근거 추출(`evidence_extractor`, 선택적 비교 실험용) | 코드 구현 완료·라이브 미검증(`ALLOW_PAID_API=false`가 기본값, DEC-013) |
| 웹 애플리케이션(`webapp/`, Streamlit) | 구현 완료·**공개 배포됨** — [prstiapp-xhvlnxkiyczgg46bluu7qu.streamlit.app](https://prstiapp-xhvlnxkiyczgg46bluu7qu.streamlit.app/), 기업명·기간 입력 → DART 조회 → 자동 채점 요약 화면 |

## 저장소 구조

```
PRSTI/
├── .claude/
│   ├── agents/        # 전문 에이전트 5개 + portfolio-curator
│   └── skills/         # 에이전트가 따르는 절차 스킬 6개
├── docs/
│   ├── scoring-methodology.md      # 19개 항목 판정기준 + 논문 근거
│   ├── decision-log.md             # 주요 의사결정 기록
│   ├── development-log.md          # 작업 원본 로그
│   ├── troubleshooting-log.md      # 문제 해결 과정
│   ├── portfolio-evidence.md       # 포트폴리오/자기소개서 근거
│   └── progress-report-2026-07-20.md
├── rubric/
│   ├── rubric.yaml         # 사람이 승인한 채점 기준(배점·N/A 규칙 등)
│   └── rubric_rules.yaml   # 기계가 읽는 규칙(키워드·정규식·rule_status)
├── prsti_common/        # rubric 로더 등 공용 모듈
├── scoring_engine/      # 결정론적 점수 계산(API 미사용)
├── dart_researcher/     # DART Open API 조회 + 키워드 탐지(무료)
├── rule_based_extractor/  # 규칙 기반 자동 채점 파이프라인(API 미사용)
├── evidence_extractor/  # AI 근거 추출(선택적 비교 실험용, 기본 비활성)
├── webapp/              # 로컬 웹 애플리케이션(Streamlit)
├── tests/               # 자동 테스트 60개
├── _workspace/
│   └── rubric_gaps.md  # 사용자 결정이 필요한 쟁점 기록(현재 전부 해결됨)
└── 논문 원문·기획초안 (참고자료)
```

## 참고

- 논문: 최아리·고민서·박신화·이규진·현정훈. (2026). 「주가수익스와프(PRS)의 공시 투명성 제고 방안」. 한국회계학회지, 35(3), 241-280.
- 지표 설계 시 삼일PwC·전자신문의 ARIX(AI Readiness Index)를 상위 설계 원칙(다영역 진단 → 정량·정성 평가 → 개선 로드맵)의 벤치마크로 참고했으며, 비공개 세부 평가기준은 추정하지 않았습니다.
