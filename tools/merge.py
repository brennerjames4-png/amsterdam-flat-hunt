"""Step 3 of a search run: combine all raw listings, locate, filter, classify, dedupe, rank.

  python3 tools/merge.py runs/<stamp>

Reads params.json, raw_scripted.json, raw_browser.json (optional), verdicts.json (optional: the
session's manual verdicts for 'unverified' advertisers / listing checks). Writes results.json with
'leases', 'sublets', 'excluded' (with reasons) and 'stats'.
"""
import json
import os
import re
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import classify  # noqa: E402
import geo  # noqa: E402
from common import LISTING_FIELDS, log  # noqa: E402


def load(path, default):
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        return default


def dedupe_key(r):
    street = geo.norm(r.get("street") or "")
    street = re.sub(r"[^a-z]", "", street)
    return (street, r.get("price_eur"), r.get("size_m2")) if street and r.get("price_eur") else ("id", r["source"], r["source_id"])


def main(run):
    params = load(os.path.join(run, "params.json"), None)
    if not params:
        sys.exit("params.json missing: run tools/search.py first")
    budget, types, min_size = params["budget"], set(params["types"]), params.get("min_size", 0)
    spec = geo.resolve_area(params.get("area"))
    raw = load(os.path.join(run, "raw_scripted.json"), []) + load(os.path.join(run, "raw_browser.json"), [])
    verdicts = load(os.path.join(run, "verdicts.json"), {})  # {"source:source_id": {"verdict":..,"tenure":..,"reject":..,"note":..}}
    registry = classify.load_registry()

    kept, excluded, seen = [], [], {}
    for r in raw:
        r = {**LISTING_FIELDS, **r}
        key = f"{r['source']}:{r['source_id']}"
        # ---- price / type / size
        if not r.get("price_eur"):
            excluded.append({**r, "excluded_because": "no price"}); continue
        if r["price_eur"] > budget:
            excluded.append({**r, "excluded_because": f"over budget (EUR {r['price_eur']})"}); continue
        if r.get("property_type") not in types and r.get("property_type") != "unknown":
            excluded.append({**r, "excluded_because": f"type {r.get('property_type')}"}); continue
        if min_size and r.get("size_m2") and r["size_m2"] < min_size:
            excluded.append({**r, "excluded_because": f"smaller than {min_size} m²"}); continue
        if r.get("size_m2") and (r["size_m2"] > 400 or r["size_m2"] < 8):
            r["size_m2"] = None  # implausible, site data error
        if r.get("available_to"):
            import datetime as _dt
            if r["available_to"] < (_dt.date.today() + _dt.timedelta(days=21)).isoformat():
                excluded.append({**r, "excluded_because": f"sublet ends too soon ({r['available_to']})"}); continue
        # ---- location
        g = None
        if r.get("lat") is None and (r.get("postcode") or r.get("street")):
            if r.get("postcode"):
                g = geo.geocode(r["postcode"].replace(" ", ""))
            else:
                g = geo.geocode(r.get("street"), place=r.get("city") or "Amsterdam")
            if g:
                r["lat"], r["lng"] = g["lat"], g["lng"]
                r["postcode"] = r.get("postcode") or g.get("postcode")
        loc = geo.locate(r["lat"], r["lng"]) if r.get("lat") is not None else {}
        muni = (g or {}).get("municipality") or geo.municipality_of(r.get("city"))
        r["district"], r["area_name"], r["neighbourhood"] = loc.get("stadsdeel"), loc.get("gebied"), loc.get("wijk")
        if not r["district"] and muni and geo.norm(muni) != "amsterdam":
            r["district"] = muni
        m = geo.area_match(spec, loc, r.get("postcode"), muni, (r.get("title") or "") + " " + (r.get("description") or ""), has_coords=r.get("lat") is not None)
        if m is False:
            excluded.append({**r, "excluded_because": f"outside area ({r.get('neighbourhood') or r.get('district') or muni})"}); continue
        r["area_confirmed"] = m is True
        # ---- judgement
        verdict, vreason = classify.classify_advertiser(r, registry)
        manual = verdicts.get(key, {})
        if manual.get("verdict") and manual["verdict"] not in ("private", "landlord", "manager", "agent", "unverified"):
            manual["verdict"] = "unverified"
        if r.get("deposit_eur") is not None and r["deposit_eur"] < 100:
            r["deposit_eur"] = None  # site data-entry error (e.g. EUR 14)
        if manual.get("verdict"):
            verdict, vreason = manual["verdict"], manual.get("note") or "verified by agent"
        tenure, treason = classify.classify_tenure(r, verdict)
        if manual.get("tenure"):
            tenure, treason = manual["tenure"], manual.get("note") or treason
        red, notes, reject = classify.flags(r, verdict, tenure)
        if manual.get("reject"):
            reject = manual["reject"]
        auto_red = list(red)
        if manual.get("red_flags"):
            red += [f"Checked: {f}" for f in manual["red_flags"]]
        r.update({"advertiser_verdict": verdict, "advertiser_reason": vreason, "tenure": tenure, "tenure_reason": treason,
                  "red_flags": red, "notes": notes})
        if reject:
            excluded.append({**r, "excluded_because": reject}); continue
        if len(auto_red) >= 3:  # verifier cautions are shown, never auto-exclude
            excluded.append({**r, "excluded_because": "too many red flags: " + "; ".join(red)}); continue
        r["score"] = classify.score(r, verdict, tenure, auto_red + manual.get("red_flags", [])[:1], budget)
        if manual.get("note"):
            r["notes"] = [f"Checked by agent: {manual['note']}"] + r["notes"]
        # ---- dedupe across sites (keep higher score, remember other URLs)
        dk = dedupe_key(r)
        if dk in seen:
            other = seen[dk]
            keep, drop = (r, other) if r["score"] > other["score"] else (other, r)
            keep.setdefault("also_on", []).append({"source": drop["source"], "url": drop["url"]})
            seen[dk] = keep
            continue
        seen[dk] = r
    kept = list(seen.values())
    kept.sort(key=lambda x: (-x["score"], x["price_eur"]))
    geo.save_cache()
    out = {
        "params": params,
        "leases": [r for r in kept if r["tenure"] == "lease"],
        "sublets": [r for r in kept if r["tenure"] == "sublet"],
        "excluded": excluded,
        "stats": {
            "raw": len(raw),
            "kept": len(kept),
            "by_source_raw": Counter(r["source"] for r in raw),
            "by_source_kept": Counter(r["source"] for r in kept),
            "excluded_reasons": Counter(re.sub(r"\(.*", "", e["excluded_because"]).strip()[:60] for e in excluded),
            "unverified": sum(1 for r in kept if r["advertiser_verdict"] == "unverified"),
            "source_status": {**load(os.path.join(run, "status_scripted.json"), {}), **load(os.path.join(run, "status_browser.json"), {})},
        },
    }
    json.dump(out, open(os.path.join(run, "results.json"), "w"), indent=1, ensure_ascii=False)
    log(f"leases {len(out['leases'])}, sublets {len(out['sublets'])}, excluded {len(excluded)}, unverified {out['stats']['unverified']}")
    for k, v in out["stats"]["excluded_reasons"].most_common(8):
        log(f"  excluded {v}: {k}")


if __name__ == "__main__":
    main(sys.argv[1])
