# Nouba × AgriFlow — WhatsApp-first MVP

Farmers communicate via the official WhatsApp Cloud API (text or voice). Audio is transcribed, an LLM extracts structured fields, and a cooperative dashboard reviews confirmed requests. **This is a development starter, not a production-ready booking platform.**

## Start backend (Ubuntu)

```bash
cd backend
python3 -m venv ../.venv
../.venv/bin/python -m pip install -r requirements.txt
cp .env.example .env
# edit .env with your own secrets (NEVER commit it)
../.venv/bin/uvicorn app.main:app --reload
```

API docs: http://localhost:8000/docs; health: http://localhost:8000/health

## Run backend tests

The tests use Python's built-in `unittest` and do not call live APIs or require real credentials.

```bash
cd backend
../.venv/bin/python -m unittest discover -s tests -v
```

## Start dashboard (second terminal)

```bash
cd frontend
npm ci
npm run dev
```

Dashboard: http://localhost:5173

## WhatsApp setup

1. Create a Meta developer app with WhatsApp Cloud API and obtain a **test phone number**, phone number ID, access token and app secret.
2. Set `META_VERIFY_TOKEN`, `META_APP_SECRET`, `META_ACCESS_TOKEN`, `META_PHONE_NUMBER_ID` in `backend/.env`.
3. Set `GEMINI_API_KEY` and `GEMINI_MODEL` for Gemini audio transcription and structured extraction. Optionally set `GEMINI_STT_MODEL`; otherwise it uses `GEMINI_MODEL`. Without configuration, the bot reports a processing failure and asks the farmer to retry. See [docs/gemini.md](docs/gemini.md).
4. Expose port 8000 over an HTTPS tunnel (e.g. ngrok). Register `https://YOUR_HOST/webhook/whatsapp` as the Meta webhook URL, with your verify token.
5. Subscribe to the WhatsApp `messages` webhook field. Add your own phone as an allowed recipient in Meta's test configuration.
6. Send a real message to the test number. Inspect `/api/requests` and the dashboard.

### Data flow

`WhatsApp webhook -> signature validation -> message deduplication -> media download (if audio) -> STT -> validated Gemini JSON -> SQLite conversation draft -> follow-up -> summary -> farmer confirms -> saved request (pending_review) -> human approval in dashboard`

The dashboard currently reads requests and approves/rejects them; scheduling, machine availability, pricing, outbound approval notifications and real operator authentication are **not yet implemented**.

### Security and production TODOs

- Add cooperative-user authentication and authorization to all `/api/*` endpoints **before exposing the dashboard publicly**.
- Replace FastAPI in-process background tasks with a durable job queue; implement retry and dead-letter handling for WhatsApp delivery and AI errors.
- Add explicit farmer consent, retention/deletion rules, encrypted storage, rate limits and audit logs.
- Implement conversation states robustly (multiple simultaneous requests, correction intents, relative dates, language variants), and improved handling of ambiguous dates. Gemini output is now validated with Pydantic.
- Store audio only when necessary; do not expose sensitive phone numbers in dashboards without access control.
- Test STT accuracy on real Moroccan Darija samples, including rural dialects and noisy audio.
- Implement machine inventory, availability and booking conflict checks before offering any confirmed slot.
- Use a supported Meta Graph API version; update `META_GRAPH_VERSION` as needed.

## Project structure

- `backend/app/main.py`: app startup, health endpoint and WhatsApp webhook
- `backend/app/routes/`: request and machine API endpoints
- `backend/app/`: configuration, database, WhatsApp, AI and workflow services
- `backend/tests/`: offline backend contract and regression tests
- `frontend/src/main.tsx`: React entry point and legal-page selection
- `frontend/src/App.tsx`: application navigation and static-page embedding
- `frontend/src/pages/`: API-backed dashboard and legal pages
- `frontend/src/shared/`: API client and frontend response types
- `frontend/src/style.css`: shared frontend styles
- `frontend/*.html` and `frontend/public/`: Vite entry pages and static assets
- `docs/`: deployment, integration, Gemini setup and product roadmap guides

## Public information pages

The frontend includes `/privacy`, `/terms` and `/data-deletion`, linked from its
footer. These pages describe the current implementation and clearly mark owner
information that still needs confirmation. See [docs/deployment.md](docs/deployment.md)
for the manual deletion workflow, local preview and frontend-only HTTPS deployment.

## Project guides

- [docs/frontend-backend-integration.md](docs/frontend-backend-integration.md)
- [docs/gemini.md](docs/gemini.md)
- [docs/roadmap-fr.md](docs/roadmap-fr.md)
