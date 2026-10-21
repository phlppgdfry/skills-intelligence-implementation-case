# Risk register

| # | Risk | P | I | Owner | Mitigation | Trigger |
|---|---|---|---|---|---|---|
| K1 | German works agreement takes longer than 6 weeks | M | H | employee relations | start in week 2; budget an external expert for the council; go live per legal entity (BE first) | no draft by week 6 |
| K2 | Job architecture not fixed in time | M | H | HR director | gate per sub-population ([ADR-0008](../02-decisions/ADR-0008-phased-rollout-behind-a-readiness-gate.md)) | gate fails in week 7 |
| K3 | Low response to validation cards | M | H | internal comms | Teams, not a portal; short card; manager nudge without content; corroborated-first ([ADR-0009](../02-decisions/ADR-0009-corroborated-suggestions-by-default.md)) | < 30% after 7 days |
| K4 | Security review blocks the Teams app | L | H | IT architect | app permissions limited to sending cards; review pack sent in week 2 | open questions in week 4 |
| K5 | Sandbox refresh wipes integration security | M | M | HRIS lead | re-apply step in the runbook; check before SIT and UAT | SIT-01 fails with 403 |
| K6 | Employees feel surveilled through Jira | M | H | employee relations | metadata only, FAQ, council demo | questions in the council |
| K7 | Wrong merges after more transfers | L | H | data steward | identity rules; weekly steward queue; transfer process sets the Workday cross-reference | a wrong-person report from an employee |
| K8 | Vendor model weaker in German than in English on Norvane's texts | M | M | impl. consultant | per-language check in UAT ([ADR-0010](../02-decisions/ADR-0010-multilingual-taxonomy-before-go-live.md)); field insight with examples | gap > 6 points |
| K9 | Scope creep: "can it also do performance?" | M | H | CHRO | purposes fixed in the agreement; change = new consultation | request in steering |
| K10 | SuccessFactors migration date moves | M | M | HRIS lead | [ADR-0003](../02-decisions/ADR-0003-workday-is-the-identity-anchor.md) review trigger | migration plan changes |
