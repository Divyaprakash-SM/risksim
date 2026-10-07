import numpy as np
import plotly.graph_objects as go
import streamlit as st

from montecarlo import jcl, jcl_grid, schedule_sensitivity
from risksim.engine import drivers, headline
from risksim.project import blocking, validate
from risksim.ui import BLUE, GREEN, INK, MUTED, ORANGE, answer, money, project, style

p = project()
cur = p.currency
st.title(f"Results: {p.name}")
issues = validate(p)
if blocking(issues):
    st.error("Fix these first (on the Tasks or Risk register page):")
    for level, msg in issues:
        if level == "error":
            st.markdown(f"- {msg}")
    st.stop()

a = answer(p)
conf = int(p.options.confidence * 100)
import re

st.markdown(f"<div class='answer'>{re.sub(r'[*][*](.+?)[*][*]', r'<b>\1</b>', headline(a))}</div>", unsafe_allow_html=True)

c = st.columns(5 if a.date is not None else 3)
c[0].metric("Base estimate", money(a.base_cost, cur), help="The plain sum of task costs. No uncertainty, no risk.")
c[1].metric(f"P{conf} budget", money(a.budget, cur), f"+{money(a.contingency, cur)} contingency", delta_color="off", delta_arrow="off")
c[2].metric("Chance base estimate is enough", f"{a.chance_base_enough:.0%}")
if a.date is not None:
    c[3].metric(f"P{conf} finish", f"{a.date:%d %b %Y}", f"plan {a.plan_date:%d %b}", delta_color="off", delta_arrow="off")
    c[4].metric("Budget AND date together", f"{a.joint:.0%}", help="Joint confidence: the chance of meeting both at once.")

tabs = st.tabs(["Budget", "Timeline", "Budget + date together", "Risks & contingency"])
res = a.res
with tabs[0]:
    l, r = st.columns([1.4, 1])
    with l:
        xs = np.sort(res.total_cost)[:: max(1, len(res.total_cost) // 600)]
        fig = go.Figure(go.Scatter(x=xs, y=np.linspace(0, 1, len(xs)), mode="lines", line=dict(color=BLUE, width=2.5),
                                   hovertemplate=f"%{{y:.0%}} chance cost ≤ {cur}%{{x:,.0f}}<extra></extra>"))
        fig.add_vline(x=a.base_cost, line=dict(color=INK, width=1, dash="dot"))
        fig.add_annotation(x=a.base_cost, y=0.97, text="Base estimate", showarrow=False, xanchor="right", font=dict(size=11, color=MUTED))
        fig.add_trace(go.Scatter(x=[a.budget], y=[p.options.confidence], mode="markers+text", text=[f"  P{conf} {money(a.budget, cur)}"],
                                 textposition="middle right", marker=dict(size=11, color=BLUE, line=dict(color="white", width=2)),
                                 showlegend=False, hoverinfo="skip"))
        style(fig, 380, showlegend=False, title=dict(text="Chance the project costs this much or less", font=dict(size=15)))
        fig.update_xaxes(tickprefix=cur, tickformat=",.0f"); fig.update_yaxes(tickformat=".0%", range=[0, 1.03])
        st.plotly_chart(fig, use_container_width=True)
    with r:
        lv = [0.5, 0.7, 0.8, 0.9]
        st.markdown("##### Budget at each confidence level")
        st.dataframe({"Confidence": [f"P{int(x * 100)}" for x in lv],
                      "Budget": [money(float(np.quantile(res.total_cost, x)), cur) for x in lv],
                      "Contingency": [f"{(np.quantile(res.total_cost, x) - a.base_cost) / a.base_cost:+.0%}" for x in lv]},
                     hide_index=True, use_container_width=True)
        st.caption("Choose the confidence level on the Tasks page. P80 is the common choice; P90 suits fixed-price bids "
                   "where an overrun comes out of your margin.")

with tabs[1]:
    if res.schedule is None:
        st.info("Give every task **Days** (and **Depends on** where relevant) to get finish dates.")
    else:
        sr = res.schedule
        l, r = st.columns([1.4, 1])
        with l:
            days = np.sort(sr.project_days)[:: max(1, len(sr.project_days) // 600)]
            dates = [sr.finish_date(d) for d in days]
            fig = go.Figure(go.Scatter(x=dates, y=np.linspace(0, 1, len(dates)), mode="lines", line=dict(color=GREEN, width=2.5),
                                       hovertemplate="%{y:.0%} chance of finishing by %{x|%d %b %Y}<extra></extra>"))
            fig.add_vline(x=a.plan_date, line=dict(color=INK, width=1, dash="dot"))
            fig.add_annotation(x=a.plan_date, y=0.97, text=f"Plan {a.plan_date:%d %b}", showarrow=False, xanchor="right",
                               font=dict(size=11, color=MUTED))
            style(fig, 380, title=dict(text="Chance of finishing by each date", font=dict(size=15)))
            fig.update_yaxes(tickformat=".0%", range=[0, 1.03])
            st.plotly_chart(fig, use_container_width=True)
        with r:
            st.markdown(f"**Why the plan date is optimistic:** wherever parallel tasks join, the project waits for the "
                        f"slowest one, so uncertainty only ever pushes the date later. Your plan date of "
                        f"{a.plan_date:%d %b %Y} has a {a.chance_plan_date:.0%} chance; the P50 is {a.p50_date:%d %b} and "
                        f"the P{conf} is **{a.date:%d %b %Y}**.")
        ss = schedule_sensitivity(sr).sort_values(["Criticality index", "Cruciality"], ascending=False).head(10).iloc[::-1]
        fig = go.Figure(go.Bar(x=ss["Criticality index"], y=ss["Task"], orientation="h", marker=dict(color=GREEN, cornerradius=4),
                               text=[f"{v:.0%}" for v in ss["Criticality index"]], textposition="outside", cliponaxis=False,
                               hovertemplate="%{y}<br>On the critical path in %{x:.0%} of runs<extra></extra>"))
        style(fig, 380, title=dict(text="Tasks that control the end date (share of runs on the critical path)", font=dict(size=15)))
        fig.update_xaxes(tickformat=".0%", range=[0, 1.2])
        st.plotly_chart(fig, use_container_width=True)

with tabs[2]:
    if res.schedule is None:
        st.info("Joint confidence needs a schedule: add Days to every task.")
    else:
        sr = res.schedule
        c = st.columns(3)
        b_in = c[0].number_input(f"Budget ({cur})", value=float(round(a.budget, -2)), step=500.0)
        d_in = c[1].number_input("Working days", value=float(round(a.date_days)), step=1.0)
        c[2].metric("Chance of meeting both", f"{jcl(res, b_in, d_in):.0%}", f"finish {sr.finish_date(d_in):%d %b %Y}",
                    delta_color="off", delta_arrow="off")
        bx, dy, z = jcl_grid(res)
        fig = go.Figure(go.Contour(x=bx, y=dy, z=z, contours=dict(start=0.1, end=0.9, size=0.1, showlabels=True,
                                                                 labelfont=dict(size=11, color="white")),
                                   colorscale=[[0, "#f0efec"], [0.5, "#6da7ec"], [1, "#0d366b"]], showscale=False,
                                   hovertemplate=f"{cur}%{{x:,.0f}} · %{{y:.0f}} days<br>%{{z:.0%}} chance of both<extra></extra>"))
        fig.add_trace(go.Scatter(x=[b_in], y=[d_in], mode="markers", marker=dict(size=13, color=ORANGE, line=dict(color="white", width=2)),
                                 name="Your budget and date"))
        style(fig, 440, title=dict(text="Chance of meeting budget and date together, for every combination", font=dict(size=15)))
        fig.update_xaxes(tickprefix=cur, tickformat=",.0f", title="Budget"); fig.update_yaxes(title="Working days")
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Every point on a contour line is a budget-and-date pair with the same chance of meeting both. "
                   "Moving along a line trades money for time. NASA requires major projects to be planned at 70% joint confidence.")

with tabs[3]:
    dv = drivers(a)
    sp = dv["split"]
    l, r = st.columns([1, 1.2])
    with l:
        fig = go.Figure(go.Waterfall(x=["Base estimate", "Estimating uncertainty", "Named risks", f"P{conf} budget"],
                                     measure=["absolute", "relative", "relative", "total"],
                                     y=[sp["base_cost"], sp["estimate_uncertainty"], sp["risk_events"], 0],
                                     text=[money(v, cur) for v in (sp["base_cost"], sp["estimate_uncertainty"], sp["risk_events"], sp["total_budget"])],
                                     textposition="outside", cliponaxis=False, increasing=dict(marker=dict(color=ORANGE)),
                                     totals=dict(marker=dict(color=INK)), connector=dict(line=dict(color=MUTED, dash="dot", width=1))))
        style(fig, 380, showlegend=False, title=dict(text="Where the contingency comes from", font=dict(size=15)))
        fig.update_yaxes(tickprefix=cur, tickformat=",.0f", range=[sp["base_cost"] * 0.8, sp["total_budget"] * 1.07])
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Estimating uncertainty can only be narrowed with better estimates. The named-risk part is what "
                   "risk responses can buy down.")
    with r:
        rk = dv["risks"]
        if len(rk):
            cc = [c for c in rk.columns if c.endswith("cost saved if removed")][0]
            dc = [c for c in rk.columns if c.endswith("days saved if removed")]
            d = rk.iloc[::-1]
            fig = go.Figure(go.Bar(x=d[cc], y=d["Risk ID"] + " · " + d["Risk"].str.slice(0, 40), orientation="h",
                                   marker=dict(color=ORANGE, cornerradius=4),
                                   text=[f"{money(v, cur)}" + (f" · {dd:.0f}d" if dc else "") for v, dd in zip(d[cc], d[dc[0]] if dc else [0] * len(d))],
                                   textposition="outside", cliponaxis=False))
            style(fig, 380, title=dict(text=f"What removing each risk saves (P{conf} budget · days)", font=dict(size=15)))
            fig.update_xaxes(tickprefix=cur, tickformat=",.0f", range=[0, max(d[cc].max(), 1) * 1.45])
            st.plotly_chart(fig, use_container_width=True)
            st.caption("If a mitigation costs less than what it saves here (allowing for how much it reduces the risk), it pays for itself.")
        else:
            st.info("Add risks on the Risk register page to see which are worth mitigating.")
    st.markdown("##### Contingency by phase")
    st.dataframe(dv["allocation"], hide_index=True, use_container_width=True,
                 column_config={"Base estimate": st.column_config.NumberColumn(format=f"{cur}%,.0f"),
                                "Expected cost": st.column_config.NumberColumn(format=f"{cur}%,.0f"),
                                "Share of variance": st.column_config.NumberColumn(format="percent"),
                                "Contingency": st.column_config.NumberColumn(format=f"{cur}%,.0f"),
                                f"P{conf} budget": st.column_config.NumberColumn(format=f"{cur}%,.0f")})
    st.caption("Each phase holds its expected overrun plus its share of the spread; the parts add up exactly to the total.")
