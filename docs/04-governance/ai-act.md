# EU AI Act: where this implementation stands

*An implementer's working analysis for Norvane's legal team and DPO, not legal advice. Dates follow the AI Act as amended by the Digital Omnibus on AI. Published summaries put Annex III high-risk obligations at 2 December 2027. Legal must confirm the dates against the Official Journal before any decision depends on them.*

## Is it high-risk?

Annex III, point 4 lists AI systems in **employment and workers management**. That includes systems intended to be used to make decisions affecting promotion, to allocate tasks based on individual behaviour or personal traits, or to monitor and evaluate the performance and behaviour of workers.

| Use at Norvane | Likely reading |
|---|---|
| Suggesting skills to an employee, who validates them | supports the employee; on its own, arguably not a decision about them |
| Internal mobility matching shown to HR for vacancies | can influence promotion and task allocation → **treat as high-risk** |
| Aggregate workforce planning | not about individuals → lower concern |

**Recommendation: implement as if the system is high-risk** for the mobility use. That costs little extra, because most of the controls are already in the design, and it avoids a re-implementation when a regulator or a works council takes the stricter reading.

## Who has which obligations

- **Provider** (the platform vendor): risk management, data governance, technical documentation, logging, transparency to deployers, human-oversight design, accuracy and robustness, conformity assessment.
- **Deployer** (Norvane): use according to the instructions; assign **human oversight** to competent people; make sure input data is relevant; monitor operation; keep logs; and, before putting a high-risk system into use at the workplace, **inform workers' representatives and the affected workers** (Art. 26(7)).

## What the implementation already gives the deployer

| Deployer duty | How it is met here |
|---|---|
| Human oversight | employee validation ([ADR-0001](../02-decisions/ADR-0001-employees-validate-before-anything-leaves.md)); the HRBP decides on mobility; no automated ranking is shown to managers |
| Relevant input data | readiness gate ([ADR-0008](../02-decisions/ADR-0008-phased-rollout-behind-a-readiness-gate.md)); metadata-only sources ([ADR-0002](../02-decisions/ADR-0002-work-metadata-not-message-content.md)) |
| Monitoring | nightly run log, governance counts, rejection rate per division and language |
| Logs | run logs (13 months); validation decisions with timestamps |
| Inform worker representatives and workers | [works council plan](works-councils.md), [employee FAQ](employee-faq.md), before the pilot |
| AI literacy (Art. 4, in force since February 2025) | [training plan](../06-enablement/training-plan.md): every HR user and manager gets the "how the AI works" session |

## What is prohibited, and stays out

Art. 5(1)(f) prohibits AI systems that infer **emotions** of a natural person in the workplace, except for medical or safety reasons. Nothing here infers emotions, sentiment or personality. It is also one more reason not to read Teams messages.

## Open points for legal

1. Confirm the Annex III reading for mobility matching, with the vendor's provider documentation.
2. Agree with the vendor which logs the deployer needs and how long they are kept.
3. Decide whether the AI register lists the system as high-risk from the pilot on (recommended).
