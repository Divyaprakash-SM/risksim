# Product requirements: RiskSim MVP

| | |
|---|---|
| **Status** | MVP built (v0.1). Usability testing not yet run |
| **Owner** | Divyaprakash S M |
| **Goal** | A PM gets a defensible budget, date and risk ranking from their WBS in under 10 minutes |

## Goals and non-goals
**Goals**
1. Time to first answer **under 10 minutes** for a 20-task project (from a template or an import).
2. The answer is understandable **without statistics training**: plain-English headline and no unexplained jargon.
3. Every number is **reproducible and explainable**: fixed random seed, assumptions shown, method stated in the report.

**Non-goals (MVP)**
- User accounts, cloud storage, collaboration.
- Integration with MS Project, Primavera or Jira (import is via spreadsheet).
- Resource levelling, calendars, or correlation by group.

## User stories and acceptance criteria

| # | As a… | I want to… | So that… | Acceptance criteria | MVP |
|---|---|---|---|---|---|
| 1 | PM | start from my existing WBS spreadsheet | I don't retype it | Import finds Task and Cost columns by name, wherever the header row is; milestone sub-total rows are excluded automatically | ✅ |
| 2 | PM | build a project in the browser | I can start without Excel | Editable table; add and delete rows; edits persist across pages | ✅ |
| 3 | PM | be told in plain English what's wrong with my inputs | I can fix them myself | Errors (block results) and warnings (don't), each naming the task, e.g. "cost low ≤ cost ≤ cost high is not true" | ✅ |
| 4 | PM | see the budget and date at my chosen confidence | I can commit with known odds | P50/P70/P80/P90 selector; headline sentence; odds of the base estimate and the plan date | ✅ |
| 5 | Sponsor | know the chance of hitting budget **and** date | I'm not misled by two separate P80s | Joint confidence shown, with an interactive budget/date check | ✅ |
| 6 | PM | see which tasks drive the date | I manage the right ones | Criticality index per task | ✅ |
| 7 | PM | see which risks are worth mitigating | I spend mitigation money well | Risks ranked by reduction in P80 budget and P80 date if removed | ✅ |
| 8 | PMO | see where contingency comes from and who holds it | approval is transparent | Split into estimate uncertainty vs named risks; allocation by phase that sums exactly | ✅ |
| 9 | PM | compare a mitigation or change with the baseline | I can price the decision | Save scenarios; side-by-side table; overlaid confidence curves; plain-English difference | ✅ |
| 10 | Sponsor | read one page | I can decide in a meeting | Word one-pager: headline, table, two charts, top risks with responses | ✅ |
| 11 | PMO | keep the full analysis | it's auditable | Excel export with inputs, assumptions, sensitivity, schedule, allocation | ✅ |
| 12 | PM | save and reopen my work without an account | my data stays with me | JSON project file; lossless round trip | ✅ |
| 13 | PMO | apply one method across 25 projects | approvals are consistent | Portfolio view | ❌ Next |
| 14 | PM | import from MS Project | I don't keep two plans | .xml / .mpp import | ❌ Later |

## Screens
1. **Start:** value proposition, three-step explainer; sample, blank, import or open a project.
2. **Tasks & schedule:** project settings, task table, default ranges, live checks.
3. **Risk register:** risk table, probability-impact map.
4. **Results:** headline; tabs for budget, timeline, joint confidence, risks and contingency.
5. **Scenarios:** save, load, delete, compare.
6. **Report & export:** Word, Excel, JSON.

## Non-functional requirements
| Area | Requirement | MVP |
|---|---|---|
| Performance | 10,000 simulations of a 20-task project with 6 risks in about 1 second | ✅ (~1 s) |
| Privacy | No project data stored server-side; files only leave via user download | ✅ |
| Correctness | Formulas tested against hand calculations; 37 automated tests | ✅ |
| Accessibility | Status never shown by colour alone; plain-English labels | Partial |
| Reproducibility | Same inputs give the same answer (fixed seed) | ✅ |

## Open questions
- Is P80 the right default for all users, or should bid teams default to P90?
- Do users trust a range more if they can see the individual simulated projects (dot plot) or less?
- What's the minimum viable import from MS Project: XML export, or a CSV of tasks?
