"""Application Metrics Collector for SalesOS — Prometheus-format endpoint.

Collects:
- Request count, latency histogram, error rate
- Active WebSocket connections
- Database pool utilization
- Cache hit/miss ratio
- NBA engine processing time
"""

import threading
import time
from collections import defaultdict
from typing import Any


class _Histogram:
    """Prometheus-style histogram with predefined buckets."""

    BUCKETS = [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]

    def __init__(self) -> None:
        self._buckets = {b: 0 for b in self.BUCKETS}
        self._sum = 0.0
        self._count = 0

    def observe(self, value: float) -> None:
        self._count += 1
        self._sum += value
        for b in self.BUCKETS:
            if value <= b:
                self._buckets[b] += 1

    def snapshot(self) -> dict[str, Any]:
        return {
            "buckets": dict(self._buckets),
            "sum": self._sum,
            "count": self._count,
        }


class ApplicationMetricsCollector:
    """Thread-safe in-memory metrics collector exposing Prometheus-formatted output."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._http_requests: dict[tuple[str, str, int], int] = defaultdict(int)
        self._http_duration: dict[tuple[str, str], _Histogram] = defaultdict(_Histogram)
        self._error_count: dict[str, int] = defaultdict(int)
        self._ws_active: int = 0
        self._ws_total_opened: int = 0
        self._ws_total_closed: int = 0
        self._db_pool_checkedout: int = 0
        self._db_pool_checkedin: int = 0
        self._db_pool_overflow: int = 0
        self._db_pool_total: int = 0
        self._cache_hits: int = 0
        self._cache_misses: int = 0
        self._nba_duration: _Histogram = _Histogram()
        self._start_time = time.time()

    def track_http_request(self, method: str, path: str, status: int, duration: float) -> None:
        with self._lock:
            self._http_requests[(method, path, status)] += 1
            self._http_duration[(method, path)].observe(duration)
            if status >= 500:
                self._error_count["http_5xx"] += 1
            elif status >= 400:
                self._error_count["http_4xx"] += 1

    def track_cache_hit(self) -> None:
        with self._lock:
            self._cache_hits += 1

    def track_cache_miss(self) -> None:
        with self._lock:
            self._cache_misses += 1

    def track_ws_connection(self) -> None:
        with self._lock:
            self._ws_total_opened += 1
            self._ws_active += 1

    def track_ws_disconnection(self) -> None:
        with self._lock:
            self._ws_total_closed += 1
            self._ws_active = max(0, self._ws_active - 1)

    def track_db_pool(self, checkedout: int, checkedin: int, overflow: int, total_open: int) -> None:
        with self._lock:
            self._db_pool_checkedout = checkedout
            self._db_pool_checkedin = checkedin
            self._db_pool_overflow = overflow
            self._db_pool_total = total_open

    def track_nba_processing(self, duration: float) -> None:
        with self._lock:
            self._nba_duration.observe(duration)

    def generate(self) -> str:
        lines: list[str] = []

        def _line(text: str) -> None:
            lines.append(text)

        with self._lock:
            # ── HTTP requests ──
            _line("# HELP salesos_http_requests_total Total HTTP requests by method, path, status")
            _line("# TYPE salesos_http_requests_total counter")
            for (method, path, status), count in sorted(self._http_requests.items()):
                path_clean = path.replace('"', '\\"')
                _line(f'salesos_http_requests_total{{method="{method}",path="{path_clean}",status="{status}"}} {count}')

            # ── HTTP latency histogram ──
            _line("")
            _line("# HELP salesos_http_request_duration_seconds HTTP request duration histogram")
            _line("# TYPE salesos_http_request_duration_seconds histogram")
            for (method, path), hist in sorted(self._http_duration.items()):
                path_clean = path.replace('"', '\\"')
                labels = f'method="{method}",path="{path_clean}"'
                snap = hist.snapshot()
                base = f'salesos_http_request_duration_seconds{{{labels}}}'
                for bucket, count in sorted(snap["buckets"].items()):
                    _line(f'{base}_bucket{{le="{bucket}"}} {count}')
                _line(f'{base}_bucket{{le="+Inf"}} {snap["count"]}')
                _line(f"{base}_count {snap['count']}")
                _line(f"{base}_sum {snap['sum']:.6f}")

            # ── Error counts ──
            _line("")
            _line("# HELP salesos_errors_total Total error counts by type")
            _line("# TYPE salesos_errors_total counter")
            for err_type, count in sorted(self._error_count.items()):
                _line(f'salesos_errors_total{{type="{err_type}"}} {count}')

            # ── WebSocket connections ──
            _line("")
            _line("# HELP salesos_websocket_active Active WebSocket connections")
            _line("# TYPE salesos_websocket_active gauge")
            _line(f"salesos_websocket_active {self._ws_active}")

            _line("# HELP salesos_websocket_connections_total Total WebSocket connections opened")
            _line("# TYPE salesos_websocket_connections_total counter")
            _line(f"salesos_websocket_connections_total {self._ws_total_opened}")

            _line("# HELP salesos_websocket_disconnections_total Total WebSocket disconnections")
            _line("# TYPE salesos_websocket_disconnections_total counter")
            _line(f"salesos_websocket_disconnections_total {self._ws_total_closed}")

            # ── Database pool ──
            _line("")
            _line("# HELP salesos_db_pool_checkedout Database connections currently checked out")
            _line("# TYPE salesos_db_pool_checkedout gauge")
            _line(f"salesos_db_pool_checkedout {self._db_pool_checkedout}")

            _line("# HELP salesos_db_pool_checkedin Database connections currently checked in")
            _line("# TYPE salesos_db_pool_checkedin gauge")
            _line(f"salesos_db_pool_checkedin {self._db_pool_checkedin}")

            _line("# HELP salesos_db_pool_overflow Database pool overflow connections")
            _line("# TYPE salesos_db_pool_overflow gauge")
            _line(f"salesos_db_pool_overflow {self._db_pool_overflow}")

            _line("# HELP salesos_db_pool_total Total open database connections")
            _line("# TYPE salesos_db_pool_total gauge")
            _line(f"salesos_db_pool_total {self._db_pool_total}")

            total_cache = self._cache_hits + self._cache_misses
            hit_rate = self._cache_hits / total_cache if total_cache > 0 else 0.0

            _line("")
            _line("# HELP salesos_cache_hits_total Total cache hits")
            _line("# TYPE salesos_cache_hits_total counter")
            _line(f"salesos_cache_hits_total {self._cache_hits}")

            _line("# HELP salesos_cache_misses_total Total cache misses")
            _line("# TYPE salesos_cache_misses_total counter")
            _line(f"salesos_cache_misses_total {self._cache_misses}")

            _line("# HELP salesos_cache_hit_ratio Current cache hit ratio")
            _line("# TYPE salesos_cache_hit_ratio gauge")
            _line(f"salesos_cache_hit_ratio {hit_rate:.4f}")

            # ── NBA engine ──
            _line("")
            _line("# HELP salesos_nba_processing_duration_seconds NBA engine processing duration histogram")
            _line("# TYPE salesos_nba_processing_duration_seconds histogram")
            nba_snap = self._nba_duration.snapshot()
            nba_base = "salesos_nba_processing_duration_seconds"
            for bucket, count in sorted(nba_snap["buckets"].items()):
                _line(f'{nba_base}_bucket{{le="{bucket}"}} {count}')
            _line(f'{nba_base}_bucket{{le="+Inf"}} {nba_snap["count"]}')
            _line(f"{nba_base}_count {nba_snap['count']}")
            _line(f"{nba_base}_sum {nba_snap['sum']:.6f}")

            # ── Uptime ──
            _line("")
            _line("# HELP salesos_app_uptime_seconds Application uptime in seconds")
            _line("# TYPE salesos_app_uptime_seconds gauge")
            _line(f"salesos_app_uptime_seconds {time.time() - self._start_time:.0f}")

        lines.append(f"# EOF {time.time()}")
        return "\n".join(lines) + "\n"


collector = ApplicationMetricsCollector()
