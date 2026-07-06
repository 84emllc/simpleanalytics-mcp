"""Shared pytest fixtures."""

import pytest


@pytest.fixture(autouse=True)
def _sa_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    """Provide dummy SimpleAnalytics credentials for all tests."""
    monkeypatch.setenv("SA_API_KEY", "sa_api_key_test")
    monkeypatch.setenv("SA_USER_ID", "sa_user_id_test")
