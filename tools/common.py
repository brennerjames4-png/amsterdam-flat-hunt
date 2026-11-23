"""Shared helpers: HTTP, the normalized listing record, small parsers."""
import json
import re
import time
import urllib.request

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"

# Every source (scripted or browser-collected) produces records with exactly these keys.
LISTING_FIELDS = {
    "source": None,            # "kamernet", "housinganywhere", "pararius", ...
    "source_id": None,         # id on that site
    "url": None,               # public listing URL
    "title": None,
    "property_type": None,     # apartment | studio | room | house | unknown
    "price_eur": None,         # monthly rent as advertised (int)
    "price_includes": None,    # "all-in" | "excl. utilities" | "service costs extra" | None
    "deposit_eur": None,
    "agency_fee_eur": None,    # any fee charged to the tenant (should be none for direct)
    "size_m2": None,
    "bedrooms": None,
    "furnished": None,         # furnished | upholstered | shell | None
    "street": None,
    "postcode": None,
    "city": None,
    "lat": None,
    "lng": None,
    "available_from": None,    # YYYY-MM-DD
    "available_to": None,      # YYYY-MM-DD, set => fixed end (sublet / temporary)
    "min_stay_months": None,
    "max_stay_months": None,
    "registration_possible": None,  # can the tenant register (BRP) at the address? True/False/None
    "advertiser_name": None,
    "advertiser_kind_raw": None,    # what the site itself says (e.g. landlordTypeId=1, "private-landlord")
    "advertiser_verified": None,
    "description": None,       # first ~1500 chars, used for classification
    "image": None,
    "posted": None,            # YYYY-MM-DD
}


def new_listing(**kw):
    rec = dict(LISTING_FIELDS)
    unknown = set(kw) - set(rec)
    if unknown:
        raise KeyError(f"unknown listing fields: {unknown}")
    rec.update(kw)
    return rec


def http_get(url, headers=None, timeout=25, retries=2):
    h = {"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9,nl;q=0.8"}
    h.update(headers or {})
    last = None
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers=h)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"GET failed {url}: {last}")


def next_data(html):
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.S)
    return json.loads(m.group(1)) if m else None


def day(s):
    """'2027-03-08T00:00:00' / '2027-03-08T00:00:00.000Z' -> '2027-03-08'."""
    if not s:
        return None
    m = re.match(r"(\d{4}-\d{2}-\d{2})", str(s))
    return m.group(1) if m else None


def clip(s, n=1500):
    if not s:
        return None
    s = re.sub(r"\s+", " ", str(s)).strip()
    return s[:n]


def log(*a):
    import sys
    print(*a, file=sys.stderr, flush=True)
