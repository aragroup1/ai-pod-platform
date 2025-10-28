-- scripts/add_feedback_table.sql
-- Add product feedback table for learning user preferences

CREATE TABLE IF NOT EXISTS product_feedback (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    action VARCHAR(20) NOT NULL CHECK (action IN ('approve', 'reject')),
    reason TEXT,
    style VARCHAR(100),
    provider VARCHAR(50),
    keyword VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_feedback_product_id ON product_feedback(product_id);
CREATE INDEX IF NOT EXISTS idx_feedback_action ON product_feedback(action);
CREATE INDEX IF NOT EXISTS idx_feedback_style ON product_feedback(style);
CREATE INDEX IF NOT EXISTS idx_feedback_created_at ON product_feedback(created_at);

-- Add updated_at to products table if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'products' AND column_name = 'updated_at'
    ) THEN
        ALTER TABLE products ADD COLUMN updated_at TIMESTAMP DEFAULT NOW();
    END IF;
END $$;

-- Update products enum to include 'rejected' status
DO $$
BEGIN
    ALTER TYPE product_status ADD VALUE IF NOT EXISTS 'rejected';
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

COMMENT ON TABLE product_feedback IS 'Stores user feedback on products to learn preferences';
COMMENT ON COLUMN product_feedback.action IS 'Either approve or reject';
COMMENT ON COLUMN product_feedback.style IS 'Art style for pattern analysis';
COMMENT ON COLUMN product_feedback.provider IS 'AI provider for quality analysis';
