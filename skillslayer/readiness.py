"""AI-readiness scan: is this customer's data good enough to infer skills from, and safe to use?

Run it in week one, before anyone promises a go-live date. Each finding says what
is wrong, how bad it is, who owns the fix and what the fix is. The scores roll up
into five dimensions with a pilot gate, so "are we ready?" gets a yes/no with reasons.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from datetime import date

from .identity import Resolution, fold
from .landscape import Landscape

STALE_DAYS = 3 * 365
MIN_DESCRIPTION_WORDS = 25

SENSITIVE = {  # GDPR art. 9 categories and national identifiers that must never feed inference
    "health": re.compile(r"\b(burn-?out|surgery|operation an|krankheit|krank|ziekte|ziek|sick leave|arbeitsunfähig|chronic)\b", re.I),
    "union": re.compile(r"\b(ig metall|ver\.di|gewerkschaft|betriebsrat|vakbond|acv|abvv|aclvb|union member)\b", re.I),
    "national_id": re.compile(r"\b(steuer-?id|rijksregister\w*|insz)\b.{0,30}\d|\b\d{2}\.\d{2}\.\d{2}-\d{3}\.\d{2}\b", re.I),
}

OWNERS = {
    "job_description_missing": ("high", "HR job architecture", "Write or import a description; until then the job only gets skills from its incumbents."),
    "job_description_stale": ("medium", "HR job architecture", "Review descriptions older than three years with the job owner."),
    "duplicate_job_title": ("medium", "HR job architecture", "Merge or retire the duplicate job profile; map incumbents to one code."),
    "job_without_incumbents": ("low", "HR job architecture", "Inactivate the job profile or confirm it is a planned role."),
    "worker_without_job": ("high", "HR operations", "Assign a job profile; without one the worker gets no role-based skills."),
    "manager_missing": ("high", "HR operations", "Fix the supervisory organisation; validation reminders go to the manager."),
    "manager_loop": ("high", "HR operations", "Break the loop in the reporting line."),
    "jira_account_unresolved": ("low", "IT / tool owners", "Confirm the account is external, or add the person's work email to the mapping."),
    "identity_review": ("medium", "Data steward", "Confirm or reject the candidate match in the steward queue."),
    "sensitive_free_text": ("critical", "DPO + HR operations", "Remove the text at the source and inform the employee; the record is quarantined."),
}

# privacy has no percentage gate: it passes when every flagged record is quarantined (and a DPO action is open)
GATE = {"job_architecture": 0.85, "workforce_data": 0.95, "identity": 0.90, "work_evidence": 0.50}


@dataclass
class Finding:
    check: str
    object: str
    severity: str
    owner: str
    fix: str
    detail: str = ""


def _finding(check: str, obj: str, detail: str = "") -> Finding:
    base = check.split(":")[0]
    sev, owner, fix = OWNERS[base]
    return Finding(check, obj, sev, owner, fix, detail)


def scan(land: Landscape, res: Resolution) -> dict:
    f: list[Finding] = []
    as_of: date = land.as_of

    # --- job architecture
    wd_jobs = [j for j in land.jobs if j.source == "workday" and j.active]
    for j in land.jobs:
        if len(j.description.split()) < MIN_DESCRIPTION_WORDS:
            f.append(_finding("job_description_missing", j.job_id, j.title))
        elif j.updated and (as_of - j.updated).days > STALE_DAYS:
            f.append(_finding("job_description_stale", j.job_id, f"last updated {j.updated.isoformat()}"))
    by_title: dict[str, list[str]] = {}
    for j in wd_jobs:
        by_title.setdefault(fold(j.title), []).append(j.job_id)
    for ids in by_title.values():
        if len(ids) > 1:
            f.append(_finding("duplicate_job_title", "|".join(sorted(ids))))
    staffed = {w.job_id for w in land.workday}
    for j in wd_jobs:
        if j.job_id not in staffed:
            f.append(_finding("job_without_incumbents", j.job_id, j.title))

    # --- workforce data
    ids = {w.source_id for w in land.workday}
    mgr = {w.source_id: w.manager_id for w in land.workday}
    for w in land.workday:
        if not w.job_id:
            f.append(_finding("worker_without_job", w.source_id, w.display))
        if w.manager_id and w.manager_id not in ids:
            f.append(_finding("manager_missing", w.source_id, f"manager {w.manager_id} does not exist"))
    loops: set[str] = set()
    for start in ids:
        seen, cur = [], start
        while cur and cur not in seen:
            seen.append(cur)
            cur = mgr.get(cur)
        if cur and cur in seen:
            cycle = seen[seen.index(cur):]
            if len(cycle) > 1:
                loops.add("|".join(sorted(cycle)))
    for loop in sorted(loops):
        f.append(_finding("manager_loop", loop))

    # --- identity
    for key in res.unresolved:
        src, sid = key.split(":", 1)
        if src == "jira" and not any(r["record"] == key for r in res.review):
            f.append(_finding("jira_account_unresolved", sid))
    for r in res.review:
        f.append(_finding("identity_review", r["record"], f"{r['display']}: {r['reason']}"))

    # --- privacy: sensitive data in free text
    quarantined: list[str] = []
    for a in land.activities:
        if a.kind != "about":
            continue
        for cat, pat in SENSITIVE.items():
            if pat.search(a.text):
                f.append(_finding(f"sensitive_free_text:{cat}", a.person_key.split(":", 1)[1]))
                quarantined.append(a.ref)
                break

    # --- scores
    usable = [j for j in wd_jobs if not any(x.object == j.job_id and x.check in ("job_description_missing", "job_description_stale") for x in f)]
    dup_extra = sum(len(x.object.split("|")) - 1 for x in f if x.check == "duplicate_job_title")
    job_arch = (len(usable) - dup_extra) / len(wd_jobs)
    bad_workers = {x.object for x in f if x.check in ("worker_without_job", "manager_missing")} | {p for x in f if x.check == "manager_loop" for p in x.object.split("|")}
    workforce = 1 - len(bad_workers) / len(land.workday)
    source_records = len(land.workday) + len(land.sf) + len(land.jira)
    linked_auto = sum(1 for k in res.of if not k.startswith("lms:"))
    review_keys = {r["record"] for r in res.review}
    identity = (linked_auto - sum(1 for k in review_keys if k in res.of and k.startswith("successfactors:"))) / source_records
    with_evidence = {res.of.get(a.person_key) for a in land.activities if a.ref not in quarantined} - {None}
    evidence = len(with_evidence) / max(1, len(res.entities))
    privacy = 1.0 if not quarantined else 1.0 - len(quarantined) / max(1, sum(1 for a in land.activities if a.kind == "about"))
    scores = {"job_architecture": round(job_arch, 3), "workforce_data": round(workforce, 3), "identity": round(identity, 3),
              "work_evidence": round(evidence, 3), "privacy": round(privacy, 3)}
    gate = {k: v >= GATE[k] for k, v in scores.items() if k in GATE}
    gate["privacy"] = len(quarantined) == sum(1 for x in f if x.check.startswith("sensitive_free_text"))
    order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    f.sort(key=lambda x: (order[x.severity], x.check, x.object))
    return {
        "findings": [asdict(x) for x in f],
        "scores": scores,
        "gate": gate,
        "thresholds": GATE,
        "ready_for_pilot": all(gate.values()),
        "quarantined": sorted(quarantined),
        "counts": {sev: sum(1 for x in f if x.severity == sev) for sev in order},
    }
