"""Focused tests for StructuredLogger stdlib-style arity (GA Wave 2 residual)."""

from __future__ import annotations

import logging

from sdk.telemetry import StructuredLogger


def test_structured_logger_error_accepts_printf_args(caplog):
    logger = StructuredLogger("test.structured_logger")
    with caplog.at_level(logging.ERROR, logger="test.structured_logger"):
        logger.error("Graph %s SQL fallback error (%.0fms): %s", "competitors", 12.3, "boom")
    assert "Graph competitors SQL fallback error (12ms): boom" in caplog.text


def test_structured_logger_warning_alias_accepts_printf_args(caplog):
    logger = StructuredLogger("test.structured_logger.warn")
    with caplog.at_level(logging.WARNING, logger="test.structured_logger.warn"):
        logger.warning("Neo4j attempt %d/%d failed: %s", 1, 3, "timeout")
    assert "Neo4j attempt 1/3 failed: timeout" in caplog.text


def test_structured_logger_kwargs_extra_still_works(caplog):
    logger = StructuredLogger("test.structured_logger.extra")
    with caplog.at_level(logging.INFO, logger="test.structured_logger.extra"):
        logger.info("hello", tenant_id="t-1")
    assert "hello" in caplog.text
