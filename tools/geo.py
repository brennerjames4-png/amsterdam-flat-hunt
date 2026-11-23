"""Amsterdam geography: locate a listing in district/area/neighbourhood and match a user's area request.

Uses the city's official boundaries (api.data.amsterdam.nl, saved in data/*.geojson) and
PDOK, the Dutch government geocoder, for postcode/street -> coordinates. Standard library only.
"""
import json
import os
import re
import unicodedata
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
CACHE_FILE = os.path.join(DATA, "geocode_cache.json")
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"

# Municipalities next to Amsterdam that people commonly accept as "Amsterdam area".
NEARBY_MUNICIPALITIES = ["Amstelveen", "Diemen", "Zaanstad", "Haarlem", "Ouder-Amstel", "Haarlemmermeer", "Landsmeer", "Oostzaan"]
# Place names seen in listings -> their municipality.
PLACE_TO_MUNICIPALITY = {"zaandam": "Zaanstad", "zaandijk": "Zaanstad", "koog aan de zaan": "Zaanstad", "wormerveer": "Zaanstad",
                         "assendelft": "Zaanstad", "badhoevedorp": "Haarlemmermeer", "hoofddorp": "Haarlemmermeer",
                         "lijnden": "Haarlemmermeer", "zwanenburg": "Haarlemmermeer", "duivendrecht": "Ouder-Amstel",
                         "ouderkerk aan de amstel": "Ouder-Amstel", "weesp": "Amsterdam", "driemond": "Amsterdam"}


def municipality_of(place):
    if not place:
        return None
    return PLACE_TO_MUNICIPALITY.get(norm(place), place)

# Everyday names -> official names (lower-case, accent-free). Values may be district (stadsdeel),
# area (ggw-gebied) or neighbourhood (wijk) names, or municipalities.
ALIASES = {
    "centre": ["centrum"], "center": ["centrum"], "city centre": ["centrum"], "city center": ["centrum"],
    "canal ring": ["grachtengordel-west", "grachtengordel-zuid"], "grachtengordel": ["grachtengordel-west", "grachtengordel-zuid"],
    "de pijp": ["oude pijp", "nieuwe pijp", "zuid pijp"], "pijp": ["oude pijp", "nieuwe pijp", "zuid pijp"],
    "jordaan": ["jordaan"], "red light district": ["burgwallen-oude zijde"], "de wallen": ["burgwallen-oude zijde"],
    "oud-west": ["oud-west, de baarsjes"], "oud west": ["oud-west, de baarsjes"], "old west": ["oud-west, de baarsjes"],
    "de baarsjes": ["oud-west, de baarsjes"], "baarsjes": ["oud-west, de baarsjes"],
    "oud-zuid": ["oud-zuid"], "oud zuid": ["oud-zuid"], "museum quarter": ["museumkwartier"], "museumkwartier": ["museumkwartier"],
    "rivierenbuurt": ["rivierenbuurt"], "zuidas": ["zuidas"], "buitenveldert": ["buitenveldert-west", "buitenveldert-oost"],
    "watergraafsmeer": ["watergraafsmeer"], "ijburg": ["ijburg-west", "ijburg-zuid", "ijburg-oost"],
    "indische buurt": ["indische buurt-west", "indische buurt-oost"], "dapperbuurt": ["dapperbuurt"],
    "oosterparkbuurt": ["oosterparkbuurt"], "oost": ["oost"], "east": ["oost"], "west": ["west"], "south": ["zuid"],
    "north": ["noord"], "new west": ["nieuw-west"], "nieuw west": ["nieuw-west"], "south east": ["zuidoost"],
    "southeast": ["zuidoost"], "bijlmer": ["bijlmer-centrum", "bijlmer-oost", "bijlmer-west", "bijlmermuseum", "h-buurt", "k-buurt", "ganzenhoef e.o.", "amsterdamse poort e.o."], "westerpark": ["westerpark"],
    "bos en lommer": ["bos en lommer"], "noord": ["noord"], "amsterdam noord": ["noord"], "amsterdam-noord": ["noord"],
    "eastern docklands": ["oostelijk havengebied"], "oostelijk havengebied": ["oostelijk havengebied"],
    "plantage": ["weesperbuurt/plantage"], "weesperbuurt": ["weesperbuurt/plantage"],
    "slotervaart": ["slotervaart"], "osdorp": ["osdorp"], "sloterdijk": ["sloterdijk nieuw-west"],
    "amstelveen": ["amstelveen"], "diemen": ["diemen"], "zaandam": ["zaanstad"], "haarlem": ["haarlem"], "weesp": ["weesp binnenstad/zuid", "weesp-noordwest", "weesp, driemond"],
}


def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower().strip()
    return re.sub(r"\s+", " ", s)


def _load(name):
    with open(os.path.join(DATA, name + ".geojson")) as f:
        feats = json.load(f)["features"]
    out = []
    for ft in feats:
        p = ft["properties"]
        if p.get("eindGeldigheid"):
            continue
        g = ft["geometry"]
        polys = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
        out.append({"name": p["naam"], "id": p.get("identificatie"), "stadsdeel_id": p.get("ligtInStadsdeelId"), "polys": polys})
    return out


_LAYERS = None


def layers():
    global _LAYERS
    if _LAYERS is None:
        _LAYERS = {"stadsdeel": _load("stadsdelen"), "gebied": _load("gebieden"), "wijk": _load("wijken")}
    return _LAYERS


def _in_ring(x, y, ring):
    inside = False
    j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-12) + xi:
            inside = not inside
        j = i
    return inside


def _in_poly(lng, lat, poly):
    return _in_ring(lng, lat, poly[0]) and not any(_in_ring(lng, lat, h) for h in poly[1:])


def locate(lat, lng):
    """Return {'stadsdeel','gebied','wijk'} names for a coordinate inside Amsterdam (None outside)."""
    res = {}
    for key, feats in layers().items():
        res[key] = next((f["name"] for f in feats if any(_in_poly(lng, lat, p) for p in f["polys"])), None)
    return res


# ---------- geocoding (PDOK) ----------
_cache = None


def _cache_get():
    global _cache
    if _cache is None:
        try:
            with open(CACHE_FILE) as f:
                _cache = json.load(f)
        except Exception:
            _cache = {}
    return _cache


def save_cache():
    if _cache is not None:
        with open(CACHE_FILE, "w") as f:
            json.dump(_cache, f)


def geocode(query, place=None):
    """Postcode / street (+ place) -> {'lat','lng','municipality','postcode'} via PDOK. Cached.
    Pass place (e.g. 'Amsterdam') for street lookups, otherwise PDOK may pick a same-named street elsewhere."""
    if not query:
        return None
    c = _cache_get()
    key = norm(query) + ("|" + norm(place) if place else "")
    if key in c:
        return c[key]
    params = {"q": query, "rows": 1, "fl": "centroide_ll,gemeentenaam,postcode,woonplaatsnaam,weergavenaam"}
    url = "https://api.pdok.nl/bzk/locatieserver/search/v3_1/free?" + urllib.parse.urlencode(params)
    if place:
        url += "&" + urllib.parse.urlencode({"fq": f'woonplaatsnaam:"{place}"'})
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        docs = json.load(urllib.request.urlopen(req, timeout=15))["response"]["docs"]
    except Exception:
        return None
    out = None
    if docs:
        d = docs[0]
        m = re.match(r"POINT\(([\d.]+) ([\d.]+)\)", d.get("centroide_ll", ""))
        if m:
            out = {"lng": float(m.group(1)), "lat": float(m.group(2)), "municipality": d.get("gemeentenaam"),
                   "place": d.get("woonplaatsnaam"), "postcode": d.get("postcode"), "label": d.get("weergavenaam")}
    c[key] = out
    return out


# ---------- area matching ----------
def resolve_area(area):
    """Turn the user's free-text area into a matcher spec.

    Returns {'any': True} for no restriction, else {'names': set of normalized official names,
    'municipalities': set, 'postcode_prefixes': set, 'label': str, 'unmatched': [tokens]}.
    Multiple areas can be separated by commas, '/', ' or ', ' and ', '+'.
    """
    if not area or norm(area) in ("", "any", "anywhere", "all", "amsterdam", "all of amsterdam", "whole city"):
        return {"any": True, "label": "All of Amsterdam"}
    all_names = {norm(f["name"]): (lvl, f["name"]) for lvl, feats in layers().items() for f in feats}
    spec = {"names": set(), "municipalities": set(), "postcode_prefixes": set(), "label": area, "unmatched": []}
    for tok in re.split(r",|/|\+|\bor\b|\band\b|;", area, flags=re.I):
        t = norm(tok).replace("amsterdam ", "").strip() if norm(tok) not in ALIASES else norm(tok)
        if not t:
            continue
        if re.fullmatch(r"\d{4}( ?[a-z]{2})?", t) or re.fullmatch(r"\d{2,3}", t):
            spec["postcode_prefixes"].add(t[:4].replace(" ", ""))
            continue
        targets = ALIASES.get(t) or ALIASES.get(norm(tok)) or [t]
        hit = False
        for tg in targets:
            if tg in all_names:
                spec["names"].add(tg); hit = True
            elif any(norm(m) == tg for m in NEARBY_MUNICIPALITIES):
                spec["municipalities"].add(tg); hit = True
            else:
                partial = [n for n in all_names if tg in n]
                if partial:
                    spec["names"].update(partial); hit = True
        if not hit:
            spec["unmatched"].append(tok.strip())
    return spec


def area_match(spec, loc, postcode=None, municipality=None, text="", has_coords=False):
    """True / False / None (unknown location). loc = locate() result."""
    outside_city = has_coords and not (loc or {}).get("stadsdeel")
    if spec.get("any"):
        if municipality and norm(municipality) not in ("amsterdam",) and not (loc or {}).get("stadsdeel"):
            return norm(municipality) in {norm(m) for m in NEARBY_MUNICIPALITIES}
        return True
    if postcode and spec["postcode_prefixes"]:
        pc = postcode.replace(" ", "")
        if any(pc.startswith(p) for p in spec["postcode_prefixes"]):
            return True
    if municipality and norm(municipality) in spec["municipalities"]:
        return True
    if outside_city:
        return False
    names = {norm(v) for v in (loc or {}).values() if v}
    if names:
        return bool(names & spec["names"])
    # no coordinates: fall back to text mention of the area
    nt = norm(text)
    if nt and any(n in nt for n in spec["names"] | spec["municipalities"]):
        return True
    return None


if __name__ == "__main__":
    import sys
    print(resolve_area(" ".join(sys.argv[1:]) or "De Pijp, Oost"))
    print(locate(52.3546, 4.8952))  # De Pijp-ish
    print(geocode("1097DN"))
    save_cache()
