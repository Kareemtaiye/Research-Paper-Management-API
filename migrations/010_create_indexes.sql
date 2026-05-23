-- 008_create_indexes.sql
CREATE UNIQUE INDEX IF NOT EXISTS ix_sessions_token_hash 
    ON sessions (token_hash);

CREATE INDEX IF NOT EXISTS ix_task_id
    ON papers (task_id);