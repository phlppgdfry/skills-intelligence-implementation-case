# ADR-0001: Employees validate every inferred skill before it leaves the layer

**Status:** Accepted (week 3, steering committee; confirmed with both works councils)

## Context

The engine infers skills from job profiles, Jira tickets, courses and profile text. Inferred skills are probabilistic. Even with corroboration, about one suggestion in ten is wrong in our eval (<!--n:profiles.policies.corroborated.suggested.precision-->90.6%<!--/n--> precision). If inferred skills went straight into Workday, managers and Visier, three things would happen: wrong skills would be used in mobility decisions, the councils would see a profiling system without human control, and employees would find skills on their profile they never claimed.

## Options

1. **Write everything inferred, with a confidence score.** This gives the most data fastest, but it fails the works council test, and "confidence 0.62" means nothing to a manager.
2. **Manager validates.** One person per team, so it is quick to organise. But it puts the manager in the position of judging skills from data the employee has not seen, which is exactly the performance-monitoring concern under BetrVG §87.
3. **Employee validates, in Teams.** The person who knows best decides, in a tool they already use, with the evidence shown.

## Decision

Option 3. Nothing inferred leaves the layer until the employee confirms it. The Teams card shows up to six suggestions, each with the sentence it came from. No answer means nothing is written. Managers and Visier only ever see validated skills.

## Consequences

- Coverage grows at the speed of employee response. The pilot target is ≥ 60% response in 3 weeks ([success criteria](../00-engagement/success-criteria.md)).
- The validated set is accurate: <!--n:profiles.policies.corroborated.validated.precision-->100%<!--/n--> precision in the simulation, against <!--n:profiles.policies.corroborated.suggested.precision-->90.6%<!--/n--> before validation.
- Every validation is a labelled example, which is worth feeding back to the vendor ([field insights](../07-product-feedback/field-insights.md)).
- The governance ablation shows what the rule prevents: without it, <!--n:governance.ablation.inferred skills downstream.total-->157<!--/n--> unvalidated rows would land in the analytics export.

## How we would know it was wrong

Response stays under 40% after reminders, or HRBPs work around the empty profiles with spreadsheets.

## Revisit when

After the pilot. A "validated by manager on request of the employee" path may be added for people without Teams access (some production workers).
