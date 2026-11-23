# Amsterdam Flat Hunt

A Claude Code agent that searches Amsterdam's rental sites for homes let **directly by a landlord or property manager, never through a rental agent (makelaar)**. It splits the results into **new leases** and **sublets**, filters them by your budget and area, flags scams and illegal sublets, and builds one report page.

## Use it (nothing to install)

Open Claude Code (the desktop app is best, because it has a built-in browser for the sites that block scripts) and paste this:

```
Clone https://github.com/brennerjames4-png/amsterdam-flat-hunt into a folder called amsterdam-flat-hunt in my home directory, go into it, read .claude/skills/find-apartment/SKILL.md and do exactly what it says. Ask me only for my monthly budget and the area I want, then handle everything else yourself.
```

That's it. Claude asks for your budget and area, searches everything, and gives you a link to the results page.

To search again later, open Claude Code in that folder and type `/find-apartment 1600 Oost, De Pijp`, with your own numbers and areas.

## What it searches
- **Automatically:** Kamernet, HousingAnywhere, DirectWonen, Marktplaats
- **Through the browser:** Pararius (landlords and managers only), Vesteda, MVGM ikwilhuren.nu, DĀK regio Amsterdam (mid-rent and free sector), Holland2Stay/Codomo

Agents, aggregators (Rentola, Huurportaal) and anti-squat listings are left out on purpose.

## How it decides
- **Advertiser:** private landlord, direct landlord or property manager. Known names are in `knowledge/advertisers.json`, which grows with every search.
- **Lease or sublet:** decided from the end date, maximum stay and the wording of the ad.
- **Area:** each listing is placed using the city's official district and neighbourhood boundaries.
- **Red flags:** no address registration (you can't get a BSN), illegal fees, a deposit over 2 months, scam wording, prices far below the market, sublets of housing-association homes.

The rules and research behind it are in `knowledge/market-and-law.md` and `knowledge/sources.md`.

## Never done automatically
It never signs up, pays, messages a landlord, or enters your personal details on any site. Replying to listings is up to you.
