# app/routers/admin_routes.py
# Uses asyncpg pool that matches your database setup

from fastapi import APIRouter, HTTPException, Depends
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# Add to app/routers/admin_routes.py

@router.get("/clean-duplicate-keywords")
async def clean_duplicate_keywords():
    """
    Removes duplicate keywords, keeping the one with highest search volume.
    If volumes are equal, keeps the most recent.
    """
    try:
        from app.database import get_db_pool
        
        pool = await get_db_pool()
        
        # Find duplicates
        duplicates = await pool.fetch("""
            SELECT 
                LOWER(keyword) as normalized_keyword,
                COUNT(*) as count,
                ARRAY_AGG(id ORDER BY 
                    COALESCE(search_volume, 0) DESC, 
                    created_at DESC
                ) as trend_ids
            FROM trends
            GROUP BY LOWER(keyword)
            HAVING COUNT(*) > 1
        """)
        
        if not duplicates:
            return {
                "success": True,
                "duplicates_found": 0,
                "records_deleted": 0,
                "message": "No duplicate keywords found"
            }
        
        deleted_count = 0
        
        for dup in duplicates:
            # Keep first ID (highest volume/most recent), delete the rest
            keep_id = dup['trend_ids'][0]
            delete_ids = dup['trend_ids'][1:]
            
            logger.info(f"Keyword '{dup['normalized_keyword']}': keeping ID {keep_id}, deleting {len(delete_ids)} duplicates")
            
            # Delete duplicate records
            result = await pool.execute("""
                DELETE FROM trends
                WHERE id = ANY($1::int[])
            """, delete_ids)
            
            deleted_count += len(delete_ids)
        
        return {
            "success": True,
            "duplicates_found": len(duplicates),
            "records_deleted": deleted_count,
            "message": f"Cleaned {deleted_count} duplicate keyword entries"
        }
        
    except Exception as e:
        logger.error(f"Error cleaning duplicates: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/keyword-stats")
async def get_keyword_stats():
    """Get statistics about keywords and duplicates"""
    try:
        from app.database import get_db_pool
        
        pool = await get_db_pool()
        
        stats = await pool.fetchrow("""
            SELECT 
                COUNT(*) as total_keywords,
                COUNT(DISTINCT LOWER(keyword)) as unique_keywords,
                COUNT(*) - COUNT(DISTINCT LOWER(keyword)) as duplicates,
                COUNT(*) FILTER (WHERE search_volume IS NOT NULL) as with_volume,
                COUNT(*) FILTER (WHERE search_volume IS NULL) as without_volume,
                MAX(search_volume) as max_volume,
                AVG(search_volume) FILTER (WHERE search_volume IS NOT NULL) as avg_volume
            FROM trends
        """)
        
        # Get top duplicates
        top_dups = await pool.fetch("""
            SELECT 
                LOWER(keyword) as keyword,
                COUNT(*) as duplicate_count,
                MAX(search_volume) as highest_volume
            FROM trends
            GROUP BY LOWER(keyword)
            HAVING COUNT(*) > 1
            ORDER BY COUNT(*) DESC
            LIMIT 10
        """)
        
        return {
            "total_keywords": stats['total_keywords'],
            "unique_keywords": stats['unique_keywords'],
            "duplicate_count": stats['duplicates'],
            "keywords_with_volume": stats['with_volume'],
            "keywords_without_volume": stats['without_volume'],
            "max_search_volume": stats['max_volume'],
            "avg_search_volume": float(stats['avg_volume']) if stats['avg_volume'] else 0,
            "top_duplicates": [
                {
                    "keyword": dup['keyword'],
                    "count": dup['duplicate_count'],
                    "highest_volume": dup['highest_volume']
                }
                for dup in top_dups
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting keyword stats: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# Add to app/routers/admin_routes.py

@router.get("/import-orphaned-images")
async def import_orphaned_images():
    """
    Scans S3 for images not in database and creates artwork/product records for them.
    Focuses on keyword-based folders to recover orphaned images.
    """
    try:
        from app.database import get_db_pool
        from app.utils.s3_storage import get_storage_manager
        import re
        
        pool = await get_db_pool()
        storage = get_storage_manager()
        
        # Get all image keys from S3
        paginator = storage.s3_client.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=storage.bucket_name)
        
        # Get all existing image URLs from database
        existing_urls = set()
        rows = await pool.fetch("SELECT image_url FROM artwork WHERE image_url LIKE '%s3%'")
        for row in rows:
            existing_urls.add(row['image_url'])
        
        orphaned_images = []
        keyword_folders = {}
        
        for page in pages:
            for obj in page.get('Contents', []):
                key = obj['Key']
                
                # Skip non-image files and generated folder (already handled)
                if not key.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                    continue
                if key.startswith('generated/'):
                    continue
                if key.endswith('/'):  # Skip folder markers
                    continue
                
                # Build full URL
                url = f"https://s3.{storage.region}.amazonaws.com/{storage.bucket_name}/{key}"
                
                if url not in existing_urls:
                    # Extract keyword from folder structure
                    # Format: keyword-folder/filename.png
                    match = re.match(r'([^/]+)/(.+)$', key)
                    if match:
                        folder = match.group(1)
                        filename = match.group(2)
                        keyword = folder.replace('-', ' ')
                        
                        orphaned_images.append({
                            'key': key,
                            'url': url,
                            'keyword': keyword,
                            'folder': folder
                        })
                        
                        if folder not in keyword_folders:
                            keyword_folders[folder] = 0
                        keyword_folders[folder] += 1
        
        if not orphaned_images:
            return {
                "success": True,
                "orphaned_count": 0,
                "message": "No orphaned images found"
            }
        
        # Import orphaned images as artwork
        imported_count = 0
        
        for img in orphaned_images:
            try:
                # Check if trend exists for this keyword
                trend_id = await pool.fetchval("""
                    SELECT id FROM trends 
                    WHERE LOWER(keyword) = LOWER($1)
                    LIMIT 1
                """, img['keyword'])
                
                # Create artwork record
                artwork_id = await pool.fetchval("""
                    INSERT INTO artwork (
                        prompt, provider, style, image_url, 
                        generation_cost, quality_score, trend_id, metadata
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8::jsonb)
                    RETURNING id
                """,
                    f"{img['keyword']} wall art",  # prompt
                    'replicate-flux',  # provider
                    'abstract',  # style (default)
                    img['url'],  # image_url
                    0.003,  # generation_cost
                    7.0,  # quality_score
                    trend_id,  # trend_id (may be null)
                    '{"source": "s3_import", "original_folder": "' + img['folder'] + '"}'  # metadata
                )
                
                # Create product for this artwork
                from app.core.products.generator import generate_sku
                
                sku = generate_sku(prefix="POD")
                
                await pool.execute("""
                    INSERT INTO products (
                        sku, title, description, base_price,
                        artwork_id, category, tags, status, image_url
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """,
                    sku,
                    f"{img['keyword'].title()} - Wall Art",
                    f"Premium artwork featuring {img['keyword']}. High-quality print perfect for home or office decor.",
                    44.99,
                    artwork_id,
                    'GB',
                    [img['keyword'], 'imported', 'wall art'],
                    'pending',  # Status pending for review
                    img['url']
                )
                
                imported_count += 1
                
            except Exception as e:
                logger.error(f"Failed to import {img['key']}: {str(e)}")
                continue
        
        return {
            "success": True,
            "orphaned_count": len(orphaned_images),
            "imported_count": imported_count,
            "keyword_folders": keyword_folders,
            "message": f"Imported {imported_count} orphaned images from {len(keyword_folders)} folders"
        }
        
    except Exception as e:
        logger.error(f"Error importing orphaned images: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
        
@router.get("/link-artwork-to-products")
async def link_artwork_to_products():
    """
    Links existing artwork to products by matching:
    1. Created date
    2. Style keywords in product title/tags
    """
    try:
        from app.database import get_db_pool
        
        pool = await get_db_pool()
        
        # Update products with matching artwork
        query = """
            UPDATE products p
            SET 
                artwork_id = a.id,
                image_url = a.image_url
            FROM artwork a
            WHERE 
                p.artwork_id IS NULL
                AND DATE(p.created_at) = DATE(a.created_at)
                AND (
                    p.title ILIKE '%' || a.style || '%'
                    OR a.style = ANY(p.tags)
                )
        """
        
        result = await pool.execute(query)
        
        # Extract row count from result string like "UPDATE 42"
        matched_count = int(result.split()[-1]) if result.startswith('UPDATE') else 0
        
        # Get remaining unmatched
        unmatched = await pool.fetchval("""
            SELECT COUNT(*) 
            FROM products
            WHERE artwork_id IS NULL
        """)
        
        return {
            "success": True,
            "matched_products": matched_count,
            "remaining_unmatched": unmatched,
            "message": f"Linked {matched_count} products to artwork"
        }
        
    except Exception as e:
        logger.error(f"Error linking artwork: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/check-linkage-status")
async def check_linkage_status():
    """Check how many products are linked vs unlinked"""
    try:
        from app.database import get_db_pool
        
        pool = await get_db_pool()
        
        row = await pool.fetchrow("""
            SELECT 
                COUNT(*) FILTER (WHERE artwork_id IS NOT NULL) as linked,
                COUNT(*) FILTER (WHERE artwork_id IS NULL) as unlinked,
                COUNT(*) as total
            FROM products
        """)
        
        return {
            "total_products": row['total'],
            "linked": row['linked'],
            "unlinked": row['unlinked']
        }
        
    except Exception as e:
        logger.error(f"Error checking status: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
