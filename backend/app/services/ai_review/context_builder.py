import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analysis import AnalysisResult
from app.models.findings import CodeSmell, SecurityFinding
from app.models.pull_request import ChangedFile, PullRequest
from app.models.repository import Repository
from app.models.review_job import ReviewJob


class AIReviewContextBuilder:
    """
    Context Assembly Engine for building enriched prompts combining PR metadata,
    line-numbered diff patches, and static analysis findings.
    """
    def __init__(self, db: AsyncSession):
        self.db = db

    async def build_pr_review_context(
        self, repository_id: uuid.UUID, pr_number: int
    ) -> dict[str, Any]:
        """
        Build complete context dictionary for LLM code review prompt.
        """
        # Fetch Repository
        repo_stmt = select(Repository).where(Repository.id == repository_id)
        repo_res = await self.db.execute(repo_stmt)
        repo = repo_res.scalars().first()

        # Fetch PullRequest
        pr_stmt = select(PullRequest).where(
            PullRequest.repository_id == repository_id, PullRequest.pr_number == pr_number
        )
        pr_res = await self.db.execute(pr_stmt)
        pr = pr_res.scalars().first()

        if not repo or not pr:
            return {}

        # Fetch Effective Settings
        from app.services.repository_settings_service import RepositorySettingsService
        settings_service = RepositorySettingsService(self.db)
        settings = await settings_service.get_effective_settings(repository_id)

        # Fetch Changed Files
        cf_stmt = select(ChangedFile).where(ChangedFile.pull_request_id == pr.id)
        cf_res = await self.db.execute(cf_stmt)
        changed_files = list(cf_res.scalars().all())

        files_payload: list[dict[str, Any]] = []
        for cf in changed_files:
            if settings_service.is_file_excluded(cf.filename, settings):
                continue

            files_payload.append({
                "filename": cf.filename,
                "status": cf.status,
                "language": cf.language or "Plain Text",
                "additions": cf.additions,
                "deletions": cf.deletions,
                "patch": cf.patch,
                "parsed_diff": cf.parsed_diff,
            })


        # Fetch Static Analysis Findings
        job_stmt = select(ReviewJob).where(ReviewJob.pull_request_id == pr.id).order_by(ReviewJob.created_at.desc())
        job_res = await self.db.execute(job_stmt)
        job = job_res.scalars().first()

        security_findings: list[dict[str, Any]] = []
        code_smells: list[dict[str, Any]] = []

        if job:
            ar_stmt = select(AnalysisResult).where(AnalysisResult.review_job_id == job.id)
            ar_res = await self.db.execute(ar_stmt)
            ar_results = list(ar_res.scalars().all())

            for ar in ar_results:
                sf_stmt = select(SecurityFinding).where(SecurityFinding.analysis_result_id == ar.id)
                sf_res = await self.db.execute(sf_stmt)
                for sf in sf_res.scalars().all():
                    security_findings.append({
                        "rule_id": sf.rule_id,
                        "title": sf.title,
                        "severity": sf.severity,
                        "file_path": sf.file_path,
                        "start_line": sf.start_line,
                    })

                cs_stmt = select(CodeSmell).where(CodeSmell.analysis_result_id == ar.id)
                cs_res = await self.db.execute(cs_stmt)
                for cs in cs_res.scalars().all():
                    code_smells.append({
                        "smell_type": cs.smell_type,
                        "description": cs.description,
                        "file_path": cs.file_path,
                        "start_line": cs.start_line,
                    })

        return {
            "repository": {
                "full_name": repo.full_name,
                "language": repo.language,
                "default_branch": repo.default_branch,
            },
            "pull_request": {
                "number": pr.pr_number,
                "title": pr.title,
                "body": pr.body or "",
                "author": pr.author_login,
                "head_branch": pr.head_branch,
                "base_branch": pr.base_branch,
                "additions": pr.additions,
                "deletions": pr.deletions,
            },
            "changed_files": files_payload,
            "settings": settings.model_dump(),
            "static_analysis": {

                "security_findings": security_findings,
                "code_smells": code_smells,
            },
        }
