"""Validate capability registries are in sync across all 4 sources.

Usage:
    python scripts/validate_capability_registries.py
    python scripts/validate_capability_registries.py --join-map-only

Returns exit code 0 if all registries are in sync, non-zero on mismatch.
``--join-map-only`` exits 0 when CAP→kebab join map integrity passes (5.2);
it does **not** claim criterion 5.3.

**SoT (DEC-132 / Phase 0 criterion 5.1):** Decorator Framework
(`runtime/capability_framework`, kebab-case IDs) is the canonical *runtime*
source of truth. SDK / governance YAML / docs CAP-### catalog are secondary
and must converge toward that SoT.

**Join map (DEC-133 / Phase 0 criterion 5.2):**
`runtime/capability_framework/cap_to_kebab_join.yaml` joins CAP-### → kebab.
Integrity of that map is checked here. Full 4-way sync exit 0 remains
criterion **5.3** (still expected non-zero until convergence land).

Surfaces:
    1. SDK CapabilityRegistry (sdk/capability_registry.py + modules/registry.py) — secondary
    2. Decorator Framework (runtime/capability_framework/__init__.py) — **SoT**
    3. Governance YAML (engineering-os/kernel/capability-registry.yaml) — secondary
    4. Documentation Catalog (docs/CAPABILITY_CATALOG.md) — secondary (CAP-###)
    5. CAP-### → kebab join map (cap_to_kebab_join.yaml) — criterion 5.2
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

# Add project root to path (salesos/backend)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
# Monorepo root (Muhide) — docs/ and engineering-os/ live here
REPO_ROOT = PROJECT_ROOT.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

EXPECTED_CATALOG_CAPS = {f"CAP-{i:03d}" for i in range(1, 41)}


def validate_sdk_registry():
    """Ensure modules/registry.py registers all expected capabilities."""
    from sdk.capability_registry import CapabilityRegistry

    registry = CapabilityRegistry
    all_caps = registry.all()
    cap_names = {c.name for c in all_caps}
    print(f"\n[SDK Registry] {len(all_caps)} capabilities registered:")
    for c in all_caps:
        print(f"  + {c.name} ({c.type.value})")
    return cap_names


def validate_decorator_framework():
    """Ensure decorator registry has all expected capabilities."""
    from runtime.capability_framework import Capability

    all_caps = Capability.all()
    cap_ids = {c.id for c in all_caps}
    print(f"\n[Decorator Framework] {len(all_caps)} capabilities registered:")
    for c in all_caps:
        status = c.manifest.status.value
        print(f"  + {c.id} ({c.manifest.name}) [{status}]")
    return cap_ids


def validate_governance_yaml(yaml_path: Path) -> set[str]:
    """Parse governance YAML and extract capability IDs."""
    if not yaml_path.exists():
        print(f"\n[Governance YAML] WARN File not found: {yaml_path}")
        return set()

    content = yaml_path.read_text(encoding="utf-8")
    cap_ids = set(re.findall(r'^\s+- id:\s+"([^"]+)"', content, re.MULTILINE))
    print(f"\n[Governance YAML] {len(cap_ids)} capabilities found:")
    for cid in sorted(cap_ids):
        print(f"  + {cid}")
    return cap_ids


def validate_capability_catalog(md_path: Path) -> set[str]:
    """Parse CAPABILITY_CATALOG.md and extract capability IDs."""
    if not md_path.exists():
        print(f"\n[Capability Catalog] WARN File not found: {md_path}")
        return set()

    content = md_path.read_text(encoding="utf-8")
    # Prefer heading form: ### CAP-001: Identity (current catalog)
    heading_caps = re.findall(r"^###\s+(CAP-\d{3}):\s+(.+)$", content, re.MULTILINE)
    if heading_caps:
        print(f"\n[Capability Catalog] {len(heading_caps)} capabilities found:")
        for cid, name in sorted(heading_caps):
            print(f"  + {cid}: {name.strip()}")
        return {cid for cid, _ in heading_caps}

    # Legacy bold form fallback
    bold_caps = set(re.findall(r"\bCAP-(\d{3}):\s+\*\*([^*]+)\*\*", content))
    names = {name.strip().lower().replace(" ", "-") for _, name in bold_caps}
    print(f"\n[Capability Catalog] {len(bold_caps)} capabilities found (legacy parse):")
    for num, name in sorted(bold_caps):
        print(f"  + CAP-{num}: {name}")
    return names


def _join_map_path() -> Path:
    try:
        from runtime.capability_framework import CAPABILITY_CAP_TO_KEBAB_JOIN_MAP

        rel = CAPABILITY_CAP_TO_KEBAB_JOIN_MAP
    except Exception:  # pragma: no cover
        rel = "runtime/capability_framework/cap_to_kebab_join.yaml"
    return PROJECT_ROOT / rel


def decorator_ids_from_source() -> set[str]:
    """Parse built-in @Capability(id=...) from SoT module without importing runtime deps."""
    init_path = PROJECT_ROOT / "runtime" / "capability_framework" / "__init__.py"
    text = init_path.read_text(encoding="utf-8")
    # Built-ins use id="kebab" at decorator call sites (skip docstring examples with spaces).
    return set(re.findall(r'^\s*id="([a-z0-9]+(?:-[a-z0-9]+)*)"', text, re.MULTILINE))


def validate_cap_to_kebab_join_map(decorator_ids: set[str], catalog_cap_ids: set[str]) -> list[str]:
    """Validate DEC-133 CAP-### → kebab join map integrity (criterion 5.2).

    Unmapped catalog entries are allowed (honest residual). Failures are structural:
    missing map, missing CAP keys, unknown runtime_id, SoT IDs neither joined nor
    listed in decorator_only.
    """
    errors: list[str] = []
    map_path = _join_map_path()
    print(f"\n[Join Map 5.2 / DEC-133] {map_path}")

    if not map_path.exists():
        msg = f"Join map missing: {map_path}"
        print(f"  x {msg}")
        return [msg]

    try:
        import yaml
    except ImportError:  # pragma: no cover
        msg = "PyYAML unavailable; cannot load join map"
        print(f"  x {msg}")
        return [msg]

    data: dict[str, Any] = yaml.safe_load(map_path.read_text(encoding="utf-8")) or {}
    joins: dict[str, Any] = data.get("joins") or {}
    decorator_only_raw = data.get("decorator_only") or []
    decorator_only = {
        item["id"] if isinstance(item, dict) else str(item) for item in decorator_only_raw
    }

    join_keys = set(joins.keys())
    missing_caps = EXPECTED_CATALOG_CAPS - join_keys
    extra_caps = join_keys - EXPECTED_CATALOG_CAPS
    if missing_caps:
        errors.append(f"Join map missing CAP keys: {sorted(missing_caps)}")
    if extra_caps:
        errors.append(f"Join map unexpected CAP keys: {sorted(extra_caps)}")

    # Catalog headings should be covered when parse returned CAP-### tokens
    catalog_as_caps = {c for c in catalog_cap_ids if re.fullmatch(r"CAP-\d{3}", c)}
    if catalog_as_caps:
        catalog_missing = catalog_as_caps - join_keys
        if catalog_missing:
            errors.append(f"Catalog CAP headings absent from join map: {sorted(catalog_missing)}")

    direct_runtime: set[str] = set()
    unmapped = 0
    for cap_id, entry in sorted(joins.items()):
        if not isinstance(entry, dict):
            errors.append(f"{cap_id}: entry must be a mapping")
            continue
        join_kind = entry.get("join")
        runtime_id = entry.get("runtime_id")
        if join_kind == "direct":
            if not runtime_id or not isinstance(runtime_id, str):
                errors.append(f"{cap_id}: direct join requires runtime_id string")
                continue
            if runtime_id not in decorator_ids:
                errors.append(
                    f"{cap_id}: runtime_id '{runtime_id}' not in decorator SoT {sorted(decorator_ids)}"
                )
            if runtime_id in direct_runtime:
                errors.append(f"Duplicate direct runtime_id '{runtime_id}' (also {cap_id})")
            direct_runtime.add(runtime_id)
        elif join_kind == "unmapped":
            unmapped += 1
            if runtime_id not in (None, "", "null"):
                errors.append(f"{cap_id}: unmapped join must have runtime_id null (got {runtime_id!r})")
        else:
            errors.append(f"{cap_id}: join must be 'direct' or 'unmapped' (got {join_kind!r})")

    sot_unaccounted = decorator_ids - direct_runtime - decorator_only
    if sot_unaccounted:
        errors.append(
            f"Decorator SoT IDs missing from direct joins and decorator_only: "
            f"{sorted(sot_unaccounted)}"
        )
    orphan_decorator_only = decorator_only - decorator_ids
    if orphan_decorator_only:
        errors.append(
            f"decorator_only lists unknown SoT IDs: {sorted(orphan_decorator_only)}"
        )

    print(
        f"  caps={len(joins)} direct={len(direct_runtime)} "
        f"unmapped={unmapped} decorator_only={len(decorator_only)} "
        f"sot={len(decorator_ids)}"
    )
    if errors:
        for e in errors:
            print(f"  x {e}")
    else:
        print("  OK Join map integrity (partial catalog coverage is documented residual)")
        print("  NOTE Criterion 5.3 (full 4-way exit 0) remains separate / still OPEN")
    return errors


def run_join_map_only() -> int:
    """Criterion 5.2 light path — no SDK/SQLAlchemy import required."""
    print("=" * 60)
    print("Capability Join Map Validation (5.2 / DEC-133)")
    print("=" * 60)
    print("SoT (DEC-132 / 5.1): decorator-framework @ runtime/capability_framework [kebab-case]")
    print(f"Join map: {_join_map_path()}")
    print("Mode: --join-map-only (does NOT claim 5.3 exit 0)")

    decorator_ids = decorator_ids_from_source()
    print(f"\n[Decorator SoT source parse] {len(decorator_ids)} ids: {sorted(decorator_ids)}")
    catalog_path = REPO_ROOT / "docs" / "CAPABILITY_CATALOG.md"
    catalog_ids = validate_capability_catalog(catalog_path)
    errors = validate_cap_to_kebab_join_map(decorator_ids, catalog_ids)
    print("\n" + "=" * 60)
    if errors:
        print(f"FAIL Join map integrity ({len(errors)} issue(s))")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("OK Join map integrity (5.2). Criterion 5.3 still OPEN.")
    return 0


def main(argv: list[str] | None = None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--join-map-only" in argv:
        sys.exit(run_join_map_only())

    print("=" * 60)
    print("Capability Registry Sync Validation")
    print("=" * 60)
    try:
        from runtime.capability_framework import (
            CAPABILITY_CAP_TO_KEBAB_JOIN_MAP,
            CAPABILITY_ID_SCHEME,
            CAPABILITY_REGISTRY_SOT,
            CAPABILITY_REGISTRY_SOT_PATH,
        )

        print(
            f"SoT (DEC-132 / 5.1): {CAPABILITY_REGISTRY_SOT} "
            f"@ {CAPABILITY_REGISTRY_SOT_PATH} [{CAPABILITY_ID_SCHEME}]"
        )
        print(f"Join map (DEC-133 / 5.2): {CAPABILITY_CAP_TO_KEBAB_JOIN_MAP}")
        print("Secondary: SDK · governance YAML · docs CAP-### (converge toward SoT)")
        print("Criterion 5.3 = full sync exit 0 (still expected non-zero until convergence)")
    except Exception as exc:  # pragma: no cover - import path diagnostics only
        print(f"SoT pins unavailable ({exc}); continuing comparison")

    sdk_ids = validate_sdk_registry()
    decorator_ids = validate_decorator_framework()

    yaml_path = REPO_ROOT / "engineering-os" / "kernel" / "capability-registry.yaml"
    gov_ids = validate_governance_yaml(yaml_path)

    catalog_path = REPO_ROOT / "docs" / "CAPABILITY_CATALOG.md"
    catalog_ids = validate_capability_catalog(catalog_path)

    # ── Compare ──
    errors = []
    errors.extend(validate_cap_to_kebab_join_map(decorator_ids, catalog_ids))

    # SDK vs Decorator: SDK names should map to decorator IDs
    # Convert SDK names to IDs
    sdk_name_to_id = {
        "company intelligence": "company",
        "search & discovery": "search",
        "timeline & activity": "timeline",
        "recommendation engine": "recommendation",
        "decision context": "context",
        "ai copilot": "ai_copilot",
        "email intelligence": "email",
        "meeting intelligence": "meeting",
        "pipeline management": "pipeline",
        "opportunity management": "opportunity",
        "revenue analytics": "analytics",
        "revenue forecasting": "forecast",
        "contract management": "contract",
        "proposal management": "proposal",
        "quote management": "quote",
        "playbook": "playbook",
        "sales playbook": "playbook",
        "infrastructure": "infrastructure",
        "quota management": "quota",
        "territory management": "territory",
        "activity management": "activity",
        "entity resolution": "entity-resolution",
        "entity resolution": "entity_resolution",
    }

    sdk_ids_lower = {id.lower() for id in sdk_ids}
    # Manual mapping for SDK capability names to decorator IDs
    sdk_mapped: set[str] = set()
    for sdk_name in sdk_ids:
        sdk_lower = sdk_name.lower()
        mapped = sdk_name_to_id.get(sdk_lower, sdk_lower.replace(" ", "_"))
        sdk_mapped.add(mapped)

    missing_in_decorator = sdk_mapped - decorator_ids
    if missing_in_decorator:
        errors.append(f"SDK capabilities missing in Decorator Framework: {missing_in_decorator}")

    missing_in_sdk = decorator_ids - sdk_mapped
    if missing_in_sdk:
        errors.append(f"Decorator capabilities missing in SDK Registry: {missing_in_sdk}")

    # SDK vs Governance YAML
    # Governance uses kebab-case, SDK IDs are lower_snake_case
    missing_in_gov = set()
    for sdk_cap in sdk_mapped:
        gov_id = sdk_cap.replace("_", "-")
        if gov_id not in gov_ids:
            missing_in_gov.add(sdk_cap)
    if missing_in_gov:
        errors.append(f"SDK capabilities missing in Governance YAML: {missing_in_gov}")

    # Decorator vs Governance YAML
    missing_decorator_in_gov = set()
    for decorator_id in decorator_ids:
        gov_id = decorator_id.replace("_", "-")
        if gov_id not in gov_ids:
            missing_decorator_in_gov.add(decorator_id)
    if missing_decorator_in_gov:
        errors.append(f"Decorator capabilities missing in Governance YAML: {missing_decorator_in_gov}")

    print("\n" + "=" * 60)
    if errors:
        print(f"FAIL {len(errors)} sync issue(s) found:")
        for e in errors:
            print(f"  - {e}")
        print("\nRun `python scripts/sync_capability_registries.py` to auto-fix.")
        print("(Full exit 0 = criterion 5.3; join-map-only OK does not close 5.3.)")
        sys.exit(1)
    else:
        print("OK All capability registries are in sync!")
        sys.exit(0)


if __name__ == "__main__":
    main()
