#!/usr/bin/env python3
"""STORY-14-01 — optional real wall-clock field soak (honest labeling).

Runs register→login token mint, then periodic HTTP harness against a deployed
non-prod URL for a wall-clock duration. Does NOT invent a 2h PASS if duration
is shorter. Does NOT claim Production GO / live prod kill / Companion acceptance.

Usage:
  python scripts/story_14_01_field_soak.py --duration-seconds 7200 --interval-seconds 600
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HARNESS = Path(__file__).resolve().parent / "story_14_01_nonprod_load_harness.py"
DEFAULT_BASE = "https://salesos-production-96c0.up.railway.app"


def _http_json(
    method: str,
    url: str,
    body: dict | None = None,
    token: str | None = None,
    timeout: float = 90,
):
    data = None if body is None else json.dumps(body).encode()
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode()
            return resp.status, (json.loads(raw) if raw else None), time.perf_counter() - t0
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors="replace")
        try:
            payload = json.loads(raw) if raw else None
        except json.JSONDecodeError:
            payload = {"raw": raw[:500]}
        return e.code, payload, time.perf_counter() - t0
    except TimeoutError:
        return 598, {"error": "timeout"}, time.perf_counter() - t0


def mint_login_token(base: str) -> tuple[str, str, dict]:
    """Prefer login JWT (register-only token may 401 load/meta intermittently)."""
    email = f"story1401.soak.{int(time.time())}@example.com"
    password = "LoadTest14-01!NpX9Soak"
    code, reg, elapsed = _http_json(
        "POST",
        f"{base}/api/v1/identity/register",
        {"email": email, "password": password, "full_name": "STORY-14-01 Field Soak"},
    )
    if code not in (200, 201) or not isinstance(reg, dict) or not reg.get("access_token"):
        raise SystemExit(f"REGISTER_FAIL status={code} elapsed={elapsed:.2f} body={reg!r}"[:500])
    code, login, elapsed = _http_json(
        "POST",
        f"{base}/api/v1/identity/login",
        {"email": email, "password": password},
    )
    if code != 200 or not isinstance(login, dict) or not login.get("access_token"):
        # Fall back to register token with honesty note
        return reg["access_token"], email, {
            "token_source": "register_fallback",
            "login_status": code,
            "register_ok": True,
        }
    return login["access_token"], email, {
        "token_source": "login",
        "login_elapsed_s": elapsed,
        "register_ok": True,
    }


def run_harness(base: str, token: str, out_path: Path) -> tuple[int, dict | None, str]:
    env = os.environ.copy()
    env["SALESOS_BASE_URL"] = base
    env["SALESOS_TOKEN"] = token
    proc = subprocess.run(
        [
            sys.executable,
            str(HARNESS),
            "--mode",
            "http",
            "--allow-deployed-nonprod",
            "--base-url",
            base,
            "--token",
            token,
            "--output",
            str(out_path),
        ],
        cwd=str(ROOT),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    payload = None
    if out_path.exists():
        try:
            payload = json.loads(out_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            payload = None
    err = (proc.stderr or "").strip()
    # Never echo tokens; stderr is HTTP ERROR / URL ERROR only from harness.
    return proc.returncode, payload, err[:800]


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="STORY-14-01 optional wall-clock field soak")
    p.add_argument("--base-url", default=os.getenv("SALESOS_BASE_URL", DEFAULT_BASE))
    p.add_argument("--duration-seconds", type=int, default=7200)
    p.add_argument("--interval-seconds", type=int, default=600)
    p.add_argument(
        "--evidence-dir",
        default=str(Path(__file__).resolve().parents[2] / ".tmp-1401-field-soak"),
    )
    args = p.parse_args(argv)

    evidence = Path(args.evidence_dir)
    evidence.mkdir(parents=True, exist_ok=True)
    start = datetime.now(timezone.utc)
    start_mono = time.monotonic()
    planned = int(args.duration_seconds)
    interval = max(30, int(args.interval_seconds))
    true_2h = planned >= 7200

    print("STORY-14-01 optional field soak")
    print(f"base_url={args.base_url}")
    print(f"start_utc={start.isoformat()}")
    print(f"planned_duration_seconds={planned} true_2h_wall_clock={true_2h}")
    print(f"interval_seconds={interval}")
    print("production_go=False live_prod_kill=False stage6_ghcr=SKIPPED")
    print(f"evidence_dir={evidence}")
    print("-" * 60)

    h_code, health, _ = _http_json("GET", f"{args.base_url.rstrip('/')}/health", timeout=30)
    print(f"HEALTH status={h_code} uptime={health.get('uptime_seconds') if isinstance(health, dict) else None}")

    # Remint login JWT each iteration — tip-line Railway rolls regenerate JWKS
    # and invalidate prior tokens mid-soak (field: attempt1 ITER2 exit 2 after
    # uptime reset ~417s during docs Deploy churn).
    iterations: list[dict] = []
    exit_worst = 0
    i = 0
    last_email = ""
    while True:
        elapsed = time.monotonic() - start_mono
        if elapsed >= planned and i > 0:
            break
        i += 1
        iter_started = datetime.now(timezone.utc)
        out = evidence / f"iter_{i:03d}_harness.json"
        print(f"ITER {i} start_utc={iter_started.isoformat()} elapsed_s={elapsed:.0f}")
        try:
            token, email, mint_meta = mint_login_token(args.base_url.rstrip("/"))
            last_email = email
            print(
                f"ITER {i} TOKEN_MINTED source={mint_meta.get('token_source')} "
                f"email={email} token_len={len(token)}"
            )
            (evidence / f"iter_{i:03d}_mint.json").write_text(
                json.dumps(
                    {"email": email, **mint_meta, "token_len": len(token)},
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
        except SystemExit as exc:
            print(f"ITER {i} MINT_FAIL {exc}")
            summary = {
                "iter": i,
                "started_utc": iter_started.isoformat(),
                "elapsed_since_soak_start_s": round(elapsed, 1),
                "harness_exit": 12,
                "ok": False,
                "field_2h_soak_claim": False,
                "profiles": [],
                "error": str(exc)[:300],
            }
            iterations.append(summary)
            exit_worst = 12
            (evidence / "progress.json").write_text(
                json.dumps(
                    {
                        "start_utc": start.isoformat(),
                        "planned_duration_seconds": planned,
                        "true_2h_wall_clock_planned": true_2h,
                        "iterations_completed": i,
                        "latest": summary,
                        "remint_each_iter": True,
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            elapsed = time.monotonic() - start_mono
            if elapsed >= planned:
                break
            time.sleep(min(interval, max(0, planned - elapsed)))
            continue

        rc, payload, harness_err = run_harness(args.base_url.rstrip("/"), token, out)
        if harness_err:
            (evidence / f"iter_{i:03d}_harness.stderr.txt").write_text(
                harness_err + "\n", encoding="utf-8"
            )
            print(f"ITER {i} harness_stderr={harness_err[:200]}")
        # One remint+retry on HTTP/CSRF flake (tip-line JWKS roll or missing CSRF).
        if rc != 0:
            print(f"ITER {i} harness_exit={rc} — remint+retry once")
            try:
                token, email, mint_meta = mint_login_token(args.base_url.rstrip("/"))
                last_email = email
                print(
                    f"ITER {i} RETRY_TOKEN source={mint_meta.get('token_source')} "
                    f"token_len={len(token)}"
                )
            except SystemExit as exc:
                print(f"ITER {i} RETRY_MINT_FAIL {exc}")
            else:
                retry_out = evidence / f"iter_{i:03d}_harness_retry.json"
                rc2, payload2, err2 = run_harness(
                    args.base_url.rstrip("/"), token, retry_out
                )
                if err2:
                    (evidence / f"iter_{i:03d}_harness_retry.stderr.txt").write_text(
                        err2 + "\n", encoding="utf-8"
                    )
                    print(f"ITER {i} retry_stderr={err2[:200]}")
                if rc2 == 0:
                    rc, payload, harness_err = rc2, payload2, err2
                    out = retry_out
        ok = bool(payload and payload.get("ok")) if payload else rc == 0
        summary = {
            "iter": i,
            "started_utc": iter_started.isoformat(),
            "elapsed_since_soak_start_s": round(elapsed, 1),
            "harness_exit": rc,
            "ok": ok,
            "field_2h_soak_claim": False,
            "token_source": mint_meta.get("token_source"),
            "harness_stderr": (harness_err or "")[:200] or None,
            "profiles": [],
        }
        if isinstance(payload, dict):
            for r in payload.get("runs") or []:
                summary["profiles"].append(
                    {
                        "profile": r.get("profile"),
                        "ok": r.get("ok"),
                        "within_slo": r.get("within_slo"),
                        "p95_latency_ms": r.get("p95_latency_ms"),
                        "error_rate": r.get("error_rate"),
                    }
                )
        iterations.append(summary)
        print(f"ITER {i} exit={rc} ok={ok}")
        (evidence / "progress.json").write_text(
            json.dumps(
                {
                    "start_utc": start.isoformat(),
                    "planned_duration_seconds": planned,
                    "true_2h_wall_clock_planned": true_2h,
                    "iterations_completed": i,
                    "latest": summary,
                    "remint_each_iter": True,
                    "restart_note": "attempt2: remint each iter after attempt1 ITER2 fail on JWKS/uptime reset",
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        if rc != 0:
            exit_worst = rc if exit_worst == 0 else exit_worst
        elapsed = time.monotonic() - start_mono
        if elapsed >= planned:
            break
        sleep_for = min(interval, max(0, planned - elapsed))
        if sleep_for > 0:
            time.sleep(sleep_for)

    end = datetime.now(timezone.utc)
    wall = time.monotonic() - start_mono
    achieved_2h = wall >= 7200 - 30  # 30s tolerance
    final = {
        "story": "STORY-14-01",
        "mode": "optional_wall_clock_field_soak",
        "base_url": args.base_url,
        "start_utc": start.isoformat(),
        "end_utc": end.isoformat(),
        "planned_duration_seconds": planned,
        "actual_wall_clock_seconds": round(wall, 1),
        "true_2h_wall_clock_planned": true_2h,
        "true_2h_wall_clock_achieved": achieved_2h,
        "field_2h_soak": achieved_2h,
        "interval_seconds": interval,
        "remint_each_iter": True,
        "iterations": iterations,
        "all_iters_ok": all(x.get("ok") for x in iterations) if iterations else False,
        "honesty": {
            "production_go": False,
            "live_prod_kill": False,
            "stage6_ghcr": "SKIPPED (DEC-150 B)",
            "companion_acceptance": False,
            "note": (
                "Periodic auth-gated HTTP harness over wall-clock duration; "
                "not continuous k6/locust 50-tenant live traffic. "
                "Login JWT reminted each iteration (JWKS rotates on Railway roll). "
                "Do not invent 2h PASS unless true_2h_wall_clock_achieved."
            ),
        },
        "mint_policy": {
            "remint_each_iter": True,
            "last_email": last_email,
        },
        "health_at_start": health if isinstance(health, dict) else {"status_code": h_code},
    }
    final_path = evidence / "soak_final.json"
    final_path.write_text(json.dumps(final, indent=2) + "\n", encoding="utf-8")
    print("-" * 60)
    print(f"wrote {final_path}")
    print(
        f"RESULT wall_s={wall:.0f} planned_s={planned} "
        f"true_2h_achieved={achieved_2h} all_ok={final['all_iters_ok']} "
        f"production_go=False"
    )
    if not iterations:
        return 2
    if not final["all_iters_ok"]:
        return exit_worst or 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
