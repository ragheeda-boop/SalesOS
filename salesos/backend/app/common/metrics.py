"""In-memory Prometheus-style metrics tracker for SalesOS.

Usage:
    from app.common.metrics import metrics

    # Track HTTP request
    metrics.track_http_request("GET", "/api/companies", 200, 0.045)

    # Time a DB query
    with metrics.db_timer("get_companies"):
        await db.execute(...)

    # Time an AI inference
    with metrics.ai_timer("gpt-4o"):
        await openai.chat(...)

    # Generate Prometheus output
    print(metrics.generate())
"""

import threading
import time
from collections import defaultdict


class _Histogram:
    """Prometheus-style histogram with predefined buckets."""

    BUCKETS = [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]

    def __init__(self):
        self._buckets = {b: 0 for b in self.BUCKETS}
        self._sum = 0.0
        self._count = 0

    def observe(self, value: float):
        self._count += 1
        self._sum += value
        for b in self.BUCKETS:
            if value <= b:
                self._buckets[b] += 1

    def snapshot(self) -> dict:
        return {
            "buckets": dict(self._buckets),
            "sum": self._sum,
            "count": self._count,
        }


class MetricsTracker:
    """Thread-safe in-memory metrics tracker exposing Prometheus-formatted output."""

    def __init__(self):
        self._lock = threading.Lock()
        self._http_requests: dict[tuple[str, str, int], int] = defaultdict(int)
        self._http_duration: dict[tuple[str, str], _Histogram] = defaultdict(_Histogram)
        self._db_duration: dict[str, _Histogram] = defaultdict(_Histogram)
        self._ai_duration: dict[str, _Histogram] = defaultdict(_Histogram)
        self._start_time = time.time()

    # ── HTTP metrics ──

    def track_http_request(self, method: str, path: str, status: int, duration: float):
        with self._lock:
            self._http_requests[(method, path, status)] += 1
            self._http_duration[(method, path)].observe(duration)

    # ── DB query metrics ──

    def track_db_query(self, query_name: str, duration: float):
        with self._lock:
            self._db_duration[query_name].observe(duration)

    def db_timer(self, query_name: str):
        return _TimerContext(self, "db", query_name=query_name)

    # ── AI inference metrics ──

    def track_ai_inference(self, model: str, duration: float):
        with self._lock:
            self._ai_duration[model].observe(duration)

    def ai_timer(self, model: str):
        return _TimerContext(self, "ai", model=model)

    # ── Generator ──

    def generate(self) -> str:
        lines = [
            "# HELP salesos_http_requests_total Total HTTP requests",
            "# TYPE salesos_http_requests_total counter",
        ]
        with self._lock:
            for (method, path, status), count in sorted(self._http_requests.items()):
                path_clean = path.replace('"', '\\"')
                lines.append(
                    f'salesos_http_requests_total{{method="{method}",path="{path_clean}",status="{status}"}} {count}'
                )

            lines.append("")
            lines.append("# HELP salesos_http_request_duration_seconds HTTP request duration histogram")
            lines.append("# TYPE salesos_http_request_duration_seconds histogram")
            for (method, path), hist in sorted(self._http_duration.items()):
                path_clean = path.replace('"', '\\"')
                labels = f'method="{method}",path="{path_clean}"'
                snap = hist.snapshot()
                base = f'salesos_http_request_duration_seconds{{{labels}}}'
                for bucket, count in sorted(snap["buckets"].items()):
                    lines.append(f'{base}_bucket{{le="{bucket}"}} {count}')
                lines.append(f'{base}_bucket{{le="+Inf"}} {snap["count"]}')
                lines.append(f"{base}_count {snap['count']}")
                lines.append(f"{base}_sum {snap['sum']:.6f}")

            lines.append("")
            lines.append("# HELP salesos_db_query_duration_seconds Database query duration histogram")
            lines.append("# TYPE salesos_db_query_duration_seconds histogram")
            for query_name, hist in sorted(self._db_duration.items()):
                labels = f'query_name="{query_name}"'
                snap = hist.snapshot()
                base = f'salesos_db_query_duration_seconds{{{labels}}}'
                for bucket, count in sorted(snap["buckets"].items()):
                    lines.append(f'{base}_bucket{{le="{bucket}"}} {count}')
                lines.append(f'{base}_bucket{{le="+Inf"}} {snap["count"]}')
                lines.append(f"{base}_count {snap['count']}")
                lines.append(f"{base}_sum {snap['sum']:.6f}")

            lines.append("")
            lines.append("# HELP salesos_ai_inference_duration_seconds AI inference duration histogram")
            lines.append("# TYPE salesos_ai_inference_duration_seconds histogram")
            for model, hist in sorted(self._ai_duration.items()):
                labels = f'model="{model}"'
                snap = hist.snapshot()
                base = f'salesos_ai_inference_duration_seconds{{{labels}}}'
                for bucket, count in sorted(snap["buckets"].items()):
                    lines.append(f'{base}_bucket{{le="{bucket}"}} {count}')
                lines.append(f'{base}_bucket{{le="+Inf"}} {snap["count"]}')
                lines.append(f"{base}_count {snap['count']}")
                lines.append(f"{base}_sum {snap['sum']:.6f}")

            lines.append("")
            lines.append("# HELP salesos_uptime_seconds Application uptime")
            lines.append("# TYPE salesos_uptime_seconds gauge")
            lines.append(f"salesos_uptime_seconds {time.time() - self._start_time:.0f}")

        lines.append(f"# EOF {time.time()}")
        return "\n".join(lines) + "\n"


class _TimerContext:
    def __init__(self, tracker: MetricsTracker, kind: str, query_name: str = "", model: str = ""):
        self._tracker = tracker
        self._kind = kind
        self._query_name = query_name
        self._model = model
        self._start: float = 0.0

    def __enter__(self):
        self._start = time.time()
        return self

    def __exit__(self, *exc_info):
        duration = time.time() - self._start
        if self._kind == "db":
            self._tracker.track_db_query(self._query_name, duration)
        elif self._kind == "ai":
            self._tracker.track_ai_inference(self._model, duration)


metrics = MetricsTracker()
