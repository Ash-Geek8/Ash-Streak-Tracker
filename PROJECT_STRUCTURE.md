# Structure
- backend/: Flask app factory, configuration, SQLAlchemy models, API routes, timezone and notes retrieval.
- frontend/: Create React App, React UI, Recharts analytics and responsive navy/teal CSS.
- tests/: API smoke test.
- wsgi.py: Gunicorn entry point.
- render.yaml/build.sh: Render deployment starter.
Runtime SQLite and Chroma files live in instance/ (gitignored). PostgreSQL is the hosted source of truth; Chroma is a rebuildable notes-only cache.
