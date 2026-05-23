#!/bin/bash
# scripts/migrate.sh

# Runs only unapplied migrations:
for file in /migrations/*.sql; do
    filename=$(basename "$file")
    
    # Check if already applied
    applied=$(psql $DATABASE_URL -tAc \
        "SELECT filename FROM schema_migrations WHERE filename='$filename'")
    
    if [ -z "$applied" ]; then
        echo "Running migration: $filename"
        psql $DATABASE_URL -f "$file"
        psql $DATABASE_URL -c \
            "INSERT INTO schema_migrations (filename) VALUES ('$filename')"
        echo "Done: $filename"
    else
        echo "Skipping: $filename (already applied)"
    fi
done