#!/usr/bin/env python3
"""EOS fingerprint measurement helper (Phase 0 criteria 4.2 / 4.4 / 4.7).

Re-run from repo root and diff against `.engineering/23_PROJECT_FINGERPRINT.json`.
Does not mutate files. Docker `alembic heads` is optional corroboration.
"""
from __future__ import annotations

import json
import re
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BINARY_EXT = {
    "pptx",
    "xlsx",
    "zip",
    "pdf",
    "png",
    "jpg",
    "jpeg",
    "gif",
    "svg",
    "woff2",
    "ttf",
    "otf",
    "map",
}
SKIP_SUBSTR = ("node_modules", "/.next/", "__pycache__", ".pytest_cache", ".ruff_cache")


def run(*args: str) -> str:
    return subprocess.check_output(args, cwd=ROOT, text=True, encoding="utf-8", errors="replace")


def git_ls_files() -> list[str]:
    return [ln for ln in run("git", "ls-files").splitlines() if ln]


def parse_alembic_heads(versions: Path) -> tuple[list[str], int, dict[str, str]]:
    revs: dict[str, str] = {}
    downs: set[str] = set()
    for f in sorted(versions.glob("*.py")):
        text = f.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"^revision(?::\s*str)?\s*=\s*[\"']([^\"']+)[\"']", text, re.M)
        d = re.search(r"^down_revision(?::\s*[^=]+)?\s*=\s*([^\n]+)", text, re.M)
        if not m:
            continue
        rev = m.group(1)
        revs[rev] = f.name
        if not d:
            continue
        val = d.group(1).strip()
        if val == "None":
            continue
        for x in re.findall(r"[\"']([^\"']+)[\"']", val):
            downs.add(x)
    heads = sorted(r for r in revs if r not in downs)
    return heads, len(revs), {h: revs[h] for h in heads}


def main() -> None:
    head7 = run("git", "rev-parse", "--short=7", "HEAD").strip()
    head_full = run("git", "rev-parse", "HEAD").strip()
    branch = run("git", "rev-parse", "--abbrev-ref", "HEAD").strip()
    files = git_ls_files()
    filtered = [
        p
        for p in files
        if not any(s in p.replace("\\", "/") for s in SKIP_SUBSTR)
        and Path(p).suffix.lstrip(".").lower() not in BINARY_EXT
    ]
    ext_hist = Counter(
        (Path(p).suffix.lstrip(".").lower() or "extensionless") for p in files
    )
    versions = ROOT / "salesos" / "backend" / "app" / "alembic" / "versions"
    heads, rev_count, head_files = parse_alembic_heads(versions)
    modules = sorted(
        d.name
        for d in (ROOT / "salesos" / "backend" / "app" / "modules").iterdir()
        if d.is_dir() and d.name != "__pycache__"
    )
    domains = sorted(
        d.name
        for d in (ROOT / "salesos" / "backend" / "domains").iterdir()
        if d.is_dir() and d.name != "__pycache__"
    )
    runtime = sorted(
        d.name
        for d in (ROOT / "salesos" / "backend" / "runtime").iterdir()
        if d.is_dir() and d.name != "__pycache__"
    )
    pages = list((ROOT / "salesos" / "frontend" / "src" / "app").rglob("page.tsx"))
    routers = (ROOT / "salesos" / "backend" / "app" / "boot" / "routers.py").read_text(
        encoding="utf-8", errors="replace"
    )
    include_router = len(re.findall(r"include_router", routers))
    fe_pkgs = sorted(
        d.name
        for d in (ROOT / "salesos" / "frontend" / "packages").iterdir()
        if d.is_dir()
    )
    tests = [
        p
        for p in files
        if p.replace("\\", "/").startswith("salesos/backend/")
        and (
            re.search(r"/test_[^/]+\.py$", p.replace("\\", "/"))
            or p.endswith("_test.py")
        )
    ]
    e2e = list((ROOT / "salesos" / "frontend" / "e2e").rglob("*.spec.ts"))
    workflows = list((ROOT / ".github" / "workflows").glob("*.yml"))
    k8s = list((ROOT / "salesos" / "infra" / "k8s").rglob("*.yaml")) + list(
        (ROOT / "salesos" / "infra" / "k8s").rglob("*.yml")
    )
    monitoring = [
        p for p in (ROOT / "salesos" / "infra" / "monitoring").rglob("*") if p.is_file()
    ]
    pyproject = (ROOT / "salesos" / "backend" / "pyproject.toml").read_text(
        encoding="utf-8", errors="replace"
    )
    fastapi_m = re.search(r'^fastapi\s*=\s*"([^"]+)"', pyproject, re.M)
    sub_head = run("git", "-C", "engineering-os", "rev-parse", "HEAD").strip()
    sub_dirty = bool(run("git", "-C", "engineering-os", "status", "--porcelain").strip())

    alembic_cli_heads: list[str] | None = None
    alembic_cli_error: str | None = None
    try:
        out = subprocess.check_output(
            ["docker", "compose", "exec", "-T", "backend", "alembic", "heads"],
            cwd=ROOT / "salesos",
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=90,
        )
        alembic_cli_heads = [
            ln.split()[0]
            for ln in out.splitlines()
            if ln.strip() and "(head)" in ln
        ] or [ln.split()[0] for ln in out.splitlines() if ln.strip()]
    except Exception as exc:  # noqa: BLE001
        alembic_cli_error = str(exc)

    print(
        json.dumps(
            {
                "measured_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "repository_commit": head7,
                "repository_commit_full": head_full,
                "repository_branch": branch,
                "tracked_files_raw": len(files),
                "tracked_files_filtered": len(filtered),
                "languages_top": dict(ext_hist.most_common(15)),
                "migration_files": rev_count,
                "alembic_heads_parsed": heads,
                "alembic_head_files": head_files,
                "alembic_cli_heads": alembic_cli_heads,
                "alembic_cli_error": alembic_cli_error,
                "fastapi_constraint": fastapi_m.group(1) if fastapi_m else None,
                "backend_app_modules": len(modules),
                "module_names": modules,
                "backend_domains": len(domains),
                "domain_names": domains,
                "backend_runtime_engines": len(runtime),
                "frontend_app_router_pages_tsx": len(pages),
                "include_router_registrations": include_router,
                "frontend_workspace_packages": len(fe_pkgs),
                "backend_test_files": len(tests),
                "frontend_e2e_files": len(e2e),
                "workflow_count": len(workflows),
                "k8s_manifests": len(k8s),
                "monitoring_files": len(monitoring),
                "engineering_os_head": sub_head,
                "engineering_os_dirty": sub_dirty,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
