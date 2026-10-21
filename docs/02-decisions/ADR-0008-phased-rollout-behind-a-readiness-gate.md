# ADR-0008: Phased rollout behind a readiness gate

**Status:** Accepted

## Context

The sponsor wanted all 9,000 people live by the end of Q1. The readiness scan on the electrification division's data says the job architecture is not ready: <!--n:readiness.scores.job_architecture-->70%<!--/n--> against an <!--n:readiness.thresholds.job_architecture-->85%<!--/n--> gate, because of missing, stale and duplicate job profiles.

## Options

1. **Go live everywhere and fix the data on the way.** Fast on paper. In practice the first impression employees get is wrong suggestions from bad job profiles.
2. **Fix all job architecture first.** Clean, but HR's job architecture project is a year of work.
3. **Pilot one division behind a gate**, fix that division's findings (12 job profiles, 2 workers, 1 loop), then scale division by division, each behind the same gate.

## Decision

Option 3. The gate is the five readiness dimensions with the thresholds in `skillslayer/readiness.py`. A division goes live when all five pass on its production extract.

## Consequences

- The plan has a real checkpoint the sponsor can explain to the board: "we go when the data is ready, and here is the scorecard."
- HR gets a concrete, owned fix list instead of a general "improve data quality" ([remediation plan](../03-readiness/remediation-plan.md)).
