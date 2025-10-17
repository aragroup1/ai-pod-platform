#!/bin/bash
set -e

echo "--- [Pod Platform] Startup Script Initializing ---"

if [ -n "$DATABASE_URL" ]; then
  echo "--- [Pod Platform] Database URL found. Initializing schema... ---"
  
  # Check if we need to reset (look for a marker file)
  if [ ! -f /tmp/schema_initialized ]; then
    echo "--- [Pod Platform] First run detected. Resetting schema completely... ---"
    psql $DATABASE_URL -f scripts/reset_schema.sql -q || echo "--- [Pod Platform] Schema reset completed ---"
    # Create marker file so we don't reset again
    touch /tmp/schema_initialized
  else
    echo "--- [Pod Platform] Schema already initialized. Running regular init... ---"
    psql $DATABASE_URL -f scripts/init_db.sql -q || echo "--- [Pod Platform] Init completed ---"
  fi
  
  echo "--- [Pod Platform] Schema ready. ---"
else
  echo "--- [Pod Platform] No DATABASE_URL found. Skipping schema initialization. ---"
fi

echo "--- [Pod Platform] Starting Uvicorn web server... ---"
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --log-level info
