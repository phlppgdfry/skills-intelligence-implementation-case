# How the AI works, in plain language

*For HR business partners, managers and works council members. A 20-minute session, built from this page. No slides needed.*

## The one-sentence version

The system reads short pieces of work you already did, notices which skills they mention, and asks you whether that is right. **You decide.**

## Step by step, with one real example

Take Hannah, a software engineer who moved from Keldorf to Norvane last year. Run `python -m skillslayer profile W30579` to see her (fictional) profile.

**1. Collect evidence.** The system looks at four kinds of things:

| Kind | Hannah's example | How much it counts |
|---|---|---|
| Her job profile | "You have hands-on experience with SQL." | a little: it says what the *role* needs, not what *she* can do |
| A Jira ticket she finished | "SQL-Fehler an Linie 7 beheben" | a lot, if it is recent |
| A course she completed | "Grundlagen Java" | some: she learned about it |
| Her own "about me" text | "Ich arbeite seit 2 Jahren mit SQL." | a lot: she wrote it herself |

**2. Recognise skills, in four languages.** "Prozessleittechnik", "WinCC" and "SCADA" in Hannah's tickets all point to the same skill. The system has a list of the ways people say each skill in English, Dutch, German and French. Without that list it would find far fewer skills in German texts than in English ones, which would be unfair to the Keldorf colleagues ([why that matters](../02-decisions/ADR-0010-multilingual-taxonomy-before-go-live.md)).

**3. Skip what does not count.** "No experience with Docker is needed" is not a skill. Neither is "I would like to learn Kubernetes", nor "you excel at deadlines" (that is not Excel). The system recognises these patterns. It still makes some mistakes, and that is why step 5 exists.

**4. Add it up, carefully.** One mention is weak, and several independent ones are strong. Old evidence counts less: half as much after 18 months, nothing after 3 years. A job profile alone is not enough to suggest a skill. It needs something Hannah actually did ([why](../02-decisions/ADR-0009-corroborated-suggestions-by-default.md)). That rule also protects her from a known mistake: her job profile says "HSE is not part of this role", which the system wrongly reads as a mention of health and safety. Because nothing else backs it up, it stays below the line and she is never asked.

**5. Ask Hannah.** In Teams she gets a card: "Are these your skills?" Every suggestion shows the sentence it came from. She answers Yes, No or Not sure. **Only her Yes answers go to her Workday profile.**

## What it does not do

- It does not read chats, emails or documents.
- It does not score, rank or evaluate people.
- It does not decide anything. People decide; the system prepares the question.
- It does not know what you did not write down anywhere. Skills from outside work, or from a previous job, only show up if you add them yourself.

## Questions people ask

**"How accurate is it?"** In our test set, about 9 out of 10 suggestions shown to employees are right (<!--n:profiles.policies.corroborated.suggested.precision-->90.6%<!--/n-->), and after people confirm, what reaches Workday is right. The real platform is measured again on Norvane's own data before go-live.

**"Why did it suggest something I don't have?"** Usually because a ticket mentions a tool you worked *around*, not *with*. Click No; it will not ask again.

**"Why are some of my skills missing?"** It only sees part of your work: job profile, Jira, courses and your profile text. If you don't use Jira, you will get fewer suggestions. You can always add skills yourself in Workday.

**"Can my manager see what I rejected?"** No. Managers see only confirmed skills.
