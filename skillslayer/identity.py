"""Identity resolution: which records in Workday, SuccessFactors, Jira and the LMS are the same person?

After the merger, people who moved from Keldorf to Norvane exist twice: once in
SuccessFactors (often still with their old @keldorf.example address) and once in
Workday. Jira hides many email addresses. Get this wrong and one person's work
becomes another person's skills.

Rules, in order (ADR-0003: Workday is the anchor):

1. Workday's legacySuccessFactorsId cross-reference                 -> match
2. exact email                                                      -> match
3. same email local part across the two company domains, same
   folded name, and a Workday hire date after the merger close     -> match
4. same folded name or same local part, but rule 3 does not hold     -> review queue
5. Jira with hidden email: full display name unique across people   -> match
   initials or several candidates                                   -> review queue
6. nothing                                                          -> unresolved
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass, field
from datetime import date

from .canonical import SourcePerson

MERGER_CLOSE = date(2025, 4, 1)
COMPANY_DOMAINS = ("norvane.example", "keldorf.example")
FOLD = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"})


def fold(name: str) -> str:
    """'Jürgen Müller' and 'Juergen Mueller' fold to the same key."""
    s = name.casefold().translate(FOLD)
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return " ".join(s.replace("-", " ").split())


def local_part(email: str | None) -> str | None:
    if not email or "@" not in email:
        return None
    local, domain = email.lower().split("@", 1)
    return local if domain in COMPANY_DOMAINS else None


@dataclass
class Entity:
    id: str
    members: dict[str, str] = field(default_factory=dict)   # source key -> rule that linked it
    name: str = ""
    emails: set[str] = field(default_factory=set)

    @property
    def workday_id(self) -> str | None:
        return next((k.split(":", 1)[1] for k in self.members if k.startswith("workday:")), None)


@dataclass
class Resolution:
    entities: dict[str, Entity]
    of: dict[str, str]                        # source key -> entity id
    review: list[dict]                        # needs a data steward
    unresolved: list[str]                     # source keys nobody could link

    def entity_for(self, key: str) -> Entity | None:
        eid = self.of.get(key)
        return self.entities.get(eid) if eid else None


def resolve(workday: list[SourcePerson], sf: list[SourcePerson], jira: list[SourcePerson], lms_emails: list[str]) -> Resolution:
    entities: dict[str, Entity] = {}
    of: dict[str, str] = {}
    review: list[dict] = []
    unresolved: list[str] = []

    def new(p: SourcePerson, rule: str) -> Entity:
        e = Entity(f"N{len(entities) + 1:04d}", name=p.display)
        entities[e.id] = e
        link(e, p, rule)
        return e

    def link(e: Entity, p: SourcePerson, rule: str) -> None:
        e.members[p.key] = rule
        if p.email:
            e.emails.add(p.email.lower())
        of[p.key] = e.id

    by_email: dict[str, Entity] = {}
    by_local: dict[str, list[tuple[Entity, SourcePerson]]] = {}
    by_name: dict[str, list[Entity]] = {}
    by_xref: dict[str, Entity] = {}
    hire: dict[str, date | None] = {}

    for w in workday:  # 1. Workday anchors
        e = new(w, "anchor")
        hire[e.id] = w.hire_date
        if w.email:
            by_email[w.email.lower()] = e
        if (lp := local_part(w.email)):
            by_local.setdefault(lp, []).append((e, w))
        by_name.setdefault(fold(w.display), []).append(e)
        if (x := w.legacy_ids.get("successfactors")):
            by_xref[x] = e

    for s in sf:
        if (e := by_xref.get(s.source_id)):
            link(e, s, "xref")
            continue
        if s.email and (e := by_email.get(s.email.lower())):
            link(e, s, "email")
            continue
        lp = local_part(s.email)
        name_hits = by_name.get(fold(s.display), [])
        local_hits = [e for e, _ in by_local.get(lp, [])] if lp else []
        strong = [e for e in local_hits if e in name_hits and (hire[e.id] or date.min) >= MERGER_CLOSE]
        if len(strong) == 1:
            link(strong[0], s, "local-part+name+post-merger hire")
            continue
        candidates = sorted({e.id for e in name_hits + local_hits})
        e = new(s, "anchor")  # keep the person as their own entity until a steward decides
        by_name.setdefault(fold(s.display), []).append(e)
        if s.email:
            by_email[s.email.lower()] = e
        if candidates:
            review.append({"record": s.key, "display": s.display, "candidates": candidates,
                           "reason": "same name or email local part, but no post-merger Workday hire"})

    for j in jira:
        if j.email and (e := by_email.get(j.email.lower())):
            link(e, j, "email")
            continue
        hits = by_name.get(fold(j.display), [])
        distinct = {e.id for e in hits}
        initials = len(j.display.split()[0].rstrip(".")) == 1 if j.display.split() else False
        if len(distinct) == 1 and not initials:
            link(hits[0], j, "display name (unique)")
        elif distinct or initials:
            cands = sorted(distinct) or sorted(e.id for e in entities.values() if fold(e.name).split()[-1:] == fold(j.display).split()[-1:])
            review.append({"record": j.key, "display": j.display, "candidates": cands,
                           "reason": "initials only" if initials else "several people with this name"})
            unresolved.append(j.key)
        else:
            unresolved.append(j.key)

    for email in lms_emails:
        key = f"lms:{email}"
        if (e := by_email.get(email)):
            link(e, SourcePerson("lms", email, email, email=email), "email")
        else:
            unresolved.append(key)

    return Resolution(entities, of, review, unresolved)
