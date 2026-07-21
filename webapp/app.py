"""PRSTI 웹 애플리케이션 (Streamlit).

임의의 상장기업명을 입력하면 DART 공시를 실시간 조회해 규칙 기반(rule_based_extractor)
으로 자동 채점한다. 생성형 AI를 호출하지 않는 결정론적 규칙 엔진이라 DART_API_KEY만
있으면 되고, ANTHROPIC_API_KEY나 anthropic 패키지는 전혀 필요 없다(DEC-013·DEC-014).
기준기업을 미리 정해두지 않고 어떤 기업이든 조회할 수 있는 것이 제품의 핵심 목적이다
(DEC-017).

화면(이 파일)과 로직(report_view.py)을 분리했다 — 디자인을 바꿔도 채점 엔진 코드는
건드리지 않는다.

실행:
    streamlit run webapp/app.py
"""

from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path

# `streamlit run webapp/app.py`는 이 스크립트가 있는 webapp/ 폴더만 sys.path에 넣고
# 저장소 루트는 넣지 않는다 — 그래서 `pip install -e .`나 `python -m` 없이 그냥
# 실행하면 webapp(자기 자신)도, rule_based_extractor/dart_researcher 같은 형제
# 패키지도 못 찾는다. 저장소 루트를 직접 sys.path에 넣어 어디서 실행하든 동작하게 한다.
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import streamlit as st

from webapp.report_view import build_summary, run_scoring

st.set_page_config(page_title="PRSTI — PRS 공시 투명성 지수", page_icon="📊", layout="centered")

st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .prsti-subtitle {
        color: #4B5563;
        font-size: 1.02rem;
        line-height: 1.6;
        margin: 0.3rem 0 0.9rem 0;
    }
    .prsti-badge {
        display: inline-block;
        padding: 0.3rem 0.85rem;
        margin: 0 0.35rem 0.4rem 0;
        border-radius: 999px;
        font-size: 0.82rem;
        font-weight: 600;
        background-color: #EAF1FB;
        color: #14213D;
        border: 1px solid #C7D7EE;
    }
    .prsti-steps {
        color: #6B7280;
        font-size: 0.85rem;
        margin-top: 0.6rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("📊 PRSTI — PRS Transparency Intelligence")
st.markdown(
    '<div class="prsti-subtitle">'
    "기업의 주가수익스와프(PRS) 공시를 분석해 19개 항목의 투명성 점수와 원문 근거를 "
    "자동으로 제공하는 분석 도구입니다.<br>"
    "「주가수익스와프(PRS)의 공시 투명성 제고 방안」(한국회계학회지, 2026) 연구를 코드로 구현했습니다."
    "</div>",
    unsafe_allow_html=True,
)
st.markdown(
    '<span class="prsti-badge">✅ 실제 DART 연동</span>'
    '<span class="prsti-badge">⚙️ 규칙 기반 자동 채점</span>'
    '<span class="prsti-badge">🔗 근거 추적 가능</span>',
    unsafe_allow_html=True,
)

st.write("")

with st.container(border=True):
    st.markdown("#### 기업 분석")

    company_name = st.text_input("기업명", placeholder="DART 등록명 그대로 입력 (예: 한화솔루션)")

    today = date.today()
    preset = st.radio("조회 기간", ["최근 1년", "최근 3년", "직접 설정"], horizontal=True)

    if preset == "최근 1년":
        bgn_date, end_date = today - timedelta(days=365), today
        st.caption(f"조회 기간: {bgn_date.isoformat()} ~ {end_date.isoformat()}")
    elif preset == "최근 3년":
        bgn_date, end_date = today - timedelta(days=365 * 3), today
        st.caption(f"조회 기간: {bgn_date.isoformat()} ~ {end_date.isoformat()}")
    else:
        col1, col2 = st.columns(2)
        with col1:
            bgn_date = st.date_input("시작일", value=today - timedelta(days=365))
        with col2:
            end_date = st.date_input("종료일", value=today)

    st.caption("⏱️ DART 조회부터 채점까지 보통 10~30초 정도 걸립니다.")
    submitted = st.button("🔍 PRSTI 분석 시작", type="primary", width="stretch")

st.markdown(
    '<div class="prsti-steps">분석 절차: DART 조회 → 근거 탐색 → 19개 항목 판정 → 결과 시각화</div>',
    unsafe_allow_html=True,
)

if submitted:
    if not company_name.strip():
        st.error("기업명을 입력하세요.")
    elif bgn_date > end_date:
        st.error("시작일이 종료일보다 늦습니다.")
    else:
        with st.spinner(f"{company_name} DART 공시 조회 및 채점 중..."):
            outcome = run_scoring(
                company_name=company_name.strip(),
                bgn_de=bgn_date.strftime("%Y%m%d"),
                end_de=end_date.strftime("%Y%m%d"),
            )

        if outcome.error:
            st.error(outcome.error)
        else:
            summary = build_summary(outcome.report)

            if summary["no_evidence_found"]:
                st.warning(
                    "지정한 기간에서 PRS 관련 공시 후보를 찾지 못했습니다. "
                    "아래 점수는 전부 근거 없음(0점)으로 처리된 것이며, 실제로 PRS 계약이 없다는 "
                    "뜻은 아닙니다 — 조회 기간을 넓혀서 다시 시도해보세요."
                )

            st.divider()
            st.markdown(f"#### {summary['company']} 분석 결과")

            col_a, col_b = st.columns(2)
            with col_a:
                st.metric(
                    "총점", f"{summary['total_score']} / {summary['max_score']}점", border=True
                )
            with col_b:
                st.metric(
                    "권장항목 충족", f"{summary['recommended_met']}/{summary['recommended_total']}", border=True
                )
            st.caption(f"총점 비율: {summary['percent']}%")

            st.write("🟡 **잠정치** (일부 항목 근거 불충분)" if summary["is_provisional"] else "🟢 **확정**")

            st.markdown("###### 영역별 점수")
            for area in summary["areas"]:
                percent = min(area["percent"] / 100, 1.0)
                st.progress(
                    percent,
                    text=(
                        f"{area['area_id']}. {area['area_name']} — "
                        f"{area['earned']}/{area['max_possible']}점 ({area['percent']}%)"
                    ),
                )

            st.caption(
                f"검토된 공시 후보 {summary['candidates_considered']}건 중 "
                f"{summary['candidates_excluded']}건은 어떤 항목에도 채택되지 않음. "
                f"사람의 재검토를 권고하는 항목 {summary['review_needed_count']}개."
            )

            st.info(
                "이 점수는 결정론적 규칙 엔진의 자동 산출 결과입니다. 근거가 불충분한 항목은 "
                "임의로 점수를 올리지 않고 항상 0점으로 보수적으로 처리됩니다 — '정확도가 "
                "검증됐다'는 뜻은 아닙니다(docs/portfolio-evidence.md 한계 참고)."
            )
