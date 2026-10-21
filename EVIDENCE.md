# Evidence: what is executed, simulated and not done

| Claim | Status | Where |
|---|---|---|
| Connectors read Workday-, SuccessFactors- and Jira-shaped APIs over real HTTP, with paging, retries on 429/503, no retry on 4xx | **executed** against local mock tenants | `skillslayer/sources/`, `skillslayer/mock/servers.py`, `tests/test_integration.py`, eval `connectors` |
| Delta sync returns exactly the changed workers | **executed** (mock) | eval `connectors`: <!--n:connectors.delta_fetched-->7<!--/n-->/<!--n:connectors.delta_changed-->7<!--/n--> |
| Identity rules: <!--n:identity.rules.false_merges-->0<!--/n--> wrong merges, <!--n:identity.rules.recall-->87.2%<!--/n--> recall before stewarding | **executed** on synthetic data with planted transfers, homonyms, umlaut variants and hidden emails | eval `identity` |
| Readiness scan finds <!--n:readiness.found-->22<!--/n-->/<!--n:readiness.planted-->22<!--/n--> planted problems | **executed** on synthetic data | eval `readiness` |
| Extraction ablation A/B/C | **executed** on <!--n:extraction.texts-->1,503<!--/n--> generated texts with gold labels | eval `extraction` |
| Suggestion policies and validated precision | **simulated**: employee answers come from `evals/simulate.py` (20% no response; 90/5/5 for true skills, 85/10/5 for wrong ones) | eval `profiles` |
| Write-back is idempotent and leaves employee skills alone | **executed** against an in-memory target that remembers idempotency keys | eval `writeback`, `tests/test_units.py` |
| Governance controls hold, with ablation | **executed** | eval `governance` |
| Teams validation card | **generated** (valid Adaptive Card 1.5 JSON); **not** deployed to Teams or rendered in a Teams client | `skillslayer/teams.py` |
| Field mappings match real Workday, SuccessFactors and Jira APIs | **not verified against real tenants.** Shapes follow public API conventions (Workday REST and RaaS, SuccessFactors OData v2, Jira Cloud `search/jql`). Real tenants have customer-specific fields and security. | `docs/01-architecture/interface-specs.md` |
| The skills engine | **a stand-in** written for this case (alias matching + guards + noisy-OR fusion). It is not a vendor's model and says nothing about any vendor's accuracy. | `skillslayer/inference.py` |
| Legal analysis (GDPR, AI Act, CAO 39/81, BetrVG, WOR) | **working notes**, not reviewed by a lawyer, DPO or works council | `docs/04-governance/` |
| Plan, RACI, cutover, training | **written**, not executed with a real customer | `docs/05-delivery/`, `docs/06-enablement/` |

## How the numbers stay honest

- `scripts/make_data.py` plants the truth into `data/gold/`. The toolkit never reads it; only `evals/` does. `make_data.py --check` proves the data is reproducible.
- `evals/thresholds.json` is the release gate. CI fails when a threshold breaks.
- `scripts/build.py --check` fails CI when any number in the docs or the site differs from the latest eval report.

## Who did what

Built AI-first with Claude Code ([how](docs/08-ai-first/how-this-was-built.md)). The author has not run this implementation at a customer.
