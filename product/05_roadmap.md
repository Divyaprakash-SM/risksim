# Roadmap

Prioritised with **RICE** (Reach × Impact × Confidence ÷ Effort). Reach = projects per quarter it would affect in a pilot of ~50 PMs; Impact 0.5–3; Confidence 50–100%; Effort in person-weeks.

| Feature | Reach | Impact | Confidence | Effort | RICE | When |
|---|---|---|---|---|---|---|
| Usability test with 5 PMs and fix top issues | 50 | 2 | 100% | 1 | **100** | Now |
| MS Project XML import | 30 | 2 | 80% | 2 | **24** | Next |
| Portfolio view (many projects, one method) | 10 | 3 | 70% | 3 | **7** | Next |
| Correlation by phase (not just one global value) | 20 | 1 | 60% | 1 | **12** | Next |
| Risk-response costing ("is this mitigation worth it?" calculator) | 40 | 2 | 80% | 1.5 | **43** | Now |
| Accounts + cloud save (opt-in) | 50 | 1 | 50% | 4 | **6** | Later |
| Primavera P6 XER import | 5 | 3 | 60% | 4 | **2** | Later |
| Jira / Monday.com connectors | 15 | 1 | 50% | 3 | **2.5** | Later |

## Now (MVP → v0.2)
- ✅ Browser project builder, validation, risk register, results, scenarios, board report.
- ⏭ **Usability test** (see `07_metrics_and_testing.md`) → fix the top 3 issues.
- ⏭ **Mitigation calculator:** enter a response's cost and its effect on probability/impact, and see the net saving at P80.

## Next (v0.3)
- MS Project import.
- Portfolio view: run every project in a folder and roll up contingency.
- Correlation by phase.

## Later
- Opt-in accounts and cloud save; team sharing.
- P6 import; integrations.

## What we will not build
- A Gantt editor or a scheduling engine competitor.
- A "black box" AI estimate. Every number must be explainable from the inputs.
