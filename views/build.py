import pandas as pd
import streamlit as st

from risksim.project import NUMERIC_TASK, TASK_COLUMNS, validate
from risksim.ui import project, table_editor

p = project()
st.title("Tasks & schedule")
st.markdown("<p class='note'>One row per task. <b>Cost</b> and <b>Days</b> are your best guess; the low and high columns are "
            "the realistic range (leave them blank to use the defaults below). <b>Depends on</b> lists the task codes "
            "that must finish first, separated by commas.</p>", unsafe_allow_html=True)

c = st.columns([2, 1, 1, 1])
p.name = c[0].text_input("Project name", p.name)
p.start_date = str(c[1].date_input("Start date", pd.Timestamp(p.start_date)))
p.currency = c[2].text_input("Currency symbol", p.currency, max_chars=3)
p.options.confidence = c[3].select_slider("Plan to confidence", [0.5, 0.7, 0.8, 0.9], p.options.confidence,
                                          format_func=lambda v: f"P{int(v * 100)}",
                                          help="P80 = 8 in 10 simulated projects come in under the budget and date. Most organisations plan to P80.")

cur = p.currency
cfg = {
    "Phase": st.column_config.TextColumn("Phase", help="Groups tasks for the milestone view, e.g. Design, Build, Test"),
    "Code": st.column_config.TextColumn("Code", help="Short unique ID, e.g. 1.2. Used in 'Depends on'."),
    "Task": st.column_config.TextColumn("Task", width="medium", required=True),
    "Cost": st.column_config.NumberColumn(f"Cost ({cur})", min_value=0, format="%d", help="Most likely cost"),
    "Cost low": st.column_config.NumberColumn("Cost low", min_value=0, format="%d"),
    "Cost high": st.column_config.NumberColumn("Cost high", min_value=0, format="%d"),
    "Days": st.column_config.NumberColumn("Days", min_value=0, help="Most likely working days"),
    "Days low": st.column_config.NumberColumn("Days low", min_value=0),
    "Days high": st.column_config.NumberColumn("Days high", min_value=0),
    "Depends on": st.column_config.TextColumn("Depends on", help="Codes of tasks that must finish first, e.g. 1.1, 1.3"),
    "Time-dependent %": st.column_config.NumberColumn("Time-dep. %", min_value=0, max_value=100,
                                                      help="Share of the cost paid by the day (people, equipment). If the task runs long, this part costs more."),
}
table_editor("tasks", TASK_COLUMNS, NUMERIC_TASK, cfg, height=460)

with st.expander("Default ranges, used when a task has no low/high of its own"):
    c = st.columns(5)
    o = p.options
    o.cost_low_factor = c[0].number_input("Cost low (× best guess)", 0.5, 1.0, o.cost_low_factor, 0.05)
    o.cost_high_factor = c[1].number_input("Cost high (×)", 1.0, 3.0, o.cost_high_factor, 0.05)
    o.days_low_factor = c[2].number_input("Days low (×)", 0.5, 1.0, o.days_low_factor, 0.05)
    o.days_high_factor = c[3].number_input("Days high (×)", 1.0, 3.0, o.days_high_factor, 0.05)
    o.time_dependent = c[4].number_input("Time-dependent % (default)", 0.0, 100.0, float(o.time_dependent), 5.0)
    st.caption("Days default to a wider, more lopsided range than cost: in practice tasks overrun in time more than they underrun.")

issues = validate(p)
st.subheader("Checks")
if not issues:
    st.success("Everything looks consistent. Head to **Risk register** or straight to **Results**.")
for level, msg in issues:
    (st.error if level == "error" else st.warning)(msg)
t = p.engine_tasks()
c = st.columns(3)
c[0].metric("Tasks", len(t))
c[1].metric("Base estimate", f"{cur}{t['Cost'].sum():,.0f}" if t["Cost"].notna().any() else "–")
c[2].metric("Tasks with their own cost range", f"{int((t['Optimistic'].notna() | t['Pessimistic'].notna()).sum())} of {len(t)}")
