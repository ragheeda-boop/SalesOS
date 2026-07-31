"""Tests for scripts/check_diff_coverage.py (STORY-03-03, Sprint 02).

`git` calls are monkeypatched throughout (via `_run_git`) rather than
exercised against a real repository — the hunk-parsing regex and the
scope/test-file filtering are the actual logic worth locking down; git's
own diff correctness is not this project's concern to re-test.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.check_diff_coverage import (
    IN_SCOPE_PREFIXES,
    _is_test_file,
    _load_coverage,
    analyze,
)

# A real unified diff, exercising three hunk shapes: pure addition,
# in-place change, and a hunk near end-of-file — this is the exact text
# manually verified against during Sprint 02 development (see the Sprint 02
# report for the interactive session that produced it).
SAMPLE_DIFF = """diff --git a/foo.py b/foo.py
index abc..def 100644
--- a/foo.py
+++ b/foo.py
@@ -10,0 +11,3 @@ def existing():
+def new_func():
+    return 1
+
@@ -20,2 +23,2 @@ def other():
-    old_line_1
-    old_line_2
+    new_line_1
+    new_line_2
"""

SAMPLE_COVERAGE_XML = """<?xml version="1.0" ?>
<coverage version="7.0" lines-valid="10" lines-covered="7" line-rate="0.7">
  <packages>
    <package name="domains.example">
      <classes>
        <class name="foo.py" filename="domains/example/foo.py" line-rate="0.7">
          <methods/>
          <lines>
            <line number="11" hits="1"/>
            <line number="12" hits="0"/>
            <line number="23" hits="1"/>
            <line number="24" hits="1"/>
          </lines>
        </class>
      </classes>
    </package>
  </packages>
</coverage>
"""


class TestHunkParsing:
    """These exercise the exact loop in _added_line_numbers, without shelling
    out to git — patches _run_git to return SAMPLE_DIFF directly."""

    def test_added_lines_extracted_correctly(self):
        from scripts.check_diff_coverage import _added_line_numbers

        with patch("scripts.check_diff_coverage._run_git", return_value=SAMPLE_DIFF):
            added = _added_line_numbers("base", "foo.py")

        assert added == {11, 12, 13, 23, 24}

    def test_pure_deletion_hunk_contributes_no_added_lines(self):
        from scripts.check_diff_coverage import _added_line_numbers

        diff = (
            "diff --git a/foo.py b/foo.py\n"
            "--- a/foo.py\n"
            "+++ b/foo.py\n"
            "@@ -5,2 +5,0 @@ def existing():\n"
            "-    removed_1\n"
            "-    removed_2\n"
        )
        with patch("scripts.check_diff_coverage._run_git", return_value=diff):
            added = _added_line_numbers("base", "foo.py")

        assert added == set()


class TestCoverageXmlParsing:
    def test_load_coverage_maps_filename_to_line_hits(self, tmp_path: Path):
        xml_path = tmp_path / "coverage.xml"
        xml_path.write_text(SAMPLE_COVERAGE_XML)

        result = _load_coverage(xml_path)

        assert result["domains/example/foo.py"] == {11: 1, 12: 0, 23: 1, 24: 1}

    def test_load_coverage_handles_class_with_no_lines_element(self, tmp_path: Path):
        xml_path = tmp_path / "coverage.xml"
        xml_path.write_text(
            '<?xml version="1.0" ?><coverage><packages><package name="p">'
            '<classes><class name="empty.py" filename="domains/empty.py"/>'
            "</classes></package></packages></coverage>"
        )

        result = _load_coverage(xml_path)

        assert result["domains/empty.py"] == {}


class TestScopeFiltering:
    @pytest.mark.parametrize(
        "path,expected",
        [
            ("app/routers/foo.py", True),
            ("domains/decision_center/service.py", True),
            ("sdk/database.py", True),
            ("runtime/data_fabric_runtime/foo.py", True),
            ("intelligence/memory/store.py", True),
            ("scripts/generate_rls_policies.py", False),
            ("tests/unit/test_foo.py", False),
            ("docs/program/RISK_REGISTER.md", False),
        ],
    )
    def test_in_scope_prefixes(self, path: str, expected: bool):
        assert path.startswith(IN_SCOPE_PREFIXES) is expected

    @pytest.mark.parametrize(
        "path,expected",
        [
            ("domains/decision_center/tests/test_postgres_repo.py", True),
            ("domains/decision_center/postgres_repo.py", False),
            ("app/routers/meetings_test.py", True),
            ("tests/unit/test_check_diff_coverage.py", True),
            ("app/routers/meetings.py", False),
        ],
    )
    def test_is_test_file(self, path: str, expected: bool):
        assert _is_test_file(path) is expected


class TestAnalyzeEndToEnd:
    def test_analyze_computes_per_file_and_excludes_test_files(self, tmp_path: Path):
        xml_path = tmp_path / "coverage.xml"
        xml_path.write_text(SAMPLE_COVERAGE_XML)

        def fake_changed_files(base_ref):
            return ["domains/example/foo.py", "domains/example/tests/test_foo.py"]

        def fake_added_lines(base_ref, path):
            if path == "domains/example/foo.py":
                return {11, 12, 23, 24}
            return {1, 2, 3}  # test file — must not affect the result at all

        with (
            patch(
                "scripts.check_diff_coverage._changed_python_files", side_effect=fake_changed_files
            ),
            patch("scripts.check_diff_coverage._added_line_numbers", side_effect=fake_added_lines),
        ):
            results = analyze("base", xml_path)

        assert len(results) == 1
        assert results[0].path == "domains/example/foo.py"
        assert results[0].coverable == 4
        assert results[0].covered == 3  # line 12 has hits=0

    def test_analyze_treats_whole_missing_file_as_uncovered_not_skipped(self, tmp_path: Path):
        """A changed in-scope file entirely absent from coverage.xml (never
        imported/exercised by any test) must count against the gate — a file
        outside pytest's import graph must not be a free way to dodge it."""
        xml_path = tmp_path / "coverage.xml"
        xml_path.write_text(SAMPLE_COVERAGE_XML)

        with (
            patch(
                "scripts.check_diff_coverage._changed_python_files",
                return_value=["domains/example/never_imported.py"],
            ),
            patch(
                "scripts.check_diff_coverage._added_line_numbers",
                return_value={1, 2, 3, 4, 5},
            ),
        ):
            results = analyze("base", xml_path)

        assert results[0].coverable == 5
        assert results[0].covered == 0
