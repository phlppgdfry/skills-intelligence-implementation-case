# Field insights

What this implementation showed that the product could do better. Each insight is written so that a product manager can act on it without having been in the room: what happened, how often, what it costs, what we did instead, and the ask.

Severity × frequency gives a rough priority. "Frequency" is how often it would hit *other* customers, not just Norvane.

| ID | Insight | Evidence | Workaround at Norvane | Ask | Impact | Frequency |
|---|---|---|---|---|---|---|
| FI-01 | **Negation after the mention is missed.** "Python is not part of this role" counts as Python. | the remaining extraction false positives in config C are all this pattern; unit test `test_known_limit_trailing_negation` | none on the customer side; HR is asked to avoid the phrasing in job profiles | handle post-mention negation cues per language | M | H: job profiles often list what a role is *not* |
| FI-02 | **German compounds hide skills.** "Projektmanagementerfahrung", "Ladeinfrastrukturprojekte" are not found by alias matching. | the wild forms in the generator are the extraction false negatives | none | compound splitting or sub-word matching for DE (and NL) | M | H for DACH customers |
| FI-03 | **The readiness gate should live in the product.** We built the scan as a customer-side script, but every implementation needs it in week 2. | 22/22 planted defects found; the job-architecture verdict changed the plan | the script in this repo | a "data maturity" report with per-dimension gates and owner fields, exportable for steering | H | H |
| FI-04 | **Jira users with initials-only display names** cannot be linked when the email is hidden. | 22 identity cases, mostly Jira initials | steward queue + a request to users | an onboarding check that lists unlinkable accounts on day 1, with a template message to users | M | M |
| FI-05 | **Special-category data in free text** needs quarantine *before* inference. | 4 records in 48 profiles | the quarantine rule in this repo | a configurable pre-inference filter with an audit trail, plus a "quarantined" state visible to the DPO | H | M |
| FI-06 | **Abbreviations and certifications in customer libraries** ("PM", "Lean Six Sigma Green Belt") don't map. | 8 in-scope misses of 85 | steward maps by hand | an abbreviation dictionary per domain; certifications as a separate entity that maps to several skills | L | H |
| FI-07 | **Validation fatigue risk.** Role-based suggestions are wrong about 4 times in 10. | ADR-0009 policy eval: 1.75 wrong asks per person for role-only | corroborated-first card, role skills in a second card later | make the "two-step" validation a product setting, with different wording per step | M | H |
| FI-08 | **Write-back provenance.** The HCM must know which skills the platform owns, or a sync can delete employee entries. | ADR-0007 | `source` field and a removal rule | make provenance and "never touch employee-entered" a documented guarantee of the connector | H | H |

## How these are reported

- Logged the day they appear, with a reproducible example (a sentence, a record, an API response).
- Reviewed with the vendor's product team every two weeks during the implementation.
- Closed with a link: product ticket, documentation change, or "won't do, because…".

Example tickets written from these insights: [product tickets](product-tickets.md).
