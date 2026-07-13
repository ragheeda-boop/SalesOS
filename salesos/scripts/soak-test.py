#!/usr/bin/env python3
"""SalesOS Soak Test — Sustained moderate load for 4 hours.

Monitors memory leaks, connection leaks, cache degradation.
Outputs hourly reports.

Usage:
    python scripts/soak-test.py
    python scripts/soak-test.py --duration 14400 --users 50
    SALESOS_BASE_URL=http://staging.example.com python scripts/soak-test.py
"""

import argparse
import asyncio
import json
import os
import random
import sys
import time
from dataclasses import dataclass, field
from typing import Optional

try:
    import aiohttp
except ImportError:
    aiohttp = None

try:
    import httpx
except ImportError:
    httpx = None

if aiohttp is None and httpx is None:
    print("ERROR: pip install aiohttp httpx")
    sys.exit(1)

BASE_URL = os.getenv("SALESOS_BASE_URL", "http://localhost:8000")
USERNAME = os.getenv("SALESOS_USERNAME", "admin@test.com")
PASSWORD = os.getenv("SALESOS_PASSWORD", "password")
COMPANY_ID = os.getenv("SALESOS_COMPANY_ID", "1")

SEARCH_QUERIES = [
    "Arabian company", "Riyadh", "technology", "Saudi Arabia",
    "AI startup", "fintech", "healthcare", "investor",
    "real estate", "construction", "e-commerce", "logistics",
]


@dataclass
class HourSnapshot:
    hour: int
    timestamp: float
    total_requests: int = 0
    errors: int = 0
    latencies: list = field(default_factory=list)
    elapsed: float = 0.0
    pool_checked_out: int = 0
    pool_total: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    ws_active: int = 0
    memory_bytes: int = 0

    @property
    def error_rate(self):
        return (self.errors / self.total_requests * 100) if self.total_requests else 0.0

    def percentile(self, p):
        if not self.latencies:
            return 0.0
        vals = sorted(self.latencies)
        return vals[min(int(len(vals) * p / 100), len(vals) - 1)]

    @property
    def p50(self): return self.percentile(50)
    @property
    def p95(self): return self.percentile(95)
    @property
    def cache_hit_rate(self):
        total = self.cache_hits + self.cache_misses
        return (self.cache_hits / total * 100) if total else 0.0

    def to_dict(self):
        return {
            "hour": self.hour,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(self.timestamp)),
            "total_requests": self.total_requests,
            "errors": self.errors,
            "error_rate_pct": round(self.error_rate, 2),
            "p50_ms": round(self.p50, 1),
            "p95_ms": round(self.p95, 1),
            "throughput_rps": round(self.total_requests / self.elapsed, 1) if self.elapsed else 0,
            "db_pool_checked_out": self.pool_checked_out,
            "db_pool_total": self.pool_total,
            "cache_hit_rate_pct": round(self.cache_hit_rate, 1),
            "ws_active": self.ws_active,
            "memory_mb": round(self.memory_bytes / 1024 / 1024, 1) if self.memory_bytes else 0,
        }


class AioHttpClient:
    def __init__(self):
        self._session = None

    async def __aenter__(self):
        timeout = aiohttp.ClientTimeout(total=30)
        conn = aiohttp.TCPConnector(limit=200, limit_per_host=100)
        self._session = aiohttp.ClientSession(timeout=timeout, connector=conn)
        return self

    async def __aexit__(self, *args):
        if self._session:
            await self._session.close()

    async def get(self, url, headers=None):
        start = time.perf_counter()
        try:
            async with self._session.get(url, headers=headers) as resp:
                await resp.read()
                return resp.status, (time.perf_counter() - start) * 1000
        except Exception:
            return 0, (time.perf_counter() - start) * 1000

    async def post(self, url, json=None, headers=None):
        start = time.perf_counter()
        try:
            async with self._session.post(url, json=json, headers=headers) as resp:
                await resp.read()
                return resp.status, (time.perf_counter() - start) * 1000
        except Exception:
            return 0, (time.perf_counter() - start) * 1000


class HttpxClient:
    def __init__(self):
        self._client = None

    async def __aenter__(self):
        self._client = httpx.AsyncClient(timeout=30.0, limits=httpx.Limits(max_connections=200))
        return self

    async def __aexit__(self, *args):
        if self._client:
            await self._client.aclose()

    async def get(self, url, headers=None):
        start = time.perf_counter()
        try:
            resp = await self._client.get(url, headers=headers)
            return resp.status_code, (time.perf_counter() - start) * 1000
        except Exception:
            return 0, (time.perf_counter() - start) * 1000

    async def post(self, url, json=None, headers=None):
        start = time.perf_counter()
        try:
            resp = await self._client.post(url, json=json, headers=headers)
            return resp.status_code, (time.perf_counter() - start) * 1000
        except Exception:
            return 0, (time.perf_counter() - start) * 1000


def make_client():
    return AioHttpClient() if aiohttp else HttpxClient()


async def get_token(client):
    status, _, body = await client.post(
        f"{BASE_URL}/api/v1/identity/login",
        json={"email": USERNAME, "password": PASSWORD},
    )
    if status == 200:
        data = json.loads(body) if isinstance(body, str) else body
        return data.get("access_token")
    return None


async def fetch_server_metrics(client, token):
    """Fetch /metrics/pool and /health for DB pool and cache info."""
    headers = {"Authorization": f"Bearer {token}"}
    metrics = {}
    try:
        status, _, body = await client.get(f"{BASE_URL}/metrics/pool", headers=headers)
        if status == 200:
            data = json.loads(body) if isinstance(body, str) else body
            metrics["pool_checked_out"] = data.get("checked_out", 0)
            metrics["pool_total"] = data.get("total_open", 0)
            metrics["cache_hits"] = data.get("cache_hits", 0)
            metrics["cache_misses"] = data.get("cache_misses", 0)
            metrics["ws_active"] = data.get("ws_active", 0)
            metrics["memory_bytes"] = data.get("memory_bytes", 0)
    except Exception:
        pass
    return metrics


async def run_sustained_load(client, token, snapshot, concurrency, interval_s):
    """Run sustained moderate load for the given interval."""
    headers = {"Authorization": f"Bearer {token}"}
    sem = asyncio.Semaphore(concurrency)
    target_requests = concurrency * 2
    interval = interval_s / target_requests

    endpoints = [
        ("GET", f"{BASE_URL}/api/v1/companies/{COMPANY_ID}"),
        ("GET", f"{BASE_URL}/api/v1/dashboard"),
        ("GET", f"{BASE_URL}/health"),
        ("POST", f"{BASE_URL}/api/v1/search", {"query": random.choice(SEARCH_QUERIES), "limit": 5}),
    ]

    async def _hit():
        async with sem:
            method, url, *rest = random.choice(endpoints)
            body = rest[0] if rest else None
            snapshot.total_requests += 1
            try:
                if method == "GET":
                    status, elapsed = await client.get(url, headers=headers)
                else:
                    status, elapsed = await client.post(url, json=body, headers=headers)
                snapshot.latencies.append(elapsed)
                if status >= 400:
                    snapshot.errors += 1
            except Exception:
                snapshot.errors += 1

    tasks = []
    for i in range(target_requests):
        tasks.append(asyncio.create_task(_hit()))
        if (i + 1) % 10 == 0:
            await asyncio.sleep(interval)
    await asyncio.gather(*tasks)


def print_hourly_report(snapshot, prev_snapshot=None):
    d = snapshot.to_dict()
    print(f"  Hour {snapshot.hour:>3} | "
          f"reqs={d['total_requests']:>5} | "
          f"err={d['error_rate_pct']:>5.1f}% | "
          f"p50={d['p50_ms']:>6.0f}ms | "
          f"p95={d['p95_ms']:>6.0f}ms | "
          f"rps={d['throughput_rps']:>5.0f} | "
          f"db_pool={d['db_pool_checked_out']}/{d['db_pool_total']} | "
          f"cache={d['cache_hit_rate_pct']:.0f}% | "
          f"ws={d['ws_active']} | "
          f"mem={d['memory_mb']:.0f}MB")

    if prev_snapshot:
        alerts = []
        if snapshot.pool_checked_out > prev_snapshot.pool_checked_out * 1.5 and snapshot.pool_checked_out > 15:
            alerts.append(f"DB POOL GROWTH: {prev_snapshot.pool_checked_out} -> {snapshot.pool_checked_out}")
        if snapshot.cache_hit_rate < 50 and prev_snapshot.cache_hit_rate > 70:
            alerts.append(f"CACHE DEGRADATION: {prev_snapshot.cache_hit_rate:.0f}% -> {snapshot.cache_hit_rate:.0f}%")
        if snapshot.errors > prev_snapshot.errors * 1.5 and prev_snapshot.errors > 0:
            alerts.append(f"ERROR RATE SPIKE: {prev_snapshot.error_rate:.1f}% -> {snapshot.error_rate:.1f}%")
        if snapshot.memory_bytes > 0 and prev_snapshot.memory_bytes > 0:
            mem_growth = (snapshot.memory_bytes - prev_snapshot.memory_bytes) / prev_snapshot.memory_bytes * 100
            if mem_growth > 10:
                alerts.append(f"MEMORY LEAK SUSPECTED: +{mem_growth:.1f}% ({prev_snapshot.memory_bytes/1024/1024:.0f}MB -> {snapshot.memory_bytes/1024/1024:.0f}MB)")
        for alert in alerts:
            print(f"  >>> ALERT: {alert}")


def main():
    parser = argparse.ArgumentParser(description="SalesOS Soak Test")
    parser.add_argument("--duration", type=int, default=14400, help="Duration in seconds (default: 14400 = 4h)")
    parser.add_argument("--users", type=int, default=50, help="Concurrent users (default: 50)")
    parser.add_argument("--output", type=str, default="soak-test-results.json")
    args = parser.parse_args()

    hours = args.duration // 3600
    print(f"\nSalesOS Soak Test")
    print(f"Target:  {BASE_URL}")
    print(f"Duration: {args.duration}s ({hours}h)")
    print(f"Users:   {args.users} concurrent")
    print("-" * 90)

    async def run():
        snapshots = []
        prev = None

        async with make_client() as client:
            token = await get_token(client)
            if not token:
                print("ERROR: Authentication failed")
                sys.exit(1)
            print(f"Token acquired\n")

            hour_num = 0
            start_time = time.time()
            while time.time() - start_time < args.duration:
                hour_num += 1
                print(f"[Hour {hour_num}/{hours}]", flush=True)

                snap = HourSnapshot(hour=hour_num, timestamp=time.time())

                await run_sustained_load(client, token, snap, args.users, 300)

                metrics = await fetch_server_metrics(client, token)
                snap.pool_checked_out = metrics.get("pool_checked_out", 0)
                snap.pool_total = metrics.get("pool_total", 0)
                snap.cache_hits = metrics.get("cache_hits", 0)
                snap.cache_misses = metrics.get("cache_misses", 0)
                snap.ws_active = metrics.get("ws_active", 0)
                snap.memory_bytes = metrics.get("memory_bytes", 0)

                snap.elapsed = time.time() - snap.timestamp
                snapshots.append(snap)
                print_hourly_report(snap, prev)
                prev = snap
                print()

        report = {
            "meta": {
                "target": BASE_URL,
                "start_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(start_time)),
                "end_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "duration_s": int(time.time() - start_time),
                "concurrent_users": args.users,
                "total_hours": len(snapshots),
            },
            "hourly_reports": [s.to_dict() for s in snapshots],
            "summary": {
                "total_requests": sum(s.total_requests for s in snapshots),
                "total_errors": sum(s.errors for s in snapshots),
                "avg_error_rate_pct": round(sum(s.error_rate for s in snapshots) / len(snapshots), 2) if snapshots else 0,
                "peak_p95_ms": round(max(s.p95 for s in snapshots), 1) if snapshots else 0,
                "memory_growth": round(
                    (snapshots[-1].memory_bytes - snapshots[0].memory_bytes) / snapshots[0].memory_bytes * 100, 1
                ) if snapshots and snapshots[0].memory_bytes else 0,
            },
        }

        with open(args.output, "w") as f:
            json.dump(report, f, indent=2)

        print(f"{'=' * 90}")
        print(f"  SOAK TEST COMPLETE")
        print(f"  Duration: {len(snapshots)} hours")
        print(f"  Total requests: {report['summary']['total_requests']}")
        print(f"  Avg error rate: {report['summary']['avg_error_rate_pct']}%")
        print(f"  Peak p95: {report['summary']['peak_p95_ms']}ms")
        print(f"  Memory growth: {report['summary']['memory_growth']}%")
        print(f"  Report: {args.output}")
        print(f"{'=' * 90}")

    asyncio.run(run())


if __name__ == "__main__":
    main()
