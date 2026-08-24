from app.schemas.repository import RepositoryResponse, RepositorySettingsSchema
from app.services.repository_settings_service import RepositorySettingsService


def test_repository_response_schema():
    """Verify RepositoryResponse serialization."""
    repo_data = {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "name": "core-engine",
        "full_name": "acme/core-engine",
        "github_repo_id": 987654321,
        "owner_login": "acme",
        "default_branch": "main",
        "is_private": True,
        "is_active": True,
    }
    obj = RepositoryResponse(**repo_data)
    assert str(obj.id) == "123e4567-e89b-12d3-a456-426614174000"
    assert obj.full_name == "acme/core-engine"
    assert obj.is_private is True


def test_repository_settings_defaults():
    """Verify repository settings inheritance."""
    defaults = RepositorySettingsService.resolve_effective_settings(None)
    assert isinstance(defaults, RepositorySettingsSchema)
    assert defaults.analysis_enabled is True
    assert defaults.auto_publish_github_review is True
    assert defaults.max_cyclomatic_complexity == 15


def test_repository_pagination_mock():
    """Simulate repository list pagination."""
    all_repos = [{"id": f"repo_{i}", "name": f"repo_{i}"} for i in range(25)]

    def get_paginated_repos(page: int = 1, limit: int = 10):
        start = (page - 1) * limit
        end = start + limit
        return all_repos[start:end]

    page1 = get_paginated_repos(1, 10)
    assert len(page1) == 10
    assert page1[0]["name"] == "repo_0"

    page3 = get_paginated_repos(3, 10)
    assert len(page3) == 5
    assert page3[0]["name"] == "repo_20"


if __name__ == "__main__":
    test_repository_response_schema()
    test_repository_settings_defaults()
    test_repository_pagination_mock()
    print("Repository management unit tests PASSED!")
