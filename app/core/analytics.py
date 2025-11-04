import asyncio
from typing import List, Dict, Optional
from datetime import datetime, timedelta, date
from decimal import Decimal
from loguru import logger

from app.utils.cache import cache_result

class AnalyticsEngine:
    """Comprehensive business analytics and intelligence"""
    
    def __init__(self, db_pool):
        """Initialize with database pool"""
        self.db_pool = db_pool

    @cache_result(ttl=60)  # Cache dashboard results for 1 minute
    async def get_dashboard_metrics(
        self,
        days: int = 30
    ) -> Dict:
        """Get main dashboard metrics for a given period."""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)

        # We will run all queries in parallel for maximum speed
        revenue_task = self._get_revenue_metrics(start_date, end_date)
        orders_task = self._get_order_count(start_date, end_date)
        products_task = self._get_product_count()
        trends_task = self._get_trend_count(start_date, end_date)
        
        # Await all results
        revenue_data, order_count, product_count, trend_count = await asyncio.gather(
            revenue_task,
            orders_task,
            products_task,
            trends_task
        )
        
        return {
            "revenue": revenue_data.get("total_revenue", 0),
            "orders": order_count,
            "products": product_count,
            "trends": trend_count,
            "profit": revenue_data.get("total_profit", 0),
            "avg_order_value": revenue_data.get("avg_order_value", 0)
        }

    async def _get_revenue_metrics(
        self,
        start_date: date,
        end_date: date
    ) -> Dict:
        """Helper to get revenue and profit."""
        query = """
            SELECT 
                COALESCE(SUM(order_value), 0) as total_revenue,
                COALESCE(SUM(profit), 0) as total_profit,
                COALESCE(AVG(order_value), 0) as avg_order_value
            FROM orders
            WHERE 
                created_at >= $1 
                AND created_at <= $2
                AND status NOT IN ('cancelled', 'refunded')
        """
        try:
            result = await self.db_pool.fetchrow(query, start_date, end_date + timedelta(days=1))
            
            return {
                "total_revenue": float(result['total_revenue']) if result else 0,
                "total_profit": float(result['total_profit']) if result else 0,
                "avg_order_value": float(result['avg_order_value']) if result else 0
            }
        except Exception as e:
            logger.error(f"Error fetching revenue metrics: {e}")
            return {
                "total_revenue": 0,
                "total_profit": 0,
                "avg_order_value": 0
            }

    async def _get_order_count(
        self,
        start_date: date,
        end_date: date
    ) -> int:
        """Helper to get total order count."""
        query = """
            SELECT COUNT(id) FROM orders
            WHERE created_at >= $1 AND created_at <= $2
        """
        try:
            count = await self.db_pool.fetchval(query, start_date, end_date + timedelta(days=1))
            return count or 0
        except Exception as e:
            logger.error(f"Error fetching order count: {e}")
            return 0

    async def _get_product_count(self) -> int:
        """Helper to get total active product count."""
        query = "SELECT COUNT(id) FROM products WHERE status = 'active'"
        try:
            count = await self.db_pool.fetchval(query)
            return count or 0
        except Exception as e:
            logger.error(f"Error fetching product count: {e}")
            return 0

    async def _get_trend_count(
        self,
        start_date: date,
        end_date: date
    ) -> int:
        """Helper to get number of trends analyzed in the period."""
        query = """
            SELECT COUNT(id) FROM trends 
            WHERE created_at >= $1 AND created_at <= $2
        """
        try:
            count = await self.db_pool.fetchval(query, start_date, end_date + timedelta(days=1))
            return count or 0
        except Exception as e:
            logger.error(f"Error fetching trend count: {e}")
            return 0
