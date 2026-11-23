---
name: find-apartment
description: Search every Amsterdam rental source for homes offered DIRECTLY by a landlord or property manager (never a makelaar/agent), split into new leases and sublets, filtered by the user's monthly budget and area, and publish ONE artifact with all findings. Triggers on "/find-apartment <budget> <area>", "find my cousin an apartment", "search amsterdam rentals", "rerun the flat search", "update the apartment list".
---

> Knowledge: see KNOWLEDGE.md in this folder (read before changing this skill; update its change log after).

# Amsterdam direct-rental search

You are a rental scout for someone moving to Amsterdam. The user gives a **monthly budget** and an **area**. You find every home in that budget and area that is let **directly by a private landlord, an owner, or a landlord-side property manager**. You put them in two groups, **new leases** and **sublets/temporary**, and publish **one** artifact. That is always the same artifact: re-publishing updates it.

**Read these first. They are your training.**
- `knowledge/market-and-law.md`: price rules, lease law, sublet legality, BRP registration, scams, what "direct" means.
- `knowledge/sources.md`: every site, how to query it, how to tell an agent from a landlord there, and what is excluded.
- `knowledge/advertisers.json`: known landlords, managers and agents. You add to it.

## Works on any setup (check once, at the start)
The person running this may be new to Claude Code. Do all the technical work yourself and keep them out of it.
- **Python:** run `python3 --version`. If it is missing on a Mac, tell them to accept the "install command line developer tools" pop-up, then continue. The tools use the standard library only; never pip-install anything.
- **Browser for step 2.** Use whichever of these is available, in this order:
  1. The built-in browser (`mcp__Claude_Browser__*`, Claude desktop app)
  2. Claude in Chrome (`mcp__claude-in-chrome__*`)
  3. Neither: skip the browser sources, set them to `{"ok":false,"error":"no browser tool in this Claude Code setup"}` in `status_browser.json`, and say once in the reply that Pararius, Vesteda, MVGM and DĀK were not covered. The scripted sources still give a full report.
- **Publishing step 5.** If the Artifact tool is available, publish there. If not, run `open report/amsterdam-apartments.html` (macOS; `start` on Windows, `xdg-open` on Linux) and give the file path.
- **First run in someone's account:** there is no existing artifact yet. `Artifact action:list` finds nothing titled "Amsterdam Flat Hunt", so publish a new one with `icon: "home"`. Every later run updates that one.

## Inputs
If the person gave no budget or area, ask in **one** short message: monthly budget in euros, area(s) (or "anywhere"), and whether rooms in a shared flat are OK. Never ask more than that.

Parse from the args or the message:
- **budget**: euros a month. "1.5k" = 1500. If missing, ask once.
- **area**: free text. Commas separate several areas. Empty or "anywhere" = all of Amsterdam. Areas can be districts (Oost, Zuid, Noord…), neighbourhoods (De Pijp, Jordaan, IJburg…), postcodes (1017) or nearby towns (Amstelveen, Diemen, Zaandam, Haarlem).
- Optional:
  - **types**: default apartment, studio, house. Add `room` only if the user says rooms are fine.
  - **min size**
  - **move-in date**

Before searching, check the area with:
```bash
python3 -c "import sys;sys.path.insert(0,'tools');import geo;print(geo.resolve_area('<area>'))"
```
If anything comes back `unmatched`, tell the user which term was not recognised and how you will treat it.

## Steps

**1. Scripted sources** (Kamernet, HousingAnywhere, DirectWonen, Marktplaats). This takes about 2–4 minutes, so run it in the background:
```bash
python3 tools/search.py --budget <B> --area "<area>" [--types apartment,studio,house] [--min-size N]
```
It prints the run folder, `runs/<stamp>`.

**2. Browser sources, while step 1 runs.** Use the browser picked above and follow `knowledge/sources.md` §B. Cover at least:
- **Pararius:** every page up to the budget. Keep only allowlisted landlords and managers, plus project cards with no agent link.
- **Vesteda**
- **MVGM ikwilhuren.nu**
- **DĀK regio Amsterdam:** the Middenhuur and Vrije sector tabs
- **Codomo/Holland2Stay**
- **Pararius short-stay:** for sublets
- If time allows: Kamer.nl ("Particulier" only), and Funda (Homecrew, Huizenbalie and developer-landlords only).

Write every kept listing to `runs/<stamp>/raw_browser.json`. That file is a JSON array of records with exactly the fields in `tools/common.py: LISTING_FIELDS`. Rules for filling them:
- Set `source` (pararius, vesteda, mvgm, dak, codomo, kamer.nl, funda, heimstaden, corporatie).
- Set `advertiser_name` exactly as shown.
- Set `postcode` whenever the site shows one.
- Set `price_eur` as an integer.

Also write `runs/<stamp>/status_browser.json`, for example `{"pararius":{"ok":true,"count":N}}`. Record a failure honestly as `{"ok":false,"error":"..."}`.

Do **not** write agent listings into the file. If you are unsure whether an advertiser is an agent, include the listing; `merge.py` will mark it unverified.

**3. Merge:**
```bash
python3 tools/merge.py runs/<stamp>
```
This geocodes every listing, places it in the official district, neighbourhood and area boundaries, applies the budget, type and area filters, classifies the advertiser and the tenure, adds red flags, de-duplicates across sites and ranks the results.

**4. Verify what the rules could not decide.** Open `results.json`.
- For every kept listing with `advertiser_verdict: "unverified"`: look the advertiser up (WebSearch for their website or KvK listing, or open the listing). Decide landlord, manager, private or agent.
  - Add the name to `knowledge/advertisers.json` with a one-line note and the source. **This is how the agent learns.**
  - For a decision about a single listing, write it to `runs/<stamp>/verdicts.json` as `{"<source>:<source_id>": {"verdict":..., "tenure":..., "reject":..., "note":..., "red_flags":[...]}}`.
- For the top 10 listings in each group, open the listing page (browser or curl). Check for:
  - agency-fee wording, "makelaar", or "bemiddelingskosten"
  - scam wording
  - "no registration"
  - a housing-association sublet
  - dates that contradict the tenure
  Record anything you find in `verdicts.json`. Using the `amsterdam-rental-verifier` subagent in parallel batches is fine. It loads only in sessions started after it was created; in the session that created it, use a general-purpose agent told to follow `.claude/agents/amsterdam-rental-verifier.md`.
- Re-run `merge.py` after any change.

**5. Build the one report and publish:**
```bash
python3 tools/build_report.py runs/<stamp>
```
This writes `report/amsterdam-apartments.html`, always to the same path. Publish it with the Artifact tool, using `file_path` = that path.
- If this conversation already published it, re-publish the same path.
- In a new conversation, first find the existing artifact with `Artifact action:list` (title "Amsterdam Flat Hunt"), `read` it, then publish to its `url`. Never create a second artifact for findings.
- The first ever publish takes `icon: "home"`.

**6. Reply** in a few lines:
- the counts per group
- the 3 best leases and 3 best sublets (price, area, why they're good)
- any source that failed
- what the user should do first (for example: pre-register on DĀK and Vesteda; Kamernet needs Premium to message)

## Hard rules
- **Never include agents.** Not even if they are cheap or the only option. The test is who the entity is, not which section of the site lists it.
- **Never present a housing-association sublet** (illegal). Flag any whole home under about €935 from a private tenant.
- **Never pay, register, sign up or message landlords on the user's behalf.** Searching and reading is fine. Sign-ups and replies are for the user.
- **Never put the cousin's personal details into any site.**
- **One artifact only**, always the same one.
- **Report honestly:** if a source was blocked or returned nothing, say so in the page (status table) and in the reply.
- Listings change by the hour. Date the report, and never claim one is still available without opening it.
