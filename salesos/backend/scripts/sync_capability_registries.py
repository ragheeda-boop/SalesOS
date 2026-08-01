"""Helper notes for secondary registry sync (NOT the 5.3 close gate).

Usage:
    python scripts/sync_capability_registries.py

**SoT (DEC-132 / 5.1):** Decorator framework is the canonical *runtime* source
of truth. This helper historically appended missing SDK-derived entries into
governance YAML (secondary→secondary).

**DEC-134 / criterion 5.3:** Close gate is
``validate_capability_registries.py`` (default SoT-oriented mode):
joined secondaries subset-of decorator SoT via join map. Do **not** delete secondary
SDK/YAML entries to force exit 0. Do **not** treat this sync helper as SoT.

This script is import-light diagnostics only (source/YAML parse). It does not
mutate YAML by default — mutation of governance YAML requires an explicit
``--apply`` flag and remains secondary→secondary (not recommended for 5.3).
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _resolve_repo_root() -> Path:
    raw = os.environ.get("MUHIDE_REPO_ROOT") or os.environ.get("REPO_ROOT")
    if raw:
        candidate = Path(raw).resolve()
        if (candidate / "engineering-os" / "kernel" / "capability-registry.yaml").exists():
            return candidate
    here = PROJECT_ROOT
    for _ in range(6):
        if (here / "engineering-os" / "kernel" / "capability-registry.yaml").exists():
            return here
        if here.parent == here:
            break
        here = here.parent
    return PROJECT_ROOT.parent.parent


REPO_ROOT = _resolve_repo_root()


def decorator_ids_from_source() -> set[str]:
    init_path = PROJECT_ROOT / "runtime" / "capability_framework" / "__init__.py"
    text = init_path.read_text(encoding="utf-8")
    return set(re.findall(r'^\s*id="([a-z0-9]+(?:-[a-z0-9]+)*)"', text, re.MULTILINE))


def sdk_ids_from_source() -> set[str]:
    registry_path = PROJECT_ROOT / "modules" / "registry.py"
    text = registry_path.read_text(encoding="utf-8")
    return set(
        re.findall(
            r"CapabilityRegistry\.register\(\s*Capability\(\s*name=\"([^\"]+)\"",
            text,
            re.DOTALL,
        )
    )


def get_yaml_capability_ids(yaml_path: Path) -> set[str]:
    if not yaml_path.exists():
        return set()
    content = yaml_path.read_text(encoding="utf-8")
    return set(re.findall(r'^\s+- id:\s+"([^"]+)"', content, re.MULTILINE))


def _to_kebab(raw: str) -> str:
    return raw.strip().lower().replace("_", "-").replace(" ", "-")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Capability secondary sync helper (DEC-134)")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Append missing SDK-aligned IDs into governance YAML (secondary; not 5.3 gate)",
    )
    args = parser.parse_args(argv)

    yaml_path = REPO_ROOT / "engineering-os" / "kernel" / "capability-registry.yaml"
    if not yaml_path.exists():
        print(f"YAML not found: {yaml_path}")
        sys.exit(1)

    decorator_ids = decorator_ids_from_source()
    sdk_ids = sdk_ids_from_source()
    gov_ids = get_yaml_capability_ids(yaml_path)

    sdk_kebab = {_to_kebab(x) for x in sdk_ids}
    gov_kebab = {_to_kebab(x) for x in gov_ids}

    print("SoT (DEC-132): decorator-framework kebab IDs")
    print(f"  sot={len(decorator_ids)} sdk={len(sdk_kebab)} yaml={len(gov_kebab)}")
    print("5.3 gate: validate_capability_registries.py (SoT-oriented; do not delete secondaries)")

    aligned_sdk = sorted(sdk_kebab & decorator_ids)
    residual_sdk = sorted(sdk_kebab - decorator_ids)
    print(f"\nSDK aligned to SoT ({len(aligned_sdk)}): {aligned_sdk}")
    print(f"SDK secondary residual ({len(residual_sdk)}): {residual_sdk}")

    aligned_gov = sorted(gov_kebab & decorator_ids)
    residual_gov = sorted(gov_kebab - decorator_ids)
    print(f"\nYAML aligned to SoT ({len(aligned_gov)}): {aligned_gov}")
    print(f"YAML secondary residual ({len(residual_gov)}): {residual_gov}")

    # Optional secondary→secondary append (legacy helper; off by default).
    name_to_yaml_id = {
        "company": "company",  # prefer SoT id if appending; do not invent company-360
        "search": "search",
        "timeline": "timeline",
        "identity": "identity",
    }
    missing_for_apply = []
    for name in sdk_ids:
        yaml_id = name_to_yaml_id.get(name.lower(), _to_kebab(name))
        if yaml_id in decorator_ids and yaml_id not in gov_ids:
            missing_for_apply.append((yaml_id, name))

    if not args.apply:
        if missing_for_apply:
            print(
                f"\nINFO {len(missing_for_apply)} SoT-aligned SDK IDs absent from YAML "
                f"(run with --apply to append secondary mirrors): "
                f"{[m[0] for m in missing_for_apply]}"
            )
        else:
            print("\nINFO No SoT-aligned SDK IDs missing from YAML.")
        print("Sync diagnostic complete (no mutation). Prefer validate_capability_registries.py.")
        sys.exit(0)

    if not missing_for_apply:
        print("\nNothing to apply.")
        sys.exit(0)

    print(f"\nApplying {len(missing_for_apply)} secondary YAML append(s)...")
    with yaml_path.open("a", encoding="utf-8") as f:
        for yaml_id, name in missing_for_apply:
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
            print(f"  + Added '{yaml_id}' ({name})")
    print("Apply complete (secondary only; SoT unchanged).")


if __name__ == "__main__":
    main()
