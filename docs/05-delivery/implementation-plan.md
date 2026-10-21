# Implementation plan

20 weeks from kick-off to the scale decision. The plan is built around two hard checkpoints: the **readiness gate** (week 7) and the **works council agreements** (week 9). Nothing in production depends on a date that does not depend on those two first.

```mermaid
gantt
  dateFormat  YYYY-MM-DD
  axisFormat  w%W
  title Norvane: skills intelligence, wave 1 (electrification)
  section Discover
  Kick-off, discovery workshop      :a1, 2027-01-11, 7d
  Extracts + readiness scan         :a2, after a1, 7d
  section Design
  Integration design + ADRs         :b1, 2027-01-18, 14d
  Security review, accounts         :b2, 2027-01-25, 21d
  section Prepare
  HR remediation (job architecture) :c1, 2027-02-01, 21d
  Readiness gate re-run             :milestone, m1, 2027-02-22, 0d
  Works council BE (CAO 39)         :c2, 2027-01-25, 35d
  Betriebsvereinbarung DE           :c3, 2027-01-25, 42d
  Agreements signed                 :milestone, m2, 2027-03-08, 0d
  section Build
  Connectors + identity             :d1, 2027-02-01, 21d
  Write-back + Teams app            :d2, 2027-02-15, 21d
  section Test
  SIT                               :e1, 2027-03-01, 10d
  UAT (HRBPs, works council observers) :e2, 2027-03-11, 10d
  section Pilot
  Go-live pilot (electrification)   :milestone, m3, 2027-03-29, 0d
  Pilot + hypercare                 :f1, 2027-03-29, 42d
  Scale decision                    :milestone, m4, 2027-05-24, 0d
```

## Phases, outputs and exit criteria

| Phase | Weeks | Outputs | Exit criterion |
|---|---|---|---|
| **Discover** | 1–2 | discovery notes, system map, stakeholder map, success criteria, readiness report | sponsor accepts the readiness verdict and the remediation owners |
| **Design** | 2–4 | integration architecture, interface specs, ADRs, security pack, DPIA draft | HRIS lead and IT architect sign the design; DPO accepts the DPIA draft |
| **Prepare** | 3–7 | remediation done by HR; works council information and consultation | readiness gate passes (week 7); agreements on track |
| **Build** | 4–9 | connectors configured against the implementation tenant, identity rules, Teams app, write-back, analytics export, run log | SIT entry: all interfaces green in the build environment |
| **Test** | 8–11 | SIT, UAT, per-language recall on a labelled Norvane sample | UAT sign-off by HR director; agreements signed |
| **Pilot** | 12–17 | go-live for electrification, validation wave 1, hypercare | success criteria S1–S8 ([success criteria](../00-engagement/success-criteria.md)) |
| **Scale decision** | 18–20 | pilot report, wave 2 plan, product feedback summary | steering decides on the next divisions |

## Critical path and buffers

1. **Works council in Germany** (6 weeks planned). Every day of delay moves the pilot for Keldorf. Mitigation: the Belgian part of the pilot can start alone. The design already supports going live per legal entity.
2. **Security review** (3 weeks). It runs in parallel with design, and the security pack is sent in week 2.
3. **Job architecture fixes** (3 weeks, by HR). If the week-7 gate fails, the pilot starts with the subset that passes ([ADR-0008](../02-decisions/ADR-0008-phased-rollout-behind-a-readiness-gate.md)).

## Working rhythm

- Weekly working session with the HRIS lead and the SF admin (60 min), with a written status every Friday ([example](status-report-example.md)).
- Steering every 4 weeks: CHRO, HR director, IT architect, DPO and the vendor's engagement lead.
- Decisions go into an ADR or the decision log, never only into a meeting.
- Field insights are logged the same day they appear and reviewed with the vendor's product team every two weeks ([field insights](../07-product-feedback/field-insights.md)).
