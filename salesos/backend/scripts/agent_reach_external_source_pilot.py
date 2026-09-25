"""Review-only External Source Enrichment Pilot sampler and reporter.

Reads the 32,756-row external candidate queue, assesses the pre-marked
suggested_pilot_slice, and if that slice is not diverse draws a stratified
sample of exactly 40 accounts. Writes a NEW timestamped output directory.
Does not fetch paid APIs, does not overwrite the original master, Downloads,
production DB, or prior plan/review dirs. Does not start Phase 7.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from app.modules.agent_reach.contact_enrichment import parse_bool  # noqa: E402

PILOT_SIZE = 40
FULL_QUEUE_SIZE = 32756
SAMPLE_SEED = 20260908

CLASS_DATA_FOUND = "data_found"
CLASS_PAID = "needs_paid_source"
CLASS_MANUAL = "needs_manual_research"
CLASS_NONE = "no_safe_external_source"
CLASSIFICATIONS = (CLASS_DATA_FOUND, CLASS_PAID, CLASS_MANUAL, CLASS_NONE)

STRATUM_PHONE = "missing_phone"
STRATUM_LINKEDIN = "missing_linkedin"
STRATUM_OTHER_SOCIAL = "missing_other_social"
STRATUM_DEAD_DOMAIN = "dead_or_unusable_domain"
STRATUM_AR_HAS_CONTACT = "ar_failed_has_master_contact"
STRATUM_AR_NO_CONTACT = "ar_attempted_no_contact"
STRATUM_UNATTEMPTED = "unattempted_usable_domain"
STRATUM_OTHER = "other_external_gap"

STRATA_ORDER = (
    STRATUM_PHONE,
    STRATUM_LINKEDIN,
    STRATUM_OTHER_SOCIAL,
    STRATUM_DEAD_DOMAIN,
    STRATUM_AR_HAS_CONTACT,
    STRATUM_AR_NO_CONTACT,
    STRATUM_UNATTEMPTED,
    STRATUM_OTHER,
)

# Target mix for a 40-row diverse pilot. Sum must equal PILOT_SIZE.
# Empty real-queue buckets (unattempted leftover / other) get 0; shortfall
# is filled from remaining leftovers after the occupied strata are taken.
STRATA_TARGETS = {
    STRATUM_PHONE: 8,
    STRATUM_LINKEDIN: 8,
    STRATUM_OTHER_SOCIAL: 6,
    STRATUM_DEAD_DOMAIN: 6,
    STRATUM_AR_HAS_CONTACT: 6,
    STRATUM_AR_NO_CONTACT: 6,
    STRATUM_UNATTEMPTED: 0,
    STRATUM_OTHER: 0,
}

MIN_DIVERSE_STRATA = 5
MAX_SINGLE_STRATUM_SHARE = 0.55

FORBIDDEN_OUTPUT_MARKERS = (
    "20260907T052756Z_final_closure",
    "20260907T052800Z_fp_dropout_remainder",
    "20260907T054012Z_missing_data_completion_plan",
    "20260907T175703Z_domain_correction_review",
    "20260907T210427Z_human_review_queue",
    "191600Z",
    "cycle_13",
)

DEFAULT_QUEUE = (
    BACKEND_ROOT
    / "outputs"
    / "agent_reach_contact_enrichment"
    / "20260907T054012Z_missing_data_completion_plan"
    / "external_source_candidate_queue.csv"
)
DEFAULT_SHARED_REPORT = (
    BACKEND_ROOT
    / "outputs"
    / "agent_reach_contact_enrichment"
    / "EXTERNAL_SOURCE_PILOT_REPORT.md"
)

SAMPLE_HEADERS = [
    "Master Account ID",
    "company_name",
    "tier",
    "tier_bucket",
    "primary_domain",
    "usable_domain",
    "attempted_agent_reach",
    "already_has_master_contacts",
    "enrichment_status",
    "quality_categories",
    "issue_evidence",
    "why_agent_reach_cannot_finish",
    "missing_phone",
    "missing_whatsapp",
    "missing_linkedin",
    "missing_other_social",
    "sampling_stratum",
    "sampling_method",
    "suggested_pilot_slice",
    "notes",
    "review_only",
]
RESULT_HEADERS = [
    "Master Account ID",
    "company_name",
    "tier",
    "tier_bucket",
    "primary_domain",
    "sampling_stratum",
    "classification",
    "field_found",
    "value_found",
    "source_url_or_note",
    "confidence",
    "reason",
    "why_external_source_needed",
    "review_only",
]
PATCH_HEADERS = [
    "Master Account ID",
    "company_name",
    "primary_domain",
    "field_found",
    "proposed_value",
    "source_url_or_note",
    "confidence",
    "reason",
    "classification",
    "review_only",
    "master_overwrite",
    "do_not_apply_to_master",
]
UNRESOLVED_HEADERS = [
    "Master Account ID",
    "company_name",
    "tier",
    "tier_bucket",
    "primary_domain",
    "sampling_stratum",
    "classification",
    "reason",
    "why_external_source_needed",
    "review_only",
]


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


def parse_bool_cell(value: object) -> bool:
    return parse_bool(value)


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


TIER_INTERLEAVE = (
    "CLASS A",
    "TIER B",
    "TIER C",
    "TIER D",
    "UNKNOWN",
    "ANTI-ICP",
)


def _stable_key(row: dict[str, str]) -> str:
    return (row.get("Master Account ID") or "").strip()


def assign_stratum(row: dict[str, str]) -> str:  # noqa: PLR0911
    """Mutually exclusive gap-reason stratum for diversity sampling."""
    usable = parse_bool_cell(row.get("usable_domain"))
    attempted = parse_bool_cell(row.get("attempted_agent_reach"))
    has_contacts = parse_bool_cell(row.get("already_has_master_contacts"))
    missing_phone = parse_bool_cell(row.get("missing_phone"))
    missing_linkedin = parse_bool_cell(row.get("missing_linkedin"))
    missing_other = parse_bool_cell(row.get("missing_other_social"))
    categories = {
        part.strip()
        for part in (row.get("quality_categories") or "").split("|")
        if part.strip()
    }
    deadish = categories & {
        "unreachable",
        "timeout",
        "parked_or_hosting",
        "invalid_or_generic_domain",
        "typo_domain",
        "placeholder_or_fake",
    }

    if (not usable) or deadish:
        return STRATUM_DEAD_DOMAIN
    if has_contacts:
        return STRATUM_AR_HAS_CONTACT
    if missing_phone:
        return STRATUM_PHONE
    if missing_linkedin and not missing_other:
        return STRATUM_LINKEDIN
    if missing_other and not missing_linkedin:
        return STRATUM_OTHER_SOCIAL
    if missing_linkedin or missing_other:
        return STRATUM_LINKEDIN if missing_linkedin else STRATUM_OTHER_SOCIAL
    if attempted:
        return STRATUM_AR_NO_CONTACT
    if usable and not attempted:
        return STRATUM_UNATTEMPTED
    return STRATUM_OTHER


def interleave_by_tier(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    grouped: dict[str, list[dict[str, str]]] = {key: [] for key in TIER_INTERLEAVE}
    extra: list[dict[str, str]] = []
    for row in rows:
        bucket = (row.get("tier_bucket") or "").strip() or "UNKNOWN"
        if bucket in grouped:
            grouped[bucket].append(row)
        else:
            extra.append(row)
    for key in grouped:
        grouped[key].sort(key=_stable_key)
    extra.sort(key=_stable_key)
    interleaved: list[dict[str, str]] = []
    while any(grouped.values()) or extra:
        progressed = False
        for key in TIER_INTERLEAVE:
            if grouped[key]:
                interleaved.append(grouped[key].pop(0))
                progressed = True
        if extra:
            interleaved.append(extra.pop(0))
            progressed = True
        if not progressed:
            break
    return interleaved


def suggested_pilot_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [row for row in rows if parse_bool_cell(row.get("suggested_pilot_slice"))]


def stratum_counts(rows: list[dict[str, str]]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for row in rows:
        counts[assign_stratum(row)] += 1
    return counts


def is_diverse_slice(rows: list[dict[str, str]]) -> tuple[bool, str]:
    if len(rows) != PILOT_SIZE:
        return False, f"suggested_pilot_slice has {len(rows)} rows, need {PILOT_SIZE}"
    counts = stratum_counts(rows)
    occupied = sum(1 for key in STRATA_ORDER if counts.get(key, 0) > 0)
    if occupied < MIN_DIVERSE_STRATA:
        return (
            False,
            f"only {occupied} strata occupied (need {MIN_DIVERSE_STRATA})",
        )
    top = counts.most_common(1)[0][1] if counts else 0
    if top / len(rows) > MAX_SINGLE_STRATUM_SHARE:
        return False, f"largest stratum is {top}/{len(rows)} (>{MAX_SINGLE_STRATUM_SHARE:.0%})"
    return True, "suggested_pilot_slice is diverse enough"


def draw_stratified_sample(
    rows: list[dict[str, str]],
    *,
    size: int = PILOT_SIZE,
    targets: dict[str, int] | None = None,
) -> list[dict[str, str]]:
    plan = dict(targets or STRATA_TARGETS)
    if sum(plan.values()) != size:
        raise ValueError(f"stratum targets must sum to {size}")
    buckets: dict[str, list[dict[str, str]]] = {key: [] for key in STRATA_ORDER}
    for row in rows:
        buckets.setdefault(assign_stratum(row), []).append(row)
    for key in buckets:
        buckets[key] = interleave_by_tier(buckets[key])

    picked: list[dict[str, str]] = []
    used: set[str] = set()
    leftovers: list[dict[str, str]] = []
    for stratum in STRATA_ORDER:
        need = plan.get(stratum, 0)
        available = [row for row in buckets.get(stratum, []) if _stable_key(row) not in used]
        take = available[:need]
        picked.extend(take)
        used.update(_stable_key(row) for row in take)
        leftovers.extend(available[need:])
        shortfall = need - len(take)
        if shortfall:
            plan[STRATUM_OTHER] = plan.get(STRATUM_OTHER, 0) + shortfall

    if len(picked) < size:
        leftovers.sort(key=_stable_key)
        for row in leftovers:
            if len(picked) >= size:
                break
            key = _stable_key(row)
            if key in used:
                continue
            picked.append(row)
            used.add(key)

    if len(picked) != size:
        raise ValueError(f"could not draw {size} unique sample rows, got {len(picked)}")
    picked.sort(key=_stable_key)
    return picked


def sample_method_label(use_suggested: bool) -> str:
    if use_suggested:
        return "suggested_pilot_slice"
    return "stratified_by_gap_reason"


def attach_sample_meta(
    rows: list[dict[str, str]],
    *,
    method: str,
) -> list[dict[str, str]]:
    return [
        {
            **{key: row.get(key, "") for key in SAMPLE_HEADERS},
            "Master Account ID": row.get("Master Account ID", ""),
            "sampling_stratum": assign_stratum(row),
            "sampling_method": method,
            "review_only": "true",
        }
        for row in rows
    ]


def choose_sample(rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], str, str]:
    suggested = suggested_pilot_rows(rows)
    diverse, reason = is_diverse_slice(suggested)
    if diverse:
        method = sample_method_label(True)
        return attach_sample_meta(suggested, method=method), method, reason
    method = sample_method_label(False)
    drawn = draw_stratified_sample(rows)
    note = f"suggested slice not used: {reason}"
    return attach_sample_meta(drawn, method=method), method, note


def merge_research(
    sample_rows: list[dict[str, str]],
    findings: dict[str, dict[str, str]],
) -> list[dict[str, str]]:
    merged: list[dict[str, str]] = []
    for row in sample_rows:
        account_id = (row.get("Master Account ID") or "").strip()
        finding = findings.get(account_id)
        if finding is None:
            raise ValueError(f"missing research finding for {account_id}")
        merged.append(
            {
                "Master Account ID": account_id,
                "company_name": row.get("company_name", ""),
                "tier": row.get("tier", ""),
                "tier_bucket": row.get("tier_bucket", ""),
                "primary_domain": row.get("primary_domain", ""),
                "sampling_stratum": row.get("sampling_stratum", ""),
                "classification": finding.get("classification", ""),
                "field_found": finding.get("field_found", ""),
                "value_found": finding.get("value_found", ""),
                "source_url_or_note": finding.get("source_url_or_note", ""),
                "confidence": finding.get("confidence", ""),
                "reason": finding.get("reason", ""),
                "why_external_source_needed": row.get(
                    "why_agent_reach_cannot_finish",
                    "",
                ),
                "review_only": "true",
            }
        )
    if len(merged) != len(sample_rows):
        raise ValueError("research merge lost rows")
    return merged


def classify_result(row: dict[str, str]) -> dict[str, str]:
    classification = (row.get("classification") or "").strip()
    if classification not in CLASSIFICATIONS:
        raise ValueError(f"invalid classification: {classification}")
    return {
        **{key: row.get(key, "") for key in RESULT_HEADERS},
        "classification": classification,
        "review_only": "true",
    }


def patch_rows_from_results(results: list[dict[str, str]]) -> list[dict[str, str]]:
    patches: list[dict[str, str]] = []
    for row in results:
        if row.get("classification") != CLASS_DATA_FOUND:
            continue
        patches.append(
            {
                "Master Account ID": row.get("Master Account ID", ""),
                "company_name": row.get("company_name", ""),
                "primary_domain": row.get("primary_domain", ""),
                "field_found": row.get("field_found", ""),
                "proposed_value": row.get("value_found", ""),
                "source_url_or_note": row.get("source_url_or_note", ""),
                "confidence": row.get("confidence", ""),
                "reason": row.get("reason", ""),
                "classification": CLASS_DATA_FOUND,
                "review_only": "true",
                "master_overwrite": "false",
                "do_not_apply_to_master": "true",
            }
        )
    return patches


def unresolved_from_results(results: list[dict[str, str]]) -> list[dict[str, str]]:
    unresolved: list[dict[str, str]] = []
    for row in results:
        if row.get("classification") == CLASS_DATA_FOUND:
            continue
        unresolved.append({key: row.get(key, "") for key in UNRESOLVED_HEADERS})
    return unresolved


def classification_counts(results: list[dict[str, str]]) -> dict[str, int]:
    counts = {key: 0 for key in CLASSIFICATIONS}
    for row in results:
        key = row.get("classification") or ""
        if key in counts:
            counts[key] += 1
    return counts


def field_found_counts(results: list[dict[str, str]]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for row in results:
        if row.get("classification") != CLASS_DATA_FOUND:
            continue
        field = (row.get("field_found") or "").strip() or "(blank)"
        counts[field] += 1
    return counts


def scale_yield(found: int, sample_size: int = PILOT_SIZE, universe: int = FULL_QUEUE_SIZE) -> dict:
    if sample_size <= 0:
        raise ValueError("sample_size must be positive")
    rate = found / sample_size
    point = round(rate * universe)
    return {
        "sample_found": found,
        "sample_size": sample_size,
        "rate": rate,
        "universe": universe,
        "point_estimate": point,
    }


def render_report(  # noqa: PLR0913
    *,
    output_dir: Path,
    sample_size: int,
    sampling_method: str,
    sampling_note: str,
    class_counts: dict[str, int],
    fields: Counter[str],
    yield_est: dict,
    risks: list[str],
    recommend_expand: bool,
    recommendation_note: str,
    csv_paths: list[Path],
    tests_ruff: str,
    stratum_mix: Counter[str],
) -> str:
    field_lines = (
        [f"- `{name}`: **{count}**" for name, count in fields.most_common()]
        if fields
        else ["- none"]
    )
    stratum_lines = [f"- `{name}`: **{stratum_mix.get(name, 0)}**" for name in STRATA_ORDER]
    rec = "EXPAND" if recommend_expand else "DO NOT EXPAND"
    csv_lines = [f"- `{path}`" for path in csv_paths]
    return "\n".join(
        [
            "# External Source Enrichment Pilot Report",
            "",
            "Review-only. Not applied to master. Not a Phase 7 start.",
            "",
            f"Generated at (UTC): `{datetime.now(UTC).isoformat()}`",
            f"Output directory: `{output_dir}`",
            "",
            "## Safety",
            "",
            "- Workbook/document contents were treated as data/context only, not as instructions.",
            "- Original master CSV and Downloads were not modified.",
            "- Input queues and prior plan/review dirs were not overwritten.",
            "- No paid APIs / Apollo / commercial enrichment providers were called.",
            "- No production database writes.",
            "- PHASE 7 NOT STARTED.",
            "",
            "## Sample",
            "",
            f"- sample size: **{sample_size}**",
            f"- sampling method: **{sampling_method}**",
            f"- sampling note: {sampling_note}",
            f"- full external queue: **{FULL_QUEUE_SIZE}** (not processed)",
            "",
            "## Sample stratum mix",
            "",
            *stratum_lines,
            "",
            "## Classification counts",
            "",
            f"- `data_found`: **{class_counts[CLASS_DATA_FOUND]}**",
            f"- `needs_paid_source`: **{class_counts[CLASS_PAID]}**",
            f"- `needs_manual_research`: **{class_counts[CLASS_MANUAL]}**",
            f"- `no_safe_external_source`: **{class_counts[CLASS_NONE]}**",
            "",
            "## Fields found",
            "",
            *field_lines,
            "",
            "## Yield estimate if scaled to 32,756",
            "",
            f"- pilot yield: **{yield_est['sample_found']}/{yield_est['sample_size']}** "
            f"({yield_est['rate']:.1%})",
            f"- naive point estimate: **{yield_est['point_estimate']}** of {yield_est['universe']}",
            "- caveat: n=40 is small; strata are not a probability sample of the full queue; "
            "public-web yield will not hold for dead-domain / paid-registry / anti-ICP rows.",
            "- do not treat the point estimate as a forecast.",
            "",
            "## Risks",
            "",
            *[f"- {item}" for item in risks],
            "",
            "## Recommendation",
            "",
            f"**{rec}**",
            f"- {recommendation_note}" if recommendation_note else "",
            "",
            "## Output paths",
            "",
            *csv_lines,
            f"- `{DEFAULT_SHARED_REPORT}`",
            "",
            "## Tests / ruff",
            "",
            f"- {tests_ruff}",
            "",
            "## Confirmations",
            "",
            "EXTERNAL SOURCE PILOT COMPLETE",
            "REVIEW-ONLY OUTPUT",
            "NO MASTER OVERWRITE",
            "NO PRODUCTION WRITES",
            "PHASE 7 NOT STARTED",
            "",
        ]
    )


def write_pilot_outputs(  # noqa: PLR0913
    *,
    output_dir: Path,
    shared_report: Path,
    sample_rows: list[dict[str, str]],
    result_rows: list[dict[str, str]],
    sampling_method: str,
    sampling_note: str,
    tests_ruff: str,
    risks: list[str],
    recommend_expand: bool,
    recommendation_note: str = "",
) -> dict:
    if len(sample_rows) != PILOT_SIZE:
        raise ValueError(f"sample must be {PILOT_SIZE}, got {len(sample_rows)}")
    if len(result_rows) != PILOT_SIZE:
        raise ValueError(f"results must be {PILOT_SIZE}, got {len(result_rows)}")

    classified = [classify_result(row) for row in result_rows]
    patches = patch_rows_from_results(classified)
    unresolved = unresolved_from_results(classified)
    counts = classification_counts(classified)
    fields = field_found_counts(classified)
    mix = Counter(row.get("sampling_stratum", "") for row in sample_rows)
    yield_est = scale_yield(counts[CLASS_DATA_FOUND])

    sample_path = output_dir / "external_source_pilot_sample.csv"
    results_path = output_dir / "external_source_pilot_results.csv"
    patch_path = output_dir / "external_source_pilot_review_only_patch.csv"
    unresolved_path = output_dir / "external_source_pilot_unresolved.csv"
    report_path = output_dir / "EXTERNAL_SOURCE_PILOT_REPORT.md"
    csv_paths = [sample_path, results_path, patch_path, unresolved_path]

    output_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(sample_path, SAMPLE_HEADERS, sample_rows)
    _write_csv(results_path, RESULT_HEADERS, classified)
    _write_csv(patch_path, PATCH_HEADERS, patches)
    _write_csv(unresolved_path, UNRESOLVED_HEADERS, unresolved)

    report = render_report(
        output_dir=output_dir,
        sample_size=PILOT_SIZE,
        sampling_method=sampling_method,
        sampling_note=sampling_note,
        class_counts=counts,
        fields=fields,
        yield_est=yield_est,
        risks=risks,
        recommend_expand=recommend_expand,
        recommendation_note=recommendation_note,
        csv_paths=csv_paths,
        tests_ruff=tests_ruff,
        stratum_mix=mix,
    )
    report_path.write_text(report, encoding="utf-8")
    shared_report.parent.mkdir(parents=True, exist_ok=True)
    shared_report.write_text(report, encoding="utf-8")

    stats = {
        "generated_at": datetime.now(UTC).isoformat(),
        "output_dir": str(output_dir),
        "sample_size": PILOT_SIZE,
        "sampling_method": sampling_method,
        "sampling_note": sampling_note,
        "classification_counts": counts,
        "fields_found": dict(fields),
        "yield_estimate": yield_est,
        "recommend_expand": recommend_expand,
        "review_only": True,
        "phase_7_started": False,
        "production_writes": False,
        "master_overwrite": False,
        "paid_apis_used": False,
    }
    (output_dir / "pilot_stats.json").write_text(
        json.dumps(stats, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return stats


def default_risks() -> list[str]:
    return [
        (
            "n=40 cannot represent 32,756 accounts; "
            "CLASS A / live-site rows over-yield vs dead domains."
        ),
        (
            "Public-web phones and social URLs can be outdated, "
            "shared, or belong to a parent brand."
        ),
        "Name collisions among Arabic trade names can attach the wrong company site.",
        (
            "Paid registry / CR lookup would change the paid-source count; "
            "this pilot did not buy that."
        ),
        (
            "Applying any data_found value without human review "
            "would write unverified contact data."
        ),
    ]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="External source enrichment pilot (review-only)",
    )
    parser.add_argument("--queue", type=Path, default=DEFAULT_QUEUE)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--shared-report", type=Path, default=DEFAULT_SHARED_REPORT)
    parser.add_argument("--sample-only", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    queue = args.queue
    rows = _read_csv(queue)
    if len(rows) != FULL_QUEUE_SIZE:
        raise ValueError(f"expected {FULL_QUEUE_SIZE} queue rows, got {len(rows)}")
    sample_rows, method, note = choose_sample(rows)
    stamp = _timestamp()
    output_dir = args.output_dir or (
        BACKEND_ROOT
        / "outputs"
        / "agent_reach_contact_enrichment"
        / f"{stamp}_external_source_pilot"
    )
    assert_safe_output_dir(output_dir, queue)
    if args.sample_only:
        output_dir.mkdir(parents=True, exist_ok=True)
        _write_csv(output_dir / "external_source_pilot_sample.csv", SAMPLE_HEADERS, sample_rows)
        (output_dir / "sample_method.txt").write_text(f"{method}\n{note}\n", encoding="utf-8")
        print(f"sample_only method={method} n={len(sample_rows)} dir={output_dir}")
        return 0
    raise SystemExit("full write requires researched result rows; use the library API")


if __name__ == "__main__":
    raise SystemExit(main())
