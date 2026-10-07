# Success metrics and user testing plan

## North-star metric
**Board reports generated per week.** A report means a user got to a decision-ready answer, which is the value RiskSim exists to deliver.

## Funnel
| Stage | Metric | Target (pilot) |
|---|---|---|
| Activation | Visitors who reach Results (sample or own project) | 60% |
| Own data | Users who import or build their own project | 30% of activated |
| Value | Users who download a board report | 50% of own-data users |
| Habit | Users who return within 30 days with a saved project | 25% |

## Guardrails
- **Time to first answer:** median under 10 minutes from a spreadsheet import.
- **Validation dead-ends:** under 10% of sessions stuck on a blocking error for more than 2 minutes.
- **Comprehension:** 4 of 5 test users can explain the headline sentence correctly in their own words.

## Usability test plan (5 project managers, 45 minutes each)
1. **Warm-up (5 min):** how do you set contingency today?
2. **Task 1 (10 min):** "Here's your WBS spreadsheet. Find out what budget to ask for." Observe the import and validation, and where they hesitate.
3. **Task 2 (10 min):** "Your sponsor asks how likely the date is." Can they find and explain the timeline and joint confidence?
4. **Task 3 (10 min):** "Is it worth £3k to mitigate the vendor-API risk?" Do they use scenarios or the risk ranking?
5. **Debrief (10 min):** what would stop you using this at work? What would you pay?

**Record:** task success, time on task, errors, quotes. **Decide:** the top 3 issues by frequency × severity go into v0.2.
