import uuid
from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class RepositorySettingsSchema(BaseModel):
    # General
    analysis_enabled: bool = True
    auto_review_enabled: bool = True
    auto_publish_github_review: bool = True

    # File Rules
    excluded_files: List[str] = Field(
        default_factory=lambda: [
            ".min.js",
            ".min.css",
            "package-lock.json",
            "yarn.lock",
            "pnpm-lock.yaml",
            "poetry.lock",
        ]
    )
    excluded_directories: List[str] = Field(
        default_factory=lambda: [
            "node_modules",
            "dist",
            "build",
            ".git",
            "__pycache__",
            "vendor",
            "target",
            ".idea",
            ".vscode",
        ]
    )
    supported_file_extensions: List[str] = Field(
        default_factory=lambda: [
            ".py", ".ts", ".tsx", ".js", ".jsx", ".java", ".go", ".rs",
            ".cpp", ".c", ".h", ".cs", ".php", ".rb", ".swift", ".kt",
            ".sql", ".sh", ".yaml", ".yml", ".json", ".html", ".css", ".scss", ".md"
        ]
    )
    max_file_size_kb: int = 1024

    # Analysis Rules
    max_cyclomatic_complexity: int = 15
    min_maintainability_score: int = 60
    min_severity_level: str = "LOW"  # INFO, LOW, MEDIUM, HIGH, CRITICAL
    max_findings_limit: int = 50

    # Analyzer Controls
    static_analysis_enabled: bool = True
    security_analysis_enabled: bool = True
    performance_analysis_enabled: bool = True
    ast_analysis_enabled: bool = True
    ai_review_enabled: bool = True
    test_generation_enabled: bool = True
    documentation_analysis_enabled: bool = True

    # GitHub Review Behavior
    post_inline_comments: bool = True
    post_summary: bool = True
    auto_publish: bool = True
    review_mode: str = "COMMENT"  # COMMENT, REQUEST_CHANGES, APPROVE

    model_config = ConfigDict(from_attributes=True)


class RepositorySettingsUpdateSchema(BaseModel):
    # General
    analysis_enabled: Optional[bool] = None
    auto_review_enabled: Optional[bool] = None
    auto_publish_github_review: Optional[bool] = None

    # File Rules
    excluded_files: Optional[List[str]] = None
    excluded_directories: Optional[List[str]] = None
    supported_file_extensions: Optional[List[str]] = None
    max_file_size_kb: Optional[int] = None

    # Analysis Rules
    max_cyclomatic_complexity: Optional[int] = None
    min_maintainability_score: Optional[int] = None
    min_severity_level: Optional[str] = None
    max_findings_limit: Optional[int] = None

    # Analyzer Controls
    static_analysis_enabled: Optional[bool] = None
    security_analysis_enabled: Optional[bool] = None
    performance_analysis_enabled: Optional[bool] = None
    ast_analysis_enabled: Optional[bool] = None
    ai_review_enabled: Optional[bool] = None
    test_generation_enabled: Optional[bool] = None
    documentation_analysis_enabled: Optional[bool] = None

    # GitHub Review Behavior
    post_inline_comments: Optional[bool] = None
    post_summary: Optional[bool] = None
    auto_publish: Optional[bool] = None
    review_mode: Optional[str] = None


class RepositoryBase(BaseModel):
    name: str
    full_name: str
    github_repo_id: int
    default_branch: str = "main"


class RepositoryCreate(RepositoryBase):
    pass


class RepositoryResponse(RepositoryBase):
    id: uuid.UUID
    owner_login: str
    is_private: bool = True
    is_active: bool = True
    language: Optional[str] = None
    stargazers_count: int = 0
    forks_count: int = 0
    open_issues_count: int = 0
    settings: Optional[dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

