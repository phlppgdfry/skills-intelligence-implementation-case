# ADR-0006: Nightly delta on a watermark, weekly full reconciliation

**Status:** Accepted

## Context

A full read of 9,000 workers every night is possible, but it is slow and loads the tenant. A delta read is fast, but it trusts that every change updates the "last updated" field, and in HR systems that is not always true (some retro-active and mass changes).

## Decision

- Nightly: delta on `updatedFrom = last successful run`. The watermark only advances when the whole run succeeds.
- Weekly (Sunday): a full read, compared with the state the deltas built. Every difference needs a reason.

## Evidence

The connector eval changes 7 workers and runs a delta: it returns exactly those <!--n:connectors.delta_fetched-->7<!--/n--> (<!--n:connectors.delta_exact-->yes<!--/n-->).

## Revisit when

Workday business-process events or a change feed become available to the integration; then the delta becomes event-driven and the weekly reconciliation stays.
