-- scripts/add_keywords_table.sql
CREATE TABLE IF NOT EXISTS keywords (
    id SERIAL PRIMARY KEY,
    keyword VARCHAR(255) UNIQUE NOT NULL,
    search_volume INTEGER DEFAULT 0,
    category VARCHAR(100),
    designs_allocated INTEGER DEFAULT 0,
    trend_score FLOAT DEFAULT 5.0,
    created_at TIMESTAMP DEFAULT NOW(),
    data JSONB
);

CREATE INDEX IF NOT EXISTS idx_keywords_keyword ON keywords(keyword);
CREATE INDEX IF NOT EXISTS idx_keywords_category ON keywords(category);
