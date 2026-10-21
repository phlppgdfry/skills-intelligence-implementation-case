# GDPR and DPIA (lite)

*This is an implementer's working analysis, written for Norvane's DPO. It is not legal advice. The DPO owns the final DPIA.*

## Roles

- **Norvane Group (and Keldorf as a group entity)**: controller. They decide on the purposes: workforce planning and internal mobility.
- **Skills platform vendor**: processor, under a DPA with sub-processor list, EU hosting and the security annex.
- **Implementation partner**: processor or sub-processor for the configuration and hypercare work. It has no access beyond what each task needs, and access is logged.

## Purposes and legal basis

| Purpose | Data | Legal basis (proposal) | Notes |
|---|---|---|---|
| Infer skill suggestions for the employee | job profile, resolved Jira summaries, course completions, profile text | legitimate interest (Art. 6(1)(f)), with a documented balancing test | consent is not a good basis in an employment relationship, because it is rarely freely given; an **opt-out** is offered anyway as an extra safeguard |
| Store validated skills on the HCM profile | validated skills | legitimate interest | the employee confirmed each one |
| Workforce planning in aggregate | validated skills, job, org unit | legitimate interest | aggregated in Visier; minimum group size 10 in reports |
| Internal mobility matching | validated skills | legitimate interest | the employee can see their own matches; HR sees them only for open vacancies the employee applied to or opted into |

## Balancing test, in short

- **Interest:** better internal mobility and a credible workforce plan. Employees benefit too, through visibility for roles they would not have found.
- **Necessity:** the purpose cannot be reached with job profiles alone. Role-only skills are right only <!--n:profiles.policies.role_only.suggested.precision-->56.4%<!--/n--> of the time in our eval.
- **Safeguards that tip the balance:** metadata only, no message content ([ADR-0002](../02-decisions/ADR-0002-work-metadata-not-message-content.md)); employee validation before any use ([ADR-0001](../02-decisions/ADR-0001-employees-validate-before-anything-leaves.md)); opt-out; quarantine of special-category data; no automated decisions; transparency in four languages.

## Data minimisation, measured

| Control | Where | Evidence |
|---|---|---|
| Jira: four fields only | `sources/connectors.py: JIRA_FIELDS` | connector eval: fields in the response ⊆ the four (<!--n:connectors.jira_fields_minimal-->yes<!--/n-->) |
| Opt-out applied before inference | `pipeline.run` | <!--n:governance.with_controls.optout_with_evidence-->0<!--/n--> opted-out people with evidence; <!--n:governance.ablation.no opt-out filter.total-->13<!--/n--> leaks with the filter off |
| Special-category data quarantined | `readiness.SENSITIVE` | <!--n:governance.with_controls.quarantined_text_used-->0<!--/n--> quarantined texts used; <!--n:governance.ablation.no quarantine.total-->6<!--/n--> evidence items from them with quarantine off |
| Only validated skills downstream | `pipeline.analytics_export` | <!--n:governance.with_controls.unvalidated_in_export-->0<!--/n--> unvalidated rows; <!--n:governance.ablation.inferred skills downstream.total-->157<!--/n--> with the rule off |
| The run log holds no free text | design | code review checklist |

## Article 9 data

Free text sometimes holds health or union information, written by the employee themselves. We **do not process** it: the scan flags it, the record is quarantined before inference, and the DPO informs HR to remove it at the source. The scan found <!--n:readiness.by_check.sensitive_free_text.found-->4<!--/n--> such records in the pilot data.

## Article 22

No decision with legal or similarly significant effects is taken automatically. Suggestions are questions to the employee. Mobility matches are input for an HR business partner who talks to the person. This is written into the works council agreement as well.

## Data subject rights

- **Access:** the employee sees all their suggestions, the evidence behind each, and what was written where (the platform UI, plus the HCM profile).
- **Rectification:** reject a skill at any time, and the write-back removes it if we wrote it ([ADR-0007](../02-decisions/ADR-0007-write-back-owns-only-its-own-skills.md)).
- **Objection:** the opt-out stops all processing from the next nightly run. Existing inferred data is deleted within 30 days. Validated skills stay on the HCM profile, because the employee entered them through validation; they can remove them there.

## Retention

| Data | Kept |
|---|---|
| Evidence sentences | 3 years rolling (evidence older than that has no weight anyway) |
| Suggestions not answered | deleted after the card expires + 90 days |
| Rejected skills | kept as a rejection for 12 months so they are not asked again, then deleted |
| Run logs (counts and IDs) | 13 months |

## DPIA trigger and risks

A DPIA is needed: systematic evaluation of employees using new technology. Main risks and mitigations:

| Risk | Likelihood × impact | Mitigation | Residual |
|---|---|---|---|
| Profiling felt as surveillance | medium × high | metadata only, validation, works council agreement, FAQ | low |
| Wrong skills used in a mobility decision | medium × medium | validated only downstream; HRBP talks to the person | low |
| Bias against non-English speakers | medium × high | multilingual taxonomy gate ([ADR-0010](../02-decisions/ADR-0010-multilingual-taxonomy-before-go-live.md)); per-language recall in UAT | low |
| Bias against people without Jira | high × medium | role-based second card ([ADR-0009](../02-decisions/ADR-0009-corroborated-suggestions-by-default.md)); not used to rank people | medium: monitored |
| Special-category data processed | low × high | quarantine before inference | low |
| Wrong person merged | low × high | identity rules, steward queue, 0 wrong merges in eval | low |
