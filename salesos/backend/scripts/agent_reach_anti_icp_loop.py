"""8-hour ANTI-ICP-only Agent Reach contact-enrichment loop.

Review-only: plans 8 non-overlapping shards, staggers worker starts, merges
into a new workbook each cycle, and inspects ready rows. Never writes the
production DB, original master CSV, or prior patch directories.
"""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
import time
from collections import Counter
from datetime import UTC, datetime, timedelta
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
BACKEND_ROOT = SCRIPTS_DIR.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from agent_reach_parallel_contact_enrichment import (  # noqa: E402
    build_worker_command,
    collect_worker_results,
    merge_worker_results,
    shards_overlap,
    split_shards,
    write_merge_outputs,
    write_plan,
)

from app.modules.agent_reach.contact_enrichment import (  # noqa: E402
    INSTAGRAM_RESERVED_FIRST_SEGMENTS,
    MARKDOWN_IMAGE_ARTIFACT,
    PLATFORM_LINKEDIN_SLUGS,
    TRACKING_SUBDOMAINS,
    TWITTER_RESERVED_FIRST_SEGMENTS,
    EnrichmentCandidate,
    EnrichmentRow,
    _has_concatenated_http,
    _linkedin_compact_slug,
    _linkedin_entity_token,
    _normalize_linkedin_url,
    _normalize_phone,
    _normalize_twitter_profile_url,
    _normalize_whatsapp_url,
    _safe_urlparse,
    load_master_candidates,
    load_processed_accounts,
    sanitize_ready_url_value,
)

OTHER_PENDING_TIERS = ("CLASS A", "TIER B", "TIER C", "TIER D", "UNKNOWN")
REPEATED_FP_THRESHOLD = 2
DEFAULT_CYCLE_OVERHEAD_SECONDS = 180.0
PHONE_FIELDS = frozenset({"جوال", "هاتف"})
WHATSAPP_FIELDS = frozenset({"واتساب"})
TWITTER_FIELDS = frozenset({"تويتر", "تويتر/X", "تويتر/اكس"})
LINKEDIN_FIELDS = frozenset({"لينكدإن", "لينكدان"})
INSTAGRAM_FIELDS = frozenset({"انستقرام", "إنستغرام", "انستغرام"})
SOCIAL_HOST_HINTS = (
    "facebook.com",
    "instagram.com",
    "linkedin.com",
    "tiktok.com",
    "twitter.com",
    "x.com",
    "youtube.com",
    "snapchat.com",
    "wa.me",
    "whatsapp.com",
)


def _timestamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def log(message: str, log_path: Path | None = None) -> None:
    line = f"{datetime.now(UTC).isoformat()} {message}"
    print(line, flush=True)
    if log_path is not None:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")


def estimate_cycle_seconds(  # noqa: PLR0913
    assigned: int,
    *,
    workers: int,
    shard_size: int,
    sleep_seconds: float,
    stagger_seconds: float,
    fetch_seconds: float = 12.0,
    overhead_seconds: float = DEFAULT_CYCLE_OVERHEAD_SECONDS,
) -> float:
    """Conservative wall-clock estimate for plan + staggered workers + merge."""
    if assigned <= 0:
        return overhead_seconds
    shard_count = min(workers, (assigned + shard_size - 1) // shard_size)
    per_worker = min(shard_size, assigned) * (sleep_seconds + fetch_seconds)
    stagger_total = max(0, shard_count - 1) * stagger_seconds
    return overhead_seconds + stagger_total + per_worker


def assert_anti_icp_only(pending: list[EnrichmentCandidate]) -> None:
    """Refuse to continue if the planned queue is mixed with another tier."""
    other = Counter(
        item.tier_bucket for item in pending if item.tier_bucket != "ANTI-ICP"
    )
    if other:
        raise RuntimeError(f"STOP: non-ANTI-ICP rows in pending: {dict(other)}")


def pending_overlap_with_processed(
    pending: list[EnrichmentCandidate],
    processed: set[str],
) -> list[str]:
    return [item.account_id for item in pending if item.account_id in processed]


def inspect_ready_value(field: str, value: str) -> list[str]:  # noqa: PLR0912, PLR0915
    """Return guard-violation reasons for one merged ready value."""
    reasons: list[str] = []
    raw = value or ""
    if MARKDOWN_IMAGE_ARTIFACT in raw or "![Image" in raw:
        reasons.append("markdown_image")
    if ")###" in raw or raw.strip().startswith("*") or raw.strip().endswith("*"):
        reasons.append("markdown_artifact")
    if " icon" in raw.lower() or raw.lower().endswith("icon"):
        reasons.append("markdown_icon")
    if _has_concatenated_http(raw):
        reasons.append("concatenated_http")

    if field in PHONE_FIELDS:
        if _normalize_phone(raw) is None:
            reasons.append("non_saudi_phone")
        return reasons  # phones have no further URL guards

    if field in WHATSAPP_FIELDS:
        lowered = raw.lower()
        if "text=" in lowered:
            reasons.append("whatsapp_text_param")
        if _normalize_whatsapp_url(raw) is None:
            reasons.append("whatsapp_rejected")
        return reasons

    parsed = _safe_urlparse(raw)
    if parsed is None:
        reasons.append("malformed_url")
        return reasons
    host = (parsed.netloc or "").lower()
    path = (parsed.path or "").strip("/")
    parts = path.split("/") if path else []
    first = parts[0].lower() if parts else ""
    prefix = host.split(".")[0]

    if prefix in TRACKING_SUBDOMAINS:
        reasons.append("tracking_subdomain")
    if any(hint in host for hint in SOCIAL_HOST_HINTS) and not path:
        reasons.append("social_homepage")

    if field in TWITTER_FIELDS or "twitter.com" in host or host.endswith("x.com"):
        if first in TWITTER_RESERVED_FIRST_SEGMENTS:
            reasons.append("twitter_intent_or_share")
        if _normalize_twitter_profile_url(raw) is None:
            reasons.append("twitter_rejected")

    if (
        field in INSTAGRAM_FIELDS or "instagram.com" in host
    ) and first in INSTAGRAM_RESERVED_FIRST_SEGMENTS:
        reasons.append("instagram_reserved")

    if field in LINKEDIN_FIELDS or "linkedin.com" in host:
        if "@" in path:
            reasons.append("linkedin_at")
        if "mycompany" in path.lower():
            reasons.append("linkedin_mycompany")
        if _linkedin_entity_token(parts) in PLATFORM_LINKEDIN_SLUGS:
            reasons.append(f"platform_linkedin_{_linkedin_entity_token(parts)}")
        elif _linkedin_compact_slug(parts) in PLATFORM_LINKEDIN_SLUGS:
            reasons.append(f"platform_linkedin_{_linkedin_compact_slug(parts)}")
        if _normalize_linkedin_url(raw) is None:
            reasons.append("linkedin_rejected")

    nested_social = any(
        hint in part.lower()
        for part in parts[1:]
        for hint in SOCIAL_HOST_HINTS
    )
    if nested_social:
        reasons.append("nested_social_url")
    return reasons


def inspect_ready_rows(rows: list[EnrichmentRow]) -> dict:
    flagged: list[dict] = []
    reason_counts: Counter[str] = Counter()
    for row in rows:
        cleaned = sanitize_ready_url_value(row.value)
        reasons = inspect_ready_value(row.field, cleaned)
        if not reasons:
            continue
        flagged.append(
            {
                "id": row.account_id,
                "field": row.field,
                "val": row.value,
                "reasons": reasons,
            }
        )
        reason_counts.update(reasons)

    repeated = [
        reason for reason, count in reason_counts.items() if count >= REPEATED_FP_THRESHOLD
    ]
    platform_count = sum(
        count
        for reason, count in reason_counts.items()
        if reason.startswith("platform_linkedin_")
    )
    if platform_count >= REPEATED_FP_THRESHOLD and "platform_linkedin_family" not in repeated:
        repeated.append("platform_linkedin_family")
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "ready_rows_inspected": len(rows),
        "flagged": flagged,
        "reason_counts": dict(reason_counts),
        "repeated_platform_footer_fp": platform_count >= REPEATED_FP_THRESHOLD,
        "repeated_fp_reasons": repeated,
        "stop_for_tighten": bool(repeated),
        "notes": (
            f"Inspector flagged {len(flagged)}. "
            + (f"Repeated: {repeated}." if repeated else "No repeated FP.")
        ),
    }


def load_anti_icp_pending(
    master_csv: Path,
    existing_xlsx: Path,
) -> tuple[list[EnrichmentCandidate], set[str], dict[str, int]]:
    """Load processed IDs once, then split remaining candidates by tier bucket."""
    processed = load_processed_accounts(existing_xlsx) if existing_xlsx.exists() else set()
    all_pending = load_master_candidates(master_csv, processed_accounts=processed)
    counts: dict[str, int] = {}
    anti: list[EnrichmentCandidate] = []
    for item in all_pending:
        counts[item.tier_bucket] = counts.get(item.tier_bucket, 0) + 1
        if item.tier_bucket == "ANTI-ICP":
            anti.append(item)
    other_counts = {label: counts.get(label, 0) for label in OTHER_PENDING_TIERS}
    return anti, processed, other_counts


def launch_staggered_workers(
    commands: list[list[str]],
    worker_dirs: list[Path],
    *,
    stagger_seconds: float,
) -> list[int]:
    """Start workers with a delay between subprocesses; capture UTF-8 logs."""
    running: list[tuple[subprocess.Popen, object, object]] = []
    last_launch: float | None = None
    for command, worker_dir in zip(commands, worker_dirs, strict=True):
        if last_launch is not None and stagger_seconds > 0:
            wait = stagger_seconds - (time.monotonic() - last_launch)
            if wait > 0:
                time.sleep(wait)
        worker_dir.mkdir(parents=True, exist_ok=True)
        stdout = (worker_dir / "worker_stdout.log").open("w", encoding="utf-8")
        stderr = (worker_dir / "worker_stderr.log").open("w", encoding="utf-8")
        proc = subprocess.Popen(command, stdout=stdout, stderr=stderr)
        running.append((proc, stdout, stderr))
        last_launch = time.monotonic()

    exit_codes: list[int] = []
    for proc, stdout, stderr in running:
        exit_codes.append(proc.wait())
        stdout.close()
        stderr.close()
    return exit_codes


def load_merged_ready_rows(path: Path) -> list[EnrichmentRow]:
    if not path.exists():
        return []
    rows: list[EnrichmentRow] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            account_id = (row.get("رقم الحساب") or "").strip()
            if not account_id:
                continue
            rows.append(
                EnrichmentRow(
                    account_id=account_id,
                    company_name=(row.get("اسم الشركة") or "").strip(),
                    domain=(row.get("النطاق") or "").strip(),
                    tier=(row.get("الفئة") or "").strip(),
                    field=(row.get("الحقل") or "").strip(),
                    value=(row.get("القيمة/الرابط") or "").strip(),
                )
            )
    return rows


def run_cycle(  # noqa: PLR0913
    *,
    cycle_index: int,
    existing_xlsx: Path,
    master_csv: Path,
    output_dir: Path,
    python_executable: str,
    workers: int,
    shard_size: int,
    sleep_seconds: float,
    stagger_seconds: float,
    log_path: Path,
    pending: list[EnrichmentCandidate] | None = None,
    processed: set[str] | None = None,
    other_counts: dict[str, int] | None = None,
) -> dict:
    if pending is None or processed is None or other_counts is None:
        pending, processed, other_counts = load_anti_icp_pending(
            master_csv,
            existing_xlsx,
        )
    assert_anti_icp_only(pending)
    overlap = pending_overlap_with_processed(pending, processed)
    if overlap:
        raise RuntimeError(f"STOP: pending overlaps processed workbook IDs: {overlap[:20]}")

    leaked_other = {label: count for label, count in other_counts.items() if count}
    log(
        f"cycle={cycle_index} anti_icp_pending={len(pending)} "
        f"processed={len(processed)} other_tier_pending={other_counts}",
        log_path,
    )
    if leaked_other:
        log(f"NOTE other-tier remaining candidates (not queued): {leaked_other}", log_path)

    if not pending:
        return {
            "status": "ANTI-ICP COMPLETE",
            "pending": 0,
            "assigned": 0,
            "workbook": str(existing_xlsx),
        }

    raw_shards = split_shards(pending, workers=workers, shard_size=shard_size)
    if shards_overlap(raw_shards):
        raise RuntimeError("STOP: shard overlap detected")
    assigned = sum(len(shard) for shard in raw_shards)
    if assigned != min(len(pending), workers * shard_size):
        raise RuntimeError("STOP: shards do not cover the intended ANTI-ICP batch")
    if len(pending) <= workers * shard_size and assigned != len(pending):
        raise RuntimeError("STOP: remainder shards left unattempted ANTI-ICP IDs")

    plan = write_plan(
        output_dir,
        existing_xlsx=existing_xlsx,
        master_csv=master_csv,
        pending=pending,
        processed=processed,
        workers=workers,
        shard_size=shard_size,
        sleep_seconds=sleep_seconds,
        python_executable=python_executable,
    )
    commands = [
        build_worker_command(
            Path(record["shard_path"]),
            Path(record["worker_dir"]),
            python_executable=python_executable,
            sleep_seconds=sleep_seconds,
        )
        for record in plan["shards"]
    ]
    worker_dirs = [Path(record["worker_dir"]) for record in plan["shards"]]
    log(
        f"cycle={cycle_index} launching {len(commands)} workers "
        f"assigned={assigned} stagger={stagger_seconds}s sleep={sleep_seconds}s",
        log_path,
    )
    exit_codes = launch_staggered_workers(
        commands,
        worker_dirs,
        stagger_seconds=stagger_seconds,
    )
    log(f"cycle={cycle_index} worker_exit_codes={exit_codes}", log_path)
    if any(code != 0 for code in exit_codes):
        raise RuntimeError(f"STOP: worker crash exit_codes={exit_codes}")

    bundle = merge_worker_results(collect_worker_results(output_dir))
    if bundle.incomplete_shards:
        raise RuntimeError(f"STOP: incomplete shards {bundle.incomplete_shards}")
    summary = write_merge_outputs(
        output_dir,
        bundle,
        existing_xlsx=existing_xlsx,
        pending_total=plan["pending_queue_total"],
    )
    ready_rows = load_merged_ready_rows(output_dir / "merged_ready_rows.csv")
    inspect = inspect_ready_rows(ready_rows)
    (output_dir / "fp_inspect.json").write_text(
        json.dumps(inspect, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    log(
        f"cycle={cycle_index} merge attempted={summary['attempted']} "
        f"ready={summary['ready_rows']} issues={summary['issue_rows']} "
        f"flagged={len(inspect['flagged'])}",
        log_path,
    )
    if inspect["stop_for_tighten"]:
        raise RuntimeError(
            "STOP: repeated false-positive pattern "
            f"{inspect['repeated_fp_reasons']}"
        )
    return {
        "status": "CYCLE_OK",
        "pending_before": len(pending),
        "assigned": assigned,
        "attempted": summary["attempted"],
        "ready_rows": summary["ready_rows"],
        "issue_rows": summary["issue_rows"],
        "workbook": summary["next_existing_xlsx"],
        "inspect": inspect,
        "exit_codes": exit_codes,
    }


def run_loop(args: argparse.Namespace) -> dict:
    start = datetime.now(UTC)
    deadline = start + timedelta(hours=args.max_hours)
    log_dir = Path(args.loop_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "LOOP_LOG.txt"
    (log_dir / "loop_start.json").write_text(
        json.dumps(
            {
                "start_utc": start.isoformat(),
                "deadline_utc": deadline.isoformat(),
                "max_hours": args.max_hours,
                "workers": args.workers,
                "shard_size": args.shard_size,
                "tiers": "ANTI-ICP",
                "existing_xlsx": str(Path(args.existing_xlsx).resolve()),
                "review_only": True,
                "production_not_approved": True,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    log(
        f"LOOP START workers={args.workers} shard_size={args.shard_size} "
        f"deadline={deadline.isoformat()}",
        log_path,
    )

    current_xlsx = Path(args.existing_xlsx)
    cycles: list[dict] = []
    stop_reason = "ANTI-ICP COMPLETE"
    latest_workbook = str(current_xlsx.resolve())

    for cycle_index in range(1, args.max_cycles + 1):
        now = datetime.now(UTC)
        remaining = (deadline - now).total_seconds()
        pending, processed, other_counts = load_anti_icp_pending(
            Path(args.master_csv),
            current_xlsx,
        )
        if not pending:
            stop_reason = "ANTI-ICP COMPLETE"
            log("ANTI-ICP queue empty; stopping success.", log_path)
            break
        assigned = min(len(pending), args.workers * args.shard_size)
        estimate = estimate_cycle_seconds(
            assigned,
            workers=args.workers,
            shard_size=args.shard_size,
            sleep_seconds=args.sleep_seconds,
            stagger_seconds=args.stagger_seconds,
        )
        if remaining < estimate:
            stop_reason = (
                f"TIME_BUDGET remaining={remaining:.0f}s estimate={estimate:.0f}s"
            )
            log(f"STOP: {stop_reason}", log_path)
            break

        output_dir = log_dir / f"cycle_{cycle_index:02d}_{_timestamp()}"
        try:
            result = run_cycle(
                cycle_index=cycle_index,
                existing_xlsx=current_xlsx,
                master_csv=Path(args.master_csv),
                output_dir=output_dir,
                python_executable=args.python_executable,
                workers=args.workers,
                shard_size=args.shard_size,
                sleep_seconds=args.sleep_seconds,
                stagger_seconds=args.stagger_seconds,
                log_path=log_path,
                pending=pending,
                processed=processed,
                other_counts=other_counts,
            )
        except Exception as exc:
            stop_reason = str(exc)
            log(f"STOP: {stop_reason}", log_path)
            cycles.append({"cycle": cycle_index, "status": "STOP", "error": stop_reason})
            break
        cycles.append({"cycle": cycle_index, **result})
        if result["status"] == "ANTI-ICP COMPLETE":
            stop_reason = "ANTI-ICP COMPLETE"
            break
        latest_workbook = result["workbook"] or latest_workbook
        current_xlsx = Path(latest_workbook)

    end = datetime.now(UTC)
    summary = {
        "start_utc": start.isoformat(),
        "end_utc": end.isoformat(),
        "elapsed_seconds": (end - start).total_seconds(),
        "max_hours": args.max_hours,
        "stop_reason": stop_reason,
        "cycles": cycles,
        "latest_workbook": latest_workbook,
        "review_only": True,
        "production_not_approved": True,
    }
    (log_dir / "loop_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    log(f"LOOP END reason={stop_reason} elapsed_s={summary['elapsed_seconds']:.0f}", log_path)
    return summary


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="8-hour ANTI-ICP Agent Reach loop.")
    parser.add_argument(
        "--master-csv",
        type=Path,
        default=Path.home() / "Downloads" / "MUHIDE_extracted" / "01_Master_Accounts.csv",
    )
    parser.add_argument("--existing-xlsx", type=Path, required=True)
    parser.add_argument("--loop-dir", type=Path, required=True)
    parser.add_argument(
        "--python-executable",
        default=sys.executable,
    )
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--shard-size", type=int, default=25)
    parser.add_argument("--sleep-seconds", type=float, default=1.0)
    parser.add_argument("--stagger-seconds", type=float, default=10.0)
    parser.add_argument("--max-hours", type=float, default=8.0)
    parser.add_argument("--max-cycles", type=int, default=40)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    summary = run_loop(args)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["stop_reason"] == "ANTI-ICP COMPLETE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
