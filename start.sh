#!/bin/bash
set -e

echo "--- [Pod Platform] Startup Script Initializing ---"

# Check if DATABASE_URL is set. If not, the psql command will fail, which is okay.
if [ -n "$DATABASE_URL" ]; then
  echo "--- [Pod Platform] Database URL found. Attempting to initialize schema... ---"
  
  # The '-q' flag makes it quiet, and '|| true' ensures that if the script fails
  # (e.g., tables already exist), it doesn't crash the entire container startup.
  psql $DATABASE_URL -f scripts/init_db.sql -q || echo "--- [Pod Platform] psql command finished (may have non-fatal errors if tables exist) ---"
  
  echo "--- [Pod Platform] Schema initialization complete. ---"
else
  echo "--- [Pod Platform] No DATABASE_URL found. Skipping schema initialization. ---"
fi

echo "--- [Pod Platform] Starting Uvicorn web server... ---"

# This command will start the Uvicorn server.
# It uses the PORT variable provided by Railway, defaulting to 8000.
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --log-level info

echo "--- [Pod Platform] Application process exited. ---"
