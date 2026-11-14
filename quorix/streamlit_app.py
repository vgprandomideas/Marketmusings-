import os
import json
from datetime import datetime, timezone
import httpx
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="QUORIX | Financial Intelligence Terminal", page_icon="◈", layout="wide", initial_sidebar_state="collapsed")
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
html,body,[class*="css"],[data-testid="stAppViewContainer"]{font-family:'DM Sans',sans-serif}
[data-testid="stAppViewContainer"]{background:linear-gradient(135deg,#090f19 0%,#0d1522 58%,#0b1220 100%)}
[data-testid="stSidebar"]{background:#0e1726;border-right:1px solid #26354a}
[data-testid="stHeader"]{background:rgba(9,15,25,.78);backdrop-filter:blur(12px)}
.block-container{padding-top:2rem;max-width:1450px}
h1,h2,h3{font-family:'Space Grotesk',sans-serif;letter-spacing:-.04em}
h1{font-size:2rem!important;font-weight:700!important}
h3{font-size:1.12rem!important}
div[data-testid="stMetric"]{background:linear-gradient(135deg,#142238,#101b2c);border:1px solid #26384e;border-radius:12px;padding:15px 17px}
div[data-testid="stMetricLabel"]{color:#8ea3bb}
div[data-testid="stMetricValue"]{font-family:'Space Grotesk';font-size:1.45rem}
div[data-testid="stDataFrame"]{border:1px solid #26384e;border-radius:12px;overflow:hidden}
.stButton button[kind="primary"]{background:#447de8;border:0;border-radius:8px}
.stButton button{border-radius:8px}
div[data-testid="stAlert"]{border-radius:9px}
.q-hero{background:linear-gradient(110deg,#13243b,#102039 60%,#152f48);border:1px solid #2b405c;border-radius:16px;padding:23px 26px;margin:2px 0 20px}
.q-eyebrow{color:#80b7fb;font-size:11px;letter-spacing:.18em;font-weight:700}
.q-title{font-family:'Space Grotesk';font-size:30px;font-weight:700;letter-spacing:-.04em;color:#f4f7ff;margin-top:6px}
.q-sub{color:#9eb2ca;font-size:13px;margin-top:5px}
.q-strip{color:#87a4c4;font-size:11px;letter-spacing:.08em;padding:7px 0 16px}
@media(max-width:700px){.block-container{padding:1.1rem .9rem}.q-hero{padding:17px}.q-title{font-size:24px}h1{font-size:1.65rem!important}}
</style>""", unsafe_allow_html=True)

def setting(key):
    try:
        return st.secrets.get(key, os.getenv(key, ""))
    except Exception:
        return os.getenv(key, "")

@st.cache_data(ttl=120, show_spinner=False)
def get_json(url, params=None, headers=None):
    with httpx.Client(timeout=20, follow_redirects=True) as client:
        response = client.get(url, params=params, headers=headers)
        response.raise_for_status()
        return response.json()

def show_error(exc):
    st.error(f"Provider request failed: {type(exc).__name__}: {exc}")

sections = {
    "MARKETS": ["Overview", "Global Markets", "Equity Analytics", "Fixed Income", "Derivatives", "Macro Intelligence"],
    "INTELLIGENCE": ["Corporate Intelligence", "Prediction Markets", "News Intelligence", "AI Research", "Quant Research"],
    "PORTFOLIO": ["Portfolio Analytics", "Risk Management", "Screening", "Alerts"],
    "SETTINGS": ["Administration"],
}
st.sidebar.markdown("## ◈ QUORIX")
st.sidebar.markdown('<span style="color:#7f9bbd;font-size:10px;letter-spacing:.16em">FINANCIAL INTELLIGENCE</span>', unsafe_allow_html=True)
choices = [item for items in sections.values() for item in items]
if "nav_target" in st.session_state:
    st.session_state["selected_workspace"] = st.session_state.pop("nav_target")
workspace = st.sidebar.radio("Navigation", choices, key="selected_workspace", label_visibility="collapsed")
st.sidebar.divider()
if st.sidebar.button("↻  Refresh", use_container_width=True):
    get_json.clear()
    st.rerun()
st.markdown(f'<div class="q-hero"><div class="q-eyebrow">QUORIX / {next(k for k,v in sections.items() if workspace in v)}</div><div class="q-title">{workspace}</div><div class="q-sub">Markets, data and analytical tools in one workspace</div></div>', unsafe_allow_html=True)
st.markdown('<div class="q-strip">◉ TERMINAL ONLINE &nbsp; · &nbsp; UTC '+datetime.now(timezone.utc).strftime("%d %b %Y · %H:%M")+'</div>',unsafe_allow_html=True)

if workspace == "Overview":
    left,right = st.columns([2.15,1],gap="large")
    with left:
        st.subheader("Prediction market activity")
        try:
            markets = get_json("https://gamma-api.polymarket.com/markets", {"active":"true","closed":"false","limit":40,"order":"volumeNum","ascending":"false"})
            df = pd.DataFrame([{"Market":m.get("question",""),"Volume (USD)":pd.to_numeric(m.get("volumeNum",m.get("volume")),errors="coerce"),"Liquidity (USD)":pd.to_numeric(m.get("liquidityNum",m.get("liquidity")),errors="coerce"),"Closes":m.get("endDate","")[:10]} for m in markets])
            if not df.empty:
                c1,c2,c3 = st.columns(3)
                c1.metric("Active markets shown",f"{len(df):,}")
                c2.metric("Combined volume",f"${df['Volume (USD)'].sum():,.0f}")
                c3.metric("Combined liquidity",f"${df['Liquidity (USD)'].sum():,.0f}")
                st.dataframe(df, use_container_width=True,hide_index=True,height=465)
                st.download_button("Export market data",df.to_csv(index=False),"quorix-markets.csv","text/csv")
            else:
                st.warning("No active markets returned.")
        except (httpx.HTTPError,ValueError,KeyError) as exc:
            show_error(exc)
    with right:
        st.subheader("Research desk")
        st.markdown("**Economic series**")
        st.caption("FRED · US economic indicators")
        if st.button("Open macro intelligence",use_container_width=True):
            st.session_state["nav_target"]="Macro Intelligence"
            st.rerun()
        st.markdown("**Company filings**")
        st.caption("SEC EDGAR · US corporate disclosures")
        if st.button("Open corporate intelligence",use_container_width=True):
            st.session_state["nav_target"]="Corporate Intelligence"
            st.rerun()
        st.markdown("**Market probabilities**")
        st.caption("Polymarket · Active contracts")
        if st.button("Open prediction markets",use_container_width=True):
            st.session_state["nav_target"]="Prediction Markets"
            st.rerun()
elif workspace == "Prediction Markets":
    st.subheader("Polymarket — active markets")
    limit = st.slider("Number of markets", 10, 100, 30, 10)
    if st.button("Fetch active markets", type="primary"):
        try:
            data = get_json("https://gamma-api.polymarket.com/markets", {"active":"true","closed":"false","limit":limit,"order":"volumeNum","ascending":"false"})
            df = pd.DataFrame([{"Question":x.get("question"),"Volume":x.get("volumeNum",x.get("volume")),"Liquidity":x.get("liquidityNum",x.get("liquidity")),"End date":x.get("endDate")} for x in data])
            st.session_state["predictions"] = df
        except (httpx.HTTPError, ValueError) as exc:
            show_error(exc)
    if "predictions" in st.session_state:
        df = st.session_state["predictions"]
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.download_button("Download CSV", df.to_csv(index=False), "quorix-prediction-markets.csv", "text/csv")
elif workspace in ("Macro Intelligence", "Fixed Income"):
    st.subheader("FRED economic and yield data")
    series = st.text_input("FRED series ID", value="DGS10" if workspace=="Fixed Income" else "UNRATE", help="Examples: DGS10, DGS2, UNRATE, CPIAUCSL, GDP")
    if st.button("Fetch observations", type="primary"):
        key = setting("FRED_API_KEY")
        if not key:
            st.warning("Set FRED_API_KEY in Streamlit secrets.")
        elif not series.replace("_","").isalnum() or len(series)>40:
            st.error("Invalid FRED series ID.")
        else:
            try:
                data = get_json("https://api.stlouisfed.org/fred/series/observations", {"series_id":series,"api_key":key,"file_type":"json","sort_order":"asc","limit":10000})
                df = pd.DataFrame(data.get("observations",[]))
                if not df.empty:
                    df["value"] = pd.to_numeric(df["value"], errors="coerce")
                    df["date"] = pd.to_datetime(df["date"], errors="coerce")
                    st.session_state["fred"] = (series,df)
            except (httpx.HTTPError, ValueError) as exc:
                show_error(exc)
    if "fred" in st.session_state:
        sid,df = st.session_state["fred"]
        st.caption(f"Source: FRED · Series: {sid} · Provider observations")
        st.plotly_chart(px.line(df, x="date", y="value", title=sid), use_container_width=True)
        st.dataframe(df.tail(200).sort_values("date",ascending=False),use_container_width=True,hide_index=True)
        st.download_button("Download CSV",df.to_csv(index=False),f"quorix-{sid}.csv","text/csv")
elif workspace in ("Corporate Intelligence","Equity Analytics"):
    st.subheader("SEC EDGAR company submissions")
    cik = st.text_input("Company CIK",value="320193",help="Apple CIK: 320193")
    if st.button("Fetch company filings",type="primary"):
        ua=setting("SEC_USER_AGENT")
        if not ua or "@" not in ua:
            st.warning("Set SEC_USER_AGENT with your organization and valid contact email in Streamlit secrets.")
        elif not cik.isdigit() or len(cik)>10:
            st.error("CIK must be numeric, up to 10 digits.")
        else:
            try:
                data=get_json(f"https://data.sec.gov/submissions/CIK{int(cik):010d}.json",headers={"User-Agent":ua,"Accept-Encoding":"gzip, deflate"})
                st.session_state["sec"] = data
            except (httpx.HTTPError,ValueError) as exc:
                show_error(exc)
    if "sec" in st.session_state:
        data=st.session_state["sec"]
        st.subheader(data.get("name","Company"))
        recent=data.get("filings",{}).get("recent",{})
        fields=["filingDate","form","accessionNumber","primaryDocument"]
        df=pd.DataFrame([{field:recent.get(field,[])[i] if i < len(recent.get(field,[])) else None for field in fields} for i in range(len(recent.get("accessionNumber",[])))])
        st.dataframe(df.head(200),use_container_width=True,hide_index=True)
        st.download_button("Download CSV",df.to_csv(index=False),"quorix-sec-filings.csv","text/csv")
else:
    st.subheader("Workspace")
    st.markdown("Select a connected data module from the navigation.")
    col1,col2=st.columns(2)
    with col1:
        if st.button("Prediction markets",use_container_width=True):
            st.session_state["nav_target"]="Prediction Markets"
            st.rerun()
    with col2:
        if st.button("Company filings",use_container_width=True):
            st.session_state["nav_target"]="Corporate Intelligence"
            st.rerun()


