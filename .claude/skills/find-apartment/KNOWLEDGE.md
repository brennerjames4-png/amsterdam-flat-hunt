# find-apartment: KNOWLEDGE

## What it is
The Amsterdam direct-rental search. Given a budget and an area, it finds homes let by private landlords, owners and property managers (no agents). It splits them into new leases and sublets and publishes one artifact, "Amsterdam Flat Hunt".

## How it works
1. `tools/search.py`: scripted sources (Kamernet, HousingAnywhere, DirectWonen, Marktplaats). Writes `runs/<stamp>/raw_scripted.json`.
2. The browser collects Pararius, Vesteda, MVGM, DĀK, Codomo and others into `raw_browser.json`.
3. `tools/merge.py`: locates each listing against the official Amsterdam boundaries and PDOK, filters, classifies (`tools/classify.py` plus `knowledge/advertisers.json`), dedupes and ranks.
4. Manual verdicts go in `verdicts.json`; new advertiser names go in `knowledge/advertisers.json`.
5. `tools/build_report.py` writes `report/amsterdam-apartments.html`, which is published as the single artifact.

## What already exists
- Knowledge: `knowledge/market-and-law.md`, `knowledge/sources.md`, `knowledge/advertisers.json`.
- Subagent: `.claude/agents/amsterdam-rental-verifier.md`.
- Boundary data: `data/stadsdelen|gebieden|wijken.geojson`, plus `data/geocode_cache.json`.

## Rules that must hold
- Never include agents. Classify by entity, not by the site's section.
- Never show a housing-association sublet.
- Exactly one findings artifact, always at the same path / URL.
- No sign-ups, payments or messages on the user's behalf.
- Every source failure is reported, in the page and in the reply.

## Change log
- 2026-11-23: Created. Scrapers probed and verified that day:
  - Kamernet: maxRent index scale; ownerTypes 1/2/4.
  - HousingAnywhere: escaped JSON state.
  - DirectWonen: cards.
  - Marktplaats: lrp API; m/a ids; showWebsiteUrl.
- 2026-11-23: Made shareable. Added a 'works on any setup' section (browser fallback, local HTML fallback, first-run artifact), a one-question input step, README and public GitHub repo.
