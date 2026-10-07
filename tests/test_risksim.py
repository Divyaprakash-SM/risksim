"""Run with:  pytest -q"""

import io
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from risksim.engine import analyse, compare, headline
from risksim.project import Project, blank, blocking, validate
from risksim.report import board_report, excel_report

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = (ROOT / "data" / "sample_project.json").read_text()


@pytest.fixture(scope="module")
def sample():
    return Project.from_json(SAMPLE)


@pytest.fixture(scope="module")
def ans(sample):
    return analyse(sample, 4000)


def small(rows, risks=None) -> Project:
    t = pd.DataFrame(rows)
    for c in ["Phase", "Code", "Task", "Cost", "Cost low", "Cost high", "Days", "Days low", "Days high",
              "Depends on", "Time-dependent %"]:
        if c not in t:
            t[c] = None
    p = Project.from_json(blank().to_json())
    p.tasks = t
    if risks is not None:
        p.risks = pd.DataFrame(risks)
    return Project.from_json(p.to_json())


# --- Save / load ------------------------------------------------------------------
def test_json_round_trip_is_lossless(sample):
    again = Project.from_json(sample.to_json())
    assert again.to_json() == sample.to_json()
    assert again.name == "Customer Platform Upgrade" and len(again.tasks) == 17 and len(again.risks) == 6


def test_foreign_json_is_rejected():
    with pytest.raises(ValueError, match="RiskSim"):
        Project.from_json('{"name": "x"}')


# --- Validation (plain-English errors) ---------------------------------------------
def test_sample_is_clean(sample):
    assert validate(sample) == []


def test_blank_project_cannot_run():
    assert blocking(validate(blank()))


@pytest.mark.parametrize("rows,needle", [
    ([{"Code": "A", "Task": "x", "Cost": 100, "Cost low": 150}], "cost low ≤ cost ≤ cost high"),
    ([{"Code": "A", "Task": "x", "Cost": 100}, {"Code": "A", "Task": "y", "Cost": 5}], "unique"),
    ([{"Code": "A", "Task": "x", "Cost": 1, "Days": 1, "Depends on": "B"},
      {"Code": "B", "Task": "y", "Cost": 1, "Days": 1, "Depends on": "A"}], "loop"),
    ([{"Code": "A", "Task": "x", "Cost": 1, "Days": 1, "Depends on": "Z"}], "not in the WBS"),
])
def test_errors_are_caught(rows, needle):
    issues = validate(small(rows))
    assert blocking(issues) and any(needle in m for _, m in issues)


def test_missing_durations_is_a_warning_not_an_error():
    issues = validate(small([{"Code": "A", "Task": "x", "Cost": 100}]))
    assert not blocking(issues) and any("cost only" in m for _, m in issues)


def test_bad_risk_probability_is_an_error():
    p = small([{"Code": "A", "Task": "x", "Cost": 100}],
              [{"ID": "R1", "Risk": "r", "Probability %": 140, "Cost likely": 10}])
    assert any("between 0 and 100" in m for _, m in validate(p))


# --- Answers --------------------------------------------------------------------------
def test_answer_is_consistent(ans):
    assert ans.budget == pytest.approx(np.quantile(ans.res.total_cost, 0.8))
    assert ans.base_cost == pytest.approx(106_400)
    assert ans.budget > ans.p50_cost > ans.base_cost
    assert ans.date > ans.plan_date and 0 < ans.joint < 0.8
    text = headline(ans)
    assert f"{ans.budget:,.0f}" in text and f"{ans.date:%d %b %Y}" in text


def test_cost_only_project_runs_without_dates():
    a = analyse(small([{"Code": "A", "Task": "x", "Cost": 100}, {"Code": "B", "Task": "y", "Cost": 50}]), 2000)
    assert a.date is None and a.budget > 150


def test_mitigating_a_risk_lowers_the_budget(sample):
    mit = Project.from_json(sample.to_json())
    mit.risks.loc[mit.risks["ID"] == "R1", "Probability %"] = 5
    cmp = compare({"Base": sample, "Mitigated": mit}, n_sims=4000).set_index("Scenario")
    assert cmp.loc["Mitigated", "P80 budget"] < cmp.loc["Base", "P80 budget"]


def test_reports_build(ans):
    from docx import Document
    doc = Document(io.BytesIO(board_report(ans, "Tester")))
    text = "\n".join(p.text for p in doc.paragraphs)
    assert "Customer Platform Upgrade" in text and "Risks to act on first" in text
    assert len(excel_report(ans)) > 5000
