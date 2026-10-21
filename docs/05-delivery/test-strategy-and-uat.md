# Test strategy and UAT

## Test levels

| Level | What | Where | Who | Automated |
|---|---|---|---|---|
| Unit | extraction rules, fusion, OData dates, effective dating, identity rules, write-back plan, card | this repo, `tests/test_units.py` | implementation | yes, CI |
| Integration | real HTTP against mock tenants: paging, 429/503 retries, 4xx not retried, field minimisation | `tests/test_integration.py` | implementation | yes, CI |
| Eval | eight suites with thresholds = release gate | `evals/run.py --gate` | implementation | yes, CI |
| SIT | the same flows against the customer's implementation tenant, sandbox and test instance | customer build environment | implementation + HRIS + SF admin | partly (run log comparison) |
| UAT | business scenarios on production data for the pilot population | UAT environment | HRBPs, HRIS lead; works council observers invited | no (scripted) |
| Model check | the vendor engine on a labelled Norvane sample, per language | UAT | implementation + 2 HRBPs label | semi |

## SIT checklist (excerpt)

| # | Test | Expected |
|---|---|---|
| SIT-01 | full read, all interfaces | record counts equal to source control totals |
| SIT-02 | throttling (lower the page size to force many calls) | 429s handled, no gaps or duplicates |
| SIT-03 | delta after 5 manual changes in Workday | exactly 5 workers in the delta |
| SIT-04 | wrong secret | the interface stops with a 401, alert raised, no retry storm |
| SIT-05 | effective-dated job change in SuccessFactors with a future record | today's job is used, not the future one |
| SIT-06 | write-back dry run | plan reviewed by HRIS lead; no `employee` skill in it |
| SIT-07 | write-back applied twice | second apply changes nothing |
| SIT-08 | opt-out added at 10:00 | excluded in that night's run; nothing in the export |
| SIT-09 | sensitive text planted in a test profile | quarantined; DPO alert |
| SIT-10 | Teams card to a test user, answer "No" to one skill | not written; not asked again |

## UAT scenarios

1. **"Find people for a battery systems vacancy."** An HRBP searches validated skills across BE and DE. Expected: Keldorf and Norvane people both appear; only validated skills are shown.
2. **"A transferred employee checks their profile."** The person exists in both HCMs. Expected: one profile, evidence from both, written to Workday.
3. **"An employee rejects a skill we wrote last week."** Expected: removed from Workday the next night; still visible as rejected in the platform.
4. **"The works council observer asks what we read from Jira."** Expected: the run log and the field list show four fields.
5. **"Workforce plan: how many people with high-voltage skills per site?"** Expected: Visier shows validated counts only, for groups of 10 or more.

## Model check on Norvane's own data

The stand-in in this repo is measured on synthetic data. The real engine must be checked on Norvane's data before go-live:

- 2 HRBPs label 150 texts (job descriptions, ticket summaries, course titles), stratified over EN, NL, DE and FR.
- Measure precision and recall per language, and the gap between the best and worst language (gate from [ADR-0010](../02-decisions/ADR-0010-multilingual-taxonomy-before-go-live.md): ≤ 6 points).
- Measure inter-annotator agreement (Cohen's kappa) on 30 shared texts. If the labellers disagree a lot, the problem is the definition, not the model.
- Report to the vendor with examples ([field insights](../07-product-feedback/field-insights.md)).

## Defect severity

| Severity | Example | Response |
|---|---|---|
| P1 | data for an opted-out person processed; an employee skill deleted; a wrong person merged | stop the interface, inform the DPO the same day |
| P2 | an interface fails two nights in a row | fix within 2 working days |
| P3 | wrong suggestion pattern (for example a recurring false positive) | log as field insight; fix in the taxonomy or report to product |
| P4 | cosmetic | backlog |
