-- Add a search vector column to papers
ALTER TABLE papers ADD COLUMN search_vector tsvector;

-- Create index for fast search
CREATE INDEX idx_papers_search ON papers USING GIN(search_vector);

-- Update existing papers
UPDATE papers SET search_vector = 
  to_tsvector('english', 
    COALESCE(title, '') || ' ' || 
    COALESCE(abstract, '') || ' ' || 
    COALESCE(array_to_string(authors, ' '), '')
  );

-- Auto-update on insert/update via trigger
CREATE OR REPLACE FUNCTION update_search_vector()
RETURNS TRIGGER AS $$
BEGIN
  NEW.search_vector = to_tsvector('english',
    COALESCE(NEW.title, '') || ' ' ||
    COALESCE(NEW.abstract, '') || ' ' ||
    COALESCE(array_to_string(NEW.authors, ' '), '')
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER papers_search_vector_update
  BEFORE INSERT OR UPDATE ON papers
  FOR EACH ROW EXECUTE FUNCTION update_search_vector();