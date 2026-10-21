# Data steward guide

Two queues need a person: **identity** (who is who) and the **crosswalk** (how a library entry maps). Both appear in the nightly run log. Target: under 2% of records waiting, nothing older than 10 working days.

## Identity queue

Open it with `python -m skillslayer sync` (the count) and the steward view in the platform. Each case has a record, the candidates and a reason.

| Reason | What you check | Decide |
|---|---|---|
| *same name or email local part, but no post-merger Workday hire* | Is this the same person? Look at the job, location and SF status. A homonym usually has a different job and an old Workday hire date. | **Same person:** fill `legacySuccessFactorsId` on the Workday worker (fixes it for good). **Different:** mark "not a match". |
| *initials only* (Jira) | Ask the Atlassian admin for the account's email, or ask the person's team lead. | Add the mapping, or ask the user to make their email visible to the organisation. |
| *several people with this name* (Jira) | Same as above. | Same. |
| unresolved Jira account, no candidates | Contractor? Test account? Shared account? | Add it to the exclusion list with a reason. |

**Never** merge on a guess. A wrong merge means one person is asked to confirm another person's work. That is a P1 incident.

## Crosswalk queue

`python -m skillslayer crosswalk` lists every library entry with its method.

| Method | Meaning | Your job |
|---|---|---|
| `exact`, `normalized` | automatic | spot-check 5 per month |
| `fuzzy` | a guess based on spelling | confirm or correct |
| `none` | no match | either map it by hand ("PM" → Project management) or mark it *out of scope* (soft skills like "Teamwork", languages, driving licences: these stay customer attributes) |

When you map something by hand that a better rule could have caught (abbreviations, certifications), log it as a field insight. The next customer will hit the same thing.

## Run-log alerts you own

| Alert | First step |
|---|---|
| steward queue > 2% | check whether a transfer wave happened; ask HR operations to fill the cross-reference at transfer |
| new `sensitive_free_text` finding | inform the DPO the same day; do not open or copy the text beyond what is needed to remove it |
| new `duplicate_job_title` | inform HR job architecture |
