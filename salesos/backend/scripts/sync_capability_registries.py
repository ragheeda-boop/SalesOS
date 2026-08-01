"""Auto-sync capability registries: update Governance YAML from SDK registry.

Usage:
    python scripts/sync_capability_registries.py

**SoT (DEC-132 / Phase 0 criterion 5.1):** Decorator framework is the canonical
*runtime* source of truth. This helper currently appends missing SDK-derived
entries into governance YAML (secondary→secondary). Criterion **5.3** should
reorient sync toward decorator kebab IDs; do not treat this script as SoT.

Updates:
    - engineering-os/kernel/capability-registry.yaml
      with any capabilities from the SDK CapabilityRegistry that are missing.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def get_sdk_capabilities() -> dict:
    """Extract all registered SDK capabilities."""
    from sdk.capability_registry import CapabilityRegistry

    return {c.name: c for c in CapabilityRegistry.all()}


def get_decorator_capabilities() -> dict:
    """Extract all decorator framework capabilities."""
    from runtime.capability_framework import Capability

    return {c.id: c for c in Capability.all()}


def get_yaml_capability_ids(yaml_path: Path) -> set[str]:
    """Get set of capability IDs from YAML."""
    import re

    if not yaml_path.exists():
        return set()
    content = yaml_path.read_text(encoding="utf-8")
    return set(re.findall(r'^\s+- id:\s+"([^"]+)"', content, re.MULTILINE))


def main():
    yaml_path = PROJECT_ROOT.parent / "engineering-os" / "kernel" / "capability-registry.yaml"
    if not yaml_path.exists():
        print(f"❌ YAML not found: {yaml_path}")
        sys.exit(1)

    sdk_caps = get_sdk_capabilities()
    decorator_caps = get_decorator_capabilities()
    gov_ids = get_yaml_capability_ids(yaml_path)

    # Map SDK names to YAML kebab-case IDs
    name_to_yaml_id = {
        "company intelligence": "company-360",
        "search & discovery": "search",
        "timeline & activity": "timeline",
        "opportunity management": "opportunity",
        "pipeline management": "pipeline",
        "activity management": "activity",
        "contract management": "contract",
        "proposal management": "proposal",
        "quote management": "quote",
        "email intelligence": "email",
        "meeting intelligence": "meeting",
        "quota management": "quota",
        "territory management": "territory",
        "revenue analytics": "analytics",
        "revenue forecasting": "forecast",
        "decision context": "context",
        "recommendation engine": "recommendation",
        "entity resolution": "entity-resolution",
        "infrastructure": "infrastructure",
        "sales playbook": "playbook",
        "ai copilot": "ai_copilot",
    }

    missing_in_yaml = set()
    for name, cap in sdk_caps.items():
        yaml_id = name_to_yaml_id.get(name.lower())
        if yaml_id and yaml_id not in gov_ids:
            missing_in_yaml.add((yaml_id, name, cap))

    if not missing_in_yaml:
        print("✅ All SDK capabilities are present in Governance YAML.")
    else:
        print(f"Adding {len(missing_in_yaml)} missing capabilities to YAML...")
        with yaml_path.open("a", encoding="utf-8") as f:
            for yaml_id, name, cap in missing_in_yaml:
                entry = f"""
  - id: "{yaml_id}"
    name: "{name}"
    owner: "platform"
    status: "in_progress"
    version: "v0.8.0"
    dependencies: []
    api: []
    frontend: []
    tests:
      unit: false
      integration: false
      e2e: false
    documentation: []
    frozen: false
"""
                f.write(entry)
                print(f"  ✓ Added '{yaml_id}' ({name})")

    # Check decorator framework for gaps
    decorator_ids = set(decorator_caps.keys())
    sdk_yaml_ids = {name_to_yaml_id.get(n.lower(), n.lower().replace(" ", "_"))
                     for n in sdk_caps}

    # Activity Intelligence is a separate concept from SDK's "activity"
    sdk_yaml_ids.add("activity-intelligence")
    sdk_yaml_ids.add("workflow")

    missing_in_decorator = sdk_yaml_ids - decorator_ids
    if missing_in_decorator:
        print(f"\n⚠ {len(missing_in_decorator)} capabilities missing from Decorator Framework (add manually to runtime/capability_framework/__init__.py):")
        for c in sorted(missing_in_decorator):
            print(f"  - {c}")

    print("\n✅ Sync complete.")


if __name__ == "__main__":
    main()
