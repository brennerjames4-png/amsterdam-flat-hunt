# Amsterdam direct-rental agent

This folder is an agent that finds Amsterdam homes let **directly by landlords or property managers, never through agents (makelaars)**. It covers **new leases** and **sublets**, filtered by a monthly budget and an area. The output is **one** artifact page.

## Run it
`/find-apartment <budget> <area>`, for example `/find-apartment 1600 Oost, De Pijp`. Full playbook: `.claude/skills/find-apartment/SKILL.md`.

## Layout
- `knowledge/`: what the agent knows.
  - `market-and-law.md`: rules and law.
  - `sources.md`: site playbook.
  - `advertisers.json`: landlord, manager and agent registry. It grows with every run, so keep adding verified names.
- `tools/`: Python, standard library only (macOS python3).
  - `search.py`: scripted sources, writes to `runs/<stamp>/`.
  - `sources/*.py`: one scraper per site.
  - `merge.py`: locate, filter, classify, dedupe, rank.
  - `classify.py`: judgement rules.
  - `geo.py`: official Amsterdam boundaries (`data/*.geojson`) and PDOK geocoding.
  - `build_report.py`: writes `report/amsterdam-apartments.html`, the single artifact, always at that path.
- `.claude/agents/amsterdam-rental-verifier.md`: subagent that vets unknown advertisers and top listings.
- `runs/`: one folder per search. Holds raw data, verdicts and results.

## Conventions
- Pararius, Funda, Kamer.nl and Huurwoningen block scripts (Cloudflare), so read them with the built-in browser.
- Kamernet, HousingAnywhere, DirectWonen and Marktplaats are scripted.
- When a site changes its markup and a scraper breaks, fix the scraper, update the "Facts established by probing" docstring at the top of that file, and note the date.
- Never sign up, pay or message on the user's behalf, and never enter the cousin's personal data on any site.
