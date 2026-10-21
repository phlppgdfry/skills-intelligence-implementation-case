# Interface specifications

Field-level mapping from each source to the canonical model (`skillslayer/canonical.py`), plus the two outbound interfaces. The shapes follow each system's public API conventions. Customer-specific names (report names, custom objects) are Norvane's choices and appear in *italics*.

## I1 Workday workers → `SourcePerson`

`GET /ccx/api/v1/{tenant}/workers?offset={n}&limit=100&updatedFrom={watermark}` returns `{"total": int, "data": [...]}`.

| Workday field | Canonical | Rule |
|---|---|---|
| `id` | `source_id` | Workday ID, the anchor key ([ADR-0003](../02-decisions/ADR-0003-workday-is-the-identity-anchor.md)) |
| `descriptor` | `display` | |
| `firstName`, `lastName` | `first`, `last` | |
| `primaryWorkEmail` | `email` | lower-cased for matching |
| `hireDate` | `hire_date` | the Workday hire date; after a transfer this is the *new* date |
| `jobProfile.id` | `job_id` | null → readiness finding `worker_without_job` |
| `manager.id` | `manager_id` | must exist and must not loop (readiness) |
| `location` | `country` | |
| *`legacySuccessFactorsId`* | `legacy_ids.successfactors` | a custom field Norvane added at the transfer; filled for some transferred people |
| `lastUpdated` | `updated` | used as the delta watermark |

## I2 Workday job profiles (RaaS) → `Job`

`GET /ccx/service/customreport2/{tenant}/ISU_SkillsLayer/`*`Job_Profiles_for_Skills_Layer`*`?format=json` returns `{"Report_Entry": [...]}`.

| Report column | Canonical | Rule |
|---|---|---|
| `Job_Profile_ID` | `job_id` | |
| `Job_Profile_Name` | `title` | duplicates by folded title → readiness finding |
| `Job_Description` | `description` | fewer than 25 words → `job_description_missing` |
| `Language` | `language` | informational; extraction does not trust it (all aliases are tried) |
| `Last_Updated` | `updated` | older than 3 years → `job_description_stale` |
| `Inactive` | `active` | |

The report is owned by the ISU and filtered to active job profiles in the pilot's supervisory organisations.

## I4 SuccessFactors (OData v2) → `SourcePerson`

`GET /odata/v2/User?$format=json`, then follow `d.__next` until it is absent. Dates arrive as `/Date(ms)/` literals in UTC milliseconds; `9999-12-31` means "open end".

| Entity.field | Canonical | Rule |
|---|---|---|
| `User.userId` | `source_id` | |
| `User.firstName`, `lastName` | `first`, `last` | umlauts kept; identity folds them |
| `User.email` | `email` | often still `@keldorf.example` after a transfer |
| `User.hireDate` | `hire_date` | the original Keldorf hire date |
| `User.status` | `active` | inactive users are kept, because they may be transferred people |
| `EmpJob.jobCode` | `job_id` | **effective-dated**: the record with `startDate ≤ as_of ≤ endDate` and the highest `seqNumber` wins |
| *`cust_AboutMe.aboutMe`* | `Activity(kind="about")` | free text; scanned for sensitive data **before** inference, quarantined if flagged |

## I7 Jira Cloud → `Activity`

`GET /rest/api/3/search/jql?jql=project = ELEC AND statusCategory = Done&fields=summary,assignee,resolutiondate,components&maxResults=100&nextPageToken={t}` returns `{"issues", "nextPageToken", "isLast"}`.

| Field | Canonical | Rule |
|---|---|---|
| `key` | `ref` | shown to the employee as evidence ("From Jira ELEC-1042") |
| `fields.summary` | `text` | the only text we read |
| `fields.assignee.accountId` | `person_key` | resolved through I8 users; hidden email → display-name rule |
| `fields.resolutiondate` | `on` | evidence decays with a half-life of 18 months; older than 3 years is ignored |
| `fields.components` | not used for inference | kept for the run log |
| `description`, `comment`, `worklog` | **never requested** | [ADR-0002](../02-decisions/ADR-0002-work-metadata-not-message-content.md); the eval checks the response holds only these four fields |

## I9 LMS completions (CSV) → `Activity`

`learner_email, course_id, course_title, completed_on`. UTF-8, comma-separated, header row. Linked by exact email only. Unknown emails go to the run log as unresolved and are never guessed.

## O1 Workday skills write-back

Operation plan (`skillslayer/writeback.py`):

| Field | Value |
|---|---|
| `op` | `add` or `remove` |
| `worker_id` | Workday ID |
| `skill_id`, `skill_name` | taxonomy ID and name |
| `key` | `sha256(op, worker, skill, taxonomy version)[:16]`: the idempotency key |

Rules: add only when validated and not already present (by ID or by name, case-insensitive). Remove only when the skill's source is `skills-layer` **and** the employee rejected it. Never touch `source = employee`.

## O3 Visier flat file

`EmployeeID, SkillID, SkillName, SkillCluster, Status, EffectiveDate`. One row per person and validated skill. `EmployeeID` is the Workday ID, or the SuccessFactors user ID for people who exist only there. `Status` is always `validated` ([ADR-0001](../02-decisions/ADR-0001-employees-validate-before-anything-leaves.md)); the eval counts <!--n:governance.with_controls.unvalidated_in_export-->0<!--/n--> other rows. A full file every night (not a delta), so Visier never drifts.

## O2 Teams validation card

Adaptive Card schema 1.5. Each suggestion is one `Input.ChoiceSet` (`accept`, `reject`, `unsure`), with at most 6 suggestions per card. A single `Action.Execute` with verb `validateSkills` sends the answers. Evidence is shown as "From Jira ELEC-1042: “…”", truncated to 90 characters. See `python -m skillslayer card W30579`.
