-- Complete database initialization script
-- Run this after connecting to Railway PostgreSQL

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
-- pgvector extension (optional, for AI similarity search)
-- Commented out because Railway's default Postgres doesn't include it
-- You can enable it later if needed
-- CREATE EXTENSION IF NOT EXISTS "vector";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Drop existing types if they exist (for clean setup)
DROP TYPE IF EXISTS product_status CASCADE;
DROP TYPE IF EXISTS order_status CASCADE;
DROP TYPE IF EXISTS platform_type CASCADE;
DROP TYPE IF EXISTS fulfillment_provider CASCADE;

-- Create enum types
CREATE TYPE product_status AS ENUM (
    'draft', 'pending_approval', 'approved', 
    'active', 'paused', 'archived'
);

CREATE TYPE order_status AS ENUM (
    'pending', 'processing', 'fulfilled', 
    'shipped', 'delivered', 'cancelled', 'refunded'
);

CREATE TYPE platform_type AS ENUM (
    'shopify', 'amazon', 'etsy', 'ebay', 'tiktok'
);

CREATE TYPE fulfillment_provider AS ENUM (
    'printful', 'printify', 'gooten', 'customcat', 'gelato'
);

-- Trends table
CREATE TABLE IF NOT EXISTS trends (
    id SERIAL PRIMARY KEY,
    keyword VARCHAR(255) NOT NULL,
    search_volume INTEGER DEFAULT 0,
    trend_score FLOAT DEFAULT 0.0,
    competition_level VARCHAR(50),
    geography VARCHAR(10) DEFAULT 'GB',
    category VARCHAR(100),
    source VARCHAR(50),
    data JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_trends_keyword ON trends(keyword);
CREATE INDEX idx_trends_score ON trends(trend_score DESC);
CREATE INDEX idx_trends_created ON trends(created_at DESC);

-- Artwork table
CREATE TABLE IF NOT EXISTS artwork (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE,
    prompt TEXT NOT NULL,
    negative_prompt TEXT,
    provider VARCHAR(50) NOT NULL,
    model_version VARCHAR(100),
    style VARCHAR(100),
    image_url VARCHAR(500),
    thumbnail_url VARCHAR(500),
    cloudflare_url VARCHAR(500),
    generation_cost DECIMAL(10, 6) DEFAULT 0.0,
    generation_time FLOAT,
    quality_score FLOAT DEFAULT 0.0,
    width INTEGER DEFAULT 1024,
    height INTEGER DEFAULT 1024,
    seed INTEGER,
    trend_id INTEGER REFERENCES trends(id) ON DELETE SET NULL,
    metadata JSONB DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'pending',
    approved_at TIMESTAMP,
    approved_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_artwork_status ON artwork(status);
CREATE INDEX idx_artwork_provider ON artwork(provider);
CREATE INDEX idx_artwork_trend ON artwork(trend_id);

-- Products table
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    sku VARCHAR(100) UNIQUE NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    base_price DECIMAL(10, 2) NOT NULL,
    cost DECIMAL(10, 2) DEFAULT 0.0,
    profit_margin FLOAT DEFAULT 0.35,
    artwork_id INTEGER REFERENCES artwork(id) ON DELETE RESTRICT,
    product_type VARCHAR(50),
    category VARCHAR(100),
    subcategory VARCHAR(100),
    tags TEXT[],
    sizes JSONB DEFAULT '{}',
    colors TEXT[],
    materials TEXT[],
    status product_status DEFAULT 'draft',
    seo_title VARCHAR(255),
    seo_description TEXT,
    seo_keywords TEXT[],
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    published_at TIMESTAMP
);

CREATE INDEX idx_products_sku ON products(sku);
CREATE INDEX idx_products_status ON products(status);
CREATE INDEX idx_products_category ON products(category);

-- Platform listings table
CREATE TABLE IF NOT EXISTS platform_listings (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    platform platform_type NOT NULL,
    platform_product_id VARCHAR(255),
    platform_variant_id VARCHAR(255),
    platform_url VARCHAR(500),
    listing_title VARCHAR(255),
    listing_price DECIMAL(10, 2),
    currency VARCHAR(3) DEFAULT 'GBP',
    inventory_quantity INTEGER DEFAULT 999,
    status VARCHAR(50) DEFAULT 'pending',
    error_message TEXT,
    listing_data JSONB DEFAULT '{}',
    performance_data JSONB DEFAULT '{}',
    last_synced_at TIMESTAMP,
    listed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(product_id, platform)
);

CREATE INDEX idx_platform_listings_platform ON platform_listings(platform);
CREATE INDEX idx_platform_listings_status ON platform_listings(status);

-- Orders table
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    order_number VARCHAR(100) UNIQUE NOT NULL,
    platform_order_id VARCHAR(255),
    platform platform_type,
    product_id INTEGER REFERENCES products(id),
    quantity INTEGER DEFAULT 1,
    customer_email VARCHAR(255),
    customer_name VARCHAR(255),
    customer_data JSONB DEFAULT '{}',
    shipping_address JSONB DEFAULT '{}',
    billing_address JSONB DEFAULT '{}',
    order_value DECIMAL(10, 2) NOT NULL,
    cost DECIMAL(10, 2) DEFAULT 0.0,
    profit DECIMAL(10, 2) DEFAULT 0.0,
    currency VARCHAR(3) DEFAULT 'GBP',
    fulfillment_provider fulfillment_provider,
    fulfillment_id VARCHAR(255),
    fulfillment_status VARCHAR(50) DEFAULT 'pending',
    fulfillment_data JSONB DEFAULT '{}',
    tracking_number VARCHAR(255),
    tracking_url VARCHAR(500),
    notes TEXT,
    status order_status DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    fulfilled_at TIMESTAMP,
    shipped_at TIMESTAMP,
    delivered_at TIMESTAMP
);

CREATE INDEX idx_orders_number ON orders(order_number);
CREATE INDEX idx_orders_platform ON orders(platform, platform_order_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_created ON orders(created_at DESC);

-- Product analytics table
CREATE TABLE IF NOT EXISTS product_analytics (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    platform platform_type,
    views INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    add_to_carts INTEGER DEFAULT 0,
    checkouts INTEGER DEFAULT 0,
    orders INTEGER DEFAULT 0,
    revenue DECIMAL(10, 2) DEFAULT 0.0,
    cost DECIMAL(10, 2) DEFAULT 0.0,
    profit DECIMAL(10, 2) DEFAULT 0.0,
    conversion_rate FLOAT DEFAULT 0.0,
    average_order_value DECIMAL(10, 2) DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(date, product_id, platform)
);

CREATE INDEX idx_analytics_date ON product_analytics(date DESC);
CREATE INDEX idx_analytics_product ON product_analytics(product_id);

-- Provider statistics table
CREATE TABLE IF NOT EXISTS provider_statistics (
    provider_name VARCHAR(100) PRIMARY KEY,
    total_requests INTEGER DEFAULT 0,
    total_successes INTEGER DEFAULT 0,
    total_failures INTEGER DEFAULT 0,
    total_cost DECIMAL(10, 4) DEFAULT 0,
    avg_generation_time FLOAT DEFAULT 0,
    last_used TIMESTAMP,
    last_error TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Generation logs table
CREATE TABLE IF NOT EXISTS generation_logs (
    id SERIAL PRIMARY KEY,
    provider VARCHAR(100),
    prompt TEXT,
    negative_prompt TEXT,
    style VARCHAR(100),
    width INTEGER,
    height INTEGER,
    num_images INTEGER,
    success BOOLEAN,
    cost DECIMAL(10, 4),
    generation_time FLOAT,
    error TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_generation_provider ON generation_logs(provider);
CREATE INDEX idx_generation_created ON generation_logs(created_at DESC);

-- Custom providers table (for dashboard)
CREATE TABLE IF NOT EXISTS custom_providers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(200) NOT NULL,
    api_key_encrypted TEXT NOT NULL,
    template VARCHAR(100),
    configuration JSONB NOT NULL,
    enabled BOOLEAN DEFAULT true,
    cost_per_image DECIMAL(10, 6) DEFAULT 0.01,
    priority INTEGER DEFAULT 100,
    total_requests INTEGER DEFAULT 0,
    total_successes INTEGER DEFAULT 0,
    total_failures INTEGER DEFAULT 0,
    total_cost DECIMAL(12, 4) DEFAULT 0,
    avg_generation_time FLOAT DEFAULT 0,
    last_used_at TIMESTAMP,
    last_error TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(100)
);

CREATE INDEX idx_custom_provider_name ON custom_providers(name);
CREATE INDEX idx_custom_provider_enabled ON custom_providers(enabled);

-- POD providers configuration
CREATE TABLE IF NOT EXISTS pod_providers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    api_key VARCHAR(255),
    api_endpoint VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    priority INTEGER DEFAULT 100,
    capabilities JSONB DEFAULT '{}',
    pricing JSONB DEFAULT '{}',
    average_production_time INTEGER,
    average_shipping_time JSONB DEFAULT '{}',
    quality_score FLOAT DEFAULT 0.0,
    reliability_score FLOAT DEFAULT 0.0,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- System settings
CREATE TABLE IF NOT EXISTS system_settings (
    id SERIAL PRIMARY KEY,
    key VARCHAR(100) UNIQUE NOT NULL,
    value JSONB DEFAULT '{}',
    category VARCHAR(50),
    description TEXT,
    is_encrypted BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Update timestamp trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply update trigger to tables
CREATE TRIGGER update_trends_updated_at BEFORE UPDATE ON trends
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_products_updated_at BEFORE UPDATE ON products
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_platform_listings_updated_at BEFORE UPDATE ON platform_listings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_orders_updated_at BEFORE UPDATE ON orders
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_custom_providers_updated_at BEFORE UPDATE ON custom_providers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Initial seed data
INSERT INTO pod_providers (name, is_active, priority, capabilities) VALUES
    ('printful', true, 1, '{"regions": ["US", "EU", "UK"], "products": ["canvas", "poster", "t-shirt"]}'),
    ('printify', true, 2, '{"regions": ["US", "EU"], "products": ["canvas", "poster", "mug"]}'),
    ('gooten', true, 3, '{"regions": ["US"], "products": ["canvas", "poster"]}')
ON CONFLICT (name) DO NOTHING;

-- Grant permissions (adjust user as needed)
GRANT ALL ON ALL TABLES IN SCHEMA public TO current_user;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO current_user;
