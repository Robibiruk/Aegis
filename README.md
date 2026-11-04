# Aegis

Aegis is an AI-assisted personal follow-through platform. The first
milestone focuses on dependable task and reminder state, without requiring
AI or paid integrations.

## Local API

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e '.[test]'
cp .env.example .env
uvicorn apps.api.main:app --reload
```

The API is available at `http://localhost:8000`; OpenAPI documentation is
at `/docs`.

Run tests with:

```bash
pytest
```

The default local database is SQLite. The application uses SQLAlchemy and
can use PostgreSQL by setting `AEGIS_DATABASE_URL` to a PostgreSQL URL.

## Phase 1 scope

- Token-based authentication with persisted sessions
- User-owned task CRUD
- Explicit timezone-aware deadlines
- Durable reminder and delivery-attempt records
- Idempotent reminder processing with state re-checks
- Bounded retry handling for transient delivery failures

Telegram, AI extraction, scraping, and external calendar integrations are
intentionally not part of this foundation.

## Phase 2 slice: URL capture

The web/API foundation now also accepts manual HTTP(S) URLs into an
unreviewed, user-owned source queue. URLs are canonicalized and
deduplicated; they are not fetched, scraped, or converted into tasks
automatically.

## Make the app live locally

Use three terminals:

```bash
# Terminal 1: API
. .venv/bin/activate
uvicorn apps.api.main:app --reload

# Terminal 2: reminder worker
. .venv/bin/activate
python -m apps.worker

# Terminal 3: web app
cd apps/web
npm run dev
```

Open `http://localhost:5173`, create an account, and add a task with a
deadline. The worker polls every 30 seconds and logs due reminders. The
current sender is deliberately a local logging sender; Telegram and web
push are later delivery adapters.

### What is the access token?

After registration or login, the API returns a bearer access token. It is
a random opaque value generated with Python's `secrets` module. Only its
SHA-256 hash is stored in the database, together with the user ID and an
expiry time. The browser stores the raw token in local storage and sends it
as `Authorization: Bearer <token>` on authenticated requests. The token is
not a third-party API key and should never be committed or shared.

You normally do not need to copy it manually: the web app now obtains it
through `/auth/register` or `/auth/login`. For API testing, use the
Authorize control in `/docs` and enter `Bearer <token>`.
