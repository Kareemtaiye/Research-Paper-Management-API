ALTER TABLE paper_tags 
DROP CONSTRAINT paper_tags_paper_id_fkey,
ADD CONSTRAINT paper_tags_paper_id_fkey 
    FOREIGN KEY (paper_id) 
    REFERENCES papers(id) 
    ON DELETE SET NULL;
