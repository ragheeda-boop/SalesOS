"""Integration test conftest — lightweight fixtures for Kafka integration tests.

These tests mock Kafka and PostgreSQL but exercise the full
outbox → relay → consumer flow in-process.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    """Set test environment variables."""
    import os

    os.environ.setdefault("SALESOS_TESTING", "true")
    os.environ.setdefault("SECRET_KEY", "test")
    os.environ.setdefault("POSTGRES_PASSWORD", "test")
    os.environ.setdefault("NEO4J_PASSWORD", "test")
    os.environ.setdefault("JWT_SECRET_KEY", "test")
    os.environ.setdefault("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    yield


def make_mock_session() -> MagicMock:
    """Create a mock DB session whose execute() returns a proper result."""
    session = MagicMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    exec_result = MagicMock()
    exec_result.fetchall.return_value = []
    exec_result.fetchone.return_value = None
    exec_result.scalar.return_value = 0
    exec_result.rowcount = 0
    session.execute.return_value = exec_result
    return session


def make_mock_session_factory(session: MagicMock | None = None) -> MagicMock:
    """Create a mock session factory yielding the given session."""
    if session is None:
        session = make_mock_session()
    factory = MagicMock()
    factory.return_value.__aenter__.return_value = session
    factory.return_value.__aexit__.return_value = None
    return factory
