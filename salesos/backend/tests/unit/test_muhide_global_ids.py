"""GlobalIdResolver: pinned original IDs win; unpinned keys are deterministic."""

from __future__ import annotations

import csv
import gzip
import sys
import uuid
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from _muhide_global_ids import GlobalIdResolver  # noqa: E402

PINNED = "ef465b4f-8b32-4df2-9207-c638d30dcd6b"


@pytest.fixture
def pins(tmp_path):
    p = tmp_path / "pins.csv.gz"
    with gzip.open(p, "wt", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["legacy_id_type", "legacy_id", "kind", "global_entity_id", "slug"])
        w.writerow(["LEGACY_MUHIDE_MA_ID", "MA-0000001", "C", PINNED, "G-C-ABCDEFGH"])
    return p


def test_pinned_key_returns_original_id_and_slug(pins):
    r = GlobalIdResolver(pins)
    assert r.resolve("LEGACY_MUHIDE_MA_ID", "MA-0000001", "C") == (uuid.UUID(PINNED), "G-C-ABCDEFGH")
    assert (r.pinned_hits, r.derived_hits) == (1, 0)


def test_unpinned_key_is_deterministic_across_instances(pins):
    a = GlobalIdResolver(pins).resolve("LEGACY_MUHIDE_MA_ID", "MA-NEW", "C")
    b = GlobalIdResolver(pins).resolve("LEGACY_MUHIDE_MA_ID", "MA-NEW", "C")
    assert a == b
    assert a[0] != uuid.UUID(PINNED)
    assert a[1].startswith("G-C-") and len(a[1]) == 12


def test_same_legacy_id_under_different_type_does_not_collide(pins):
    r = GlobalIdResolver(pins)
    assert r.resolve("LEGACY_MUHIDE_CONTACT_ID", "X", "P")[0] != r.resolve("LEGACY_MUHIDE_MA_ID", "X", "C")[0]


def test_missing_pin_file_aborts_unless_overridden(tmp_path, monkeypatch):
    r = GlobalIdResolver(tmp_path / "missing.csv.gz")
    monkeypatch.delenv("MUHIDE_ALLOW_UNPINNED", raising=False)
    with pytest.raises(SystemExit):
        r.require_loaded()
    monkeypatch.setenv("MUHIDE_ALLOW_UNPINNED", "1")
    r.require_loaded()
