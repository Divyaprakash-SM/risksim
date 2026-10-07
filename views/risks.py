import plotly.graph_objects as go
import streamlit as st

from risksim.project import NUMERIC_RISK, RISK_COLUMNS, validate
from risksim.ui import BLUE, MUTED, ORANGE, project, style, table_editor

p = project()
cur = p.currency
st.title("Risk register")
st.markdown("<p class='note'>Named risks are things that <i>might</i> happen. Each one either happens or doesn't in each "
            "simulation, according to its probability. If it happens it adds cost, and adds delay to the task it affects "
            "(which only moves the end date if that task is on the critical path).</p>", unsafe_allow_html=True)

cfg = {
    "ID": st.column_config.TextColumn("ID", width="small"),
    "Risk": st.column_config.TextColumn("Risk", width="large", required=True),
    "Owner": st.column_config.TextColumn("Owner"),
    "Probability %": st.column_config.NumberColumn("Chance %", min_value=0, max_value=100),
    "Cost low": st.column_config.NumberColumn(f"Cost low ({cur})", min_value=0, format="%d"),
    "Cost likely": st.column_config.NumberColumn("Cost likely", min_value=0, format="%d"),
    "Cost high": st.column_config.NumberColumn("Cost high", min_value=0, format="%d"),
    "Delay low": st.column_config.NumberColumn("Delay low (days)", min_value=0),
    "Delay likely": st.column_config.NumberColumn("Delay likely", min_value=0),
    "Delay high": st.column_config.NumberColumn("Delay high", min_value=0),
    "Affects task": st.column_config.TextColumn("Affects task", help="Code of the task the delay lands on. Blank = cost only."),
    "Response": st.column_config.TextColumn("Planned response", width="medium"),
}
table_editor("risks", RISK_COLUMNS, NUMERIC_RISK, cfg, height=330)
st.caption("Tip: to test a mitigation, save the current version as a scenario, lower the chance or impact here, "
           "and compare the two on the Scenarios page.")

r = p.engine_risks()
if r is not None:
    r = r.assign(ev=r["Probability"] * (r["Cost Min"] + 4 * r["Cost ML"] + r["Cost Max"]) / 6,
                 ed=r["Probability"] * (r["Days Min"] + 4 * r["Days ML"] + r["Days Max"]) / 6)
    fig = go.Figure(go.Scatter(x=r["Probability"], y=r["Cost ML"], mode="markers+text", text=r["Risk ID"],
                               textposition="top center", marker=dict(size=10 + r["Days ML"].clip(0, 40), color=ORANGE,
                                                                       opacity=.75, line=dict(color="white", width=2)),
                               customdata=r[["Risk", "ev", "Days ML"]],
                               hovertemplate="%{customdata[0]}<br>Chance %{x:.0%} · likely cost " + cur +
                                             "%{y:,.0f} · %{customdata[2]:.0f} days<br>Expected cost " + cur +
                                             "%{customdata[1]:,.0f}<extra></extra>"))
    style(fig, 360, title=dict(text="Risk map: chance vs likely cost (bubble size = likely delay)", font=dict(size=15)))
    fig.update_xaxes(tickformat=".0%", range=[0, max(0.6, r["Probability"].max() * 1.15)], title="Chance")
    fig.update_yaxes(tickprefix=cur, tickformat=",.0f", title="Likely cost if it happens",
                     range=[0, r["Cost ML"].max() * 1.25 + 1])
    st.plotly_chart(fig, use_container_width=True)
    st.caption("This is the classic probability-impact view. The Results page goes further: it measures how much each "
               "risk actually moves your P80 budget and date, which is the better guide to where mitigation pays.")

for level, msg in [i for i in validate(p) if i[1].startswith("Risk")]:
    (st.error if level == "error" else st.warning)(msg)
