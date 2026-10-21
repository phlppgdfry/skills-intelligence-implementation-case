"""Build: one command keeps code, evals, docs and site consistent.

    python3 scripts/build.py           # regenerate everything
    python3 scripts/build.py --check   # CI: fail if anything is stale

1. evals/reports/offline.json from the eval suites
2. site/data/*.json: the report, readiness findings, demo people, run log, cards
3. every <!--n:path-->value<!--/n--> marker in README, docs and site is rewritten
   from the report, so no document can quote a stale number
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from evals import simulate  # noqa: E402
from evals.run import REPORT, build_report  # noqa: E402
from skillslayer import pipeline  # noqa: E402
from skillslayer.landscape import fetch  # noqa: E402
from skillslayer.mock.servers import TOKEN, MockServer  # noqa: E402
from skillslayer.taxonomy import load  # noqa: E402
from skillslayer.teams import validation_card  # noqa: E402

MARKER = re.compile(r"<!--n:([\w.:\- ]+)-->(.*?)<!--/n-->", re.S)
PCT = re.compile(r"(precision|recall|f1|gap|scores|coverage|auto_precision|thresholds)")
DEMO_PEOPLE = ["W30579", "W30459", "W30012", "kdwebst66", "W30570"]


def fmt(path: str, v) -> str:
    if isinstance(v, bool):
        return "yes" if v else "no"
    if isinstance(v, int):
        return f"{v:,}"
    if isinstance(v, float):
        if PCT.search(path):
            x = v * 100
            return f"{x:.0f}%" if abs(x - round(x)) < 0.05 else f"{x:.1f}%"
        return f"{v:.2f}".rstrip("0").rstrip(".")
    return str(v)


def flatten(d, prefix: str = "") -> dict[str, str]:
    out: dict[str, str] = {}
    if isinstance(d, dict):
        for k, v in d.items():
            out.update(flatten(v, f"{prefix}{k}."))
    elif isinstance(d, list):
        out[prefix[:-1] + ".count"] = str(len(d))
    else:
        out[prefix[:-1]] = fmt(prefix[:-1], d)
    return out


def demo(report: dict) -> dict:
    with MockServer(faults=True) as m:
        land = fetch(m.url, TOKEN)
        faults = list(m.state.faults_served)
    base = pipeline.run(land)
    answer = simulate.responder(simulate.truth_by_entity(base.res))
    r = pipeline.run(land, responder=answer)
    tax = load().by_id
    people = []
    for who in DEMO_PEOPLE:
        eid = next(e for e, ent in r.res.entities.items() if any(k.endswith(":" + who) for k in ent.members))
        ent = r.res.entities[eid]
        scores = sorted(r.profiles.get(eid, {}).values(), key=lambda s: -s.score)
        people.append({
            "id": eid, "name": ent.name, "records": ent.members, "opted_out": eid in r.excluded,
            "skills": [{"id": s.skill_id, "name": tax[s.skill_id].name, "cluster": tax[s.skill_id].cluster, "score": s.score,
                        "suggested": s in r.suggested.get(eid, []), "decision": r.decisions.get(eid, {}).get(s.skill_id),
                        "evidence": [{"kind": e.kind, "ref": e.ref, "weight": e.weight, "sentence": e.sentence} for e in s.evidence[:4]]}
                       for s in scores],
            "card": None if eid in r.excluded else validation_card(ent.name.split()[0], r.suggested.get(eid, []), "run-2026-10-01"),
            # the idempotency key is published as op_id: a 16-hex "key" field trips secret scanners
            "ops": [{"op": o.op, "skill_id": o.skill_id, "skill_name": o.skill_name, "op_id": o.key} for o in r.ops if o.worker_id == ent.workday_id],
        })
    return {
        "people": people,
        "runlog": {"stats": [s.__dict__ for s in land.stats], "faults": faults, "entities": len(r.res.entities),
                   "review": len(r.res.review), "excluded": len(r.excluded), "quarantined": len(r.ready["quarantined"]),
                   "suggestions": sum(len(v) for v in r.suggested.values()),
                   "decisions": {d: sum(1 for v in r.decisions.values() for x in v.values() if x == d) for d in ("accept", "reject", "unsure")},
                   "adds": sum(o.op == "add" for o in r.ops), "removes": sum(o.op == "remove" for o in r.ops), "export_rows": len(r.export_rows)},
        "findings": r.ready["findings"],
        "crosswalk": r.crosswalk["mappings"],
        "review": r.res.review[:12],
        "export_sample": r.export_rows[:8],
    }


def render(report: dict) -> dict[Path, str]:
    nums = flatten(report)
    files: dict[Path, str] = {
        REPORT: json.dumps(report, indent=1, ensure_ascii=False, default=str) + "\n",
        ROOT / "site" / "data" / "report.json": json.dumps(report, ensure_ascii=False, default=str) + "\n",
        ROOT / "site" / "data" / "demo.json": json.dumps(demo(report), ensure_ascii=False, default=str) + "\n",
    }
    docs = [p for p in (ROOT / "README.md", ROOT / "EVIDENCE.md", *sorted((ROOT / "docs").rglob("*.md")), *sorted((ROOT / "site").rglob("*.html"))) if p.exists()]
    missing: set[str] = set()
    for p in docs:
        text = p.read_text(encoding="utf-8")

        def sub(m: re.Match) -> str:
            key = m.group(1)
            if key not in nums:
                missing.add(f"{p.relative_to(ROOT)}: {key}")
                return m.group(0)
            return f"<!--n:{key}-->{nums[key]}<!--/n-->"

        new = MARKER.sub(sub, text)
        if new != text:
            files[p] = new
    if missing:
        raise SystemExit("unknown number keys:\n  " + "\n  ".join(sorted(missing)))
    return files


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    files = render(build_report())
    stale = [p for p, c in files.items() if not p.exists() or p.read_text(encoding="utf-8") != c]
    if args.check:
        for p in stale:
            print("stale:", p.relative_to(ROOT))
        print("build is up to date" if not stale else "run: python3 scripts/build.py")
        return 1 if stale else 0
    for p in stale:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(files[p], encoding="utf-8")
    print(f"updated {len(stale)} file(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
