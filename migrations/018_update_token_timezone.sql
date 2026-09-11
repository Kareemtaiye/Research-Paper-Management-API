  ALTER TABLE password_reset_tokens
ALTER COLUMN expires_at TYPE TIMESTAMPTZ
USING expires_at AT TIME ZONE 'UTC';

ALTER TABLE email_verification_tokens
ALTER COLUMN expires_at TYPE TIMESTAMPTZ
USING expires_at AT TIME ZONE 'UTC';