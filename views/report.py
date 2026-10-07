import streamlit as st

from risksim.engine import headline
from risksim.project import blocking, validate
from risksim.report import board_report, excel_report
from risksim.ui import answer, project

p = project()
st.title("Report & export")
if blocking(validate(p)):
    st.error("Fix the issues on the Tasks or Risk register page first.")
    st.stop()
a = answer(p)
st.markdown("<p class='note'>Three outputs: a one-page board report for the sponsor, the full analysis in Excel for the "
            "PMO, and the project file to reopen later.</p>", unsafe_allow_html=True)
author = st.text_input("Prepared by (optional)")


@st.cache_data(show_spinner="Writing the report…")
def files(fp: str, author: str):
    return board_report(a, author), excel_report(a)


docx, xlsx = files(p.fingerprint(), author)
safe = p.name.replace(" ", "_")
c = st.columns(3)
c[0].download_button("📄 One-page board report (Word)", docx, f"{safe}_board_report.docx", type="primary", use_container_width=True,
                     mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
c[1].download_button("📊 Full analysis (Excel)", xlsx, f"{safe}_analysis.xlsx", use_container_width=True,
                     mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
c[2].download_button("💾 Project file (.json)", p.to_json(), f"{safe}.json", "application/json", use_container_width=True)

st.markdown("##### What the board report says")
with st.container(border=True):
    st.markdown(headline(a))
