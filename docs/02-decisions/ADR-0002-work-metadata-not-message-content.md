# ADR-0002: Read work metadata, never message content

**Status:** Accepted

## Context

Teams and Slack conversations contain a lot of skill evidence. They also contain private conversations, health remarks and union matters. Belgian CAO 81 sets strict conditions on monitoring electronic online communication data: a legitimate purpose, proportionality and transparency. In Germany, any technical system that *can* monitor behaviour or performance needs the *Betriebsrat*'s agreement (BetrVG §87(1) no. 6). Reading chat content would make the whole project depend on the hardest possible negotiation, for evidence we can mostly get elsewhere.

## Options

1. **Read Teams and Slack messages.** The richest signal, and the worst privacy and acceptance profile.
2. **Read Jira tickets in full** (description, comments, worklogs). A rich signal, but comments contain the same conversational risks.
3. **Read only the metadata of resolved work**: Jira summary, assignee, resolution date, component. Use Teams only as the channel for the validation card.

## Decision

Option 3. The Jira connector sends an explicit `fields=summary,assignee,resolutiondate,components` list. The connector eval checks that the response holds only those four fields (<!--n:connectors.jira_fields_minimal-->yes<!--/n-->). Teams is used to *send* the validation card and to receive the answer, nothing else.

## Consequences

- Less evidence per person: only <!--n:profiles.evidence_coverage-->73.1%<!--/n--> of true skills have any evidence in the pilot data. Validation and the later role-based step make up part of the gap ([ADR-0009](ADR-0009-corroborated-suggestions-by-default.md)).
- The works council conversation is about a defined, small data set, and the agreement can list the four fields.
- People who do not use Jira (production, finance) get evidence from job profiles and courses only. That is a known equity gap, raised in the DPIA.

## Revisit when

A wave 2 source is proposed (Confluence page titles, ServiceNow resolved incidents). Each one gets the same test: metadata of finished work, fields named in the agreement.
