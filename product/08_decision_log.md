# Decision log

| # | Decision | Options considered | Why | Revisit if |
|---|---|---|---|---|
| 1 | **Streamlit** for the MVP UI | React + API; Excel add-in | Ships a working, deployable product in days on the existing Python engine; free hosting | Users need multi-user editing or a native feel |
| 2 | **No server-side storage**; project saved as a JSON file | Database + accounts | Removes the data-security approval that blocks most enterprise tools; no account friction | >30% of test users ask for cloud save |
| 3 | **Risk register as events** is the default method | Loading every task by its risk %, as in the dissertation | Loading treats risks as certain and over-budgets the sample by about £40k; events match how risks behave | Users can't produce probability/impact estimates |
| 4 | **P80 default** confidence | P50, P90 | Most common organisational standard; switchable per project | Bid teams consistently switch to P90 |
| 5 | **Beta-PERT** default distribution | Triangular, Lognormal | Standard in PM practice; less weight on the extremes than triangular | Calibration against actuals shows a long tail |
| 6 | Rank risks by **change in P80 if removed** | Probability × impact | P × I ignores whether the risk hits the critical path; P80 change is what the budget feels | Too slow for large registers (currently one re-run per risk) |
| 7 | **Plain-English validation** that names the task | Generic errors | Users fix inputs themselves instead of abandoning | Error dead-end guardrail is breached |
| 8 | **Fixed random seed** | Fresh randomness each run | The same inputs always give the same answer, which builds trust and auditability | Users want to see run-to-run variation |
