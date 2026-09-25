"""Coordinate parallel-safe Agent Reach contact-enrichment workers.

Review-only flow:
- one coordinator builds a pending queue and non-overlapping shards;
- each worker writes CSV/checkpoint/summary into its own directory;
- only the coordinator copies the latest workbook and appends merged rows.

Workers never share a workbook or output directory. Incomplete shard rows are
not treated as processed unless they appear in ready/issues CSV or a
checkpoint that records an actual Agent Reach attempt.
"""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
BACKEND_ROOT = SCRIPTS_DIR.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from agent_reach_contact_enrichment_loop import (  # noqa: E402
    ISSUE_HEADERS,
    READY_HEADERS,
    _append_to_workbook,
    _default_downloads_path,
    _parse_tiers,
    _timestamp,
    _write_csv,
    sanitize_existing_workbook,
)

from app.modules.agent_reach.contact_enrichment import (  # noqa: E402
    QUEUE_HEADERS,
    EnrichmentCandidate,
    EnrichmentRow,
    QualityIssue,
    load_master_candidates,
    load_processed_accounts,
    queue_row_from_candidate,
)

LOOP_SCRIPT = SCRIPTS_DIR / "agent_reach_contact_enrichment_loop.py"
WORKBOOK_NAME = "14_Website_Phone_Social_Enrichment_AgentReach.xlsx"


@dataclass
class ShardSpec:
    shard_id: str
    accounts: list[EnrichmentCandidate]
    shard_path: Path
    worker_dir: Path

    @property
    def account_ids(self) -> list[str]:
        return [item.account_id for item in self.accounts]


@dataclass
class WorkerResult:
    shard_id: str
    worker_dir: Path
    assigned_ids: list[str]
    attempted_ids: list[str]
    ready_rows: list[EnrichmentRow] = field(default_factory=list)
    issues: list[QualityIssue] = field(default_factory=list)
    incomplete: bool = False

    @property
    def unattempted_ids(self) -> list[str]:
        attempted = set(self.attempted_ids)
        return [account_id for account_id in self.assigned_ids if account_id not in attempted]


@dataclass
class MergeBundle:
    ready_rows: list[EnrichmentRow]
    issues: list[QualityIssue]
    workers: list[WorkerResult]
    incomplete_shards: list[str]
    assigned_ids: list[str]
    attempted_ids: list[str]


def load_checkpoint_attempted_ids(path: Path) -> list[str]:
    """Account IDs Agent Reach actually attempted, in checkpoint order."""
    if not path.exists():
        return []
    attempted: list[str] = []
    seen: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        account_id = str(payload.get("account_id") or "").strip()
        if account_id and account_id not in seen:
            seen.add(account_id)
            attempted.append(account_id)
    return attempted


def load_ready_rows_csv(path: Path) -> list[EnrichmentRow]:
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


def load_quality_issues_csv(path: Path) -> list[QualityIssue]:
    if not path.exists():
        return []
    issues: list[QualityIssue] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            account_id = (row.get("رقم الحساب") or "").strip()
            if not account_id:
                continue
            issues.append(
                QualityIssue(
                    account_id=account_id,
                    company_name=(row.get("اسم الشركة") or "").strip(),
                    domain=(row.get("النطاق المسجل") or row.get("النطاق") or "").strip(),
                    issue=(row.get("المشكلة") or "").strip(),
                )
            )
    return issues


def build_pending_candidates(
    master_csv: Path,
    existing_xlsx: Path,
    *,
    tiers: set[str],
) -> tuple[list[EnrichmentCandidate], set[str]]:
    processed = load_processed_accounts(existing_xlsx) if existing_xlsx.exists() else set()
    candidates = load_master_candidates(
        master_csv,
        processed_accounts=processed,
        tiers=tiers,
    )
    return candidates, processed


def split_shards(
    candidates: list[EnrichmentCandidate],
    *,
    workers: int,
    shard_size: int,
) -> list[list[EnrichmentCandidate]]:
    """Split the front of the pending queue into non-overlapping shards."""
    if workers < 1:
        raise ValueError("workers must be >= 1")
    if shard_size < 1:
        raise ValueError("shard_size must be >= 1")
    batch = candidates[: workers * shard_size]
    shards: list[list[EnrichmentCandidate]] = []
    for index in range(workers):
        start = index * shard_size
        chunk = batch[start : start + shard_size]
        if chunk:
            shards.append(chunk)
    return shards


def shard_account_sets(shards: list[list[EnrichmentCandidate]]) -> list[set[str]]:
    return [{item.account_id for item in shard} for shard in shards]


def shards_overlap(shards: list[list[EnrichmentCandidate]]) -> bool:
    seen: set[str] = set()
    for account_ids in shard_account_sets(shards):
        if seen & account_ids:
            return True
        seen.update(account_ids)
    return False


def _dedupe_ready_rows(rows: list[EnrichmentRow]) -> list[EnrichmentRow]:
    unique: list[EnrichmentRow] = []
    seen: set[tuple[str, str, str, str]] = set()
    for row in rows:
        key = (row.account_id, row.field, row.value, row.domain)
        if key in seen:
            continue
        seen.add(key)
        unique.append(row)
    return unique


def _dedupe_issues(issues: list[QualityIssue]) -> list[QualityIssue]:
    unique: list[QualityIssue] = []
    seen: set[tuple[str, str, str]] = set()
    for issue in issues:
        key = (issue.account_id, issue.domain, issue.issue)
        if key in seen:
            continue
        seen.add(key)
        unique.append(issue)
    return unique


def build_worker_command(
    shard_path: Path,
    worker_dir: Path,
    *,
    python_executable: str | None = None,
    sleep_seconds: float = 1.0,
) -> list[str]:
    return [
        python_executable or sys.executable,
        str(LOOP_SCRIPT.resolve()),
        "--queue-csv",
        str(shard_path.resolve()),
        "--no-workbook",
        "--output-dir",
        str(worker_dir.resolve()),
        "--sleep-seconds",
        str(sleep_seconds),
    ]


def format_worker_command(command: list[str]) -> str:
    return subprocess.list2cmdline(command)


def write_plan(  # noqa: PLR0913
    output_dir: Path,
    *,
    existing_xlsx: Path,
    master_csv: Path,
    pending: list[EnrichmentCandidate],
    processed: set[str],
    workers: int,
    shard_size: int,
    sleep_seconds: float = 1.0,
    python_executable: str | None = None,
) -> dict:
    """Write pending_queue.csv, shard CSVs, worker dirs, and command files."""
    output_dir.mkdir(parents=True, exist_ok=True)
    shards_dir = output_dir / "shards"
    workers_dir = output_dir / "workers"
    shards_dir.mkdir(parents=True, exist_ok=True)
    workers_dir.mkdir(parents=True, exist_ok=True)

    _write_csv(
        output_dir / "pending_queue.csv",
        QUEUE_HEADERS,
        [queue_row_from_candidate(item) for item in pending],
    )

    raw_shards = split_shards(pending, workers=workers, shard_size=shard_size)
    if shards_overlap(raw_shards):
        raise RuntimeError("shard overlap detected; refusing to write plan")

    specs: list[ShardSpec] = []
    commands: list[list[str]] = []
    shard_records: list[dict] = []
    for index, accounts in enumerate(raw_shards, start=1):
        shard_id = f"shard_{index:03d}"
        worker_id = f"worker_{index:03d}"
        spec = ShardSpec(
            shard_id=shard_id,
            accounts=accounts,
            shard_path=shards_dir / f"{shard_id}.csv",
            worker_dir=workers_dir / worker_id,
        )
        spec.worker_dir.mkdir(parents=True, exist_ok=True)
        rows = [queue_row_from_candidate(item) for item in accounts]
        _write_csv(spec.shard_path, QUEUE_HEADERS, rows)
        _write_csv(spec.worker_dir / "assigned_queue.csv", QUEUE_HEADERS, rows)
        command = build_worker_command(
            spec.shard_path,
            spec.worker_dir,
            python_executable=python_executable,
            sleep_seconds=sleep_seconds,
        )
        specs.append(spec)
        commands.append(command)
        shard_records.append(
            {
                "shard_id": spec.shard_id,
                "worker_id": worker_id,
                "shard_path": str(spec.shard_path.resolve()),
                "worker_dir": str(spec.worker_dir.resolve()),
                "accounts": len(spec.accounts),
                "account_ids": spec.account_ids,
                "command": format_worker_command(command),
            }
        )

    assigned_this_run = sum(len(spec.accounts) for spec in specs)
    plan = {
        "mode": "plan",
        "review_only": True,
        "existing_xlsx": str(existing_xlsx.resolve()),
        "master_csv": str(master_csv.resolve()),
        "processed_in_workbook": len(processed),
        "pending_queue_total": len(pending),
        "assigned_this_run": assigned_this_run,
        "remaining_after_assignment": len(pending) - assigned_this_run,
        "workers": workers,
        "shard_size": shard_size,
        "shards": shard_records,
        "worker_commands": [record["command"] for record in shard_records],
        "generated_at": datetime.now(UTC).isoformat(),
    }
    (output_dir / "plan.json").write_text(
        json.dumps(plan, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (output_dir / "worker_commands.txt").write_text(
        "\n".join(plan["worker_commands"]) + ("\n" if plan["worker_commands"] else ""),
        encoding="utf-8",
    )
    return plan


def load_assigned_ids(path: Path) -> list[str]:
    if not path.exists():
        return []
    assigned: list[str] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            account_id = (row.get("account_id") or "").strip()
            if account_id:
                assigned.append(account_id)
    return assigned


def load_worker_result(
    worker_dir: Path,
    *,
    shard_id: str | None = None,
    assigned_ids: list[str] | None = None,
) -> WorkerResult:
    resolved_assigned = assigned_ids or load_assigned_ids(worker_dir / "assigned_queue.csv")
    checkpoint_ids = load_checkpoint_attempted_ids(worker_dir / "agent_reach_checkpoint.jsonl")
    ready_rows = load_ready_rows_csv(worker_dir / "agent_reach_ready_rows.csv")
    issues = load_quality_issues_csv(worker_dir / "agent_reach_quality_issues.csv")
    csv_ids = [row.account_id for row in ready_rows] + [issue.account_id for issue in issues]
    attempted: list[str] = []
    seen: set[str] = set()
    for account_id in checkpoint_ids + csv_ids:
        if account_id not in seen:
            seen.add(account_id)
            attempted.append(account_id)
    incomplete = any(account_id not in seen for account_id in resolved_assigned)
    return WorkerResult(
        shard_id=shard_id or worker_dir.name,
        worker_dir=worker_dir,
        assigned_ids=resolved_assigned,
        attempted_ids=attempted,
        ready_rows=ready_rows,
        issues=issues,
        incomplete=incomplete,
    )


def merge_worker_results(results: list[WorkerResult]) -> MergeBundle:
    ready_rows: list[EnrichmentRow] = []
    issues: list[QualityIssue] = []
    assigned_ids: list[str] = []
    attempted_ids: list[str] = []
    incomplete_shards: list[str] = []
    assigned_seen: set[str] = set()
    attempted_seen: set[str] = set()

    for result in results:
        ready_rows.extend(result.ready_rows)
        issues.extend(result.issues)
        if result.incomplete:
            incomplete_shards.append(result.shard_id)
        for account_id in result.assigned_ids:
            if account_id not in assigned_seen:
                assigned_seen.add(account_id)
                assigned_ids.append(account_id)
        for account_id in result.attempted_ids:
            if account_id not in attempted_seen:
                attempted_seen.add(account_id)
                attempted_ids.append(account_id)

    return MergeBundle(
        ready_rows=_dedupe_ready_rows(ready_rows),
        issues=_dedupe_issues(issues),
        workers=results,
        incomplete_shards=incomplete_shards,
        assigned_ids=assigned_ids,
        attempted_ids=attempted_ids,
    )


def discover_worker_dirs(output_dir: Path) -> list[Path]:
    workers_root = output_dir / "workers"
    if not workers_root.exists():
        return []
    return sorted(
        path
        for path in workers_root.iterdir()
        if path.is_dir() and path.name.startswith("worker_")
    )


def load_plan_shard_map(output_dir: Path) -> dict[str, dict]:
    plan_path = output_dir / "plan.json"
    if not plan_path.exists():
        return {}
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    mapping: dict[str, dict] = {}
    for record in plan.get("shards", []):
        worker_dir = str(Path(record["worker_dir"]).resolve())
        mapping[worker_dir] = record
    return mapping


def collect_worker_results(output_dir: Path) -> list[WorkerResult]:
    shard_map = load_plan_shard_map(output_dir)
    results: list[WorkerResult] = []
    for worker_dir in discover_worker_dirs(output_dir):
        record = shard_map.get(str(worker_dir.resolve()), {})
        results.append(
            load_worker_result(
                worker_dir,
                shard_id=record.get("shard_id"),
                assigned_ids=record.get("account_ids"),
            )
        )
    return results


def write_merge_outputs(
    output_dir: Path,
    bundle: MergeBundle,
    *,
    existing_xlsx: Path,
    pending_total: int | None = None,
) -> dict:
    """Copy the latest workbook once and append each merged row once."""
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(
        output_dir / "merged_ready_rows.csv",
        READY_HEADERS,
        [row.as_csv_row() for row in bundle.ready_rows],
    )
    _write_csv(
        output_dir / "merged_quality_issues.csv",
        ISSUE_HEADERS,
        [issue.as_csv_row() for issue in bundle.issues],
    )

    workbook_path = None
    if existing_xlsx.exists():
        workbook_path = output_dir / WORKBOOK_NAME
        _append_to_workbook(existing_xlsx, workbook_path, bundle.ready_rows, bundle.issues)

    remaining = None
    if pending_total is not None:
        remaining = pending_total - len(bundle.attempted_ids)

    summary = {
        "mode": "merge",
        "review_only": True,
        "workers": len(bundle.workers),
        "assigned": len(bundle.assigned_ids),
        "attempted": len(bundle.attempted_ids),
        "ready_rows": len(bundle.ready_rows),
        "issue_rows": len(bundle.issues),
        "incomplete_shards": bundle.incomplete_shards,
        "unattempted_account_ids": [
            account_id
            for result in bundle.workers
            for account_id in result.unattempted_ids
        ],
        "workbook": str(workbook_path.resolve()) if workbook_path else None,
        "next_existing_xlsx": str(workbook_path.resolve()) if workbook_path else None,
        "remaining_queue_estimate": remaining,
        "generated_at": datetime.now(UTC).isoformat(),
    }
    (output_dir / "merge_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return summary


def launch_workers(
    commands: list[list[str]],
    *,
    max_workers: int,
    stagger_seconds: float = 0.0,
) -> list[int]:
    """Launch bounded worker subprocesses and wait for all to finish.

    When stagger_seconds > 0, wait that long between each new subprocess
    start so workers do not all hit the network at the same second.
    """
    pending = list(commands)
    running: list[subprocess.Popen] = []
    exit_codes: list[int] = []
    bound = max(1, max_workers)
    last_launch: float | None = None

    while pending or running:
        while pending and len(running) < bound:
            if last_launch is not None and stagger_seconds > 0:
                wait = stagger_seconds - (time.monotonic() - last_launch)
                if wait > 0:
                    time.sleep(wait)
            running.append(subprocess.Popen(pending.pop(0)))
            last_launch = time.monotonic()
        finished = []
        for proc in running:
            code = proc.poll()
            if code is not None:
                exit_codes.append(code)
                finished.append(proc)
        for proc in finished:
            running.remove(proc)
        if running and not finished:
            running[0].wait()

    return exit_codes


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Plan, launch, or merge parallel Agent Reach contact-enrichment workers."
    )
    parser.add_argument(
        "--master-csv",
        type=Path,
        default=_default_downloads_path("MUHIDE_extracted/01_Master_Accounts.csv"),
    )
    parser.add_argument(
        "--existing-xlsx",
        type=Path,
        default=_default_downloads_path("14_Website_Phone_Social_Enrichment_InProgress.xlsx"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs") / "agent_reach_contact_enrichment" / f"{_timestamp()}_parallel",
    )
    parser.add_argument("--tiers", default="TIER C")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--shard-size", type=int, default=25)
    parser.add_argument("--sleep-seconds", type=float, default=1.0)
    parser.add_argument(
        "--stagger-seconds",
        type=float,
        default=0.0,
        help="Seconds to wait between worker subprocess starts (0 = launch immediately).",
    )
    parser.add_argument(
        "--plan-only",
        action="store_true",
        help="Write queue, shards, and worker commands; do not launch or merge.",
    )
    parser.add_argument(
        "--merge-only",
        action="store_true",
        help="Merge existing worker directories into one new workbook.",
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="Plan, launch bounded worker subprocesses, then merge. Live site fetches.",
    )
    parser.add_argument(
        "--sanitize-xlsx",
        action="store_true",
        help="Copy the existing workbook and strip ![Image leaks from ready URL values.",
    )
    return parser


def write_sanitize_outputs(output_dir: Path, existing_xlsx: Path) -> dict:
    """Copy the latest workbook into a new folder and sanitize ready URL leaks."""
    output_dir.mkdir(parents=True, exist_ok=True)
    workbook_path = output_dir / WORKBOOK_NAME
    stats = sanitize_existing_workbook(existing_xlsx, workbook_path)
    summary = {
        "mode": "sanitize",
        "review_only": True,
        "generated_at": datetime.now(UTC).isoformat(),
        **stats,
        "workbook": stats["output"],
        "next_existing_xlsx": stats["output"],
    }
    (output_dir / "sanitize_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return summary


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    selected = [args.plan_only, args.merge_only, args.run, args.sanitize_xlsx]
    if sum(bool(flag) for flag in selected) > 1:
        print(
            "Choose only one of --plan-only, --merge-only, --run, --sanitize-xlsx.",
            file=sys.stderr,
        )
        return 2
    if not any(selected):
        args.plan_only = True

    args.output_dir.mkdir(parents=True, exist_ok=True)
    tiers = _parse_tiers(args.tiers)

    if args.sanitize_xlsx:
        summary = write_sanitize_outputs(args.output_dir, args.existing_xlsx)
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0

    if args.merge_only:
        pending_total = None
        plan_path = args.output_dir / "plan.json"
        if plan_path.exists():
            pending_total = json.loads(plan_path.read_text(encoding="utf-8")).get(
                "pending_queue_total"
            )
        bundle = merge_worker_results(collect_worker_results(args.output_dir))
        summary = write_merge_outputs(
            args.output_dir,
            bundle,
            existing_xlsx=args.existing_xlsx,
            pending_total=pending_total,
        )
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0

    pending, processed = build_pending_candidates(
        args.master_csv,
        args.existing_xlsx,
        tiers=tiers,
    )
    plan = write_plan(
        args.output_dir,
        existing_xlsx=args.existing_xlsx,
        master_csv=args.master_csv,
        pending=pending,
        processed=processed,
        workers=args.workers,
        shard_size=args.shard_size,
        sleep_seconds=args.sleep_seconds,
    )
    print(json.dumps(plan, ensure_ascii=False, indent=2))

    if args.plan_only:
        return 0

    commands = [
        build_worker_command(
            Path(record["shard_path"]),
            Path(record["worker_dir"]),
            sleep_seconds=args.sleep_seconds,
        )
        for record in plan["shards"]
    ]
    print(f"launching {len(commands)} workers (live Agent Reach fetches)", flush=True)
    exit_codes = launch_workers(
        commands,
        max_workers=args.workers,
        stagger_seconds=args.stagger_seconds,
    )
    print(f"worker_exit_codes={exit_codes}", flush=True)

    bundle = merge_worker_results(collect_worker_results(args.output_dir))
    summary = write_merge_outputs(
        args.output_dir,
        bundle,
        existing_xlsx=args.existing_xlsx,
        pending_total=plan["pending_queue_total"],
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if all(code == 0 for code in exit_codes) else 1


if __name__ == "__main__":
    raise SystemExit(main())
