# Problem and vision

## The problem
Most project budgets and delivery dates are single numbers. A team adds up its estimates, puts 10% on top "for contingency", and commits. The sum hides three facts:

1. **Every estimate is a range.** Adding up the most-likely values gives a total that is almost never the most likely total. In RiskSim's sample project the base estimate of £106,400 has *almost no chance* of being enough.
2. **Schedules are biased towards optimism.** Where parallel work streams join, the project waits for the slowest one, so uncertainty only pushes the date later. The sample plan date has a 4% chance.
3. **Risks are events, not percentages.** A risk either happens or it doesn't. Treating every risk as certain over-budgets; ignoring risks under-budgets.

Specialist quantitative risk tools exist, but they are priced, trained and staffed for large capital programmes. The people who make most budget-and-date commitments (project managers, PMO analysts and bid teams in small and mid-sized organisations) don't have them, so they fall back on spreadsheets and rules of thumb.

## Who feels it
- **Project managers** who are held to a number they never believed.
- **Bid and commercial teams** pricing fixed-price work, where every overrun comes out of margin.
- **PMOs and sponsors** who approve contingency with no way to tell whether 10% is too much or too little.

## Vision
> Any project manager can get a defensible budget, a realistic date and a ranked list of risks worth acting on, in under ten minutes, without a risk analyst.

## What RiskSim does
- **Answers in plain English:** "Budget £126,861 to be 80% confident. Plan for 23 Sep. Budget and date together: 72%."
- **Separates the contingency:** estimating uncertainty vs named risks. Only the second can be bought down.
- **Ranks risks by what they do to the budget and date,** not by probability × impact.
- **Compares scenarios,** so a mitigation or scope change can be priced before it is approved.
- **Produces a one-page board report** a sponsor will read.

## What it deliberately does not do (yet)
- Replace a scheduling tool. Durations and dependencies are inputs, not a Gantt editor.
- Store data on a server. The project file stays with the user, which removes the main adoption barrier (data security approval).
- Resource levelling, calendars or cost-loaded schedules from Primavera or MS Project (see the roadmap).

## Why now
- Contingency is under more scrutiny. HM Treasury's Green Book requires optimism-bias adjustment, and NASA-style joint confidence levels are spreading beyond aerospace.
- Browser-based Python apps make it possible to ship a credible simulation tool with no install and no IT ticket.
