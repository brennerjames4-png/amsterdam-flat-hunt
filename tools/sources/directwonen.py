"""DirectWonen (directwonen.nl): platform aimed at private landlords ("Plaats gratis je woning").

Facts established by probing (Nov 2026):
- Search: /huurwoningen-huren/amsterdam?pageno=<n>  (plain HTML, no bot wall). No working max-price URL param.
- Card: <a class="inner-content" href=".../<street>/<type>-<id>"> with .advert-location-header (type),
  .advert-location-price (EUR), h3.location-text ("Street, City"), .kale-huur ("(Excl.)"/"(Incl.)"),
  .small-banner.rooms / .surface. "Beschikbaar per" date in the hidden details block.
- The advertiser's identity and contact are behind a paid tenant premium account. Treat as private but tell
  the user to confirm it is not an agent before paying for access.
"""
import html as htmllib
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import http_get, log, new_listing  # noqa: E402

BASE = "https://directwonen.nl"
TYPE = {"appartement": "apartment", "studio": "studio", "woning": "house", "huis": "house", "kamer": "room"}


def _txt(s):
    return re.sub(r"\s+", " ", htmllib.unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()


def search(budget, types=("apartment", "studio", "house"), city="amsterdam", pages=8, delay=0.8):
    records, seen = [], set()
    for p in range(1, pages + 1):
        h = http_get(f"{BASE}/huurwoningen-huren/{city}" + (f"?pageno={p}" if p > 1 else ""))
        blocks = re.split(r'(?=<a href="https://directwonen\.nl/huurwoningen-huren/[^"]+" class="inner-content")', h)[1:]
        new = 0
        for b in blocks:
            m = re.match(r'<a href="(https://directwonen\.nl/huurwoningen-huren/([a-z-]+)/([^"/]+)/([a-z]+)-(\d+))"', b)
            if not m or m.group(5) in seen:
                continue
            seen.add(m.group(5)); new += 1
            url, city_slug, street_slug, tslug, lid = m.groups()
            ptype = TYPE.get(tslug, "unknown")
            price = re.search(r'advert-location-price">\s*&euro;\s*([\d.]+)', b)
            price = int(price.group(1).replace(".", "")) if price else None
            loc = re.search(r'class="location-text"[^>]*>(.*?)</h3>', b, re.S)
            loc = _txt(loc.group(1)) if loc else ""
            street, _, cty = loc.partition(",")
            incl = re.search(r'class="kale-huur"[^>]*>(.*?)</div>', b, re.S)
            incl = _txt(incl.group(1)) if incl else ""
            size = re.search(r'surface">\s*<p class="small-banner-top">(\d+)', b)
            rooms = re.search(r'rooms">\s*<p class="small-banner-top">(\d+)', b)
            avail = re.search(r"Beschikbaar per\s*:?\s*(?:</[^>]+>\s*)*(\d{2})-(\d{2})-(\d{4})", b)
            img = re.search(r'<img alt="[^"]*" src="([^"]+)"', b)
            if ptype not in types or not price or price > budget:
                continue
            records.append(new_listing(
                source="directwonen", source_id=lid, url=url,
                title=f"{ptype.title()} {street.strip()}", property_type=ptype, price_eur=price,
                price_includes="excl. utilities" if "excl" in incl.lower() else ("all-in" if "incl" in incl.lower() else None),
                size_m2=int(size.group(1)) if size else None,
                bedrooms=max(0, int(rooms.group(1)) - 1) if rooms else None,
                street=street.strip() or None, city=(cty.strip() or city.title()),
                available_from=f"{avail.group(3)}-{avail.group(2)}-{avail.group(1)}" if avail else None,
                advertiser_name=None,
                advertiser_kind_raw="particulier",
                description="DirectWonen listing (advertiser identity hidden behind paid tenant account)",
                image=img.group(1) if img else None,
            ))
        if not new:
            break
        time.sleep(delay)
    log(f"directwonen: {len(seen)} cards scanned, kept {len(records)}")
    return records


if __name__ == "__main__":
    import json
    print(json.dumps(search(int(sys.argv[1]) if len(sys.argv) > 1 else 1800, pages=2)[:3], indent=1))
