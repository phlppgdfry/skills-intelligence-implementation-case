# ADR-0010: No go-live in a language before the taxonomy has aliases in it

**Status:** Accepted

## Context

Norvane's job descriptions are in English and Dutch, Wavre's are in French, and Keldorf's are mostly German. An engine that only knows canonical English skill names finds a skill in an English text much more often than in a German one. Because language follows the legacy company, that bias lands on the Keldorf employees, which is exactly the group the merger story says must not be disadvantaged.

## Evidence (extraction ablation on <!--n:extraction.texts-->1,503<!--/n--> texts)

| Config | Precision | Recall | Recall EN | Recall NL | Recall DE | Recall FR | Language gap |
|---|---|---|---|---|---|---|---|
| A: canonical names | <!--n:extraction.A.all.precision-->93.9%<!--/n--> | <!--n:extraction.A.all.recall-->41.6%<!--/n--> | <!--n:extraction.A.lang:en.recall-->47.5%<!--/n--> | <!--n:extraction.A.lang:nl.recall-->35.4%<!--/n--> | <!--n:extraction.A.lang:de.recall-->29.1%<!--/n--> | <!--n:extraction.A.lang:fr.recall-->32.1%<!--/n--> | <!--n:extraction.A.language_recall_gap-->18.5%<!--/n--> |
| B: + aliases in 4 languages | <!--n:extraction.B.all.precision-->93.3%<!--/n--> | <!--n:extraction.B.all.recall-->96.2%<!--/n--> | <!--n:extraction.B.lang:en.recall-->95.3%<!--/n--> | <!--n:extraction.B.lang:nl.recall-->96.2%<!--/n--> | <!--n:extraction.B.lang:de.recall-->98.1%<!--/n--> | <!--n:extraction.B.lang:fr.recall-->100%<!--/n--> | <!--n:extraction.B.language_recall_gap-->4.7%<!--/n--> |
| C: + negation, aspiration, ambiguity guards | <!--n:extraction.C.all.precision-->98.1%<!--/n--> | <!--n:extraction.C.all.recall-->96.2%<!--/n--> | <!--n:extraction.C.lang:en.recall-->95.3%<!--/n--> | <!--n:extraction.C.lang:nl.recall-->96.2%<!--/n--> | <!--n:extraction.C.lang:de.recall-->98.1%<!--/n--> | <!--n:extraction.C.lang:fr.recall-->100%<!--/n--> | <!--n:extraction.C.language_recall_gap-->4.7%<!--/n--> |

## Decision

A division goes live in a language only when recall in its weakest language is within 6 points of the strongest (gate: `extraction.C.language_recall_gap ≤ 0.06`). The per-language recall is part of the UAT report, and the DPIA mentions it as a fairness control.

## Consequences

- The vendor's real engine is multilingual. The point of this ADR is the **check**, not the stand-in: during UAT the same per-language comparison runs on a labelled sample of Norvane's own texts ([test strategy](../05-delivery/test-strategy-and-uat.md)).
- German compound words ("Projektmanagementerfahrung") are still missed by alias matching. That is field feedback, not something we patch on the customer side.
