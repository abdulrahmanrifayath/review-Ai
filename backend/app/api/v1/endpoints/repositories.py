import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.repository import Repository
from app.models.user import User
from app.schemas.analytics import DashboardMetricsResponse, RepositoryAnalyticsResponse
from app.schemas.repository import (
    RepositoryResponse,
    RepositorySettingsSchema,
    RepositorySettingsUpdateSchema,
)
from app.services.repository_analytics import RepositoryAnalyticsService
from app.services.repository_settings_service import RepositorySettingsService

router = APIRouter()


@router.get("", response_model=list[RepositoryResponse])
async def list_repositories(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List connected repositories."""
    statement = select(Repository).where(Repository.is_active.is_(True)).order_by(Repository.updated_at.desc())
    result = await db.execute(statement)
    repos = list(result.scalars().all())
    return repos


@router.get("/dashboard/metrics", response_model=DashboardMetricsResponse)
async def get_dashboard_metrics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Fetch high-level SaaS platform dashboard metrics."""
    analytics_service = RepositoryAnalyticsService(db)
    return await analytics_service.get_dashboard_metrics()


@router.get("/{id}/analytics", response_model=RepositoryAnalyticsResponse)
async def get_repository_analytics(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Fetch detailed health, quality score, commit activity, and review history analytics for a repository."""
    analytics_service = RepositoryAnalyticsService(db)
    return await analytics_service.get_repository_analytics(id)


@router.get("/{id}/settings", response_model=RepositorySettingsSchema)
async def get_repository_settings(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Fetch effective ReviewAI configuration settings for a repository."""
    settings_service = RepositorySettingsService(db)
    return await settings_service.get_effective_settings(id)


@router.put("/{id}/settings", response_model=RepositorySettingsSchema)
async def update_repository_settings(
    id: uuid.UUID,
    settings_update: RepositorySettingsUpdateSchema,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update ReviewAI configuration settings for a repository."""
    settings_service = RepositorySettingsService(db)
    updated = await settings_service.update_repository_settings(id, settings_update)
    await db.commit()
    return updated


@router.post("/{id}/settings/reset", response_model=RepositorySettingsSchema)
async def reset_repository_settings(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Reset repository settings back to system defaults."""
    settings_service = RepositorySettingsService(db)
    reset = await settings_service.reset_repository_settings(id)
    await db.commit()
    return reset

