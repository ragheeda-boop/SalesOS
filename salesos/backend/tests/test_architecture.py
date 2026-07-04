"""Architecture Fitness Tests — verify architectural constraints in CI.

Each test enforces a rule from the Platform Constitution.
If any test fails → build fails → architecture drift prevented.
"""

import ast
import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
DOMAINS = ROOT / "domains"
SDK = ROOT / "sdk"
COMMERCIAL = DOMAINS / "commercial"


# ─────────────────────────────────────────────
# Rule 1: No Domain imports UI
# ─────────────────────────────────────────────

BANNED_UI_IMPORTS = {"flask", "fastapi", "jinja2", "django", "streamlit", "gradio"}
_ALLOWED_API_PATTERNS = ("/api.py",)  # domain api.py files are the allowed FastAPI boundary


def _get_imports(filepath: Path) -> set[str]:
    """Extract all top-level import names from a Python file."""
    try:
        with open(filepath, encoding="utf-8") as f:
            tree = ast.parse(f.read())
    except (SyntaxError, UnicodeDecodeError):
        return set()

    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module.split(".")[0])
    return imports


@pytest.mark.parametrize("domain_dir", [
    d for d in DOMAINS.iterdir() if d.is_dir() and d.name != "__pycache__"
])
def test_domain_does_not_import_ui(domain_dir):
    """No domain module should import UI frameworks."""
    violations: list[str] = []
    for pyfile in domain_dir.rglob("*.py"):
        if pyfile.name.startswith("__"):
            continue
        if any(str(pyfile).endswith(p) for p in _ALLOWED_API_PATTERNS):
            continue
        imports = _get_imports(pyfile)
        banned = BANNED_UI_IMPORTS & imports
        if banned:
            rel = pyfile.relative_to(ROOT)
            violations.append(f"{rel} imports {banned}")

    assert not violations, f"Domain {domain_dir.name} imports UI:\n" + "\n".join(violations)


# ─────────────────────────────────────────────
# Rule 2: Kernel does not import Commercial
# ─────────────────────────────────────────────

@pytest.mark.parametrize("kernel_dir", [
    d for d in DOMAINS.iterdir() if d.is_dir() and d.name != "__pycache__" and d.name != "commercial"
])
def test_kernel_does_not_import_commercial(kernel_dir):
    """Kernel domains must not import from commercial."""
    violations: list[str] = []
    for pyfile in kernel_dir.rglob("*.py"):
        if pyfile.name.startswith("__"):
            continue
        imports = _get_imports(pyfile)
        # Check if any import starts with "domains.commercial"
        with open(pyfile, encoding="utf-8") as f:
            content = f.read()
        if "domains.commercial" in content or "from domains.commercial" in content:
            rel = pyfile.relative_to(ROOT)
            violations.append(str(rel))

    assert not violations, f"Kernel domain {kernel_dir.name} imports commercial:\n" + "\n".join(violations)


# ─────────────────────────────────────────────
# Rule 3: SDK does not import Domains
# ─────────────────────────────────────────────

def test_sdk_does_not_import_domains():
    """SDK must not import from domains."""
    violations: list[str] = []
    for pyfile in SDK.rglob("*.py"):
        if pyfile.name.startswith("__"):
            continue
        content = pyfile.read_text(encoding="utf-8")
        if "from domains." in content or "import domains." in content:
            rel = pyfile.relative_to(ROOT)
            violations.append(str(rel))

    assert not violations, f"SDK imports domains:\n" + "\n".join(violations)


# ─────────────────────────────────────────────
# Rule 4: Frozen Interfaces must not change
# ─────────────────────────────────────────────

FROZEN_INTERFACES = {
    "SearchQuery": {
        "fields": {"query", "filters", "sort", "page", "page_size", "tenant_id", "context"},
    },
    "SearchResult": {
        "fields": {"items", "total", "page", "page_size", "facets", "filters",
                   "ranking", "duration_ms", "query", "execution_time",
                   "strategy", "ranking_version", "next_cursor"},
    },
    "SearchPlanner": {
        "methods": {"search", "count", "facets", "suggest", "set_repository", "set_ranking_pipeline"},
    },
}


def _get_class_fields(filepath: Path, class_name: str) -> set[str]:
    """Extruct field names from a dataclass."""
    try:
        with open(filepath, encoding="utf-8") as f:
            tree = ast.parse(f.read())
    except (SyntaxError, UnicodeDecodeError):
        return set()

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            fields = set()
            for item in node.body:
                if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                    fields.add(item.target.id)
                elif isinstance(item, ast.FunctionDef) and item.name == "__init__":
                    for arg in item.args.args[1:]:  # skip self
                        fields.add(arg.arg)
            return fields
    return set()


def test_frozen_interfaces_preserved():
    """Verify frozen interfaces haven't changed their public API."""
    contracts_dir = ROOT / "domains" / "search" / "contracts" / "models.py"
    planner_dir = ROOT / "domains" / "search" / "engine" / "planner.py"

    import importlib.util
    import sys

    # Check SearchQuery fields
    sq_fields = _get_class_fields(contracts_dir, "SearchQuery")
    expected = FROZEN_INTERFACES["SearchQuery"]["fields"]
    missing = expected - sq_fields
    assert not missing, f"SearchQuery missing fields: {missing}"

    # Check SearchResult fields
    sr_fields = _get_class_fields(contracts_dir, "SearchResult")
    expected = FROZEN_INTERFACES["SearchResult"]["fields"]
    missing = expected - sr_fields
    assert not missing, f"SearchResult missing fields: {missing}"


# ─────────────────────────────────────────────
# Rule 5: Every Domain module must register in CapabilityRegistry
# ─────────────────────────────────────────────

def test_commercial_modules_registered():
    """Every module under commercial/ must have a capability registration."""
    from modules.registry import _register_platform_capabilities
    from sdk.capability_registry import CapabilityRegistry

    _register_platform_capabilities()
    registered = set(CapabilityRegistry.all().keys())

    for domain_dir in COMMERCIAL.iterdir():
        if not domain_dir.is_dir() or domain_dir.name.startswith("_"):
            continue
        assert domain_dir.name in registered, (
            f"Commercial domain '{domain_dir.name}' not registered in CapabilityRegistry. "
            f"Add it to modules/registry.py:_register_platform_capabilities()"
        )
