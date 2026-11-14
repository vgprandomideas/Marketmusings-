import os
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

app = FastAPI(title="MarketOS Pro", version="0.3.0")
HEADERS = {"User-Agent": os.getenv("SEC_USER_AGENT", "MarketOS research contact admin@example.com")}

async def fetch(url, params=None, headers=None):
    async with httpx.AsyncClient(timeout=18, follow_redirects=True) as client:
        try:
            r = await client.get(url, params=params, headers=headers)
            r.raise_for_status()
            return r.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise HTTPException(502, detail=f"Upstream provider unavailable: {type(exc).__name__}")

@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "0.3.0"}

@app.get("/api/fred/{series}")
async def fred(series: str):
    key = os.getenv("FRED_API_KEY")
    if not key:
        raise HTTPException(503, detail="FRED_API_KEY not configured")
    if not series.replace("_", "").isalnum() or len(series) > 40:
        raise HTTPException(400, detail="Invalid series")
    return await fetch("https://api.stlouisfed.org/fred/series/observations",
                       {"series_id": series, "api_key": key, "file_type": "json", "sort_order": "desc", "limit": 120})

@app.get("/api/polymarket")
async def polymarket(limit: int = 25):
    limit = max(1, min(limit, 100))
    return await fetch("https://gamma-api.polymarket.com/markets",
                       {"active": "true", "closed": "false", "limit": limit, "order": "volumeNum", "ascending": "false"})

@app.get("/api/sec/{cik}")
async def sec(cik: str):
    if not cik.isdigit() or len(cik) > 10:
        raise HTTPException(400, detail="CIK must be numeric")
    if "example.com" in HEADERS["User-Agent"]:
        raise HTTPException(503, detail="Configure SEC_USER_AGENT with a real contact email")
    return await fetch(f"https://data.sec.gov/submissions/CIK{int(cik):010d}.json", headers=HEADERS)

@app.get("/", response_class=HTMLResponse)
async def index():
    return PAGE

PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>MarketOS Pro | Financial Intelligence</title>
<style>
:root{color-scheme:dark;font-family:Inter,ui-sans-serif,system-ui,Arial;background:#0a0e17;color:#edf2fc}
*{box-sizing:border-box}body{margin:0}.shell{display:grid;grid-template-columns:230px 1fr;min-height:100vh}
aside{border-right:1px solid #273043;background:#101725;padding:26px 18px}
.brand{font-size:23px;font-weight:800;letter-spacing:-.7px;color:#7cb6ff;margin-bottom:35px}
.nav{padding:13px 12px;color:#9fb0cb;border-radius:9px;margin:6px 0;cursor:pointer}
.nav.active,.nav:hover{background:#1e304c;color:white}
main{padding:32px;max-width:1600px;width:100%;margin:auto}
header{display:flex;justify-content:space-between;align-items:center;gap:20px;flex-wrap:wrap}
h1{font-size:28px;letter-spacing:-.7px;margin:0}p{color:#9fb0cb}
.tag{font-size:12px;background:#1b3446;color:#83d4c2;padding:8px 11px;border-radius:99px}
.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;margin:28px 0}
.card{background:#131d2d;border:1px solid #28384f;border-radius:15px;padding:22px;min-width:0}
.card b{font-size:19px}.card small{display:block;color:#8fa2bd;margin:10px 0}
button,input,select{background:#17253a;border:1px solid #344862;border-radius:8px;color:#f4f7ff;padding:11px 13px;font:inherit}
button{cursor:pointer;background:#2762b5;border-color:#2762b5}button:hover{background:#367bd5}
.controls{display:flex;flex-wrap:wrap;gap:10px;margin:15px 0}
pre{white-space:pre-wrap;overflow-wrap:anywhere;max-height:500px;overflow:auto;color:#c5d5ec;font-size:12px}
table{width:100%;border-collapse:collapse;font-size:13px}td,th{text-align:left;border-bottom:1px solid #27384f;padding:12px}
th{color:#9fb0cb}.error{color:#ff9b9b}.muted{color:#8fa2bd}
@media(max-width:850px){.shell{display:block}aside{padding:12px;display:flex;align-items:center;gap:8px;overflow:auto}.brand{margin:0 15px 0 0;white-space:nowrap}.nav{white-space:nowrap}main{padding:18px}.grid{grid-template-columns:1fr}}
</style></head><body>
<div class="shell"><aside><div class="brand">◈ MarketOS Pro</div>
<div class="nav active" onclick="tab('overview',this)">Overview</div>
<div class="nav" onclick="tab('predictions',this)">Prediction markets</div>
<div class="nav" onclick="tab('macro',this)">Macro data</div>
<div class="nav" onclick="tab('filings',this)">SEC filings</div>
</aside><main><header><div><h1 id="heading">Financial Intelligence Terminal</h1><p>Research-grade dashboard · Public market feeds · Beta</p></div><span class="tag">Public data connectors</span></header>
<div class="grid"><div class="card"><small>Prediction markets</small><b>Polymarket</b><small>Active market discovery</small></div>
<div class="card"><small>Economic series</small><b>FRED</b><small>Federal Reserve data</small></div>
<div class="card"><small>Corporate disclosures</small><b>SEC EDGAR</b><small>Official US company filings</small></div></div>
<section class="card"><div class="controls" id="controls"></div><div id="output" class="muted">Select a workspace to retrieve provider data.</div></section>
<p class="muted">Data is informational, may be delayed or unavailable, and is not investment advice. MarketOS is not affiliated with Bloomberg.</p>
</main></div>
<script>
let active='overview';
function tab(name,el){active=name;document.querySelectorAll('.nav').forEach(x=>x.classList.remove('active'));el.classList.add('active');render()}
function render(){
const c=document.getElementById('controls'),o=document.getElementById('output'),h=document.getElementById('heading');
h.textContent={overview:'Financial Intelligence Terminal',predictions:'Prediction Markets',macro:'Macroeconomic Data',filings:'SEC Company Filings'}[active];
o.textContent='Select a dataset and click Fetch data.';
if(active==='overview'){c.innerHTML='<button onclick="tab(\'predictions\',document.querySelectorAll(\'.nav\')[1])">Explore markets</button>';return}
if(active==='predictions')c.innerHTML='<label>Markets <input id="limit" type="number" value="25" min="1" max="100"></label><button onclick="load(\'/api/polymarket?limit=\'+document.getElementById(\'limit\').value)">Fetch active markets</button>';
if(active==='macro')c.innerHTML='<label>FRED series <input id="series" value="DGS10" placeholder="DGS10"></label><button onclick="load(\'/api/fred/\'+encodeURIComponent(document.getElementById(\'series\').value))">Fetch observations</button>';
if(active==='filings')c.innerHTML='<label>Company CIK <input id="cik" value="320193" placeholder="320193"></label><button onclick="load(\'/api/sec/\'+encodeURIComponent(document.getElementById(\'cik\').value))">Fetch filings</button>';
}
function esc(s){return String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
async function load(url){let o=document.getElementById('output');o.textContent='Loading provider data...';
try{let r=await fetch(url);let d=await r.json();if(!r.ok)throw Error(d.detail||'Provider error');
if(active==='predictions'&&Array.isArray(d)){o.innerHTML='<table><thead><tr><th>Market</th><th>Volume</th><th>Liquidity</th></tr></thead><tbody>'+d.map(x=>'<tr><td>'+esc(x.question)+'</td><td>'+esc(x.volumeNum||x.volume)+'</td><td>'+esc(x.liquidityNum||x.liquidity)+'</td></tr>').join('')+'</tbody></table>';return}
if(active==='macro'&&d.observations){o.innerHTML='<table><tr><th>Date</th><th>Value</th></tr>'+d.observations.slice(0,100).map(x=>'<tr><td>'+esc(x.date)+'</td><td>'+esc(x.value)+'</td></tr>').join('')+'</table>';return}
if(active==='filings'){o.innerHTML='<h3>'+esc(d.name)+'</h3><p>CIK: '+esc(d.cik)+'</p><pre>'+esc(JSON.stringify(d.filings?.recent||{},null,2).slice(0,16000))+'</pre>';return}
o.innerHTML='<pre>'+esc(JSON.stringify(d,null,2))+'</pre>';
}catch(e){o.innerHTML='<p class="error">'+esc(e.message)+'</p>'}}
render();
</script></body></html>"""
