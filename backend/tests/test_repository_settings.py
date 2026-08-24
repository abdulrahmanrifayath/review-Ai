import uuid
import pytest
from app.schemas.repository import (
    RepositorySettingsSchema,
    RepositorySettingsUpdateSchema,
)
from app.services.repository_settings_service import RepositorySettingsService


def test_default_repository_settings_schema():
    """Verify default repository settings values."""
    defaults = RepositorySettingsSchema()
    assert defaults.analysis_enabled is True
    assert defaults.auto_review_enabled is True
    assert defaults.auto_publish_github_review is True

    assert "package-lock.json" in defaults.excluded_files
    assert "node_modules" in defaults.excluded_directories
    assert ".py" in defaults.supported_file_extensions

    assert defaults.max_cyclomatic_complexity == 15
    assert defaults.min_maintainability_score == 60
    assert defaults.min_severity_level == "LOW"
    assert defaults.max_findings_limit == 50

    assert defaults.static_analysis_enabled is True
    assert defaults.security_analysis_enabled is True
    assert defaults.performance_analysis_enabled is True
    assert defaults.ast_analysis_enabled is True

    assert defaults.post_inline_comments is True
    assert defaults.review_mode == "COMMENT"


def test_resolve_effective_settings_with_custom_overrides():
    """Verify merging custom JSON settings over defaults."""
    custom_dict = {
        "max_cyclomatic_complexity": 8,
        "min_severity_level": "HIGH",
        "security_analysis_enabled": False,
        "excluded_directories": ["custom_node_modules", "temp"],
        "review_mode": "REQUEST_CHANGES",
    }

    effective = RepositorySettingsService.resolve_effective_settings(custom_dict)

    # Overridden values
    assert effective.max_cyclomatic_complexity == 8
    assert effective.min_severity_level == "HIGH"
    assert effective.security_analysis_enabled is False
    assert effective.excluded_directories == ["custom_node_modules", "temp"]
    assert effective.review_mode == "REQUEST_CHANGES"

    # Non-overridden values remain default
    assert effective.analysis_enabled is True
    assert effective.performance_analysis_enabled is True


def test_file_exclusion_filtering_directories():
    """Verify path exclusion matching for directories."""
    settings = RepositorySettingsSchema(excluded_directories=["node_modules", "dist", "build"])

    assert RepositorySettingsService.is_file_excluded("node_modules/express/index.js", settings) is True
    assert RepositorySettingsService.is_file_excluded("src/build/output.js", settings) is True
    assert RepositorySettingsService.is_file_excluded("src/components/Button.tsx", settings) is False


def test_file_exclusion_filtering_filenames():
    """Verify path exclusion matching for specific file patterns."""
    settings = RepositorySettingsSchema(excluded_files=["package-lock.json", ".min.js", "yarn.lock"])

    assert RepositorySettingsService.is_file_excluded("package-lock.json", settings) is True
    assert RepositorySettingsService.is_file_excluded("assets/bundle.min.js", settings) is True
    assert RepositorySettingsService.is_file_excluded("src/utils.js", settings) is False


def test_file_exclusion_filtering_unsupported_extensions():
    """Verify filtering for unsupported file extensions."""
    settings = RepositorySettingsSchema(supported_file_extensions=[".py", ".ts", ".js"])

    assert RepositorySettingsService.is_file_excluded("main.py", settings) is False
    assert RepositorySettingsService.is_file_excluded("app.ts", settings) is False
    assert RepositorySettingsService.is_file_excluded("binary_executable.exe", settings) is True
    assert RepositorySettingsService.is_file_excluded("archive.zip", settings) is True


def test_repository_settings_update_schema_validation():
    """Verify Pydantic update schema partial parsing."""
    update_data = RepositorySettingsUpdateSchema(
        max_cyclomatic_complexity=10,
        post_inline_comments=False,
    )
    dumped = update_data.model_dump(exclude_unset=True, exclude_none=True)
    assert dumped == {"max_cyclomatic_complexity": 10, "post_inline_comments": False}


if __name__ == "__main__":
    test_default_repository_settings_schema()
    test_resolve_effective_settings_with_custom_overrides()
    test_file_exclusion_filtering_directories()
    test_file_exclusion_filtering_filenames()
    test_file_exclusion_filtering_unsupported_extensions()
    test_repository_settings_update_schema_validation()
    print("All repository settings unit tests PASSED successfully!")
