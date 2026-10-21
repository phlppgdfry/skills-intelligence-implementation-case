# ADR-0007: The write-back owns only the skills it wrote

**Status:** Accepted (HRIS lead is the design authority)

## Context

Worker profiles in Workday already hold skills: some typed by employees, some from an earlier experiment. An integration that "syncs" by making Workday equal to its own view would delete things people entered themselves. That is the fastest way to lose the HRIS team's trust.

## Decision

- Every skill carries a source. The layer only adds skills that were validated, and only removes skills whose source is `skills-layer` **and** which the employee has since rejected.
- Skills with source `employee` are never touched, not even when they duplicate a taxonomy skill.
- Every operation has an idempotency key (operation, worker, skill, taxonomy version). A retried batch changes nothing.
- The plan is computed first. During the first two weeks the HRIS lead reviews the dry run before it is applied.

## Evidence

First run: <!--n:writeback.adds-->207<!--/n--> adds and <!--n:writeback.removes-->1<!--/n--> remove for <!--n:writeback.workers_touched-->91<!--/n--> workers. A replayed batch applies <!--n:writeback.replayed_batch_applied-->0<!--/n-->. The second run plans <!--n:writeback.second_run_ops-->0<!--/n-->. All <!--n:writeback.employee_skills_before-->56<!--/n--> employee-entered skills are untouched (<!--n:writeback.employee_skills_untouched-->yes<!--/n-->).
