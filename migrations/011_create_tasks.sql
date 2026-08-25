-- migrations/011_create_tasks.sql
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id VARCHAR(255) UNIQUE NOT NULL,   -- Celery task ID
    owner_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    task_type VARCHAR(100) NOT NULL,         -- fetch_paper, send_email, etc
    status VARCHAR(20) DEFAULT 'pending',    -- pending, processing, completed, failed
    progress INTEGER DEFAULT 0,
    stage VARCHAR(50),
    stage_message TEXT,
    result JSONB,                            -- store task result
    error TEXT,                              -- store error if failed
    paper_id UUID REFERENCES papers(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_tasks_owner_id ON tasks(owner_id);
CREATE INDEX idx_tasks_task_id ON tasks(task_id);
CREATE INDEX idx_tasks_status ON tasks(status);