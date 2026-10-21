# Cutover and hypercare

## Cutover runbook (go-live weekend)

| # | When | Step | Owner | Check |
|---|---|---|---|---|
| 1 | T-5 days | go/no-go with steering: UAT signed, agreements signed, readiness gate passed on the latest extract | PS lead | minutes |
| 2 | T-3 | production accounts tested: ISU, SF API user, Jira service account, SFTP, Teams app consent | IT architect | each returns 200 with a read call |
| 3 | T-3 | secrets in the production key vault; build secrets revoked | IT architect | vault audit log |
| 4 | T-2 | opt-out list exported from production; the "how it works" mail sent to the pilot population | employee relations + comms | count matches the consent tool |
| 5 | T-1 | **full read** of all sources (no watermark) | impl. consultant | run log: counts equal control totals |
| 6 | T-1 | readiness scan on the production read; no new critical finding | impl. consultant | scorecard |
| 7 | T-1 | identity steward queue worked down | data steward | queue < 2% |
| 8 | T0 morning | inference + suggestions for the pilot population | impl. consultant | suggestions per person within the UAT range |
| 9 | T0 | write-back **dry run** reviewed | HRIS lead | sign-off in the change ticket |
| 10 | T0 10:00 | Teams cards sent in batches of 200, every 30 minutes | impl. consultant | first answers arrive; no error spike |
| 11 | T0 | watermark set; nightly schedule switched on | impl. consultant | next run is a delta |
| 12 | T+1 | first nightly run reviewed; first write-back applied | impl. consultant + HRIS lead | run log; spot check of 10 profiles |

**Rollback:** the write-back only adds and removes `skills-layer` skills, so rolling back means applying the inverse plan for the operations of the affected run (the operation log has every key). Cards that were already answered stay answered. The answers are kept and re-applied when the problem is fixed.

## Hypercare (6 weeks)

- **Daily** in weeks 1–2: run log review at 08:30; governance counts (opt-outs, quarantine, unvalidated downstream) must be 0; response and rejection rates per division and language.
- **Twice a week** in weeks 3–6.
- **One channel** for issues: a Teams channel with HRIS, the SF admin and the implementation team. Every issue becomes a ticket with a severity ([test strategy](test-strategy-and-uat.md)).
- **Weekly** a hypercare note to the steering committee: what broke, what we changed, what is open.

## Monitoring and alerts

| Signal | Threshold | Action |
|---|---|---|
| Interface failed | any 4xx, or 5xx after retries | page on-call; the watermark does not move |
| Record count drop | > 5% fewer than last night without a known reason | stop the write-back for that run |
| Governance count | > 0 | P1 |
| Rejection rate | > 25% in a division or language | review the suggestions; field insight |
| Response rate | < 30% after 7 days | comms: reminder + manager nudge (managers are told *that* someone has not answered, never *what* they answered) |

## Handover to run

At the end of hypercare the customer's HRIS team owns monitoring, with a [runbook entry per alert](../06-enablement/data-steward-guide.md). Vendor support takes over the platform side.
