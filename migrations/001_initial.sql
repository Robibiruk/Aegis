CREATE TABLE users (
  id UUID PRIMARY KEY,
  email VARCHAR(320) NOT NULL UNIQUE,
  password_hash VARCHAR(256) NOT NULL,
  timezone VARCHAR(64) NOT NULL DEFAULT 'UTC',
  created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE tasks (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  title VARCHAR(240) NOT NULL,
  notes TEXT,
  due_at TIMESTAMPTZ,
  timezone VARCHAR(64) NOT NULL DEFAULT 'UTC',
  status VARCHAR(20) NOT NULL DEFAULT 'open',
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE reminders (
  id UUID PRIMARY KEY,
  task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
  scheduled_for TIMESTAMPTZ NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'pending',
  idempotency_key VARCHAR(120) NOT NULL UNIQUE,
  attempt_count INTEGER NOT NULL DEFAULT 0,
  last_error TEXT,
  UNIQUE (task_id, scheduled_for)
);

CREATE TABLE delivery_attempts (
  id UUID PRIMARY KEY,
  reminder_id UUID NOT NULL REFERENCES reminders(id) ON DELETE CASCADE,
  idempotency_key VARCHAR(120) NOT NULL UNIQUE,
  attempted_at TIMESTAMPTZ NOT NULL,
  outcome VARCHAR(20) NOT NULL,
  error TEXT
);

CREATE TABLE source_records (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  canonical_url VARCHAR(2048) NOT NULL,
  title VARCHAR(240),
  status VARCHAR(20) NOT NULL DEFAULT 'unreviewed',
  captured_at TIMESTAMPTZ NOT NULL,
  UNIQUE (user_id, canonical_url)
);
