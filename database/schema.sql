CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    status TEXT NOT NULL,
    current_stage TEXT,
    retry_count INTEGER NOT NULL DEFAULT 0,
    error TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_jobs_status
ON jobs(status);

CREATE INDEX IF NOT EXISTS idx_jobs_current_stage
ON jobs(current_stage);

CREATE TABLE IF NOT EXISTS generated_contents (
    fingerprint TEXT PRIMARY KEY,
    topic TEXT NOT NULL,
    problem TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_generated_contents_problem
ON generated_contents(problem);
