"""Step 1 of a search run: create the run folder and pull every scripted source.

  python3 tools/search.py --budget 1500 --area "Oost, De Pijp" [--types apartment,studio] [--radius 5]

Writes runs/<stamp>/params.json and runs/<stamp>/raw_scripted.json, prints the run folder.
Browser-only sources (Pararius, Kamer.nl, Huurstunt, landlord portals...) are collected afterwards by
the Claude session into runs/<stamp>/raw_browser.json (see .claude/skills/find-apartment/SKILL.md).
"""
import argparse
import datetime as dt
import json
import os
import sys
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "sources"))
ROOT = os.path.dirname(HERE)

import geo  # noqa: E402
from common import log  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--budget", type=int, required=True, help="max monthly rent in EUR")
    ap.add_argument("--area", default="", help="free text; comma-separated areas; empty = all Amsterdam")
    ap.add_argument("--types", default="apartment,studio,house", help="apartment,studio,house,room")
    ap.add_argument("--radius", type=int, default=0, help="km around Amsterdam centre for Kamernet (0 = auto)")
    ap.add_argument("--min-size", type=int, default=0)
    ap.add_argument("--sources", default="kamernet,housinganywhere,directwonen,marktplaats")
    ap.add_argument("--run", default="", help="reuse an existing run folder")
    a = ap.parse_args()

    spec = geo.resolve_area(a.area)
    types = tuple(t.strip() for t in a.types.split(",") if t.strip())
    radius = a.radius or (10 if spec.get("municipalities") else 5)
    stamp = dt.datetime.now().strftime("%Y-%m-%d_%H%M")
    run = a.run or os.path.join(ROOT, "runs", stamp)
    os.makedirs(run, exist_ok=True)
    params = {"budget": a.budget, "area": a.area, "area_label": spec.get("label"), "types": list(types),
              "min_size": a.min_size, "radius_km": radius, "started": dt.datetime.now().isoformat(timespec="minutes"),
              "area_unmatched": spec.get("unmatched", [])}
    json.dump(params, open(os.path.join(run, "params.json"), "w"), indent=1)
    if spec.get("unmatched"):
        log(f"WARNING: area terms not recognised: {spec['unmatched']} (they will be matched by text only)")

    results, status = [], {}
    for name in a.sources.split(","):
        name = name.strip()
        try:
            if name == "kamernet":
                import kamernet
                recs = kamernet.search(a.budget, types=types, radius=radius)
            elif name == "housinganywhere":
                import housinganywhere
                recs = housinganywhere.search(a.budget, types=types)
            elif name == "directwonen":
                import directwonen
                recs = directwonen.search(a.budget, types=types)
            elif name == "marktplaats":
                import marktplaats
                recs = marktplaats.search(a.budget, types=types, distance_m=radius * 1000 + 5000)
            else:
                log("unknown source", name); continue
            results += recs
            status[name] = {"ok": True, "count": len(recs)}
        except Exception as e:  # noqa: BLE001
            traceback.print_exc()
            status[name] = {"ok": False, "error": str(e)[:300]}
    json.dump(results, open(os.path.join(run, "raw_scripted.json"), "w"), indent=1, ensure_ascii=False)
    json.dump(status, open(os.path.join(run, "status_scripted.json"), "w"), indent=1)
    log(json.dumps(status))
    print(run)


if __name__ == "__main__":
    main()
