"""Marktplaats (marktplaats.nl), huizen-en-kamers. Low-trust source: many holiday lets and scams.

Facts established by probing (Nov 2026):
- JSON API: /lrp/api/search?l1CategoryId=1032&postcode=1012AB&distanceMeters=<m>&limit=100&offset=<n>
  &attributeRanges[]=PriceCents:0:<cents>   (the l2CategoryId filter is ignored server-side, so filter
  client-side on categoryId: 2143 huizen-te-huur, 2771 kamers-te-huur, 2147 expat-rentals).
- itemId starting with 'a' = Admarkt paid commercial feed (bulk advertisers / agencies / aggregators such
  as "Domiva"); 'm' = ad placed by a consumer account. We keep only 'm' ads.
- Many 'm' ads quote a NIGHTLY price (EUR 100–300) for holiday lets: anything under EUR 400 for a whole
  home is dropped as a holiday let / bait.
"""
import json
import os
import sys
import time
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import clip, http_get, log, new_listing  # noqa: E402

BASE = "https://www.marktplaats.nl"
RENT_CATS = {2143: "huizen-te-huur", 2771: "kamers-te-huur", 2147: "expat-rentals"}


def search(budget, types=("apartment", "studio", "house"), postcode="1012AB", distance_m=10000, pages=4, delay=0.8):
    records, seen = [], set()
    for p in range(pages):
        q = {"l1CategoryId": 1032, "postcode": postcode, "distanceMeters": distance_m, "limit": 100,
             "offset": p * 100, "sortBy": "SORT_INDEX", "sortOrder": "DECREASING"}
        url = f"{BASE}/lrp/api/search?" + urllib.parse.urlencode(q) + f"&attributeRanges[]=PriceCents%3A0%3A{int(budget*100)}"
        d = json.loads(http_get(url))
        L = d.get("listings", [])
        if not L:
            break
        for x in L:
            iid = x.get("itemId", "")
            seller0 = x.get("sellerInformation") or {}
            if iid in seen or not iid.startswith("m") or x.get("categoryId") not in RENT_CATS or seller0.get("showWebsiteUrl"):
                continue
            seen.add(iid)
            price = (x.get("priceInfo") or {}).get("priceCents")
            price = round(price / 100) if price else None
            title = x.get("title") or ""
            desc = x.get("description") or x.get("categorySpecificDescription") or ""
            t = (title + " " + desc).lower()
            if any(w in t for w in ("parkeer", "garage", "berging", "postbus", "opslag", "te koop")):
                continue
            ptype = "room" if x.get("categoryId") == 2771 or "kamer" in t or "room" in t else (
                "studio" if "studio" in t else "apartment")
            if ptype not in types:
                continue
            if not price or price < 400 or price > budget:
                continue
            loc = x.get("location") or {}
            attrs = {a.get("key"): a.get("value") for a in x.get("attributes", []) if isinstance(a, dict)}
            seller = x.get("sellerInformation") or {}
            records.append(new_listing(
                source="marktplaats",
                source_id=iid,
                url=BASE + x.get("vipUrl", ""),
                title=title,
                property_type=ptype,
                price_eur=price,
                size_m2=int(attrs["surface"]) if str(attrs.get("surface", "")).isdigit() else None,
                city=loc.get("cityName"),
                lat=loc.get("latitude"),
                lng=loc.get("longitude"),
                advertiser_name=seller.get("sellerName"),
                advertiser_kind_raw="marktplaats consumer ad (m-id)",
                advertiser_verified=seller.get("isVerified"),
                description=clip(desc, 800),
                image=((x.get("pictures") or [{}])[0] or {}).get("mediumUrl"),
                posted=x.get("date"),
            ))
        time.sleep(delay)
    log(f"marktplaats: kept {len(records)} consumer rental ads")
    return records


if __name__ == "__main__":
    print(json.dumps(search(int(sys.argv[1]) if len(sys.argv) > 1 else 1500)[:3], indent=1))
