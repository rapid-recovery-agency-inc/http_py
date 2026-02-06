"""Pytest configuration and shared fixtures."""

import pytest


@pytest.fixture
def sample_data() -> dict[str, str]:
    """Sample data for tests."""
    return {"id": "1", "name": "test"}
