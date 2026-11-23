# Amsterdam rental market and law (researched 23 Nov 2026)

What the agent must know to judge any listing. Items marked [UNVERIFIED] could not be confirmed against a primary 2026 source.

## 1. Sectors and price rules

| Sector | WWS points | Max base rent (kale huur) 2026 | 2027 |
|---|---|---|---|
| Social (sociale huur) | ≤143 | €932.93 | €959.71 |
| Regulated mid-rent (middenhuur) | 144–186 | €932.94 – €1,228.07 | up to €1,263.32 |
| Free sector (vrije sector) | ≥187 | no cap on starting rent | |

- Wet betaalbare huur (since 1 July 2024): the WWS points table is binding up to 186 points. A tenant paying above the points maximum can get the rent lowered via the Huurcommissie.
- Yearly increase caps for 2026: 6.1% mid-rent, 4.4% free sector.
- Amsterdam requires a huisvestingsvergunning (housing permit) for mid-rent homes since 1 July 2025, with income caps (at launch €81,633 single, €89,821 family; 2026 figures [UNVERIFIED]).
- Social housing goes through WoningNet Stadsregio Amsterdam (also covers Amstelveen, Diemen, Zaanstad). Average wait is about 10 years, so it is useless to a newcomer. **The agent targets mid-rent and free sector only.**
- Supply is shrinking. Investors are selling units as they become vacant: Heimstaden says about 90%, and Vesteda is selling thousands. Expect fewer than 1 in 10 listings to be cheap, and expect around 450 applicants for a mid-rent home.

**Flag, don't reject:** a listing asking more than €1,228 for a small flat (under about 50–60 m²) or one with a poor energy label may legally be mid-rent and over-priced. The tenant could claim the difference back later.

### Typical asking rents in 2026 (bands, not facts)
- About €28–29/m² citywide in the free sector.
- Studio: €1,250–1,650. 1-bed: €1,750–2,250. 2-bed: €2,350–3,100.
- Centrum and Zuid are the most expensive. Noord, Nieuw-West and Zuidoost are the cheapest (around €20/m² in parts).
- A room averages about €950 in Amsterdam [UNVERIFIED]. Many Kamernet rooms are priced above the legal maximum.
- **Sanity check:** a whole flat priced far below €20/m², or a whole 1-bed under about €900, is a scam signal unless it is plainly a regulated new-build mid-rent unit from an institutional landlord.

## 2. Leases

- **Indefinite leases are the default for all new leases** (Wet vaste huurcontracten, since 1 July 2024).
- A temporary lease (max 2 years) is allowed only for: students; people temporarily displaced by work or renovation on their own home; people leaving shelters; second-chance tenants; surviving relatives; divorcing parents; Wadden island workers; status holders.
- **Diplomatenclausule (tussenhuur):** an owner who is temporarily away may let their **own** home for a fixed period. The tenant must leave when the owner returns. This is common in furnished expat listings. Confirm that the person letting it is the owner, because a tenant cannot use this clause.
- **Room in the landlord's own home (hospita):** the tenant has reduced protection for the first 9 months.

### Wet goed verhuurderschap (since 1 July 2023), binds landlords and managers
- **Deposit:** at most 2 months' base rent. It must be returned within 14 days, or 30 days if costs are deducted.
- **No fees to the tenant:** no "bemiddelingskosten", "administratiekosten" or "contractkosten" when the agent or manager works for the landlord. Charging both sides is called "dubbel petje" and is illegal. Fees paid can be reclaimed for 5 years. **Any fee asked of the tenant = red flag.**
- The contract must be written, and the tenant must get written information on: the landlord's contact details, the deposit, service costs, and the municipal meldpunt (complaints point).
- No discrimination. The selection criteria must be published.

## 3. Subletting (onderhuur)

| Situation | Legal? | Agent treatment |
|---|---|---|
| Whole **social housing** unit sublet by the tenant | **Illegal.** Evictions are common, and the subtenant has no rights. | **Reject** |
| Whole private unit, with the landlord's **written** consent | Legal | Keep. Tell the user to ask for the consent letter. |
| Whole private unit, without consent | Breach of the head lease | Keep only with a warning |
| Room in a tenant's private rental | Usually needs consent | Keep with a warning |
| Room from a resident owner (hospita) | Legal | Keep |
| Owner away temporarily (diplomatenclausule) | Legal | Keep. Verify ownership via Kadaster. |

**Illegal-sublet signals** (flag; reject when several stack up):
- A housing association is named (Ymere, Eigen Haard, Stadgenoot, De Key, Rochdale, De Alliantie, Lieven de Key…)
- A whole flat at or below about €930 rent
- "No registration" (geen inschrijving)
- "Don't tell the neighbours", "cash only"
- No contract
- The Kadaster owner differs from the person letting, with no explanation

**Sharing rules (Huisvestingsverordening Amsterdam):** two unrelated adults may share without a permit. Three or more need an omzettingsvergunning (conversion permit). Rooms must have individual contracts, not one group contract.

**BRP registration (inschrijving):** the tenant registers at the address where they actually live. The landlord's consent is legally irrelevant, but a listing that refuses registration is usually an illegal sublet. **The cousin needs a BSN** for salary, banking and healthcare. So "registration not possible" is a major red flag, and "registration possible" is a big plus.

## 4. Areas

The agent locates every listing with the city's official boundaries (`data/*.geojson`, matched in `tools/geo.py`). The postcode table below is only a quick reference [ranges approximate]:

| District | Postcodes | Neighbourhoods used in listings |
|---|---|---|
| Centrum | 1011–1018 | Grachtengordel, Jordaan, De Wallen, Nieuwmarkt, Plantage |
| West | 1051–1057 (+parts 1013–1014) | Oud-West, De Baarsjes, Bos en Lommer, Westerpark, Staatsliedenbuurt |
| Nieuw-West | 1058(part)–1069 | Slotervaart, Overtoomse Veld, Geuzenveld, Osdorp, Slotermeer, De Aker |
| Zuid | 1071–1079, 1081–1083 | Oud-Zuid, De Pijp, Rivierenbuurt, Vondelpark, Zuidas, Buitenveldert |
| Oost | 1086–1098, 1019 | Oosterpark, Dapperbuurt, Indische Buurt, Watergraafsmeer, IJburg, Oostelijk Havengebied |
| Noord | 1020–1037 | Overhoeks, Buiksloterham, NDSM, Tuindorp Oostzaan, Nieuwendam |
| Zuidoost | 1101–1108 | Bijlmer, Amstel III, Gaasperdam, Holendrecht, Arena |
| Weesp (part of Amsterdam since 2022) | 1380–1384 | |
| Nearby: Amstelveen 1180–1189, Diemen 1110–1113, Duivendrecht 1115, Zaandam 1500–1509, Haarlem 2000–2037, Badhoevedorp 1171 | | |

"Amsterdam" in a listing title can mean Diemen, Duivendrecht or Amstelveen, so always locate by postcode or coordinates.

## 5. Scams

**Patterns:**
- The landlord is abroad: keys "by courier", Airbnb/Booking "escrow", a foreign IBAN.
- Payment is demanded before a viewing.
- Copied photos (TikTok rental scams went up eightfold in 2026; they often reuse Pararius photos).
- A fake Booking.com rental.
- An ID copy is demanded up front.
- A staged viewing in a borrowed flat.
- Fake WoningNet fees.
- Anti-kraak (anti-squat) offers with fees.
- Rent far below about €20–28/m².
- Any "contract fee" or "admin fee".

**Verification checklist** (the report gives this to the user for each shortlisted listing):
1. Kadaster eigendomsinformatie (€3.70) to check whether the owner matches the person letting.
2. KvK (Chamber of Commerce) lookup for companies and managers: trade name, age, activity code.
3. Reverse-image search the photos. Check the address on Street View.
4. Search the name plus "oplichting", "klacht" or "review".
5. Never pay before a physical viewing and a signed contract. Pay only to a Dutch or EU IBAN in the landlord's or company's name.
6. Send ID copies only with a watermark (the KopieID app), and only after the landlord is verified.
7. If scammed: Fraudehelpdesk 088-7867372, the police, and the bank.

## 6. Who counts as "direct"

- **Direct landlord (verhuurder):** the owner. Can be a private person, an institutional investor, or a housing association (for mid-rent or free sector). ✅
- **Property manager (beheerder / vastgoedmanagement / operator):** lets units on the owner's behalf and is not allowed to charge the tenant. ✅
- **Agent (makelaar / verhuurmakelaar / relocation / rental agency):** an intermediary. ❌ **Exclude.**

Pararius lists *every* advertiser under `/real-estate-agents/`, including owners such as Vesteda and Heimstaden. **Classify by who the entity is, not by the site's section.** Lists of names: `knowledge/advertisers.md`.

## 7. Applying (goes in the report's "how to win" box)

- **Income:** usually 3× the monthly rent gross for one earner, or 4× combined for couples. Bouwinvest asks for 42× (single) or 48× (more than one person) yearly.
- **The pack, as one PDF:**
  - Watermarked ID
  - Werkgeversverklaring (employer statement)
  - Last 3 payslips
  - Bank statement
  - Employment contract
  - Verhuurdersverklaring (landlord reference)
  - BRP extract
  - A guarantor if income is short
- **What wins:**
  - Respond within minutes.
  - Add a short personal motivation.
  - Be flexible on dates.
  - Pre-register on landlord portals (Vesteda, Wonen bij Bouwinvest, ikwilhuren.nu, Holland2Stay), since many let units only to pre-registered applicants.
  - For mid-rent, confirm the Amsterdam housing-permit income limits first.

## Sources (selection)
Rijksoverheid indexation 2026 · volkshuisvestingnederland.nl (maximum rents; good landlordship rules) · Aedes huurbeleid 2027 · Pararius rent-increase guide 2026 · NVM Q2 2026 analysis · CBS rents 2026 · DutchNews (mid-rent permit; €/m² Sept 2026; TikTok scams) · iamexpat (rooms €950; Booking scams) · Huisvestingsverordening Amsterdam 2024 (CVDR706038) · Raad van State 202101676/1/A3 · NH Nieuws (illegal subletting evictions) · inburgering.org (registration) · Kadaster eigendomsinformatie · findlawyer.nl rental scams · vesteda.com · holland2stay.com · BAM/Bouwinvest press release Feb 2026 · CBRE OurDomain sale Nov 2026.
