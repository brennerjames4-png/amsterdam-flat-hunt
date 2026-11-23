"""Kamernet (kamernet.nl): rooms, studios, apartments; strong on private landlords and sublets.

Facts established by probing the site (Nov 2026):
- Search pages are Next.js; listings sit in __NEXT_DATA__ props.pageProps.targetPageProps.findListingsResponse.
- URL: /en/for-rent/properties-amsterdam?maxRent=<hundreds>&radius=<km>&pageNo=<n>&ownerTypes=<1|2>
  maxRent is an INDEX: 1..15 = x * EUR 100; above that EUR 250 steps (16=1750, 17=2000, 18=2250 ... 25=4000).
  17 listings per page.
  ownerTypes / landlordTypeId: 1 = private owner, 2 = roommate (room in their home), 4 = real estate agent.
  We query 1 and 2 only; agents (4) are never fetched.
- listingType: 1 room, 2 apartment, 4 studio, 8 anti-squat (anti-kraak, always via an agency; skipped).
- Detail page: /en/for-rent/<type>-<city>/<street-slug>/<type>-<id>, with listingDetails holding
  landlordTypeId, landlordDisplayName, postalCode(+Lat/Long), agencyFee, externalUrl, deposit,
  availabilityEndDate, isRegistrationAllowed, English/Dutch description.
- Messaging a landlord needs a paid Kamernet tenant subscription unless the ad is "react for free".
"""
import math
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import clip, day, http_get, log, new_listing, next_data  # noqa: E402

BASE = "https://kamernet.nl"
TYPES = {1: "room", 2: "apartment", 4: "studio", 8: "anti-squat"}
FURN = {1: None, 2: "shell", 3: "upholstered", 4: "furnished"}


def _search_page(city_slug, max_rent_hundreds, radius, page, owner_type):
    url = f"{BASE}/en/for-rent/properties-{city_slug}?maxRent={max_rent_hundreds}&radius={radius}&pageNo={page}&ownerTypes={owner_type}&sort=1"
    d = next_data(http_get(url))
    r = d["props"]["pageProps"]["targetPageProps"]["findListingsResponse"] if d else None
    return r or {"total": 0, "listings": []}


def _detail(listing):
    t = TYPES.get(listing["listingType"], "property")
    url = f"{BASE}/en/for-rent/{t}-{listing['citySlug']}/{listing['streetSlug']}/{t}-{listing['listingId']}"
    d = next_data(http_get(url))
    det = d["props"]["pageProps"].get("targetPageProps", {}).get("listingDetails") if d else None
    return url, det or {}


def max_rent_index(budget):
    if budget <= 1500:
        return max(1, math.ceil(budget / 100))
    return min(25, 15 + math.ceil((budget - 1500) / 250))


def search(budget, types=("apartment", "studio"), radius=5, city_slug="amsterdam", max_pages=25, delay=0.6, details=True):
    hundreds = max_rent_index(budget)
    out, seen = [], set()
    for owner_type in (1, 2):
        page, total = 1, None
        while page <= max_pages:
            r = _search_page(city_slug, hundreds, radius, page, owner_type)
            total = r.get("total", 0) if total is None else total
            batch = (r.get("listings") or []) + ([] if page > 1 else [])
            if not batch:
                break
            for L in batch:
                if L["listingId"] in seen:
                    continue
                seen.add(L["listingId"])
                ptype = TYPES.get(L["listingType"], "unknown")
                if ptype == "anti-squat" or ptype not in types:
                    continue
                if L.get("totalRentalPrice") and L["totalRentalPrice"] > budget:
                    continue
                out.append((owner_type, L))
            if page * 17 >= total:
                break
            page += 1
            time.sleep(delay)
        log(f"kamernet ownerTypes={owner_type}: {total} on site under index {hundreds} (budget EUR {budget})")

    records = []
    for i, (owner_type, L) in enumerate(out):
        ptype = TYPES.get(L["listingType"], "unknown")
        url, det = (None, {})
        if details:
            try:
                url, det = _detail(L)
            except Exception as e:  # noqa: BLE001
                log("kamernet detail failed", L["listingId"], e)
            time.sleep(delay)
        if not url:
            url = f"{BASE}/en/for-rent/{ptype}-{L['citySlug']}/{L['streetSlug']}/{ptype}-{L['listingId']}"
        desc = det.get("englishDescription") or det.get("dutchDescription")
        records.append(new_listing(
            source="kamernet",
            source_id=str(L["listingId"]),
            url=url,
            title=det.get("englishTitle") or det.get("dutchTitle") or f"{ptype.title()} {L.get('street')}",
            property_type=ptype,
            price_eur=L.get("totalRentalPrice"),
            price_includes="all-in" if L.get("utilitiesIncluded") else "excl. utilities",
            deposit_eur=det.get("deposit"),
            agency_fee_eur=det.get("agencyFee"),
            size_m2=L.get("surfaceArea"),
            bedrooms=det.get("numOfBedrooms"),
            furnished=FURN.get(L.get("furnishingId")),
            street=det.get("computedStreetName") or L.get("street"),
            postcode=det.get("postalCode"),
            city=L.get("city"),
            lat=det.get("postalCodeLat"),
            lng=det.get("postalCodeLong"),
            available_from=day(L.get("availabilityStartDate")),
            available_to=day(L.get("availabilityEndDate")),
            registration_possible=det.get("isRegistrationAllowed"),
            advertiser_name=det.get("landlordDisplayName"),
            advertiser_kind_raw=f"kamernet ownerTypes={owner_type}; landlordTypeId={det.get('landlordTypeId')}"
                                + (f"; externalUrl={det['externalUrl']}" if det.get("externalUrl") else ""),
            advertiser_verified=bool(det.get("isLandlordOBPIDVerified") or det.get("isLandlordOBPBankVerified")) if det else None,
            description=clip(desc),
            image=L.get("resizedFullPreviewImageUrl") or L.get("thumbnailUrl"),
            posted=day(det.get("publishDate") or det.get("createDate")),
        ))
        if (i + 1) % 20 == 0:
            log(f"kamernet details {i+1}/{len(out)}")
    return records


if __name__ == "__main__":
    import json
    print(json.dumps(search(int(sys.argv[1]) if len(sys.argv) > 1 else 1500, max_pages=1)[:3], indent=1))
