#!/bin/bash
set -e

echo "--- Starting Application ---"

# This command will start the Uvicorn server.
# It uses the PORT variable provided by Railway, defaulting to 8000 for local use.
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --log-level info

echo "--- Application Stopped ---"
