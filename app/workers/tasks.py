from app.workers.celery_app import celery_app
from loguru import logger

@celery_app.task
def process_trend_analysis(trend_id: int):
    """Process trend analysis task"""
    logger.info(f"Processing trend {trend_id}")
    return {"status": "completed", "trend_id": trend_id}

@celery_app.task
def generate_products_task(trend_id: int, count: int = 5):
    """Generate products from trend"""
    logger.info(f"Generating {count} products from trend {trend_id}")
    return {"status": "completed", "products_created": count}
