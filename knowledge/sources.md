# Source playbook: where Amsterdam rentals live, and how to read each site (verified 23 Nov 2026)

**Rule for every source:** keep a listing only if it is offered by a private landlord (an owner, or a tenant subletting) or by a landlord-side property manager or institutional owner. Drop makelaars, rental agencies, relocation firms and aggregators. When the site files every advertiser as an "agent" (Pararius), classify by the entity itself using `knowledge/advertisers.json`.

## A. Scripted sources (`tools/search.py` runs these)

| Source | Script | Good for | Advertiser signal | Cost to tenant |
|---|---|---|---|---|
| **Kamernet** | `tools/sources/kamernet.py` | Sublets (end dates), private flats, rooms | `landlordTypeId`/`ownerTypes`: 1 private owner, 2 roommate, 4 agent (agents never fetched). `agencyFee`, `externalUrl` | Premium needed to message (~€38/4 weeks) unless "React for free" |
| **HousingAnywhere** | `tools/sources/housinganywhere.py` | Furnished mid-term sublets (1–24 months) | `landlordType`: private-landlord / rental-company | NL: first month via platform; check the current service fee |
| **DirectWonen** | `tools/sources/directwonen.py` | Private landlords, mostly long-term | Platform for private landlords; identity hidden until paid | Paid premium to respond |
| **Marktplaats** | `tools/sources/marktplaats.py` | Private rooms, odd private flats | `m…` id = consumer, `a…` = Admarkt business feed; `showWebsiteUrl:true` = business. Both business types are dropped. | Free. **High scam risk** |

Probed URL formats:
- Kamernet: `https://kamernet.nl/en/for-rent/properties-amsterdam?maxRent=<idx>&radius=<km>&pageNo=<n>&ownerTypes=<1|2>`
  - The `idx` value: 1–15 means idx × €100; from 16 upward each step adds €250 (16 = €1,750 … 25 = €4,000).
  - Category paths: `room-`, `studio-`, `apartment-`, `short-term-rentals-amsterdam`, `long-term-rentals-amsterdam`.
- HousingAnywhere: `https://housinganywhere.com/s/Amsterdam--Netherlands?priceMax=<cents>&page=<n>`
- DirectWonen: `https://directwonen.nl/huurwoningen-huren/amsterdam?pageno=<n>`
- Marktplaats API: `https://www.marktplaats.nl/lrp/api/search?l1CategoryId=1032&postcode=1012AB&distanceMeters=10000&limit=100&offset=0&attributeRanges[]=PriceCents:0:<cents>`
  - Filter on `categoryId` in the results: 2143 huizen-te-huur, 2771 kamers-te-huur, 2147 expat.

## B. Browser sources (the session reads these with the built-in browser, `mcp__Claude_Browser__*`)

The browser gets past the Cloudflare checks that block scripts on Pararius, Huurwoningen, Kamer.nl, Huurstunt and Funda. Save each kept listing into `runs/<stamp>/raw_browser.json`, using the same fields as `tools/common.py: LISTING_FIELDS`. Set `advertiser_name` to exactly what the card shows, and set `advertiser_kind_raw` to the site's own label.

### B1. Pararius (biggest supply; every advertiser is a professional account)
- **URL:** `https://www.pararius.com/apartments/amsterdam/0-<budget>`. Pages: append `/page-2`, `/page-3`…
- **Narrowing:**
  - Districts: `/apartments/amsterdam/city-area-<centrum|nieuw-west|noord|oost|zuidoost>/0-<budget>`
  - Types: `/apartments/amsterdam/<apartment|studio|house>/0-<budget>`
  - Short stays: `https://www.pararius.com/short-stay/amsterdam`
- **Extractor** (run with `javascript_tool` after the page loads, about 3 seconds):
```js
await new Promise(r=>setTimeout(r,3000));
[...document.querySelectorAll('section.listing-search-item')].map(e=>{
 const q=s=>e.querySelector(s); const t=q('a.listing-search-item__link--title');
 const adv=q('a[href*="/real-estate-agents/"]');
 const sub=(q('.listing-search-item__sub-title')||{}).innerText||'';
 return {title:t&&t.innerText.trim(), url:t&&('https://www.pararius.com'+t.getAttribute('href')),
  price:(q('.listing-search-item__price')||{}).innerText, sub, // "1101 BK Amsterdam (Amstel III/Bullewijk)"
  features:(q('.listing-search-item__features, .illustrated-features')||{}).innerText,
  advertiser:adv?adv.innerText.trim():((q('.listing-search-item__info')||{}).innerText||'').trim(),
  advertiser_href:adv&&adv.getAttribute('href'), img:(q('img')||{}).src}})
```
- **Keep only these advertisers:** names in `advertisers.json` with verdict landlord or manager (Heimstaden, Vesteda, Ik wil huren van MVGM, Van der Linden Vastgoedmanagement, Uppmärk/OurDomain projects, corporaties…). Also keep **project cards that have no agent link** (new-build projects), classifying them by the project name.
- **Every other advertiser is an agent: drop it.** An unknown name with no agent words goes to the verification step (see the skill).
- Read the postcode from the subtitle and put it in `postcode`. The neighbourhood in brackets is for display only; `merge.py` locates the listing properly.
- **Learned in the 23 Nov 2026 dry run:**
  - Pararius keeps serving page 1–2 content for page numbers past the real total, so de-duplicate by URL. The header count (`.search-list-header__title`) gives the true total; that day it was 42 under €1,800.
  - Run `fetch('/apartments/...page-N')` from a pararius.com tab: same-origin requests pass the bot check.
  - Project cards show a price range ("€1,333 – €1,675"). Take the lowest figure and set `price_includes: "from, excl. utilities"`.
  - Images are lazy placeholders (`data:`). The artifact can't show third-party photos anyway, so leave `image` null.

### B2. Vesteda (institutional landlord, direct)
- **URL:** `https://www.vesteda.com/en/unit-search?placeType=1&sortType=1&radius=5&s=Amsterdam&sc=woning&latitude=52.37&longitude=4.89&filters=0&priceFrom=500&priceTo=<budget>`
- Use `get_page_text`; each unit shows its address, rent and m².
- `advertiser_name: "Vesteda"`, `advertiser_kind_raw: "owner portal"`. Tenure: lease.
- To apply you need a free Vesteda account.

### B3. MVGM: ikwilhuren.nu (property manager for many funds, including Bouwinvest)
- **URL:** `https://ikwilhuren.nu/aanbod/`. The search form is a POST (`selAdres`, `selPrijsTot`), so fill it in the browser: type "Amsterdam", set the max price, submit, then `get_page_text`.
- `advertiser_name: "MVGM (ikwilhuren.nu)"`. Tenure: lease.

### B4. DĀK regio Amsterdam (formerly WoningNet; housing associations only)
- **URL:** `https://amsterdam.mijndak.nl/Woningaanbod`. Tabs: Aanbod (social, needs years of registration, so skip), **Middenhuur**, **Vrije sector**, Loting (lottery).
- Read the Middenhuur and Vrije sector tabs.
- `advertiser_name` = the corporatie (Ymere, Eigen Haard, Stadgenoot, Rochdale, de Alliantie, Lieven de Key). Tenure: lease.
- Note for the user: free registration; mid-rent units have income rules, and Amsterdam requires a housing permit for mid-rent.

### B5. Codomo / Holland2Stay (operator; furnished studios and apartments)
- **URL:** `https://codomo.eu/homes/nl/en?from=holland2stay`. Pick Amsterdam and read the available units.
- `advertiser_name: "Holland2Stay / Codomo"`. Usually a lease. Short-stay units count as sublet/temporary.

### B6. Heimstaden
- **URL:** `https://heimstaden.com/nl/` (Woning zoeken). Also on Pararius as the advertiser "Heimstaden".

### B7. Kamer.nl (aggregator-like; low priority)
- **URL:** `https://www.kamer.nl/huren/appartement-amsterdam/` (also `studio-`, `kamer-`).
- Each listing has a field **"Aanbieder"**. **Drop "Makelaar / Bedrijfsmatige verhuurder"**; keep "Particulier".
- Many listings are scraped from other sites ("Gevonden op…"), so prefer the original source. Prices are sometimes misparsed.

### B8. Funda huur (almost all makelaars; low yield)
- **URL:** `https://www.funda.nl/zoeken/huur?selected_area=["amsterdam"]&price="0-<budget>"&object_type=["apartment"]`
- Keep only listings whose office is **Homecrew** or **Huizenbalie** (DIY services, so the owner is a private landlord), plus developer-landlords (Uppmärk, NMG Wonen, Amvest, Yvastgoed).

### B9. Corporatie mid-rent and free-sector pages (direct)
- Rochdale: rochdale.nl → Woning zoeken → Vrije sector huur
- Stadgenoot: stadgenoot.nl
- Eigen Haard: eigenhaard.nl
- de Alliantie: de-alliantie.nl/ik-zoek (apply with a Qii huurpaspoort)
- Lieven de Key: lievendekey.nl
- Ymere: search via ymere.nl
- Project sites such as hureninmix.nl

### B10. Social and manual-only (list as links in the report; cannot be searched automatically)
- **Facebook groups**, joined by the user:
  - Rooms for Amsterdam
  - Amsterdam Housing
  - Amsterdam Rooms and Apartments
  - Rooms for rent in Amsterdam
  - Apartments for Rent Amsterdam The Netherlands
  - Amsterdam Apartments 4 Rent
  - Expats in Amsterdam
  - Amsterdam Apartments and Housing (NO SPAM)
  - These are mostly private sublets. **High scam risk.**
- **Reddit:** r/Amsterdam housing megathread, r/NetherlandsHousing.

## C. Excluded on purpose (never show)
- **Rentola, Huurportaal:** scraped listings plus subscription traps.
- **Uniplaces, Spotahome:** almost no Amsterdam supply, and booking fees.
- **ExpatRentals, Interhouse,** and any makelaar or relocation agency.
- **Huurstunt:** paywall, mostly reposts; the Consumentenbond criticised it.
- **Huurwoningen.nl:** a Pararius mirror that hides the advertiser. Use only to cross-check.
- **Alert aggregators** (Uprent, Rentbird, RentSlam, Findify): copies of the sites above. Mention them as optional alert tools only.
- **Anti-kraak** (anti-squat) listings: always via agencies, with no tenant protection.
- **Bouwinvest homes let through vb&t Verhuurmakelaars:** vb&t is a makelaar, so these are excluded. Bouwinvest homes let by **MVGM** are fine.
