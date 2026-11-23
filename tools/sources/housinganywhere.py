"""HousingAnywhere (housinganywhere.com): furnished mid-term rentals (1–12+ months). Good for sublets.

Facts established by probing (Nov 2026):
- Search: /s/Amsterdam--Netherlands?priceMax=<cents>&page=<n>  (priceMax in CENTS; ~23 per page).
- Listings are embedded as escaped JSON inside window.__PRELOADED_STATE__; each object has
  landlordType ('private-landlord' | 'rental-company'), propertyType (APARTMENT, STUDIO, PRIVATE_ROOM,
  SHARED_ROOM, HOUSE), priceEUR, _geoloc{lat,lng}, minimalRentalPeriod / maximumStay (months),
  facility_registration_possible ('yes'/'no'), facility_total_size, listingPath, advertiserFirstName,
  bookableDateFromStart.
- Tenants pay HousingAnywhere a one-off service fee when booking (platform fee, not an agent fee) and
  pay the first month through the platform (held until 48h after move-in). Note it in the report.
- 'rental-company' covers both operators/managers and agencies; classification decides.
"""
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import day, http_get, log, new_listing  # noqa: E402

BASE = "https://housinganywhere.com"
PTYPE = {"APARTMENT": "apartment", "STUDIO": "studio", "PRIVATE_ROOM": "room", "SHARED_ROOM": "shared room", "HOUSE": "house"}


def _objects(html):
    u = html.replace('\\\\"', '"').replace('\\"', '"').replace("\\u002F", "/")
    dec = json.JSONDecoder()
    out = []
    for m in re.finditer(r'"landlordType":"', u):
        depth, i = 0, m.start()
        while i > 0:
            c = u[i]
            if c == "}":
                depth += 1
            elif c == "{":
                if depth == 0:
                    break
                depth -= 1
            i -= 1
        try:
            o, _ = dec.raw_decode(re.sub(r":undefined\b", ":null", u[i:i + 30000]))
            out.append(o)
        except Exception:  # noqa: BLE001
            pass
    return out


def search(budget, types=("apartment", "studio", "house"), city="Amsterdam--Netherlands", max_pages=15, delay=0.8):
    seen, records = set(), []
    for page in range(1, max_pages + 1):
        url = f"{BASE}/s/{city}?priceMax={int(budget * 100)}" + (f"&page={page}" if page > 1 else "")
        objs = _objects(http_get(url))
        new = [o for o in objs if o.get("id") not in seen]
        if not new:
            break
        for o in new:
            seen.add(o.get("id"))
            ptype = PTYPE.get(o.get("propertyType"), "unknown")
            if ptype not in types:
                continue
            price = o.get("priceEUR") or o.get("minPrice")
            if price and price > budget:
                continue
            geo = o.get("_geoloc") or {}
            reg = o.get("facility_registration_possible")
            records.append(new_listing(
                source="housinganywhere",
                source_id=str(o.get("id")),
                url=BASE + (o.get("listingPath") or o.get("unitTypePath") or ""),
                title=f"{ptype.title()} {o.get('street') or ''}".strip(),
                property_type=ptype,
                price_eur=price,
                price_includes={"I": "all-in", "E": "excl. utilities"}.get(o.get("utilities")),
                size_m2=int(float(o["facility_total_size"])) if str(o.get("facility_total_size", "")).replace(".", "").isdigit() else None,
                bedrooms=o.get("facility_bedroom_count"),
                furnished="furnished" if o.get("facility_bedroom_furnished") == "yes" else None,
                street=o.get("street"),
                city=o.get("city"),
                lat=geo.get("lat"),
                lng=geo.get("lng"),
                available_from=day(o.get("bookableDateFromStart")),
                min_stay_months=o.get("minimalRentalPeriod"),
                max_stay_months=o.get("maximumStay"),
                registration_possible=True if reg == "yes" else False if reg == "no" else None,
                advertiser_name=o.get("advertiserFirstName"),
                advertiser_kind_raw=f"housinganywhere landlordType={o.get('landlordType')}; isPartner={o.get('isPartner')}",
                advertiser_verified=bool(o.get("isExcellentAdvertiser")),
                image=o.get("previewImage"),
            ))
        time.sleep(delay)
    log(f"housinganywhere: {len(seen)} on site within EUR {budget}, kept {len(records)}")
    return records


if __name__ == "__main__":
    print(json.dumps(search(int(sys.argv[1]) if len(sys.argv) > 1 else 2000)[:2], indent=1))
