# Ash Streak

Private daily consistency tracker. Flask API + React Create React App frontend (not Vite).

## Features
- Private login, hashed passwords, secure session cookies; disable registration after first account.
- Daily routines across Food, Prayer, Skincare and Workout.
- Configurable routines, historical completion records, date-specific reflections.
- Local day boundary follows the selected IANA timezone at midnight; history is retained.
- Weeks run Sunday through Saturday (Saturday is week end).
- Analytics filters by date range, category and routine; Recharts daily/category/weekly charts.
- Notes-only RAG: LangChain integration + ChromaDB derived index. Tracker data is never indexed.
- SSE streaming notes assistant with AG-UI-style event envelopes.
- SQLite locally, PostgreSQL when hosted; responsive navy/teal UI.
- Render Free deployment starter; PostgreSQL is durable source of truth and Chroma index is rebuildable.

## Local setup (Windows)
1. Install Python 3.11+ and Node 18+.
2. Copy `.env.example` to `.env`; set a unique `SECRET_KEY`.
3. Backend: `py -m venv .venv`, activate it, `pip install -r requirements.txt`, then `flask --app wsgi.py run`.
4. Frontend: `cd frontend`, `npm install`, `npm start`.
5. Open http://localhost:3000. Create your account while `ALLOW_REGISTRATION=true`, then set it to `false` and restart Flask.

CRA proxies `/api` to Flask at 127.0.0.1:5000.

## Render
Create a Render PostgreSQL database and a Python Web Service. Build command: `./build.sh`; start command: `gunicorn wsgi:app`. Set `SECRET_KEY`, `DATABASE_URL` (Render PostgreSQL URL), `SESSION_COOKIE_SECURE=true`, `ALLOW_REGISTRATION=true` for first account creation, and `CORS_ORIGINS` to the service URL. Create the account, then set `ALLOW_REGISTRATION=false`. Do not rely on the Render web service filesystem for durable data. Chroma is a cache rebuilt from PostgreSQL notes.

## Notes RAG
Only rows in the `notes` table are indexed. Completion records, routines and account metadata are excluded. Chroma lives under `instance/chroma/` and can be rebuilt via `POST /api/notes/rebuild-index` or `flask --app wsgi.py rebuild-notes-index`. The default local Chroma embedding function is used. The notes assistant returns retrieved note excerpts unless a model is deliberately configured.

## API
Auth: `/api/auth/{register,login,logout,me}`. Settings: `/api/settings`. Routines: `/api/routines`. Completions: `/api/days/<date>/completions`. Notes: `/api/notes`. Analytics: `/api/analytics`. SSE assistant: `/api/stream/notes-assistant?q=...`.

## Tests
`pytest`
