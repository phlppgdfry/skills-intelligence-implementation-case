"""Simulated employees answering the Teams validation card.

This is the only place outside evals/run.py that reads data/gold/. It stands in
for real people, so its behaviour is an assumption, stated here and in EVIDENCE.md:

- 20% of people never answer (the card expires; nothing is written)
- a true skill: accepted 90%, "not sure" 5%, wrongly rejected 5%
- a wrong suggestion: rejected 85%, "not sure" 10%, wrongly accepted 5%

Answers are derived from a hash, so every run gives the same answers.
"""

from __future__ import annotations

import hashlib
import json

from skillslayer.config import DATA
from skillslayer.identity import Resolution

NO_RESPONSE = 0.20


def _u(*parts: str) -> float:
    return int(hashlib.sha256("|".join(parts).encode()).hexdigest()[:8], 16) / 0xFFFFFFFF


def truth_by_entity(res: Resolution) -> dict[str, set[str]]:
    """Entity id -> true skills, for entities that map to exactly one real person."""
    gold = json.loads((DATA / "gold" / "identity.json").read_text(encoding="utf-8"))
    persons = json.loads((DATA / "gold" / "persons.json").read_text(encoding="utf-8"))
    out = {}
    for eid, ent in res.entities.items():
        pids = {gold[k] for k in ent.members if k in gold and gold[k] != "external"}
        if len(pids) == 1:
            out[eid] = set(persons[pids.pop()]["skills"])
    return out


def responder(truth: dict[str, set[str]]):
    def answer(eid: str, sid: str) -> str | None:
        if eid not in truth or _u("respond", eid) < NO_RESPONSE:
            return None
        u = _u("answer", eid, sid)
        if sid in truth[eid]:
            return "accept" if u < 0.90 else "unsure" if u < 0.95 else "reject"
        return "reject" if u < 0.85 else "unsure" if u < 0.95 else "accept"
    return answer
