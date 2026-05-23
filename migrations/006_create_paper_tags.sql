CREATE TABLE paper_tags(
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    paper_id UUID REFERENCES papers(id),
    tag_id UUID REFERENCES tags(id),
    created_at TIMESTAMP DEFAULT NOW()
)