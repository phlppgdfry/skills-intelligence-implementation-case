# Success criteria

Agreed with the sponsor in week 1. Each criterion has a number, a source and an owner, so nobody has to argue later about whether it worked.

## Pilot exit (end of week 14)

| # | Criterion | Target | Measured by | Owner |
|---|---|---|---|---|
| S1 | Readiness gate passes for the pilot population | all five dimensions pass | `python -m skillslayer readiness` on the production extract | HRIS lead |
| S2 | Data flows complete and reconciled | 100% of source records accounted for in the run log, 0 unexplained differences | nightly run log + weekly reconciliation | integration lead |
| S3 | Employees respond to their validation card | ≥ 60% of invited employees within 3 weeks | Teams bot telemetry | HR director |
| S4 | Wrong suggestions stay rare | ≤ 0.5 wrong suggestions per person (eval: <!--n:profiles.policies.corroborated.wrong_asks_per_person-->0.17<!--/n-->) | rejected / asked, from the bot | implementation consultant |
| S5 | Nothing unvalidated reaches Workday or Visier | 0 rows (eval: <!--n:governance.with_controls.unvalidated_in_export-->0<!--/n-->) | daily governance check in the run log | DPO |
| S6 | Opt-outs fully honoured | 0 records processed for opted-out people (eval: <!--n:governance.with_controls.optout_with_evidence-->0<!--/n-->) | daily governance check | DPO |
| S7 | Used in real decisions | ≥ 10 internal mobility cases where HRBPs used skills data | HRBP log | HR director |
| S8 | Works council agreement in place | signed in BE and DE before production data flows | agreement | employee relations |

## Scale decision (end of week 20)

Go to all divisions if S1–S8 hold, the steward queue is under 2% of records, and hypercare has had no P1 incident for 4 weeks.

## What we explicitly do not promise

- A number for "skills coverage" without validation behind it. Inferred skills are suggestions, not facts.
- Model accuracy figures from this repository. They come from a stand-in engine and synthetic data. The vendor's own model is evaluated separately on the customer's data during the pilot ([test strategy](../05-delivery/test-strategy-and-uat.md)).
