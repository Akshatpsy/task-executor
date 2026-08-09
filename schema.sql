CREATE TABLE tasks (
    id TEXT PRIMARY KEY,
    dependencies TEXT[] NOT NULL DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'pending',
    idempotency_key TEXT NOT NULL,
    start_time TIMESTAMPTZ,
    end_time TIMESTAMPTZ,
    output TEXT,
    error TEXT
);