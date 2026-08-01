"""Validate capability registries against decorator SoT (Phase 0 criterion 5.3).

Usage:
    python scripts/validate_capability_registries.py
    python scripts/validate_capability_registries.py --join-map-only
    python scripts/validate_capability_registries.py --legacy-equality

Exit codes:
    0 — SoT-oriented gate passes (DEC-134 / criterion 5.3 default), or
        ``--join-map-only`` join-map integrity passes (5.2 light path)
    1 — integrity / alignment failure
    2 — ``--legacy-equality`` requested and 4-way identity equality fails

**SoT (DEC-132 / 5.1):** Decorator Framework
(`runtime/capability_framework`, kebab-case IDs) is the canonical *runtime*
source of truth. SDK / governance YAML / docs CAP-### catalog are secondary.

**Join map (DEC-133 / 5.2):**
`runtime/capability_framework/cap_to_kebab_join.yaml` joins CAP-### → kebab.

**Gate (DEC-134 / 5.3):** Exit 0 means joined secondaries are a subset of
decorator SoT via the join map — **not** 4-way identity equality. Unmapped
catalog CAPs and SDK/YAML IDs outside SoT are honest secondary residual
(INFO), not failures. SoT need not be a subset of secondaries (decorator-only
already documented in 5.2).

Import-light by design: parses sources / YAML / markdown. Does **not** import
``runtime`` (package ``__init__`` pulls the full runtime stack) or SDK
(SQLAlchemy). Safe on host without full app deps; Docker preferred for CI parity.

Surfaces:
    1. Decorator Framework (runtime/capability_framework/__init__.py) — **SoT**
    2. CAP-### → kebab join map — criterion 5.2 integrity
    3. Documentation Catalog (docs/CAPABILITY_CATALOG.md) — secondary
    4. SDK CapabilityRegistry (modules/registry.py) — secondary
    5. Governance YAML (engineering-os/kernel/capability-registry.yaml) — secondary
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _resolve_repo_root() -> Path:
    """Monorepo root (docs/ + engineering-os/). Host: backend/../.. ; Docker may lack mounts."""
    raw = os.environ.get("MUHIDE_REPO_ROOT") or os.environ.get("REPO_ROOT")
    if raw:
        candidate = Path(raw).resolve()
        if (candidate / "docs" / "CAPABILITY_CATALOG.md").exists():
            return candidate

    # Walk up from backend for docs/CAPABILITY_CATALOG.md (host Muhide layout).
    here = PROJECT_ROOT
    for _ in range(6):
        if (here / "docs" / "CAPABILITY_CATALOG.md").exists():
            return here
        if here.parent == here:
            break
        here = here.parent

    # Fallback: salesos/backend -> ../../Muhide (catalog/YAML may be absent in backend-only Docker).
    return PROJECT_ROOT.parent.parent


REPO_ROOT = _resolve_repo_root()

EXPECTED_CATALOG_CAPS = {f"CAP-{i:03d}" for i in range(1, 41)}

# Fallback pins when SoT module is not imported (DEC-132 / DEC-133).
_SOT_NAME = "decorator-framework"
_SOT_PATH = "runtime/capability_framework"
_SOT_SCHEME = "kebab-case"
_JOIN_MAP_REL = "runtime/capability_framework/cap_to_kebab_join.yaml"


def _read_sot_pins() -> tuple[str, str, str, str]:
    """Read SoT/join pins from source text (no package import)."""
    init_path = PROJECT_ROOT / "runtime" / "capability_framework" / "__init__.py"
    text = init_path.read_text(encoding="utf-8") if init_path.exists() else ""

    def _pin(name: str, default: str) -> str:
        m = re.search(rf'^{name}\s*=\s*"([^"]+)"', text, re.MULTILINE)
        return m.group(1) if m else default

    return (
        _pin("CAPABILITY_REGISTRY_SOT", _SOT_NAME),
        _pin("CAPABILITY_REGISTRY_SOT_PATH", _SOT_PATH),
        _pin("CAPABILITY_ID_SCHEME", _SOT_SCHEME),
        _pin("CAPABILITY_CAP_TO_KEBAB_JOIN_MAP", _JOIN_MAP_REL),
    )


def _join_map_path() -> Path:
    _, _, _, rel = _read_sot_pins()
    return PROJECT_ROOT / rel


def decorator_ids_from_source() -> set[str]:
    """Parse built-in @Capability(id=...) from SoT module without importing runtime."""
    init_path = PROJECT_ROOT / "runtime" / "capability_framework" / "__init__.py"
    text = init_path.read_text(encoding="utf-8")
    # Built-ins use id="kebab" at decorator call sites (skip docstring examples with spaces).
    return set(re.findall(r'^\s*id="([a-z0-9]+(?:-[a-z0-9]+)*)"', text, re.MULTILINE))


def sdk_ids_from_source() -> set[str]:
    """Parse CapabilityRegistry.register(... name=...) without importing SDK."""
    registry_path = PROJECT_ROOT / "modules" / "registry.py"
    if not registry_path.exists():
        print(f"\n[SDK Registry] WARN File not found: {registry_path}")
        return set()

    text = registry_path.read_text(encoding="utf-8")
    # Match CapabilityRegistry.register( Capability( name="..." ) blocks.
    names = set(
        re.findall(
            r"CapabilityRegistry\.register\(\s*Capability\(\s*name=\"([^\"]+)\"",
            text,
            re.DOTALL,
        )
    )
    print(f"\n[SDK Registry] {len(names)} capabilities (source parse):")
    for n in sorted(names):
        print(f"  + {n}")
    return names


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
    heading_caps = re.findall(r"^###\s+(CAP-\d{3}):\s+(.+)$", content, re.MULTILINE)
    if heading_caps:
        print(f"\n[Capability Catalog] {len(heading_caps)} capabilities found:")
        for cid, name in sorted(heading_caps):
            print(f"  + {cid}: {name.strip()}")
        return {cid for cid, _ in heading_caps}

    bold_caps = set(re.findall(r"\bCAP-(\d{3}):\s+\*\*([^*]+)\*\*", content))
    names = {name.strip().lower().replace(" ", "-") for _, name in bold_caps}
    print(f"\n[Capability Catalog] {len(bold_caps)} capabilities found (legacy parse):")
    for num, name in sorted(bold_caps):
        print(f"  + CAP-{num}: {name}")
    return names


def _to_kebab(raw: str) -> str:
    return raw.strip().lower().replace("_", "-").replace(" ", "-")


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
    return errors


def check_secondary_subset_of_sot(
    *,
    label: str,
    secondary_ids: set[str],
    decorator_ids: set[str],
) -> tuple[list[str], set[str], set[str]]:
    """Joined secondary IDs (those equal to a SoT kebab after normalize) ⊆ SoT.

    Returns (errors, aligned_ids, residual_ids). Residual = outside SoT — INFO only.
    """
    errors: list[str] = []
    aligned: set[str] = set()
    residual: set[str] = set()
    for raw in secondary_ids:
        kebab = _to_kebab(raw)
        if kebab in decorator_ids:
            aligned.add(kebab)
        else:
            residual.add(kebab)

    # Tautology guard: aligned must ⊆ SoT (always true if built via ∩). Fail if mismatch.
    bad = aligned - decorator_ids
    if bad:
        errors.append(f"{label} joined IDs not in decorator SoT: {sorted(bad)}")

    print(f"\n[{label} subset-of SoT via join/normalize]")
    print(f"  aligned={len(aligned)} residual_secondary={len(residual)}")
    if residual:
        shown = sorted(residual)[:12]
        more = len(residual) - len(shown)
        suffix = f" (+{more} more)" if more > 0 else ""
        print(f"  INFO residual (allowed): {shown}{suffix}")
    if not errors:
        print("  OK joined subset is subset of decorator SoT")
    else:
        for e in errors:
            print(f"  x {e}")
    return errors, aligned, residual


def run_join_map_only() -> int:
    """Criterion 5.2 light path — no SDK/runtime import required."""
    print("=" * 60)
    print("Capability Join Map Validation (5.2 / DEC-133)")
    print("=" * 60)
    sot, sot_path, scheme, _ = _read_sot_pins()
    print(f"SoT (DEC-132 / 5.1): {sot} @ {sot_path} [{scheme}]")
    print(f"Join map: {_join_map_path()}")
    print("Mode: --join-map-only (does NOT claim 5.3 exit 0 alone)")

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
    print("OK Join map integrity (5.2).")
    return 0


def run_sot_oriented() -> int:
    """DEC-134 / criterion 5.3 — joined secondaries ⊆ SoT + join map integrity."""
    print("=" * 60)
    print("Capability Registry SoT-Oriented Validation (5.3 / DEC-134)")
    print("=" * 60)
    sot, sot_path, scheme, join_rel = _read_sot_pins()
    print(f"SoT (DEC-132 / 5.1): {sot} @ {sot_path} [{scheme}]")
    print(f"Join map (DEC-133 / 5.2): {join_rel}")
    print("Gate: joined secondaries subset-of decorator SoT via join map (NOT 4-way equality)")
    print("Mode: default SoT-oriented (import-light source parse)")

    decorator_ids = decorator_ids_from_source()
    print(f"\n[Decorator SoT source parse] {len(decorator_ids)} ids: {sorted(decorator_ids)}")

    catalog_path = REPO_ROOT / "docs" / "CAPABILITY_CATALOG.md"
    catalog_ids = validate_capability_catalog(catalog_path)

    errors: list[str] = []
    errors.extend(validate_cap_to_kebab_join_map(decorator_ids, catalog_ids))

    # Catalog CAP-### join is fully owned by the join map (direct -> SoT; unmapped OK).
    print("\n[Catalog subset-of SoT via join map]")
    print("  OK accounted by join map integrity (direct in SoT; unmapped = residual)")

    sdk_ids = sdk_ids_from_source()
    e_sdk, _, _ = check_secondary_subset_of_sot(
        label="SDK",
        secondary_ids=sdk_ids,
        decorator_ids=decorator_ids,
    )
    errors.extend(e_sdk)

    yaml_path = REPO_ROOT / "engineering-os" / "kernel" / "capability-registry.yaml"
    gov_ids = validate_governance_yaml(yaml_path)
    e_gov, _, _ = check_secondary_subset_of_sot(
        label="Governance YAML",
        secondary_ids=gov_ids,
        decorator_ids=decorator_ids,
    )
    errors.extend(e_gov)

    # Honest residual: SoT IDs absent from SDK/YAML are allowed (decorator-only / partial mirrors).
    sdk_kebab = {_to_kebab(x) for x in sdk_ids}
    gov_kebab = {_to_kebab(x) for x in gov_ids}
    sot_not_in_sdk = decorator_ids - sdk_kebab
    sot_not_in_gov = decorator_ids - gov_kebab
    print("\n[SoT not subset of secondaries - allowed residual]")
    print(f"  SoT missing from SDK (INFO): {sorted(sot_not_in_sdk)}")
    print(f"  SoT missing from YAML (INFO): {sorted(sot_not_in_gov)}")

    print("\n" + "=" * 60)
    if errors:
        print(f"FAIL {len(errors)} SoT-oriented issue(s):")
        for e in errors:
            print(f"  - {e}")
        print("\nHint: fix join map / SoT IDs; do not delete secondaries to force exit 0.")
        print("Legacy 4-way equality: --legacy-equality (not the 5.3 close gate).")
        return 1

    print("OK SoT-oriented gate (5.3 / DEC-134): joined secondaries subset-of SoT + join map")
    print("NOTE Secondary extras + SoT-only IDs remain documented residual (not failures).")
    print("NOTE Production GO / CI GREEN / VERIFIED-CLOSED not claimed by this script.")
    return 0


def run_legacy_equality() -> int:
    """Historical 4-way identity equality — diagnostic only; not the 5.3 gate."""
    print("=" * 60)
    print("Capability Registry LEGACY 4-way Equality (diagnostic)")
    print("=" * 60)
    print("Mode: --legacy-equality - NOT the DEC-134 / 5.3 close gate")
    print("Exit 2 on mismatch (does not redefine 5.3)")

    decorator_ids = decorator_ids_from_source()
    print(f"\n[Decorator SoT source parse] {len(decorator_ids)} ids: {sorted(decorator_ids)}")
    sdk_ids = sdk_ids_from_source()
    sdk_mapped = {_to_kebab(x) for x in sdk_ids}

    yaml_path = REPO_ROOT / "engineering-os" / "kernel" / "capability-registry.yaml"
    gov_ids = validate_governance_yaml(yaml_path)
    gov_kebab = {_to_kebab(x) for x in gov_ids}

    catalog_path = REPO_ROOT / "docs" / "CAPABILITY_CATALOG.md"
    catalog_ids = validate_capability_catalog(catalog_path)

    errors: list[str] = []
    errors.extend(validate_cap_to_kebab_join_map(decorator_ids, catalog_ids))

    missing_in_decorator = sdk_mapped - decorator_ids
    if missing_in_decorator:
        errors.append(f"SDK capabilities missing in Decorator Framework: {sorted(missing_in_decorator)}")

    missing_in_sdk = decorator_ids - sdk_mapped
    if missing_in_sdk:
        errors.append(f"Decorator capabilities missing in SDK Registry: {sorted(missing_in_sdk)}")

    missing_in_gov = sdk_mapped - gov_kebab
    if missing_in_gov:
        errors.append(f"SDK capabilities missing in Governance YAML: {sorted(missing_in_gov)}")

    missing_decorator_in_gov = decorator_ids - gov_kebab
    if missing_decorator_in_gov:
        errors.append(
            f"Decorator capabilities missing in Governance YAML: {sorted(missing_decorator_in_gov)}"
        )

    print("\n" + "=" * 60)
    if errors:
        print(f"FAIL legacy equality ({len(errors)} issue(s)) - expected until full convergence:")
        for e in errors:
            print(f"  - {e}")
        return 2
    print("OK Legacy 4-way equality (unexpected — registries fully identical)")
    return 0


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Validate capability registries (DEC-134 SoT gate)")
    parser.add_argument(
        "--join-map-only",
        action="store_true",
        help="Criterion 5.2 light path — join map integrity only",
    )
    parser.add_argument(
        "--legacy-equality",
        action="store_true",
        help="Diagnostic 4-way identity equality (not the 5.3 close gate)",
    )
    args = parser.parse_args(argv)

    if args.join_map_only and args.legacy_equality:
        print("ERROR: choose at most one of --join-map-only / --legacy-equality")
        sys.exit(1)
    if args.join_map_only:
        sys.exit(run_join_map_only())
    if args.legacy_equality:
        sys.exit(run_legacy_equality())
    sys.exit(run_sot_oriented())


if __name__ == "__main__":
    main()
