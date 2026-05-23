ALTER TABLE papers
ADD COLUMN arxiv_url TEXT,
ADD COLUMN arxiv_id VARCHAR(50) UNIQUE,
ADD COLUMN authors TEXT[],
ADD COLUMN abstract TEXT,
ADD COLUMN published_at TIMESTAMP,
ADD COLUMN categories TEXT[],     -- arxiv categories e.g. cs.LG
ADD COLUMN status VARCHAR(20) DEFAULT 'pending',
ADD COLUMN task_id VARCHAR(255);  -- celery task ID for tracking