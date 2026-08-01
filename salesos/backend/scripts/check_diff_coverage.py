#!/usr/bin/env python3
"""Fail if newly added/changed lines fall below a coverage threshold (STORY-03-03).

Distinct from the existing `--cov-fail-under=85` gate in
.github/workflows/ci.yml, which is repo-wide and would take years to move on
a 2,000+ file codebase with documented Grade D historical coverage (see
CANONICAL_ARCHITECTURE.md §17). This gate looks only at lines a PR actually
added or changed, per docs/program/TEST_STRATEGY.md §0's stated policy
("New/changed line coverage | >=80% | CI, diff-coverage tool, blocks merge").
The two gates are independent and both stay on — this one holds the line on
new code without requiring the whole repo to be retrofitted first.

Usage (local/docker):
  python scripts/check_diff_coverage.py --coverage-xml coverage.xml --base-ref origin/main
  docker compose exec -T backend python scripts/check_diff_coverage.py --base-ref origin/main

Exit 0 if diff coverage >= --fail-under (default 80.0) or there are no
in-scope changed lines; exit 1 on a genuine drop below threshold; exit 2 on
a usage/environment error (missing coverage.xml, git not available, etc.) —
distinguished from a real coverage failure so CI can tell "the gate caught
something" apart from "the gate itself is broken."

Never runs git commands that mutate the working tree (no checkout, no
merge, no reset) — read-only `git diff`/`git rev-parse` only. Never targets
production; this only ever reads local git history and a coverage report.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

# Cobertura XML from coverage.py is local CI output (not untrusted network XML).
# Parse with regex instead of xml.etree / defusedxml to avoid XXE-class parsers
# (CI-19 Wave 5 — Semgrep use-defused-xml-parse) without adding a runtime dep.
_CLASS_FILENAME_RE = re.compile(
    r"<class\b(?P<attrs>[^>]*)>",
    re.IGNORECASE,
)
_ATTR_FILENAME_RE = re.compile(r'\bfilename\s*=\s*"([^"]*)"', re.IGNORECASE)
_LINE_TAG_RE = re.compile(r"<line\b([^/]*)/>", re.IGNORECASE)
_ATTR_NUMBER_RE = re.compile(r'\bnumber\s*=\s*"(\d+)"', re.IGNORECASE)
_ATTR_HITS_RE = re.compile(r'\bhits\s*=\s*"(\d+)"', re.IGNORECASE)

# Must match the --cov= flags in .github/workflows/ci.yml's test-backend job
# exactly — anything outside these top-level dirs (tests/, scripts/,
# migrations/, docs, etc.) is intentionally not coverage-gated the same way
# a legitimate test file doesn't need "coverage" of itself.
IN_SCOPE_PREFIXES = ("app/", "domains/", "sdk/", "runtime/", "intelligence/")

HUNK_HEADER = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")


@dataclass
class FileDiffResult:
    path: str
    added_lines: set[int]
    covered: int = 0
    coverable: int = 0
    uninstrumented: set[int] = field(default_factory=set)


def _run_git(args: list[str]) -> str:
    # encoding must be explicit: this is an Arabic-first codebase (see
    # CANONICAL_ARCHITECTURE.md §1) — relying on subprocess's platform
    # default text encoding silently decodes as cp1252 on Windows and
    # crashes (UnicodeDecodeError) on the first Arabic string in any diff,
    # discovered by testing this script against real project history rather
    # than only a synthetic all-ASCII sample.
    result = subprocess.run(
        ["git", *args], capture_output=True, text=True, encoding="utf-8", errors="replace", check=False
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout


def _changed_python_files(base_ref: str) -> list[str]:
    # --relative: report paths relative to CWD (expected to be salesos/backend,
    # matching the "cd salesos/backend" step in .github/workflows/ci.yml),
    # not the repo root — coverage.xml's <source>/app</source> and every
    # <class filename="..."> entry are relative to that same directory, and
    # without --relative the two would never line up.
    out = _run_git(["diff", "--relative", "--name-only", "--diff-filter=ACM", f"{base_ref}...HEAD", "--", "*.py"])
    return [line.strip() for line in out.splitlines() if line.strip()]


def _added_line_numbers(base_ref: str, path: str) -> set[int]:
    """Line numbers, in the NEW version of `path`, that this diff added or changed."""
    diff = _run_git(["diff", "--relative", "-U0", f"{base_ref}...HEAD", "--", path])
    added: set[int] = set()
    current_new_line = None
    for line in diff.splitlines():
        header = HUNK_HEADER.match(line)
        if header:
            current_new_line = int(header.group(1))
            continue
        if current_new_line is None:
            continue
        if line.startswith("+") and not line.startswith("+++"):
            added.add(current_new_line)
            current_new_line += 1
        elif line.startswith("-") and not line.startswith("---"):
            continue  # deleted line — doesn't exist in the new file, doesn't advance the new-line counter
        else:
            current_new_line += 1
    return added


def _load_coverage(xml_path: Path) -> dict[str, dict[int, int]]:
    """Return {filename: {line_number: hits}} exactly as coverage.py's Cobertura XML reports it."""
    payload = xml_path.read_text(encoding="utf-8", errors="replace")
    by_file: dict[str, dict[int, int]] = {}
    parts = _CLASS_FILENAME_RE.split(payload)
    for i in range(1, len(parts), 2):
        attrs = parts[i]
        body = parts[i + 1] if i + 1 < len(parts) else ""
        fm = _ATTR_FILENAME_RE.search(attrs)
        if fm is None:
            continue
        filename = fm.group(1)
        lines: dict[int, int] = {}
        class_body = body.split("</class>", 1)[0]
        for line_attrs in _LINE_TAG_RE.findall(class_body):
            nm = _ATTR_NUMBER_RE.search(line_attrs)
            hm = _ATTR_HITS_RE.search(line_attrs)
            if nm is None or hm is None:
                continue
            lines[int(nm.group(1))] = int(hm.group(1))
        by_file[filename] = lines
    return by_file


def _is_test_file(path: str) -> bool:
    name = Path(path).name
    return "/tests/" in f"/{path}" or name.startswith("test_") or name.endswith("_test.py")


def analyze(base_ref: str, coverage_xml: Path) -> list[FileDiffResult]:
    coverage = _load_coverage(coverage_xml)
    results = []
    for path in _changed_python_files(base_ref):
        if not path.startswith(IN_SCOPE_PREFIXES):
            continue
        if _is_test_file(path):
            # Gate whether new *production* code is tested, not whether new
            # *test* code happens to execute itself during collection —
            # discovered mattering in practice: domains/*/tests/test_*.py
            # lives under the domains/ prefix and was otherwise counted.
            continue
        added = _added_line_numbers(base_ref, path)
        if not added:
            continue
        file_lines = coverage.get(path)
        result = FileDiffResult(path=path, added_lines=added)
        for ln in sorted(added):
            if file_lines is None or ln not in file_lines:
                # Not tracked by coverage.py at all (blank line, comment,
                # docstring-only line) — OR the whole file is absent from
                # the report, meaning it was never imported/exercised by
                # any test. The former is correctly excluded from the
                # denominator; the latter is deliberately NOT excluded
                # (fail-closed) rather than silently skipped — see below.
                if file_lines is None:
                    result.coverable += 1  # whole file untested: count against the gate, don't let it dodge silently
                else:
                    result.uninstrumented.add(ln)
                continue
            result.coverable += 1
            if file_lines[ln] > 0:
                result.covered += 1
        results.append(result)
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--coverage-xml", type=Path, default=Path("coverage.xml"))
    parser.add_argument("--base-ref", default="origin/main")
    parser.add_argument("--fail-under", type=float, default=80.0)
    args = parser.parse_args(argv)

    if not args.coverage_xml.exists():
        print(f"ERROR: {args.coverage_xml} not found — run pytest with --cov-report=xml first.", file=sys.stderr)
        return 2

    try:
        results = analyze(args.base_ref, args.coverage_xml)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    total_coverable = sum(r.coverable for r in results)
    total_covered = sum(r.covered for r in results)

    if total_coverable == 0:
        print("No in-scope changed lines to check (only tests/scripts/docs changed, or no diff). OK.")
        return 0

    pct = 100.0 * total_covered / total_coverable
    print(f"Diff coverage: {pct:.1f}% ({total_covered}/{total_coverable} new/changed lines), "
          f"threshold {args.fail_under:.1f}%\n")

    for r in results:
        if r.coverable == 0:
            continue
        file_pct = 100.0 * r.covered / r.coverable
        marker = "OK " if file_pct >= args.fail_under else "LOW"
        print(f"  [{marker}] {r.path}: {file_pct:.1f}% ({r.covered}/{r.coverable})")

    if pct < args.fail_under:
        print(f"\nFAIL: diff coverage {pct:.1f}% is below the {args.fail_under:.1f}% threshold.", file=sys.stderr)
        return 1

    print("\nOK: diff coverage meets threshold.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
