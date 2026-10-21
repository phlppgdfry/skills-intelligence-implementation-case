# How this was built: AI-first delivery

The role this case was written for asks for "AI-first ways of working (internal agents, Claude Code, and beyond) as your real leverage", and for compressing knowledge work from days to hours. This repository is that working style applied to an implementation, so this page says plainly how it was made.

## What was done with Claude Code

The whole repository was produced in an AI-first session with Claude Code. That covers the synthetic landscape generator, the toolkit, the mock tenants, the tests, the eval suites, the build script, the documentation and the site. The human part was choosing the scope and the customer scenario, deciding what had to be true for the case to be credible (fictional, measured, honest about limits), and reviewing the result.

## Where AI-first actually compresses the work in an implementation

| Task | Traditional | AI-first | What makes it safe |
|---|---|---|---|
| First draft of interface specs from API docs and a sample extract | 2–3 days | 2–3 hours | every field mapping is tested against a real (masked) record before it counts |
| Readiness scan on a new customer's extract | a week of spreadsheet work | an afternoon: generate checks, run them, review findings with the customer | checks are code, rerunnable, with planted-defect tests |
| Mock tenants for SIT before access is granted | usually skipped | an hour | the mocks model *failure modes* (429, 503, paging), not just happy paths |
| Discovery notes → decision log → ADRs | days of writing after the workshop | same day | ADRs are reviewed by the decision owner; numbers come from evals, not from the model |
| Training material per audience | a week | a day | built from the customer's own screens and data; an HRBP reviews it |
| Field insights → product tickets | often never written | minutes per insight | each ticket carries a reproducible example |

## Guardrails with customer data

AI-first does not mean customer data goes into any AI tool.

1. **No customer personal data in tools that the customer has not approved.** Generators, checks and mocks are built on synthetic data like the data in this repo, and run on the real extract inside the customer's agreed processing environment.
2. **Prompts get structure, never records.** For example: "here are the column names and 5 masked rows; write the mapping and the tests". Not "here is our HR export".
3. **The model drafts, a person decides.** Every ADR, every customer-facing text and every write-back plan has a named human reviewer.
4. **Numbers come from code, not from prose.** Every figure in this repository's docs comes from the eval report through `build.py`. A model can't "round up" a result in a sentence.
5. **Log what the AI did.** Commit messages and the decision log say what was generated and what was reviewed.

## What this does not prove

It shows a way of working and a design. It does not show that the author has run a Workday or SuccessFactors implementation at a customer: nothing here was connected to a real tenant ([EVIDENCE.md](../../EVIDENCE.md)).
