"""Shared UI: theme, chart style, session state and an editable table that survives page changes."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from .engine import Answer, analyse
from .project import NUMERIC_RISK, NUMERIC_TASK, Project, _typed

ROOT = Path(__file__).resolve().parent.parent
SAMPLE = ROOT / "data" / "sample_project.json"
BLUE, GREEN, ORANGE, INK, MUTED, GRID = "#2a78d6", "#1baf7a", "#eb6834", "#0b0b0b", "#52514e", "#e6e5e0"
SCEN_COLOURS = ["#2a78d6", "#eb6834", "#1baf7a", "#4a3aa7", "#e87ba4", "#eda100"]

CSS = """<style>
  .block-container {padding-top: 2rem; max-width: 1300px;}
  [data-testid="stMetricValue"] {font-size: 1.6rem; font-weight: 650;}
  [data-testid="stMetricLabel"] p {font-size: .78rem; text-transform: uppercase; letter-spacing: .04em; color: #52514e;}
  .note {font-size:.95rem; color:#52514e;}
  .answer {border-left: 5px solid #1c5cab; background:#f3f2ee; padding: 16px 20px; border-radius: 6px; margin: 6px 0 18px; font-size:1.05rem; line-height:1.6;}
  .step {border:1px solid #e6e5e0; border-radius:10px; padding:16px 18px; background:#ffffff; height:100%;}
  .step b.num {display:inline-block; width:26px; height:26px; border-radius:50%; background:#1c5cab; color:#fff; text-align:center; line-height:26px; margin-right:8px;}
  h1 {font-weight: 700; letter-spacing: -.02em;}
</style>"""


def style(fig, height=360, **kw):
    top = 40
    if "title" in kw:
        kw["title"] = {**kw["title"], "x": 0.01, "xanchor": "left", "y": 0.985, "yanchor": "top"}
        top = 78
    fig.update_layout(template="plotly_white", height=height, margin=dict(l=10, r=10, t=top, b=10),
                      font=dict(family="Inter, Segoe UI, sans-serif", size=13, color=INK),
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, title=None),
                      hoverlabel=dict(bgcolor="white", font_size=12), **kw)
    fig.update_xaxes(showgrid=False, linecolor=GRID, tickfont=dict(color=MUTED))
    fig.update_yaxes(gridcolor=GRID, zeroline=False, tickfont=dict(color=MUTED))
    return fig


# ------------------------------------------------------------------ state
def project() -> Project:
    ss = st.session_state
    if "project" not in ss:
        ss.project = Project.from_json(SAMPLE.read_text())
        ss.scenarios = {}
    ss.setdefault("scenarios", {})
    ss.setdefault("editor_version", 0)
    return ss.project


def set_project(p: Project) -> None:
    st.session_state.project = p
    st.session_state.editor_version = st.session_state.get("editor_version", 0) + 1


@st.cache_data(show_spinner="Simulating your project…", max_entries=12)
def _analyse(fingerprint: str) -> Answer:
    return analyse(Project.from_json(fingerprint))


def answer(p: Project) -> Answer:
    return _analyse(p.fingerprint())


def money(x, cur="£"):
    return f"{'-' if x < 0 else ''}{cur}{abs(x):,.0f}"


# ------------------------------------------------------------------ editable tables
def table_editor(attr: str, columns: list[str], numeric: list[str], column_config: dict, height: int = 420) -> None:
    """Edit project.<attr> (tasks or risks). Edits are committed to the project on every change, so they
    survive navigation between pages; each commit starts a fresh editor from the updated table."""
    ss = st.session_state
    key = f"{attr}_editor_{ss.editor_version}"

    def commit():
        delta = ss[key]
        df = getattr(ss.project, attr).copy().reset_index(drop=True)
        for idx, change in delta["edited_rows"].items():
            for col, val in change.items():
                df.loc[int(idx), col] = val
        if delta["deleted_rows"]:
            df = df.drop(index=delta["deleted_rows"]).reset_index(drop=True)
        for row in delta["added_rows"]:
            df = pd.concat([df, pd.DataFrame([{c: row.get(c) for c in columns}])], ignore_index=True)
        setattr(ss.project, attr, _typed(df[columns], numeric))
        ss.editor_version += 1

    st.data_editor(getattr(ss.project, attr)[columns], num_rows="dynamic", use_container_width=True, hide_index=True,
                   key=key, on_change=commit, column_config=column_config, height=height)
