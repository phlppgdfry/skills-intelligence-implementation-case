# Remediation plan

From the [readiness report](readiness-report.md). Every finding has an owner and a date. The implementation team does not fix customer data itself: we find problems, explain them, give a fix list and re-measure. The data stays the customer's.

| # | Finding | Owner | Action | Due | Re-measured by |
|---|---|---|---|---|---|
| R1 | 4 free-text records with health, union or national-ID data | DPO + HR operations | remove the text in SuccessFactors; tell the employee why; add a hint to the field's label ("do not enter health or personal identification data") | week 3 | readiness scan: `sensitive_free_text` = 0 |
| R2 | 2 job profiles without a description | HR job architecture | import from the 2023 job evaluation files, or write new ones with the job owner | week 5 | `job_description_missing` = 0 |
| R3 | 5 job descriptions older than 3 years | HR job architecture + job owners | 30-minute review per job; use the job-description draft prompt to propose an update ([prompts](../08-ai-first/prompts-and-agents.md)), then the owner edits and approves | week 6 | `job_description_stale` = 0 |
| R4 | 2 duplicate job titles under two codes | HR job architecture + HRIS | retire the legacy code, move incumbents, inactivate | week 5 | `duplicate_job_title` = 0 |
| R5 | 2 workers without a job profile | HR operations | assign a profile through the normal business process | week 3 | `worker_without_job` = 0 |
| R6 | 1 missing manager, 1 reporting loop | HR operations | fix the supervisory organisation | week 3 | `manager_missing`, `manager_loop` = 0 |
| R7 | 22 identity cases | data steward | work the queue ([steward guide](../06-enablement/data-steward-guide.md)) | week 4 | steward queue < 2% of records |
| R8 | 3 Jira accounts without a person | Atlassian admin | confirm they are contractors; add them to the exclusion list | week 4 | `jira_account_unresolved` explained |

**Gate re-run:** week 7, on a fresh production extract. If job architecture is still under 85%, the pilot goes ahead in the sub-population whose job profiles pass, and the rest follows in the next wave ([ADR-0008](../02-decisions/ADR-0008-phased-rollout-behind-a-readiness-gate.md)).

## What we hand back to HR permanently

The readiness scan stays in the nightly run. After go-live, new findings appear in the run log with the same owners. That is how "data quality" becomes a routine rather than a project.
