# Data flows

## 1. Nightly sync

```mermaid
sequenceDiagram
  autonumber
  participant S as Scheduler (02:00 CET)
  participant C as Connectors
  participant WD as Workday
  participant SF as SuccessFactors
  participant J as Jira
  participant L as Run log
  S->>C: start run (watermark = last successful run)
  C->>WD: GET /workers?updatedFrom=watermark&offset=0&limit=100
  WD-->>C: 429 Too Many Requests (Retry-After: 1)
  C->>WD: retry after 1 s
  WD-->>C: 200 {total, data}
  C->>SF: GET /odata/v2/User?$format=json
  SF-->>C: 200 {d: {results, __next}}
  C->>SF: GET __next
  SF-->>C: 503 (maintenance window)
  C->>SF: retry with backoff
  C->>J: GET /search/jql?fields=summary,assignee,resolutiondate,components
  J-->>C: 200 {issues, nextPageToken, isLast}
  C->>L: per interface: records, pages, retries
  Note over C,L: a 400/401/403 is never retried: the run stops that interface and pages the on-call
```

Retry policy (`skillslayer/sources/http.py`):

- 429, 500, 502, 503 and 504 are retried up to 5 times. Retry-After is honoured when present; otherwise the client backs off exponentially from 0.5 s with jitter.
- 400, 401, 403 and 404 are not retried, because the request itself is wrong. The eval checks that a 401 produces exactly one attempt.
- The watermark only moves forward when the whole run succeeded. A failed night re-reads from the last good watermark, so nothing is skipped.

## 2. From records to suggestions

```mermaid
flowchart TB
  A[Source records] --> B{Identity rules}
  B -- linked --> E[Entity]
  B -- ambiguous --> Q[Steward queue]
  B -- nothing --> U[Unresolved: contractors, test accounts]
  E --> G{Opted out?}
  G -- yes --> X[Nothing processed. Kept only as an ID to stay excluded]
  G -- no --> H{Free text flagged sensitive?}
  H -- yes --> Z[Quarantined: never read by the engine; DPO action]
  H -- no --> I[Extract mentions: config C]
  I --> K[Evidence: kind, ref, date, sentence]
  K --> P[Profile: noisy-OR with decay]
  P --> S{score ≥ 0.4?}
  S -- yes --> T[Suggestion with evidence]
  S -- no --> N[Kept, not shown]
```

## 3. Validation and write-back

```mermaid
sequenceDiagram
  autonumber
  participant L as Skills layer
  participant T as Teams bot
  participant E as Employee
  participant WD as Workday
  participant V as Visier
  L->>T: Adaptive Card: up to 6 suggestions, each with its evidence
  T->>E: "Hi Hannah, are these your skills?"
  E->>T: accept / reject / not sure per skill (Action.Execute)
  T->>L: decisions
  L->>L: plan write-back (adds for accepted, removes only for our own rejected skills)
  L->>L: dry run reviewed by HRIS lead (first 2 weeks)
  L->>WD: apply operations with idempotency keys
  L->>V: nightly flat file, validated rows only
  Note over E,L: no answer = nothing written. Reminder after 7 days, card expires after 21
```

## 4. Reconciliation (weekly)

A full read (no watermark) is compared with the state the delta runs built up. Every difference is listed with a reason: a terminated worker, a changed job profile, or a record a delta missed. A difference without a reason is an incident. This catches the classic delta bug where a source changes a record without touching its "last updated" field ([ADR-0006](../02-decisions/ADR-0006-delta-sync-with-weekly-reconciliation.md)).

## The run log

`python -m skillslayer sync --simulate` prints the run log this design produces:

```
fetch workday                          197 records    2 pages  1 retries
fetch successfactors:User               95 records    3 pages  1 retries
fetch successfactors:EmpJob            190 records    5 pages  1 retries
fetch successfactors:FOJobCode          18 records    1 pages  0 retries
fetch successfactors:cust_AboutMe       48 records    2 pages  1 retries
fetch jira                            1211 records   13 pages  1 retries
identities: 266 people, 22 for the steward, 24 unresolved
excluded (opt-out): 7 people; quarantined texts: 4
suggestions: 479 for 180 people
validation (simulated): 322 accepted, 50 rejected, 14 unsure
write-back plan: 207 adds, 1 removes (dry run)
analytics export: 322 validated rows
```
