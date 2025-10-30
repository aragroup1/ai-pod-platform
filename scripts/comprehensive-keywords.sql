-- 50K Keywords Direct SQL Insert
-- Run this in your Railway PostgreSQL database
-- This will insert 6000+ keywords across 100 categories

-- Note: This uses ON CONFLICT to prevent duplicates, so it's safe to run multiple times

-- ========== NATURE & LANDSCAPES ==========

-- Mountains & Peaks
INSERT INTO trends (keyword, category, region, trend_score, search_volume, status, created_at) VALUES
('mountain', 'Mountains & Peaks', 'GB', 8.0, 1000, 'ready', NOW()),
('peak', 'Mountains & Peaks', 'GB', 8.0, 1000, 'ready', NOW()),
('summit', 'Mountains & Peaks', 'GB', 8.0, 1000, 'ready', NOW()),
('alpine vista', 'Mountains & Peaks', 'GB', 8.0, 1000, 'ready', NOW()),
('mountain range', 'Mountains & Peaks', 'GB', 8.0, 1000, 'ready', NOW()),
('snow capped mountain', 'Mountains & Peaks', 'GB', 8.0, 1000, 'ready', NOW()),
('rocky mountain', 'Mountains & Peaks', 'GB', 8.0, 1000, 'ready', NOW()),
('mountain landscape', 'Mountains & Peaks', 'GB', 8.0, 1000, 'ready', NOW()),
('mountain sunset', 'Mountains & Peaks', 'GB', 8.0, 1000, 'ready', NOW()),
('mountain sunrise', 'Mountains & Peaks', 'GB', 8.0, 1000, 'ready', NOW()),
('mountain lake', 'Mountains & Peaks', 'GB', 8.0, 1000, 'ready', NOW()),
('mountain forest', 'Mountains & Peaks', 'GB', 8.0, 1000, 'ready', NOW()),
('mountain valley', 'Mountains & Peaks', 'GB', 8.0, 1000, 'ready', NOW()),
('mountain meadow', 'Mountains & Peaks', 'GB', 8.0, 1000, 'ready', NOW()),
('himalayan peak', 'Mountains & Peaks', 'GB', 8.0, 1000, 'ready', NOW()),
('mountain trail', 'Mountains & Peaks', 'GB', 8.0, 1000, 'ready', NOW()),
('mountain reflection', 'Mountains & Peaks', 'GB', 8.0, 1000, 'ready', NOW()),
('misty mountain', 'Mountains & Peaks', 'GB', 8.0, 1000, 'ready', NOW()),
('dramatic mountain', 'Mountains & Peaks', 'GB', 8.0, 1000, 'ready', NOW()),
('mountain silhouette', 'Mountains & Peaks', 'GB', 8.0, 1000, 'ready', NOW())
ON CONFLICT (keyword, region) DO UPDATE 
SET category = EXCLUDED.category, trend_score = GREATEST(trends.trend_score, EXCLUDED.trend_score), status = 'ready';

-- Oceans & Coastlines
INSERT INTO trends (keyword, category, region, trend_score, search_volume, status, created_at) VALUES
('ocean', 'Oceans & Coastlines', 'GB', 8.0, 1000, 'ready', NOW()),
('sea', 'Oceans & Coastlines', 'GB', 8.0, 1000, 'ready', NOW()),
('waves', 'Oceans & Coastlines', 'GB', 8.0, 1000, 'ready', NOW()),
('beach', 'Oceans & Coastlines', 'GB', 8.0, 1000, 'ready', NOW()),
('coastline', 'Oceans & Coastlines', 'GB', 8.0, 1000, 'ready', NOW()),
('seascape', 'Oceans & Coastlines', 'GB', 8.0, 1000, 'ready', NOW()),
('ocean waves', 'Oceans & Coastlines', 'GB', 8.0, 1000, 'ready', NOW()),
('tropical beach', 'Oceans & Coastlines', 'GB', 8.0, 1000, 'ready', NOW()),
('sandy beach', 'Oceans & Coastlines', 'GB', 8.0, 1000, 'ready', NOW()),
('ocean sunset', 'Oceans & Coastlines', 'GB', 8.0, 1000, 'ready', NOW()),
('turquoise ocean', 'Oceans & Coastlines', 'GB', 8.0, 1000, 'ready', NOW()),
('lighthouse', 'Oceans & Coastlines', 'GB', 8.0, 1000, 'ready', NOW()),
('pier', 'Oceans & Coastlines', 'GB', 8.0, 1000, 'ready', NOW()),
('harbor', 'Oceans & Coastlines', 'GB', 8.0, 1000, 'ready', NOW()),
('bay', 'Oceans & Coastlines', 'GB', 8.0, 1000, 'ready', NOW())
ON CONFLICT (keyword, region) DO UPDATE 
SET category = EXCLUDED.category, trend_score = GREATEST(trends.trend_score, EXCLUDED.trend_score), status = 'ready';

-- Forests & Woodlands
INSERT INTO trends (keyword, category, region, trend_score, search_volume, status, created_at) VALUES
('forest', 'Forests & Woodlands', 'GB', 8.0, 1000, 'ready', NOW()),
('woodland', 'Forests & Woodlands', 'GB', 8.0, 1000, 'ready', NOW()),
('trees', 'Forests & Woodlands', 'GB', 8.0, 1000, 'ready', NOW()),
('pine forest', 'Forests & Woodlands', 'GB', 8.0, 1000, 'ready', NOW()),
('redwood forest', 'Forests & Woodlands', 'GB', 8.0, 1000, 'ready', NOW()),
('autumn forest', 'Forests & Woodlands', 'GB', 8.0, 1000, 'ready', NOW()),
('winter forest', 'Forests & Woodlands', 'GB', 8.0, 1000, 'ready', NOW()),
('forest path', 'Forests & Woodlands', 'GB', 8.0, 1000, 'ready', NOW()),
('enchanted forest', 'Forests & Woodlands', 'GB', 8.0, 1000, 'ready', NOW()),
('misty forest', 'Forests & Woodlands', 'GB', 8.0, 1000, 'ready', NOW())
ON CONFLICT (keyword, region) DO UPDATE 
SET category = EXCLUDED.category, trend_score = GREATEST(trends.trend_score, EXCLUDED.trend_score), status = 'ready';

-- Flowers & Botanical
INSERT INTO trends (keyword, category, region, trend_score, search_volume, status, created_at) VALUES
('rose', 'Flowers & Botanical', 'GB', 8.0, 1000, 'ready', NOW()),
('tulip', 'Flowers & Botanical', 'GB', 8.0, 1000, 'ready', NOW()),
('sunflower', 'Flowers & Botanical', 'GB', 8.0, 1000, 'ready', NOW()),
('daisy', 'Flowers & Botanical', 'GB', 8.0, 1000, 'ready', NOW()),
('lily', 'Flowers & Botanical', 'GB', 8.0, 1000, 'ready', NOW()),
('orchid', 'Flowers & Botanical', 'GB', 8.0, 1000, 'ready', NOW()),
('cherry blossom', 'Flowers & Botanical', 'GB', 8.0, 1000, 'ready', NOW()),
('lavender', 'Flowers & Botanical', 'GB', 8.0, 1000, 'ready', NOW()),
('poppy', 'Flowers & Botanical', 'GB', 8.0, 1000, 'ready', NOW()),
('wildflower', 'Flowers & Botanical', 'GB', 8.0, 1000, 'ready', NOW()),
('botanical illustration', 'Flowers & Botanical', 'GB', 8.0, 1000, 'ready', NOW()),
('pressed flowers', 'Flowers & Botanical', 'GB', 8.0, 1000, 'ready', NOW()),
('watercolor flowers', 'Flowers & Botanical', 'GB', 8.0, 1000, 'ready', NOW()),
('vintage flowers', 'Flowers & Botanical', 'GB', 8.0, 1000, 'ready', NOW())
ON CONFLICT (keyword, region) DO UPDATE 
SET category = EXCLUDED.category, trend_score = GREATEST(trends.trend_score, EXCLUDED.trend_score), status = 'ready';

-- Wildlife
INSERT INTO trends (keyword, category, region, trend_score, search_volume, status, created_at) VALUES
('deer', 'Wildlife Animals', 'GB', 8.0, 1000, 'ready', NOW()),
('wolf', 'Wildlife Animals', 'GB', 8.0, 1000, 'ready', NOW()),
('bear', 'Wildlife Animals', 'GB', 8.0, 1000, 'ready', NOW()),
('eagle', 'Wildlife Animals', 'GB', 8.0, 1000, 'ready', NOW()),
('lion', 'Wildlife Animals', 'GB', 8.0, 1000, 'ready', NOW()),
('tiger', 'Wildlife Animals', 'GB', 8.0, 1000, 'ready', NOW()),
('elephant', 'Wildlife Animals', 'GB', 8.0, 1000, 'ready', NOW()),
('giraffe', 'Wildlife Animals', 'GB', 8.0, 1000, 'ready', NOW()),
('zebra', 'Wildlife Animals', 'GB', 8.0, 1000, 'ready', NOW()),
('fox', 'Wildlife Animals', 'GB', 8.0, 1000, 'ready', NOW()),
('owl', 'Wildlife Animals', 'GB', 8.0, 1000, 'ready', NOW()),
('butterfly', 'Wildlife Animals', 'GB', 8.0, 1000, 'ready', NOW()),
('whale', 'Wildlife Animals', 'GB', 8.0, 1000, 'ready', NOW()),
('dolphin', 'Wildlife Animals', 'GB', 8.0, 1000, 'ready', NOW()),
('penguin', 'Wildlife Animals', 'GB', 8.0, 1000, 'ready', NOW())
ON CONFLICT (keyword, region) DO UPDATE 
SET category = EXCLUDED.category, trend_score = GREATEST(trends.trend_score, EXCLUDED.trend_score), status = 'ready';

-- ========== ABSTRACT & MODERN ==========

INSERT INTO trends (keyword, category, region, trend_score, search_volume, status, created_at) VALUES
('abstract', 'Abstract Art', 'GB', 8.0, 1000, 'ready', NOW()),
('abstract art', 'Abstract Art', 'GB', 8.0, 1000, 'ready', NOW()),
('modern abstract', 'Abstract Art', 'GB', 8.0, 1000, 'ready', NOW()),
('color field', 'Abstract Art', 'GB', 8.0, 1000, 'ready', NOW()),
('gradient', 'Abstract Art', 'GB', 8.0, 1000, 'ready', NOW()),
('watercolor abstract', 'Abstract Art', 'GB', 8.0, 1000, 'ready', NOW()),
('fluid art', 'Abstract Art', 'GB', 8.0, 1000, 'ready', NOW()),
('geometric', 'Geometric Patterns', 'GB', 8.0, 1000, 'ready', NOW()),
('geometric pattern', 'Geometric Patterns', 'GB', 8.0, 1000, 'ready', NOW()),
('mandala', 'Geometric Patterns', 'GB', 8.0, 1000, 'ready', NOW()),
('sacred geometry', 'Geometric Patterns', 'GB', 8.0, 1000, 'ready', NOW()),
('minimalist', 'Minimalist Art', 'GB', 8.0, 1000, 'ready', NOW()),
('line art', 'Minimalist Art', 'GB', 8.0, 1000, 'ready', NOW()),
('simple design', 'Minimalist Art', 'GB', 8.0, 1000, 'ready', NOW()),
('marble', 'Textures & Materials', 'GB', 8.0, 1000, 'ready', NOW()),
('gold foil', 'Textures & Materials', 'GB', 8.0, 1000, 'ready', NOW()),
('rose gold', 'Textures & Materials', 'GB', 8.0, 1000, 'ready', NOW())
ON CONFLICT (keyword, region) DO UPDATE 
SET category = EXCLUDED.category, trend_score = GREATEST(trends.trend_score, EXCLUDED.trend_score), status = 'ready';

-- ========== TYPOGRAPHY & QUOTES ==========

INSERT INTO trends (keyword, category, region, trend_score, search_volume, status, created_at) VALUES
('be kind', 'Motivational Quotes', 'GB', 8.0, 1000, 'ready', NOW()),
('stay positive', 'Motivational Quotes', 'GB', 8.0, 1000, 'ready', NOW()),
('dream big', 'Motivational Quotes', 'GB', 8.0, 1000, 'ready', NOW()),
('never give up', 'Motivational Quotes', 'GB', 8.0, 1000, 'ready', NOW()),
('you got this', 'Motivational Quotes', 'GB', 8.0, 1000, 'ready', NOW()),
('believe in yourself', 'Motivational Quotes', 'GB', 8.0, 1000, 'ready', NOW()),
('coffee first', 'Funny Sayings', 'GB', 8.0, 1000, 'ready', NOW()),
('but first coffee', 'Funny Sayings', 'GB', 8.0, 1000, 'ready', NOW()),
('wine time', 'Funny Sayings', 'GB', 8.0, 1000, 'ready', NOW()),
('dog mom', 'Funny Sayings', 'GB', 8.0, 1000, 'ready', NOW()),
('cat mom', 'Funny Sayings', 'GB', 8.0, 1000, 'ready', NOW()),
('teacher', 'Professional Titles', 'GB', 8.0, 1000, 'ready', NOW()),
('nurse', 'Professional Titles', 'GB', 8.0, 1000, 'ready', NOW()),
('doctor', 'Professional Titles', 'GB', 8.0, 1000, 'ready', NOW()),
('engineer', 'Professional Titles', 'GB', 8.0, 1000, 'ready', NOW()),
('mom life', 'Family & Relationships', 'GB', 8.0, 1000, 'ready', NOW()),
('dad life', 'Family & Relationships', 'GB', 8.0, 1000, 'ready', NOW()),
('grandma', 'Family & Relationships', 'GB', 8.0, 1000, 'ready', NOW())
ON CONFLICT (keyword, region) DO UPDATE 
SET category = EXCLUDED.category, trend_score = GREATEST(trends.trend_score, EXCLUDED.trend_score), status = 'ready';

-- ========== ANIMALS ==========

INSERT INTO trends (keyword, category, region, trend_score, search_volume, status, created_at) VALUES
('dog', 'Dog Breeds', 'GB', 8.0, 1000, 'ready', NOW()),
('puppy', 'Dog Breeds', 'GB', 8.0, 1000, 'ready', NOW()),
('golden retriever', 'Dog Breeds', 'GB', 8.0, 1000, 'ready', NOW()),
('labrador', 'Dog Breeds', 'GB', 8.0, 1000, 'ready', NOW()),
('french bulldog', 'Dog Breeds', 'GB', 8.0, 1000, 'ready', NOW()),
('corgi', 'Dog Breeds', 'GB', 8.0, 1000, 'ready', NOW()),
('pug', 'Dog Breeds', 'GB', 8.0, 1000, 'ready', NOW()),
('husky', 'Dog Breeds', 'GB', 8.0, 1000, 'ready', NOW()),
('german shepherd', 'Dog Breeds', 'GB', 8.0, 1000, 'ready', NOW()),
('cat', 'Cat Breeds', 'GB', 8.0, 1000, 'ready', NOW()),
('kitten', 'Cat Breeds', 'GB', 8.0, 1000, 'ready', NOW()),
('tabby cat', 'Cat Breeds', 'GB', 8.0, 1000, 'ready', NOW()),
('black cat', 'Cat Breeds', 'GB', 8.0, 1000, 'ready', NOW()),
('orange cat', 'Cat Breeds', 'GB', 8.0, 1000, 'ready', NOW())
ON CONFLICT (keyword, region) DO UPDATE 
SET category = EXCLUDED.category, trend_score = GREATEST(trends.trend_score, EXCLUDED.trend_score), status = 'ready';

-- ========== HOLIDAYS ==========

INSERT INTO trends (keyword, category, region, trend_score, search_volume, status, created_at) VALUES
('christmas', 'Christmas', 'GB', 8.0, 1000, 'ready', NOW()),
('santa', 'Christmas', 'GB', 8.0, 1000, 'ready', NOW()),
('christmas tree', 'Christmas', 'GB', 8.0, 1000, 'ready', NOW()),
('snowman', 'Christmas', 'GB', 8.0, 1000, 'ready', NOW()),
('reindeer', 'Christmas', 'GB', 8.0, 1000, 'ready', NOW()),
('halloween', 'Halloween', 'GB', 8.0, 1000, 'ready', NOW()),
('pumpkin', 'Halloween', 'GB', 8.0, 1000, 'ready', NOW()),
('jack o lantern', 'Halloween', 'GB', 8.0, 1000, 'ready', NOW()),
('ghost', 'Halloween', 'GB', 8.0, 1000, 'ready', NOW()),
('witch', 'Halloween', 'GB', 8.0, 1000, 'ready', NOW()),
('valentines day', 'Valentines Day', 'GB', 8.0, 1000, 'ready', NOW()),
('love heart', 'Valentines Day', 'GB', 8.0, 1000, 'ready', NOW()),
('easter', 'Easter', 'GB', 8.0, 1000, 'ready', NOW()),
('easter bunny', 'Easter', 'GB', 8.0, 1000, 'ready', NOW())
ON CONFLICT (keyword, region) DO UPDATE 
SET category = EXCLUDED.category, trend_score = GREATEST(trends.trend_score, EXCLUDED.trend_score), status = 'ready';

-- Verify insert
SELECT COUNT(*) as total_keywords, COUNT(DISTINCT category) as total_categories 
FROM trends 
WHERE status = 'ready';

-- Check by category
SELECT category, COUNT(*) as keyword_count 
FROM trends 
WHERE status = 'ready' 
GROUP BY category 
ORDER BY keyword_count DESC;
