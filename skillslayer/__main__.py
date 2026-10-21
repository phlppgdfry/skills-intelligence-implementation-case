"""Command line for the implementation toolkit.

    python -m skillslayer readiness                 # AI-readiness scorecard and top findings
    python -m skillslayer sync [--simulate]         # full run against the mock tenants, with a run log
    python -m skillslayer profile <name or id>      # one person's suggested skills and why
    python -m skillslayer card <name or id>         # the Teams validation card (Adaptive Card JSON)
    python -m skillslayer crosswalk                 # how the customer's own libraries map
    python -m skillslayer export                    # the people-analytics flat file (CSV) to stdout
    python -m skillslayer mocks [--port 8787]       # run the mock Workday / SuccessFactors / Jira APIs
"""

from __future__ import annotations

import argparse
import json
import sys
import time

from . import pipeline
from .identity import fold
from .landscape import fetch
from .mock.servers import TOKEN, MockServer
from .taxonomy import load
from .teams import validation_card


def _land(faults: bool = True):
    with MockServer(faults=faults) as m:
        return fetch(m.url, TOKEN)


def _responder(simulate: bool, land):
    if not simulate:
        return None
    from evals import simulate as sim  # simulated employees; reads the gold labels, demo only
    base = pipeline.run(land)
    return sim.responder(sim.truth_by_entity(base.res))


def _find(r: pipeline.Run, who: str) -> str:
    q = fold(who)
    for eid, e in r.res.entities.items():
        if who in (eid, e.workday_id) or q == fold(e.name) or any(k.endswith(":" + who) for k in e.members):
            return eid
    sys.exit(f"nobody matches {who!r}")


def cmd_readiness(_: argparse.Namespace) -> None:
    r = pipeline.run(_land())
    rep = r.ready
    print("AI-readiness scorecard (pilot gate in brackets)\n")
    for k, v in rep["scores"].items():
        mark = "PASS" if rep["gate"][k] else "FAIL"
        bar = f"{rep['thresholds'][k]:.0%}" if k in rep["thresholds"] else "all flagged quarantined"
        print(f"  {k:<18} {v:6.1%}  [{bar}]  {mark}")
    print(f"\n  ready for pilot: {'yes' if rep['ready_for_pilot'] else 'no'}")
    print(f"  findings: {rep['counts']}\n")
    for f in rep["findings"][:12]:
        print(f"  [{f['severity']:<8}] {f['check']:<32} {f['object']:<22} -> {f['owner']}: {f['fix']}")
    if len(rep["findings"]) > 12:
        print(f"  … and {len(rep['findings']) - 12} more")


def cmd_sync(a: argparse.Namespace) -> None:
    t0 = time.time()
    with MockServer(faults=True) as m:
        land = fetch(m.url, TOKEN)
        faults = m.state.faults_served
    r = pipeline.run(land, responder=_responder(a.simulate, land))
    print("run log")
    for s in land.stats:
        print(f"  fetch {s.source:<30} {s.records:>5} records  {s.pages:>3} pages  {s.retries} retries")
    print(f"  faults injected by the mock tenants: {', '.join(faults)}")
    print(f"  identities: {len(r.res.entities)} people, {len(r.res.review)} for the steward, {len(r.res.unresolved)} unresolved")
    print(f"  excluded (opt-out): {len(r.excluded)} people; quarantined texts: {len(r.ready['quarantined'])}")
    n = sum(len(v) for v in r.suggested.values())
    print(f"  suggestions: {n} for {sum(1 for v in r.suggested.values() if v)} people")
    if a.simulate:
        dec = [d for v in r.decisions.values() for d in v.values()]
        print(f"  validation (simulated): {dec.count('accept')} accepted, {dec.count('reject')} rejected, {dec.count('unsure')} unsure")
    print(f"  write-back plan: {sum(o.op == 'add' for o in r.ops)} adds, {sum(o.op == 'remove' for o in r.ops)} removes (dry run)")
    print(f"  analytics export: {len(r.export_rows)} validated rows")
    print(f"  done in {time.time() - t0:.1f}s")


def cmd_profile(a: argparse.Namespace) -> None:
    r = pipeline.run(_land(False))
    eid = _find(r, a.who)
    e = r.res.entities[eid]
    tax = load().by_id
    print(f"{e.name} ({eid}) — records: {', '.join(f'{k} [{v}]' for k, v in e.members.items())}")
    if eid in r.excluded:
        print("  opted out: no data is processed for this person.")
        return
    scores = sorted(r.profiles.get(eid, {}).values(), key=lambda s: -s.score)
    for s in scores:
        tag = "SUGGEST" if s in r.suggested.get(eid, []) else "below threshold"
        print(f"\n  {tax[s.skill_id].name}  score {s.score:.2f}  ({tag})")
        for ev in s.evidence[:4]:
            print(f"    {ev.kind:<6} {ev.ref:<22} w={ev.weight:.2f}  “{ev.sentence[:80]}”")


def cmd_card(a: argparse.Namespace) -> None:
    r = pipeline.run(_land(False))
    eid = _find(r, a.who)
    if eid in r.excluded:
        sys.exit("this person opted out: no card is sent")
    first = r.res.entities[eid].name.split()[0]
    print(json.dumps(validation_card(first, r.suggested.get(eid, []), "run-2026-10-01"), indent=1, ensure_ascii=False))


def cmd_crosswalk(_: argparse.Namespace) -> None:
    r = pipeline.run(_land(False))
    cw = r.crosswalk
    print(f"{cw['entries']} library entries: {cw['by_method']}; steward queue {cw['steward_queue']}\n")
    tax = load().by_id
    for m in cw["mappings"]:
        target = tax[m["skill_id"]].name if m["skill_id"] else "—"
        print(f"  {m['source']:<15} {m['library_id']:<9} {m['name'][:34]:<34} {m['method']:<10} {target}")


def cmd_export(a: argparse.Namespace) -> None:
    land = _land(False)
    r = pipeline.run(land, responder=_responder(True, land))
    sys.stdout.write(pipeline.export_csv(r.export_rows))


def cmd_mocks(a: argparse.Namespace) -> None:
    with MockServer(faults=not a.no_faults, port=a.port) as m:
        print(f"mock tenants on {m.url}  (Authorization: Bearer {TOKEN})")
        print(f"  {m.url}/workday/ccx/api/v1/norvane_impl/workers?limit=5")
        print(f"  {m.url}/sf/odata/v2/User?$format=json")
        print(f"  {m.url}/jira/rest/api/3/search/jql?jql=statusCategory%3DDone&maxResults=5")
        try:
            while True:
                time.sleep(3600)
        except KeyboardInterrupt:
            pass


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(prog="skillslayer")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("readiness").set_defaults(f=cmd_readiness)
    s = sub.add_parser("sync")
    s.add_argument("--simulate", action="store_true", help="simulate employees answering the validation card")
    s.set_defaults(f=cmd_sync)
    for name, f in (("profile", cmd_profile), ("card", cmd_card)):
        p = sub.add_parser(name)
        p.add_argument("who")
        p.set_defaults(f=f)
    sub.add_parser("crosswalk").set_defaults(f=cmd_crosswalk)
    sub.add_parser("export").set_defaults(f=cmd_export)
    m = sub.add_parser("mocks")
    m.add_argument("--port", type=int, default=8787)
    m.add_argument("--no-faults", action="store_true")
    m.set_defaults(f=cmd_mocks)
    a = ap.parse_args(argv)
    a.f(a)


if __name__ == "__main__":
    main()
