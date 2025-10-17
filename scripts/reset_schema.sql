-- FORCE RECREATION OF DATABASE SCHEMA
-- This will drop and recreate all tables to ensure proper structure

-- Drop all tables in correct order (respecting foreign keys)
DROP TABLE IF EXISTS analytics_daily CASCADE;
DROP TABLE IF EXISTS platform_listings CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS artwork CASCADE;
DROP TABLE IF EXISTS trends CASCADE;
DROP TABLE IF EXISTS generation_logs CASCADE;
DROP TABLE IF EXISTS provider_statistics CASCADE;
DROP TABLE IF EXISTS custom_providers CASCADE;
DROP TABLE IF EXISTS pod_providers CASCADE;
DROP TABLE IF EXISTS system_settings CASCADE;

-- Drop and recreate ENUM types
DROP TYPE IF EXISTS product_status CASCADE;
DROP TYPE IF EXISTS order_status CASCADE;
DROP TYPE IF EXISTS platform_type CASCADE;
DROP TYPE IF EXISTS fulfillment_provider CASCADE;

CREATE TYPE product_status AS ENUM ('draft', 'pending_approval', 'approved', 'active', 'paused', 'archived');
CREATE TYPE order_status AS ENUM ('pending', 'processing', 'fulfilled', 'shipped', 'delivered', 'cancelled', 'refunded');
CREATE TYPE platform_type AS ENUM ('shopify', 'amazon', 'etsy', 'ebay', 'tiktok');
CREATE TYPE fulfillment_provider AS ENUM ('printful', 'printify', 'gooten', 'customcat', 'gelato');

-- Now run the full schema creation
\i /app/scripts/init_db.sql
