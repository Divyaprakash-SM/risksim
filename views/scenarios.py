import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from risksim.engine import compare
from risksim.project import Project, blocking, validate
from risksim.ui import SCEN_COLOURS, money, project, set_project, style

p = project()
cur = p.currency
ss = st.session_state
st.title("Scenarios")
st.markdown("<p class='note'>Save the current version of the project as a scenario, change something (cut a risk's "
            "chance, add a task, fast-track a dependency), save again, and compare. This is how you show a sponsor "
            "what a risk response or a scope change is worth.</p>", unsafe_allow_html=True)

c = st.columns([2, 1])
name = c[0].text_input("Scenario name", f"Scenario {len(ss.scenarios) + 1}" if ss.scenarios else "Baseline")
if c[1].button("Save current project as scenario", type="primary", use_container_width=True,
               disabled=blocking(validate(p))):
    ss.scenarios[name] = p.to_json()
    st.toast(f"Saved '{name}'")
    st.rerun()

if not ss.scenarios:
    st.info("No scenarios yet. Save the current project as **Baseline** to start.")
    if st.button("Load a ready-made example: baseline vs mitigating the two biggest risks"):
        base = Project.from_json(p.to_json())
        mit = Project.from_json(p.to_json())
        rr = mit.risks
        top = rr.assign(score=pd.to_numeric(rr["Probability %"]) * pd.to_numeric(rr["Cost likely"])).nlargest(2, "score").index
        rr.loc[top, "Probability %"] = rr.loc[top, "Probability %"] / 4
        ss.scenarios = {"Baseline": base.to_json(), "Mitigate top 2 risks (chance ÷ 4)": mit.to_json()}
        st.rerun()
    st.stop()

st.markdown("##### Saved scenarios")
for nm in list(ss.scenarios):
    c = st.columns([4, 1, 1])
    c[0].markdown(f"**{nm}**")
    if c[1].button("Load into editor", key=f"load_{nm}", use_container_width=True):
        set_project(Project.from_json(ss.scenarios[nm]))
        st.toast(f"Loaded '{nm}'. Edit it on the Tasks or Risk register page.")
    if c[2].button("Delete", key=f"del_{nm}", use_container_width=True):
        del ss.scenarios[nm]
        st.rerun()


@st.cache_data(show_spinner="Comparing scenarios…")
def run_compare(items: tuple):
    return compare({k: Project.from_json(v) for k, v in items})


cmp = run_compare(tuple(ss.scenarios.items()))
conf = int(p.options.confidence * 100)
show = cmp.drop(columns=[c for c in cmp.columns if c.startswith("_")]).copy()
base = show.iloc[0]
st.markdown("##### Comparison")
st.dataframe(show, hide_index=True, use_container_width=True,
             column_config={c: st.column_config.NumberColumn(format=f"{cur}%,.0f") for c in
                            ["Base estimate", "P50 cost", f"P{conf} budget", "Contingency"]}
             | {"Chance of plan date": st.column_config.NumberColumn(format="percent"),
                "Joint confidence": st.column_config.NumberColumn(format="percent"),
                "P50 finish": st.column_config.DateColumn(format="DD MMM YYYY"),
                f"P{conf} finish": st.column_config.DateColumn(format="DD MMM YYYY")})
if len(show) > 1:
    for _, r in show.iloc[1:].iterrows():
        d_cost = r[f"P{conf} budget"] - base[f"P{conf} budget"]
        msg = f"**{r['Scenario']}** vs **{base['Scenario']}**: P{conf} budget {money(d_cost, cur)}"
        if pd.notna(r[f"P{conf} finish"]) and pd.notna(base[f"P{conf} finish"]):
            dd = np.busday_count(pd.Timestamp(base[f"P{conf} finish"]).date(), pd.Timestamp(r[f"P{conf} finish"]).date())
            msg += f", P{conf} finish {dd:+d} working days"
        st.markdown("- " + msg + ".")

l, r = st.columns(2)
with l:
    fig = go.Figure()
    for i, row in cmp.iterrows():
        xs = np.sort(row["_cost"])[::10]
        fig.add_trace(go.Scatter(x=xs, y=np.linspace(0, 1, len(xs)), name=row["Scenario"], mode="lines",
                                 line=dict(color=SCEN_COLOURS[i % len(SCEN_COLOURS)], width=2.5)))
    fig.add_hline(y=p.options.confidence, line=dict(color="#9a9993", dash="dash", width=1))
    style(fig, 380, title=dict(text="Cost confidence by scenario", font=dict(size=15)))
    fig.update_xaxes(tickprefix=cur, tickformat=",.0f"); fig.update_yaxes(tickformat=".0%")
    st.plotly_chart(fig, use_container_width=True)
with r:
    if cmp["_days"].notna().all():
        fig = go.Figure()
        for i, row in cmp.iterrows():
            ds = np.sort(row["_days"])[::10]
            fig.add_trace(go.Scatter(x=ds, y=np.linspace(0, 1, len(ds)), name=row["Scenario"], mode="lines",
                                     line=dict(color=SCEN_COLOURS[i % len(SCEN_COLOURS)], width=2.5)))
        fig.add_hline(y=p.options.confidence, line=dict(color="#9a9993", dash="dash", width=1))
        style(fig, 380, title=dict(text="Schedule confidence by scenario (working days)", font=dict(size=15)))
        fig.update_yaxes(tickformat=".0%")
        st.plotly_chart(fig, use_container_width=True)
