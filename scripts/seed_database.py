#!/usr/bin/env python3
"""
One-time database seeding script
Run this to populate the database with sample data
"""
import asyncio
import asyncpg
import os
from datetime import datetime, timedelta
import random

async def seed_database():
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        print("❌ No DATABASE_URL found!")
        return
    
    print("📦 Connecting to database...")
    conn = await asyncpg.connect(database_url)
    
    try:
        # Check if data already exists
        product_count = await conn.fetchval("SELECT COUNT(*) FROM products")
        
        if product_count > 0:
            print(f"ℹ️ Database already has {product_count} products. Skipping seed.")
            return
        
        print("🌱 Seeding database with sample data...")
        
        # Insert trends
        print("  📈 Adding trends...")
        trend_ids = []
        trends_data = [
            ('vintage posters', 15000, 8.5, 'GB', 'home-decor'),
            ('minimalist art', 12000, 7.8, 'GB', 'wall-art'),
            ('nature photography', 18000, 9.2, 'GB', 'photography'),
            ('abstract canvas', 9500, 6.5, 'GB', 'wall-art'),
            ('motivational quotes', 22000, 8.9, 'GB', 'typography')
        ]
        
        for keyword, volume, score, geo, category in trends_data:
            trend_id = await conn.fetchval("""
                INSERT INTO trends (keyword, search_volume, trend_score, geography, category)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id
            """, keyword, volume, score, geo, category)
            trend_ids.append(trend_id)
        
        # Insert products
        print("  🎨 Adding products...")
        products_data = [
            ('POD-2024-001', 'Vintage London Travel Poster', 'Beautiful vintage-style travel poster', 29.99, 'posters', ['vintage', 'travel', 'london'], 'active'),
            ('POD-2024-002', 'Minimalist Mountain Canvas', 'Modern minimalist mountain landscape', 39.99, 'canvas', ['minimalist', 'nature', 'mountains'], 'active'),
            ('POD-2024-003', 'Abstract Geometric Art Print', 'Contemporary abstract geometric design', 24.99, 'prints', ['abstract', 'geometric', 'modern'], 'active'),
            ('POD-2024-004', 'Motivational Quote Poster', 'Inspiring motivational quote typography', 19.99, 'posters', ['motivation', 'quotes', 'typography'], 'active'),
            ('POD-2024-005', 'Sunset Beach Photography', 'Stunning sunset beach photography', 49.99, 'canvas', ['photography', 'beach', 'sunset'], 'active'),
            ('POD-2024-006', 'Botanical Illustration Set', 'Set of 3 botanical illustrations', 34.99, 'prints', ['botanical', 'nature', 'illustration'], 'active'),
            ('POD-2024-007', 'City Skyline Silhouette', 'Modern city skyline silhouette', 27.99, 'prints', ['city', 'urban', 'silhouette'], 'active'),
            ('POD-2024-008', 'Watercolor Landscape Print', 'Beautiful watercolor landscape', 32.99, 'prints', ['watercolor', 'landscape', 'art'], 'active')
        ]
        
        product_ids = []
        for sku, title, desc, price, category, tags, status in products_data:
            product_id = await conn.fetchval("""
                INSERT INTO products (sku, title, description, base_price, category, tags, status)
                VALUES ($1, $2, $3, $4, $5, $6, $7::product_status)
                ON CONFLICT (sku) DO UPDATE SET title = EXCLUDED.title
                RETURNING id
            """, sku, title, desc, price, category, tags, status)
            product_ids.append(product_id)
        
        # Insert orders for the last 30 days
        print("  📦 Adding orders...")
        platforms = ['shopify', 'amazon', 'etsy']
        providers = ['printful', 'printify']
        statuses = ['pending', 'processing', 'fulfilled', 'shipped', 'delivered']
        
        for i in range(50):  # Create 50 sample orders
            days_ago = random.randint(0, 29)
            order_date = datetime.now() - timedelta(days=days_ago)
            product_id = random.choice(product_ids)
            platform = random.choice(platforms)
            provider = random.choice(providers)
            status = random.choice(statuses)
            order_value = round(19.99 + random.random() * 30, 2)
            profit = round(order_value * 0.3, 2)  # 30% profit margin
            
            await conn.execute("""
                INSERT INTO orders (
                    platform_order_id, platform, product_id, 
                    customer_data, order_value, profit,
                    fulfillment_provider, fulfillment_status, 
                    status, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """, 
                f"ORD-{platform.upper()}-{1000+i}",
                platform,
                product_id,
                '{"name": "Sample Customer"}',
                order_value,
                profit,
                provider,
                'pending' if status in ['pending', 'processing'] else 'fulfilled',
                status,
                order_date
            )
        
        # Insert some analytics data
        print("  📊 Adding analytics data...")
        for product_id in product_ids[:5]:  # Add analytics for first 5 products
            for days_ago in range(30):
                date = datetime.now().date() - timedelta(days=days_ago)
                views = random.randint(10, 200)
                clicks = random.randint(1, 50)
                orders = random.randint(0, 5)
                revenue = orders * 29.99
                profit = revenue * 0.3
                
                await conn.execute("""
                    INSERT INTO analytics_daily (
                        date, platform, product_id, views, clicks, 
                        orders, revenue, profit
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    ON CONFLICT (date, platform, product_id) DO NOTHING
                """, date, 'shopify', product_id, views, clicks, orders, revenue, profit)
        
        # Verify the results
        product_count = await conn.fetchval("SELECT COUNT(*) FROM products")
        order_count = await conn.fetchval("SELECT COUNT(*) FROM orders")
        trend_count = await conn.fetchval("SELECT COUNT(*) FROM trends")
        
        print(f"""
✅ Database seeded successfully!
   - Products: {product_count}
   - Orders: {order_count}
   - Trends: {trend_count}
        """)
        
    except Exception as e:
        print(f"❌ Error seeding database: {e}")
    finally:
        await conn.close()
        print("🔒 Database connection closed")

if __name__ == "__main__":
    asyncio.run(seed_database())
