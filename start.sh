#!/bin/bash
set -e

echo "--- [Pod Platform] Startup Script Initializing ---"

# Check if DATABASE_URL is set.
if [ -n "$DATABASE_URL" ]; then
  echo "--- [Pod Platform] Database URL found. Initializing schema... ---"
  
  # On first boot or reset, wipe the schema to ensure it's clean.
  # The || true prevents the script from crashing if it's the very first run.
  echo "--- [Pod Platform] Resetting schema completely... ---"
  psql $DATABASE_URL -f scripts/reset_schema.sql -q || true
  
  # Run the main initialization script. This will now run on a clean slate.
  psql $DATABASE_URL -f scripts/init_db.sql -q

  echo "--- [Pod Platform] Schema is ready. ---"
else
  echo "--- [Pod Platform] No DATABASE_URL found. Skipping schema initialization. ---"
fi

echo "--- [Pod Platform] Starting Uvicorn web server... ---"
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --log-level info
