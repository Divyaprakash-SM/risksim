import streamlit as st

from risksim.project import Project, blank, from_excel
from risksim.ui import SAMPLE, project, set_project

p = project()
st.title("RiskSim")
st.markdown("#### Know your budget and delivery date confidence *before* you commit to them.")
st.markdown("<p class='note'>Most project budgets and dates are single numbers that quietly assume nothing goes wrong. "
            "RiskSim simulates your project thousands of times, with estimating uncertainty, named risks and task "
            "dependencies, and tells you what to budget, what date to promise, and which risks are worth paying "
            "to reduce. No spreadsheets of formulas, no training course.</p>", unsafe_allow_html=True)

c = st.columns(3)
steps = [("1", "List your tasks", "Cost and duration as a best guess plus a low and high. Say which tasks depend on which."),
         ("2", "Add your risks", "What could happen, how likely it is, and what it would cost in money and days."),
         ("3", "Get the answer", "The budget and date for your chosen confidence, the odds of the current plan, and where the risk sits.")]
for col, (n, title, body) in zip(c, steps):
    col.markdown(f"<div class='step'><b class='num'>{n}</b><b>{title}</b><p class='note' style='margin-top:8px'>{body}</p></div>",
                 unsafe_allow_html=True)

st.subheader("Start")
c = st.columns(4)
if c[0].button("Explore the sample project", use_container_width=True, type="primary"):
    set_project(Project.from_json(SAMPLE.read_text()))
    st.switch_page("views/results.py")
if c[1].button("Start a blank project", use_container_width=True):
    set_project(blank())
    st.switch_page("views/build.py")
with c[2].popover("Import from Excel", use_container_width=True):
    st.caption("Any WBS sheet with Task and Cost columns. Durations, dependencies and a 'Risk Register' sheet are optional.")
    xl = st.file_uploader("Excel or CSV", type=["xlsx", "xls", "csv"], label_visibility="collapsed")
    if xl is not None and st.button("Import", type="primary"):
        import tempfile
        from pathlib import Path
        tmp = Path(tempfile.mkdtemp()) / xl.name
        tmp.write_bytes(xl.getvalue())
        try:
            set_project(from_excel(tmp))
            st.switch_page("views/build.py")
        except Exception as e:
            st.error(f"Couldn't import that file: {e}")
with c[3].popover("Open a saved project", use_container_width=True):
    js = st.file_uploader("RiskSim .json", type="json", label_visibility="collapsed")
    if js is not None and st.button("Open", type="primary"):
        try:
            set_project(Project.from_json(js.getvalue().decode()))
            st.switch_page("views/results.py")
        except Exception as e:
            st.error(f"Couldn't open that file: {e}")

st.divider()
st.markdown("**Who it's for:** project managers, PMO analysts and bid teams who need a defensible contingency and date "
            "but don't have a specialist risk tool or analyst. **What it replaces:** the single-point estimate and the "
            "'add 10% contingency' rule of thumb.")
st.caption("Built on an open-source Monte Carlo engine that grew out of an MSc dissertation with a UK engineering firm. "
           "Methods: three-point estimates (Beta-PERT), risk events with probability and impact, critical path on every run, "
           "joint cost-and-schedule confidence.")
