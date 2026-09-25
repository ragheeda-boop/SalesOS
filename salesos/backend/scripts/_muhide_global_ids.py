"""Stable Global IDs for MUHIDE restores into salesos_test.

Global company/person UUIDs and G-C/G-P slugs used to be ``uuid4()`` on every
ingest, so every restore of salesos_test silently re-keyed all 296,746
companies and orphaned every artifact keyed by Global ID (Phase 6 P3 evidence,
MA link proposals, review-queue state). This violates the Global-ID stability
invariant (report 91 §4.5).

Resolution order for a legacy key:
1. the pin file (original IDs recovered from the 2026-09-20 pre-repair dump);
2. otherwise a deterministic uuid5 + slug, so any new key is stable too.
"""

from __future__ import annotations

import csv
import gzip
import os
import uuid
from pathlib import Path

_NAMESPACE = uuid.UUID("6f3c1e9a-4b2d-5f8e-9a1c-7d2e4b6a8c01")
_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
_DEFAULT_PINS = (
    Path(__file__).resolve().parents[3]
    / "salesos_test_export"
    / "muhide_global_id_pins_20260920.csv.gz"
)


def _slug(prefix: str, value: uuid.UUID) -> str:
    x = value.int
    chars = []
    for _ in range(8):
        chars.append(_ALPHABET[x % 32])
        x //= 32
    return f"G-{prefix}-{''.join(chars)}"


class GlobalIdResolver:
    def __init__(self, pins_path: str | os.PathLike | None = None):
        path = Path(pins_path or os.environ.get("MUHIDE_GLOBAL_ID_PINS", _DEFAULT_PINS))
        self.pins: dict[tuple[str, str], tuple[uuid.UUID, str]] = {}
        self.pins_path = path if path.is_file() else None
        if self.pins_path:
            opener = gzip.open if path.suffix == ".gz" else open
            with opener(path, "rt", encoding="utf-8", newline="") as fh:
                for row in csv.DictReader(fh):
                    self.pins[(row["legacy_id_type"], row["legacy_id"])] = (
                        uuid.UUID(row["global_entity_id"]),
                        row["slug"],
                    )
        self.pinned_hits = 0
        self.derived_hits = 0

    def require_loaded(self) -> None:
        """Refuse to re-key a restore silently: no pins means every existing
        Global ID would change. Override only for a genuinely fresh dataset."""
        if not self.pins and os.environ.get("MUHIDE_ALLOW_UNPINNED") != "1":
            raise SystemExit(
                "ABORT: Global ID pin file not found; a restore without it would "
                "re-key every existing account. Set MUHIDE_GLOBAL_ID_PINS, or "
                "MUHIDE_ALLOW_UNPINNED=1 for a genuinely new dataset."
            )

    def resolve(self, legacy_id_type: str, legacy_id: str, prefix: str) -> tuple[uuid.UUID, str]:
        hit = self.pins.get((legacy_id_type, legacy_id))
        if hit:
            self.pinned_hits += 1
            return hit
        self.derived_hits += 1
        gid = uuid.uuid5(_NAMESPACE, f"{legacy_id_type}:{legacy_id}")
        return gid, _slug(prefix, gid)
