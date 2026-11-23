"""Step 4: render runs/<stamp>/results.json into ONE artifact page: report/amsterdam-apartments.html

  python3 tools/build_report.py runs/<stamp>

Always the same output path, so re-publishing updates the same artifact URL.
"""
import datetime as dt
import html
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "report", "amsterdam-apartments.html")

KEEP = ["source", "url", "title", "property_type", "price_eur", "price_includes", "deposit_eur", "size_m2", "bedrooms",
        "furnished", "street", "postcode", "city", "district", "area_name", "neighbourhood", "area_confirmed",
        "available_from", "available_to", "min_stay_months", "max_stay_months", "registration_possible",
        "advertiser_name", "advertiser_verdict", "advertiser_reason", "tenure", "tenure_reason", "red_flags", "notes",
        "score", "also_on", "posted", "description"]

SOURCE_LABEL = {"kamernet": "Kamernet", "housinganywhere": "HousingAnywhere", "directwonen": "DirectWonen",
                "marktplaats": "Marktplaats", "pararius": "Pararius", "vesteda": "Vesteda", "mvgm": "MVGM ikwilhuren",
                "dak": "DĀK Amsterdam", "codomo": "Holland2Stay/Codomo", "heimstaden": "Heimstaden", "kamer.nl": "Kamer.nl",
                "funda": "Funda", "corporatie": "Housing association"}


def slim(r):
    o = {k: r.get(k) for k in KEEP}
    if o.get("description"):
        o["description"] = o["description"][:420]
    return o


def main(run):
    res = json.load(open(os.path.join(run, "results.json")))
    p, st = res["params"], res["stats"]
    data = {
        "params": p,
        "generated": dt.datetime.now().strftime("%d %b %Y, %H:%M"),
        "leases": [slim(r) for r in res["leases"]],
        "sublets": [slim(r) for r in res["sublets"]],
        "excluded_reasons": st["excluded_reasons"],
        "excluded_n": len(res["excluded"]),
        "raw_n": st["raw"],
        "by_source_raw": st["by_source_raw"],
        "by_source_kept": st["by_source_kept"],
        "source_status": st.get("source_status", {}),
        "source_label": SOURCE_LABEL,
    }
    page = TEMPLATE.replace("/*DATA*/null", json.dumps(data, ensure_ascii=False).replace("</", "<\\/"))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w").write(page)
    print(OUT, f"{len(page)//1024} KB", f"leases={len(data['leases'])} sublets={len(data['sublets'])}")


TEMPLATE = r"""<title>Amsterdam Flat Hunt</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap">
<style>
/* Layout: canal-water toolbar band on top, then a single reading column of listing rows (photo | facts | verdict), tabs split new leases from sublets. */
:root{
  --bg:#f3f5f4; --surface:#ffffff; --ink:#15211f; --muted:#5b6b67; --line:#d9e0dd;
  --water:#1f4b4a; --water-ink:#e9f2f0; --accent:#c8102e; --accent-soft:#fbe7ea;
  --ok:#1d7a4c; --ok-soft:#e3f3ea; --warn:#a15c00; --warn-soft:#fdf0dc; --bad:#b4232c; --bad-soft:#fbe5e6;
  --f-display:"Bricolage Grotesque", "Avenir Next", system-ui, sans-serif;
  --f-body:"Inter", system-ui, -apple-system, "Segoe UI", sans-serif;
  --f-mono:"JetBrains Mono", ui-monospace, "SF Mono", Menlo, monospace;
}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){
  --bg:#0f1716; --surface:#16211f; --ink:#e4ecea; --muted:#94a6a1; --line:#283633;
  --water:#123432; --water-ink:#d8ebe7; --accent:#ff5c6e; --accent-soft:#3a1a1f;
  --ok:#5fd39a; --ok-soft:#14301f; --warn:#f0b35a; --warn-soft:#33260f; --bad:#ff7a82; --bad-soft:#3a1719; color-scheme:dark}}
:root[data-theme="dark"]{
  --bg:#0f1716; --surface:#16211f; --ink:#e4ecea; --muted:#94a6a1; --line:#283633;
  --water:#123432; --water-ink:#d8ebe7; --accent:#ff5c6e; --accent-soft:#3a1a1f;
  --ok:#5fd39a; --ok-soft:#14301f; --warn:#f0b35a; --warn-soft:#33260f; --bad:#ff7a82; --bad-soft:#3a1719; color-scheme:dark}
*{box-sizing:border-box}
body{background:var(--bg);color:var(--ink);font:15px/1.5 var(--f-body);margin:0}
a{color:inherit}
.wrap{max-width:1080px;margin:0 auto;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px))}
header.band{background:var(--water);color:var(--water-ink);margin-top:calc(-1 * env(safe-area-inset-top,0px));padding-top:env(safe-area-inset-top,0px)}
header .wrap{padding-block:28px 22px;display:grid;gap:14px}
.eyebrow{font:500 12px/1 var(--f-mono);letter-spacing:.08em;text-transform:uppercase;opacity:.75}
h1{font:700 clamp(28px,5vw,44px)/1.05 var(--f-display);margin:0;text-wrap:balance}
h1 .x{display:inline-flex;gap:.18em;vertical-align:.12em;margin-right:.3em}
h1 .x i{width:.42em;height:.42em;background:var(--accent);clip-path:polygon(20% 0,50% 30%,80% 0,100% 20%,70% 50%,100% 80%,80% 100%,50% 70%,20% 100%,0 80%,30% 50%,0 20%)}
.brief{display:flex;flex-wrap:wrap;gap:8px 22px;font-size:14px}
.brief b{font:500 15px var(--f-mono)}
.counts{display:flex;flex-wrap:wrap;gap:8px}
.count{background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.18);border-radius:999px;padding:4px 12px;font:500 13px var(--f-mono)}
nav.tabs{position:sticky;top:env(safe-area-inset-top,0px);z-index:5;background:var(--bg);border-bottom:1px solid var(--line)}
body::before{content:"";position:fixed;inset:0 0 auto;height:env(safe-area-inset-top,0px);z-index:10;background:var(--bg)}
nav .wrap{display:flex;flex-wrap:wrap;align-items:center;gap:10px;padding-block:10px}
.tab{font:600 15px var(--f-body);background:none;border:0;border-bottom:3px solid transparent;padding:8px 4px;color:var(--muted);cursor:pointer}
.tab[aria-selected="true"]{color:var(--ink);border-color:var(--accent)}
.tab span{font:500 12px var(--f-mono);margin-left:6px;color:var(--muted)}
.filters{display:flex;flex-wrap:wrap;gap:8px;margin-left:auto}
select,label.chk{font:14px var(--f-body);background:var(--surface);color:var(--ink);border:1px solid var(--line);border-radius:8px;padding:6px 8px}
label.chk{display:inline-flex;gap:6px;align-items:center;cursor:pointer}
:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
main .wrap{padding-block:18px 40px;display:grid;gap:28px}
.intro{color:var(--muted);max-width:68ch;margin:0}
.list{display:grid;gap:12px}
.row{padding:14px 16px!important;display:grid;grid-template-columns:minmax(0,1fr) 260px;gap:18px;background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:12px}
.row.flagged{border-left:4px solid var(--warn)}
.ph{width:168px;aspect-ratio:4/3;max-width:100%;border-radius:6px;object-fit:cover;background:var(--line);display:block}
.ph.none{display:grid;place-items:center;color:var(--muted);font:12px var(--f-mono)}
.facts{min-width:0;display:grid;gap:6px;align-content:start}
.ttl{font:700 18px/1.2 var(--f-display);margin:0;text-wrap:balance}
.ttl a{text-decoration:none}.ttl a:hover{text-decoration:underline}
.where{font:500 13px var(--f-mono);color:var(--muted)}
.nums{display:flex;flex-wrap:wrap;gap:6px 16px;font:500 14px var(--f-mono);font-variant-numeric:tabular-nums}
.nums .price{font-size:18px;color:var(--ink)}
.nums small{color:var(--muted);font-size:12px}
.desc{color:var(--muted);font-size:13.5px;margin:0;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}
.tags{display:flex;flex-wrap:wrap;gap:6px}
.tag{font:500 12px var(--f-body);padding:2px 8px;border-radius:999px;background:var(--bg);border:1px solid var(--line);color:var(--muted)}
.tag.ok{background:var(--ok-soft);color:var(--ok);border-color:transparent}
.side{display:grid;gap:8px;align-content:start;min-width:0}
.verdict{border-radius:8px;padding:8px 10px;font-size:13px;background:var(--bg)}
.verdict b{display:block;font:600 12px var(--f-mono);letter-spacing:.06em;text-transform:uppercase;margin-bottom:2px}
.v-private b{color:var(--ok)} .v-landlord b,.v-manager b{color:var(--water)} .v-unverified b{color:var(--warn)}
:root[data-theme="dark"] .v-landlord b,:root[data-theme="dark"] .v-manager b{color:var(--water-ink)}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]) .v-landlord b,:root:not([data-theme="light"]) .v-manager b{color:var(--water-ink)}}
.flags{display:grid;gap:4px;margin:0;padding:0;list-style:none}
.flags li{font-size:12.5px;padding:5px 8px;border-radius:6px;background:var(--warn-soft);color:var(--warn)}
.notes{font-size:12.5px;color:var(--muted);margin:0;padding-left:16px}
.open{justify-self:start;font:600 13px var(--f-body);background:var(--accent);color:#fff;border-radius:8px;padding:7px 12px;text-decoration:none}
.also{font-size:12px;color:var(--muted)}
.empty{background:var(--surface);border:1px dashed var(--line);border-radius:10px;padding:22px;color:var(--muted)}
section h2{font:700 22px/1.2 var(--f-display);margin:0 0 10px}
.cols{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px}
.panel{background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:16px 18px}
.panel h3{font:600 15px var(--f-body);margin:0 0 8px}
.panel ul,.panel ol{margin:0;padding-left:18px;display:grid;gap:5px;font-size:14px}
.mono{font-family:var(--f-mono);font-size:13px}
table{border-collapse:collapse;width:100%;font-size:13.5px;font-variant-numeric:tabular-nums}
td,th{text-align:left;padding:6px 8px;border-bottom:1px solid var(--line)} th{font:600 12px var(--f-mono);text-transform:uppercase;letter-spacing:.06em;color:var(--muted)}
.tablebox{overflow-x:auto}
footer{color:var(--muted);font-size:12.5px;padding-block:0 30px}
@media (max-width:760px){.row{grid-template-columns:1fr}}
@media (prefers-reduced-motion:no-preference){.row{transition:border-color .15s}.row:hover{border-color:var(--muted)}}
</style>

<header class="band"><div class="wrap">
  <div class="eyebrow">Direct from landlords &amp; property managers · no makelaars</div>
  <h1><span class="x" aria-hidden="true"><i></i><i></i><i></i></span>Amsterdam flat hunt</h1>
  <div class="brief" id="brief"></div>
  <div class="counts" id="counts"></div>
</div></header>

<nav class="tabs" aria-label="Listing type"><div class="wrap">
  <button class="tab" id="tab-lease" role="tab" aria-selected="true" data-k="leases">New leases<span id="n-lease"></span></button>
  <button class="tab" id="tab-sublet" role="tab" aria-selected="false" data-k="sublets">Sublets &amp; temporary<span id="n-sublet"></span></button>
  <div class="filters">
    <select id="f-district" aria-label="District"></select>
    <select id="f-type" aria-label="Type"></select>
    <select id="f-sort" aria-label="Sort">
      <option value="score">Best match</option><option value="price">Cheapest</option><option value="ppm">Lowest €/m²</option><option value="size">Largest</option><option value="new">Newest</option>
    </select>
    <label class="chk"><input type="checkbox" id="f-reg"> BRP registration</label>
    <label class="chk"><input type="checkbox" id="f-clean"> No red flags</label>
  </div>
</div></nav>

<main><div class="wrap">
  <p class="intro" id="intro"></p>
  <div class="list" id="list"></div>

  <section aria-labelledby="h-apply"><h2 id="h-apply">Before you reply to any of these</h2>
  <div class="cols">
    <div class="panel"><h3>Have this ready as one PDF</h3><ul>
      <li>Passport copy with a watermark (KopieID app)</li>
      <li>Employer statement (werkgeversverklaring) + last 3 payslips</li>
      <li>Employment contract, a bank statement showing salary</li>
      <li>Reference from the current landlord (verhuurdersverklaring)</li>
      <li>Short personal note in English or Dutch: who, job, move-in date</li>
      <li>Income test: usually 3× the rent gross a month (4× for two earners). Without it, a guarantor.</li>
    </ul></div>
    <div class="panel"><h3>Scam and legality checks</h3><ul>
      <li>Never pay anything before a viewing in person and a signed contract.</li>
      <li>Pay only to a Dutch/EU IBAN in the landlord's or company's own name.</li>
      <li>No fees to the tenant: "contract", "admin" or agency fees are illegal.</li>
      <li>Deposit is at most 2 months' base rent.</li>
      <li>Check the owner on Kadaster (€3.70) and companies on KvK.</li>
      <li>Your cousin must be able to register at the address (BRP) to get a BSN.</li>
      <li>Never sublet a housing-association home: illegal, and the subtenant gets evicted.</li>
      <li>Scammed? Fraudehelpdesk <span class="mono">088-7867372</span>, police, bank.</li>
    </ul></div>
    <div class="panel"><h3>Sublet checklist</h3><ul>
      <li>Ask the tenant for the landlord's written permission to sublet.</li>
      <li>If they say they own it, ask for proof and check Kadaster.</li>
      <li>Get a written contract with dates, rent, deposit and who pays utilities.</li>
      <li>A fixed end date is only legal from an owner who is away temporarily, or for specific groups such as students.</li>
    </ul></div>
  </div></section>

  <section aria-labelledby="h-manual"><h2 id="h-manual">Also check by hand</h2>
  <div class="cols">
    <div class="panel"><h3>Landlord portals (register free, apply directly)</h3><ul>
      <li><a href="https://amsterdam.mijndak.nl/Woningaanbod" target="_blank" rel="noopener">DĀK regio Amsterdam</a>: Middenhuur and Vrije sector tabs</li>
      <li><a href="https://www.vesteda.com/en/unit-search?placeType=1&sortType=1&radius=5&s=Amsterdam" target="_blank" rel="noopener">Vesteda</a></li>
      <li><a href="https://ikwilhuren.nu/aanbod/" target="_blank" rel="noopener">MVGM ikwilhuren.nu</a> (also Bouwinvest homes)</li>
      <li><a href="https://codomo.eu/homes/nl/en?from=holland2stay" target="_blank" rel="noopener">Holland2Stay / Codomo</a></li>
      <li><a href="https://heimstaden.com/nl/" target="_blank" rel="noopener">Heimstaden</a>, <a href="https://www.lievendekey.nl/" target="_blank" rel="noopener">Lieven de Key</a>, <a href="https://www.de-alliantie.nl/ik-zoek/" target="_blank" rel="noopener">de Alliantie</a>, <a href="https://www.stadgenoot.nl/" target="_blank" rel="noopener">Stadgenoot</a>, <a href="https://www.rochdale.nl/" target="_blank" rel="noopener">Rochdale</a>, <a href="https://www.eigenhaard.nl/" target="_blank" rel="noopener">Eigen Haard</a></li>
    </ul></div>
    <div class="panel"><h3>Facebook groups (private sublets, high scam risk)</h3><ul>
      <li>Rooms for Amsterdam</li><li>Amsterdam Housing</li><li>Amsterdam Rooms and Apartments</li>
      <li>Apartments for Rent Amsterdam The Netherlands</li><li>Amsterdam Apartments and Housing (NO SPAM)</li><li>Expats in Amsterdam</li>
    </ul></div>
    <div class="panel"><h3>Left out on purpose</h3><ul>
      <li>Makelaars and rental agencies (all Funda agents, most Pararius advertisers)</li>
      <li>Rentola, Huurportaal: scraped ads and subscription traps</li>
      <li>Anti-kraak (anti-squat): agency-run, no tenant protection</li>
      <li>Huurwoningen.nl: mirrors Pararius and hides who is advertising</li>
    </ul></div>
  </div></section>

  <section aria-labelledby="h-run"><h2 id="h-run">What was searched</h2>
    <div class="tablebox"><table id="srcs"><thead><tr><th>Source</th><th>Found</th><th>Shown</th><th>Status</th></tr></thead><tbody></tbody></table></div>
    <p class="intro" id="excl" style="margin-top:12px"></p>
  </section>
</div></main>
<footer><div class="wrap" id="foot"></div></footer>

<script>
const D=/*DATA*/null;
const $=s=>document.querySelector(s), esc=s=>String(s??"").replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const eur=n=>n==null?"–":"€"+Number(n).toLocaleString("en-GB");
const VERDICT={private:"Private landlord",landlord:"Direct landlord",manager:"Property manager",unverified:"Check advertiser"};
let tab="leases"; try{const t=localStorage.getItem("afh-tab"); if(t==="sublets"||t==="leases") tab=t}catch(e){}
const P=D.params;
$("#brief").innerHTML=`<span>Budget <b>${eur(P.budget)}</b>/month</span><span>Area <b>${esc(P.area_label||"All of Amsterdam")}</b></span><span>Types <b>${esc((P.types||[]).join(", "))}</b></span><span>Searched <b>${esc(D.generated)}</b></span>`;
$("#counts").innerHTML=`<span class="count">${D.leases.length} new leases</span><span class="count">${D.sublets.length} sublets</span><span class="count">${D.raw_n} scanned · ${D.excluded_n} filtered out</span>`;
$("#n-lease").textContent=D.leases.length; $("#n-sublet").textContent=D.sublets.length;
const all=[...D.leases,...D.sublets];
const dists=[...new Set(all.map(r=>r.district).filter(Boolean))].sort();
$("#f-district").innerHTML=`<option value="">All districts</option>`+dists.map(d=>`<option>${esc(d)}</option>`).join("");
const types=[...new Set(all.map(r=>r.property_type).filter(Boolean))].sort();
$("#f-type").innerHTML=`<option value="">All types</option>`+types.map(d=>`<option>${esc(d)}</option>`).join("");
function card(r){
  const ppm=r.price_eur&&r.size_m2?Math.round(r.price_eur/r.size_m2):null;
  const where=[r.postcode&&r.postcode.replace(/(\d{4})\s?([A-Z]{2})/,"$1 $2"),r.neighbourhood,r.district].filter(Boolean).join(" · ")||esc(r.city||"");
  const dates=r.available_to?`${r.available_from||"now"} → ${r.available_to}`:(r.available_from?`from ${r.available_from}`:"");
  const stay=[r.min_stay_months&&`min ${r.min_stay_months} mo`,r.max_stay_months&&`max ${r.max_stay_months} mo`].filter(Boolean).join(", ");
  const tags=[r.property_type,r.furnished,r.bedrooms!=null&&r.bedrooms!==""?`${r.bedrooms} bedroom${r.bedrooms==1?"":"s"}`:null,dates,stay].filter(Boolean).map(t=>`<span class="tag">${esc(t)}</span>`).join("")
    +(r.registration_possible===true?`<span class="tag ok">BRP registration possible</span>`:"")
    +`<span class="tag">${esc(D.source_label[r.source]||r.source)}</span>`;
  const flags=(r.red_flags||[]).map(f=>`<li>${esc(f)}</li>`).join("");
  const notes=(r.notes||[]).map(n=>`<li>${esc(n)}</li>`).join("");
  const also=(r.also_on||[]).map(a=>`<a href="${esc(a.url)}" target="_blank" rel="noopener">${esc(D.source_label[a.source]||a.source)}</a>`).join(", ");
  return `<article class="row${flags?" flagged":""}">
    <div class="facts">
      <h3 class="ttl"><a href="${esc(r.url)}" target="_blank" rel="noopener">${esc(r.title||r.street||"Listing")}</a></h3>
      <div class="where">${where}${r.area_confirmed===false?" · area not confirmed":""}</div>
      <div class="nums"><span class="price">${eur(r.price_eur)}</span><small>${esc(r.price_includes||"")}</small>${r.size_m2?`<span>${r.size_m2} m²</span>`:""}${ppm?`<span>€${ppm}/m²</span>`:""}${r.deposit_eur?`<span><small>deposit</small> ${eur(r.deposit_eur)}</span>`:""}</div>
      ${r.description?`<p class="desc">${esc(r.description)}</p>`:""}
      <div class="tags">${tags}</div>
    </div>
    <div class="side">
      <div class="verdict v-${esc(r.advertiser_verdict)}"><b>${esc(VERDICT[r.advertiser_verdict]||r.advertiser_verdict)}</b>${esc(r.advertiser_name?r.advertiser_name+": ":"")}${esc(r.advertiser_reason||"")}</div>
      <div class="verdict"><b>${r.tenure==="sublet"?"Sublet / temporary":"Long-term lease"}</b>${esc(r.tenure_reason||"")}</div>
      ${flags?`<ul class="flags">${flags}</ul>`:""}
      ${notes?`<ul class="notes">${notes}</ul>`:""}
      <a class="open" href="${esc(r.url)}" target="_blank" rel="noopener">Open listing ↗</a>
      ${also?`<div class="also">Also on ${also}</div>`:""}
    </div></article>`;
}
function render(){
  document.querySelectorAll(".tab").forEach(b=>b.setAttribute("aria-selected",b.dataset.k===tab));
  const d=$("#f-district").value,t=$("#f-type").value,s=$("#f-sort").value,reg=$("#f-reg").checked,clean=$("#f-clean").checked;
  let L=D[tab].filter(r=>(!d||r.district===d)&&(!t||r.property_type===t)&&(!reg||r.registration_possible===true)&&(!clean||!(r.red_flags||[]).length));
  const ppm=r=>r.price_eur&&r.size_m2?r.price_eur/r.size_m2:1e9;
  L.sort({score:(a,b)=>b.score-a.score,price:(a,b)=>a.price_eur-b.price_eur,ppm:(a,b)=>ppm(a)-ppm(b),size:(a,b)=>(b.size_m2||0)-(a.size_m2||0),new:(a,b)=>String(b.posted||"").localeCompare(String(a.posted||""))}[s]);
  $("#intro").textContent=tab==="leases"
    ?"Homes with no end date, offered by the owner, a private landlord or a landlord's property manager. Since July 2024 new leases are indefinite by law, so these are the long-term options."
    :"Fixed-period homes: sublets from a tenant, owners away for a while, and furnished mid-term stays. Each one needs the landlord's written consent or proof of ownership.";
  $("#list").innerHTML=L.length?L.map(card).join(""):`<div class="empty">Nothing matches these filters. Loosen the district, type or checkbox filters above, or rerun the search with a higher budget or wider area.</div>`;
}
document.querySelectorAll(".tab").forEach(b=>b.addEventListener("click",()=>{tab=b.dataset.k;try{localStorage.setItem("afh-tab",tab)}catch(e){};render()}));
["#f-district","#f-type","#f-sort","#f-reg","#f-clean"].forEach(id=>$(id).addEventListener("change",render));
render();
const st=D.source_status||{};
const srcs=[...new Set([...Object.keys(D.by_source_raw),...Object.keys(st)])];
$("#srcs tbody").innerHTML=srcs.map(k=>`<tr><td>${esc(D.source_label[k]||k)}</td><td>${D.by_source_raw[k]||0}</td><td>${D.by_source_kept[k]||0}</td><td>${st[k]?(st[k].ok?"searched":"failed: "+esc(st[k].error||"")):"searched"}</td></tr>`).join("");
const ex=Object.entries(D.excluded_reasons).sort((a,b)=>b[1]-a[1]).map(([k,v])=>`${v} ${k}`).join(" · ");
$("#excl").textContent=ex?`Filtered out: ${ex}.`:"";
$("#foot").textContent="Built by the Amsterdam rental agent in Claude Code. Listings change by the hour: open each one to confirm it is still available. This page is not legal advice.";
</script>
"""

if __name__ == "__main__":
    main(sys.argv[1])
