-- Resilient Database Initialization Script
-- Safe to run multiple times.

-- Step 1: Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Step 2: Create custom ENUM types if they don't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'product_status') THEN
        CREATE TYPE product_status AS ENUM ('draft', 'pending_approval', 'approved', 'active', 'paused', 'archived');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'order_status') THEN
        CREATE TYPE order_status AS ENUM ('pending', 'processing', 'fulfilled', 'shipped', 'delivered', 'cancelled', 'refunded');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'platform_type') THEN
        CREATE TYPE platform_type AS ENUM ('shopify', 'amazon', 'etsy', 'ebay', 'tiktok');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'fulfillment_provider') THEN
        CREATE TYPE fulfillment_provider AS ENUM ('printful', 'printify', 'gooten', 'customcat', 'gelato');
    END IF;
END$$;

-- Step 3: Create tables using IF NOT EXISTS

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
    status product_status DEFAULT 'draft', -- Uses the ENUM type
    created_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB
);

CREATE TABLE IF NOT EXISTS platform_listings (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id),
    platform platform_type, -- Uses the ENUM type
    platform_product_id VARCHAR(255),
    platform_url VARCHAR(500),
    status VARCHAR(50),
    listed_at TIMESTAMP DEFAULT NOW(),
    performance_data JSONB
);

CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    platform_order_id VARCHAR(255),
    platform platform_type, -- Uses the ENUM type
    product_id INTEGER REFERENCES products(id),
    customer_data JSONB,
    order_value DECIMAL(10,2),
    fulfillment_provider fulfillment_provider, -- Uses the ENUM type
    fulfillment_status VARCHAR(50),
    tracking_number VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    status order_status DEFAULT 'pending' -- Uses the ENUM type
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

-- Add other tables if they don't exist
CREATE TABLE IF NOT EXISTS custom_providers (id SERIAL PRIMARY KEY, name VARCHAR(100) UNIQUE);
CREATE TABLE IF NOT EXISTS generation_logs (id SERIAL PRIMARY KEY, provider VARCHAR(100));
CREATE TABLE IF NOT EXISTS pod_providers (id SERIAL PRIMARY KEY, name VARCHAR(100) UNIQUE);
CREATE TABLE IF NOT EXISTS provider_statistics (provider_name VARCHAR(100) PRIMARY KEY);
CREATE TABLE IF NOT EXISTS system_settings (id SERIAL PRIMARY KEY, key VARCHAR(100) UNIQUE);


-- Step 4: Create indexes using IF NOT EXISTS
CREATE INDEX IF NOT EXISTS idx_products_status ON products(status);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);

-- Note: We are leaving out more complex objects like triggers for now to ensure startup.
-- They can be added back later if needed.

-- Step 5: Initial seed data using ON CONFLICT to be safe
INSERT INTO pod_providers (name, is_active, priority, capabilities) VALUES
    ('printful', true, 1, '{"regions": ["US", "EU", "UK"], "products": ["canvas", "poster", "t-shirt"]}'),
    ('printify', true, 2, '{"regions": ["US", "EU"], "products": ["canvas", "poster", "mug"]}'),
    ('gooten', true, 3, '{"regions": ["US"], "products": ["canvas", "poster"]}')
ON CONFLICT (name) DO NOTHING;
