# Identity resolution

After a merger, "who is who" is the first thing that breaks. If it goes wrong quietly, one person's Jira work becomes another person's skills, and the error then surfaces in a validation card sent to the wrong person.

## The situation at Norvane

| Population | Workday | SuccessFactors | Jira | LMS |
|---|---|---|---|---|
| Norvane employees | yes | — | engineers | yes, `@norvane.example` |
| Keldorf employees who stayed | — | yes, `@keldorf.example` | engineers | yes, `@keldorf.example` |
| Keldorf employees who transferred | yes, new hire date, `@norvane.example`, sometimes `Mueller` instead of `Müller` | yes, often still the old address | yes, often hidden email | `@norvane.example` |
| Contractors | — | — | yes, no email | — |

## Rules (in order)

1. **Workday is the anchor** ([ADR-0003](../02-decisions/ADR-0003-workday-is-the-identity-anchor.md)). Each Workday worker starts an entity.
2. **Cross-reference.** Workday's custom `legacySuccessFactorsId` → match.
3. **Exact email** → match.
4. **Transfer pattern.** The email local part is the same across the two company domains, the folded name is the same (`Jürgen Müller` = `Juergen Mueller`), **and** the Workday hire date is after the merger close (1 April 2025) → match. The hire-date condition is what stops a homonym from being merged.
5. **Same name or same local part without rule 4** → the SuccessFactors record stays its own entity and goes to the **steward queue**.
6. **Jira with a hidden email.** A full display name that is unique across all entities → match. Initials ("T. Becker") or several candidates → steward queue.
7. **Nothing** → unresolved, and listed in the run log (contractors, test accounts).

## Measured

| Approach | Precision | Recall | Wrong merges |
|---|---|---|---|
| Exact email only | <!--n:identity.baseline_email_only.precision-->99.1%<!--/n--> | <!--n:identity.baseline_email_only.recall-->55.3%<!--/n--> | <!--n:identity.baseline_email_only.false_merges-->1<!--/n--> |
| Email local part only | <!--n:identity.baseline_local_part.precision-->98.4%<!--/n--> | <!--n:identity.baseline_local_part.recall-->67%<!--/n--> | <!--n:identity.baseline_local_part.false_merges-->2<!--/n--> |
| Folded name only | <!--n:identity.baseline_name_only.precision-->99.4%<!--/n--> | <!--n:identity.baseline_name_only.recall-->87.2%<!--/n--> | <!--n:identity.baseline_name_only.false_merges-->1<!--/n--> |
| **The rules above** | <!--n:identity.rules.precision-->100%<!--/n--> | <!--n:identity.rules.recall-->87.2%<!--/n--> | **<!--n:identity.rules.false_merges-->0<!--/n-->** |
| Rules + steward works the queue | <!--n:identity.after_steward.precision-->100%<!--/n--> | <!--n:identity.after_steward.recall-->100%<!--/n--> | <!--n:identity.after_steward.false_merges-->0<!--/n--> |

Precision and recall are pairwise: for every pair of records that belong to the same person, did we link them? There are <!--n:identity.records-->443<!--/n--> records and <!--n:identity.people-->266<!--/n--> people. Name matching looks almost as good as the rules, but it merges a Norvane project manager with a Keldorf colleague who has the same name. In a 9,000-person group the number of such pairs grows quickly. Exact email matching never sees the transfers.

## The steward queue

<!--n:identity.review_queue-->22<!--/n--> records: one SuccessFactors homonym and the Jira accounts that show only initials. The [data steward guide](../06-enablement/data-steward-guide.md) explains how to work it. Most of the Jira cases disappear once the Atlassian admin asks those users to make their email visible to the organisation, which is a one-line request in the go-live communication.
