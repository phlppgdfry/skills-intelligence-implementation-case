# Discovery workshop

Two half-days in week 1, on site in Antwerp, with one video session for the Dortmund team. The goal is to leave with a validated system map, a data access plan, a list of people who will decide, and the first readiness extracts requested.

## Agenda

| Block | Who | Output |
|---|---|---|
| 1. Why this, why now (45 min) | CHRO, HR director electrification, HRIS lead | the three use cases ranked; what "success in 6 months" means to each |
| 2. System landscape walk-through (90 min) | HRIS lead (Workday), SuccessFactors admin (Keldorf), IT integration architect, Atlassian admin | system map with owners, environments, data volumes, change windows |
| 3. Job architecture and skills today (60 min) | HR job architecture owner, two HR business partners | how jobs are maintained, who owns descriptions, what the current skills fields are used for |
| 4. Identity after the merger (45 min) | HRIS lead, SuccessFactors admin | how transferred people are recorded, which IDs exist where |
| 5. Privacy, works councils, security (60 min) | DPO, employee relations, IT security | legal basis, consultation timeline, security questionnaire owner |
| 6. People and adoption (45 min) | internal comms, two line managers, one engineer | how employees will hear about it, where they already are (Teams) |
| 7. Wrap-up (30 min) | everyone | decisions made, open questions with owners, the extract request |

## Questions I ask, and why

### Business

- Which decision will be made differently once skills data exists? Who makes it, and how often? *(A use case without a decision becomes a dashboard nobody opens.)*
- What happens today when a battery-systems vacancy opens? Walk me through the last one. *(This gives the real baseline for the mobility use case.)*
- Who will look at a person's skills: the person, their manager, HR, an analyst? *(This drives the visibility rules and the works council conversation.)*

### Systems

- Which Workday tenant do we get first, and how often is it refreshed from production? *(A sandbox with year-old data makes UAT meaningless.)*
- Is there an integration system user (ISU) pattern, and who approves security group changes? *(This often takes the longest.)*
- In SuccessFactors: which entities hold the job history, and is EmpJob effective-dated with future records? Is basic auth still on for the API, or OAuth 2.0 SAML bearer? *(Basic auth is being retired for SuccessFactors APIs, so we plan for OAuth.)*
- Jira: one cloud site or several? Do users hide their email? *(Hidden emails make identity matching harder; see [ADR-0003](../02-decisions/ADR-0003-workday-is-the-identity-anchor.md).)*
- Teams: may we install a bot app tenant-wide, and who approves it in the Teams admin centre?
- Visier: API or SFTP for custom data? Which effective-date convention?

### Data

- Who owns job descriptions, and when were they last reviewed? *(The readiness scan will tell us anyway. Asking first shows respect and surfaces the politics.)*
- Are there free-text fields where employees write about themselves? Has anyone looked at what is in them? *(Sensitive data is almost always there.)*
- How are contractors and interns represented: in the HCM, only in Jira, or not at all?

### Governance

- What did the works councils already hear about this? Who is the contact person on each side?
- Is there a DPIA template, and who signs it?
- Is there an AI policy or AI register? *(The AI Act requires AI literacy, and deployers of high-risk systems have obligations of their own.)*

### People

- Where do employees already spend their day? *(Teams, so the validation card goes there and not into another portal.)*
- What went wrong the last time HR rolled out a new tool?

## Extract request (sent the same day)

1. Workday: worker list with job profile, manager and hire date; job profiles with descriptions; the current skills field. Report owner: the ISU.
2. SuccessFactors: User, EmpJob (all records, including history), FOJobCode, the about-me custom object, the competency library.
3. Jira: user list and a count of resolved issues per project for the last 3 years (metadata only).
4. LMS: one month of completions as a CSV sample.
5. The consent and opt-out process, if one exists.

The extracts feed the [readiness scan](../03-readiness/readiness-report.md) in week 2.
