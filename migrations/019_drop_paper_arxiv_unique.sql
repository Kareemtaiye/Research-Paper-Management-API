ALTER TABLE papers
DROP CONSTRAINT IF EXISTS papers_arxiv_id_key;

ALTER TABLE papers
ADD CONSTRAINT unique_owner_arxiv_id
UNIQUE (owner_id, arxiv_id);