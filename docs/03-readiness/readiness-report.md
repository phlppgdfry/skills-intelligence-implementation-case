# AI-readiness report: electrification division

*Generated from `python -m skillslayer readiness` on the week-2 extract. Numbers between markers are refreshed by `scripts/build.py`.*

## Verdict

**Not ready for a pilot yet. Fixable in about three weeks.** Four of the five dimensions pass. Job architecture does not: too many job profiles have no description, an old one, or a duplicate. Every finding has an owner and a fix.

| Dimension | Score | Pilot gate | Status | What it measures |
|---|---|---|---|---|
| Job architecture | <!--n:readiness.scores.job_architecture-->70%<!--/n--> | <!--n:readiness.thresholds.job_architecture-->85%<!--/n--> | **fail** | share of active Workday job profiles with a usable, current, unique description |
| Workforce data | <!--n:readiness.scores.workforce_data-->97.5%<!--/n--> | <!--n:readiness.thresholds.workforce_data-->95%<!--/n--> | pass | workers with a job profile and a valid reporting line |
| Identity | <!--n:readiness.scores.identity-->94.4%<!--/n--> | <!--n:readiness.thresholds.identity-->90%<!--/n--> | pass | source records linked to a person automatically |
| Work evidence | <!--n:readiness.scores.work_evidence-->90.2%<!--/n--> | <!--n:readiness.thresholds.work_evidence-->50%<!--/n--> | pass | people with at least one piece of work or learning evidence |
| Privacy | <!--n:readiness.scores.privacy-->91.7%<!--/n--> clean | every flagged record quarantined | pass | free-text records without special-category data |

## Findings

<!--n:readiness.findings-->44<!--/n--> findings: <!--n:readiness.counts.critical-->4<!--/n--> critical, <!--n:readiness.counts.high-->6<!--/n--> high, <!--n:readiness.counts.medium-->29<!--/n--> medium, <!--n:readiness.counts.low-->5<!--/n--> low.

| Check | Found | Severity | Owner | Fix |
|---|---|---|---|---|
| Sensitive data in free text (health, union, national ID) | <!--n:readiness.by_check.sensitive_free_text.found-->4<!--/n--> | critical | DPO + HR operations | remove at the source, inform the employee; the record is quarantined until then |
| Job description missing | <!--n:readiness.by_check.job_description_missing.found-->2<!--/n--> | high | HR job architecture | write or import one |
| Worker without a job profile | <!--n:readiness.by_check.worker_without_job.found-->2<!--/n--> | high | HR operations | assign a job profile |
| Manager reference to a non-existent worker | <!--n:readiness.by_check.manager_missing.found-->1<!--/n--> | high | HR operations | fix the supervisory organisation |
| Reporting-line loop | <!--n:readiness.by_check.manager_loop.found-->1<!--/n--> | high | HR operations | break the loop |
| Job description older than 3 years | <!--n:readiness.by_check.job_description_stale.found-->5<!--/n--> | medium | HR job architecture | review with the job owner |
| Duplicate job title under two codes | <!--n:readiness.by_check.duplicate_job_title.found-->2<!--/n--> | medium | HR job architecture | merge, remap incumbents |
| Identity: steward review | <!--n:readiness.identity_review-->22<!--/n--> | medium | data steward | confirm or reject the candidate |
| Job profile with no incumbents | <!--n:readiness.by_check.job_without_incumbents.found-->2<!--/n--> | low | HR job architecture | inactivate or confirm as planned role |
| Jira account nobody can be linked to | <!--n:readiness.by_check.jira_account_unresolved.found-->3<!--/n--> | low | Atlassian admin | confirm external, or add a mapping |

## Is the scan itself right?

The synthetic extract contains <!--n:readiness.planted-->22<!--/n--> problems that the data generator planted on purpose. The scan found <!--n:readiness.found-->22<!--/n--> of them (<!--n:readiness.recall-->100%<!--/n-->) and raised <!--n:readiness.false_alarm_count-->0<!--/n--> false alarms. This is the eval suite `readiness`. It runs in CI, so a change to a check that stops finding a planted problem fails the build.

## What the scores mean for the plan

- **Job architecture is the critical path.** The 12 job-profile findings belong to one team, HR job architecture. Their fix is scheduled in weeks 4–6 of the [implementation plan](../05-delivery/implementation-plan.md), and the gate is re-run in week 7.
- **The critical privacy findings do not block the pilot**, because the records are quarantined and never reach the engine. They do require a DPO action within 5 working days, because the data should not be in that field at all.
- **Identity is good enough** to start. The steward queue is small, and most Jira cases resolve once users make their email visible.

See the [remediation plan](remediation-plan.md).
