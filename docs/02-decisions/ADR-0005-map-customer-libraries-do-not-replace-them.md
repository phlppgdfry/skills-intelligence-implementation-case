# ADR-0005: Map the customer's own skills libraries; do not replace them

**Status:** Accepted

## Context

Norvane has a free-typed Workday skills library (~70 entries in scope, with "Project Mgmt", "PM" and "projectmanagement" side by side). Keldorf has a German competency library used in annual reviews. Replacing both with the vendor taxonomy would be clean, and it would also break Keldorf's review process and throw away the language employees already use.

## Decision

Map every library entry to the taxonomy. Exact and normalised matches are automatic. Fuzzy matches are suggestions for a data steward. Entries that are not skills in the taxonomy's sense (soft skills, languages, driving licences) stay customer attributes.

## Evidence

<!--n:crosswalk.entries-->99<!--/n--> entries. <!--n:crosswalk.auto-->76<!--/n--> map automatically, all of them correctly (<!--n:crosswalk.auto_precision-->100%<!--/n-->), which covers <!--n:crosswalk.auto_coverage_of_in_scope-->89.4%<!--/n--> of the in-scope entries. The steward queue holds <!--n:crosswalk.steward_queue-->23<!--/n-->: the 14 out-of-scope entries and 8 in-scope ones the rules cannot place ("PM", "Leadership", "Lean Six Sigma Green Belt"), plus one fuzzy match. See `python -m skillslayer crosswalk`.

## Consequences

- Each mapping decision is stored with its method, so it can be audited and redone after a taxonomy update.
- The 8 in-scope misses are product feedback. Abbreviations and certifications need a better matching strategy than string similarity ([field insights](../07-product-feedback/field-insights.md)).
