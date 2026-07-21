"""PRSTI 로컬 웹 애플리케이션 (Streamlit).

임의의 상장기업명을 입력하면 DART 공시를 실시간 조회해 규칙 기반(rule_based_extractor)
으로 자동 채점한다. 생성형 AI를 호출하지 않는 결정론적 규칙 엔진이라 DART_API_KEY만
있으면 되고, ANTHROPIC_API_KEY나 anthropic 패키지는 전혀 필요 없다(DEC-013·DEC-014).
기준기업을 미리 정해두지 않고 어떤 기업이든 조회할 수 있는 것이 제품의 핵심 목적이다
(DEC-017).

실행:
    streamlit run webapp/app.py
"""

from __future__ import annotations

import sys
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

st.set_page_config(page_title="PRSTI — PRS 공시 투명성 지수", page_icon="📊")

st.title("PRSTI — PRS 공시 투명성 지수")
st.caption(
    "임의의 상장기업명을 입력하면 DART 공시를 조회해 규칙 기반으로 자동 채점합니다. "
    "생성형 AI를 호출하지 않는 결정론적 규칙 엔진입니다."
)

with st.form("score_form"):
    company_name = st.text_input("기업명 (DART 등록명 그대로, 예: 한화솔루션)")
    col1, col2 = st.columns(2)
    with col1:
        bgn_date = st.date_input("조회 시작일")
    with col2:
        end_date = st.date_input("조회 종료일")
    submitted = st.form_submit_button("조회 및 채점 실행")

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

            st.metric(f"{summary['company']} 총점", f"{summary['total_score']} / {summary['max_score']}점")
            st.caption(f"{summary['percent']}%")

            col_a, col_b = st.columns(2)
            with col_a:
                st.write(
                    "**잠정치 여부**:",
                    "잠정치 (일부 항목 근거 불충분)" if summary["is_provisional"] else "확정",
                )
            with col_b:
                st.write("**권장항목 충족**:", f"{summary['recommended_met']}/{summary['recommended_total']}")

            st.subheader("영역별 점수")
            st.dataframe(
                [
                    {
                        "영역": f"{a['area_id']}. {a['area_name']}",
                        "획득": a["earned"],
                        "만점": a["max_possible"],
                        "비율(%)": a["percent"],
                    }
                    for a in summary["areas"]
                ],
                hide_index=True,
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
