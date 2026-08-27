-- add to your tasks table
ALTER TABLE tasks ADD COLUMN completed_at TIMESTAMP;
ALTER TABLE tasks ADD COLUMN worker_name VARCHAR(100);
