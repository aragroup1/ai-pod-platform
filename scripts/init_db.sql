-- Resilient and Complete Database Initialization Script

-- Step 1: Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Step 2: Create custom ENUM types
CREATE TYPE product_status AS ENUM ('draft', 'pending_approval', 'approved', 'active', 'paused', 'archived');
CREATE TYPE order_status AS ENUM ('pending', 'processing', 'fulfilled', 'shipped', 'delivered', 'cancelled', 'refunded');
CREATE TYPE platform_type AS ENUM ('shopify', 'amazon', 'etsy', 'ebay', 'tiktok');
CREATE TYPE fulfillment_provider AS ENUM ('printful', 'printify', 'gooten', 'customcat', 'gelato');

-- Step 3: Create tables
CREATE TABLE trends (
    id SERIAL PRIMARY KEY,
    keyword VARCHAR(255) NOT NULL,
    search_volume INTEGER DEFAULT 0,
    trend_score FLOAT DEFAULT 0.0,
    geography VARCHAR(10) DEFAULT 'GB',
    category VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW(),
    data JSONB
);

CREATE TABLE artwork (
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

CREATE TABLE products (
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

CREATE TABLE platform_listings (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id),
    platform platform_type,
    platform_product_id VARCHAR(255),
    platform_url VARCHAR(500),
    status VARCHAR(50),
    listed_at TIMESTAMP DEFAULT NOW(),
    performance_data JSONB
);

CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    platform_order_id VARCHAR(255),
    platform platform_type,
    product_id INTEGER REFERENCES products(id),
    customer_data JSONB,
    order_value DECIMAL(10,2),
    profit DECIMAL(10,2),  -- <-- THIS COLUMN WAS MISSING
    fulfillment_provider fulfillment_provider,
    fulfillment_status VARCHAR(50),
    tracking_number VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    status order_status DEFAULT 'pending'
);

CREATE TABLE analytics_daily (
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

CREATE TABLE pod_providers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE,
    is_active BOOLEAN DEFAULT true, -- <-- THIS COLUMN WAS MISSING
    priority INTEGER,
    capabilities JSONB
);

-- Step 4: Initial seed data
INSERT INTO pod_providers (name, is_active, priority, capabilities) VALUES
('printful', true, 1, '{"regions": ["US", "EU", "UK"], "products": ["canvas", "poster", "t-shirt"]}'),
('printify', true, 2, '{"regions": ["US", "EU"], "products": ["canvas", "poster", "mug"]}'),
('gooten', true, 3, '{"regions": ["US"], "products": ["canvas", "poster"]}');
