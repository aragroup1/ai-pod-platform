-- Resilient and Complete Database Initialization Script

-- Step 1: Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Step 2: Create custom ENUM types (only if they don't exist)
DO $$ BEGIN
    CREATE TYPE product_status AS ENUM ('draft', 'pending_approval', 'approved', 'active', 'paused', 'archived');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE order_status AS ENUM ('pending', 'processing', 'fulfilled', 'shipped', 'delivered', 'cancelled', 'refunded');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE platform_type AS ENUM ('shopify', 'amazon', 'etsy', 'ebay', 'tiktok');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE fulfillment_provider AS ENUM ('printful', 'printify', 'gooten', 'customcat', 'gelato');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Step 3: Create tables (IF NOT EXISTS for safety)
CREATE TABLE IF NOT EXISTS trends (
    id SERIAL PRIMARY KEY,
    keyword VARCHAR(255) NOT NULL,
    search_volume INTEGER DEFAULT 0,
    trend_score FLOAT DEFAULT 0.0,
    geography VARCHAR(10) DEFAULT 'GB',
    category VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW(),
    data JSONB
);

CREATE TABLE IF NOT EXISTS artwork (
    id SERIAL PRIMARY KEY,
    prompt TEXT,
    provider VARCHAR(50),
    style VARCHAR(100),
    image_url VARCHAR(500),
    generation_cost DECIMAL(10,6),
    quality_score FLOAT,
    trend_id INTEGER REFERENCES trends(id),
    created_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB
);

CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    sku VARCHAR(100) UNIQUE,
    title VARCHAR(255),
    description TEXT,
    base_price DECIMAL(10,2),
    artwork_id INTEGER REFERENCES artwork(id),
    category VARCHAR(100),
    tags TEXT[],
    status product_status DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB
);

CREATE TABLE IF NOT EXISTS platform_listings (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id),
    platform platform_type,
    platform_product_id VARCHAR(255),
    platform_url VARCHAR(500),
    status VARCHAR(50),
    listed_at TIMESTAMP DEFAULT NOW(),
    performance_data JSONB
);

CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    platform_order_id VARCHAR(255),
    platform platform_type,
    product_id INTEGER REFERENCES products(id),
    customer_data JSONB,
    order_value DECIMAL(10,2),
    profit DECIMAL(10,2),
    fulfillment_provider fulfillment_provider,
    fulfillment_status VARCHAR(50),
    tracking_number VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    status order_status DEFAULT 'pending'
);

CREATE TABLE IF NOT EXISTS analytics_daily (
    date DATE,
    platform VARCHAR(50),
    product_id INTEGER,
    views INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    orders INTEGER DEFAULT 0,
    revenue DECIMAL(10,2) DEFAULT 0,
    profit DECIMAL(10,2) DEFAULT 0,
    PRIMARY KEY (date, platform, product_id)
);

CREATE TABLE IF NOT EXISTS pod_providers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE,
    is_active BOOLEAN DEFAULT true,
    priority INTEGER,
    capabilities JSONB
);

-- Step 4: Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_trends_keyword ON trends(keyword);
CREATE INDEX IF NOT EXISTS idx_products_status ON products(status);
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_analytics_date ON analytics_daily(date);

-- Step 5: Insert default POD providers (only if they don't exist)
INSERT INTO pod_providers (name, priority, capabilities) VALUES
    ('printful', 1, '{"regions": ["US", "EU", "UK"], "products": ["canvas", "poster", "t-shirt"]}'),
    ('printify', 2, '{"regions": ["US", "EU"], "products": ["canvas", "poster", "mug"]}'),
    ('gooten', 3, '{"regions": ["US"], "products": ["canvas", "poster"]}')
ON CONFLICT (name) DO NOTHING;

-- Step 6: Insert some sample data for testing (optional)
-- Only insert if tables are empty
INSERT INTO products (sku, title, base_price, status)
SELECT 'SAMPLE-001', 'Sample Canvas Print', 29.99, 'active'
WHERE NOT EXISTS (SELECT 1 FROM products LIMIT 1);

INSERT INTO products (sku, title, base_price, status)
SELECT 'SAMPLE-002', 'Sample T-Shirt Design', 19.99, 'active'
WHERE NOT EXISTS (SELECT 1 FROM products WHERE sku = 'SAMPLE-002');

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'Database schema initialized successfully!';
END $$;
