# ADR-0003: Workday is the identity anchor; no write-back to SuccessFactors in wave 1

**Status:** Accepted

## Context

Transferred Keldorf employees exist in both HCMs. Norvane's target state is Workday for everyone (SuccessFactors migration planned for 2027). We need one person ID to hang skills on, and one place to write validated skills to.

## Options

1. **A new master ID in the skills layer.** Neutral, but it creates a third identity nobody else uses.
2. **SuccessFactors as anchor for Keldorf people, Workday for Norvane.** Mirrors the org chart, and breaks for every transfer.
3. **Workday as anchor.** Every Workday worker starts an entity. SuccessFactors-only people are their own entity until they transfer.

## Decision

Option 3, with the matching rules in [identity](../01-architecture/identity.md). Validated skills are written to Workday only. For SuccessFactors-only people they live in the platform and the Visier export until the migration decision.

## Consequences

- <!--n:identity.rules.false_merges-->0<!--/n--> wrong merges and <!--n:identity.review_queue-->22<!--/n--> steward cases in the pilot data. A name-only approach would have merged a homonym.
- No change request in SuccessFactors, which the Keldorf admin team cannot absorb before the migration.
- Keldorf-only employees validate in Teams like everyone else, but their skills are not on an HCM profile yet. This is said plainly in the FAQ.

## Revisit when

The 2027 migration is confirmed (then: load validated skills as part of the migration), or postponed beyond 2027 (then: build the SuccessFactors write-back to Growth Portfolio or the talent profile, whichever Norvane uses).
