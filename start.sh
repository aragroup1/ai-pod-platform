#!/bin/bash
set -e

echo "--- [Pod Platform] Startup Script Initializing ---"

if [ -n "$DATABASE_URL" ]; then
  echo "--- [Pod Platform] Database URL found. Checking database state... ---"
  
  # Check if the 'trends' table exists (as a proxy for schema being initialized)
  TABLE_EXISTS=$(psql $DATABASE_URL -tAc "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'trends');" 2>/dev/null || echo "f")
  
  if [ "$TABLE_EXISTS" = "f" ]; then
    echo "--- [Pod Platform] Database not initialized. Setting up schema... ---"
    
    # Only reset and init if tables don't exist (first deployment or after database reset)
    if [ "$FORCE_RESET" = "true" ]; then
      echo "--- [Pod Platform] FORCE_RESET=true. Dropping and recreating schema... ---"
      psql $DATABASE_URL -f scripts/reset_schema.sql -q 2>&1 || echo "--- [Pod Platform] Schema reset completed ---"
    fi
    
    # Initialize the database schema
    psql $DATABASE_URL -f scripts/init_db.sql -q 2>&1 || echo "--- [Pod Platform] Schema initialization completed ---"
    echo "--- [Pod Platform] Database initialized successfully! ---"
  else
    echo "--- [Pod Platform] Database already initialized. Skipping schema setup. ---"
  fi
  
  # Run any pending migrations here in the future
  # alembic upgrade head || echo "--- [Pod Platform] No migrations to run ---"
  
  # Optionally seed sample data (only if SEED_DATA is set to true)
  if [ "$SEED_DATA" = "true" ]; then
    echo "--- [Pod Platform] SEED_DATA=true. Adding sample data... ---"
    psql $DATABASE_URL -f scripts/seed_data.sql -q 2>&1 || echo "--- [Pod Platform] Sample data seeding completed ---"
  fi
  
else
  echo "--- [Pod Platform] No DATABASE_URL found. Running without database. ---"
fi

echo "--- [Pod Platform] Starting Uvicorn web server... ---"
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --log-level info
