CREATE UNIQUE INDEX IF NOT EXISTS ix_sessions_token_hash 
        ON sessions (token_hash)