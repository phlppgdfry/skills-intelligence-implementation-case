# ADR-0009: Suggest only corroborated skills by default

**Status:** Accepted for the pilot

## Context

Which skills should the first validation card ask about? The first card an employee sees decides whether they trust the tool. Four policies were measured with simulated employees (assumptions in `evals/simulate.py`):

| Policy | Suggested precision | Recall | Asked per person | Wrong asks per person | Validated per person | Validated precision |
|---|---|---|---|---|---|---|
| Role only (the job profile's skills) | <!--n:profiles.policies.role_only.suggested.precision-->56.4%<!--/n--> | <!--n:profiles.policies.role_only.suggested.recall-->45.5%<!--/n--> | <!--n:profiles.policies.role_only.asked_per_person-->4.02<!--/n--> | <!--n:profiles.policies.role_only.wrong_asks_per_person-->1.75<!--/n--> | <!--n:profiles.policies.role_only.validated_per_person-->1.7<!--/n--> | <!--n:profiles.policies.role_only.validated.precision-->95.9%<!--/n--> |
| Work and learning only | <!--n:profiles.policies.work_only.suggested.precision-->89.2%<!--/n--> | <!--n:profiles.policies.work_only.suggested.recall-->23.6%<!--/n--> | <!--n:profiles.policies.work_only.asked_per_person-->1.32<!--/n--> | <!--n:profiles.policies.work_only.wrong_asks_per_person-->0.14<!--/n--> | <!--n:profiles.policies.work_only.validated_per_person-->0.9<!--/n--> | <!--n:profiles.policies.work_only.validated.precision-->100%<!--/n--> |
| **Corroborated** (job profile + work/learning) | <!--n:profiles.policies.corroborated.suggested.precision-->90.6%<!--/n--> | <!--n:profiles.policies.corroborated.suggested.recall-->33.6%<!--/n--> | <!--n:profiles.policies.corroborated.asked_per_person-->1.85<!--/n--> | <!--n:profiles.policies.corroborated.wrong_asks_per_person-->0.17<!--/n--> | <!--n:profiles.policies.corroborated.validated_per_person-->1.24<!--/n--> | <!--n:profiles.policies.corroborated.validated.precision-->100%<!--/n--> |
| Broad (job profile alone suffices) | <!--n:profiles.policies.broad.suggested.precision-->60.6%<!--/n--> | <!--n:profiles.policies.broad.suggested.recall-->58.1%<!--/n--> | <!--n:profiles.policies.broad.asked_per_person-->4.78<!--/n--> | <!--n:profiles.policies.broad.wrong_asks_per_person-->1.88<!--/n--> | <!--n:profiles.policies.broad.validated_per_person-->2.18<!--/n--> | <!--n:profiles.policies.broad.validated.precision-->96.8%<!--/n--> |

## Decision

The first card uses **corroborated** suggestions: few questions, and almost all of them right. Three to four weeks later, a second, differently framed card asks about the remaining skills of the person's role ("People in your role often use these. Do you?"). At that point the employee knows the tool, and the framing makes clear these are not claims about them.

## Consequences

- Fewer validated skills after the first card (<!--n:profiles.policies.corroborated.validated_per_person-->1.24<!--/n--> per person against <!--n:profiles.policies.broad.validated_per_person-->2.18<!--/n--> for broad). The workforce plan's first internal-supply numbers will be conservative, and the sponsor accepted this in steering.
- A 10x lower rate of wrong questions in the first card (<!--n:profiles.policies.corroborated.wrong_asks_per_person-->0.17<!--/n--> against <!--n:profiles.policies.role_only.wrong_asks_per_person-->1.75<!--/n-->). A wrong first question is what people screenshot and share.

## How we would know it was wrong

The response rate to the first card is high and the rejection rate is very low. Then the tool is trusted, and the second card can come sooner.
