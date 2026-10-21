# Architecture and implementation decisions

Each ADR records one decision: the context, the options that were really on the table, what we chose, what it costs, how we would know it was wrong, and when to look at it again. Where a decision is backed by a measurement, the number comes from the eval report and is kept current by `scripts/build.py`.

| ADR | Decision | Backed by |
|---|---|---|
| [0001](ADR-0001-employees-validate-before-anything-leaves.md) | Employees validate every inferred skill before it reaches Workday, a manager or Visier | governance ablation, policy eval |
| [0002](ADR-0002-work-metadata-not-message-content.md) | Read work metadata (Jira: four fields), never message content (Teams, Slack) | connector eval: field minimisation |
| [0003](ADR-0003-workday-is-the-identity-anchor.md) | Workday is the identity anchor during the transition; no write-back to SuccessFactors | identity eval |
| [0004](ADR-0004-api-first-file-fallback.md) | API first, files where the customer's standard is a file | interface inventory |
| [0005](ADR-0005-map-customer-libraries-do-not-replace-them.md) | Map the customer's own skills libraries onto the taxonomy; do not replace them | crosswalk eval |
| [0006](ADR-0006-delta-sync-with-weekly-reconciliation.md) | Nightly delta on a watermark, weekly full reconciliation | connector eval: delta |
| [0007](ADR-0007-write-back-owns-only-its-own-skills.md) | The write-back owns only the skills it wrote; idempotency keys; dry run first | write-back eval |
| [0008](ADR-0008-phased-rollout-behind-a-readiness-gate.md) | Phased rollout behind a readiness gate; pilot in one division | readiness eval |
| [0009](ADR-0009-corroborated-suggestions-by-default.md) | Suggest only corroborated skills by default; role-based skills as a separate, later step | policy eval |
| [0010](ADR-0010-multilingual-taxonomy-before-go-live.md) | No go-live in a language before the taxonomy has aliases in it | extraction ablation |
