# Stakeholder map

| Stakeholder | What they care about | What they fear | How we involve them |
|---|---|---|---|
| **CHRO** (sponsor) | workforce plan for electrification; a credible post-merger story | an AI project that embarrasses HR in front of the councils | monthly steering, one-page status, the readiness gate as an honest checkpoint |
| **HR director, electrification** (business owner) | filling HV and battery roles from inside | another tool for HR business partners to maintain | co-designs the mobility workflow; owns pilot success criteria |
| **HRIS lead (Workday)** | tenant stability, security, no surprise integrations | an integration that writes garbage onto worker profiles | design authority for every Workday change; reviews the write-back dry run ([ADR-0007](../02-decisions/ADR-0007-write-back-owns-only-its-own-skills.md)) |
| **SuccessFactors admin (Keldorf)** | keeping Keldorf running until the migration | being forgotten, or getting extra work just before the migration | read-only scope, one OData user, no write-back ([ADR-0003](../02-decisions/ADR-0003-workday-is-the-identity-anchor.md)) |
| **IT integration architect** | standards: secrets, network, monitoring | shadow integrations nobody can support | owns the environments and security sign-off ([environments](../01-architecture/environments-and-security.md)) |
| **Atlassian admin** | Jira performance, API rate limits | scraping that slows Jira down | API token for one service account, four fields, nightly window |
| **DPO** | lawful basis, minimisation, DPIA | special-category data in free text; profiling claims | co-writes the DPIA, approves the quarantine rules ([GDPR and DPIA](../04-governance/gdpr-and-dpia.md)) |
| **Works council BE / Betriebsrat DE** | no performance surveillance; employees in control | managers ranking people on inferred skills | early information, a written agreement, the employee FAQ, a demo of the validation card ([works councils](../04-governance/works-councils.md)) |
| **Line managers** | finding people, less admin | being judged on their team's "skills score" | see validated skills only; short training |
| **Employees** | fairness, control, career chances | being surveilled through Jira and Teams | the validation card, opt-out, FAQ in four languages ([employee FAQ](../04-governance/employee-faq.md)) |
| **People analytics (Visier)** | a clean, dated feed | inferred noise in reports | validated-only flat file ([interface specs](../01-architecture/interface-specs.md)) |
| **Vendor product and engineering** | what breaks in the field | one-off customer hacks | structured field insights ([field insights](../07-product-feedback/field-insights.md)) |

## Power and interest

```
            high interest
                 |
  Works councils | CHRO, HR director
  Employees      | HRIS lead, DPO
 ----------------+----------------- high power
  Line managers  | IT architect
  Visier team    | SF admin, Atlassian admin
                 |
            low interest
```

Works councils are in the high-interest quadrant, and they have veto-like power in Germany. They are treated as high power throughout.
