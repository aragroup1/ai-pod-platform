#!/bin/bash
set -e

echo "--- [Pod Platform] Startup Script Initializing ---"

if [ -n "$DATABASE_URL" ]; then
  echo "--- [Pod Platform] Database URL found. Checking database state... ---"
  
  TABLE_EXISTS=$(psql $DATABASE_URL -tAc "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'trends');" 2>/dev/null || echo "f")
  
  if [ "$TABLE_EXISTS" = "f" ]; then
    echo "--- [Pod Platform] Database not initialized. Setting up schema... ---"
    psql $DATABASE_URL -f scripts/init_db.sql -q 2>&1 || echo "--- [Pod Platform] Schema initialization completed ---"
    echo "--- [Pod Platform] Database initialized successfully! ---"
  else
    echo "--- [Pod Platform] Database already initialized. Skipping schema setup. ---"
  fi
  
else
  echo "--- [Pod Platform] No DATABASE_URL found. Running without database. ---"
fi

echo "--- [Pod Platform] Starting Uvicorn web server... ---"
# CRITICAL: Use Railway's PORT variable
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080} --log-level info
```
