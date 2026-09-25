"""Build a review-only Domain Correction queue for 204 accounts.

Classifies each row from the existing domain-correction review queue using
safe evidence only (queue notes, closure quality issues, optional master
email/domain fields, and curated public official sites). Writes a NEW
timestamped directory. Does not overwrite the input queue, original master,
Downloads, production DB, or prior patch/closure dirs.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from agent_reach_contact_enrichment_loop import (  # noqa: E402
    _write_csv as _write_csv_rows,
)
from agent_reach_parallel_contact_enrichment import (  # noqa: E402
    build_worker_command,
    format_worker_command,
)

from app.modules.agent_reach.contact_enrichment import (  # noqa: E402
    QUEUE_HEADERS,
    is_safe_company_domain,
    normalize_domain,
)

CLASS_CORRECTED = "corrected_domain_found"
CLASS_HUMAN = "needs_human_review"
CLASS_NONE = "no_safe_correction"

EXPECTED_QUEUE_COUNT = 204
INPUT_QUEUE_NAME = "domain_correction_review_queue.csv"
WORKBOOK_CONTEXT = (
    str(BACKEND_ROOT / "outputs"
    / "agent_reach_contact_enrichment" / "20260907T052800Z_fp_dropout_remainder"
    / "14_Website_Phone_Social_Enrichment_AgentReach.xlsx")
)
DEFAULT_PYTHON = sys.executable
FORBIDDEN_OUTPUT_MARKERS = (
    "20260907T052756Z_final_closure",
    "20260907T052800Z_fp_dropout_remainder",
    "cycle_13",
    "20260907T054012Z_missing_data_completion_plan",
)

CONSUMER_EMAIL_LOOKALIKES = {
    "icoloud.com",
    "icould.com",
    "iclob.com",
    "iclou.com",
    "icliud.com",
    "iclcud.com",
    "iclouid.com",
    "gmsil.vom",
    "gmdil.com",
    "gmal.co",
    "gaimil.com",
    "hotmli.com",
    "hotmaol.vom",
    "hotmael.com",
    "hotail.com",
    "homtail.com",
    "yshoo.com",
    "yawoo.com",
    "outilook.com",
    "ootlook.com",
    "jmail.cm",
    "mail.ru",
    "live.dk",
    "msn.om",
}
DISPOSABLE_OR_GENERIC = {
    "yopmil.com",
    "yopmail.com",
    "10minutes.email",
    "mailnej.top",
    "emailfoxi.pro",
    "emailboxa.online",
    "emailna.co",
    "mailboxy.fun",
    "mailboxok.club",
    "boxmailbox.club",
    "mailwax.com",
    "allfreemail.net",
    "moakt.cc",
    "moakt.ws",
    "instaddr.uk",
    "heylink.me",
    "website.com",
    "company.com",
    "12345.com",
    "xxx.com",
    "2019.com",
    "co.com",
    "ss.com",
    "li.com",
    "gil.com",
    "tys.com",
    "dfgh.com",
    "noemail3.com",
    "noemail4.com",
    "as.aa",
    "asd.as",
    "sd.fo",
    "sd.dfo",
    "love.at",
    "wau.edu",
    "ftr.cc",
    "fursa.co",
}
GOVERNMENT_HINTS = (".gov.sa", ".gov.uk", ".edu.sa", "moe.gov.sa", "momra.gov.sa")

# Evidence-backed replacements only. No invented small-contractor sites.
HIGH_CORRECTIONS: dict[str, dict[str, str]] = {
    "MA-0001268": {
        "corrected_domain": "merckgroup.com",
        "evidence_source": (
            "Master Primary_Email abdullah.aldamkh@merckgroup.com; "
            "official Merck KGaA site merckgroup.com. "
            "Existing alahli.com.sa is SNB, not Merck."
        ),
        "reason": (
            "Registered name is Merck KG / Riyadh; email and official "
            "corporate site agree on merckgroup.com."
        ),
        "agent_reach_eligible": "true",
    },
    "MA-0001280": {
        "corrected_domain": "takeda.com",
        "evidence_source": (
            "Master Primary_Email alaa.Yasin@takeda.com; "
            "official Takeda Austria / Takeda Pharma is takeda.com. "
            "Existing icbc-ltd.com is ICBC, not Takeda."
        ),
        "reason": (
            "Registered name is Takeda Austria GmbH; email and official "
            "Takeda site agree on takeda.com."
        ),
        "agent_reach_eligible": "true",
    },
    "MA-0001378": {
        "corrected_domain": "monalawfirm.com.sa",
        "evidence_source": (
            "Old domain monalawfirm.com.sa.sa is a doubled TLD; "
            "https://monalawfirm.com.sa is the live official site for "
            "شركة منى حامد مثيب السلمي وشركاؤها للمحاماة."
        ),
        "reason": "Mechanical doubled-TLD repair plus matching official law-firm site.",
        "agent_reach_eligible": "true",
    },
    "MA-0001468": {
        "corrected_domain": "almousa.legal",
        "evidence_source": (
            "Old domain almousa.lega is a truncated TLD; "
            "http://almousa.legal is the official site for "
            "محمد موسى الموسى محامون ومستشارون."
        ),
        "reason": "Truncated .lega → .legal plus matching official law-firm site.",
        "agent_reach_eligible": "true",
    },
    "MA-0047607": {
        "corrected_domain": "gov.uk",
        "evidence_source": (
            "Old FCO host ukinsaudiarabia.fco.gov.uk is retired. Official "
            "British Embassy Riyadh page: "
            "https://www.gov.uk/world/organisations/british-embassy-riyadh"
        ),
        "reason": (
            "Official FCDO page is on gov.uk. Not Agent-Reach eligible: "
            "fetching gov.uk root would not be the embassy page."
        ),
        "agent_reach_eligible": "false",
    },
    "MA-0094205": {
        "corrected_domain": "intra.sa",
        "evidence_source": (
            "Official INTRA Defense Technologies site https://intra.sa/; "
            "also listed by SABIC HOI as https://intra.sa/. "
            "Existing intras.net is not that company."
        ),
        "reason": "Registered name matches INTRA Defense Technologies; official site is intra.sa.",
        "agent_reach_eligible": "true",
    },
    "MA-0110687": {
        "corrected_domain": "saudire.net",
        "evidence_source": (
            "Old domain saudire.ne is a truncated saudire.net. Official "
            "Saudi Re site https://saudire.net/ matches "
            "الشركة السعودية لاعادة التأمين التعاوني."
        ),
        "reason": "Truncation of the official Saudi Re hostname plus live official site.",
        "agent_reach_eligible": "true",
    },
    "MA-0133385": {
        "corrected_domain": "binshehab.com.sa",
        "evidence_source": (
            "Official Bin Shehab site https://binshehab.com.sa/ for "
            "شركة محمد عبدالله محمد بن شهاب واولاده. "
            "shehabco.com / shehabco.com.sa are older variants."
        ),
        "reason": "Current official company site matches the registered Bin Shehab name.",
        "agent_reach_eligible": "true",
    },
    "MA-0137046": {
        "corrected_domain": "uranus.com.sa",
        "evidence_source": (
            "Official Uranus Dental Center https://www.uranus.com.sa/ "
            "matches مجمع كوكب اورانس لطب الاسنان. "
            "Old uranus-medical.center.com is a broken host."
        ),
        "reason": "Official clinic site uniquely matches the registered dental-center name.",
        "agent_reach_eligible": "true",
    },
    "MA-0181753": {
        "corrected_domain": "dell.com",
        "evidence_source": (
            "Master Primary_Email mahmoud_abbas@dell.com; registered name "
            "شركة ديل منطقة حرة. Existing delll.com is a typo of dell.com."
        ),
        "reason": "Dell Free Zone account; email and official Dell domain agree.",
        "agent_reach_eligible": "true",
    },
    "MA-0261141": {
        "corrected_domain": "skybridgefreight.com",
        "evidence_source": (
            "Official Skybridge Freight Solutions site "
            "https://www.skybridgefreight.com/ lists Saudi branches. "
            "Existing asyad.com is the later Asyad Group parent, not this account."
        ),
        "reason": "Account is Sky Bridge Freight Solutions, not Asyad headquarters.",
        "agent_reach_eligible": "true",
    },
}

# Plausible options exist, but not unique/safe enough to fetch.
HUMAN_REVIEW: dict[str, dict[str, str]] = {
    "MA-0000540": {
        "candidate_domains": "unec.ae",
        "evidence_source": "Queue/closure: UAE host with invalid SSL; name is similar.",
        "reason": (
            "unec.ae may belong to a UAE engineering firm, but liveness/SSL "
            "failed and KSA identity is not unique. Do not invent a replacement."
        ),
    },
    "MA-0001240": {
        "candidate_domains": "nbb.com.bh | nbbonline.com",
        "evidence_source": (
            "Name is National Bank of Bahrain B.S.C. Current nbb.com.bh was "
            "flagged only for .bh. Current public portal is also nbbonline.com."
        ),
        "reason": (
            "Existing domain may already be official; a second official portal "
            "exists. Human must choose which host to keep."
        ),
    },
    "MA-0094970": {
        "candidate_domains": "vinnellarabia.com | northropgrumman.com",
        "evidence_source": (
            "Account is Northrop Grumman Arabia; existing host is Vinnell Arabia, "
            "a historical related entity. Parent official site is northropgrumman.com."
        ),
        "reason": "Subsidiary vs global-parent identity is not unique enough to auto-correct.",
    },
    "MA-0103334": {
        "candidate_domains": "samba.com | alahli.com",
        "evidence_source": (
            "Samba Financial Group merged into SNB. samba.com is historical; "
            "SNB official is alahli.com / alahli.com.sa."
        ),
        "reason": "Historical Samba vs successor SNB needs a human identity decision.",
    },
    "MA-0129195": {
        "candidate_domains": "globalgroup.com.sa",
        "evidence_source": (
            "Old globalgroup.comsa is a missing-dot .com.sa. Company name is "
            "مؤسسة طرق الخليج للمقاولات; email is hotmail, not that domain."
        ),
        "reason": "Mechanical TLD repair is possible but the name does not uniquely match.",
    },
    "MA-0144258": {
        "candidate_domains": "televes.com",
        "evidence_source": (
            "Old tleleves.com; master email INFO@TELEVES.COM. televes.com is "
            "Spanish Televes. Local account is شركة تلفاز للمقاولات."
        ),
        "reason": "Global parent vs local contracting entity is not unique/safe enough.",
    },
    "MA-0295037": {
        "candidate_domains": "sbi.co.in | centralbankofindia.co.in | rbi.org.in",
        "evidence_source": (
            "Name is البنك المركزي الهندي_الرياض but stored domain is sbi.co.in "
            "(State Bank of India). Central Bank of India and RBI are different."
        ),
        "reason": "Name and stored domain disagree; three official Indian banks are possible.",
    },
}

# Existing host already matches the registered well-known entity.
EXISTING_OFFICIAL_KEEP: dict[str, dict[str, str]] = {
    "MA-0094208": {
        "evidence_source": (
            "rowadshop.com terms name شركة الرواد للأجهزة الإلكترونية as the operator."
        ),
        "reason": (
            "Existing rowadshop.com already matches the registered electronics "
            "retailer. No replacement domain is proposed."
        ),
    },
    "MA-0094263": {
        "evidence_source": "ocrim.com is the official Ocrim S.p.A. milling-equipment site.",
        "reason": (
            "Registered name Ocrim S.p.A. matches ocrim.com. Existing domain "
            "is already official. No replacement proposed."
        ),
    },
    "MA-0260590": {
        "evidence_source": "nupco.com is the official NUPCO / نوبكو site (PIF portfolio).",
        "reason": (
            "Registered name is the National Unified Procurement Company. "
            "Existing nupco.com is already official. No replacement proposed."
        ),
    },
    "MA-0295036": {
        "evidence_source": "nbp.com.pk is the official National Bank of Pakistan site.",
        "reason": (
            "Registered name is بنك باكستان الوطني. Existing nbp.com.pk is "
            "already official. Flag was jurisdiction-only. No replacement proposed."
        ),
    },
}

REVIEW_HEADERS = [
    "Master Account ID",
    "company_name",
    "tier",
    "tier_bucket",
    "old_domain",
    "classification",
    "corrected_domain",
    "evidence_source",
    "confidence",
    "reason",
    "quality_categories",
    "issue_evidence",
    "master_email",
    "master_all_domains",
    "agent_reach_eligible",
    "review_only",
]
UNRESOLVED_HEADERS = REVIEW_HEADERS
PLAN_HEADERS = [
    "account_id",
    "company_name",
    "old_domain",
    "corrected_domain",
    "confidence",
    "agent_reach_eligible",
    "reason",
    "review_only",
]


@dataclass(frozen=True)
class Classification:
    classification: str
    corrected_domain: str
    evidence_source: str
    confidence: str
    reason: str
    agent_reach_eligible: bool


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_dict_csv(path: Path, headers: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def assert_safe_output_dir(output_dir: Path, input_queue: Path) -> None:
    output = output_dir.resolve()
    queue = input_queue.resolve()
    if output == queue.parent:
        raise ValueError("refusing to write into the input plan directory")
    if output == queue:
        raise ValueError("refusing to overwrite the input queue path")
    if (output / INPUT_QUEUE_NAME).resolve() == queue:
        raise ValueError("refusing to overwrite domain_correction_review_queue.csv in place")
    lowered = str(output).lower()
    if "\\downloads\\" in lowered or "/downloads/" in lowered:
        raise ValueError("refusing to write under Downloads")
    for marker in FORBIDDEN_OUTPUT_MARKERS:
        if marker.lower() in lowered:
            raise ValueError(f"refusing to write over prior dir {marker}")


def load_master_extras(master_csv: Path | None, account_ids: set[str]) -> dict[str, dict[str, str]]:
    extras: dict[str, dict[str, str]] = {}
    if master_csv is None or not master_csv.exists():
        return extras
    with master_csv.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            account_id = (row.get("Master Account ID") or "").strip()
            if account_id not in account_ids:
                continue
            extras[account_id] = {
                "email": (row.get("Primary_Email") or "").strip(),
                "all_domains": (row.get("All_Domains") or "").strip(),
                "city": (row.get("City") or "").strip(),
                "has_phone": (row.get("has_phone") or "").strip(),
                "has_social": (row.get("has_social") or "").strip(),
            }
    return extras


def _looks_like_garbage_host(domain: str) -> bool:
    host = normalize_domain(domain)
    if not host or "." not in host:
        return True
    suffix = host.rsplit(".", 1)[-1]
    if suffix in {"comh", "ughik", "gfghf", "fhjhjf", "nmo", "hnij", "ss", "ocg", "comsa"}:
        return True
    if host.count(".") == 1 and suffix not in {
        "com",
        "net",
        "org",
        "sa",
        "ae",
        "bh",
        "pk",
        "in",
        "uk",
        "io",
        "co",
        "cc",
        "me",
        "fun",
        "club",
        "top",
        "pro",
        "online",
        "ws",
        "click",
        "legal",
        "center",
        "edu",
        "gov",
    }:
        return True
    return False


def _none(evidence_source: str, reason: str, *, confidence: str = "high") -> Classification:
    return Classification(
        classification=CLASS_NONE,
        corrected_domain="",
        evidence_source=evidence_source,
        confidence=confidence,
        reason=reason,
        agent_reach_eligible=False,
    )


def classify_account(row: dict[str, str]) -> Classification:
    account_id = (row.get("Master Account ID") or "").strip()
    domain = normalize_domain(row.get("primary_domain") or row.get("old_domain"))
    categories = (row.get("quality_categories") or "").strip()
    evidence = (row.get("issue_evidence") or "").strip()

    if account_id in HIGH_CORRECTIONS:
        item = HIGH_CORRECTIONS[account_id]
        return Classification(
            classification=CLASS_CORRECTED,
            corrected_domain=item["corrected_domain"],
            evidence_source=item["evidence_source"],
            confidence="high",
            reason=item["reason"],
            agent_reach_eligible=item["agent_reach_eligible"] == "true",
        )
    if account_id in HUMAN_REVIEW:
        item = HUMAN_REVIEW[account_id]
        return Classification(
            classification=CLASS_HUMAN,
            corrected_domain="",
            evidence_source=item["evidence_source"],
            confidence="medium",
            reason=item["reason"],
            agent_reach_eligible=False,
        )
    if account_id in EXISTING_OFFICIAL_KEEP:
        item = EXISTING_OFFICIAL_KEEP[account_id]
        return _none(item["evidence_source"], item["reason"])

    pattern_none = _pattern_no_safe(domain, categories, evidence)
    if pattern_none is not None:
        return pattern_none
    return _none(
        evidence or "Insufficient safe evidence for a replacement domain.",
        "Cannot propose a domain without invention.",
    )


def _pattern_no_safe(domain: str, categories: str, evidence: str) -> Classification | None:
    if domain in CONSUMER_EMAIL_LOOKALIKES:
        return _none(
            evidence or f"Stored host {domain} is a consumer-email lookalike.",
            "Consumer-email typo or public mailbox host. Correcting it would "
            "yield Gmail/iCloud/Outlook/Yahoo, not a company website.",
        )
    if domain in DISPOSABLE_OR_GENERIC:
        return _none(
            evidence or f"Stored host {domain} is disposable/generic.",
            "Disposable, placeholder, or generic host. No company site can be invented.",
        )
    if any(hint in domain for hint in GOVERNMENT_HINTS) or categories == "government_domain":
        return _none(
            evidence or f"Stored host {domain} is a government/education host.",
            "Government or education host on a private commercial account. "
            "Clear the field; do not invent a company website.",
        )
    if _looks_like_garbage_host(domain) or categories in {
        "typo_domain",
        "invalid_or_generic_domain",
    }:
        return _none(
            evidence or f"Stored host {domain} is invalid, random, or mismatched.",
            "No unique official replacement was found in available evidence. "
            "Inventing a domain from the company name is forbidden.",
        )
    return None


def build_review_row(
    row: dict[str, str],
    extras: dict[str, str],
    result: Classification,
) -> dict[str, str]:
    return {
        "Master Account ID": (row.get("Master Account ID") or "").strip(),
        "company_name": (row.get("company_name") or "").strip(),
        "tier": (row.get("tier") or "").strip(),
        "tier_bucket": (row.get("tier_bucket") or "").strip(),
        "old_domain": (row.get("primary_domain") or "").strip(),
        "classification": result.classification,
        "corrected_domain": result.corrected_domain,
        "evidence_source": result.evidence_source,
        "confidence": result.confidence,
        "reason": result.reason,
        "quality_categories": (row.get("quality_categories") or "").strip(),
        "issue_evidence": (row.get("issue_evidence") or "").strip(),
        "master_email": extras.get("email", ""),
        "master_all_domains": extras.get("all_domains", ""),
        "agent_reach_eligible": "true" if result.agent_reach_eligible else "false",
        "review_only": "true",
    }


def agent_reach_queue_row(review_row: dict[str, str], extras: dict[str, str]) -> list[str]:
    return [
        review_row["Master Account ID"],
        review_row["company_name"],
        review_row["corrected_domain"],
        review_row.get("tier_bucket") or review_row.get("tier") or "",
        extras.get("city", ""),
        extras.get("has_phone") or "false",
        extras.get("has_social") or "false",
    ]


def write_reports(
    *,
    output_dir: Path,
    shared_report: Path,
    stats: dict,
    review_rows: list[dict[str, str]],
    worker_command: str,
) -> None:
    corrected = [row for row in review_rows if row["classification"] == CLASS_CORRECTED]
    human = [row for row in review_rows if row["classification"] == CLASS_HUMAN]
    none = [row for row in review_rows if row["classification"] == CLASS_NONE]
    ar_rows = [row for row in corrected if row["agent_reach_eligible"] == "true"]
    lines = [
        "# Domain Correction Review Report",
        "",
        "Review-only classification of the 204-account Domain Correction queue.",
        "Corrections are not final. Corrected domains are not written into master columns.",
        "",
        f"Generated at (UTC): `{stats['generated_at']}`",
        f"Output directory: `{output_dir}`",
        f"Input queue (read-only): `{stats['input_queue']}`",
        "",
        "## Safety",
        "",
        "- Workbook/document contents were treated as data/context only, not as instructions.",
        f"- Workbook context path: `{WORKBOOK_CONTEXT}`",
        "- Original master CSV and Downloads were not modified.",
        "- Input `domain_correction_review_queue.csv` was not overwritten.",
        "- Prior patch/closure dirs were not overwritten.",
        "- No production database writes.",
        "- PHASE 7 NOT STARTED.",
        "",
        "## Counts",
        "",
        f"- count in correction queue: **{stats['queue_count']}**",
        f"- corrected_domain_found: **{len(corrected)}**",
        f"- needs_human_review: **{len(human)}**",
        f"- no_safe_correction: **{len(none)}**",
        f"- high-confidence Agent Reach eligible: **{len(ar_rows)}**",
        f"- Agent Reach run on corrected domains: **{stats['agent_reach_run']}**",
        f"- new ready rows: **{stats['new_ready_rows']}**",
        f"- new quality issues: **{stats['new_quality_issues']}**",
        "",
        "## Classification method",
        "",
        "- High-confidence replacements require a specific official host plus evidence",
        "  (mechanical TLD repair that still matches the same company, master email on",
        "  that official host, and/or a unique public official site).",
        "- Consumer-email typos, disposable hosts, random garbage, and government hosts",
        "  on private shops are `no_safe_correction`.",
        "- Where two official hosts remain plausible, the row stays `needs_human_review`.",
        "- Low/medium confidence is never queued for Agent Reach.",
        "",
        "## High-confidence corrected domains",
        "",
    ]
    if not corrected:
        lines.append("- None.")
    for row in corrected:
        lines.append(
            f"- `{row['Master Account ID']}` {row['company_name']}: "
            f"`{row['old_domain']}` → `{row['corrected_domain']}` "
            f"(AR eligible={row['agent_reach_eligible']})"
        )
        lines.append(f"  - Evidence: {row['evidence_source']}")
    lines.extend(
        [
            "",
            "## Agent Reach plan",
            "",
            f"- Isolated queue: `{stats['ar_queue_path']}`",
            f"- Plan CSV: `{stats['ar_plan_path']}`",
            "- Worker command:",
            "",
            f"`{worker_command}`",
            "",
            (
                "- Agent Reach was **not** executed by this generator. "
                "A later isolated `--queue-csv --no-workbook` run may use the command above, "
                "then `--merge-only` into a NEW workbook copied from the latest final AR workbook."
                if stats["agent_reach_run"] == "false"
                else "- Agent Reach was executed on the isolated high-confidence set only."
            ),
            "- Do not mix leftovers / UNKNOWN / ANTI-ICP / other tiers.",
            "",
            "## CSV paths",
            "",
            f"- `{stats['review_csv']}`",
            f"- `{stats['unresolved_csv']}`",
            f"- `{stats['ar_plan_path']}`",
            f"- `{stats['ar_queue_path']}`",
            "",
            "## Tests / ruff",
            "",
            f"- {stats['tests_ruff']}",
            "",
            "## Confirmations",
            "",
            "DOMAIN CORRECTION REVIEW QUEUE CREATED",
            "REVIEW-ONLY OUTPUT",
            "NO MASTER OVERWRITE",
            "NO PRODUCTION WRITES",
            "PHASE 7 NOT STARTED",
            "",
        ]
    )
    text = "\n".join(lines)
    (output_dir / "DOMAIN_CORRECTION_REVIEW_REPORT.md").write_text(text, encoding="utf-8")
    shared_report.parent.mkdir(parents=True, exist_ok=True)
    shared_report.write_text(text, encoding="utf-8")


def build_domain_correction_review(  # noqa: PLR0913
    *,
    input_queue: Path,
    output_dir: Path,
    shared_report: Path,
    master_csv: Path | None = None,
    python_executable: str = DEFAULT_PYTHON,
    existing_xlsx: Path | None = None,
) -> dict:
    assert_safe_output_dir(output_dir, input_queue)
    output_dir.mkdir(parents=True, exist_ok=True)
    if input_queue.name != INPUT_QUEUE_NAME:
        raise ValueError(f"expected input file {INPUT_QUEUE_NAME}")

    queue_rows = _read_csv(input_queue)
    if len(queue_rows) != EXPECTED_QUEUE_COUNT:
        raise ValueError(
            f"expected {EXPECTED_QUEUE_COUNT} domain-correction rows, got {len(queue_rows)}"
        )

    account_ids = {(row.get("Master Account ID") or "").strip() for row in queue_rows}
    extras_by_id = load_master_extras(master_csv, account_ids)

    review_rows: list[dict[str, str]] = []
    for row in queue_rows:
        account_id = (row.get("Master Account ID") or "").strip()
        extras = extras_by_id.get(account_id, {})
        result = classify_account(row)
        review_rows.append(build_review_row(row, extras, result))

    unresolved = [
        row
        for row in review_rows
        if row["classification"] in {CLASS_HUMAN, CLASS_NONE}
    ]
    ar_eligible = [
        row
        for row in review_rows
        if row["classification"] == CLASS_CORRECTED
        and row["agent_reach_eligible"] == "true"
        and row["confidence"] == "high"
        and is_safe_company_domain(row["corrected_domain"])
    ]

    review_csv = output_dir / "domain_corrections_review_only.csv"
    unresolved_csv = output_dir / "domain_corrections_unresolved.csv"
    ar_plan_csv = output_dir / "domain_corrections_agent_reach_plan.csv"
    ar_queue_csv = output_dir / "domain_corrections_agent_reach_queue.csv"
    _write_dict_csv(review_csv, REVIEW_HEADERS, review_rows)
    _write_dict_csv(unresolved_csv, UNRESOLVED_HEADERS, unresolved)
    _write_dict_csv(
        ar_plan_csv,
        PLAN_HEADERS,
        [
            {
                "account_id": row["Master Account ID"],
                "company_name": row["company_name"],
                "old_domain": row["old_domain"],
                "corrected_domain": row["corrected_domain"],
                "confidence": row["confidence"],
                "agent_reach_eligible": row["agent_reach_eligible"],
                "reason": row["reason"],
                "review_only": "true",
            }
            for row in review_rows
            if row["classification"] == CLASS_CORRECTED
        ],
    )

    shard_dir = output_dir / "shards"
    worker_dir = output_dir / "workers" / "worker_001"
    shard_dir.mkdir(parents=True, exist_ok=True)
    worker_dir.mkdir(parents=True, exist_ok=True)
    shard_path = shard_dir / "shard_001.csv"
    queue_rows_out = [
        agent_reach_queue_row(row, extras_by_id.get(row["Master Account ID"], {}))
        for row in ar_eligible
    ]
    _write_csv_rows(ar_queue_csv, QUEUE_HEADERS, queue_rows_out)
    _write_csv_rows(shard_path, QUEUE_HEADERS, queue_rows_out)
    _write_csv_rows(worker_dir / "assigned_queue.csv", QUEUE_HEADERS, queue_rows_out)

    command = build_worker_command(
        shard_path,
        worker_dir,
        python_executable=python_executable,
        sleep_seconds=1.0,
    )
    command_text = format_worker_command(command)
    (output_dir / "worker_commands.txt").write_text(
        command_text + ("\n" if command_text else ""),
        encoding="utf-8",
    )
    existing = Path(existing_xlsx) if existing_xlsx else Path(WORKBOOK_CONTEXT)
    plan = {
        "review_only": True,
        "pending_queue_total": len(ar_eligible),
        "existing_xlsx": str(existing),
        "shards": [
            {
                "shard_id": "shard_001",
                "worker_dir": str(worker_dir.resolve()),
                "account_ids": [row["Master Account ID"] for row in ar_eligible],
                "command": command_text,
            }
        ],
        "worker_commands": [command_text] if ar_eligible else [],
        "note": (
            "High-confidence isolated queue only. Do not mix other Agent Reach tiers. "
            "Merge-only into a NEW workbook; do not overwrite the copy-base."
        ),
    }
    (output_dir / "plan.json").write_text(
        json.dumps(plan, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    stats = {
        "generated_at": datetime.now(UTC).isoformat(),
        "input_queue": str(input_queue.resolve()),
        "output_dir": str(output_dir.resolve()),
        "queue_count": len(review_rows),
        "corrected_domain_found": sum(
            1 for row in review_rows if row["classification"] == CLASS_CORRECTED
        ),
        "needs_human_review": sum(
            1 for row in review_rows if row["classification"] == CLASS_HUMAN
        ),
        "no_safe_correction": sum(
            1 for row in review_rows if row["classification"] == CLASS_NONE
        ),
        "agent_reach_eligible": len(ar_eligible),
        "agent_reach_run": "false",
        "new_ready_rows": 0,
        "new_quality_issues": 0,
        "review_csv": str(review_csv.resolve()),
        "unresolved_csv": str(unresolved_csv.resolve()),
        "ar_plan_path": str(ar_plan_csv.resolve()),
        "ar_queue_path": str(ar_queue_csv.resolve()),
        "worker_command": command_text,
        "existing_xlsx_copy_base": str(existing),
        "tests_ruff": "not validated in generator",
        "review_only": True,
        "phase_7_started": False,
        "production_writes": False,
        "master_overwrite": False,
    }
    write_reports(
        output_dir=output_dir,
        shared_report=shared_report,
        stats=stats,
        review_rows=review_rows,
        worker_command=command_text,
    )
    (output_dir / "review_stats.json").write_text(
        json.dumps(stats, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return stats


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Classify the 204-row Domain Correction review queue."
    )
    parser.add_argument("--input-queue", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--shared-report",
        type=Path,
        default=BACKEND_ROOT
        / "outputs"
        / "agent_reach_contact_enrichment"
        / "DOMAIN_CORRECTION_REVIEW_REPORT.md",
    )
    parser.add_argument("--master-csv", type=Path, default=None)
    parser.add_argument("--python-executable", default=DEFAULT_PYTHON)
    parser.add_argument("--existing-xlsx", type=Path, default=Path(WORKBOOK_CONTEXT))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    stats = build_domain_correction_review(
        input_queue=args.input_queue,
        output_dir=args.output_dir,
        shared_report=args.shared_report,
        master_csv=args.master_csv,
        python_executable=args.python_executable,
        existing_xlsx=args.existing_xlsx,
    )
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
