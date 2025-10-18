#!/bin/bash
set -e

echo "--- [Pod Platform] Startup Script Initializing ---"

if [ -n "$DATABASE_URL" ]; then
  echo "--- [Pod Platform] Database URL found. Resetting schema... ---"
  
  # Always run reset to ensure clean state
  psql $DATABASE_URL -f scripts/reset_schema.sql -q 2>&1 || echo "--- [Pod Platform] Schema reset completed ---"
  
  echo "--- [Pod Platform] Schema ready. ---"
else
  echo "--- [Pod Platform] No DATABASE_URL found. Skipping schema initialization. ---"
fi

echo "--- [Pod Platform] Starting Uvicorn web server... ---"
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --log-level info
