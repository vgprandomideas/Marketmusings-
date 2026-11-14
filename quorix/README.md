# QUORIX Financial Intelligence Terminal

Streamlit beta with 16 financial research workspaces. Connected sources: Polymarket Gamma (public), FRED (API key), SEC EDGAR (contact user-agent). Other modules are clearly labelled as planned, not fabricated data.

## Deploy to Streamlit Community Cloud
Repository: `vgprandomideas/Marketmusings-`
Branch: `main`
Main file: `quorix/streamlit_app.py`

Optional Streamlit secrets:
```toml
FRED_API_KEY = "your-key"
SEC_USER_AGENT = "Quorix Research contact@example.org"
```

Run locally: `pip install -r quorix/requirements.txt && streamlit run quorix/streamlit_app.py`

This is a demonstration beta, not a commercially ready, licensed market data terminal. Never commit credentials.
