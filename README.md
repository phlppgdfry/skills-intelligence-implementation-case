# Skills intelligence, from promise to production

**An end-to-end implementation case: connecting a skills intelligence layer to a merged enterprise's HR and work systems.** It covers the whole engagement, from discovery and an AI-readiness scan through integration architecture, governance and works councils, a phased rollout plan and enablement, down to a working implementation toolkit. Every claim it makes is measured by an eval suite that runs offline in CI.

> *"We bought a skills platform. Now make it work in our landscape: two HR systems after the merger, Jira, Teams, and a works council in two countries."* (the customer's brief, in one sentence)

[![CI](https://github.com/phlppgdfry/skills-intelligence-implementation-case/actions/workflows/ci.yml/badge.svg)](../../actions/workflows/ci.yml)

The customer, **Norvane Group**, is fictional: a Belgian electrification manufacturer with about 9,000 people that bought the German company **Keldorf Systems**. Norvane runs on Workday and Keldorf still runs on SAP SuccessFactors. Engineering works in Jira, everyone works in Microsoft Teams, and people analytics runs on Visier. All data is synthetic: the dataset models the 266-person electrification division that goes first. The skills engine in `skillslayer/` is a transparent stand-in that I wrote. It is **not** any vendor's model. It exists so that everything around the model can be built and measured: connectors, identity, readiness, governance, validation, write-back and evals. That surrounding work is the implementation consultant's job.

---

## The engagement in one paragraph

Norvane wants one view of skills across both companies, for internal mobility and for its electrification workforce plan. The hard part is not the AI. The hard part is **the landscape**: two HCMs with overlapping people after the merger, job descriptions in four languages, Jira users with hidden emails, sensitive data in free-text fields, and works councils in Belgium and Germany. The approach has four steps. First, a **readiness scan** before any date is promised. Then **governance built into the pipeline**, not bolted on: opt-outs and quarantine apply *before* inference. Then **employees validate** every inferred skill in Teams before anything reaches Workday or a manager. Finally, a **write-back** that is idempotent and never touches what an employee typed in.

## What the evals show

| Question the implementation had to answer | Result | Decision |
|---|---|---|
| Is the customer ready for a pilot? | **No, not yet.** The scan found all <!--n:readiness.planted-->22<!--/n--> planted data problems with <!--n:readiness.false_alarm_count-->0<!--/n--> false alarms. Job architecture scores <!--n:readiness.scores.job_architecture-->70%<!--/n-->, below the <!--n:readiness.thresholds.job_architecture-->85%<!--/n--> pilot gate (missing, stale and duplicate job profiles). Workforce data (<!--n:readiness.scores.workforce_data-->97.5%<!--/n-->) and identity (<!--n:readiness.scores.identity-->94.4%<!--/n-->) pass. | [Readiness report](docs/03-readiness/readiness-report.md), [ADR-0008](docs/02-decisions/ADR-0008-phased-rollout-behind-a-readiness-gate.md) |
| Does a multilingual taxonomy matter? | Canonical English names alone find <!--n:extraction.A.all.recall-->41.6%<!--/n--> of skills, and only <!--n:extraction.A.lang:de.recall-->29.1%<!--/n--> in German texts. That would quietly disadvantage the Keldorf employees. With aliases in four languages recall is <!--n:extraction.B.all.recall-->96.2%<!--/n-->, and the language gap shrinks from <!--n:extraction.A.language_recall_gap-->18.5%<!--/n--> to <!--n:extraction.C.language_recall_gap-->4.7%<!--/n-->. | [ADR-0010](docs/02-decisions/ADR-0010-multilingual-taxonomy-before-go-live.md) |
| Do negation and ambiguity guards pay off? | Precision goes from <!--n:extraction.B.all.precision-->93.3%<!--/n--> to <!--n:extraction.C.all.precision-->98.1%<!--/n--> ("no experience with Docker is needed", "I would like to learn Kubernetes", "you excel at…"). Negation *after* the mention is still missed; that is logged as product feedback. | [Field insights](docs/07-product-feedback/field-insights.md) |
| What should we ask employees to confirm? | Role-only suggestions are right <!--n:profiles.policies.role_only.suggested.precision-->56.4%<!--/n--> of the time, which means <!--n:profiles.policies.role_only.wrong_asks_per_person-->1.75<!--/n--> wrong questions per person. Corroborated suggestions are right <!--n:profiles.policies.corroborated.suggested.precision-->90.6%<!--/n--> of the time (<!--n:profiles.policies.corroborated.wrong_asks_per_person-->0.17<!--/n--> wrong per person). After simulated validation, <!--n:profiles.policies.corroborated.validated.precision-->100%<!--/n--> of what reaches Workday is right. | [ADR-0009](docs/02-decisions/ADR-0009-corroborated-suggestions-by-default.md), [ADR-0001](docs/02-decisions/ADR-0001-employees-validate-before-anything-leaves.md) |
| Can we link people across both HCMs and Jira without wrong merges? | <!--n:identity.rules.false_merges-->0<!--/n--> wrong merges, against <!--n:identity.baseline_name_only.false_merges-->1<!--/n--> for name matching (a homonym) and a recall of only <!--n:identity.baseline_email_only.recall-->55.3%<!--/n--> for email matching. <!--n:identity.review_queue-->22<!--/n--> records go to a data steward. Once the queue is worked, recall is <!--n:identity.after_steward.recall-->100%<!--/n-->. | [ADR-0003](docs/02-decisions/ADR-0003-workday-is-the-identity-anchor.md) |
| Do the connectors survive real tenants? | Every record arrives through <!--n:connectors.faults_injected-->5<!--/n--> injected 429s and 503s, and a 401 is not retried. A delta run returns exactly the <!--n:connectors.delta_changed-->7<!--/n--> changed workers, and Jira returns only the four fields we asked for. | [ADR-0006](docs/02-decisions/ADR-0006-delta-sync-with-weekly-reconciliation.md), [ADR-0002](docs/02-decisions/ADR-0002-work-metadata-not-message-content.md) |
| Is the write-back safe to re-run? | The first run makes <!--n:writeback.adds-->207<!--/n--> adds and <!--n:writeback.removes-->1<!--/n--> remove. A retried batch applies <!--n:writeback.replayed_batch_applied-->0<!--/n--> operations, the second run plans <!--n:writeback.second_run_ops-->0<!--/n-->, and all <!--n:writeback.employee_skills_before-->56<!--/n--> employee-entered skills are untouched. | [ADR-0007](docs/02-decisions/ADR-0007-write-back-owns-only-its-own-skills.md) |
| Do the governance controls actually hold? | All controls on: <!--n:governance.ablation.all controls.total-->0<!--/n--> leaks. Without the opt-out filter there are <!--n:governance.ablation.no opt-out filter.total-->13<!--/n-->, without quarantine <!--n:governance.ablation.no quarantine.total-->6<!--/n-->, and with inferred skills sent downstream <!--n:governance.ablation.inferred skills downstream.total-->157<!--/n--> unvalidated rows land in the analytics export. | [Governance](docs/04-governance/gdpr-and-dpia.md) |
| How much of the customer's own library maps automatically? | <!--n:crosswalk.auto_coverage_of_in_scope-->89.4%<!--/n--> of in-scope entries map automatically, at <!--n:crosswalk.auto_precision-->100%<!--/n--> precision. Soft skills, languages and licences stay customer attributes. <!--n:crosswalk.steward_queue-->23<!--/n--> entries need a steward. | [ADR-0005](docs/02-decisions/ADR-0005-map-customer-libraries-do-not-replace-them.md) |

These numbers come from synthetic data and a deterministic stand-in engine. They test **the implementation**: integration design, identity rules, readiness checks, governance and write-back logic. They say nothing about any vendor's model quality. Employee answers are simulated with stated assumptions. [EVIDENCE.md](EVIDENCE.md) separates what is executed, what is simulated and what was not done.

## Read it by role

| You are | Start with | Then |
|---|---|---|
| Customer CHRO / sponsor (5 min) | [Engagement brief](docs/00-engagement/brief.md) | [Implementation plan](docs/05-delivery/implementation-plan.md), [readiness report](docs/03-readiness/readiness-report.md) |
| HRIS / integration lead | [Integration architecture](docs/01-architecture/integration-architecture.md) | [Interface specs](docs/01-architecture/interface-specs.md) · [environments and security](docs/01-architecture/environments-and-security.md) · [10 ADRs](docs/02-decisions/README.md) |
| DPO / works council | [GDPR and DPIA](docs/04-governance/gdpr-and-dpia.md) | [Works councils](docs/04-governance/works-councils.md) · [AI Act](docs/04-governance/ai-act.md) · [employee FAQ](docs/04-governance/employee-faq.md) |
| HR business partner | [How the AI works](docs/06-enablement/how-the-ai-works.md) | [Training plan](docs/06-enablement/training-plan.md) · [data steward guide](docs/06-enablement/data-steward-guide.md) |
| Project manager | [Implementation plan](docs/05-delivery/implementation-plan.md) | [RACI](docs/05-delivery/raci.md) · [UAT](docs/05-delivery/test-strategy-and-uat.md) · [cutover and hypercare](docs/05-delivery/cutover-and-hypercare.md) · [risks](docs/05-delivery/risk-register.md) |
| Product / engineering (vendor side) | [Field insights](docs/07-product-feedback/field-insights.md) | [Product tickets](docs/07-product-feedback/product-tickets.md) |
| Curious how it was made | [AI-first delivery](docs/08-ai-first/how-this-was-built.md) | [Prompts and agents](docs/08-ai-first/prompts-and-agents.md) |

## Run it (no API key, no dependencies)

Python 3.11 or newer.

```bash
python -m unittest discover -s tests -t .     # 27 unit and integration tests
python -m evals.run --gate                    # eight eval suites + the release gate
python -m skillslayer readiness               # AI-readiness scorecard and findings
python -m skillslayer sync --simulate         # full run against mock tenants, with a run log
python -m skillslayer profile W30579          # one person's skills and the evidence behind them
python -m skillslayer card W30579             # the Teams validation card (Adaptive Card JSON)
python -m skillslayer crosswalk               # how the customer's own libraries map
python -m skillslayer mocks                   # mock Workday / SuccessFactors / Jira APIs on :8787
python scripts/make_data.py --check           # synthetic data is reproducible
python scripts/build.py                       # refresh every number in docs and site
```

The site (`site/index.html`, plus `site/demo/?tour` for a two-minute guided tour) reads `site/data/`, which `build.py` writes.

## What is in the box

```
docs/
  00-engagement/    brief, discovery workshop, stakeholder map, success criteria
  01-architecture/  integration architecture, data flows, interface specs, identity, environments & security
  02-decisions/     10 ADRs: validation first, metadata not messages, Workday as anchor, ...
  03-readiness/     AI-readiness report (generated numbers) and remediation plan
  04-governance/    GDPR + DPIA, EU AI Act, works councils (BE/DE/NL), employee FAQ
  05-delivery/      implementation plan, RACI, test strategy & UAT, cutover & hypercare, risks, status report
  06-enablement/    how the AI works (plain language), training plan, data steward guide
  07-product-feedback/  field insights from the engagement, written-up product tickets
  08-ai-first/      how this was built with Claude Code, reusable prompts and their guardrails
skillslayer/        the toolkit: connectors, identity, readiness, inference stand-in, governance,
                    validation card, write-back, crosswalk, analytics export, CLI
skillslayer/mock/   mock tenants with real failure modes (429, 503, paging, hidden emails)
evals/              eight suites, simulated employees, thresholds (the release gate), report
data/               synthetic landscape (sources/) and the generator's gold labels (gold/)
site/               landing page and demo with guided tour
```

## Engineering practice shown

- **Generator and code under test only meet in the eval.** `scripts/make_data.py` plants the truth: who is who, which skills a text really mentions, which defects exist. It writes that to `data/gold/`, which `skillslayer/` never reads.
- **Ablations, not assertions.** Each design choice is shown by turning it off: taxonomy configs A/B/C, four suggestion policies, three governance controls, and identity rules against three baselines.
- **The docs cannot go stale.** Every number in this README and in `docs/` sits between `<!--n:…-->` markers, and `build.py --check` fails CI when one drifts.
- **Failure modes are part of the fixture.** The mock tenants return 429 with Retry-After, 503 on a page, server-side paging (`__next`, `nextPageToken`), effective-dated records and hidden emails.
- **Privacy by construction.** Jira is asked for four fields, never descriptions or comments. Free text with health, union or national-ID data is quarantined before inference. Opt-outs are applied before evidence is built, not filtered afterwards.

## Honest scope

All of this was built with Claude Code as an AI-first exercise ([how](docs/08-ai-first/how-this-was-built.md)). It has not been connected to a real Workday, SuccessFactors or Jira tenant, and it has not been reviewed by a works council or a DPO. The legal notes are an implementer's working analysis, not legal advice. See [EVIDENCE.md](EVIDENCE.md).
