-- Raw collector output, one row per signal per source
CREATE TABLE IF NOT EXISTS raw_signals (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    source      TEXT NOT NULL,
    entity_key  TEXT NOT NULL,
    raw_json    TEXT NOT NULL,
    collected_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_signals_entity ON raw_signals(entity_key);
CREATE INDEX IF NOT EXISTS idx_signals_source ON raw_signals(source, collected_at);

-- Deduplicated entity record, one row per startup
CREATE TABLE IF NOT EXISTS companies (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_key   TEXT UNIQUE NOT NULL,
    name         TEXT,
    domain       TEXT,
    founder_names TEXT,
    sources      TEXT,
    first_seen   TEXT NOT NULL,
    updated_at   TEXT NOT NULL
);

-- LLM scoring output
CREATE TABLE IF NOT EXISTS scores (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_key   TEXT NOT NULL,
    score        INTEGER NOT NULL,
    stage_guess  TEXT,
    one_line     TEXT,
    memo         TEXT,
    confidence   TEXT,
    evidence_urls TEXT,
    tokens_used  INTEGER,
    cost_gbp     REAL,
    scored_at    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_scores_entity ON scores(entity_key, scored_at);

-- User feedback from Slack buttons
CREATE TABLE IF NOT EXISTS feedback (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_key   TEXT NOT NULL,
    user_id      TEXT NOT NULL,
    signal       TEXT NOT NULL,
    ts           TEXT NOT NULL
);

-- Precision metrics
CREATE TABLE IF NOT EXISTS metrics (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    week      TEXT NOT NULL,
    precision REAL,
    rated_n   INTEGER,
    ts        TEXT NOT NULL
);
