"""Final Agent Reach + review-only master-patch closure.

Writes a cleaned workbook copy (if ready-row FPs remain), a new timestamped
master patch, and a missing-data backlog. Never overwrites the original master
CSV, Downloads, prior patch dirs, or the source workbook. No production DB.
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import sys
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from agent_reach_anti_icp_loop import inspect_ready_rows  # noqa: E402
from agent_reach_master_enrichment_patch import (  # noqa: E402
    ADDITIVE_COLUMNS,
    STATUS_QUALITY,
    STATUS_READY_WITH_ISSUES,
    VALUE_DELIMITER,
    classify_quality_issue,
    file_snapshot,
    recover_ready_values,
    run_patch,
)
from agent_reach_parallel_contact_enrichment import write_plan  # noqa: E402

from app.modules.agent_reach.contact_enrichment import (  # noqa: E402
    READY_SHEET,
    EnrichmentRow,
    is_safe_company_domain,
    load_master_candidates,
    load_processed_accounts,
    normalize_domain,
    parse_bool,
    tier_bucket,
)

CLAIMED_TIERS = ("CLASS A", "TIER B", "TIER C", "TIER D", "UNKNOWN", "ANTI-ICP")
WORKBOOK_NAME = "14_Website_Phone_Social_Enrichment_AgentReach.xlsx"
READY_COMPANY_COL = 1
READY_DOMAIN_COL = 2
READY_TIER_COL = 3
READY_FIELD_COL = 4
READY_VALUE_COL = 5
HEADER_ROW = 1
METHOD_HUMAN = "يحتاج مراجعة بشرية"
METHOD_EXTERNAL = "يحتاج مصدر خارجي غير Agent Reach"
METHOD_DOMAIN = "يحتاج تصحيح domain في الماستر"
METHOD_INSUFFICIENT = "لا يوجد evidence كافي حالياً"
DOMAIN_FIX_CATEGORIES = frozenset({
    "typo_domain",
    "government_domain",
    "invalid_or_generic_domain",
})
HUMAN_CATEGORIES = frozenset({
    "company_domain_mismatch",
    "hijacked_or_compromised",
    "global_parent_domain",
    "placeholder_or_fake",
})
DEAD_CATEGORIES = frozenset({
    "parked_or_hosting",
    "unreachable",
    "timeout",
    "company_domain_mismatch",
    "hijacked_or_compromised",
    "invalid_or_generic_domain",
    "typo_domain",
    "government_domain",
})
OTHER_SOCIAL_COLUMNS = (
    "AgentReach_Instagram",
    "AgentReach_X",
    "AgentReach_Facebook",
    "AgentReach_TikTok",
    "AgentReach_YouTube",
    "AgentReach_Snapchat",
)
BACKLOG_HEADERS = [
    "Master Account ID",
    "company_name",
    "tier",
    "tier_bucket",
    "primary_domain",
    "usable_domain",
    "attempted_agent_reach",
    "enrichment_status",
    "missing_phone",
    "missing_whatsapp",
    "missing_linkedin",
    "missing_other_social",
    "invalid_dead_or_mismatch_site",
    "quality_issues_only",
    "no_recoverable_website_social_evidence",
    "quality_categories",
    "next_method",
    "notes",
]
SUMMARY_HEADERS = [
    "tier_bucket",
    "next_method",
    "accounts",
    "missing_phone",
    "missing_whatsapp",
    "missing_linkedin",
    "missing_other_social",
    "invalid_dead_or_mismatch_site",
    "quality_issues_only",
    "no_recoverable_website_social_evidence",
    "attempted_agent_reach",
]


def _timestamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def _row_text(row: tuple[object, ...] | None, index: int) -> str:
    if not row or len(row) <= index:
        return ""
    return str(row[index] or "").strip()


def _write_csv(path: Path, headers: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def clean_ready_workbook(source: Path, dest: Path) -> dict[str, object]:
    """Copy the workbook and recover/delete ready-row FPs. Source is not overwritten."""
    from openpyxl import load_workbook

    if source.resolve() == dest.resolve():
        raise ValueError("refusing in-place workbook overwrite")
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, dest)
    wb = load_workbook(dest)
    ready = wb[READY_SHEET]
    kept: list[tuple[str, str, str, str, str, str]] = []
    deleted: list[dict[str, str]] = []
    recovered: list[dict[str, str]] = []
    extras = 0
    before_rows = 0
    before_ids: set[str] = set()
    for row in ready.iter_rows(min_row=2, values_only=True):
        account_id = _row_text(row, 0)
        if not account_id:
            continue
        before_rows += 1
        before_ids.add(account_id)
        company = _row_text(row, READY_COMPANY_COL)
        domain = _row_text(row, READY_DOMAIN_COL)
        tier = _row_text(row, READY_TIER_COL)
        field = _row_text(row, READY_FIELD_COL)
        value = _row_text(row, READY_VALUE_COL)
        values = recover_ready_values(field, value)
        if not values:
            deleted.append(
                {
                    "account_id": account_id,
                    "field": field,
                    "value": value,
                    "action": "deleted",
                }
            )
            continue
        if values[0] != value:
            recovered.append(
                {
                    "account_id": account_id,
                    "field": field,
                    "before": value,
                    "after": values[0],
                    "action": "recovered",
                }
            )
        kept.append((account_id, company, domain, tier, field, values[0]))
        for extra in values[1:]:
            extras += 1
            kept.append((account_id, company, domain, tier, field, extra))
            recovered.append(
                {
                    "account_id": account_id,
                    "field": field,
                    "before": value,
                    "after": extra,
                    "action": "split",
                }
            )

    if ready.max_row > HEADER_ROW:
        ready.delete_rows(HEADER_ROW + 1, ready.max_row - HEADER_ROW)
    for item in kept:
        ready.append(list(item))
    tables = list(ready.tables.values())
    if tables:
        table = tables[0]
        end_col = table.ref.split(":")[1]
        letters = "".join(ch for ch in end_col if ch.isalpha())
        table.ref = f"A1:{letters}{ready.max_row}"
    wb.save(dest)
    wb.close()

    after_ids = {item[0] for item in kept}
    return {
        "source": str(source.resolve()),
        "output": str(dest.resolve()),
        "ready_rows_before": before_rows,
        "ready_accounts_before": len(before_ids),
        "ready_rows_after": len(kept),
        "ready_accounts_after": len(after_ids),
        "deleted_rows": len(deleted),
        "recovered_or_split": len(recovered),
        "extra_rows_from_split": extras,
        "deleted": deleted,
        "recovered": recovered,
        "review_only": True,
    }


def load_ready_rows_from_workbook(path: Path) -> list[EnrichmentRow]:
    from openpyxl import load_workbook

    wb = load_workbook(path, read_only=True, data_only=True)
    rows: list[EnrichmentRow] = []
    if READY_SHEET in wb.sheetnames:
        for row in wb[READY_SHEET].iter_rows(min_row=2, values_only=True):
            account_id = _row_text(row, 0)
            if not account_id:
                continue
            rows.append(
                EnrichmentRow(
                    account_id=account_id,
                    company_name=_row_text(row, READY_COMPANY_COL),
                    domain=_row_text(row, READY_DOMAIN_COL),
                    tier=_row_text(row, READY_TIER_COL),
                    field=_row_text(row, READY_FIELD_COL),
                    value=_row_text(row, READY_VALUE_COL),
                )
            )
    wb.close()
    return rows


def confirm_plan_only(
    master_csv: Path,
    workbook: Path,
    output_dir: Path,
) -> dict[str, object]:
    processed = load_processed_accounts(workbook)
    all_pending = load_master_candidates(master_csv, processed_accounts=processed)
    pending_by_tier: dict[str, list] = {}
    for item in all_pending:
        pending_by_tier.setdefault(item.tier_bucket, []).append(item)
    plans: dict[str, object] = {}
    for label in CLAIMED_TIERS:
        pending = pending_by_tier.get(label, [])
        plan = write_plan(
            output_dir / f"plan_{label.replace(' ', '_').replace('-', '_')}",
            existing_xlsx=workbook,
            master_csv=master_csv,
            pending=pending,
            processed=processed,
            workers=1,
            shard_size=25,
        )
        plans[label] = {
            "pending_queue_total": plan["pending_queue_total"],
            "ids": [item.account_id for item in pending],
        }
    other = {
        label: [item.account_id for item in items]
        for label, items in pending_by_tier.items()
        if label not in CLAIMED_TIERS
    }
    return {
        "processed_in_workbook": len(processed),
        "claimed_tiers": plans,
        "other_labeled_tiers": {key: len(value) for key, value in other.items()},
        "other_labeled_ids": other,
        "all_pending_total": len(all_pending),
        "all_pending_by_tier": {key: len(value) for key, value in pending_by_tier.items()},
    }


def classify_next_method(  # noqa: PLR0913
    *,
    categories: set[str],
    status: str,
    attempted: bool,
    usable_domain: bool,
    master_has_phone: bool,
    master_has_social: bool,
    missing_any: bool,
) -> str:
    if categories & DOMAIN_FIX_CATEGORIES:
        return METHOD_DOMAIN
    if categories & HUMAN_CATEGORIES or status == STATUS_READY_WITH_ISSUES:
        return METHOD_HUMAN
    if attempted:
        if missing_any or status == STATUS_QUALITY:
            return METHOD_EXTERNAL
        return METHOD_HUMAN
    skipped_with_master_contacts = (
        usable_domain and master_has_phone and master_has_social
    )
    if skipped_with_master_contacts:
        return METHOD_EXTERNAL
    return METHOD_INSUFFICIENT


def _flag(value: bool) -> str:
    return "true" if value else "false"


def build_missing_data_backlog(  # noqa: PLR0912, PLR0915
    master_csv: Path,
    patches: dict,
    output_dir: Path,
) -> dict[str, object]:
    """Write summary + actionable missing-data CSVs. Does not dump unused 296k IDs."""
    domain_counts: Counter[str] = Counter()
    master_rows: list[dict[str, str]] = []
    with master_csv.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            domain = normalize_domain(row.get("Primary_Domain"))
            row["_domain"] = domain
            master_rows.append(row)
            if domain:
                domain_counts[domain] += 1

    actionable: list[dict[str, str]] = []
    summary: dict[tuple[str, str], dict[str, int]] = defaultdict(
        lambda: {
            "accounts": 0,
            "missing_phone": 0,
            "missing_whatsapp": 0,
            "missing_linkedin": 0,
            "missing_other_social": 0,
            "invalid_dead_or_mismatch_site": 0,
            "quality_issues_only": 0,
            "no_recoverable_website_social_evidence": 0,
            "attempted_agent_reach": 0,
        }
    )
    remaining_incomplete = 0
    gap_totals = Counter()
    method_totals = Counter()

    for row in master_rows:
        account_id = (row.get("Master Account ID") or "").strip()
        if not account_id:
            continue
        patch = patches.get(account_id)
        attempted = patch is not None and not getattr(patch, "unmatched", False)
        usable = is_safe_company_domain(row.get("_domain") or "", domain_counts)
        master_has_phone = parse_bool(row.get("has_phone")) or bool(
            (row.get("Primary_Phone") or "").strip()
        )
        master_has_social = parse_bool(row.get("has_social"))
        additive = {column: "" for column in ADDITIVE_COLUMNS}
        categories: set[str] = set()
        status = ""
        if attempted and patch is not None:
            for column, values in patch.values_by_column.items():
                additive[column] = VALUE_DELIMITER.join(values)
            status = patch.status
            for issue in patch.issues:
                categories.add(classify_quality_issue(issue.issue)[0])

        has_ar_phone = bool(additive.get("AgentReach_Phones"))
        has_ar_wa = bool(additive.get("AgentReach_WhatsApp"))
        has_ar_li = bool(additive.get("AgentReach_LinkedIn"))
        has_ar_other = any(additive.get(column) for column in OTHER_SOCIAL_COLUMNS)
        missing_phone = not has_ar_phone and not master_has_phone
        missing_wa = not has_ar_wa
        missing_li = not has_ar_li
        missing_other = not has_ar_other and not master_has_social
        quality_only = attempted and bool(categories) and not (
            has_ar_phone or has_ar_wa or has_ar_li or has_ar_other
        )
        dead = bool(categories & DEAD_CATEGORIES)
        no_evidence = (attempted and quality_only) or (
            not attempted and not usable and missing_phone and missing_other
        )
        missing_any = missing_phone or missing_wa or missing_li or missing_other
        next_method = classify_next_method(
            categories=categories,
            status=status,
            attempted=attempted,
            usable_domain=usable,
            master_has_phone=master_has_phone,
            master_has_social=master_has_social,
            missing_any=missing_any,
        )
        incomplete = missing_any or dead or quality_only or no_evidence
        if attempted and incomplete:
            remaining_incomplete += 1
        bucket = tier_bucket(row.get("Account_Tier_v2"))
        key = (bucket, next_method)
        summary[key]["accounts"] += 1
        flags = {
            "missing_phone": missing_phone,
            "missing_whatsapp": missing_wa,
            "missing_linkedin": missing_li,
            "missing_other_social": missing_other,
            "invalid_dead_or_mismatch_site": dead,
            "quality_issues_only": quality_only,
            "no_recoverable_website_social_evidence": no_evidence,
        }
        for flag_name, flag_value in flags.items():
            if flag_value:
                summary[key][flag_name] += 1
                gap_totals[flag_name] += 1
        if attempted:
            summary[key]["attempted_agent_reach"] += 1
        method_totals[next_method] += 1

        is_actionable = attempted or dead or (
            usable and missing_phone and missing_other and not master_has_phone
        )
        if not is_actionable:
            continue
        notes = []
        if attempted and missing_any:
            notes.append("agent_reach_already_attempted")
        if not usable:
            notes.append("no_usable_master_domain")
        if status:
            notes.append(status)
        actionable.append(
            {
                "Master Account ID": account_id,
                "company_name": (row.get("Canonical_Company_Name") or "").strip(),
                "tier": (row.get("Account_Tier_v2") or "").strip(),
                "tier_bucket": bucket,
                "primary_domain": row.get("_domain") or "",
                "usable_domain": _flag(usable),
                "attempted_agent_reach": _flag(attempted),
                "enrichment_status": status,
                "missing_phone": _flag(missing_phone),
                "missing_whatsapp": _flag(missing_wa),
                "missing_linkedin": _flag(missing_li),
                "missing_other_social": _flag(missing_other),
                "invalid_dead_or_mismatch_site": _flag(dead),
                "quality_issues_only": _flag(quality_only),
                "no_recoverable_website_social_evidence": _flag(no_evidence),
                "quality_categories": VALUE_DELIMITER.join(sorted(categories)),
                "next_method": next_method,
                "notes": ";".join(notes),
            }
        )

    summary_rows = [
        {
            "tier_bucket": tier,
            "next_method": method,
            **{key: str(value) for key, value in counts.items()},
        }
        for (tier, method), counts in sorted(summary.items())
    ]
    _write_csv(output_dir / "missing_data_backlog_summary.csv", SUMMARY_HEADERS, summary_rows)
    _write_csv(output_dir / "missing_data_backlog.csv", BACKLOG_HEADERS, actionable)

    splits = {
        "missing_phone.csv": "missing_phone",
        "missing_whatsapp.csv": "missing_whatsapp",
        "missing_linkedin.csv": "missing_linkedin",
        "missing_other_social.csv": "missing_other_social",
        "invalid_dead_mismatch_sites.csv": "invalid_dead_or_mismatch_site",
        "quality_issues_only.csv": "quality_issues_only",
        "no_recoverable_evidence.csv": "no_recoverable_website_social_evidence",
    }
    split_counts = {}
    for filename, flag in splits.items():
        rows = [row for row in actionable if row[flag] == "true"]
        _write_csv(output_dir / filename, BACKLOG_HEADERS, rows)
        split_counts[filename] = len(rows)

    return {
        "master_rows": len(master_rows),
        "remaining_incomplete_accounts": remaining_incomplete,
        "actionable_rows": len(actionable),
        "gap_totals": dict(gap_totals),
        "method_totals": dict(method_totals),
        "summary_rows": len(summary_rows),
        "split_counts": split_counts,
        "summary_csv": str((output_dir / "missing_data_backlog_summary.csv").resolve()),
        "backlog_csv": str((output_dir / "missing_data_backlog.csv").resolve()),
    }


def render_closure_report(stats: dict[str, object]) -> str:
    plans = stats["plan_only"]["claimed_tiers"]  # type: ignore[index]
    queue_lines = [
        f"- `{label}` pending_queue_total = **{plans[label]['pending_queue_total']}**"
        for label in CLAIMED_TIERS
    ]
    other = stats["plan_only"]["other_labeled_tiers"]  # type: ignore[index]
    gaps = stats["backlog"]["gap_totals"]  # type: ignore[index]
    methods = stats["backlog"]["method_totals"]  # type: ignore[index]
    cleanup = stats["cleanup"]
    lines = [
        "# Final Agent Reach + Master Patch Closure",
        "",
        "Review-only closure after ANTI-ICP completion. No production write.",
        "No original master overwrite. No Downloads overwrite. No Phase 7.",
        "",
        f"Generated at (UTC): `{stats['generated_at']}`",
        "",
        "## Headline counts",
        "",
        f"- إجمالي ready rows النهائي: **{stats['final_ready_rows']}**",
        f"- إجمالي الحسابات الفريدة التي حصلت على بيانات: **{stats['unique_accounts_enriched']}**",
        f"- إجمالي quality issues: **{stats['quality_issue_count']}**",
        f"- إجمالي الحسابات التي بقيت ناقصة بعد Agent Reach: "
        f"**{stats['backlog']['remaining_incomplete_accounts']}**",
        "",
        "## Queue confirmation (`--plan-only` equivalent via coordinator `write_plan`)",
        "",
        *queue_lines,
        f"- Other labeled tiers with usable-domain unattempted accounts: **{other or 0}**",
        f"- All remaining eligible pending: **{stats['plan_only']['all_pending_total']}**",
        "",
        "## Ready-row FP cleanup",
        "",
        f"- Source workbook (not overwritten): `{stats['source_workbook']}`",
        f"- Final review workbook: `{stats['final_workbook']}`",
        f"- Ready rows before: **{cleanup['ready_rows_before']}**",
        f"- Ready rows after: **{cleanup['ready_rows_after']}**",
        f"- Deleted FP rows: **{cleanup['deleted_rows']}**",
        f"- Recovered/split values: **{cleanup['recovered_or_split']}**",
        f"- Inspector flagged after cleanup: **{stats['flagged_after']}**",
        "",
        "## توزيع النواقص حسب النوع + تصنيف طريقة الإكمال",
        "",
        f"- missing phone: **{gaps.get('missing_phone', 0)}**",
        f"- missing WhatsApp: **{gaps.get('missing_whatsapp', 0)}**",
        f"- missing LinkedIn: **{gaps.get('missing_linkedin', 0)}**",
        f"- missing Instagram/X/Facebook/TikTok/YouTube/Snapchat: "
        f"**{gaps.get('missing_other_social', 0)}**",
        f"- invalid/dead/domain-mismatch sites: "
        f"**{gaps.get('invalid_dead_or_mismatch_site', 0)}**",
        f"- quality issues only: **{gaps.get('quality_issues_only', 0)}**",
        f"- no recoverable website/social evidence: "
        f"**{gaps.get('no_recoverable_website_social_evidence', 0)}**",
        "",
        f"- {METHOD_HUMAN}: **{methods.get(METHOD_HUMAN, 0)}**",
        f"- {METHOD_EXTERNAL}: **{methods.get(METHOD_EXTERNAL, 0)}**",
        f"- {METHOD_DOMAIN}: **{methods.get(METHOD_DOMAIN, 0)}**",
        f"- {METHOD_INSUFFICIENT}: **{methods.get(METHOD_INSUFFICIENT, 0)}**",
        "",
        "## Paths",
        "",
        f"- مسار final workbook: `{stats['final_workbook']}`",
        f"- مسار final master patch: `{stats['output_dir']}`",
        f"- مسار missing-data backlog: `{stats['backlog']['backlog_csv']}`",
        f"- Backlog summary: `{stats['backlog']['summary_csv']}`",
        "",
        "## Tests / Ruff",
        "",
        f"- pytest: `{stats['pytest']}`",
        f"- ruff: `{stats['ruff']}`",
        "",
        "## Safety confirmation",
        "",
        f"- Original master CSV size/mtime before: `{stats['master_before']['size']}` / "
        f"`{stats['master_before']['mtime_utc']}`",
        f"- Original master CSV size/mtime after: `{stats['master_after']['size']}` / "
        f"`{stats['master_after']['mtime_utc']}`",
        f"- Original master unchanged: **{stats['master_unchanged']}**",
        f"- Cycle_13 workbook unchanged: **{stats['source_workbook_unchanged']}**",
        f"- 191600Z patch dir unchanged: **{stats['prior_patch_unchanged']}**",
        f"- Downloads workbook observed only: `{stats['downloads_workbook_note']}`",
        "- Production DB: not opened, not written.",
        "",
        "AGENT REACH COVERAGE COMPLETE",
        "MASTER PATCH REVIEW-ONLY",
        "MISSING DATA BACKLOG CREATED",
        "PRODUCTION NOT APPROVED",
        "",
    ]
    return "\n".join(lines)


def run_closure(  # noqa: PLR0913
    *,
    workbook_path: Path,
    master_csv_path: Path,
    output_dir: Path,
    report_path: Path,
    prior_patch_dir: Path,
    downloads_workbook: Path | None,
    pytest_result: str = "not validated",
    ruff_result: str = "not validated",
) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    master_before = file_snapshot(master_csv_path)
    source_before = file_snapshot(workbook_path)
    prior_before = file_snapshot(prior_patch_dir)
    downloads_note = "no Downloads Agent Reach workbook used as a write target"
    if downloads_workbook is not None:
        snap = file_snapshot(downloads_workbook)
        downloads_note = (
            f"observed `{snap['path']}` size={snap['size']} mtime_utc={snap['mtime_utc']}"
        )

    plan_only = confirm_plan_only(master_csv_path, workbook_path, output_dir / "plan_only")
    leftover = [
        (label, record["ids"])
        for label, record in plan_only["claimed_tiers"].items()
        if record["pending_queue_total"]
    ]
    if leftover:
        raise RuntimeError(f"eligible unattempted accounts remain: {leftover}")

    cleaned_workbook = output_dir / WORKBOOK_NAME
    cleanup = clean_ready_workbook(workbook_path, cleaned_workbook)
    ready_after = load_ready_rows_from_workbook(cleaned_workbook)
    inspection = inspect_ready_rows(ready_after)
    (output_dir / "cleanup_stats.json").write_text(
        json.dumps({"cleanup": cleanup, "inspection": {
            "flagged_count": len(inspection["flagged"]),
            "reason_counts": inspection["reason_counts"],
            "flagged": inspection["flagged"],
        }}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    if inspection["flagged"]:
        raise RuntimeError(
            f"ready-row guards still flag {len(inspection['flagged'])} values after cleanup"
        )

    patch_stats = run_patch(
        workbook_path=cleaned_workbook,
        master_csv_path=master_csv_path,
        output_dir=output_dir,
        report_path=output_dir / "MASTER_ENRICHMENT_PATCH_REPORT.md",
        downloads_workbook=downloads_workbook,
    )
    from agent_reach_master_enrichment_patch import (  # local to reuse loaded patches
        build_account_patches,
        load_workbook_records,
    )

    ready_records, issues = load_workbook_records(cleaned_workbook)
    patches = build_account_patches(ready_records, issues)
    for account_id in patch_stats["unmatched_ids"]:  # type: ignore[union-attr]
        if account_id in patches:
            patches[account_id].unmatched = True
    backlog = build_missing_data_backlog(master_csv_path, patches, output_dir)

    master_after = file_snapshot(master_csv_path)
    source_after = file_snapshot(workbook_path)
    prior_after = file_snapshot(prior_patch_dir)
    stats: dict[str, object] = {
        "generated_at": datetime.now(UTC).isoformat(),
        "source_workbook": str(workbook_path.resolve()),
        "final_workbook": str(cleaned_workbook.resolve()),
        "output_dir": str(output_dir.resolve()),
        "final_ready_rows": cleanup["ready_rows_after"],
        "unique_accounts_enriched": patch_stats["unique_accounts_enriched"],
        "quality_issue_count": patch_stats["quality_issue_count"],
        "cleanup": cleanup,
        "flagged_after": len(inspection["flagged"]),
        "plan_only": plan_only,
        "backlog": backlog,
        "pytest": pytest_result,
        "ruff": ruff_result,
        "master_before": master_before,
        "master_after": master_after,
        "master_unchanged": master_before == master_after,
        "source_workbook_unchanged": source_before == source_after,
        "prior_patch_unchanged": prior_before == prior_after,
        "downloads_workbook_note": downloads_note,
    }
    report = render_closure_report(stats)
    report_path.write_text(report, encoding="utf-8")
    (output_dir / "FINAL_AGENT_REACH_MASTER_PATCH_CLOSURE.md").write_text(
        report, encoding="utf-8"
    )
    (output_dir / "closure_stats.json").write_text(
        json.dumps(stats, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    stats["report_path"] = str(report_path.resolve())
    return stats


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Final Agent Reach + master patch closure.")
    parser.add_argument(
        "--workbook",
        type=Path,
        default=(
            BACKEND_ROOT
            / "outputs"
            / "agent_reach_contact_enrichment"
            / "20260906T182856Z_antiicp_loop"
            / "cycle_13_20260906T191133Z"
            / WORKBOOK_NAME
        ),
    )
    parser.add_argument(
        "--master-csv",
        type=Path,
        default=Path.home() / "Downloads" / "MUHIDE_extracted" / "01_Master_Accounts.csv",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=(
            BACKEND_ROOT
            / "outputs"
            / "agent_reach_contact_enrichment"
            / f"{_timestamp()}_final_closure"
        ),
    )
    parser.add_argument(
        "--report-path",
        type=Path,
        default=(
            BACKEND_ROOT
            / "outputs"
            / "agent_reach_contact_enrichment"
            / "FINAL_AGENT_REACH_MASTER_PATCH_CLOSURE.md"
        ),
    )
    parser.add_argument(
        "--prior-patch-dir",
        type=Path,
        default=(
            BACKEND_ROOT
            / "outputs"
            / "agent_reach_contact_enrichment"
            / "20260906T191600Z_master_patch"
        ),
    )
    parser.add_argument(
        "--downloads-workbook",
        type=Path,
        default=Path.home() / "Downloads" / "14_Website_Phone_Social_Enrichment_InProgress.xlsx",
    )
    parser.add_argument("--pytest-result", default="not validated")
    parser.add_argument("--ruff-result", default="not validated")
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    stats = run_closure(
        workbook_path=args.workbook,
        master_csv_path=args.master_csv,
        output_dir=args.output_dir,
        report_path=args.report_path,
        prior_patch_dir=args.prior_patch_dir,
        downloads_workbook=args.downloads_workbook,
        pytest_result=args.pytest_result,
        ruff_result=args.ruff_result,
    )
    print(f"output_dir={stats['output_dir']}")
    print(f"final_workbook={stats['final_workbook']}")
    print(f"final_ready_rows={stats['final_ready_rows']}")
    print(f"unique_accounts_enriched={stats['unique_accounts_enriched']}")
    print(f"quality_issue_count={stats['quality_issue_count']}")
    print(f"report_path={stats['report_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
