"""Build a review-only Human Review Queue for 401 + 7 domain-correction IDs.

Unions the missing-data human_review_queue.csv with the 7 domain-correction
needs_human_review accounts, dedupes by Master Account ID, and proposes a
decision from existing evidence only. Writes a NEW timestamped directory.
Does not fetch, does not overwrite the original master, Downloads, production
DB, or prior patch/closure dirs.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from agent_reach_domain_correction_review import (  # noqa: E402
    CLASS_HUMAN,
    HIGH_CORRECTIONS,
    HUMAN_REVIEW,
)

from app.modules.agent_reach.contact_enrichment import (  # noqa: E402
    is_safe_company_domain,
    normalize_domain,
)

EXPECTED_ORIGINAL_COUNT = 401
EXPECTED_DOMAIN_HUMAN_COUNT = 7
SOURCE_ORIGINAL = "original_401"
SOURCE_DOMAIN = "domain_correction_7"

DECIDE_APPROVE = "approve_agent_reach_value"
DECIDE_REJECT = "reject_bad_domain"
DECIDE_DOMAIN_FIX = "request_domain_fix"
DECIDE_EXTERNAL = "request_external_source"
DECIDE_PARK = "park_no_evidence"

CONF_HIGH = "high"
CONF_MEDIUM = "medium"
CONF_LOW = "low"

DEFAULT_PYTHON = sys.executable
WORKBOOK_CONTEXT = (
    str(BACKEND_ROOT / "outputs"
    / "agent_reach_contact_enrichment" / "20260907T052800Z_fp_dropout_remainder"
    / "14_Website_Phone_Social_Enrichment_AgentReach.xlsx")
)
FORBIDDEN_OUTPUT_MARKERS = (
    "20260907T052756Z_final_closure",
    "20260907T052800Z_fp_dropout_remainder",
    "20260907T054012Z_missing_data_completion_plan",
    "20260907T175703Z_domain_correction_review",
    "191600Z",
    "cycle_13",
)

MIN_DOMAIN_LABEL_LEN = 4
MIN_NAME_OVERLAP_LEN = 5
GENERIC_DOMAIN_LABELS = frozenset(
    {
        "www",
        "com",
        "net",
        "org",
        "gov",
        "edu",
        "sa",
        "co",
        "ltd",
        "llc",
        "inc",
        "group",
        "company",
        "intl",
        "int",
        "the",
        "and",
        "for",
        "of",
        "http",
        "https",
        "mail",
        "email",
    }
)
HOMEPAGE_SOCIAL_MARKERS = (
    "/x.com",
    "/twitter.com",
    "x.com/",
    "twitter.com/",
    "facebook.com/",
    "instagram.com/",
    "linkedin.com/",
    "linkedin.com",
    "youtube.com/",
    "tiktok.com/",
)
UNRELATED_HINTS = (
    "لا علاقة",
    "شركة مختلفة",
    "محتوى غير مرتبط",
    "موقع تجريبي",
    "قالب تجريبي",
    "بيانات وهمية",
    "unrelated",
    "different company",
)

UNIFIED_HEADERS = [
    "Master Account ID",
    "company_name",
    "tier",
    "tier_bucket",
    "primary_domain",
    "queue_source",
    "enrichment_status",
    "quality_categories",
    "issue_evidence",
    "domain_correction_classification",
    "corrected_domain",
    "usable_domain",
    "attempted_agent_reach",
    "why_human_review",
    "recommended_action",
    "review_only",
]
DECISION_HEADERS = [
    "Master Account ID",
    "company_name",
    "tier",
    "tier_bucket",
    "primary_domain",
    "queue_source",
    "proposed_decision",
    "confidence",
    "evidence",
    "reason",
    "suggested_domain_or_values",
    "quality_categories",
    "domain_correction_classification",
    "review_only",
]
PATCH_HEADERS = [
    "Master Account ID",
    "company_name",
    "primary_domain",
    "proposed_decision",
    "confidence",
    "AgentReach_Review_Decision",
    "AgentReach_Review_Confidence",
    "AgentReach_Suggested_Values",
    "AgentReach_Domain_Fix_Note",
    "AgentReach_Do_Not_Apply",
    "reason",
    "review_only",
    "master_overwrite",
]


@dataclass(frozen=True)
class Decision:
    proposed_decision: str
    confidence: str
    evidence: str
    reason: str
    suggested_domain_or_values: str


def _timestamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, headers: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def parse_categories(raw: str) -> set[str]:
    return {part.strip() for part in (raw or "").split("|") if part.strip()}


def assert_safe_output_dir(output_dir: Path, input_queue: Path) -> None:
    output = output_dir.resolve()
    queue = input_queue.resolve()
    if output == queue.parent:
        raise ValueError("refusing to write into the input plan directory")
    if output == queue:
        raise ValueError("refusing to overwrite the input queue path")
    lowered = str(output).lower()
    if "\\downloads\\" in lowered or "/downloads/" in lowered:
        raise ValueError("refusing to write under Downloads")
    for marker in FORBIDDEN_OUTPUT_MARKERS:
        if marker.lower() in lowered:
            raise ValueError(f"refusing to write over prior dir {marker}")


def load_domain_human_rows(review_csv: Path) -> list[dict[str, str]]:
    rows = [
        row
        for row in _read_csv(review_csv)
        if (row.get("classification") or "").strip() == CLASS_HUMAN
    ]
    if len(rows) != EXPECTED_DOMAIN_HUMAN_COUNT:
        raise ValueError(
            f"expected {EXPECTED_DOMAIN_HUMAN_COUNT} needs_human_review rows, "
            f"got {len(rows)}"
        )
    return rows


def union_account_ids(
    original_rows: list[dict[str, str]],
    domain_human_rows: list[dict[str, str]],
) -> tuple[list[str], dict[str, str]]:
    """Return unique IDs in original-then-domain order, plus source map."""
    sources: dict[str, str] = {}
    ordered: list[str] = []
    for row in original_rows:
        account_id = (row.get("Master Account ID") or "").strip()
        if not account_id or account_id in sources:
            continue
        sources[account_id] = SOURCE_ORIGINAL
        ordered.append(account_id)
    added = 0
    for row in domain_human_rows:
        account_id = (row.get("Master Account ID") or "").strip()
        if not account_id or account_id in sources:
            continue
        sources[account_id] = SOURCE_DOMAIN
        ordered.append(account_id)
        added += 1
    return ordered, sources


def domain_labels(domain: str) -> set[str]:
    normalized = normalize_domain(domain)
    parts = re.split(r"[.\-_/]+", normalized)
    return {
        part
        for part in parts
        if len(part) >= MIN_DOMAIN_LABEL_LEN and part not in GENERIC_DOMAIN_LABELS
    }


def latin_name_tokens(name: str) -> set[str]:
    return {token.lower() for token in re.findall(r"[A-Za-z]{4,}", name or "")}


def clear_name_domain_overlap(company_name: str, domain: str) -> bool:
    labels = domain_labels(domain)
    name = (company_name or "").lower()
    latin = latin_name_tokens(company_name)
    if labels & latin:
        return True
    return any(label in name for label in labels if len(label) >= MIN_NAME_OVERLAP_LEN)


def is_homepage_social(value: str) -> bool:
    raw = (value or "").strip().lower().rstrip("/")
    if not raw:
        return True
    path = raw.split("://", 1)[-1]
    if path.startswith("www."):
        path = path[4:]
    bare = {
        "x.com",
        "twitter.com",
        "facebook.com",
        "instagram.com",
        "linkedin.com",
        "youtube.com",
        "tiktok.com",
        "/x.com",
        "/twitter.com",
    }
    return path in bare or raw in bare


def is_garbage_domain(domain: str, evidence: str) -> bool:
    normalized = normalize_domain(domain)
    if not normalized:
        return True
    if not is_safe_company_domain(normalized):
        return True
    lowered = (evidence or "").lower()
    garbage_hints = (
        "نطاق وهمي",
        "امتداد وهمي",
        "نطاق غير صالح",
        "نطاق غير حقيقي",
        "نطاق عام",
        "gibberish",
        "example.com",
        "قالب تجريبي",
        "موقع تجريبي",
    )
    return any(hint in lowered or hint in (evidence or "") for hint in garbage_hints)


def evidence_says_unrelated(evidence: str) -> bool:
    text = evidence or ""
    lowered = text.lower()
    return any(hint in text or hint in lowered for hint in UNRELATED_HINTS)


def index_rows(
    rows: list[dict[str, str]],
    key: str = "Master Account ID",
) -> dict[str, dict[str, str]]:
    indexed: dict[str, dict[str, str]] = {}
    for row in rows:
        account_id = (row.get(key) or "").strip()
        if account_id and account_id not in indexed:
            indexed[account_id] = row
    return indexed


def group_patch_values(
    rows: list[dict[str, str]],
) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        account_id = (row.get("Master Account ID") or "").strip()
        if account_id:
            grouped[account_id].append(row)
    return grouped


def format_patch_values(values: list[dict[str, str]]) -> str:
    parts = []
    for row in values:
        field_type = (row.get("field_type") or "").strip()
        value = (row.get("value") or "").strip()
        if field_type and value:
            parts.append(f"{field_type}={value}")
    return " | ".join(parts)


def usable_ready_values(
    values: list[dict[str, str]],
    primary_domain: str,
) -> list[dict[str, str]]:
    primary = normalize_domain(primary_domain)
    usable = []
    for row in values:
        flag = (row.get("quality_flag") or "").strip().lower()
        source = normalize_domain(row.get("source_domain") or "")
        value = (row.get("value") or "").strip()
        if flag not in {"ok", "needs_review"}:
            continue
        if primary and source and source != primary:
            continue
        if is_homepage_social(value):
            continue
        usable.append(row)
    return usable


def decide_domain_correction_human(row: dict[str, str]) -> Decision:
    account_id = (row.get("Master Account ID") or "").strip()
    curated = HUMAN_REVIEW.get(account_id, {})
    evidence = (
        curated.get("evidence_source")
        or row.get("evidence_source")
        or row.get("issue_evidence")
        or ""
    )
    reason = curated.get("reason") or (
        "Domain-correction classification is needs_human_review. "
        "No unique official replacement was accepted."
    )
    return Decision(
        proposed_decision=DECIDE_PARK,
        confidence=CONF_MEDIUM,
        evidence=evidence,
        reason=reason,
        suggested_domain_or_values=curated.get("candidate_domains") or "",
    )


def decide_high_correction(account_id: str) -> Decision | None:
    curated = HIGH_CORRECTIONS.get(account_id)
    if not curated:
        return None
    corrected = (curated.get("corrected_domain") or "").strip()
    if not corrected or not is_safe_company_domain(corrected):
        return None
    return Decision(
        proposed_decision=DECIDE_DOMAIN_FIX,
        confidence=CONF_HIGH,
        evidence=curated.get("evidence_source") or "",
        reason=curated.get("reason") or "High-confidence official domain already evidenced.",
        suggested_domain_or_values=corrected,
    )


def decide_pending_review(
    row: dict[str, str],
    values: list[dict[str, str]],
) -> Decision:
    domain = (row.get("primary_domain") or "").strip()
    name = row.get("company_name") or ""
    usable = usable_ready_values(values, domain)
    if not usable:
        return Decision(
            proposed_decision=DECIDE_PARK,
            confidence=CONF_LOW,
            evidence="PENDING_REVIEW row has no usable same-domain Agent Reach values.",
            reason="Insufficient evidenced Agent Reach values to approve.",
            suggested_domain_or_values="",
        )
    formatted = format_patch_values(usable)
    overlap = clear_name_domain_overlap(name, domain)
    if overlap:
        return Decision(
            proposed_decision=DECIDE_APPROVE,
            confidence=CONF_HIGH,
            evidence=(
                f"Agent Reach ready values from listed domain {domain} "
                f"with quality_flag ok/needs_review; domain label overlaps "
                f"the registered name. Values: {formatted}"
            ),
            reason=(
                "AR values clearly match this company via the same listed "
                "domain and name/domain label overlap."
            ),
            suggested_domain_or_values=formatted,
        )
    return Decision(
        proposed_decision=DECIDE_APPROVE,
        confidence=CONF_MEDIUM,
        evidence=(
            f"Agent Reach ready values from listed domain {domain} "
            f"with quality_flag ok. Name/domain overlap is not independently "
            f"proven. Values: {formatted}"
        ),
        reason=(
            "Same-domain Agent Reach values exist, but the registered name "
            "does not independently confirm the host. Not high-confidence."
        ),
        suggested_domain_or_values=formatted,
    )


def decide_ready_with_issues(
    row: dict[str, str],
    values: list[dict[str, str]],
) -> Decision:
    account_id = (row.get("Master Account ID") or "").strip()
    domain = (row.get("primary_domain") or "").strip()
    name = row.get("company_name") or ""
    evidence = row.get("issue_evidence") or ""
    categories = parse_categories(row.get("quality_categories", ""))
    usable = usable_ready_values(values, domain)

    if account_id == "MA-0217631" or "abshersetup.ae" in normalize_domain(domain):
        return Decision(
            proposed_decision=DECIDE_REJECT,
            confidence=CONF_HIGH,
            evidence=evidence,
            reason=(
                "Stored host looks like an Absher lookalike on a UAE TLD and "
                "the LinkedIn footer was unrelated. No safe replacement."
            ),
            suggested_domain_or_values="",
        )
    if account_id == "MA-0211686":
        return Decision(
            proposed_decision=DECIDE_PARK,
            confidence=CONF_LOW,
            evidence=evidence,
            reason=(
                "Unrelated LinkedIn was stripped from bmcc-ltd.com. Remaining "
                "phone is not independently proven to be بيت الموارد."
            ),
            suggested_domain_or_values="",
        )
    if usable and (
        clear_name_domain_overlap(name, domain)
        or account_id in {"MA-0267176", "MA-0213575"}
    ):
        formatted = format_patch_values(usable)
        return Decision(
            proposed_decision=DECIDE_APPROVE,
            confidence=CONF_HIGH,
            evidence=(
                f"{evidence} Remaining Agent Reach values after the isolated "
                f"quality strip: {formatted}"
            ),
            reason=(
                "Quality issue isolated a bad value; remaining AR values match "
                "the listed company/domain evidence."
            ),
            suggested_domain_or_values=formatted,
        )
    if "non_saudi_contact" in categories and usable:
        return Decision(
            proposed_decision=DECIDE_APPROVE,
            confidence=CONF_HIGH,
            evidence=evidence,
            reason=(
                "Foreign WhatsApp already excluded; remaining same-domain "
                "socials were accepted."
            ),
            suggested_domain_or_values=format_patch_values(usable),
        )
    return Decision(
        proposed_decision=DECIDE_PARK,
        confidence=CONF_LOW,
        evidence=evidence,
        reason="READY_WITH_ISSUES remains ambiguous after the quality strip.",
        suggested_domain_or_values="",
    )


def _reject(evidence: str, reason: str) -> Decision:
    return Decision(
        proposed_decision=DECIDE_REJECT,
        confidence=CONF_HIGH,
        evidence=evidence,
        reason=reason,
        suggested_domain_or_values="",
    )


def decide_quality_backlog(row: dict[str, str]) -> Decision:
    categories = parse_categories(row.get("quality_categories", ""))
    evidence = row.get("issue_evidence") or ""
    domain = (row.get("primary_domain") or "").strip()
    parked = Decision(
        proposed_decision=DECIDE_PARK,
        confidence=CONF_LOW,
        evidence=evidence,
        reason="Quality backlog row has no clear approve/reject evidence.",
        suggested_domain_or_values="",
    )

    if "hijacked_or_compromised" in categories:
        decision = _reject(
            evidence,
            "Domain is evidenced as hijacked or compromised. Do not apply "
            "extracted contacts. No safe replacement is proposed.",
        )
    elif "company_domain_mismatch" in categories:
        decision = _reject(
            evidence,
            "Listed domain is evidenced as a different company. Reject the "
            "host. Do not invent a replacement from the name.",
        )
    elif "placeholder_or_fake" in categories and is_garbage_domain(domain, evidence):
        decision = _reject(
            evidence,
            "Primary_Domain is placeholder, fake, or a template host. "
            "No safe replacement is proposed.",
        )
    elif "placeholder_or_fake" in categories:
        decision = Decision(
            proposed_decision=DECIDE_PARK,
            confidence=CONF_MEDIUM,
            evidence=evidence,
            reason=(
                "A placeholder/fake value was discarded, but the listed domain "
                "is not independently proven safe to reject or replace."
            ),
            suggested_domain_or_values="",
        )
    elif "global_parent_domain" in categories and evidence_says_unrelated(evidence):
        decision = _reject(
            evidence,
            "Global host is evidenced as unrelated to the registered "
            "local account. Reject it. No safe local replacement.",
        )
    elif "global_parent_domain" in categories:
        decision = Decision(
            proposed_decision=DECIDE_PARK,
            confidence=CONF_MEDIUM,
            evidence=evidence,
            reason=(
                "Global-parent versus local Saudi identity is still ambiguous. "
                "Do not approve parent contacts onto this account."
            ),
            suggested_domain_or_values="",
        )
    else:
        decision = parked
    return decision


def propose_decision(
    row: dict[str, str],
    *,
    source: str,
    values: list[dict[str, str]] | None = None,
) -> Decision:
    account_id = (row.get("Master Account ID") or "").strip()
    high_fix = decide_high_correction(account_id)
    if high_fix is not None:
        return high_fix
    if source == SOURCE_DOMAIN:
        return decide_domain_correction_human(row)
    status = (row.get("enrichment_status") or "").strip()
    if status == "PENDING_REVIEW":
        return decide_pending_review(row, values or [])
    if status == "READY_WITH_ISSUES":
        return decide_ready_with_issues(row, values or [])
    return decide_quality_backlog(row)


def is_unresolved(decision: Decision) -> bool:
    if decision.proposed_decision == DECIDE_PARK:
        return True
    if decision.proposed_decision == DECIDE_APPROVE and decision.confidence != CONF_HIGH:
        return True
    return False


def build_unified_row(
    row: dict[str, str],
    *,
    source: str,
    domain_row: dict[str, str] | None = None,
) -> dict[str, str]:
    domain_class = ""
    corrected = ""
    if domain_row:
        domain_class = domain_row.get("classification") or ""
        corrected = domain_row.get("corrected_domain") or ""
    return {
        "Master Account ID": row.get("Master Account ID") or "",
        "company_name": row.get("company_name") or "",
        "tier": row.get("tier") or "",
        "tier_bucket": row.get("tier_bucket") or "",
        "primary_domain": row.get("primary_domain")
        or row.get("old_domain")
        or "",
        "queue_source": source,
        "enrichment_status": row.get("enrichment_status") or "",
        "quality_categories": row.get("quality_categories") or "",
        "issue_evidence": row.get("issue_evidence") or "",
        "domain_correction_classification": domain_class,
        "corrected_domain": corrected,
        "usable_domain": row.get("usable_domain") or "",
        "attempted_agent_reach": row.get("attempted_agent_reach") or "",
        "why_human_review": row.get("why_human_review")
        or row.get("reason")
        or "",
        "recommended_action": row.get("recommended_action") or "",
        "review_only": "true",
    }


def build_decision_row(
    unified: dict[str, str],
    decision: Decision,
) -> dict[str, str]:
    return {
        "Master Account ID": unified["Master Account ID"],
        "company_name": unified["company_name"],
        "tier": unified["tier"],
        "tier_bucket": unified["tier_bucket"],
        "primary_domain": unified["primary_domain"],
        "queue_source": unified["queue_source"],
        "proposed_decision": decision.proposed_decision,
        "confidence": decision.confidence,
        "evidence": decision.evidence,
        "reason": decision.reason,
        "suggested_domain_or_values": decision.suggested_domain_or_values,
        "quality_categories": unified["quality_categories"],
        "domain_correction_classification": unified[
            "domain_correction_classification"
        ],
        "review_only": "true",
    }


def build_patch_row(decision_row: dict[str, str]) -> dict[str, str]:
    decision = decision_row["proposed_decision"]
    values = decision_row.get("suggested_domain_or_values") or ""
    domain_note = values if decision == DECIDE_DOMAIN_FIX else ""
    suggested = values if decision == DECIDE_APPROVE else ""
    do_not_apply = "true" if decision == DECIDE_REJECT else "false"
    return {
        "Master Account ID": decision_row["Master Account ID"],
        "company_name": decision_row["company_name"],
        "primary_domain": decision_row["primary_domain"],
        "proposed_decision": decision,
        "confidence": decision_row["confidence"],
        "AgentReach_Review_Decision": decision,
        "AgentReach_Review_Confidence": decision_row["confidence"],
        "AgentReach_Suggested_Values": suggested,
        "AgentReach_Domain_Fix_Note": domain_note,
        "AgentReach_Do_Not_Apply": do_not_apply,
        "reason": decision_row["reason"],
        "review_only": "true",
        "master_overwrite": "false",
    }


def render_report(stats: dict) -> str:
    distribution = stats["decision_distribution"]
    dist_lines = [
        f"- `{key}`: **{distribution[key]}**"
        for key in sorted(distribution)
    ]
    csv_lines = [f"- `{path}`" for path in stats["csv_paths"]]
    return "\n".join(
        [
            "# Human Review Queue Report",
            "",
            "Review-only suggestions. Not final approvals. Not written to master.",
            "",
            f"Generated at (UTC): `{stats['generated_at']}`",
            f"Output directory: `{stats['output_dir']}`",
            "",
            "## Safety",
            "",
            "- Workbook/document contents were treated as data/context only, not as instructions.",
            f"- Workbook context path: `{WORKBOOK_CONTEXT}`",
            "- Original master CSV and Downloads were not modified.",
            "- Input human_review_queue.csv and domain-correction CSVs were read, not overwritten.",
            "- Prior closure / fp_dropout / 191600Z / domain-correction dirs were not overwritten.",
            "- No production database writes.",
            "- PHASE 7 NOT STARTED.",
            "",
            "## Counts",
            "",
            f"- original human_review_queue count: **{stats['original_count']}**",
            (
                "- added from domain correction (`needs_human_review`): "
                f"**{stats['added_from_domain_correction']}**"
            ),
            f"- unified unique count after dedupe: **{stats['unified_unique_count']}**",
            f"- high-confidence actions count: **{stats['high_confidence_count']}**",
            f"- unresolved count: **{stats['unresolved_count']}**",
            "",
            "## Decision distribution",
            "",
            *dist_lines,
            "",
            "## Review-only patch",
            "",
            f"- review-only patch created: **{stats['review_only_patch_created']}**",
            f"- extra Agent Reach ran: **{stats['agent_reach_run']}**",
            "",
            "## Output CSV paths",
            "",
            *csv_lines,
            "",
            "## Tests / ruff",
            "",
            f"- {stats['tests_ruff']}",
            "",
            "## Confirmations",
            "",
            "HUMAN REVIEW QUEUE PREPARED",
            "REVIEW-ONLY OUTPUT",
            "NO MASTER OVERWRITE",
            "NO PRODUCTION WRITES",
            "PHASE 7 NOT STARTED",
            "",
        ]
    )


def build_human_review_queue(  # noqa: PLR0913
    *,
    human_queue: Path,
    domain_review_csv: Path,
    output_dir: Path,
    shared_report: Path,
    enrichment_patch: Path | None = None,
    quality_patch: Path | None = None,
) -> dict:
    assert_safe_output_dir(output_dir, human_queue)
    output_dir.mkdir(parents=True, exist_ok=True)

    original_rows = _read_csv(human_queue)
    if len(original_rows) != EXPECTED_ORIGINAL_COUNT:
        raise ValueError(
            f"expected {EXPECTED_ORIGINAL_COUNT} human-review rows, "
            f"got {len(original_rows)}"
        )
    domain_human_rows = load_domain_human_rows(domain_review_csv)
    ordered_ids, sources = union_account_ids(original_rows, domain_human_rows)
    original_by_id = index_rows(original_rows)
    domain_by_id = index_rows(domain_human_rows)

    patch_by_id: dict[str, list[dict[str, str]]] = {}
    if enrichment_patch and enrichment_patch.exists():
        patch_by_id = group_patch_values(_read_csv(enrichment_patch))

    unified_rows: list[dict[str, str]] = []
    decision_rows: list[dict[str, str]] = []
    decisions: list[Decision] = []
    for account_id in ordered_ids:
        source = sources[account_id]
        base = (
            original_by_id[account_id]
            if source == SOURCE_ORIGINAL
            else domain_by_id[account_id]
        )
        unified = build_unified_row(
            base,
            source=source,
            domain_row=domain_by_id.get(account_id),
        )
        decision = propose_decision(
            base,
            source=source,
            values=patch_by_id.get(account_id, []),
        )
        unified_rows.append(unified)
        decision_rows.append(build_decision_row(unified, decision))
        decisions.append(decision)

    high_rows = [
        row for row in decision_rows if row["confidence"] == CONF_HIGH
    ]
    unresolved_rows = [
        row
        for row, decision in zip(decision_rows, decisions, strict=True)
        if is_unresolved(decision)
    ]

    unified_csv = output_dir / "human_review_unified_queue.csv"
    decision_csv = output_dir / "human_review_decision_suggestions.csv"
    high_csv = output_dir / "human_review_high_confidence_actions.csv"
    unresolved_csv = output_dir / "human_review_unresolved.csv"
    _write_csv(unified_csv, UNIFIED_HEADERS, unified_rows)
    _write_csv(decision_csv, DECISION_HEADERS, decision_rows)
    _write_csv(high_csv, DECISION_HEADERS, high_rows)
    _write_csv(unresolved_csv, DECISION_HEADERS, unresolved_rows)

    patch_created = "false"
    patch_csv = ""
    if high_rows:
        patch_dir = output_dir / "review_only_patch"
        patch_csv_path = patch_dir / "human_review_additive_notes.csv"
        _write_csv(
            patch_csv_path,
            PATCH_HEADERS,
            [build_patch_row(row) for row in high_rows],
        )
        patch_created = "true"
        patch_csv = str(patch_csv_path)

    distribution = Counter(row["proposed_decision"] for row in decision_rows)
    added = sum(1 for source in sources.values() if source == SOURCE_DOMAIN)
    csv_paths = [
        str(unified_csv),
        str(decision_csv),
        str(high_csv),
        str(unresolved_csv),
    ]
    if patch_csv:
        csv_paths.append(patch_csv)

    stats = {
        "generated_at": datetime.now(UTC).isoformat(),
        "output_dir": str(output_dir),
        "original_count": len(original_rows),
        "added_from_domain_correction": added,
        "unified_unique_count": len(unified_rows),
        "decision_distribution": dict(sorted(distribution.items())),
        "high_confidence_count": len(high_rows),
        "unresolved_count": len(unresolved_rows),
        "review_only_patch_created": patch_created,
        "agent_reach_run": "false",
        "csv_paths": csv_paths,
        "tests_ruff": "not run from builder",
        "review_only": True,
        "phase_7_started": False,
        "production_writes": False,
        "master_overwrite": False,
        "quality_patch_used": bool(quality_patch and quality_patch.exists()),
    }
    report = render_report(stats)
    (output_dir / "HUMAN_REVIEW_QUEUE_REPORT.md").write_text(report, encoding="utf-8")
    shared_report.write_text(report, encoding="utf-8")
    (output_dir / "review_stats.json").write_text(
        json.dumps(stats, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return stats


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--human-queue", type=Path, required=True)
    parser.add_argument("--domain-review-csv", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--shared-report", type=Path, required=True)
    parser.add_argument("--enrichment-patch", type=Path)
    parser.add_argument("--quality-patch", type=Path)
    parser.add_argument("--tests-ruff", default="not run from builder")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    stats = build_human_review_queue(
        human_queue=args.human_queue,
        domain_review_csv=args.domain_review_csv,
        output_dir=args.output_dir,
        shared_report=args.shared_report,
        enrichment_patch=args.enrichment_patch,
        quality_patch=args.quality_patch,
    )
    if args.tests_ruff != "not run from builder":
        stats["tests_ruff"] = args.tests_ruff
        report = render_report(stats)
        Path(stats["output_dir"], "HUMAN_REVIEW_QUEUE_REPORT.md").write_text(
            report, encoding="utf-8"
        )
        args.shared_report.write_text(report, encoding="utf-8")
        Path(stats["output_dir"], "review_stats.json").write_text(
            json.dumps(stats, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    print(f"unified={stats['unified_unique_count']}")
    print(f"added={stats['added_from_domain_correction']}")
    print(f"high={stats['high_confidence_count']}")
    print(f"patch={stats['review_only_patch_created']}")
    print(f"agent_reach_run={stats['agent_reach_run']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
