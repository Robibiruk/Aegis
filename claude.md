# Aegis Build Record

## Product direction

Aegis is a personal follow-through and opportunity intelligence platform.
The product source of truth is the supplied Aegis architecture
specification. The reliability rule is: make the core reliable, make
discovery evidence-based, make AI accountable, and make follow-through
humane.

## Completed Phase 0: repository foundation

Status: complete and verified.

- Audited the initially empty workspace.
- Initialized Git.
- Added Python project metadata and environment examples.
- Added FastAPI, SQLAlchemy, Pydantic Settings, and test dependencies.
- Added SQLite local development support with PostgreSQL-compatible
  SQLAlchemy models.
- Added the initial PostgreSQL schema migration.
- Added Docker Compose PostgreSQL infrastructure.
- Added project README and ignore rules.

## Completed Phase 1: dependable task/reminder core

Status: complete and verified.

- Added persisted users and bearer sessions.
- Added PBKDF2 password hashing.
- Added user-owned task CRUD.
- Enforced timezone-aware deadlines.
- Added durable reminders and delivery-attempt records.
- Added idempotency keys and duplicate-delivery protection.
- Re-checks task state immediately before reminder delivery.
- Cancels stale reminders after completion, cancellation, or rescheduling.
- Added bounded local reminder worker polling.
- Added a React/Vite PWA surface for registration, login, task capture,
  task listing, and sign-out.
- Added tests for authentication, ownership, validation, reminder
  cancellation, delivery, and idempotency.

Verification:

```text
pytest                         4 passed
cd apps/web && npm run build   successful
python3 -m compileall apps tests successful
```

## Current architecture

```text
apps/api       FastAPI modular monolith and domain services
apps/web       React + TypeScript + Vite PWA
apps/worker.py Durable reminder polling entrypoint
migrations/    PostgreSQL schema migration
tests/         API and reminder unit/integration coverage
docker-compose PostgreSQL local infrastructure
```

The local default database is SQLite. PostgreSQL is selected through
`AEGIS_DATABASE_URL`. The core reminder sender currently logs deliveries;
real Telegram and push adapters are intentionally not faked.

## Token lifecycle

1. The user registers or logs in through the web UI.
2. The API generates a random opaque token with `secrets.token_urlsafe`.
3. Only a SHA-256 token hash is persisted in `sessions`.
4. The raw token is returned once in the authentication response.
5. Authenticated requests send `Authorization: Bearer <token>`.
6. The API checks the hash, user, and expiry on every request.
7. The browser keeps the token in local storage until sign-out or expiry.

This is suitable for the local foundation. Before production, move to
secure, HttpOnly cookie sessions or a carefully reviewed token strategy,
add revocation/logout endpoints, rate limiting, CSRF protection for
cookie auth, and secret rotation.

## Next phase roadmap

### Phase 2: Inbox and opportunity capture

Implemented slice:

- Added user-owned manual URL capture.
- Canonicalized HTTP(S) URLs and removed fragments.
- Deduplicated captured sources per user.
- Added an `unreviewed` source state.
- Added API tests for attribution and deduplication.

The remaining Phase 2 work is RSS/Atom ingestion, review actions, source
allowlists, content hashing, and evidence-preserving extraction.

1. Add source records and a review queue.
2. Add manual URL capture with canonicalization and attribution.
3. Add deterministic source metadata and review states.
4. Add safe RSS/Atom ingestion behind an allowlist.
5. Add deduplication by provider ID, canonical URL, and content hash.
6. Add user approval before creating tasks or opportunities.

Exit gate: imported content is stored as untrusted source data, traceable
to its origin, deduplicated, and never silently becomes a confirmed task.

### Phase 3: opportunity planning and evidence-backed AI

1. Add normalized opportunity records.
2. Add eligibility profile and deterministic matching rules.
3. Add requirements and document readiness checklists.
4. Add evidence spans and validated structured extraction adapters.
5. Add application plan generation with user approval.

Exit gate: an opportunity has an evidence-backed deadline and explicit
eligibility state before it becomes an approved plan.

### Phase 4: external context

1. Add user-forwarded email ingestion.
2. Add narrow-scope Google Calendar read access.
3. Add deduplication and disconnect behavior.
4. Add context-aware weekly review.

### Phase 5: recovery and intelligence

1. Add Recovery Mode and a Follow-up Queue.
2. Add friction detection and study-session workflows.
3. Add optional spaced repetition only after dependency validation.
4. Improve Amharic localization and offline PWA behavior.

### Phase 6: scale and advanced integrations

Evaluate, do not assume: Temporal, Outlook, browser extension, more
source adapters, optional SMS, advanced document parsing, additional
languages, and native mobile only if PWA limitations justify it.

## Immediate next steps

- Add a real migration runner instead of startup `create_all`.
- Add reminder retry scheduling with exponential backoff and permanent
  failure states.
- Add logout/session revocation and password reset flow.
- Add user timezone and quiet-hours preferences.
- Add task completion controls in the web UI.
- Replace the logging sender with an adapter interface for Telegram and
  web push.
- Add PostgreSQL integration tests and worker restart tests.
- Add structured observability and health checks.

## Deliberate non-goals

Do not add autonomous application submission, unrestricted scraping,
unapproved external writes, SMS, broad Gmail synchronization, or
AI-dependent task reminders before the core reliability gates pass.
