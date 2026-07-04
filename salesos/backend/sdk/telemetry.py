"""OpenTelemetry configuration and structured logging."""

import logging
import time
from contextlib import asynccontextmanager
from typing import Any

from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from sdk.config import sdk_settings


def setup_telemetry(service_name: str = "salesos") -> None:
    """Initialize OpenTelemetry tracer and meter providers."""
    resource = Resource.create({
        "service.name": service_name,
        "service.version": sdk_settings.service_version,
        "deployment.environment": sdk_settings.environment,
    })

    tracer_provider = TracerProvider(resource=resource)
    span_processor = BatchSpanProcessor(
        OTLPSpanExporter(endpoint=sdk_settings.otlp_endpoint)
    )
    tracer_provider.add_span_processor(span_processor)
    trace.set_tracer_provider(tracer_provider)


def get_tracer(name: str) -> trace.Tracer:
    return trace.get_tracer(name)


def get_meter(name: str) -> metrics.Meter:
    return metrics.get_meter(name)


def record_metric(name: str, value: float, attributes: dict | None = None) -> None:
    meter = get_meter("salesos")
    counter = meter.create_counter(name)
    counter.add(value, attributes or {})


class StructuredLogger:
    """Structured JSON logger with request context."""

    def __init__(self, name: str):
        self._logger = logging.getLogger(name)
        self._extra: dict[str, Any] = {}

    def bind(self, **kwargs) -> "StructuredLogger":
        self._extra.update(kwargs)
        return self

    def _log(self, level: int, msg: str, **kwargs) -> None:
        self._logger.log(level, msg, extra={**self._extra, **kwargs})

    def info(self, msg: str, **kwargs) -> None:
        self._log(logging.INFO, msg, **kwargs)

    def error(self, msg: str, **kwargs) -> None:
        self._log(logging.ERROR, msg, **kwargs)

    def warn(self, msg: str, **kwargs) -> None:
        self._log(logging.WARNING, msg, **kwargs)

    def debug(self, msg: str, **kwargs) -> None:
        self._log(logging.DEBUG, msg, **kwargs)

    def exception(self, msg: str, **kwargs) -> None:
        self._log(logging.ERROR, msg, exc_info=True, **kwargs)


@asynccontextmanager
async def trace_span(name: str, attributes: dict | None = None):
    tracer = get_tracer("salesos")
    with tracer.start_as_current_span(name) as span:
        if attributes:
            span.set_attributes(attributes)
        start = time.monotonic()
        try:
            yield span
        finally:
            duration_ms = (time.monotonic() - start) * 1000
            span.set_attribute("duration_ms", duration_ms)
