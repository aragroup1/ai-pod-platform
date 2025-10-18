-- Seed data script for development/testing
-- This adds sample data to test the dashboard

-- Clear existing sample data (optional - remove if you want to keep adding)
-- DELETE FROM orders WHERE platform_order_id LIKE 'SAMPLE-%';
-- DELETE FROM products WHERE sku LIKE 'POD-%';
-- DELETE FROM trends WHERE keyword LIKE 'sample-%';

-- Insert sample trends
INSERT INTO trends (keyword, search_volume, trend_score, geography, category, data) VALUES
    ('vintage posters', 15000, 8.5, 'GB', 'home-decor', '{"rising": true, "competition": "medium"}'),
    ('minimalist art', 12000, 7.8, 'GB', 'wall-art', '{"rising": true, "competition": "low"}'),
    ('nature photography', 18000, 9.2, 'GB', 'photography', '{"rising": false, "competition": "high"}'),
    ('abstract canvas', 9500, 6.5, 'GB', 'wall-art', '{"rising": true, "competition": "medium"}'),
    ('motivational quotes', 22000, 8.9, 'GB', 'typography', '{"rising": true, "competition": "low"}')
ON CONFLICT DO NOTHING;

-- Get trend IDs for reference
DO $$
DECLARE
    trend1_id INTEGER;
    trend2_id INTEGER;
BEGIN
    SELECT id INTO trend1_id FROM trends WHERE keyword = 'vintage posters' LIMIT 1;
    SELECT id INTO trend2_id FROM trends WHERE keyword = 'minimalist art' LIMIT 1;
    
    -- Insert sample artwork
    INSERT INTO artwork (prompt, provider, style, image_url, generation_cost, quality_score, trend_id, metadata) VALUES
        ('Vintage travel poster of London', 'leonardo', 'vintage', 'https://example.com/image1.jpg', 0.025, 9.2, trend1_id, '{"model": "leonardo-v2", "steps": 50}'),
        ('Minimalist geometric shapes', 'flux', 'minimalist', 'https://example.com/image2.jpg', 0.003, 8.7, trend2_id, '{"model": "flux-schnell", "steps": 4}')
    ON CONFLICT DO NOTHING;
END $$;

-- Insert sample products
INSERT INTO products (sku, title, description, base_price, category, tags, status) VALUES
    ('POD-20241018-001', 'Vintage London Travel Poster', 'Beautiful vintage-style travel poster featuring iconic London landmarks', 29.99, 'posters', ARRAY['vintage', 'travel', 'london'], 'active'),
    ('POD-20241018-002', 'Minimalist Mountain Canvas', 'Modern minimalist mountain landscape canvas print', 39.99, 'canvas', ARRAY['minimalist', 'nature', 'mountains'], 'active'),
    ('POD-20241018-003', 'Abstract Geometric Art Print', 'Contemporary abstract geometric design perfect for modern homes', 24.99, 'prints', ARRAY['abstract', 'geometric', 'modern'], 'active'),
    ('POD-20241018-004', 'Motivational Quote Poster - Success', 'Inspiring motivational quote typography poster', 19.99, 'posters', ARRAY['motivation', 'quotes', 'typography'], 'active'),
    ('POD-20241018-005', 'Sunset Beach Photography Canvas', 'Stunning sunset beach photography on premium canvas', 49.99, 'canvas', ARRAY['photography', 'beach', 'sunset'], 'active'),
    ('POD-20241018-006', 'Botanical Illustration Set', 'Set of 3 botanical illustration prints', 34.99, 'prints', ARRAY['botanical', 'nature', 'illustration'], 'draft'),
    ('POD-20241018-007', 'City Skyline Silhouette', 'Modern city skyline silhouette artwork', 27.99, 'prints', ARRAY['city', 'urban', 'silhouette'], 'pending_approval'),
    ('POD-20241018-008', 'Watercolor Landscape Print', 'Beautiful watercolor landscape artwork', 32.99, 'prints', ARRAY['watercolor', 'landscape', 'art'], 'active')
ON CONFLICT (sku) DO NOTHING;

-- Get product IDs for orders
DO $$
DECLARE
    product1_id INTEGER;
    product2_id INTEGER;
    product3_id INTEGER;
    product4_id INTEGER;
    product5_id INTEGER;
    current_date TIMESTAMP := NOW();
    i INTEGER;
BEGIN
    SELECT id INTO product1_id FROM products WHERE sku = 'POD-20241018-001' LIMIT 1;
    SELECT id INTO product2_id FROM products WHERE sku = 'POD-20241018-002' LIMIT 1;
    SELECT id INTO product3_id FROM products WHERE sku = 'POD-20241018-003' LIMIT 1;
    SELECT id INTO product4_id FROM products WHERE sku = 'POD-20241018-004' LIMIT 1;
    SELECT id INTO product5_id FROM products WHERE sku = 'POD-20241018-005' LIMIT 1;
    
    -- Insert sample orders with varying dates for the last 30 days
    FOR i IN 0..29 LOOP
        -- Random 1-5 orders per day
        IF random() > 0.3 THEN
            INSERT INTO orders (
                platform_order_id, platform, product_id, customer_data,
                order_value, profit, fulfillment_provider, fulfillment_status,
                status, created_at
            ) VALUES (
                'SAMPLE-SHOP-' || (1000 + i * 10 + floor(random() * 10))::TEXT,
                'shopify',
                CASE floor(random() * 5)::INT
                    WHEN 0 THEN product1_id
                    WHEN 1 THEN product2_id
                    WHEN 2 THEN product3_id
                    WHEN 3 THEN product4_id
                    ELSE product5_id
                END,
                '{"name": "Customer ' || i || '", "email": "customer' || i || '@example.com"}',
                19.99 + (random() * 30)::NUMERIC(10,2),
                5.00 + (random() * 15)::NUMERIC(10,2),
                'printful',
                'fulfilled',
                CASE 
                    WHEN i < 10 THEN 'delivered'
                    WHEN i < 20 THEN 'shipped'
                    ELSE 'processing'
                END,
                current_date - INTERVAL '1 day' * i
            ) ON CONFLICT DO NOTHING;
        END IF;
        
        -- Add some Amazon orders
        IF random() > 0.5 THEN
            INSERT INTO orders (
                platform_order_id, platform, product_id, customer_data,
                order_value, profit, fulfillment_provider, fulfillment_status,
                status, created_at
            ) VALUES (
                'SAMPLE-AMZ-' || (2000 + i * 10 + floor(random() * 10))::TEXT,
                'amazon',
                CASE floor(random() * 5)::INT
                    WHEN 0 THEN product1_id
                    WHEN 1 THEN product2_id
                    WHEN 2 THEN product3_id
                    WHEN 3 THEN product4_id
                    ELSE product5_id
                END,
                '{"name": "Amazon Customer ' || i || '", "email": "amz' || i || '@example.com"}',
                24.99 + (random() * 25)::NUMERIC(10,2),
                6.00 + (random() * 12)::NUMERIC(10,2),
                'printify',
                'pending',
                CASE 
                    WHEN i < 15 THEN 'fulfilled'
                    ELSE 'processing'
                END,
                current_date - INTERVAL '1 day' * i
            ) ON CONFLICT DO NOTHING;
        END IF;
    END LOOP;
END $$;

-- Insert sample analytics data
INSERT INTO analytics_daily (date, platform, product_id, views, clicks, orders, revenue, profit)
SELECT 
    CURRENT_DATE - INTERVAL '1 day' * generate_series(0, 29),
    'shopify',
    p.id,
    floor(random() * 100 + 10)::INT,
    floor(random() * 20 + 1)::INT,
    floor(random() * 5)::INT,
    (random() * 200)::NUMERIC(10,2),
    (random() * 50)::NUMERIC(10,2)
FROM products p
WHERE p.status = 'active'
LIMIT 100
ON CONFLICT DO NOTHING;

-- Verify the data was inserted
DO $$
DECLARE
    product_count INTEGER;
    order_count INTEGER;
    trend_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO product_count FROM products;
    SELECT COUNT(*) INTO order_count FROM orders;
    SELECT COUNT(*) INTO trend_count FROM trends;
    
    RAISE NOTICE 'Data seeding complete!';
    RAISE NOTICE 'Products: %', product_count;
    RAISE NOTICE 'Orders: %', order_count;
    RAISE NOTICE 'Trends: %', trend_count;
END $$;
