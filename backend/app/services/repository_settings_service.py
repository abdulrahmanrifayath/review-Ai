import os
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.models.repository import Repository
from app.schemas.repository import RepositorySettingsSchema, RepositorySettingsUpdateSchema


class RepositorySettingsService:
    """
    Service managing repository-specific ReviewAI configurations, default resolution,
    path exclusion filtering, and CRUD operations.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_effective_settings(self, repository_id: uuid.UUID) -> RepositorySettingsSchema:
        """
        Fetch repository by ID and return its effective settings (merged with system defaults).
        """
        stmt = select(Repository).where(Repository.id == repository_id)
        res = await self.db.execute(stmt)
        repo = res.scalars().first()
        if not repo:
            raise NotFoundError("Repository", repository_id)

        return self.resolve_effective_settings(repo.settings)

    async def get_effective_settings_by_name(self, owner: str, repo_name: str) -> RepositorySettingsSchema:
        """
        Fetch repository by full_name and return its effective settings.
        """
        full_name = f"{owner}/{repo_name}"
        stmt = select(Repository).where(Repository.full_name == full_name)
        res = await self.db.execute(stmt)
        repo = res.scalars().first()
        if not repo:
            raise NotFoundError("Repository", full_name)

        return self.resolve_effective_settings(repo.settings)

    @staticmethod
    def resolve_effective_settings(repo_settings_dict: dict[str, Any] | None) -> RepositorySettingsSchema:
        """
        Merge custom repository settings dictionary with global default RepositorySettingsSchema.
        """
        default_settings = RepositorySettingsSchema()
        if not repo_settings_dict:
            return default_settings

        # Create updated dict by applying non-None custom overrides
        merged_data = default_settings.model_dump()
        for key, val in repo_settings_dict.items():
            if val is not None and key in merged_data:
                merged_data[key] = val

        return RepositorySettingsSchema(**merged_data)

    async def update_repository_settings(
        self, repository_id: uuid.UUID, update_dto: RepositorySettingsUpdateSchema
    ) -> RepositorySettingsSchema:
        """
        Update repository settings in DB.
        """
        stmt = select(Repository).where(Repository.id == repository_id)
        res = await self.db.execute(stmt)
        repo = res.scalars().first()
        if not repo:
            raise NotFoundError("Repository", repository_id)

        current_settings = repo.settings or {}
        update_data = update_dto.model_dump(exclude_unset=True, exclude_none=True)

        merged_settings = {**current_settings, **update_data}

        # Validate merged result against schema
        effective = RepositorySettingsSchema(**{**RepositorySettingsSchema().model_dump(), **merged_settings})
        repo.settings = effective.model_dump()
        self.db.add(repo)
        await self.db.flush()

        return effective

    async def reset_repository_settings(self, repository_id: uuid.UUID) -> RepositorySettingsSchema:
        """
        Reset repository settings back to system defaults.
        """
        stmt = select(Repository).where(Repository.id == repository_id)
        res = await self.db.execute(stmt)
        repo = res.scalars().first()
        if not repo:
            raise NotFoundError("Repository", repository_id)

        repo.settings = None
        self.db.add(repo)
        await self.db.flush()

        return RepositorySettingsSchema()

    @staticmethod
    def is_file_excluded(filename: str, settings: RepositorySettingsSchema) -> bool:
        """
        Determine if a file should be excluded from analysis based on:
        - Excluded file patterns
        - Excluded directory names
        - Supported file extensions
        """
        if not filename:
            return True

        normalized_path = filename.replace("\\", "/").strip().lower()
        parts = [p for p in normalized_path.split("/") if p]
        base_name = os.path.basename(normalized_path)
        ext = os.path.splitext(normalized_path)[1]

        # 1. Check excluded directories
        for ex_dir in settings.excluded_directories:
            ex_dir_clean = ex_dir.strip().lower()
            if ex_dir_clean in parts:
                return True

        # 2. Check excluded files
        for ex_file in settings.excluded_files:
            ex_file_clean = ex_file.strip().lower()
            if base_name == ex_file_clean or normalized_path.endswith(ex_file_clean):
                return True

        # 3. Check supported extensions (if configured)
        if settings.supported_file_extensions:
            supported = [e.lower().strip() for e in settings.supported_file_extensions]
            if ext and ext not in supported and base_name not in ("dockerfile", "makefile"):
                return True

        return False
