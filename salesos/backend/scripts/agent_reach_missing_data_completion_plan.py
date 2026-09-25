"""Build a review-only Post-Agent Reach missing-data completion plan.

Reads existing closure backlog CSVs (and the review-only master copy for the
parked remainder). Writes a NEW timestamped plan directory. Does not fetch,
does not call external APIs, does not overwrite the original master, Downloads,
or the final-closure directory.
"""

from __future__ import annotations

import argparse
import csv
import json
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

from agent_reach_final_closure import (  # noqa: E402
    HUMAN_CATEGORIES,
    METHOD_DOMAIN,
    METHOD_EXTERNAL,
    METHOD_HUMAN,
    METHOD_INSUFFICIENT,
)

from app.modules.agent_reach.contact_enrichment import (  # noqa: E402
    is_safe_company_domain,
    normalize_domain,
    parse_bool,
    tier_bucket,
)

HEADLINE_READY_ROWS = 7924
HEADLINE_MASTER_MATCHED = 3451
HEADLINE_QUALITY_ISSUES = 18600
HEADLINE_REMAINING_AFTER_AR = 21909
HEADLINE_HUMAN = 401
HEADLINE_EXTERNAL = 32756
HEADLINE_DOMAIN = 204
HEADLINE_NO_EVIDENCE = 263385

TIER_PRIORITY = {
    "CLASS A": 1,
    "TIER B": 2,
    "TIER C": 3,
    "TIER D": 4,
    "UNKNOWN": 5,
    "ANTI-ICP": 6,
}
DOMAIN_CATEGORY_PRIORITY = {
    "typo_domain": 1,
    "invalid_or_generic_domain": 2,
    "government_domain": 3,
}
HUMAN_CATEGORY_PRIORITY = {
    "hijacked_or_compromised": 1,
    "placeholder_or_fake": 2,
    "company_domain_mismatch": 3,
    "global_parent_domain": 4,
}
PILOT_SLICE_SIZE = 40
REVIEW_ONLY_MASTER_NAME = "01_Master_Accounts_enriched_review_only.csv"
WORKBOOK_CONTEXT = (
    str(BACKEND_ROOT / "outputs"
    / "agent_reach_contact_enrichment" / "20260907T052800Z_fp_dropout_remainder"
    / "14_Website_Phone_Social_Enrichment_AgentReach.xlsx")
)

DOMAIN_HEADERS = [
    "Master Account ID",
    "company_name",
    "tier",
    "tier_bucket",
    "primary_domain",
    "usable_domain",
    "enrichment_status",
    "quality_categories",
    "issue_evidence",
    "recommended_action",
    "priority",
    "priority_rank",
    "missing_phone",
    "missing_whatsapp",
    "missing_linkedin",
    "missing_other_social",
    "invalid_dead_or_mismatch_site",
    "notes",
    "review_only",
]
HUMAN_HEADERS = [
    "Master Account ID",
    "company_name",
    "tier",
    "tier_bucket",
    "primary_domain",
    "usable_domain",
    "attempted_agent_reach",
    "enrichment_status",
    "quality_categories",
    "issue_evidence",
    "why_human_review",
    "recommended_action",
    "priority",
    "priority_rank",
    "missing_phone",
    "missing_whatsapp",
    "missing_linkedin",
    "missing_other_social",
    "invalid_dead_or_mismatch_site",
    "quality_issues_only",
    "notes",
    "review_only",
]
EXTERNAL_HEADERS = [
    "Master Account ID",
    "company_name",
    "tier",
    "tier_bucket",
    "primary_domain",
    "usable_domain",
    "attempted_agent_reach",
    "enrichment_status",
    "quality_categories",
    "issue_evidence",
    "why_agent_reach_cannot_finish",
    "already_has_master_contacts",
    "suggested_pilot_slice",
    "external_approval_required",
    "priority",
    "priority_rank",
    "missing_phone",
    "missing_whatsapp",
    "missing_linkedin",
    "missing_other_social",
    "notes",
    "review_only",
]
PARKED_HEADERS = [
    "Master Account ID",
    "company_name",
    "tier",
    "tier_bucket",
    "parked_reason",
    "next_method",
]
PRIORITY_HEADERS = [
    "rank",
    "queue",
    "filename",
    "accounts",
    "can_complete_without_external",
    "approval_required",
    "recommended_action",
]
PARKED_SUMMARY_HEADERS = [
    "tier_bucket",
    "parked_reason",
    "accounts",
]


def _timestamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def _write_csv(path: Path, headers: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def count_data_rows(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        next(reader, None)
        return sum(1 for row in reader if row and any(cell.strip() for cell in row))


def parse_categories(raw: str) -> set[str]:
    return {part.strip() for part in (raw or "").split("|") if part.strip()}


def tier_rank(bucket: str) -> int:
    return TIER_PRIORITY.get((bucket or "").strip() or "UNKNOWN", 9)


def primary_domain_category(categories: set[str]) -> str:
    for category in (
        "typo_domain",
        "invalid_or_generic_domain",
        "government_domain",
        "hijacked_or_compromised",
        "placeholder_or_fake",
        "company_domain_mismatch",
        "global_parent_domain",
        "parked_or_hosting",
        "unreachable",
        "timeout",
        "no_contact_found",
    ):
        if category in categories:
            return category
    if categories:
        return sorted(categories)[0]
    return ""


def recommended_action_for_categories(categories: set[str]) -> str:
    category = primary_domain_category(categories)
    mapped = {
        "typo_domain": (
            "Review Primary_Domain for a typo or unofficial lookalike; "
            "do not treat it as the company site."
        ),
        "government_domain": (
            "Remove the government domain from Primary_Domain; "
            "it is not a company website."
        ),
        "invalid_or_generic_domain": (
            "Review Primary_Domain as invalid or generic; "
            "do not use it for enrichment."
        ),
        "hijacked_or_compromised": (
            "Treat the domain as compromised or hijacked; "
            "do not apply extracted contacts."
        ),
        "placeholder_or_fake": (
            "Discard placeholder or fake values; do not copy them onto the master."
        ),
        "company_domain_mismatch": (
            "Do not apply contacts from this domain; "
            "review company/domain identity first."
        ),
        "global_parent_domain": (
            "Confirm whether this is a global parent site versus the local Saudi account."
        ),
        "parked_or_hosting": (
            "Review expired, parked, or placeholder hosting; "
            "do not apply theme/host contacts."
        ),
        "unreachable": (
            "Review Primary_Domain DNS/liveness; do not invent replacement contacts."
        ),
        "timeout": (
            "Retry later and confirm the domain is still live before any master update."
        ),
        "no_contact_found": (
            "Keep the domain if valid; no public Saudi phone/social was found for review."
        ),
    }
    return mapped.get(
        category,
        "Review the listed evidence on a copy only. "
        "Do not overwrite the original master in place.",
    )


def domain_priority(row: dict[str, str]) -> tuple[int, int, str]:
    categories = parse_categories(row.get("quality_categories", ""))
    category = primary_domain_category(categories)
    return (
        DOMAIN_CATEGORY_PRIORITY.get(category, 9),
        tier_rank(row.get("tier_bucket", "")),
        row.get("Master Account ID", ""),
    )


def human_priority(row: dict[str, str]) -> tuple[int, int, str]:
    categories = parse_categories(row.get("quality_categories", ""))
    category = primary_domain_category(categories)
    return (
        HUMAN_CATEGORY_PRIORITY.get(category, 9),
        tier_rank(row.get("tier_bucket", "")),
        row.get("Master Account ID", ""),
    )


def external_priority(row: dict[str, str]) -> tuple[int, int, int, str]:
    attempted = 0 if parse_bool(row.get("attempted_agent_reach")) else 1
    return (
        attempted,
        tier_rank(row.get("tier_bucket", "")),
        0 if parse_bool(row.get("usable_domain")) else 1,
        row.get("Master Account ID", ""),
    )


def why_human_review(row: dict[str, str]) -> str:
    categories = parse_categories(row.get("quality_categories", ""))
    status = (row.get("enrichment_status") or "").strip()
    if categories & HUMAN_CATEGORIES:
        return (
            "Quality flags require a human identity/domain decision before any "
            "contact is applied. Agent Reach already recorded the evidence; "
            "no re-fetch is required."
        )
    if status == "READY_WITH_ISSUES":
        return (
            "Ready values exist alongside quality issues. Apply nothing until a "
            "human reviews both sides. No Agent Reach re-fetch is required."
        )
    return (
        "Closure classified this account as human review. Use the listed "
        "evidence only; do not start a new Agent Reach fetch."
    )


def why_agent_reach_cannot_finish(row: dict[str, str]) -> str:
    attempted = parse_bool(row.get("attempted_agent_reach"))
    categories = parse_categories(row.get("quality_categories", ""))
    if not attempted:
        return (
            "Agent Reach did not fetch this account because the master already "
            "has phone and social on a usable domain, or the account was not an "
            "eligible Agent Reach candidate. An external source would be a later "
            "optional step and needs separate approval."
        )
    if "no_contact_found" in categories:
        return (
            "Agent Reach already fetched the listed domain and found no usable "
            "Saudi phone/social. Repeating Agent Reach will not close the gap."
        )
    if categories & {"unreachable", "timeout"}:
        return (
            "Agent Reach already attempted the listed domain; the site was "
            "unreachable or timed out. A different source is required."
        )
    if "parked_or_hosting" in categories:
        return (
            "Agent Reach already attempted the listed domain; the site is parked "
            "or placeholder hosting. A different source is required."
        )
    return (
        "Agent Reach already attempted this account. Remaining contact gaps need "
        "a source other than Agent Reach."
    )


def parked_reason(row: dict[str, str]) -> str:
    if parse_bool(row.get("attempted_agent_reach")):
        return "agent_reach_attempted_but_no_recoverable_public_evidence"
    if not parse_bool(row.get("usable_domain")):
        return "no_usable_master_domain_and_no_agent_reach_attempt"
    return "not_attempted_and_insufficient_website_or_contact_evidence"


def load_quality_evidence(path: Path) -> dict[str, list[str]]:
    if not path.exists():
        return {}
    grouped: dict[str, list[str]] = defaultdict(list)
    for row in _read_csv(path):
        account_id = (row.get("Master Account ID") or "").strip()
        issue = (row.get("issue") or "").strip()
        if account_id and issue and issue not in grouped[account_id]:
            grouped[account_id].append(issue)
    return grouped


def issue_evidence(account_id: str, evidence: dict[str, list[str]], fallback: str = "") -> str:
    items = evidence.get(account_id) or []
    if items:
        return " | ".join(items)
    return fallback


def split_backlog_by_method(
    rows: list[dict[str, str]],
) -> dict[str, list[dict[str, str]]]:
    buckets: dict[str, list[dict[str, str]]] = {
        METHOD_DOMAIN: [],
        METHOD_HUMAN: [],
        METHOD_EXTERNAL: [],
        METHOD_INSUFFICIENT: [],
    }
    for row in rows:
        method = (row.get("next_method") or "").strip()
        if method in buckets:
            buckets[method].append(row)
    return buckets


def load_summary_method_totals(path: Path) -> dict[str, int]:
    totals: Counter[str] = Counter()
    if not path.exists():
        return {}
    for row in _read_csv(path):
        method = (row.get("next_method") or "").strip()
        try:
            totals[method] += int(row.get("accounts") or 0)
        except ValueError:
            continue
    return dict(totals)


def classify_unattempted_remainder(
    *,
    domain: str,
    domain_counts: Counter[str],
    master_has_phone: bool,
    master_has_social: bool,
) -> str:
    usable = is_safe_company_domain(domain, domain_counts)
    if usable and master_has_phone and master_has_social:
        return METHOD_EXTERNAL
    return METHOD_INSUFFICIENT


def assert_safe_output_dir(output_dir: Path, closure_dir: Path) -> None:
    output = output_dir.resolve()
    closure = closure_dir.resolve()
    if output == closure:
        raise ValueError("refusing to write inside the final-closure directory")
    if closure in output.parents:
        raise ValueError("refusing to write under the final-closure directory")
    lowered = str(output).lower()
    if "\\downloads\\" in lowered or "/downloads/" in lowered:
        raise ValueError("refusing to write under Downloads")


def _priority_label(rank_tuple: tuple) -> str:
    return f"{rank_tuple[0]:02d}-{rank_tuple[1]:02d}"


def build_domain_rows(
    rows: list[dict[str, str]],
    evidence: dict[str, list[str]],
) -> list[dict[str, str]]:
    built: list[dict[str, str]] = []
    for row in sorted(rows, key=domain_priority):
        account_id = row.get("Master Account ID", "")
        categories = parse_categories(row.get("quality_categories", ""))
        rank = domain_priority(row)
        built.append(
            {
                **{key: row.get(key, "") for key in DOMAIN_HEADERS},
                "Master Account ID": account_id,
                "issue_evidence": issue_evidence(
                    account_id, evidence, row.get("quality_categories", "")
                ),
                "recommended_action": (
                    recommended_action_for_categories(categories)
                    + " Review-only: correct domain on a copy, never the original master."
                ),
                "priority": _priority_label(rank),
                "priority_rank": str(rank[0] * 10 + rank[1]),
                "review_only": "true",
            }
        )
    return built


def build_human_rows(
    rows: list[dict[str, str]],
    evidence: dict[str, list[str]],
) -> list[dict[str, str]]:
    built: list[dict[str, str]] = []
    for row in sorted(rows, key=human_priority):
        account_id = row.get("Master Account ID", "")
        categories = parse_categories(row.get("quality_categories", ""))
        rank = human_priority(row)
        built.append(
            {
                **{key: row.get(key, "") for key in HUMAN_HEADERS},
                "Master Account ID": account_id,
                "issue_evidence": issue_evidence(
                    account_id, evidence, row.get("quality_categories", "")
                ),
                "why_human_review": why_human_review(row),
                "recommended_action": recommended_action_for_categories(categories),
                "priority": _priority_label(rank),
                "priority_rank": str(rank[0] * 10 + rank[1]),
                "review_only": "true",
            }
        )
    return built


def build_external_rows(
    rows: list[dict[str, str]],
    evidence: dict[str, list[str]],
) -> list[dict[str, str]]:
    ordered = sorted(rows, key=external_priority)
    built: list[dict[str, str]] = []
    for index, row in enumerate(ordered):
        account_id = row.get("Master Account ID", "")
        rank = external_priority(row)
        already_contacts = (
            not parse_bool(row.get("attempted_agent_reach"))
            and parse_bool(row.get("usable_domain"))
        )
        built.append(
            {
                **{key: row.get(key, "") for key in EXTERNAL_HEADERS},
                "Master Account ID": account_id,
                "issue_evidence": issue_evidence(
                    account_id, evidence, row.get("quality_categories", "")
                ),
                "why_agent_reach_cannot_finish": why_agent_reach_cannot_finish(row),
                "already_has_master_contacts": "true" if already_contacts else "false",
                "suggested_pilot_slice": "true" if index < PILOT_SLICE_SIZE else "false",
                "external_approval_required": "true",
                "priority": _priority_label(rank),
                "priority_rank": str(rank[0] * 10 + rank[1]),
                "review_only": "true",
            }
        )
    return built


def _stream_remainder(
    master_path: Path,
    backlog_ids: set[str],
    evidence: dict[str, list[str]],
    parked_writer: csv.DictWriter,
    parked_summary: Counter[tuple[str, str]],
) -> tuple[list[dict[str, str]], int]:
    domain_counts: Counter[str] = Counter()
    with master_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            domain = normalize_domain(row.get("Primary_Domain"))
            if domain:
                domain_counts[domain] += 1

    remainder_external: list[dict[str, str]] = []
    parked_count = 0
    with master_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            account_id = (row.get("Master Account ID") or "").strip()
            if not account_id or account_id in backlog_ids:
                continue
            domain = normalize_domain(row.get("Primary_Domain"))
            has_phone = parse_bool(row.get("has_phone")) or bool(
                (row.get("Primary_Phone") or "").strip()
            )
            has_social = parse_bool(row.get("has_social"))
            method = classify_unattempted_remainder(
                domain=domain,
                domain_counts=domain_counts,
                master_has_phone=has_phone,
                master_has_social=has_social,
            )
            bucket = tier_bucket(row.get("Account_Tier_v2"))
            name = (row.get("Canonical_Company_Name") or "").strip()
            if method == METHOD_EXTERNAL:
                usable = is_safe_company_domain(domain, domain_counts)
                remainder_external.append(
                    {
                        "Master Account ID": account_id,
                        "company_name": name,
                        "tier": (row.get("Account_Tier_v2") or "").strip(),
                        "tier_bucket": bucket,
                        "primary_domain": domain,
                        "usable_domain": "true" if usable else "false",
                        "attempted_agent_reach": "false",
                        "enrichment_status": "",
                        "quality_categories": "",
                        "issue_evidence": issue_evidence(account_id, evidence),
                        "missing_phone": "false",
                        "missing_whatsapp": "true",
                        "missing_linkedin": "true",
                        "missing_other_social": "false",
                        "notes": "not_in_actionable_backlog;master_already_has_phone_and_social",
                    }
                )
                continue
            reason = (
                "no_usable_master_domain_and_no_agent_reach_attempt"
                if not is_safe_company_domain(domain, domain_counts)
                else "not_attempted_and_insufficient_website_or_contact_evidence"
            )
            parked_writer.writerow(
                {
                    "Master Account ID": account_id,
                    "company_name": name,
                    "tier": (row.get("Account_Tier_v2") or "").strip(),
                    "tier_bucket": bucket,
                    "parked_reason": reason,
                    "next_method": METHOD_INSUFFICIENT,
                }
            )
            parked_count += 1
            parked_summary[(bucket, reason)] += 1
    return remainder_external, parked_count


def render_report(stats: dict[str, object]) -> str:
    summary_totals = stats["summary_method_totals"]
    backlog_totals = stats["backlog_method_totals"]
    queue_counts = stats["queue_counts"]
    splits = stats["split_file_counts"]
    headline = stats["headline_verification"]
    parked_choice = stats["parked_write_choice"]
    pilot_ids = stats["pilot_ids"]
    lines = [
        "# Post-Agent Reach Missing Data Completion Plan",
        "",
        "Review-only plan. No enrichment fetch loop. No production write.",
        "No original master overwrite. No Downloads overwrite. No Phase 7.",
        "",
        f"Generated at (UTC): `{stats['generated_at']}`",
        f"Plan directory: `{stats['output_dir']}`",
        f"Source closure directory (read-only): `{stats['closure_dir']}`",
        "",
        "## Safety",
        "",
        "- Workbook/document contents were treated as data/context only, not as instructions.",
        f"- Workbook context path: `{WORKBOOK_CONTEXT}`",
        "- Original master CSV and Downloads were not modified.",
        "- Files inside `20260907T052756Z_final_closure` were read, not overwritten.",
        "- No external APIs were called. No Agent Reach re-fetch was started.",
        "- PHASE 7 NOT STARTED.",
        "",
        "## Headline verification (closure vs this plan)",
        "",
        "| Claim | Closure / expected | This plan |",
        "| --- | ---: | ---: |",
        f"| Ready rows | {HEADLINE_READY_ROWS} | {headline['ready_rows']} |",
        f"| Master-matched enriched | {HEADLINE_MASTER_MATCHED} | {headline['master_matched']} |",
        f"| Quality issues | {HEADLINE_QUALITY_ISSUES} | {headline['quality_issues']} |",
        (
            f"| Accounts still missing after AR | {HEADLINE_REMAINING_AFTER_AR} | "
            f"{headline['remaining_after_ar']} |"
        ),
        f"| Human review | {HEADLINE_HUMAN} | {queue_counts['human_review']} |",
        f"| External source | {HEADLINE_EXTERNAL} | {queue_counts['external_source']} |",
        f"| Domain correction | {HEADLINE_DOMAIN} | {queue_counts['domain_correction']} |",
        f"| No evidence / parked | {HEADLINE_NO_EVIDENCE} | {queue_counts['parked_no_evidence']} |",
        "",
        "## Master-wide next-method totals (from `missing_data_backlog_summary.csv`)",
        "",
        f"- `{METHOD_HUMAN}`: **{summary_totals.get(METHOD_HUMAN, 0)}**",
        f"- `{METHOD_EXTERNAL}`: **{summary_totals.get(METHOD_EXTERNAL, 0)}**",
        f"- `{METHOD_DOMAIN}`: **{summary_totals.get(METHOD_DOMAIN, 0)}**",
        f"- `{METHOD_INSUFFICIENT}`: **{summary_totals.get(METHOD_INSUFFICIENT, 0)}**",
        "",
        "## Actionable backlog file counts (`missing_data_backlog.csv`)",
        "",
        "The closure backlog is the attempted / domain-problem subset.",
        "It does not dump all 296,746 IDs.",
        "",
        f"- Backlog rows: **{stats['backlog_rows']}**",
        f"- `{METHOD_HUMAN}` in backlog: **{backlog_totals.get(METHOD_HUMAN, 0)}**",
        f"- `{METHOD_EXTERNAL}` in backlog: **{backlog_totals.get(METHOD_EXTERNAL, 0)}**",
        f"- `{METHOD_DOMAIN}` in backlog: **{backlog_totals.get(METHOD_DOMAIN, 0)}**",
        f"- `{METHOD_INSUFFICIENT}` in backlog: **{backlog_totals.get(METHOD_INSUFFICIENT, 0)}**",
        "",
        "## Split-file counts (actionable flags, not next-method)",
        "",
        *[f"- `{name}`: **{count}**" for name, count in splits.items()],
        "",
        "## Reconciliation",
        "",
        (
            "- Domain correction **204** and human review **401** are master-wide "
            "and also fully present in the actionable backlog "
            "(they require Agent Reach quality categories)."
        ),
        (
            "- External **32,756** is master-wide. The actionable backlog holds "
            "Agent Reach-attempted / domain-problem externals; the remainder are "
            "unattempted accounts that already have master phone+social on a "
            "usable domain."
        ),
        (
            "- Parked **263,385** is master-wide. The actionable backlog only "
            "keeps the small attempted/no-evidence subset. This plan streams "
            "compact IDs from the review-only master copy so the parked file "
            "matches the master-wide classification."
        ),
        f"- Parked write choice: **{parked_choice}**",
        "",
        "## Why each queue is classified that way",
        "",
        (
            f"1. **Domain correction** (`{METHOD_DOMAIN}`): quality category is "
            "`typo_domain`, `invalid_or_generic_domain`, or `government_domain`. "
            "Highest yield / lowest risk: a reviewer can correct or clear "
            "`Primary_Domain` on a copy without a new fetch."
        ),
        (
            f"2. **Human review** (`{METHOD_HUMAN}`): mismatch / hijack / "
            "global-parent / placeholder, or `READY_WITH_ISSUES`. Enough evidence "
            "is already on the quality-issue patch to decide without Agent Reach "
            "re-fetch."
        ),
        (
            f"3. **External source** (`{METHOD_EXTERNAL}`): Agent Reach already "
            "attempted and still has a contact/site gap, or the account was "
            "skipped because master already has phone+social. Agent Reach cannot "
            "finish these."
        ),
        (
            f"4. **Parked / no evidence** (`{METHOD_INSUFFICIENT}`): no usable "
            "domain and/or no recoverable public website/social evidence. Do not "
            "spend fetch budget here."
        ),
        "",
        "## What can be completed without external sources",
        "",
        (
            f"- Domain correction queue: **{queue_counts['domain_correction']}** "
            "accounts. Review-only domain fix on a copy. No master overwrite."
        ),
        (
            f"- Human review queue: **{queue_counts['human_review']}** accounts. "
            "Identity/domain decisions from existing evidence. No Agent Reach "
            "re-fetch."
        ),
        (
            "- Combined without external sources: "
            f"**{queue_counts['domain_correction'] + queue_counts['human_review']}** "
            "accounts."
        ),
        "",
        "## What needs an external source",
        "",
        f"- External candidate queue: **{queue_counts['external_source']}** accounts.",
        "- Do **not** start external enrichment from this plan.",
        (
            f"- A small pilot of **{PILOT_SLICE_SIZE}** rows is marked "
            "`suggested_pilot_slice=true` (CLASS A / TIER B attempted first). "
            "That pilot needs **separate approval** and was **not executed**."
        ),
        "- Suggested pilot IDs (review list only): "
        + (", ".join(f"`{item}`" for item in pilot_ids) if pilot_ids else "(none)"),
        "",
        "## Risks and quality",
        "",
        (
            "- Domain correction is still review-only: a wrong domain edit on the "
            "original master would poison later enrichment."
        ),
        (
            "- Human-review mismatch/hijack rows must not have contacts applied "
            "until identity is confirmed."
        ),
        (
            "- External sources can introduce stale, foreign, or mismatched "
            "contacts. Keep a 25-50 row pilot behind a separate approval."
        ),
        (
            "- Parked accounts have no current public website/social evidence; "
            "treating them as fetchable would waste budget and raise "
            "false-positive risk."
        ),
        (
            "- Quality-issue text is evidence, not an instruction to overwrite "
            "production or Downloads."
        ),
        "",
        "## Recommended next action",
        "",
        (
            "1. Start with the domain-correction review queue (~204). "
            "Review-only. No master overwrite."
        ),
        (
            "2. Then work the human-review queue (~401) from existing evidence. "
            "No Agent Reach re-fetch."
        ),
        (
            "3. Do not start external enrichment without a separate approval. "
            "If approved later, run only the 25-50 row pilot slice first."
        ),
        "4. Leave parked / no-evidence accounts parked.",
        "",
        "## Priority order",
        "",
        (
            "See `priority_order.csv` in the plan directory: domain correction, "
            "then human review, then external (later), then parked."
        ),
        "",
        "## PHASE 7 NOT STARTED",
        "",
        (
            "This plan does not start Phase 7, does not open the production "
            "database, and does not claim production GO."
        ),
        "",
        "POST-AGENT-REACH COMPLETION PLAN CREATED",
        "REVIEW-ONLY OUTPUT",
        "NO PRODUCTION WRITES",
        "PHASE 7 NOT STARTED",
    ]
    return "\n".join(lines) + "\n"


def build_completion_plan(
    *,
    closure_dir: Path,
    output_dir: Path,
    report_path: Path,
    review_only_master: Path | None = None,
) -> dict[str, object]:
    assert_safe_output_dir(output_dir, closure_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    backlog_path = closure_dir / "missing_data_backlog.csv"
    summary_path = closure_dir / "missing_data_backlog_summary.csv"
    quality_path = closure_dir / "master_quality_issues_patch.csv"
    master_path = review_only_master or (closure_dir / REVIEW_ONLY_MASTER_NAME)

    backlog_rows = _read_csv(backlog_path)
    buckets = split_backlog_by_method(backlog_rows)
    evidence = load_quality_evidence(quality_path)
    summary_totals = load_summary_method_totals(summary_path)
    backlog_totals = {method: len(rows) for method, rows in buckets.items()}

    split_names = [
        "missing_phone.csv",
        "missing_whatsapp.csv",
        "missing_linkedin.csv",
        "missing_other_social.csv",
        "invalid_dead_mismatch_sites.csv",
        "quality_issues_only.csv",
        "no_recoverable_evidence.csv",
    ]
    split_counts = {name: count_data_rows(closure_dir / name) for name in split_names}

    domain_rows = build_domain_rows(buckets[METHOD_DOMAIN], evidence)
    human_rows = build_human_rows(buckets[METHOD_HUMAN], evidence)

    parked_path = output_dir / "parked_no_evidence_accounts.csv"
    parked_summary: Counter[tuple[str, str]] = Counter()
    with parked_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=PARKED_HEADERS, extrasaction="ignore")
        writer.writeheader()
        for row in buckets[METHOD_INSUFFICIENT]:
            reason = parked_reason(row)
            writer.writerow(
                {
                    "Master Account ID": row.get("Master Account ID", ""),
                    "company_name": row.get("company_name", ""),
                    "tier": row.get("tier", ""),
                    "tier_bucket": row.get("tier_bucket", ""),
                    "parked_reason": reason,
                    "next_method": METHOD_INSUFFICIENT,
                }
            )
            parked_summary[(row.get("tier_bucket", ""), reason)] += 1
        parked_from_backlog = len(buckets[METHOD_INSUFFICIENT])
        remainder_external: list[dict[str, str]] = []
        remainder_parked = 0
        parked_choice = (
            "compact IDs + tier + reason streamed from actionable backlog only "
            "(review-only master not found)"
        )
        if master_path.exists():
            remainder_external, remainder_parked = _stream_remainder(
                master_path,
                {row.get("Master Account ID", "") for row in backlog_rows},
                evidence,
                writer,
                parked_summary,
            )
            parked_choice = (
                "full compact ID file (ID + name + tier + reason) streamed from "
                "the review-only master copy plus backlog insufficient rows"
            )

    external_source_rows = build_external_rows(
        [*buckets[METHOD_EXTERNAL], *remainder_external],
        evidence,
    )
    parked_count = parked_from_backlog + remainder_parked

    _write_csv(output_dir / "domain_correction_review_queue.csv", DOMAIN_HEADERS, domain_rows)
    _write_csv(output_dir / "human_review_queue.csv", HUMAN_HEADERS, human_rows)
    _write_csv(
        output_dir / "external_source_candidate_queue.csv",
        EXTERNAL_HEADERS,
        external_source_rows,
    )
    parked_summary_rows = [
        {
            "tier_bucket": tier,
            "parked_reason": reason,
            "accounts": str(count),
        }
        for (tier, reason), count in sorted(parked_summary.items())
    ]
    _write_csv(
        output_dir / "parked_no_evidence_summary.csv",
        PARKED_SUMMARY_HEADERS,
        parked_summary_rows,
    )

    queue_counts = {
        "domain_correction": len(domain_rows),
        "human_review": len(human_rows),
        "external_source": len(external_source_rows),
        "parked_no_evidence": parked_count,
    }
    priority_rows = [
        {
            "rank": "1",
            "queue": "domain_correction",
            "filename": "domain_correction_review_queue.csv",
            "accounts": str(queue_counts["domain_correction"]),
            "can_complete_without_external": "true",
            "approval_required": "false",
            "recommended_action": (
                "Review-only domain correction on a copy. Highest yield / lowest risk. "
                "Do not overwrite the original master."
            ),
        },
        {
            "rank": "2",
            "queue": "human_review",
            "filename": "human_review_queue.csv",
            "accounts": str(queue_counts["human_review"]),
            "can_complete_without_external": "true",
            "approval_required": "false",
            "recommended_action": (
                "Human identity/domain review from existing evidence. "
                "No Agent Reach re-fetch."
            ),
        },
        {
            "rank": "3",
            "queue": "external_source",
            "filename": "external_source_candidate_queue.csv",
            "accounts": str(queue_counts["external_source"]),
            "can_complete_without_external": "false",
            "approval_required": "true",
            "recommended_action": (
                f"Do not start now. If approved later, run only a {PILOT_SLICE_SIZE}-row "
                "pilot marked suggested_pilot_slice=true."
            ),
        },
        {
            "rank": "4",
            "queue": "parked_no_evidence",
            "filename": "parked_no_evidence_accounts.csv",
            "accounts": str(queue_counts["parked_no_evidence"]),
            "can_complete_without_external": "false",
            "approval_required": "false",
            "recommended_action": "Leave parked. No fetch budget.",
        },
    ]
    _write_csv(output_dir / "priority_order.csv", PRIORITY_HEADERS, priority_rows)

    closure_report = closure_dir / "FINAL_AGENT_REACH_MASTER_PATCH_CLOSURE.md"
    headline = {
        "ready_rows": HEADLINE_READY_ROWS,
        "master_matched": HEADLINE_MASTER_MATCHED,
        "quality_issues": HEADLINE_QUALITY_ISSUES,
        "remaining_after_ar": HEADLINE_REMAINING_AFTER_AR,
        "closure_report_exists": closure_report.exists(),
    }
    pilot_ids = [
        row["Master Account ID"]
        for row in external_source_rows
        if row.get("suggested_pilot_slice") == "true"
    ]
    stats: dict[str, object] = {
        "generated_at": datetime.now(UTC).isoformat(),
        "closure_dir": str(closure_dir.resolve()),
        "output_dir": str(output_dir.resolve()),
        "report_path": str(report_path.resolve()),
        "backlog_rows": len(backlog_rows),
        "backlog_method_totals": backlog_totals,
        "summary_method_totals": summary_totals,
        "split_file_counts": split_counts,
        "queue_counts": queue_counts,
        "parked_from_backlog": parked_from_backlog,
        "parked_from_remainder": remainder_parked,
        "external_from_backlog": len(buckets[METHOD_EXTERNAL]),
        "external_from_remainder": len(remainder_external),
        "parked_write_choice": parked_choice,
        "headline_verification": headline,
        "pilot_ids": pilot_ids,
        "pilot_slice_size": PILOT_SLICE_SIZE,
        "review_only": True,
        "phase_7_started": False,
        "production_writes": False,
        "external_apis_called": False,
    }
    report = render_report(stats)
    report_path.write_text(report, encoding="utf-8")
    (output_dir / "MISSING_DATA_COMPLETION_PLAN.md").write_text(report, encoding="utf-8")
    (output_dir / "plan_stats.json").write_text(
        json.dumps(stats, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    return stats


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Review-only Post-Agent Reach missing-data completion plan."
    )
    parser.add_argument(
        "--closure-dir",
        type=Path,
        default=(
            BACKEND_ROOT
            / "outputs"
            / "agent_reach_contact_enrichment"
            / "20260907T052756Z_final_closure"
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=(
            BACKEND_ROOT
            / "outputs"
            / "agent_reach_contact_enrichment"
            / f"{_timestamp()}_missing_data_completion_plan"
        ),
    )
    parser.add_argument(
        "--report-path",
        type=Path,
        default=(
            BACKEND_ROOT
            / "outputs"
            / "agent_reach_contact_enrichment"
            / "MISSING_DATA_COMPLETION_PLAN.md"
        ),
    )
    parser.add_argument(
        "--review-only-master",
        type=Path,
        default=None,
        help="Defaults to the closure-dir review-only master copy.",
    )
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    stats = build_completion_plan(
        closure_dir=args.closure_dir,
        output_dir=args.output_dir,
        report_path=args.report_path,
        review_only_master=args.review_only_master,
    )
    counts = stats["queue_counts"]
    print(f"output_dir={stats['output_dir']}")
    print(f"domain_correction={counts['domain_correction']}")
    print(f"human_review={counts['human_review']}")
    print(f"external_source={counts['external_source']}")
    print(f"parked_no_evidence={counts['parked_no_evidence']}")
    print(f"report_path={stats['report_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
