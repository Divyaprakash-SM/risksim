"""
The RiskSim project model: what a user builds in the browser.

The editor tables use plain-English columns (Phase, Cost low, Depends on ...).
This module converts them to and from the engine's format, checks them for
mistakes in language a project manager understands, and saves and loads
projects as JSON.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from montecarlo import load_risk_register, load_wbs
from montecarlo.schedule import resolve_predecessors, topological_order

TASK_COLUMNS = ["Phase", "Code", "Task", "Cost", "Cost low", "Cost high", "Days", "Days low", "Days high",
                "Depends on", "Time-dependent %"]
RISK_COLUMNS = ["ID", "Risk", "Owner", "Probability %", "Cost low", "Cost likely", "Cost high",
                "Delay low", "Delay likely", "Delay high", "Affects task", "Response"]
NUMERIC_TASK = ["Cost", "Cost low", "Cost high", "Days", "Days low", "Days high", "Time-dependent %"]
NUMERIC_RISK = ["Probability %", "Cost low", "Cost likely", "Cost high", "Delay low", "Delay likely", "Delay high"]


@dataclass
class Options:
    n_sims: int = 10_000
    distribution: str = "pert"
    correlation: float = 0.0
    cost_low_factor: float = 0.90      # used when a task has no Cost low
    cost_high_factor: float = 1.20
    days_low_factor: float = 0.90
    days_high_factor: float = 1.35
    time_dependent: float = 50.0       # % of cost paid by the day, when not given
    confidence: float = 0.80           # the budget and date confidence the organisation plans to
    joint_target: float = 0.70         # target chance of meeting budget AND date together


@dataclass
class Project:
    name: str = "Untitled project"
    currency: str = "£"
    start_date: str = "2026-01-05"
    tasks: pd.DataFrame = field(default_factory=lambda: pd.DataFrame(columns=TASK_COLUMNS))
    risks: pd.DataFrame = field(default_factory=lambda: pd.DataFrame(columns=RISK_COLUMNS))
    options: Options = field(default_factory=Options)

    # ------------------------------------------------------------------ save / load
    def to_json(self) -> str:
        clean = lambda df: json.loads(df.replace({np.nan: None}).to_json(orient="records"))
        return json.dumps({"app": "RiskSim", "version": 1, "name": self.name, "currency": self.currency,
                           "start_date": self.start_date, "options": asdict(self.options),
                           "tasks": clean(self.tasks.reindex(columns=TASK_COLUMNS)),
                           "risks": clean(self.risks.reindex(columns=RISK_COLUMNS))},
                          indent=2)

    @classmethod
    def from_json(cls, text: str) -> "Project":
        d = json.loads(text)
        if d.get("app") != "RiskSim":
            raise ValueError("This file wasn't saved by RiskSim.")
        tasks = _typed(pd.DataFrame(d["tasks"], columns=TASK_COLUMNS), NUMERIC_TASK)
        risks = _typed(pd.DataFrame(d.get("risks", []), columns=RISK_COLUMNS), NUMERIC_RISK)
        return cls(d["name"], d.get("currency", "£"), d.get("start_date", "2026-01-05"), tasks, risks,
                   Options(**d.get("options", {})))

    def fingerprint(self) -> str:
        return self.to_json()

    # ------------------------------------------------------------------ engine format
    def engine_tasks(self) -> pd.DataFrame:
        t = self.tasks.copy()
        t = t[t["Task"].fillna("").astype(str).str.strip() != ""].reset_index(drop=True)
        if t.empty:
            return pd.DataFrame(columns=["WBS Code", "Task", "Cost", "Optimistic", "Pessimistic", "Risk Impact",
                                         "Risk Likelihood", "Risk Score", "Risk Multiplier", "Duration",
                                         "Optimistic Duration", "Pessimistic Duration", "Predecessors",
                                         "Time-dependent %", "Milestone", "Label"])
        codes = t["Code"].fillna("").astype(str).str.strip()
        codes = [c if c else f"T{i + 1}" for i, c in enumerate(codes)]
        out = pd.DataFrame({
            "WBS Code": codes, "Task": t["Task"].astype(str).str.strip(),
            "Cost": pd.to_numeric(t["Cost"], errors="coerce"),
            "Optimistic": pd.to_numeric(t["Cost low"], errors="coerce"),
            "Pessimistic": pd.to_numeric(t["Cost high"], errors="coerce"),
            "Risk Impact": np.nan, "Risk Likelihood": np.nan, "Risk Score": np.nan, "Risk Multiplier": 0.0,
            "Duration": pd.to_numeric(t["Days"], errors="coerce"),
            "Optimistic Duration": pd.to_numeric(t["Days low"], errors="coerce"),
            "Pessimistic Duration": pd.to_numeric(t["Days high"], errors="coerce"),
            "Predecessors": t["Depends on"].fillna("").astype(str).str.replace(";", ",").str.replace(" ", ""),
            "Time-dependent %": pd.to_numeric(t["Time-dependent %"], errors="coerce") / 100,
            "Milestone": t["Phase"].fillna("").astype(str).str.strip().replace("", "Unphased"),
        })
        out["Label"] = out["WBS Code"] + " - " + out["Task"]
        return out

    def engine_risks(self) -> pd.DataFrame | None:
        r = self.risks.copy()
        r = r[r["Risk"].fillna("").astype(str).str.strip() != ""].reset_index(drop=True)
        if r.empty:
            return None
        num = {c: pd.to_numeric(r[c], errors="coerce") for c in NUMERIC_RISK}
        cost_ml = num["Cost likely"].fillna(num["Cost low"]).fillna(num["Cost high"]).fillna(0)
        days_ml = num["Delay likely"].fillna(num["Delay low"]).fillna(num["Delay high"]).fillna(0)
        ids = r["ID"].fillna("").astype(str).str.strip()
        return pd.DataFrame({
            "Risk ID": [i if i else f"R{k + 1}" for k, i in enumerate(ids)],
            "Risk": r["Risk"].astype(str), "Owner": r["Owner"].fillna("").astype(str),
            "Probability": num["Probability %"].fillna(0) / 100,
            "Cost Min": num["Cost low"].fillna(cost_ml), "Cost ML": cost_ml, "Cost Max": num["Cost high"].fillna(cost_ml),
            "Days Min": num["Delay low"].fillna(days_ml), "Days ML": days_ml, "Days Max": num["Delay high"].fillna(days_ml),
            "Affects": r["Affects task"].fillna("").astype(str).str.strip(),
        })

    @property
    def has_schedule(self) -> bool:
        d = pd.to_numeric(self.engine_tasks()["Duration"], errors="coerce")
        return len(d) > 0 and d.notna().all()


def _typed(df: pd.DataFrame, numeric: list[str]) -> pd.DataFrame:
    for c in numeric:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    for c in df.columns:
        if c not in numeric:
            df[c] = df[c].astype(object).where(df[c].notna(), None)
    return df


# ---------------------------------------------------------------------- validation
def validate(p: Project) -> list[tuple[str, str]]:
    """Return [(level, message)] where level is 'error' (blocks the run) or 'warning'."""
    out: list[tuple[str, str]] = []
    t = p.engine_tasks()
    if t.empty:
        return [("error", "Add at least one task with a name and a cost.")]
    for _, r in t.iterrows():
        name = f"{r['WBS Code']} {r['Task']}"
        if pd.isna(r["Cost"]) or r["Cost"] < 0:
            out.append(("error", f"{name}: needs a cost of zero or more."))
            continue
        lo = r["Optimistic"] if pd.notna(r["Optimistic"]) else r["Cost"]
        hi = r["Pessimistic"] if pd.notna(r["Pessimistic"]) else r["Cost"]
        if not lo <= r["Cost"] <= hi:
            out.append(("error", f"{name}: cost low ≤ cost ≤ cost high is not true."))
        if pd.notna(r["Duration"]):
            dlo = r["Optimistic Duration"] if pd.notna(r["Optimistic Duration"]) else r["Duration"]
            dhi = r["Pessimistic Duration"] if pd.notna(r["Pessimistic Duration"]) else r["Duration"]
            if not dlo <= r["Duration"] <= dhi:
                out.append(("error", f"{name}: days low ≤ days ≤ days high is not true."))
    dup = t["WBS Code"][t["WBS Code"].duplicated()].unique()
    if len(dup):
        out.append(("error", f"Task codes must be unique. Repeated: {', '.join(dup)}."))
    days = t["Duration"]
    if days.notna().any() and days.isna().any():
        missing = ", ".join(t.loc[days.isna(), "WBS Code"].head(5))
        out.append(("warning", f"Some tasks have no duration ({missing}…), so only cost is simulated. "
                               "Give every task a duration to get finish dates."))
    elif days.isna().all():
        out.append(("warning", "No durations yet: RiskSim will simulate cost only. Add Days and Depends on to get dates."))
    if days.notna().all() and not dup.size:
        try:
            topological_order(resolve_predecessors(t))
        except ValueError as e:
            out.append(("error", str(e)))
    r = p.engine_risks()
    if r is not None:
        codes = set(t["WBS Code"])
        for _, x in r.iterrows():
            if not 0 <= x["Probability"] <= 1:
                out.append(("error", f"Risk {x['Risk ID']}: probability must be between 0 and 100%."))
            if not x["Cost Min"] <= x["Cost ML"] <= x["Cost Max"]:
                out.append(("error", f"Risk {x['Risk ID']}: cost low ≤ likely ≤ high is not true."))
            if not x["Days Min"] <= x["Days ML"] <= x["Days Max"]:
                out.append(("error", f"Risk {x['Risk ID']}: delay low ≤ likely ≤ high is not true."))
            if x["Affects"] and x["Affects"] not in codes:
                out.append(("warning", f"Risk {x['Risk ID']} affects '{x['Affects']}', which isn't a task code. "
                                       "Its delay will be added at project level."))
    no_range = t["Optimistic"].isna() & t["Pessimistic"].isna()
    if no_range.all() and len(t) > 1:
        out.append(("warning", "No task has its own cost range, so the default range is used for every task. "
                               "Ranges on your biggest tasks make the answer much more credible."))
    return out


def blocking(issues) -> bool:
    return any(level == "error" for level, _ in issues)


# ---------------------------------------------------------------------- import
def from_excel(path, name: str | None = None) -> Project:
    """Import a WBS workbook (the Monte Carlo template format) into a RiskSim project."""
    tasks, _ = load_wbs(path)
    reg = load_risk_register(path)
    t = pd.DataFrame({
        "Phase": tasks["Milestone"], "Code": tasks["WBS Code"], "Task": tasks["Task"], "Cost": tasks["Cost"],
        "Cost low": tasks["Optimistic"], "Cost high": tasks["Pessimistic"], "Days": tasks["Duration"],
        "Days low": tasks["Optimistic Duration"], "Days high": tasks["Pessimistic Duration"],
        "Depends on": tasks["Predecessors"].str.replace(",", ", "),
        "Time-dependent %": tasks["Time-dependent %"] * 100,
    })
    # Tasks loaded with a risk multiplier but no register: keep them as plain tasks (register is the method here)
    r = pd.DataFrame(columns=RISK_COLUMNS)
    if reg is not None:
        r = pd.DataFrame({"ID": reg["Risk ID"], "Risk": reg["Risk"], "Owner": reg["Owner"],
                          "Probability %": reg["Probability"] * 100, "Cost low": reg["Cost Min"],
                          "Cost likely": reg["Cost ML"], "Cost high": reg["Cost Max"], "Delay low": reg["Days Min"],
                          "Delay likely": reg["Days ML"], "Delay high": reg["Days Max"], "Affects task": reg["Affects"],
                          "Response": ""})
    return Project(name or Path(path).stem.replace("_", " ").title(), "£", "2026-01-05",
                   _typed(t, NUMERIC_TASK), _typed(r, NUMERIC_RISK))


def blank() -> Project:
    t = pd.DataFrame([{"Phase": "Phase 1", "Code": "1.1", "Task": "", "Cost": None, "Cost low": None,
                       "Cost high": None, "Days": None, "Days low": None, "Days high": None,
                       "Depends on": "", "Time-dependent %": None}], columns=TASK_COLUMNS)
    return Project("New project", tasks=_typed(t, NUMERIC_TASK), risks=_typed(pd.DataFrame(columns=RISK_COLUMNS), NUMERIC_RISK))
