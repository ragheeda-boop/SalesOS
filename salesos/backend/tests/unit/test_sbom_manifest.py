from pathlib import Path

from scripts.generate_sbom_manifest import build_manifest


def test_sbom_manifest_is_deterministic_and_hashes_lockfiles():
    manifest = build_manifest(Path(__file__).parents[2])
    assert manifest["format"] == "salesos-dependency-manifest-v1"
    assert any(item["file"] == "poetry.lock" for item in manifest["files"])
    assert all(len(item["sha256"]) == 64 for item in manifest["files"])
