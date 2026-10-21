# Engagement brief: Norvane Group

*Fictional customer. Written as the internal kick-off brief that a professional services team would share with the customer's sponsor after the sales handover.*

## Situation

Norvane Group (Antwerp, about 9,000 people) builds electrification equipment for industry: switchgear, battery storage and EV charging for fleets. In 2025 it bought **Keldorf Systems** (Dortmund and Kassel, about 1,600 people), which brings embedded software and power-electronics expertise.

The deal closed on 1 April 2025. Eighteen months later the HR landscape still reflects two companies:

| | Norvane | Keldorf |
|---|---|---|
| HCM | Workday (BE, NL, FR sites) | SAP SuccessFactors (DE), migration to Workday planned for 2027 |
| Job architecture | ~400 job profiles, EN and NL, some FR at the Wavre site | ~250 job codes, mostly DE |
| Skills today | a free-typed skills field on the worker profile, rarely maintained | a German competency library, used in annual reviews |
| Work systems | Jira (engineering), Microsoft Teams (everyone) | Jira (same Atlassian cloud site since 2025), Teams |
| Learning | LMS export as CSV | same LMS since 2025 |
| People analytics | Visier | — |
| Employee representation | works council (*ondernemingsraad*) and union delegation in BE | *Betriebsrat* in DE |

Some Keldorf employees have already moved to Norvane legal entities and exist **in both HCMs**: in SuccessFactors with their old address, in Workday with a new one.

## What the customer bought, and why

Norvane licensed a skills intelligence platform: an AI layer that infers skills from HR and work data, keeps them current, and makes them usable in the HR systems. The CHRO's business case has three uses:

1. **Electrification workforce plan.** The order book needs roughly 120 more people with high-voltage, battery and charging-infrastructure skills by 2028. The plan has to show how many of them can come from inside.
2. **Internal mobility.** When a vacancy opens, show the people who already have most of the skills, across both companies.
3. **One skills language after the merger.** One taxonomy instead of a Norvane skills field and a Keldorf competency library.

## What we are asked to do

Turn the licence into production: design and build the integrations, prepare the data, make it safe and acceptable for employees and works councils, train the people who will run it, and hand over a working operation.

## Scope

| In scope | Out of scope (for now) |
|---|---|
| Workday: workers, job profiles, skills library (read); skills on the worker profile (write) | Workday Recruiting, compensation data |
| SuccessFactors: users, EmpJob, job codes, a custom about-me object, competency library (read) | Writing back to SuccessFactors before the 2027 migration decision (see [ADR-0003](../02-decisions/ADR-0003-workday-is-the-identity-anchor.md)) |
| Jira Cloud: resolved issues, four fields only | Confluence, GitHub, ServiceNow (wave 2 candidates) |
| Microsoft Teams: validation card for employees | Reading Teams or Slack messages (see [ADR-0002](../02-decisions/ADR-0002-work-metadata-not-message-content.md)) |
| LMS completions (CSV over SFTP) | |
| Visier: validated skills as a flat file | |
| Readiness scan, governance, works council support, training, hypercare | Organisational redesign, job architecture rewrite (the customer's HR team owns this; we give them the findings) |

The first wave covers the **electrification division** (BE + DE). The synthetic dataset in this repository models that 266-person slice.

## Constraints

- **Works councils first.** Belgian CAO 39 requires informing and consulting on new technology with collective consequences, and CAO 81 covers monitoring of electronic communication. In Germany, BetrVG §87(1) no. 6 gives the *Betriebsrat* co-determination over technical systems that can monitor behaviour or performance. No production data flows before both bodies have agreed. See [works councils](../04-governance/works-councils.md).
- **Employees confirm their own skills.** The CHRO promised this to both councils during the merger. It became [ADR-0001](../02-decisions/ADR-0001-employees-validate-before-anything-leaves.md).
- **No go-live in December.** Year-end closing and works council elections are both in Q4.
- **Four languages.** Job descriptions and profiles are in EN, NL, DE and FR.

## How we will know it worked

See [success criteria](success-criteria.md). In short: the pilot gate passes, a majority of invited employees respond to their validation card, HR business partners use the skills data in at least ten real mobility cases, and the workforce plan uses validated internal supply.
