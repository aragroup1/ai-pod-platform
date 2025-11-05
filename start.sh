#!/bin/bash
# Add this to your existing start.sh file

if [ -n "$DATABASE_URL" ]; then
  echo "--- Running priority system migration ---"
  
  # Run the migration SQL
  psql $DATABASE_URL << 'EOF'
-- Add unique constraint to prevent duplicates
ALTER TABLE trends ADD CONSTRAINT IF NOT EXISTS trends_keyword_unique UNIQUE (keyword);

-- Add design allocation tracking columns
ALTER TABLE trends ADD COLUMN IF NOT EXISTS designs_allocated INTEGER DEFAULT 8;
ALTER TABLE trends ADD COLUMN IF NOT EXISTS designs_generated INTEGER DEFAULT 0;
ALTER TABLE trends ADD COLUMN IF NOT EXISTS priority_tier VARCHAR(20) DEFAULT 'medium';
ALTER TABLE trends ADD COLUMN IF NOT EXISTS last_generated_at TIMESTAMP;

-- Create indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_trends_priority ON trends(search_volume DESC, designs_generated);
CREATE INDEX IF NOT EXISTS idx_trends_status ON trends(status) WHERE status = 'ready';

-- Update existing keywords with default values if they don't have them
UPDATE trends SET designs_allocated = 8 WHERE designs_allocated IS NULL OR designs_allocated = 0;
UPDATE trends SET designs_generated = 0 WHERE designs_generated IS NULL;

-- Show summary
SELECT 'Migration complete!' as status;
EOF

  echo "--- Priority system migration complete ---"
fi

# Then start your app
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}
