import shutil

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.monitoring import metrics_collector
from app.core.queue.redis_queue import queue_manager

router = APIRouter()


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Production health check endpoint verifying Database connectivity, Redis ping, Disk space, and app status.
    """
    db_status = "healthy"
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        db_status = "unhealthy"

    redis_status = "healthy"
    try:
        client = await queue_manager.get_client()
        pong = await client.ping()
        if not pong:
            redis_status = "unhealthy"
    except Exception:
        redis_status = "unhealthy"

    # Disk Space Check
    total, used, free = shutil.disk_usage("/")
    free_gb = round(free / (1024 ** 3), 2)

    overall_status = "ok" if (db_status == "healthy" and redis_status == "healthy") else "degraded"

    return {
        "status": overall_status,
        "app_name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "database": db_status,
        "redis": redis_status,
        "free_disk_gb": free_gb,
    }


@router.get("/metrics", status_code=status.HTTP_200_OK)
async def metrics_endpoint():
    """
    Prometheus metrics exposition endpoint for production monitoring scraping.
    """
    metrics_text = metrics_collector.generate_metrics_text()
    return Response(content=metrics_text, media_type="text/plain; version=0.0.4")


@router.get("/health/analyzers", status_code=status.HTTP_200_OK)
async def analyzers_health_endpoint():
    """
    Expose live health, availability, and fallback status for all configured static analysis language tools.
    """
    from app.services.static_analysis.analyzer_validator import AnalyzerToolValidator
    return AnalyzerToolValidator.get_all_analyzers_status()

