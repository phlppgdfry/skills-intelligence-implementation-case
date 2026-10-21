# Prompts and agents for implementation work

Reusable prompts an implementation consultant can run with Claude (Claude Code for anything with files and code, the Claude app for text). Each one states what goes in, what must never go in, and who reviews the output.

## 1. Interface mapping from an API sample

> You are helping map a customer's HR system into our canonical model. Below are the canonical fields (from `canonical.py`) and **five masked sample records** from `{system} {endpoint}`. Write: (1) a field mapping table with a rule per field, (2) the parser function, (3) unit tests that use the sample records, including one for each edge case you see (nulls, dates, effective dating). List every assumption you made as a question for the customer's admin.

- **In:** field names, 5 masked rows, the API's public documentation.
- **Never:** a full extract, real names or emails.
- **Review:** the customer's system admin answers the assumption questions; tests must pass on a second masked sample.

## 2. Readiness findings → steering summary

> Here is the readiness report JSON (scores, gate, findings with owners). Write a half-page summary for a CHRO: the verdict in one sentence, what blocks the pilot, who owns each fix, and the date we re-measure. No jargon. Do not change or round any number, and quote them exactly as they appear.

- **In:** the report JSON (counts and IDs, no free text).
- **Review:** the implementation consultant checks every number against the report.

## 3. Draft an updated job description

> Here is a job description last updated in {year} and the skills our taxonomy expects for this job family. Propose an updated description in {language}, at most 250 words, in the customer's style. Mark every sentence you added with [new] so the job owner can see what changed. Do not invent requirements the job owner did not state.

- **In:** the existing description (it is a company document, not personal data), the skill list.
- **Review:** the job owner edits and approves; HR job architecture publishes.

## 4. Field insight → product ticket

> Turn this field note into a product ticket with these sections: Problem, Evidence (reproducible example), Who it hits, Proposal (not a full solution), Done when. Keep it under 250 words.

- **In:** the field note and an anonymised example.
- **Review:** the implementation consultant, then the product manager.

## 5. Training material per audience

> Write a 20-minute session for {audience} on how the skills platform works, built around this one (fictional) example profile and its evidence. Include three questions this audience will ask and plain answers. Avoid: "algorithm", "model", "confidence score".

- **Review:** one person from the audience reads it before the session.

## Agents worth building (internal)

| Agent | Does | Human checkpoint |
|---|---|---|
| Readiness agent | runs the scan on a new extract, writes the report, opens remediation tickets with owners | consultant approves before anything goes to the customer |
| Run-log watcher | reads the nightly run log, flags drops, governance counts > 0, rejection spikes | on-call decides |
| Field-insight collector | turns notes from engagement channels into draft insights with examples | consultant curates every two weeks |

Each agent gets read access to what it needs and nothing else, and none of them writes to a customer system.
