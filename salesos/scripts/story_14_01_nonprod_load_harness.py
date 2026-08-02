#!/usr/bin/env python3
"""STORY-14-01 — DevOps non-prod 50-tenant load harness (pairs with BE /api/v1/load).

Modes:
  companion  — run BE MemLoadSloHarness locally (CI synthetic; no live traffic)
  http       — call tip HTTP /api/v1/load/* against an explicit non-prod base URL

Forbidden:
  - Production GO claims
  - Live prod kill / traffic against known prod hosts
  - Stage 6 GHCR reopen

Usage:
  python scripts/story_14_01_nonprod_load_harness.py --mode companion
  SALESOS_BASE_URL=http://localhost:8000 SALESOS_TOKEN=... \\
    python scripts/story_14_01_nonprod_load_harness.py --mode http
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

# Allow `python scripts/...` from salesos/ without installing the package.
_BACKEND = Path(__file__).resolve().parents[1] / "backend"
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))


def _ensure_namespace(name: str, path: Path) -> None:
    """Register a namespace package so `app/__init__.py` (redis/etc.) is not loaded."""
    import types

    if name in sys.modules:
        return
    mod = types.ModuleType(name)
    mod.__path__ = [str(path)]  # type: ignore[attr-defined]
    mod.__package__ = name
    sys.modules[name] = mod


def _bootstrap_load_slo_imports() -> None:
    """Import load_slo without host Poetry/redis (Windows low-load path)."""
    app_dir = _BACKEND / "app"
    _ensure_namespace("app", app_dir)
    _ensure_namespace("app.modules", app_dir / "modules")
    _ensure_namespace("app.modules.load_slo", app_dir / "modules" / "load_slo")


# Host substrings that must never be targeted by this harness.
_PROD_HOST_MARKERS = (
    "salesos.app",
    "aqliya.com",
    "prod.railway",
    "railway.app",  # DEC-149 single-env — treat as live; require --allow-deployed-nonprod
)


def _honesty() -> dict[str, Any]:
    return {
        "story": "STORY-14-01",
        "target_tenants": 50,
        "live_prod_kill": False,
        "production_go": False,
        "stage6_ghcr": "SKIPPED (DEC-150 B)",
        "field_2h_soak": False,
        "validation": "light validated (companion) / not validated (field soak)",
    }


def _reject_prod_url(base_url: str, *, allow_deployed_nonprod: bool) -> None:
    lowered = (base_url or "").strip().lower()
    if not lowered:
        raise SystemExit("ERROR: SALESOS_BASE_URL / --base-url required for --mode http")
    if "localhost" in lowered or "127.0.0.1" in lowered or "0.0.0.0" in lowered:
        return
    if allow_deployed_nonprod:
        print(
            "WARN: --allow-deployed-nonprod set — operator asserts non-prod target. "
            "Still not Production GO.",
            file=sys.stderr,
        )
        return
    for marker in _PROD_HOST_MARKERS:
        if marker in lowered:
            raise SystemExit(
                f"REFUSED: base_url looks deployed/live ({marker!r}). "
                "Use localhost or pass --allow-deployed-nonprod only for explicit "
                "non-prod staging after operator confirmation. No live prod kill."
            )


def run_companion() -> dict[str, Any]:
    _bootstrap_load_slo_imports()
    from app.modules.load_slo.harness import MemLoadSloHarness
    from app.modules.load_slo.targets import (
        ERROR_RATE_MAX,
        LOAD_PROFILES,
        P95_LATENCY_MS_MAX,
        TARGET_TENANTS,
    )

    harness = MemLoadSloHarness()
    reports = harness.run_all()
    return {
        "mode": "companion",
        "ok": all(r.ok for r in reports),
        "target_tenants": TARGET_TENANTS,
        "slo": {
            "p95_latency_ms_max": P95_LATENCY_MS_MAX,
            "error_rate_max": ERROR_RATE_MAX,
        },
        "profiles": sorted(LOAD_PROFILES),
        "runs": [r.as_dict() for r in reports],
        "remediation": harness.latest_remediation(),
        "postmortems": [p.as_dict() for p in harness.list_postmortems()],
        "honesty": _honesty(),
    }


def _http_json(
    method: str,
    url: str,
    *,
    token: str,
    body: dict[str, Any] | None = None,
) -> Any:
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
    )
    with urlopen(req, timeout=60) as resp:  # noqa: S310 — operator-supplied base URL
        raw = resp.read().decode("utf-8")
        return json.loads(raw) if raw else None


def run_http(base_url: str, token: str) -> dict[str, Any]:
    root = base_url.rstrip("/")
    meta = _http_json("GET", f"{root}/api/v1/load/meta", token=token)
    runs = _http_json("POST", f"{root}/api/v1/load/run-all", token=token)
    remediation = _http_json("GET", f"{root}/api/v1/load/remediation", token=token)
    postmortems = _http_json("GET", f"{root}/api/v1/load/postmortems", token=token)
    ok = bool(runs) and all(bool(r.get("ok")) for r in runs)
    return {
        "mode": "http",
        "ok": ok,
        "base_url": root,
        "meta": meta,
        "runs": runs,
        "remediation": remediation,
        "postmortems": postmortems,
        "honesty": _honesty(),
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="STORY-14-01 DevOps non-prod 50-tenant load harness"
    )
    p.add_argument(
        "--mode",
        choices=("companion", "http"),
        default="companion",
        help="companion=local BE harness; http=tip /api/v1/load",
    )
    p.add_argument(
        "--base-url",
        default=os.getenv("SALESOS_BASE_URL", "http://localhost:8000"),
        help="Non-prod API base (http mode)",
    )
    p.add_argument(
        "--token",
        default=os.getenv("SALESOS_TOKEN", ""),
        help="Bearer token (http mode); or set SALESOS_TOKEN",
    )
    p.add_argument(
        "--allow-deployed-nonprod",
        action="store_true",
        help="Operator asserts deployed URL is non-prod (still no Production GO)",
    )
    p.add_argument(
        "--output",
        default="",
        help="Optional JSON output path",
    )
    args = p.parse_args(argv)

    print("STORY-14-01 non-prod load harness")
    print(f"mode={args.mode}  production_go=False  live_prod_kill=False")
    print("-" * 60)

    try:
        if args.mode == "companion":
            result = run_companion()
        else:
            _reject_prod_url(
                args.base_url, allow_deployed_nonprod=args.allow_deployed_nonprod
            )
            if not args.token:
                raise SystemExit(
                    "ERROR: --token or SALESOS_TOKEN required for --mode http"
                )
            result = run_http(args.base_url, args.token)
    except HTTPError as exc:
        print(f"HTTP ERROR: {exc.code} {exc.reason}", file=sys.stderr)
        return 2
    except URLError as exc:
        print(f"URL ERROR: {exc.reason}", file=sys.stderr)
        return 2
    except ImportError as exc:
        print(
            f"IMPORT ERROR: BE load_slo companion not importable ({exc}). "
            "Pair with Backend tip land of app.modules.load_slo.",
            file=sys.stderr,
        )
        return 3

    text = json.dumps(result, indent=2, sort_keys=True)
    print(text)
    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text + "\n", encoding="utf-8")
        print(f"wrote {out}")

    if result.get("ok"):
        print("\nRESULT: SLOs held on companion/http profile (not Production GO)")
        return 0
    print("\nRESULT: needs_remediation — see remediation plan (not Production GO)")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
