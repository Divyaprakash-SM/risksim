"""Run a RiskSim project through the Monte Carlo engine and turn the results into answers."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from montecarlo import (Settings, allocate_contingency, budget_for_jcl, contingency_split, jcl, risk_ranking,
                        run_integrated, schedule_sensitivity)
from montecarlo.integrated import IntegratedResult

from .project import Project


def settings_for(p: Project, n_sims: int | None = None) -> Settings:
    o = p.options
    return Settings(n_sims=n_sims or o.n_sims, optimistic_factor=o.cost_low_factor, pessimistic_factor=o.cost_high_factor,
                    risk_mode="none", correlation=o.correlation, duration_optimistic_factor=o.days_low_factor,
                    duration_pessimistic_factor=o.days_high_factor, time_dependent_share=o.time_dependent / 100,
                    start_date=p.start_date)


@dataclass
class Answer:
    """Everything the results, scenarios and report pages need, in one place."""
    project: Project
    res: IntegratedResult
    base_cost: float
    budget: float              # cost at the chosen confidence
    p50_cost: float
    chance_base_enough: float
    plan_days: float | None
    plan_date: pd.Timestamp | None
    date_days: float | None    # duration at the chosen confidence
    date: pd.Timestamp | None
    p50_date: pd.Timestamp | None
    chance_plan_date: float | None
    joint: float | None        # chance of meeting budget AND date
    budget_for_target: float | None

    @property
    def contingency(self) -> float:
        return self.budget - self.base_cost


def analyse(p: Project, n_sims: int | None = None) -> Answer:
    s = settings_for(p, n_sims)
    res = run_integrated(p.engine_tasks(), p.engine_risks(), p.options.distribution, s)
    c = p.options.confidence
    base = res.base_cost
    budget = float(np.quantile(res.total_cost, c))
    a = dict(project=p, res=res, base_cost=base, budget=budget, p50_cost=float(np.median(res.total_cost)),
             chance_base_enough=float((res.total_cost <= base).mean()),
             plan_days=None, plan_date=None, date_days=None, date=None, p50_date=None, chance_plan_date=None,
             joint=None, budget_for_target=None)
    if res.schedule is not None:
        sr = res.schedule
        d = float(np.quantile(sr.project_days, c))
        a.update(plan_days=sr.deterministic_days, plan_date=sr.finish_date(sr.deterministic_days), date_days=d,
                 date=sr.finish_date(d), p50_date=sr.finish_date(np.median(sr.project_days)),
                 chance_plan_date=float((sr.project_days <= sr.deterministic_days).mean()),
                 joint=jcl(res, budget, d), budget_for_target=budget_for_jcl(res, d, p.options.joint_target))
    return Answer(**a)


def odds(x: float) -> str:
    return "almost no chance" if x < 0.01 else f"a {x:.0%} chance"


def headline(a: Answer) -> str:
    """The one-paragraph answer a sponsor wants, in plain English."""
    cur, c = a.project.currency, a.project.options.confidence
    txt = (f"Budget **{cur}{a.budget:,.0f}** to be {c:.0%} confident of covering the cost: that is "
           f"{cur}{a.contingency:,.0f} ({a.contingency / a.base_cost:.0%}) above the base estimate of "
           f"{cur}{a.base_cost:,.0f}, which on its own has {odds(a.chance_base_enough)} of being enough.")
    if a.date is not None:
        txt += (f" Plan for **{a.date:%d %b %Y}**: the schedule's own date of {a.plan_date:%d %b %Y} has "
                f"{odds(a.chance_plan_date)}. Hitting both the budget and the date together has a "
                f"{a.joint:.0%} chance.")
    return txt


def drivers(a: Answer, top: int = 5) -> dict:
    p = a.project
    s = settings_for(p, min(p.options.n_sims, 4000))
    out = {"risks": pd.DataFrame(), "critical": pd.DataFrame(), "split": None, "allocation": allocate_contingency(a.res, p.options.confidence)}
    reg = p.engine_risks()
    if reg is not None:
        out["risks"] = risk_ranking(p.engine_tasks(), reg, p.options.distribution, s, p.options.confidence).head(top)
    out["split"] = contingency_split(p.engine_tasks(), reg, p.options.distribution, settings_for(p), p.options.confidence)
    if a.res.schedule is not None:
        out["critical"] = schedule_sensitivity(a.res.schedule).head(top)
    return out


def compare(scenarios: dict[str, Project], n_sims: int = 5000) -> pd.DataFrame:
    rows = []
    for name, p in scenarios.items():
        a = analyse(p, n_sims)
        rows.append({"Scenario": name, "Base estimate": a.base_cost, "P50 cost": a.p50_cost,
                     f"P{int(p.options.confidence * 100)} budget": a.budget,
                     "Contingency": a.contingency, "P50 finish": a.p50_date,
                     f"P{int(p.options.confidence * 100)} finish": a.date,
                     "Chance of plan date": a.chance_plan_date, "Joint confidence": a.joint,
                     "_cost": a.res.total_cost, "_days": None if a.res.schedule is None else a.res.schedule.project_days,
                     "_start": p.start_date})
    return pd.DataFrame(rows)
