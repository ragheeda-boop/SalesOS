"""Generate a deterministic dependency manifest for CI evidence.

This does not claim a vulnerability scan; it produces the input artifact that
the approved scanner can consume and makes missing lockfiles explicit.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


def build_manifest(root: Path) -> dict[str, object]:
    candidates = [root / "poetry.lock", root / "requirements.txt", root / "package-lock.json"]
    files: list[dict[str, str]] = []
    for path in candidates:
        if path.is_file():
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            files.append({"file": path.name, "sha256": digest})
    if not files:
        raise FileNotFoundError("no dependency lockfile found")
    return {"format": "salesos-dependency-manifest-v1", "files": files}


if __name__ == "__main__":
    repo = Path(__file__).resolve().parents[1]
    print(json.dumps(build_manifest(repo), indent=2))
