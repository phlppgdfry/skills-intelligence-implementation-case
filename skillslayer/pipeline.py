"""One implementation run, end to end:

    fetch -> resolve identities -> readiness scan -> governance filter -> evidence -> profiles
          -> suggestions -> employee validation (Teams) -> write-back plan -> analytics export

Governance is applied before inference, not after: an opted-out person's data is
never turned into evidence, and quarantined free text is never read by the
engine. The run report counts everything, so reconciliation is a diff, not a hunt.
"""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field
from typing import Callable

from . import crosswalk, inference, readiness, writeback
from .identity import Resolution, resolve
from .inference import Evidence, SkillScore
from .landscape import Landscape
from .taxonomy import load

Responder = Callable[[str, str], str | None]   # (entity id, skill id) -> accept | reject | unsure | None


@dataclass
class Governance:
    honour_optouts: bool = True
    quarantine_sensitive: bool = True
    validated_only_downstream: bool = True


@dataclass
class Run:
    land: Landscape
    res: Resolution
    ready: dict
    excluded: set[str]                                   # entity ids opted out
    evidence: dict[str, list[Evidence]]
    profiles: dict[str, dict[str, SkillScore]]
    suggested: dict[str, list[SkillScore]]
    decisions: dict[str, dict[str, str]] = field(default_factory=dict)
    ops: list[writeback.Operation] = field(default_factory=list)
    export_rows: list[dict] = field(default_factory=list)
    crosswalk: dict = field(default_factory=dict)
    role_only: dict[str, set[str]] = field(default_factory=dict)

    def validated(self, eid: str) -> set[str]:
        return {s for s, d in self.decisions.get(eid, {}).items() if d == "accept"}

    def rejected(self, eid: str) -> set[str]:
        return {s for s, d in self.decisions.get(eid, {}).items() if d == "reject"}


def build_evidence(land: Landscape, res: Resolution, excluded: set[str], quarantined: set[str], config: str = "C") -> tuple[dict, dict]:
    jobs = {j.key: j for j in land.jobs}
    job_skills = {k: inference.extract(j.description, config) for k, j in jobs.items()}
    evidence: dict[str, list[Evidence]] = {}
    role_only: dict[str, set[str]] = {}
    for eid, ent in res.entities.items():
        if eid in excluded:
            continue
        # the job a person holds now: Workday if they have it, otherwise SuccessFactors
        job_key = None
        for member in ent.members:
            src, sid = member.split(":", 1)
            person = next((p for p in (land.workday if src == "workday" else land.sf if src == "successfactors" else []) if p.source_id == sid), None)
            if person and person.job_id:
                job_key = f"{src}:{person.job_id}"
                if src == "workday":
                    break
        evs = evidence.setdefault(eid, [])
        if job_key and job_key in job_skills:
            for m in job_skills[job_key]:
                if m.status == "accepted":
                    evs.append(Evidence(m.skill_id, "job", job_key, m.sentence, None))
            role_only[eid] = {m.skill_id for m in job_skills[job_key] if m.status == "accepted"}
    for a in land.activities:
        eid = res.of.get(a.person_key)
        if not eid or eid in excluded or a.ref in quarantined:
            continue
        for m in inference.extract(a.text, config):
            if m.status == "accepted":
                evidence.setdefault(eid, []).append(Evidence(m.skill_id, a.kind, a.ref, m.sentence, a.on))
    return evidence, role_only


def run(land: Landscape, responder: Responder | None = None, gov: Governance | None = None, config: str = "C",
        threshold: float = inference.SUGGEST_AT, weights: dict[str, float] | None = None) -> Run:
    gov = gov or Governance()
    res = resolve(land.workday, land.sf, land.jira, land.lms_emails)
    ready = readiness.scan(land, res)
    opted = {f"workday:{w}" for w in land.optouts.get("workday", [])} | {f"successfactors:{s}" for s in land.optouts.get("successfactors", [])}
    excluded = {res.of[k] for k in opted if k in res.of} if gov.honour_optouts else set()
    quarantined = set(ready["quarantined"]) if gov.quarantine_sensitive else set()
    evidence, role_only = build_evidence(land, res, excluded, quarantined, config)
    profiles = {eid: inference.profile(evs, land.as_of, weights) for eid, evs in evidence.items()}
    suggested = {eid: inference.suggestions(p, threshold) for eid, p in profiles.items()}
    r = Run(land, res, ready, excluded, evidence, profiles, suggested, role_only=role_only)

    if responder:
        for eid, sugg in suggested.items():
            for s in sugg:
                d = responder(eid, s.skill_id)
                if d:
                    r.decisions.setdefault(eid, {})[s.skill_id] = d

    tax = load()
    names = {s.id: s.name for s in tax.skills}
    validated, rejected = {}, {}
    for eid, ent in res.entities.items():
        wid = ent.workday_id
        if not wid or eid in excluded:
            continue
        validated[wid], rejected[wid] = r.validated(eid), r.rejected(eid)
    r.ops = writeback.plan(validated, rejected, land.profile_skills, names, tax.version)
    r.export_rows = analytics_export(r, gov)
    r.crosswalk = crosswalk.summary(crosswalk.map_library(land.libraries, tax))
    return r


def analytics_export(r: Run, gov: Governance) -> list[dict]:
    """Flat file for the people-analytics platform (Visier, Crunchr): one row per person and skill."""
    tax = load().by_id
    rows = []
    for eid, ent in sorted(r.res.entities.items()):
        if eid in r.excluded:
            continue
        sids = r.validated(eid) if gov.validated_only_downstream else {s.skill_id for s in r.suggested.get(eid, [])}
        emp = ent.workday_id or next((k.split(":", 1)[1] for k in ent.members if k.startswith("successfactors:")), eid)
        for sid in sorted(sids):
            rows.append({"EmployeeID": emp, "SkillID": sid, "SkillName": tax[sid].name, "SkillCluster": tax[sid].cluster,
                         "Status": "validated" if sid in r.validated(eid) else "inferred", "EffectiveDate": r.land.as_of.isoformat()})
    return rows


def export_csv(rows: list[dict]) -> str:
    buf = io.StringIO()
    if rows:
        w = csv.DictWriter(buf, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    return buf.getvalue()
