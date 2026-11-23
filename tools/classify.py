"""Judgement rules: who is advertising, lease vs sublet, red flags, score.

Rules come from knowledge/market-and-law.md. Advertiser names come from knowledge/advertisers.json.
"""
import json
import os
import re
import unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGISTRY = os.path.join(ROOT, "knowledge", "advertisers.json")

# Name fragments that mean an intermediary (exclude) unless the registry says otherwise.
AGENT_WORDS = [
    "makelaar", "makelaardij", "makelaars", "real estate", "realestate", "estate agent", "rentals", "rental agency",
    "rental service", "relocation", "relocations", "expat", "verhuurmakelaar", "woningbemiddeling", "bemiddeling",
    "housing agency", "home finders", "homefinders", "housing service", "nvm", "vbo", "vastgoedpro", "properties",
    "verhuur.nl", "verhuurt", "huurservice", "huurwoningen", "accommodation service", "residence agency",
]
# Name fragments that mean an owner-side manager / institutional landlord.
MANAGER_WORDS = [
    "vastgoedbeheer", "vastgoedmanagement", "vastgoed management", "property management", "propertymanagement",
    "beheer b.v", "beheer bv", "woningbeheer", "woningcorporatie", "woonstichting", "housing association",
    "investment management", "residential fund", "pensioenfonds",
]
# Text that says an agency is involved / charging the tenant.
AGENT_TEXT = [r"bemiddelingskosten", r"agency fee", r"agent fee", r"contractkosten", r"administratiekosten",
              r"admin(istration)? fee", r"contract fee", r"courtage", r"makelaar", r"via ons kantoor", r"referentienummer"]
SUBLET_TEXT = [r"\bonderhuur", r"\bsub-?let", r"\bsub-?rent", r"\btijdelijk", r"\btemporar", r"while i('| a)m (away|abroad|travel)",
               r"\bi('| a)m (away|abroad|travel)", r"\bgoing abroad", r"\bmoving abroad", r"\bdiplomat", r"tussenhuur",
               r"\bfor (\d+|a few|several|two|three|four|five|six) months", r"\buntil (jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|\d)",
               r"\btot (en met )?\d", r"\bflatmate", r"\bhuisgeno(o|t)", r"\broommate", r"short[- ]stay", r"\bmid[- ]term"]
LEASE_TEXT = [r"onbepaalde tijd", r"indefinite", r"\blong[- ]term", r"\bpermanent", r"vast(e)? huurcontract", r"unlimited (period|term)"]
CORPORATIES = ["ymere", "eigen haard", "stadgenoot", "de key", "rochdale", "de alliantie", "lieven de key", "woonzorg", "habion", "parteon"]
SCAM_TEXT = [r"western union", r"moneygram", r"courier", r"\bdhl\b", r"airbnb (will|payment|escrow)", r"booking\.com (will|payment|escrow)",
             r"keys? (will be )?(sent|posted|mailed)", r"i('| a)m (currently )?(living |working )?(in|out of) the (uk|usa|us|states|country)",
             r"no viewing", r"without (a )?viewing", r"pay (the )?(deposit|rent) (first|before|in advance) (to|and)", r"whatsapp only",
             r"send (me )?(a copy of )?your (passport|id)"]
NO_REG_TEXT = [r"no registration", r"registration (is )?not (possible|allowed)", r"geen inschrijving", r"inschrijven (is )?niet (mogelijk|toegestaan)",
               r"cannot register", r"can't register", r"not possible to register"]


def norm(s):
    return unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()


def _any(patterns, text):
    return [p for p in patterns if re.search(p, text)]


def load_registry():
    with open(REGISTRY) as f:
        return json.load(f)["entries"]


def registry_lookup(name, registry):
    n = norm(name)
    if not n:
        return None
    for e in registry:
        if any(norm(m) in n for m in e["match"]):
            return e
    return None


def classify_advertiser(rec, registry):
    """-> (verdict, reason). verdict: private | landlord | manager | agent | unverified"""
    name = rec.get("advertiser_name") or ""
    raw = (rec.get("advertiser_kind_raw") or "").lower()
    text = norm((rec.get("title") or "") + " " + (rec.get("description") or ""))
    if rec.get("agency_fee_eur"):
        return "agent", f"charges an agency fee (EUR {rec['agency_fee_eur']})"
    hit = registry_lookup(name, registry)
    if hit:
        return hit["verdict"], hit.get("note", "known advertiser")
    nn = norm(name)
    if any(w in nn for w in AGENT_WORDS):
        return "agent", f"advertiser name '{name}' looks like an agency"
    if "landlordtypeid=4" in raw:
        return "agent", "Kamernet marks the advertiser as a real estate agent"
    if "showwebsiteurl=true" in raw:
        return "agent", "Marktplaats business seller (links to a company website)"
    if "externalurl=" in raw:
        return "agent", "listing redirects to an external agency site"
    private_site = ("landlordtypeid=1" in raw or "landlordtypeid=2" in raw or "ownertypes=1;" in raw or "ownertypes=2;" in raw
                    or "private-landlord" in raw or "consumer ad" in raw or raw.strip() in ("private", "particulier"))
    if _any(AGENT_TEXT, text) and not private_site:
        return "agent", "listing text mentions agency/fees"
    if any(w in nn for w in MANAGER_WORDS):
        return "manager", f"advertiser name '{name}' looks like a property manager"
    if private_site:
        if _any(AGENT_TEXT, text):
            return "unverified", "marked private but text mentions agency/fees: check"
        return "private", "site marks advertiser as a private person"
    return "unverified", f"professional advertiser '{name}' not yet in registry: verify (KvK / website)"


def classify_tenure(rec, verdict):
    """-> (kind, reason). kind: lease | sublet"""
    text = norm((rec.get("title") or "") + " " + (rec.get("description") or ""))
    s_hits, l_hits = _any(SUBLET_TEXT, text), _any(LEASE_TEXT, text)
    if rec.get("available_to"):
        return "sublet", f"fixed end date {rec['available_to']}"
    mx = rec.get("max_stay_months")
    if mx and mx <= 12:
        return "sublet", f"max stay {mx} months"
    if s_hits and not l_hits:
        return "sublet", "text: temporary / sublet wording"
    if verdict in ("landlord", "manager"):
        return "lease", "institutional landlord or manager (indefinite lease is the legal default)"
    if l_hits:
        return "lease", "text: indefinite / long-term"
    if "landlordtypeid=2" in (rec.get("advertiser_kind_raw") or "").lower():
        return "sublet", "Kamernet 'roommate' advert: a room in the advertiser's own home"
    if rec.get("property_type") in ("room", "shared room") and verdict == "private" and re.search(r"flatmate|roommate|huisgeno|my apartment|our apartment|mijn appartement", text):
        return "sublet", "room in the advertiser's own rented home"
    return "lease", "no end date given (treat as long-term; confirm with landlord)"


def flags(rec, verdict, tenure):
    """-> (red_flags list, notes list, reject_reason or None)"""
    text = norm((rec.get("title") or "") + " " + (rec.get("description") or "") + " " + (rec.get("advertiser_name") or ""))
    red, notes, reject = [], [], None
    price, size, ptype = rec.get("price_eur"), rec.get("size_m2"), rec.get("property_type")
    if verdict == "agent":
        reject = "agent / intermediary"
    if rec.get("registration_possible") is False or _any(NO_REG_TEXT, text):
        red.append("No address registration (BRP): your cousin could not get a BSN here; often an illegal sublet")
    if rec.get("registration_possible") is True:
        notes.append("Registration (BRP) possible")
    if tenure == "sublet" and verdict == "private" and any(c in text for c in CORPORATIES):
        reject = "sublet of a housing-association (social) home: illegal, eviction risk"
    if tenure == "sublet" and ptype in ("apartment", "studio", "house") and price and price <= 935 and verdict == "private":
        red.append("Whole home at or below the social-rent ceiling (~EUR 933): possible illegal social-housing sublet")
    if price and size and ptype in ("apartment", "studio", "house"):
        ppm = price / size
        if ppm < 14 and verdict in ("private", "unverified"):
            red.append(f"Suspiciously cheap (EUR {ppm:.0f}/m² vs ~EUR 28/m² market): classic scam bait")
        if price > 1228 and size < 50 and verdict in ("landlord", "manager", "private"):
            notes.append("Small unit above the EUR 1,228 mid-rent ceiling: check the WWS points; rent may be legally capped (Huurcommissie)")
    sc = _any(SCAM_TEXT, text)
    if sc:
        red.append("Scam wording in ad (landlord abroad / keys by post / pay before viewing / ID up front)")
    if rec.get("deposit_eur") and price and rec["deposit_eur"] > 2 * price + 1:
        red.append(f"Deposit EUR {rec['deposit_eur']} exceeds the legal max of 2 months' base rent")
    if tenure == "sublet" and verdict == "private":
        notes.append("Ask for the head landlord's written consent to sublet (or proof they own it: Kadaster)")
    if rec.get("source") == "housinganywhere":
        notes.append("HousingAnywhere charges the tenant a one-off platform service fee; first month paid via platform")
    if rec.get("source") == "kamernet":
        notes.append("Kamernet: messaging landlords usually needs a paid tenant subscription")
    if rec.get("source") == "marktplaats":
        notes.append("Marktplaats: low-trust source, never pay before viewing in person")
    if verdict == "unverified":
        notes.append("Advertiser not yet verified as landlord/manager")
    return red, notes, reject


def score(rec, verdict, tenure, red, budget):
    s = 50
    s += {"landlord": 18, "manager": 15, "private": 10, "unverified": -10}.get(verdict, 0)
    if rec.get("registration_possible") is True:
        s += 10
    s -= 18 * len(red)
    if rec.get("advertiser_verified"):
        s += 5
    p = rec.get("price_eur")
    if p and budget:
        s += max(0, 10 - int(10 * p / budget))  # cheaper vs budget -> slightly higher
    if rec.get("size_m2"):
        s += min(10, rec["size_m2"] // 8)
    if rec.get("image"):
        s += 2
    return max(0, min(100, s))
