# Training plan

Enablement is not a training session at the end. Each audience gets what it needs to do its own part, at the moment it needs it, and the customer team ends up able to run the platform without us.

| Audience | Goal | Format | Length | When | Material | Success measure |
|---|---|---|---|---|---|---|
| **HRIS team** (Workday, SF) | run, monitor and change the integrations | hands-on in the build environment, pairing during SIT | 3 × 2 h + pairing | weeks 6–10 | [interface specs](../01-architecture/interface-specs.md), run log, cutover runbook | runs one nightly review alone in hypercare week 2 |
| **Data stewards** (2 people) | work the identity and crosswalk queues | walkthrough + 30 real cases together | 2 h | week 5 | [data steward guide](data-steward-guide.md) | queue < 2% without help |
| **HR business partners** | explain the tool, use skills in mobility cases | [how the AI works](how-the-ai-works.md) + scenario workshop (UAT scenario 1) | 2 h | week 10 | FAQ, scenarios | 10 mobility cases in the pilot (S7) |
| **Managers (pilot)** | support their team, not judge it | 20-min Teams session, recorded | 20 min | week 11 | how the AI works, FAQ | few "can I see what they rejected?" tickets |
| **Employees** | understand and answer the card | the card itself + FAQ + 2-min video in 4 languages | 2 min | at go-live | [employee FAQ](../04-governance/employee-faq.md) | response ≥ 60% (S3) |
| **Works council members** | test the safeguards themselves | live demo with a test user; Q&A with the DPO | 90 min | week 3 and week 9 | [works councils](../04-governance/works-councils.md), card demo | agreement signed (S8) |
| **Steering committee** | read the scorecard and decide | 15 min in steering | 15 min | week 4 | [readiness report](../03-readiness/readiness-report.md) | gate decisions made on the numbers |

## Principles

- **Real data, real screens.** Every session uses the customer's own scorecard, a real (consenting) employee's card in UAT, and the customer's own job profiles.
- **Teach the failure modes.** HRBPs see a wrong suggestion and why it happened, so they can explain it.
- **Train-the-trainer for scale.** Two HRBPs per division run the sessions in wave 2, with the implementation team observing the first time.
- **AI literacy counts.** The HR and manager sessions cover what the system can and cannot do, which also serves the AI Act's AI literacy duty ([AI Act](../04-governance/ai-act.md)).
