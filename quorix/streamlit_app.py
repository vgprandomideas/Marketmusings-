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

@st.cache_data(ttl=300, show_spinner=False)
def yahoo_payload(symbol, period="5d"):
    url="https://query1.finance.yahoo.com/v8/finance/chart/"+symbol
    return get_json(url,{"range":period,"interval":"1d"},headers={"User-Agent":"Mozilla/5.0"})

def yahoo_market(symbol):
    result=yahoo_payload(symbol)["chart"]["result"][0]
    meta=result.get("meta",{})
    quotes=result["indicators"]["quote"][0]["close"]
    close=next((float(v) for v in reversed(quotes) if v is not None),None)
    if close is None: return None
    prev=meta.get("chartPreviousClose") or meta.get("previousClose")
    if not prev:
        valid=[v for v in quotes if v is not None]
        prev=valid[-2] if len(valid)>1 else None
    return {"Price":round(close,4),"Change %":round((close/float(prev)-1)*100,2) if prev else None,"Currency":meta.get("currency",""),"Market time (UTC)":datetime.fromtimestamp(meta.get("regularMarketTime",result["timestamp"][-1]),timezone.utc).strftime("%Y-%m-%d %H:%M"),"Source":"Yahoo Finance (unofficial)"}

@st.cache_data(ttl=900,show_spinner=False)
def yahoo_history(symbol,period="6mo"):
    result=yahoo_payload(symbol,period)["chart"]["result"][0]
    ts=result.get("timestamp",[])
    values=result["indicators"]["quote"][0]["close"]
    return pd.DataFrame([{"Date":datetime.fromtimestamp(t,timezone.utc).date(),"Close":float(v)} for t,v in zip(ts,values) if v is not None])

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

if workspace in ("Overview","Global Markets","Derivatives","Screening","News Intelligence","AI Research","Quant Research","Portfolio Analytics","Risk Management","Alerts","Administration"):
    if workspace in ("Overview","Global Markets"):
        st.subheader("Global market monitor")
        st.caption("Latest available observations · exchange spot / reference rates / latest equity bars")
        tab1,tab2,tab3,tab4=st.tabs(["Equities & indices","Commodities","Currencies","Digital assets"])
        with tab1:
            tickers={"S&P 500":"^GSPC","Nasdaq Composite":"^IXIC","Dow Jones":"^DJI","Apple":"AAPL","Microsoft":"MSFT","NVIDIA":"NVDA","Alphabet":"GOOGL","Amazon":"AMZN","Tesla":"TSLA","SPY ETF":"SPY","Nifty 50":"^NSEI","Sensex":"^BSESN"}
            selected=st.multiselect("Instruments",list(tickers),default=list(tickers)[:9])
            equity_rows=[]
            for label in selected:
                try:
                    item=yahoo_market(tickers[label])
                    if item: equity_rows.append({"Instrument":label,**item})
                except (httpx.HTTPError,ValueError,KeyError,IndexError):
                    continue
            if equity_rows:
                edf=pd.DataFrame(equity_rows)
                st.dataframe(edf,use_container_width=True,hide_index=True)
                st.download_button("Export equities",edf.to_csv(index=False),"quorix-equities.csv","text/csv")
                chosen=st.selectbox("Price history",selected)
                try:
                    hist=yahoo_history(tickers[chosen])
                    if not hist.empty: st.plotly_chart(px.line(hist,x="Date",y="Close",title=chosen),use_container_width=True)
                except (httpx.HTTPError,ValueError,KeyError,IndexError) as exc: show_error(exc)
            else: st.warning("Equity feed unavailable. Retry later.")
        with tab2:
            st.caption("Commodity exchange-traded funds track commodity exposure; ETF prices are not physical spot quotes.")
            symbols={"Gold ETF (GLD)":"GLD","Silver ETF (SLV)":"SLV","Oil ETF (USO)":"USO","Natural Gas ETF (UNG)":"UNG","Copper ETF (CPER)":"CPER","Agriculture ETF (DBA)":"DBA"}
            rows=[]
            for label,symbol in symbols.items():
                try:
                    item=yahoo_market(symbol)
                    if item: rows.append({"Instrument":label,**item})
                except (httpx.HTTPError,ValueError,KeyError,IndexError): continue
            if rows:
                df=pd.DataFrame(rows)
                st.dataframe(df,use_container_width=True,hide_index=True)
                st.download_button("Export commodity proxies",df.to_csv(index=False),"quorix-commodity-proxies.csv","text/csv")
            else: st.warning("Commodity proxy quotes currently unavailable.")
        with tab3:
            try:
                fx=get_json("https://api.frankfurter.dev/v1/latest",{"base":"USD"})
                pairs={"EUR/USD":("EUR",True),"GBP/USD":("GBP",True),"USD/JPY":("JPY",False),"USD/INR":("INR",False),"USD/CHF":("CHF",False),"USD/CAD":("CAD",False),"USD/AUD":("AUD",False)}
                rates=fx.get("rates",{})
                rows=[{"Pair":name,"Rate":round(1/rates[ccy] if inv else rates[ccy],6),"As of":fx.get("date"),"Source":"Frankfurter / ECB reference"} for name,(ccy,inv) in pairs.items() if rates.get(ccy)]
                df=pd.DataFrame(rows)
                st.dataframe(df,use_container_width=True,hide_index=True)
                st.download_button("Export FX",df.to_csv(index=False),"quorix-fx.csv","text/csv")
            except (httpx.HTTPError,ValueError,KeyError,ZeroDivisionError) as exc: show_error(exc)
        with tab4:
            pairs={"Bitcoin":"BTC-USD","Ethereum":"ETH-USD","Solana":"SOL-USD","XRP":"XRP-USD","Dogecoin":"DOGE-USD","Cardano":"ADA-USD"}
            rows=[]
            for name,pair in pairs.items():
                try:
                    ticker=get_json("https://api.exchange.coinbase.com/products/"+pair+"/ticker")
                    rows.append({"Asset":name,"Pair":pair,"Price (USD)":float(ticker["price"]),"Bid":float(ticker["bid"]),"Ask":float(ticker["ask"]),"Exchange time (UTC)":ticker.get("time"),"Source":"Coinbase Exchange"})
                except (httpx.HTTPError,ValueError,KeyError): continue
            if rows:
                df=pd.DataFrame(rows)
                st.dataframe(df,use_container_width=True,hide_index=True)
                st.download_button("Export crypto",df.to_csv(index=False),"quorix-crypto.csv","text/csv")
            else: st.warning("Crypto exchange feed currently unavailable.")
    elif workspace=="Portfolio Analytics":
        st.subheader("Portfolio exposure")
        uploaded=st.file_uploader("Upload holdings CSV with columns: symbol, quantity, price",type="csv")
        if uploaded:
            try:
                df=pd.read_csv(uploaded)
                needed={"symbol","quantity","price"}
                if not needed.issubset(df.columns): st.error("Required columns: symbol, quantity, price")
                else:
                    df["value"]=pd.to_numeric(df["quantity"])*pd.to_numeric(df["price"])
                    total=df["value"].sum()
                    df["Weight %"]=df["value"]/total*100 if total else 0
                    st.metric("Portfolio marked value",f"{total:,.2f}")
                    st.dataframe(df,use_container_width=True,hide_index=True)
                    st.plotly_chart(px.pie(df,names="symbol",values="value",title="Portfolio weights"),use_container_width=True)
            except (ValueError,KeyError,TypeError) as exc: st.error(str(exc))
    elif workspace=="Risk Management":
        st.subheader("Return distribution & historical risk")
        symbol=st.text_input("Yahoo Finance symbol",value="SPY",key="risk_symbol")
        try:
            df=yahoo_history(symbol,period="1y")
            if len(df)>30:
                returns=df["Close"].pct_change().dropna()
                m1,m2,m3=st.columns(3)
                m1.metric("Daily volatility",f"{returns.std()*100:.2f}%")
                m2.metric("Annualized volatility",f"{returns.std()*252**.5*100:.2f}%")
                m3.metric("Historical 95% daily VaR",f"{-returns.quantile(.05)*100:.2f}%")
                st.plotly_chart(px.histogram(x=returns*100,nbins=50,labels={"x":"Daily return (%)"},title="Daily return distribution"),use_container_width=True)
            else: st.warning("Insufficient price history.")
        except (httpx.HTTPError,ValueError,KeyError,IndexError) as exc: show_error(exc)
    elif workspace=="Screening":
        st.subheader("Equity comparison")
        universe=["AAPL","MSFT","NVDA","GOOGL","AMZN","META","TSLA","JPM","XOM","WMT","BRK-B","SPY","QQQ"]
        chosen=st.multiselect("Symbols",universe,default=universe[:7])
        rows=[]
        for ticker in chosen:
            try:
                item=yahoo_market(ticker)
                if item: rows.append({"Symbol":ticker,**item})
            except (httpx.HTTPError,ValueError,KeyError,IndexError): continue
        if rows:
            df=pd.DataFrame(rows)
            st.dataframe(df,use_container_width=True,hide_index=True)
            st.download_button("Export screener",df.to_csv(index=False),"quorix-screener.csv","text/csv")
        else: st.warning("No quotes available.")
    elif workspace=="Derivatives":
        st.subheader("US Treasury yield curve")
        key=setting("FRED_API_KEY")
        if key:
            vals=[]
            for label,series in [("1M","DGS1MO"),("3M","DGS3MO"),("6M","DGS6MO"),("1Y","DGS1"),("2Y","DGS2"),("5Y","DGS5"),("10Y","DGS10"),("30Y","DGS30")]:
                try:
                    data=get_json("https://api.stlouisfed.org/fred/series/observations",{"series_id":series,"api_key":key,"file_type":"json","sort_order":"desc","limit":10})
                    obs=next((v for v in data.get("observations",[]) if v.get("value") not in (".",None)),None)
                    if obs: vals.append({"Tenor":label,"Yield %":float(obs["value"]),"Date":obs["date"]})
                except (httpx.HTTPError,ValueError,KeyError): continue
            if vals:
                st.dataframe(pd.DataFrame(vals),use_container_width=True,hide_index=True)
                st.plotly_chart(px.line(pd.DataFrame(vals),x="Tenor",y="Yield %",markers=True,title="Treasury curve"),use_container_width=True)
            else: st.warning("Yield curve unavailable.")
        else: st.warning("FRED_API_KEY is required for Treasury curve data.")
    elif workspace=="Alerts":
        st.subheader("Price threshold check")
        ticker=st.text_input("Symbol",value="AAPL",key="alert_symbol")
        threshold=st.number_input("Alert threshold",min_value=0.0,value=200.0)
        direction=st.selectbox("Condition",["Above","Below"])
        if st.button("Check threshold"):
            try:
                item=yahoo_market(ticker)
                if item:
                    price=item["Price"]
                    st.success(f"{ticker}: {price} — condition {'met' if (price>threshold if direction=='Above' else price<threshold) else 'not met'}")
                else: st.warning("Quote unavailable.")
            except (httpx.HTTPError,ValueError,KeyError,IndexError) as exc: show_error(exc)
        st.caption("Checks run only while requested; no background notification service.")
    elif workspace=="News Intelligence":
        st.subheader("Economic releases")
        st.markdown("[Federal Reserve press releases](https://www.federalreserve.gov/newsevents/pressreleases.htm) · [SEC press releases](https://www.sec.gov/newsroom/press-releases) · [BLS releases](https://www.bls.gov/schedule/news_release/)")
    elif workspace=="Quant Research":
        st.subheader("Technical analytics")
        ticker=st.text_input("Symbol",value="SPY",key="quant_symbol")
        try:
            df=yahoo_history(ticker,period="1y")
            if not df.empty:
                df["MA20"]=df["Close"].rolling(20).mean()
                df["MA50"]=df["Close"].rolling(50).mean()
                fig=px.line(df,x="Date",y=["Close","MA20","MA50"],title=ticker+" · Moving averages")
                st.plotly_chart(fig,use_container_width=True)
                st.dataframe(df.tail(20),use_container_width=True,hide_index=True)
            else: st.warning("Price history unavailable.")
        except (httpx.HTTPError,ValueError,KeyError,IndexError) as exc: show_error(exc)
    elif workspace=="AI Research":
        st.subheader("Research dataset")
        st.markdown("Use **Quant Research** for technical indicators, **Macro Intelligence** for economic time series, and **Prediction Markets** for event probabilities.")
        st.caption("Automated AI inference requires a configured model provider and research validation.")
    elif workspace=="Administration":
        st.subheader("Data connections")
        st.dataframe(pd.DataFrame([{"Provider":"Yahoo Finance chart","Access":"Public endpoint","Coverage":"Equities, indices and ETF proxies"},{"Provider":"Coinbase Exchange","Access":"Public endpoint","Coverage":"Cryptocurrency spot"},{"Provider":"Frankfurter / ECB","Access":"Public endpoint","Coverage":"FX reference rates"},{"Provider":"FRED","Access":"API key","Coverage":"Macro and US Treasury"},{"Provider":"SEC EDGAR","Access":"User-agent contact","Coverage":"Corporate filings"},{"Provider":"Polymarket Gamma","Access":"Public endpoint","Coverage":"Prediction markets"}]),use_container_width=True,hide_index=True)
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


