"""Eval suites and the release gate.

    python -m evals.run            # print the report
    python -m evals.run --gate     # exit 1 if any threshold in evals/thresholds.json fails
    python -m evals.run --write    # also write evals/reports/offline.json

Eight suites, each answering one question the implementation has to answer:

    connectors   do we get every record, through 429s and 503s, and only the fields we need?
    identity     do we link the right records to the right person, and never the wrong ones?
    readiness    does the scan find every planted data problem, and nothing else?
    extraction   which taxonomy configuration finds skills in four languages? (A/B/C ablation)
    profiles     which suggestion policy should go to employees? (with simulated validation)
    crosswalk    how much of the customer's own library maps automatically, and correctly?
    writeback    is the write-back idempotent and does it leave employee-entered skills alone?
    governance   do opt-outs, quarantine and the validated-only rule hold? (with ablation)
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import timedelta
from itertools import combinations
from pathlib import Path

from skillslayer import inference, pipeline, writeback
from skillslayer.config import AS_OF, DATA, ROOT
from skillslayer.identity import fold, local_part, resolve
from skillslayer.landscape import TENANT, fetch
from skillslayer.mock.servers import TOKEN, MockServer
from skillslayer.sources import connectors as c
from skillslayer.sources.http import Client

from . import simulate

REPORT = ROOT / "evals" / "reports" / "offline.json"
THRESHOLDS = json.loads((ROOT / "evals" / "thresholds.json").read_text(encoding="utf-8"))


def gold(name: str):
    return json.loads((DATA / "gold" / name).read_text(encoding="utf-8"))


def prf(tp: int, fp: int, fn: int) -> dict:
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    return {"precision": round(p, 4), "recall": round(r, 4), "f1": round(2 * p * r / (p + r), 4) if p + r else 0.0, "tp": tp, "fp": fp, "fn": fn}


# ------------------------------------------------------------------------ connectors
def connectors() -> tuple[dict, object]:
    with MockServer(faults=True) as m:
        land = fetch(m.url, TOKEN)
        faults = list(m.state.faults_served)
        expected = {"workday": len(m.state.workers), "successfactors:User": len(m.state.sf["User"]),
                    "successfactors:EmpJob": len(m.state.sf["EmpJob"]), "successfactors:FOJobCode": len(m.state.sf["FOJobCode"]),
                    "successfactors:cust_AboutMe": len(m.state.sf["cust_AboutMe"]), "jira": len(m.state.issues)}
        # delta: seven workers change today; a delta run with a watermark must return exactly those
        changed = m.state.workers[10:17]
        for w in changed:
            w["lastUpdated"] = AS_OF.isoformat()
        delta, _ = c.workday_workers(Client(m.url, TOKEN, time_scale=0.01), TENANT, updated_from=AS_OF - timedelta(days=0))
        issue_fields = set()
        for i in c.jira_issues(Client(m.url, TOKEN, time_scale=0.01), "statusCategory = Done")[0][:50]:
            issue_fields |= set(i["fields"])
        # a wrong token is a 401 that must not be retried
        bad = Client(m.url, "wrong", time_scale=0.01)
        try:
            bad.get_json(f"/workday/ccx/api/v1/{TENANT}/workers")
            auth_ok = False
        except Exception as e:  # ApiError
            auth_ok = getattr(e, "status", None) == 401 and len(bad.log) == 1
    rows = {s.source: {"records": s.records, "expected": expected[s.source], "pages": s.pages, "retries": s.retries} for s in land.stats}
    complete = all(v["records"] == v["expected"] for v in rows.values())
    dupes = len(land.workday) - len({w.source_id for w in land.workday})
    return {
        "sources": rows, "complete": complete, "faults_injected": len(faults), "faults": faults, "retries": land.retries,
        "duplicates": dupes, "delta_changed": len(changed), "delta_fetched": len(delta),
        "delta_exact": {w.source_id for w in delta} == {w["id"] for w in changed},
        "jira_fields": sorted(issue_fields), "jira_fields_minimal": issue_fields <= set(c.JIRA_FIELDS),
        "auth_error_not_retried": auth_ok,
    }, land


# ------------------------------------------------------------------------ identity
def _pairs(groups: dict) -> set[tuple[str, str]]:
    return {tuple(sorted(p)) for g in groups.values() for p in combinations(sorted(g), 2)}


def identity(land) -> dict:
    g = gold("identity.json")
    keys = [k for k in g if not k.startswith("lms:")]
    truth = defaultdict(set)
    for k in keys:
        if g[k] != "external":
            truth[g[k]].add(k)
    gold_pairs = _pairs(truth)

    def score(of: dict[str, str]) -> dict:
        groups = defaultdict(set)
        for k in keys:
            if k in of:
                groups[of[k]].add(k)
        pred = _pairs(groups)
        out = prf(len(pred & gold_pairs), len(pred - gold_pairs), len(gold_pairs - pred))
        out["false_merges"] = len(pred - gold_pairs)
        return out

    everyone = land.workday + land.sf + land.jira
    by_email = {p.key: p.email.lower() for p in everyone if p.email}
    by_name = {p.key: fold(p.display) for p in everyone}
    by_local = {p.key: local_part(p.email) or f"#{p.key}" for p in everyone}
    res = resolve(land.workday, land.sf, land.jira, land.lms_emails)
    result = {
        "records": len(keys), "people": len(truth),
        "rules": score(res.of),
        "baseline_email_only": score({k: v for k, v in by_email.items()}),
        "baseline_name_only": score(by_name),
        "baseline_local_part": score(by_local),
        "review_queue": len(res.review),
        "unresolved_jira": sum(1 for k in res.unresolved if k.startswith("jira:")),
        "external_accounts": sum(1 for v in g.values() if v == "external"),
    }
    # after a data steward works the queue (simulated with the gold answer), recall should reach 100%
    of = dict(res.of)
    for item in res.review:
        rec = item["record"]
        same = [k for k in keys if g.get(k) == g.get(rec) and k != rec and k in of and k.split(":")[0] != rec.split(":")[0]]
        if same and g.get(rec) != "external":
            of[rec] = of[same[0]]
    result["after_steward"] = score(of)
    return result


# ------------------------------------------------------------------------ readiness
def readiness_suite(run: pipeline.Run) -> dict:
    planted = {(d["check"], d["object"]) for d in gold("defects.json")}
    found = {(f["check"], f["object"]) for f in run.ready["findings"] if f["check"] != "identity_review"}
    by_check = defaultdict(lambda: [0, 0])
    for chk, _ in planted:
        by_check[chk.split(":")[0]][0] += 1
    for chk, obj in found & planted:
        by_check[chk.split(":")[0]][1] += 1
    return {
        "planted": len(planted), "found": len(found & planted), "recall": round(len(found & planted) / len(planted), 4),
        "false_alarm_count": len(found - planted), "missed": sorted(map(list, planted - found)),
        "false_alarms": sorted(map(list, found - planted)), "by_check": {k: {"planted": v[0], "found": v[1]} for k, v in sorted(by_check.items())},
        "scores": run.ready["scores"], "thresholds": run.ready["thresholds"], "gate": run.ready["gate"], "ready_for_pilot": run.ready["ready_for_pilot"],
        "counts": run.ready["counts"], "findings": len(run.ready["findings"]), "quarantined": len(run.ready["quarantined"]),
        "identity_review": sum(1 for f in run.ready["findings"] if f["check"] == "identity_review"),
    }


# ------------------------------------------------------------------------ extraction
def texts(land) -> dict[str, str]:
    out = {j.job_id: j.description for j in land.jobs}
    out.update({a.ref: a.text for a in land.activities})
    return out


def extraction(land) -> dict:
    g = gold("texts.json")
    t = texts(land)
    out = {}
    for cfg in inference.CONFIGS:
        agg = defaultdict(lambda: [0, 0, 0])
        for tid, label in g.items():
            pred = inference.skills_in(t[tid], cfg)
            true = set(label["skills"])
            for k in ("all", f"lang:{label['lang']}", f"kind:{label['kind']}"):
                a = agg[k]
                a[0] += len(pred & true)
                a[1] += len(pred - true)
                a[2] += len(true - pred)
        out[cfg] = {k: prf(*v) for k, v in sorted(agg.items())}
        recalls = [v["recall"] for k, v in out[cfg].items() if k.startswith("lang:")]
        out[cfg]["language_recall_gap"] = round(max(recalls) - min(recalls), 4)
    out["texts"] = len(g)
    out["by_kind"] = {k: sum(1 for v in g.values() if v["kind"] == k) for k in ("job", "ticket", "course", "about")}
    out["by_lang"] = {k: sum(1 for v in g.values() if v["lang"] == k) for k in ("en", "nl", "de", "fr")}
    return out


# ------------------------------------------------------------------------ profiles
POLICIES = {
    "role_only": "every skill in the person's job profile (what most HCMs do today)",
    "work_only": "evidence from work and learning only, no job profile",
    "corroborated": "job profile plus work or learning evidence (default, ADR-0009)",
    "broad": "a job profile alone is enough to suggest",
}


def profiles(land) -> dict:
    base = pipeline.run(land)
    truth = simulate.truth_by_entity(base.res)
    truth = {e: s for e, s in truth.items() if e not in base.excluded}
    answer = simulate.responder(truth)

    def policy(name: str) -> dict[str, set[str]]:
        if name == "role_only":
            return {e: base.role_only.get(e, set()) for e in truth}
        weights = inference.BROAD_WEIGHTS if name == "broad" else None
        out = {}
        for e in truth:
            evs = [inference.Evidence(x.skill_id, x.kind, x.ref, x.sentence, x.on) for x in base.evidence.get(e, [])
                   if name != "work_only" or x.kind != "job"]
            out[e] = {s.skill_id for s in inference.suggestions(inference.profile(evs, land.as_of, weights))}
        return out

    result = {"people": len(truth), "true_skills_per_person": round(sum(map(len, truth.values())) / len(truth), 2),
              "evidence_coverage": round(sum(len(truth[e] & {x.skill_id for x in base.evidence.get(e, [])}) for e in truth)
                                         / sum(map(len, truth.values())), 4), "policies": {}}
    for name, desc in POLICIES.items():
        sugg = policy(name)
        tp = sum(len(sugg[e] & truth[e]) for e in truth)
        fp = sum(len(sugg[e] - truth[e]) for e in truth)
        fn = sum(len(truth[e] - sugg[e]) for e in truth)
        asked = sum(map(len, sugg.values()))
        acc = {e: {s for s in sugg[e] if answer(e, s) == "accept"} for e in truth}
        vtp = sum(len(acc[e] & truth[e]) for e in truth)
        vfp = sum(len(acc[e] - truth[e]) for e in truth)
        wrong_asks = sum(1 for e in truth for s in sugg[e] if s not in truth[e])
        result["policies"][name] = {
            "description": desc, "suggested": prf(tp, fp, fn), "asked_per_person": round(asked / len(truth), 2),
            "wrong_asks_per_person": round(wrong_asks / len(truth), 2),
            "validated": prf(vtp, vfp, sum(map(len, truth.values())) - vtp),
            "validated_per_person": round((vtp + vfp) / len(truth), 2),
        }
    return result


# ------------------------------------------------------------------------ crosswalk
def crosswalk_suite(run: pipeline.Run) -> dict:
    g = gold("crosswalk.json")
    maps = run.crosswalk["mappings"]
    auto = [m for m in maps if m["method"] in ("exact", "normalized")]
    fuzzy = [m for m in maps if m["method"] == "fuzzy"]
    none = [m for m in maps if m["method"] == "none"]
    key = lambda m: f"{m['source']}:{m['library_id']}"  # noqa: E731
    in_scope = [k for k, v in g.items() if v]
    return {
        "entries": len(maps), "in_scope": len(in_scope), "out_of_scope": len(g) - len(in_scope),
        "auto": len(auto), "auto_correct": sum(1 for m in auto if g[key(m)] == m["skill_id"]),
        "auto_precision": round(sum(1 for m in auto if g[key(m)] == m["skill_id"]) / max(1, len(auto)), 4),
        "fuzzy": len(fuzzy), "fuzzy_correct": sum(1 for m in fuzzy if g[key(m)] == m["skill_id"]),
        "unmapped": len(none), "unmapped_out_of_scope": sum(1 for m in none if g[key(m)] is None),
        "unmapped_in_scope": [m["name"] for m in none if g[key(m)]],
        "auto_coverage_of_in_scope": round(sum(1 for m in auto if g[key(m)]) / len(in_scope), 4),
        "steward_queue": run.crosswalk["steward_queue"],
    }


# ------------------------------------------------------------------------ write-back
def writeback_suite(land) -> dict:
    base = pipeline.run(land)
    truth = simulate.truth_by_entity(base.res)
    r = pipeline.run(land, responder=simulate.responder(truth))
    target = writeback.Target(land.profile_skills)
    target.apply(r.ops)
    first = target.applied
    target.apply(r.ops)                     # a retried batch: every key is known, nothing changes
    replayed = target.replayed
    again = pipeline.run(land, responder=simulate.responder(truth))
    from skillslayer.taxonomy import load
    names = {s.id: s.name for s in load().skills}
    validated = {e.workday_id: again.validated(eid) for eid, e in again.res.entities.items() if e.workday_id and eid not in again.excluded}
    rejected = {e.workday_id: again.rejected(eid) for eid, e in again.res.entities.items() if e.workday_id and eid not in again.excluded}
    second = writeback.plan(validated, rejected, target.rows, names, load().version)
    employee_before = sorted((p.worker_id, p.name) for p in land.profile_skills if p.source == "employee")
    employee_after = sorted((p.worker_id, p.name) for p in target.rows if p.source == "employee")
    return {
        "adds": sum(1 for o in r.ops if o.op == "add"), "removes": sum(1 for o in r.ops if o.op == "remove"),
        "applied_first_run": first, "replayed_batch_applied": target.applied - first, "replayed_batch_skipped": replayed,
        "second_run_ops": len(second), "employee_skills_before": len(employee_before),
        "employee_skills_untouched": employee_before == employee_after,
        "workers_touched": len({o.worker_id for o in r.ops}),
        "already_present_skipped": sum(1 for eid, e in r.res.entities.items() if e.workday_id for s in r.validated(eid)
                                       if any(p.worker_id == e.workday_id and (p.skill_id == s) for p in land.profile_skills)),
    }


# ------------------------------------------------------------------------ governance
def leaks(r: pipeline.Run) -> dict:
    out_keys = {k for eid in r.excluded for k in r.res.entities[eid].members}
    opted = {f"workday:{w}" for w in r.land.optouts["workday"]} | {f"successfactors:{s}" for s in r.land.optouts["successfactors"]}
    opted_eids = {r.res.of[k] for k in opted if k in r.res.of}
    quarantined_refs = set(r.ready["quarantined"]) if r.ready["quarantined"] else set()
    workday_of = {e.workday_id: eid for eid, e in r.res.entities.items() if e.workday_id}
    sf_of = {k.split(":", 1)[1]: eid for eid, e in r.res.entities.items() for k in e.members if k.startswith("successfactors:")}
    export_eids = {workday_of.get(x["EmployeeID"]) or sf_of.get(x["EmployeeID"]) for x in r.export_rows}
    return {
        "optout_people": len(opted_eids), "optout_records": len(opted & set(r.res.of)),
        "optout_with_evidence": sum(1 for e in opted_eids if r.evidence.get(e)),
        "optout_in_export": len(opted_eids & export_eids),
        "optout_in_writeback": sum(1 for o in r.ops if workday_of.get(o.worker_id) in opted_eids),
        "quarantined_text_used": sum(1 for evs in r.evidence.values() for e in evs if e.ref in quarantined_refs),
        "unvalidated_in_export": sum(1 for x in r.export_rows if x["Status"] != "validated"),
        "excluded_members": len(out_keys), "export_rows": len(r.export_rows),
    }


def governance(land) -> dict:
    base = pipeline.run(land)
    answer = simulate.responder(simulate.truth_by_entity(base.res))
    on = pipeline.run(land, responder=answer)
    ablation = {}
    for name, gov in {
        "all controls": pipeline.Governance(),
        "no opt-out filter": pipeline.Governance(honour_optouts=False),
        "no quarantine": pipeline.Governance(quarantine_sensitive=False),
        "inferred skills downstream": pipeline.Governance(validated_only_downstream=False),
    }.items():
        r = pipeline.run(land, responder=answer, gov=gov)
        # measure leaks against the true opt-out list and the true quarantine list, whatever the run did
        r.excluded, saved = on.excluded, r.excluded
        r.ready = {**r.ready, "quarantined": on.ready["quarantined"]}
        lk = leaks(r)
        r.excluded = saved
        ablation[name] = {k: lk[k] for k in ("optout_with_evidence", "optout_in_export", "optout_in_writeback", "quarantined_text_used", "unvalidated_in_export")}
        ablation[name]["total"] = sum(ablation[name].values())
    return {"with_controls": leaks(on), "ablation": ablation}


# ------------------------------------------------------------------------ report + gate
def build_report() -> dict:
    conn, land = connectors()
    base = pipeline.run(land)
    return {
        "as_of": AS_OF.isoformat(),
        "connectors": conn,
        "identity": identity(land),
        "readiness": readiness_suite(base),
        "extraction": extraction(land),
        "profiles": profiles(land),
        "crosswalk": crosswalk_suite(base),
        "writeback": writeback_suite(land),
        "governance": governance(land),
    }


def dig(d: dict, path: str):
    for part in path.split("."):
        d = d[part]
    return d


def gate(report: dict) -> list[str]:
    fails = []
    for path, rule in THRESHOLDS.items():
        v = dig(report, path)
        if "min" in rule and v < rule["min"]:
            fails.append(f"{path} = {v} < {rule['min']}")
        if "max" in rule and v > rule["max"]:
            fails.append(f"{path} = {v} > {rule['max']}")
        if "equals" in rule and v != rule["equals"]:
            fails.append(f"{path} = {v} != {rule['equals']}")
    return fails


def summary(r: dict) -> str:
    e, p, i, g = r["extraction"], r["profiles"]["policies"], r["identity"], r["governance"]
    lines = [
        f"connectors  complete={r['connectors']['complete']} faults={r['connectors']['faults_injected']} retries={r['connectors']['retries']} delta={r['connectors']['delta_fetched']}/{r['connectors']['delta_changed']}",
        f"identity    rules P={i['rules']['precision']:.3f} R={i['rules']['recall']:.3f} false merges={i['rules']['false_merges']} review={i['review_queue']} | name-only false merges={i['baseline_name_only']['false_merges']}",
        f"readiness   planted {r['readiness']['planted']}, found {r['readiness']['found']}, false alarms {len(r['readiness']['false_alarms'])}, ready={r['readiness']['ready_for_pilot']}",
    ]
    for cfg in inference.CONFIGS:
        a = e[cfg]["all"]
        lines.append(f"extract {cfg}   P={a['precision']:.3f} R={a['recall']:.3f} F1={a['f1']:.3f} language gap={e[cfg]['language_recall_gap']:.3f}")
    for name, v in p.items():
        lines.append(f"policy {name:<13} suggested P={v['suggested']['precision']:.3f} R={v['suggested']['recall']:.3f} asked/person={v['asked_per_person']} validated P={v['validated']['precision']:.3f}")
    lines.append(f"crosswalk   auto {r['crosswalk']['auto_correct']}/{r['crosswalk']['auto']} correct, steward queue {r['crosswalk']['steward_queue']}")
    lines.append(f"writeback   ops={r['writeback']['adds']}+{r['writeback']['removes']} second run={r['writeback']['second_run_ops']} employee skills untouched={r['writeback']['employee_skills_untouched']}")
    lines.append("governance  " + ", ".join(f"{k}: {v['total']}" for k, v in g["ablation"].items()))
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gate", action="store_true")
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    report = build_report()
    print(summary(report))
    if args.write:
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(json.dumps(report, indent=1, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
    if args.gate:
        fails = gate(report)
        for f in fails:
            print("GATE FAIL", f)
        print("gate: pass" if not fails else f"gate: {len(fails)} failure(s)")
        return 1 if fails else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
