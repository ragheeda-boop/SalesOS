"""Validate capability registries are in sync across all 4 sources.

Usage:
    python scripts/validate_capability_registries.py

Returns exit code 0 if all registries are in sync, non-zero on mismatch.

This validates alignment between:
    1. SDK CapabilityRegistry (sdk/capability_registry.py + modules/registry.py)
    2. Decorator Framework (runtime/capability_framework/__init__.py)
    3. Governance YAML (engineering-os/kernel/capability-registry.yaml)
    4. Documentation Catalog (docs/CAPABILITY_CATALOG.md) -- checks only ID presence
"""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def validate_sdk_registry():
    """Ensure modules/registry.py registers all expected capabilities."""
    from sdk.capability_registry import CapabilityRegistry

    registry = CapabilityRegistry
    all_caps = registry.all()
    cap_names = {c.name for c in all_caps}
    print(f"\n[SDK Registry] {len(all_caps)} capabilities registered:")
    for c in all_caps:
        print(f"  ✓ {c.name} ({c.type.value})")
    return cap_names


def validate_decorator_framework():
    """Ensure decorator registry has all expected capabilities."""
    from runtime.capability_framework import Capability

    all_caps = Capability.all()
    cap_ids = {c.id for c in all_caps}
    print(f"\n[Decorator Framework] {len(all_caps)} capabilities registered:")
    for c in all_caps:
        status = c.manifest.status.value
        print(f"  ✓ {c.id} ({c.manifest.name}) [{status}]")
    return cap_ids


def validate_governance_yaml(yaml_path: Path) -> set[str]:
    """Parse governance YAML and extract capability IDs."""
    import re

    if not yaml_path.exists():
        print(f"\n[Governance YAML] ⚠ File not found: {yaml_path}")
        return set()

    content = yaml_path.read_text(encoding="utf-8")
    cap_ids = set(re.findall(r'^\s+- id:\s+"([^"]+)"', content, re.MULTILINE))
    print(f"\n[Governance YAML] {len(cap_ids)} capabilities found:")
    for cid in sorted(cap_ids):
        print(f"  ✓ {cid}")
    return cap_ids


def validate_capability_catalog(md_path: Path) -> set[str]:
    """Parse CAPABILITY_CATALOG.md and extract capability IDs."""
    import re

    if not md_path.exists():
        print(f"\n[Capability Catalog] ⚠ File not found: {md_path}")
        return set()

    content = md_path.read_text(encoding="utf-8")
    cap_ids = set(re.findall(r'\bCAP-(\d{3}):\s+\*\*([^*]+)\*\*', content))
    names = {name.strip().lower().replace(" ", "-") for _, name in cap_ids}
    print(f"\n[Capability Catalog] {len(cap_ids)} capabilities found:")
    for num, name in sorted(cap_ids):
        print(f"  ✓ CAP-{num}: {name}")
    return names


def main():
    print("=" * 60)
    print("Capability Registry Sync Validation")
    print("=" * 60)

    sdk_ids = validate_sdk_registry()
    decorator_ids = validate_decorator_framework()

    yaml_path = PROJECT_ROOT.parent / "engineering-os" / "kernel" / "capability-registry.yaml"
    gov_ids = validate_governance_yaml(yaml_path)

    catalog_path = PROJECT_ROOT.parent / "docs" / "CAPABILITY_CATALOG.md"
    catalog_ids = validate_capability_catalog(catalog_path)

    # ── Compare ──
    errors = []

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
        print(f"❌ {len(errors)} sync issue(s) found:")
        for e in errors:
            print(f"  - {e}")
        print("\nRun `python scripts/sync_capability_registries.py` to auto-fix.")
        sys.exit(1)
    else:
        print("✅ All capability registries are in sync!")
        sys.exit(0)


if __name__ == "__main__":
    main()
