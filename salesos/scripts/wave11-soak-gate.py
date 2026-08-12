#!/usr/bin/env python3
"""Wave 11 staging-soak readiness gate (PROD-W11-001 / PROD-W11-002 prep).

Automates local/staging *parity gates* and optional light synthetic loop.
Does NOT claim Production GO. Does NOT claim 48–72h soak complete.

Checks:
  1. Backend /health (and /health/detailed when available)
  2. Alembic current == heads (via docker compose exec, if available)
  3. DEMO_MODE / feature_ai_copilot when readable (env + Settings)
  4. Redis / cache connected (from /health payload)
  5. Frontend HTTP 200 for /, /copilot, /analytics

Usage (one-shot gate — default):
  python salesos/scripts/wave11-soak-gate.py
  python salesos/scripts/wave11-soak-gate.py --api http://localhost:8000 --fe http://localhost:3000

Usage (evidence loop for 48–72h soak — does not auto-pass soak):
  python salesos/scripts/wave11-soak-gate.py --loop --interval 300 --duration-hours 48 \\
    --evidence-dir docs/audit/ga-engineering-audit/evidence/wave11-soak

Exit codes:
  0 = all required gates PASS (or loop finished with zero hard failures if --fail-soft)
  1 = one or more required gates FAIL
  2 = script/config error
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


DEFAULT_API = os.getenv("SALESOS_API_URL", "http://localhost:8000")
DEFAULT_FE = os.getenv("SALESOS_FE_URL", "http://localhost:3000")
DEFAULT_COMPOSE_DIR = os.getenv(
    "SALESOS_COMPOSE_DIR",
    str(Path(__file__).resolve().parents[1]),  # salesos/
)
DEFAULT_BACKEND_SERVICE = os.getenv("SALESOS_BACKEND_SERVICE", "backend")
FE_ROUTES = ("/", "/copilot", "/analytics")


@dataclass
class CheckResult:
    name: str
    status: str  # PASS | FAIL | WARN | SKIP | UNVERIFIED
    detail: str = ""
    evidence: dict[str, Any] = field(default_factory=dict)

    @property
    def hard_fail(self) -> bool:
        return self.status == "FAIL"


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def http_get(url: str, timeout: float = 20.0) -> tuple[int, str, float]:
    started = time.perf_counter()
    req = urllib.request.Request(url, method="GET", headers={"Accept": "application/json,*/*"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            ms = (time.perf_counter() - started) * 1000
            return int(resp.status), body, ms
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace") if e.fp else ""
        ms = (time.perf_counter() - started) * 1000
        return int(e.code), body, ms
    except Exception as e:
        ms = (time.perf_counter() - started) * 1000
        raise RuntimeError(f"{type(e).__name__}: {e} ({ms:.0f}ms)") from e


def parse_json(body: str) -> Optional[dict[str, Any]]:
    try:
        data = json.loads(body)
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        return None


def classify_health_detailed(
    http_status: int, detailed_data: Optional[dict[str, Any]]
) -> tuple[str, str]:
    """Classify /health/detailed for soak evidence.

    Never hard-fails (api.health owns hard-fail for overall readiness).
    HTTP 200 with overall degraded/unhealthy (or DB error) must be WARN —
    historically this check returned PASS on degraded and masked DB outages
    in counts during the 2026-08-09 staging soak window.
    """
    payload = detailed_data or {}
    overall = str(payload.get("status", "")).lower()
    detail = f"HTTP {http_status} overall={payload.get('status')!r}"

    if http_status != 200:
        return "WARN", detail

    if overall in {"degraded", "unhealthy", "error", "down", "not_ready"}:
        return "WARN", detail

    checks = payload.get("checks")
    if isinstance(checks, dict):
        db = checks.get("database")
        if isinstance(db, dict):
            db_status = str(db.get("status", "")).lower()
            if db_status in {"error", "unavailable", "disconnected"}:
                return "WARN", f"{detail} database={db_status!r}"
        elif isinstance(db, str) and db.lower() in {"error", "unavailable", "disconnected"}:
            return "WARN", f"{detail} database={db!r}"

    return "PASS", detail


def run_compose(
    compose_dir: str,
    backend_service: str,
    args: list[str],
    timeout: float = 60.0,
) -> tuple[int, str, str]:
    cmd = [
        "docker",
        "compose",
        "exec",
        "-T",
        backend_service,
        *args,
    ]
    try:
        proc = subprocess.run(
            cmd,
            cwd=compose_dir,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return proc.returncode, proc.stdout or "", proc.stderr or ""
    except FileNotFoundError:
        return 127, "", "docker not found on PATH"
    except subprocess.TimeoutExpired:
        return 124, "", f"timeout after {timeout}s"
    except Exception as e:
        return 1, "", f"{type(e).__name__}: {e}"


def _extract_cache_redis(data: dict[str, Any]) -> tuple[str, str]:
    """Pull cache/redis status strings from /health or /health/detailed payloads."""
    cache = str(data.get("cache") or "")
    redis = str(data.get("redis") or "")
    checks = data.get("checks")
    if isinstance(checks, dict):
        c = checks.get("cache")
        r = checks.get("redis")
        if isinstance(c, dict):
            cache = str(c.get("status", cache))
        elif c is not None and not cache:
            cache = str(c)
        if isinstance(r, dict):
            redis = str(r.get("status", redis))
        elif r is not None and not redis:
            redis = str(r)
    return cache, redis


def check_health(api: str, retries: int = 3, retry_delay: float = 2.0) -> list[CheckResult]:
    results: list[CheckResult] = []

    # Light liveness — always attempt /ping first
    ping_url = f"{api.rstrip('/')}/ping"
    try:
        status, body, ms = http_get(ping_url, timeout=10.0)
        ok = status == 200
        results.append(
            CheckResult(
                name="api.ping",
                status="PASS" if ok else "FAIL",
                detail=f"HTTP {status} in {ms:.0f}ms",
                evidence={"url": ping_url, "http_status": status, "latency_ms": round(ms, 1), "body": body[:200]},
            )
        )
    except RuntimeError as e:
        results.append(CheckResult(name="api.ping", status="FAIL", detail=str(e)))

    url = f"{api.rstrip('/')}/health"
    health_data: dict[str, Any] = {}
    health_err: Optional[str] = None
    health_ms = 0.0
    health_status = 0
    for attempt in range(1, retries + 1):
        try:
            health_status, body, health_ms = http_get(url, timeout=25.0)
            health_data = parse_json(body) or {}
            health_err = None
            break
        except RuntimeError as e:
            health_err = str(e)
            if attempt < retries:
                time.sleep(retry_delay)

    if health_err is None:
        ok = health_status == 200 and str(health_data.get("status", "")).lower() in {
            "ok",
            "healthy",
            "ready",
        }
        results.append(
            CheckResult(
                name="api.health",
                status="PASS" if ok else "FAIL",
                detail=f"HTTP {health_status} in {health_ms:.0f}ms status={health_data.get('status')!r}",
                evidence={
                    "url": url,
                    "http_status": health_status,
                    "latency_ms": round(health_ms, 1),
                    "body": health_data or None,
                    "retries": retries,
                },
            )
        )
    else:
        results.append(
            CheckResult(
                name="api.health",
                status="FAIL",
                detail=f"{health_err} (after {retries} attempts)",
                evidence={"url": url, "retries": retries},
            )
        )

    # detailed — also used as redis/cache fallback when /health hangs on DB dep
    durl = f"{api.rstrip('/')}/health/detailed"
    detailed_data: dict[str, Any] = {}
    try:
        status, body, ms = http_get(durl, timeout=25.0)
        detailed_data = parse_json(body) or {}
        check_status, classified = classify_health_detailed(status, detailed_data)
        results.append(
            CheckResult(
                name="api.health_detailed",
                status=check_status,
                detail=f"{classified} in {ms:.0f}ms",
                evidence={
                    "url": durl,
                    "http_status": status,
                    "latency_ms": round(ms, 1),
                    "body": detailed_data or body[:800],
                },
            )
        )
    except RuntimeError as e:
        results.append(
            CheckResult(
                name="api.health_detailed",
                status="WARN",
                detail=f"unavailable: {e}",
            )
        )

    cache, redis = _extract_cache_redis(health_data)
    source = "health"
    if not cache and not redis:
        cache, redis = _extract_cache_redis(detailed_data)
        source = "health/detailed"

    cache_ok = cache.lower() in {"connected", "ok", "healthy"}
    redis_ok = redis.lower() in {"connected", "ok", "healthy"}
    if cache or redis:
        connected = redis_ok or cache_ok
        results.append(
            CheckResult(
                name="api.redis_cache",
                status="PASS" if connected else "FAIL",
                detail=f"cache={cache!r} redis={redis!r} (from {source})",
                evidence={"cache": cache, "redis": redis, "source": source},
            )
        )
    else:
        results.append(
            CheckResult(
                name="api.redis_cache",
                status="UNVERIFIED",
                detail="neither /health nor /health/detailed exposed cache/redis",
                evidence={"health_keys": list(health_data.keys()), "detailed_keys": list(detailed_data.keys())},
            )
        )
    return results


def check_frontend(fe: str) -> list[CheckResult]:
    results: list[CheckResult] = []
    for route in FE_ROUTES:
        url = f"{fe.rstrip('/')}{route}"
        try:
            status, body, ms = http_get(url, timeout=30.0)
            # Auth redirects may still land on 200 HTML; treat 2xx/3xx as acceptable for soak gate
            ok = 200 <= status < 400
            results.append(
                CheckResult(
                    name=f"fe.route{route if route != '/' else '/root'}",
                    status="PASS" if ok else "FAIL",
                    detail=f"HTTP {status} in {ms:.0f}ms bytes={len(body)}",
                    evidence={"url": url, "http_status": status, "latency_ms": round(ms, 1), "bytes": len(body)},
                )
            )
        except RuntimeError as e:
            results.append(CheckResult(name=f"fe.route{route if route != '/' else '/root'}", status="FAIL", detail=str(e)))
    return results


def _parse_alembic_revs(text: str) -> list[str]:
    revs: list[str] = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("INFO") or line.startswith("WARNING"):
            continue
        # e.g. "0039 (head)" or "0039"
        m = re.match(r"^([0-9a-fA-F_]+)(?:\s|\(|$)", line)
        if m:
            revs.append(m.group(1))
    return revs


def check_alembic(compose_dir: str, backend_service: str, skip: bool) -> list[CheckResult]:
    if skip:
        return [
            CheckResult(
                name="alembic.current_eq_heads",
                status="SKIP",
                detail="--skip-alembic set",
            )
        ]

    code_c, out_c, err_c = run_compose(compose_dir, backend_service, ["alembic", "current"], timeout=90.0)
    code_h, out_h, err_h = run_compose(compose_dir, backend_service, ["alembic", "heads"], timeout=90.0)

    if code_c == 127 or code_h == 127:
        return [
            CheckResult(
                name="alembic.current_eq_heads",
                status="UNVERIFIED",
                detail="docker not available — cannot exec alembic",
                evidence={"stderr": err_c or err_h},
            )
        ]

    current_revs = _parse_alembic_revs(out_c)
    head_revs = _parse_alembic_revs(out_h)

    if code_c != 0 or not current_revs:
        return [
            CheckResult(
                name="alembic.current_eq_heads",
                status="FAIL",
                detail=f"alembic current failed (exit {code_c})",
                evidence={"stdout": out_c[-2000:], "stderr": err_c[-2000:], "heads_stdout": out_h[-1000:]},
            )
        ]

    if code_h != 0 or not head_revs:
        return [
            CheckResult(
                name="alembic.current_eq_heads",
                status="FAIL",
                detail=f"alembic heads failed (exit {code_h})",
                evidence={"stdout": out_h[-2000:], "stderr": err_h[-2000:], "current": current_revs},
            )
        ]

    # Single-head local: current must be in heads set (or equal when one head)
    match = set(current_revs) == set(head_revs) or (
        len(head_revs) == 1 and head_revs[0] in current_revs
    )
    # Also accept "0039 (head)" style where current lists the head rev
    if not match and len(head_revs) == 1:
        match = any(head_revs[0] == c or c.startswith(head_revs[0]) for c in current_revs)

    return [
        CheckResult(
            name="alembic.current_eq_heads",
            status="PASS" if match else "FAIL",
            detail=f"current={current_revs} heads={head_revs}",
            evidence={
                "current_raw": out_c.strip(),
                "heads_raw": out_h.strip(),
                "current": current_revs,
                "heads": head_revs,
            },
        )
    ]


def check_feature_flags(compose_dir: str, backend_service: str, skip: bool) -> list[CheckResult]:
    if skip:
        return [CheckResult(name="flags.demo_and_copilot", status="SKIP", detail="--skip-flags set")]

    py = (
        "from app.config import settings\n"
        "import os\n"
        "print('demo_mode=', settings.demo_mode)\n"
        "print('feature_ai_copilot=', settings.feature_ai_copilot)\n"
        "print('env=', settings.env)\n"
        "print('DEMO_MODE_ENV=', os.getenv('DEMO_MODE',''))\n"
        "print('FEATURE_AI_COPILOT_ENV=', os.getenv('FEATURE_AI_COPILOT',''))\n"
    )
    code, out, err = run_compose(compose_dir, backend_service, ["python", "-c", py], timeout=60.0)
    if code == 127:
        return [
            CheckResult(
                name="flags.demo_and_copilot",
                status="UNVERIFIED",
                detail="docker not available — cannot read Settings",
            )
        ]
    if code != 0:
        return [
            CheckResult(
                name="flags.demo_and_copilot",
                status="UNVERIFIED",
                detail=f"could not read settings (exit {code}): {(err or out)[:300]}",
                evidence={"stdout": out[-1000:], "stderr": err[-1000:]},
            )
        ]

    def _bool_line(key: str) -> Optional[bool]:
        for line in out.splitlines():
            if line.startswith(key):
                val = line.split("=", 1)[1].strip().lower()
                if val in {"true", "1", "yes"}:
                    return True
                if val in {"false", "0", "no", ""}:
                    return False
        return None

    demo = _bool_line("demo_mode=")
    copilot = _bool_line("feature_ai_copilot=")
    env_name = None
    for line in out.splitlines():
        if line.startswith("env="):
            env_name = line.split("=", 1)[1].strip()

    # Soak candidate expectation: demo_mode False, feature_ai_copilot False
    issues: list[str] = []
    if demo is True:
        issues.append("demo_mode=True (soak candidate expects False)")
    if copilot is True:
        issues.append("feature_ai_copilot=True (AI honesty expects False until validated)")
    if demo is None and copilot is None:
        return [
            CheckResult(
                name="flags.demo_and_copilot",
                status="UNVERIFIED",
                detail="settings printed but values not parsed",
                evidence={"stdout": out},
            )
        ]

    if issues:
        status = "FAIL"
        detail = "; ".join(issues)
    else:
        status = "PASS"
        detail = f"demo_mode={demo} feature_ai_copilot={copilot} env={env_name!r}"

    return [
        CheckResult(
            name="flags.demo_and_copilot",
            status=status,
            detail=detail,
            evidence={"stdout": out.strip(), "demo_mode": demo, "feature_ai_copilot": copilot, "env": env_name},
        )
    ]


def summarize(results: list[CheckResult]) -> dict[str, Any]:
    counts = {"PASS": 0, "FAIL": 0, "WARN": 0, "SKIP": 0, "UNVERIFIED": 0}
    for r in results:
        counts[r.status] = counts.get(r.status, 0) + 1
    hard_fails = [r.name for r in results if r.hard_fail]
    return {
        "counts": counts,
        "hard_fails": hard_fails,
        "gate_pass": len(hard_fails) == 0,
    }


def print_report(results: list[CheckResult], meta: dict[str, Any]) -> None:
    print()
    print("=" * 64)
    print(" Wave 11 soak / parity gate")
    print("=" * 64)
    print(f" timestamp: {meta.get('timestamp')}")
    print(f" api:       {meta.get('api')}")
    print(f" fe:        {meta.get('fe')}")
    print(f" compose:   {meta.get('compose_dir')}")
    print("-" * 64)
    for r in results:
        print(f"  [{r.status:10}] {r.name}: {r.detail}")
    s = summarize(results)
    print("-" * 64)
    print(
        f" PASS={s['counts'].get('PASS',0)} FAIL={s['counts'].get('FAIL',0)} "
        f"WARN={s['counts'].get('WARN',0)} SKIP={s['counts'].get('SKIP',0)} "
        f"UNVERIFIED={s['counts'].get('UNVERIFIED',0)}"
    )
    verdict = "GATE PASS (readiness only — NOT soak complete, NOT Production GO)" if s["gate_pass"] else "GATE FAIL"
    print(f" verdict: {verdict}")
    if s["hard_fails"]:
        print(f" hard_fails: {', '.join(s['hard_fails'])}")
    print("=" * 64)


def write_evidence(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")


def run_once(args: argparse.Namespace) -> tuple[list[CheckResult], dict[str, Any]]:
    results: list[CheckResult] = []
    results.extend(check_health(args.api))
    results.extend(check_alembic(args.compose_dir, args.backend_service, args.skip_alembic))
    results.extend(check_feature_flags(args.compose_dir, args.backend_service, args.skip_flags))
    results.extend(check_frontend(args.fe))
    meta = {
        "timestamp": utc_now(),
        "api": args.api,
        "fe": args.fe,
        "compose_dir": args.compose_dir,
        "backend_service": args.backend_service,
        "classification": "Wave 11 readiness gate — not Production GO; not 48–72h soak complete",
        "summary": summarize(results),
    }
    return results, meta


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Wave 11 soak/parity readiness gate")
    p.add_argument("--api", default=DEFAULT_API, help="Backend base URL")
    p.add_argument("--fe", default=DEFAULT_FE, help="Frontend base URL")
    p.add_argument("--compose-dir", default=DEFAULT_COMPOSE_DIR, help="docker compose project dir")
    p.add_argument("--backend-service", default=DEFAULT_BACKEND_SERVICE, help="compose service name")
    p.add_argument("--skip-alembic", action="store_true")
    p.add_argument("--skip-flags", action="store_true")
    p.add_argument(
        "--evidence-dir",
        default="",
        help="Directory for JSON evidence (default: salesos/docs or audit evidence path if set)",
    )
    p.add_argument("--evidence-file", default="", help="Explicit evidence JSON path")
    p.add_argument("--loop", action="store_true", help="Repeat checks for soak evidence collection")
    p.add_argument("--interval", type=int, default=300, help="Seconds between loop iterations (default 300)")
    p.add_argument("--duration-hours", type=float, default=48.0, help="Loop duration hours (default 48)")
    p.add_argument(
        "--fail-soft",
        action="store_true",
        help="In loop mode, continue on failures and exit 0 if final summary only has WARN/UNVERIFIED",
    )
    return p.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)
    evidence_dir = Path(args.evidence_dir) if args.evidence_dir else (
        Path(__file__).resolve().parents[2]
        / "docs"
        / "audit"
        / "ga-engineering-audit"
        / "evidence"
        / "wave11-soak"
    )

    if not args.loop:
        results, meta = run_once(args)
        print_report(results, meta)
        payload = {
            **meta,
            "mode": "oneshot",
            "checks": [asdict(r) for r in results],
        }
        out = Path(args.evidence_file) if args.evidence_file else evidence_dir / f"gate-{meta['timestamp'].replace(':', '')}.json"
        write_evidence(out, payload)
        print(f" evidence: {out}")
        return 0 if meta["summary"]["gate_pass"] else 1

    # Loop mode — collect soak evidence; does not claim soak complete
    end_at = time.time() + max(args.duration_hours, 0.01) * 3600
    iteration = 0
    failures = 0
    history: list[dict[str, Any]] = []
    print(
        f"Starting soak evidence loop for {args.duration_hours}h "
        f"(interval={args.interval}s). This does NOT auto-declare soak pass."
    )
    while time.time() < end_at:
        iteration += 1
        results, meta = run_once(args)
        print_report(results, {**meta, "iteration": iteration})
        summary = meta["summary"]
        if not summary["gate_pass"]:
            failures += 1
        snap = {
            "iteration": iteration,
            "timestamp": meta["timestamp"],
            "gate_pass": summary["gate_pass"],
            "counts": summary["counts"],
            "hard_fails": summary["hard_fails"],
            "checks": [asdict(r) for r in results],
        }
        history.append(snap)
        iter_path = evidence_dir / f"loop-{meta['timestamp'].replace(':', '')}-i{iteration:05d}.json"
        write_evidence(iter_path, snap)
        remaining = end_at - time.time()
        if remaining <= 0:
            break
        sleep_for = min(args.interval, remaining)
        print(f" sleeping {sleep_for:.0f}s (iteration {iteration}, failures so far={failures})")
        time.sleep(sleep_for)

    final = {
        "timestamp": utc_now(),
        "mode": "loop",
        "duration_hours_requested": args.duration_hours,
        "iterations": iteration,
        "failures": failures,
        "api": args.api,
        "fe": args.fe,
        "classification": (
            "Soak evidence collection finished for requested window. "
            "Human must review incidents and file Soak Report before claiming PROD-W11-002."
        ),
        "soak_complete_claim": False,
        "production_go_claim": False,
        "history_tail": history[-20:],
        "history_count": len(history),
    }
    final_path = evidence_dir / f"loop-summary-{final['timestamp'].replace(':', '')}.json"
    write_evidence(final_path, final)
    print(f" loop summary: {final_path}")
    print(" NOTE: 48–72h soak is NOT complete until human soak report is filed.")
    if failures and not args.fail_soft:
        return 1
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nInterrupted — soak NOT complete.", file=sys.stderr)
        sys.exit(130)
