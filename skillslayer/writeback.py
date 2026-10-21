"""Write-back: put validated skills on the worker profile in the HCM, safely and idempotently.

Rules (ADR-0001, ADR-0007):
- only skills the employee validated are written; inferred-but-unvalidated never leave the layer
- we only ever remove skills that we wrote ourselves (source = skills-layer) and that the
  employee has since rejected; skills an employee typed in are never touched
- every operation has an idempotency key, so a retried or repeated run changes nothing
- the plan is computed first and can be reviewed as a dry run before it is applied
"""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass

from .canonical import ProfileSkill

OWNED = "skills-layer"


@dataclass(frozen=True)
class Operation:
    op: str            # add | remove
    worker_id: str
    skill_id: str
    skill_name: str
    key: str


def _key(op: str, worker: str, skill: str, version: str) -> str:
    return hashlib.sha256(f"{op}|{worker}|{skill}|{version}".encode()).hexdigest()[:16]


def plan(validated: dict[str, set[str]], rejected: dict[str, set[str]], current: list[ProfileSkill],
         names: dict[str, str], taxonomy_version: str) -> list[Operation]:
    """validated/rejected: worker id -> skill ids. current: what the HCM holds now."""
    have: dict[str, list[ProfileSkill]] = {}
    for p in current:
        have.setdefault(p.worker_id, []).append(p)
    ops: list[Operation] = []
    for worker in sorted(set(validated) | set(rejected)):
        mine = have.get(worker, [])
        present_ids = {p.skill_id for p in mine if p.skill_id}
        present_names = {p.name.casefold() for p in mine}
        for sid in sorted(validated.get(worker, set())):
            if sid not in present_ids and names[sid].casefold() not in present_names:
                ops.append(Operation("add", worker, sid, names[sid], _key("add", worker, sid, taxonomy_version)))
        for sid in sorted(rejected.get(worker, set())):
            if any(p.skill_id == sid and p.source == OWNED for p in mine):
                ops.append(Operation("remove", worker, sid, names[sid], _key("remove", worker, sid, taxonomy_version)))
    return ops


class Target:
    """An in-memory HCM that behaves like the real API: idempotency keys are remembered."""

    def __init__(self, current: list[ProfileSkill]) -> None:
        self.rows = [ProfileSkill(**asdict(p)) for p in current]
        self.seen_keys: set[str] = set()
        self.applied = 0
        self.replayed = 0

    def apply(self, ops: list[Operation]) -> None:
        for o in ops:
            if o.key in self.seen_keys:
                self.replayed += 1
                continue
            self.seen_keys.add(o.key)
            if o.op == "add":
                self.rows.append(ProfileSkill(o.worker_id, o.skill_name, o.skill_id, OWNED))
            else:
                self.rows = [p for p in self.rows if not (p.worker_id == o.worker_id and p.skill_id == o.skill_id and p.source == OWNED)]
            self.applied += 1
