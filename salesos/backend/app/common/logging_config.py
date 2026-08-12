"""Structured JSON logging configuration for SalesOS.

Produces newline-delimited JSON with structured fields:
  - timestamp, level, logger, message (standard)
  - Any LogRecord ``extra=`` attributes (stdlib merges these onto the record)

Railway CLI/JSON often drops or truncates ``message``; critical evaluate /
fan-out fields must therefore live as top-level JSON keys via ``extra=``,
matching RequestLoggingMiddleware (request_id, latency_ms, path, …).
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime

# Stdlib LogRecord attributes — do not re-emit as structured extras.
_STANDARD_RECORD_ATTRS = frozenset(
    {
        "name",
        "msg",
        "args",
        "levelname",
        "levelno",
        "pathname",
        "filename",
        "module",
        "exc_info",
        "exc_text",
        "stack_info",
        "lineno",
        "funcName",
        "created",
        "msecs",
        "relativeCreated",
        "thread",
        "threadName",
        "processName",
        "process",
        "message",
        "asctime",
        "taskName",
        "color_message",
    }
)


class JSONFormatter(logging.Formatter):
    """Output logs as newline-delimited JSON with structured fields."""

    def format(self, record: logging.LogRecord) -> str:
        log: dict = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # Promote logger ``extra=`` attrs so Railway JSON retains step /
        # decision_id / subscriber / retry even when message is stripped.
        for key, value in record.__dict__.items():
            if key in _STANDARD_RECORD_ATTRS or key.startswith("_"):
                continue
            if value is None or value == "":
                continue
            log[key] = value
        if record.exc_info and record.exc_info[0]:
            log["exception"] = self.formatException(record.exc_info)
        return json.dumps(log, default=str)


def configure_logging(level: str = "DEBUG") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(getattr(logging, level.upper(), logging.DEBUG))
    # Silence chatty third-party loggers
    for noisy in ("httpx", "httpcore", "urllib3", "neo4j"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
