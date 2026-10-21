# Product tickets (written from the field)

Three examples of turning a field insight into something engineering can pick up. The format matters: a problem, evidence, who it hits, a proposal, and how we would know it is fixed. No solution is dictated where product knows better.

---

## FI-01: Post-mention negation is extracted as a skill

**Problem.** Job descriptions often say what a role does *not* involve: "Python is not part of this role", "SAP MM hoort niet bij deze functie", "Löten gehört nicht zu dieser Rolle". The negation cue comes *after* the skill. Today these are extracted as positive skill mentions.

**Evidence.** In the Norvane implementation, all remaining false positives of the extraction step follow this pattern (see the extraction eval, config C). Three reproducible sentences are attached in four languages.

**Who it hits.** Every customer with job architecture written by HR, so nearly all of them. It surfaces as a wrong suggestion in the employee's first validation card, which is where trust is decided.

**Proposal.** Detect negation cues within the same clause after the mention ("is not", "hoort niet", "gehört nicht", "ne fait pas partie"). Open question for product: flag these as "excluded" in the job profile, which would be useful information in itself?

**Done when.** The attached sentences produce no positive mention; no recall loss on the standard eval set.

---

## FI-03: Readiness gate as a product report

**Problem.** Every implementation starts by finding out whether the customer's data can support inference. Today each consultant builds this check by hand, in different ways, in week 2.

**Evidence.** At Norvane the scan found 22/22 planted problems and changed the plan: the pilot moved behind a gate on job architecture (ADR-0008). The checks are generic: missing, stale and duplicate job profiles; workers without jobs; reporting-line loops; unlinkable accounts; sensitive data in free text.

**Who it hits.** Every new customer, in the first 2 weeks.

**Proposal.** A data maturity report with five dimensions, thresholds the customer can set, an owner per finding type, and an export for steering. Run it again nightly after go-live, so data quality stays visible.

**Done when.** A consultant can produce the week-2 readiness verdict from the product without a script.

---

## FI-05: Pre-inference quarantine for special-category data

**Problem.** Free-text profile fields contain health and union information that employees wrote themselves. That data must not be processed (GDPR Art. 9), and filtering after inference is too late, because the text has already been read.

**Evidence.** 4 of 48 profile texts in the pilot data. A governance ablation shows 6 evidence items derived from them when quarantine is off.

**Who it hits.** Every customer that connects a free-text source, especially in DACH, where the works council will ask.

**Proposal.** A configurable filter that runs before ingestion into the inference pipeline, with categories (health, union, national ID), per-language patterns, an audit trail and a DPO view. Quarantined records are visible as such, not silently dropped.

**Done when.** Quarantined texts never appear as evidence; the DPO can list them; the customer can add patterns.
