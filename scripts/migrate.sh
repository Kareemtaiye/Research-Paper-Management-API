
# Runs only unapplied migrations:
#!/bin/bash

echo "Waiting for PostgreSQL to be ready..."
until psql $DATABASE_URL -c '\q' 2>/dev/null; do
    echo "PostgreSQL not ready yet — retrying in 2 seconds..."
    sleep 2
done
echo "PostgreSQL is ready. Running migrations..."

for file in /migrations/*.sql; do
    filename=$(basename "$file")
    
    applied=$(psql $DATABASE_URL -tAc \
        "SELECT filename FROM schema_migrations WHERE filename='$filename'" 2>/dev/null)
    
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

echo "All migrations complete."