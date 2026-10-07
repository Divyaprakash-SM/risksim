"""RiskSim: know your budget and date confidence before you commit.

Run locally:  streamlit run app.py
"""

import streamlit as st

from risksim.project import blocking, validate
from risksim.ui import CSS, project

st.set_page_config(page_title="RiskSim", page_icon="🎯", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)
p = project()

pages = st.navigation([
    st.Page("views/home.py", title="Start", icon="🏠", default=True),
    st.Page("views/build.py", title="1 · Tasks & schedule", icon="🧱"),
    st.Page("views/risks.py", title="2 · Risk register", icon="⚠️"),
    st.Page("views/results.py", title="3 · Results", icon="🎯"),
    st.Page("views/scenarios.py", title="Scenarios", icon="🔀"),
    st.Page("views/report.py", title="Report & export", icon="📄"),
])

with st.sidebar:
    st.markdown(f"**Current project**  \n{p.name}")
    issues = validate(p)
    n_tasks = int(p.engine_tasks().shape[0])
    n_risks = 0 if p.engine_risks() is None else len(p.engine_risks())
    st.caption(f"{n_tasks} tasks · {n_risks} risks · {len(st.session_state.scenarios)} saved scenarios")
    if blocking(issues):
        st.error(f"{sum(1 for l, _ in issues if l == 'error')} issue(s) to fix before results")
    st.download_button("💾 Save project (.json)", p.to_json(), f"{p.name.replace(' ', '_')}.json", "application/json",
                       use_container_width=True)
    st.caption("RiskSim runs in your browser session: nothing is stored on a server. Save the file to keep your work.")

pages.run()
