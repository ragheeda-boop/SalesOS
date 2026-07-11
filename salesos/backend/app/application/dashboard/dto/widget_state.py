from enum import Enum


class WidgetStatus(str, Enum):
    ready = "ready"
    loading = "loading"
    degraded = "degraded"
    error = "error"
