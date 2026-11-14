# MarketOS Pro — deployment scaffold

A FastAPI-based financial research dashboard with server-side public data integrations.

## Run
```bash
pip install -r requirements.txt
uvicorn app:app --reload
```

Open http://localhost:8000. Docker deployment supports Render's `PORT` environment variable.

Public feeds are best-effort and can be rate limited. This is a beta, not a licensed Bloomberg replacement. Do not offer real-time exchange data commercially without appropriate licensing. Authentication, subscriptions, billing, persistent user data, observability and security review must be completed before commercial launch.
