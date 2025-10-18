from fastapi import APIRouter, Depends
from typing import Dict, Any
from loguru import logger

from app.database import db_pool
from app.dependencies import get_db_pool
from app.utils.cache import redis_client

router = APIRouter()

@router.get("/status")
async def test_status() -> Dict[str, Any]:
    """
    Test endpoint to verify API is working and check service connections.
    This endpoint doesn't require database connection.
    """
    return {
        "status": "online",
        "message": "API is working",
        "services": {
            "database": db_pool.is_connected,
            "redis": redis_client.is_connected
        }
    }

@router.get("/database")
async def test_database(
    pool = Depends(get_db_pool)
) -> Dict[str, Any]:
    """
    Test database connection and return table counts.
    """
    try:
        # Test basic query
        test_query = await pool.fetchval("SELECT 1")
        
        # Get table counts
        products_count = await pool.fetchval("SELECT COUNT(*) FROM products")
        orders_count = await pool.fetchval("SELECT COUNT(*) FROM orders")
        trends_count = await pool.fetchval("SELECT COUNT(*) FROM trends")
        
        # Get database version
        db_version = await pool.fetchval("SELECT version()")
        
        return {
            "status": "connected",
            "database_version": db_version,
            "tables": {
                "products": products_count,
                "orders": orders_count,
                "trends": trends_count
            }
        }
    except Exception as e:
        logger.error(f"Database test failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "message": "Database connection test failed"
        }

@router.get("/full-diagnostic")
async def full_diagnostic() -> Dict[str, Any]:
    """
    Comprehensive diagnostic endpoint for debugging.
    """
    import os
    
    diagnostics = {
        "api": {
            "status": "online",
            "version": "1.0.0"
        },
        "environment": {
            "environment": os.getenv("ENVIRONMENT", "not_set"),
            "debug": os.getenv("DEBUG", "not_set"),
            "port": os.getenv("PORT", "not_set"),
            "has_database_url": bool(os.getenv("DATABASE_URL")),
            "has_redis_url": bool(os.getenv("REDIS_URL"))
        },
        "services": {
            "database": {
                "connected": db_pool.is_connected
            },
            "redis": {
                "connected": redis_client.is_connected
            }
        }
    }
    
    # Try to get database info if connected
    if db_pool.is_connected:
        try:
            tables_query = """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name
            """
            tables = await db_pool.fetch(tables_query)
            diagnostics["services"]["database"]["tables"] = [row["table_name"] for row in tables]
            
            # Check if tables have data
            for table in ["products", "orders", "trends"]:
                try:
                    count = await db_pool.fetchval(f"SELECT COUNT(*) FROM {table}")
                    diagnostics["services"]["database"][f"{table}_count"] = count
                except:
                    diagnostics["services"]["database"][f"{table}_count"] = "error"
        except Exception as e:
            diagnostics["services"]["database"]["error"] = str(e)
    
    return diagnostics
