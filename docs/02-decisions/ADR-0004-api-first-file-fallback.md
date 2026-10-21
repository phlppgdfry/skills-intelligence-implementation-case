# ADR-0004: API first, files where the customer's standard is a file

**Status:** Accepted

## Context

APIs give fresh data, error codes and paging. Files are what many HR teams already run and monitor. Insisting on APIs everywhere would slow the project down where the customer has a working file process.

## Decision

| Interface | Choice | Why |
|---|---|---|
| Workday workers | REST API | delta on `updatedFrom`, clear error handling |
| Workday job profiles, skills library | RaaS custom report | the customer controls the columns, and it is the usual Workday pattern for custom extracts |
| SuccessFactors | OData v2 | standard, paged, effective-dated |
| SuccessFactors competency library | Integration Center export to SFTP | one-off and monthly; no reason to build an API client for 41 rows |
| Jira | REST API | field selection is only possible through the API |
| LMS | CSV over SFTP | the LMS's only export |
| Visier | flat file over SFTP | Norvane's existing Visier data pipeline is file-based |

## Consequences

Files need their own checks: header, encoding, row count against a control total, and a filename with a date. A file that does not arrive is an alert, not a silent skip.

## Revisit when

The LMS or Visier offers an API that Norvane's IT supports.
