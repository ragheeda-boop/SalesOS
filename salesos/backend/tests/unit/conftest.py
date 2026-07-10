"""Unit test conftest — overrides root conftest's DB setup with no-op."""
import os

os.environ.setdefault("SALESOS_TESTING", "true")
os.environ.setdefault("SECRET_KEY", "test")
os.environ.setdefault("POSTGRES_PASSWORD", "test")
os.environ.setdefault("NEO4J_PASSWORD", "test")
os.environ.setdefault("JWT_SECRET_KEY", "test")


import pytest


@pytest.fixture(scope="session", autouse=True)
async def setup_database():
    """Override root conftest's DB-heavy setup_database with a no-op for unit tests."""
    yield
