import os
import json
from datetime import datetime, timezone
import httpx
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="QUORIX | Financial Intelligence Terminal", page_icon="◈", layout="wide", initial_sidebar_state="expanded")
st.markdown("""<style>
[data-testid="stAppViewContainer"]{background:#0b1019}
[data-testid="stSidebar"]{background:#101927}
h1,h2,h3{letter-spacing:-.025em}
div[data-testid="stMetric"]{background:#142034;border:1px solid #2c3d55;border-radius:12px;padding:15px}
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
    "TERMINAL": ["Overview", "Global Markets", "Equity Analytics", "Fixed Income", "Derivatives", "Macro Intelligence"],
    "RESEARCH": ["Corporate Intelligence", "Prediction Markets", "News Intelligence", "AI Research", "Quant Research"],
    "PORTFOLIO": ["Portfolio Analytics", "Risk Management", "Screening", "Alerts"],
    "PLATFORM": ["Administration"],
}
st.sidebar.title("◈ QUORIX")
st.sidebar.caption("FINANCIAL INTELLIGENCE TERMINAL")
choices = [item for items in sections.values() for item in items]
workspace = st.sidebar.radio("Workspaces", choices, label_visibility="collapsed")
st.sidebar.divider()
st.sidebar.caption("Beta · Data sources clearly labelled · No simulated quotes")
if st.sidebar.button("Refresh provider cache", use_container_width=True):
    get_json.clear()
    st.rerun()
st.title(workspace)
st.caption("QUORIX / Institutional research workspace / Public-data beta")
a,b,c,d = st.columns(4)
a.metric("Platform", "QUORIX")
b.metric("Workspace", f"{choices.index(workspace)+1} / {len(choices)}")
c.metric("Mode", "Read-only")
d.metric("Data", "Provider-labelled")
st.caption("Session checked (UTC): " + datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S") + " · Refresh source data using the fetch buttons.")
st.divider()

if workspace == "Overview":
    st.subheader("Connected research sources")
    st.dataframe(pd.DataFrame([
        {"Source":"Polymarket Gamma","Coverage":"Active prediction markets","Requirement":"Public API"},
        {"Source":"FRED","Coverage":"Economic observations and US Treasury yields","Requirement":"FRED_API_KEY"},
        {"Source":"SEC EDGAR","Coverage":"US company filings","Requirement":"SEC_USER_AGENT"},
    ]), use_container_width=True, hide_index=True)
    st.info("Additional institutional modules are under development. No fabricated live prices or analytics are shown.")
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
    st.info(f"{workspace} is a planned research module. A verified provider connection and analytical engine must be implemented before this workspace can display trustworthy results.")
    st.markdown("**Production requirements:** data licensing, persistent storage, authentication, role-based access, monitoring, and tested analytics.")

st.divider()
st.caption("QUORIX is not affiliated with Bloomberg. Data may be delayed, incomplete or subject to provider terms. Not investment advice.")
