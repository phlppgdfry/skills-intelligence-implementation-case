"""Crosswalk: map the customer's own skills and competency libraries onto the taxonomy.

Customers never start empty. Norvane has ~70 free-typed skills in Workday; Keldorf
has a German competency library in SuccessFactors. We map, we do not replace
(ADR-0005): every library entry ends up as an automatic match, a suggestion for
a data steward, or "out of scope" (soft skills, languages, licences) that stays
a customer attribute.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from difflib import SequenceMatcher

from .canonical import LibrarySkill
from .taxonomy import Taxonomy, load

NOISE = re.compile(r"\((advanced|basic|siemens|tig|k8s)\)|\b(programming|ms|microsoft|cloud|planning|skills?)\b", re.I)
FUZZY_AT = 0.86


@dataclass
class Mapping:
    source: str
    library_id: str
    name: str
    skill_id: str | None
    method: str       # exact | normalized | fuzzy | none
    score: float

    @property
    def needs_steward(self) -> bool:
        return self.method in ("fuzzy", "none")


def _norm(s: str) -> str:
    s = NOISE.sub(" ", s.casefold())
    s = re.sub(r"[^\w+#&/ ]", " ", s)
    return " ".join(s.split())


def _index(tax: Taxonomy) -> dict[str, str]:
    idx: dict[str, str] = {}
    for sk in tax.skills:
        for form in [sk.name, *sk.all_aliases()]:
            idx.setdefault(form.casefold(), sk.id)
    return idx


def map_library(entries: list[LibrarySkill], taxonomy: Taxonomy | None = None) -> list[Mapping]:
    tax = taxonomy or load()
    exact = _index(tax)
    norm = {_norm(k): v for k, v in exact.items() if _norm(k)}
    out: list[Mapping] = []
    for e in entries:
        best: Mapping | None = None
        for name in e.names:
            if (sid := exact.get(name.casefold())):
                best = Mapping(e.source, e.skill_id, name, sid, "exact", 1.0)
                break
            if (sid := norm.get(_norm(name))):
                best = best or Mapping(e.source, e.skill_id, name, sid, "normalized", 0.95)
                continue
            score, sid = max((SequenceMatcher(None, _norm(name), k).ratio(), v) for k, v in norm.items())
            if score >= FUZZY_AT and (best is None or best.method == "fuzzy" and score > best.score):
                best = Mapping(e.source, e.skill_id, name, sid, "fuzzy", round(score, 3))
        out.append(best or Mapping(e.source, e.skill_id, e.names[0], None, "none", 0.0))
    return out


def summary(maps: list[Mapping]) -> dict:
    by = {m: sum(1 for x in maps if x.method == m) for m in ("exact", "normalized", "fuzzy", "none")}
    return {"entries": len(maps), "by_method": by, "steward_queue": sum(1 for m in maps if m.needs_steward),
            "mappings": [asdict(m) for m in maps]}
