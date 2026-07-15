"""Tests for Knowledge Packs — validates manifest, prompts, signals, features, and scoring schemas."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

PACKS_DIR = Path(__file__).resolve().parent.parent
PACK_NAMES = ["healthcare", "construction", "financial-services"]

REQUIRED_DIRS = ["prompts", "signals", "features", "scoring"]
REQUIRED_FILES_TEMPLATE = [
    "manifest.json",
    "prompts/company-summary.json",
    "prompts/opportunity-scoring.json",
    "prompts/signal-detection.json",
    "signals/signal-definitions.json",
    "features/feature-definitions.json",
    "scoring/scoring-weights.json",
]


@pytest.fixture(params=PACK_NAMES)
def pack_path(request) -> Path:
    return PACKS_DIR / request.param


@pytest.fixture
def manifest(pack_path: Path) -> dict:
    with open(pack_path / "manifest.json", encoding="utf-8") as f:
        return json.load(f)


# ─── Manifest validation ────────────────────────────────────────────────


class TestManifest:
    def test_manifest_exists(self, pack_path: Path):
        assert (pack_path / "manifest.json").exists(), f"Missing manifest.json in {pack_path.name}"

    def test_manifest_required_fields(self, manifest: dict):
        required = ["id", "name", "version", "description", "domain", "sector", "ar_name", "tags", "dependencies"]
        for field in required:
            assert field in manifest, f"Missing required field '{field}' in manifest"

    def test_manifest_id_format(self, manifest: dict):
        assert manifest["id"].startswith("kp-"), f"Pack ID must start with 'kp-': {manifest['id']}"

    def test_manifest_version_format(self, manifest: dict):
        parts = manifest["version"].split(".")
        assert len(parts) == 3, f"Version must be semver (X.Y.Z): {manifest['version']}"
        for p in parts:
            assert p.isdigit(), f"Version parts must be numeric: {manifest['version']}"

    def test_manifest_dependencies_format(self, manifest: dict):
        deps = manifest.get("dependencies", {})
        assert "knowledge_packs" in deps, "dependencies must include 'knowledge_packs'"
        assert "ai_assets" in deps, "dependencies must include 'ai_assets'"
        assert "version" in deps, "dependencies must include 'version'"

    def test_manifest_regulatory_bodies(self, manifest: dict):
        assert "regulatory_bodies" in manifest
        assert len(manifest["regulatory_bodies"]) > 0, "Must have at least one regulatory body"

    def test_manifest_timestamps(self, manifest: dict):
        assert "created_at" in manifest
        assert "updated_at" in manifest


# ─── Prompt validation ──────────────────────────────────────────────────


class TestPrompts:
    def test_all_prompts_exist(self, pack_path: Path):
        prompt_dir = pack_path / "prompts"
        assert prompt_dir.exists()
        expected = ["company-summary.json", "opportunity-scoring.json", "signal-detection.json"]
        for fname in expected:
            assert (prompt_dir / fname).exists(), f"Missing prompt: {prompt_dir.name}/{fname}"

    def test_prompt_has_required_fields(self, pack_path: Path):
        for f in (pack_path / "prompts").iterdir():
            if f.suffix != ".json":
                continue
            with open(f, encoding="utf-8") as fh:
                prompt = json.load(fh)
            required = ["prompt_id", "name", "version", "domain", "template", "variables", "output_schema"]
            for field in required:
                assert field in prompt, f"Missing '{field}' in {f.relative_to(PACKS_DIR)}"

    def test_prompt_id_format(self, pack_path: Path):
        for f in (pack_path / "prompts").iterdir():
            if f.suffix != ".json":
                continue
            with open(f, encoding="utf-8") as fh:
                prompt = json.load(fh)
            assert prompt["prompt_id"].startswith(
                f"kp-{pack_path.name}"
            ), f"Prompt ID must start with 'kp-{pack_path.name}': {prompt['prompt_id']}"

    def test_prompt_domain_match(self, pack_path: Path):
        for f in (pack_path / "prompts").iterdir():
            if f.suffix != ".json":
                continue
            with open(f, encoding="utf-8") as fh:
                prompt = json.load(fh)
            assert prompt["domain"] == pack_path.name, f"Domain mismatch in {f.name}"

    def test_prompt_has_output_schema(self, pack_path: Path):
        for f in (pack_path / "prompts").iterdir():
            if f.suffix != ".json":
                continue
            with open(f, encoding="utf-8") as fh:
                prompt = json.load(fh)
            schema = prompt.get("output_schema", {})
            assert "type" in schema, f"output_schema must have 'type' in {f.name}"
            assert "properties" in schema, f"output_schema must have 'properties' in {f.name}"

    def test_prompt_variables_in_template(self, pack_path: Path):
        for f in (pack_path / "prompts").iterdir():
            if f.suffix != ".json":
                continue
            with open(f, encoding="utf-8") as fh:
                prompt = json.load(fh)
            for var in prompt.get("variables", []):
                placeholder = "{" + var + "}"
                assert placeholder in prompt["template"], (
                    f"Variable '{var}' not found in template for {f.name}"
                )


# ─── Signal definitions validation ──────────────────────────────────────


class TestSignals:
    def test_signal_definitions_exist(self, pack_path: Path):
        signals_file = pack_path / "signals" / "signal-definitions.json"
        assert signals_file.exists(), f"Missing signal-definitions.json in {pack_path.name}"

    def test_signal_required_fields(self, pack_path: Path):
        with open(pack_path / "signals" / "signal-definitions.json", encoding="utf-8") as f:
            data = json.load(f)
        assert "signals" in data, "Missing 'signals' array in signal-definitions.json"
        assert len(data["signals"]) > 0, "Must have at least one signal definition"
        required = ["id", "name", "ar_name", "type", "category", "description", "source", "priority", "weight", "decay_days"]
        for signal in data["signals"]:
            for field in required:
                assert field in signal, f"Missing '{field}' in signal {signal.get('id', '?')}"

    def test_signal_id_format(self, pack_path: Path):
        with open(pack_path / "signals" / "signal-definitions.json", encoding="utf-8") as f:
            data = json.load(f)
        prefix_map = {"healthcare": "SIG-HC", "construction": "SIG-CN", "financial-services": "SIG-FS"}
        expected_prefix = prefix_map[pack_path.name]
        for signal in data["signals"]:
            assert signal["id"].startswith(expected_prefix), (
                f"Signal ID must start with '{expected_prefix}': {signal['id']}"
            )

    def test_signal_weight_range(self, pack_path: Path):
        with open(pack_path / "signals" / "signal-definitions.json", encoding="utf-8") as f:
            data = json.load(f)
        for signal in data["signals"]:
            assert 0 <= signal["weight"] <= 1, f"Weight must be 0-1: {signal['id']}"

    def test_signal_unique_ids(self, pack_path: Path):
        with open(pack_path / "signals" / "signal-definitions.json", encoding="utf-8") as f:
            data = json.load(f)
        ids = [s["id"] for s in data["signals"]]
        assert len(ids) == len(set(ids)), f"Duplicate signal IDs in {pack_path.name}"


# ─── Feature definitions validation ─────────────────────────────────────


class TestFeatures:
    def test_feature_definitions_exist(self, pack_path: Path):
        features_file = pack_path / "features" / "feature-definitions.json"
        assert features_file.exists(), f"Missing feature-definitions.json in {pack_path.name}"

    def test_feature_required_fields(self, pack_path: Path):
        with open(pack_path / "features" / "feature-definitions.json", encoding="utf-8") as f:
            data = json.load(f)
        assert "features" in data, "Missing 'features' array in feature-definitions.json"
        assert len(data["features"]) > 0, "Must have at least one feature definition"
        required = ["id", "name", "ar_name", "type", "description", "source", "importance"]
        for feature in data["features"]:
            for field in required:
                assert field in feature, f"Missing '{field}' in feature {feature.get('id', '?')}"

    def test_feature_id_format(self, pack_path: Path):
        with open(pack_path / "features" / "feature-definitions.json", encoding="utf-8") as f:
            data = json.load(f)
        prefix_map = {"healthcare": "FEAT-HC", "construction": "FEAT-CN", "financial-services": "FEAT-FS"}
        expected_prefix = prefix_map[pack_path.name]
        for feature in data["features"]:
            assert feature["id"].startswith(expected_prefix), (
                f"Feature ID must start with '{expected_prefix}': {feature['id']}"
            )

    def test_feature_importance_range(self, pack_path: Path):
        with open(pack_path / "features" / "feature-definitions.json", encoding="utf-8") as f:
            data = json.load(f)
        for feature in data["features"]:
            assert 0 <= feature["importance"] <= 1, f"Importance must be 0-1: {feature['id']}"

    def test_feature_unique_ids(self, pack_path: Path):
        with open(pack_path / "features" / "feature-definitions.json", encoding="utf-8") as f:
            data = json.load(f)
        ids = [s["id"] for s in data["features"]]
        assert len(ids) == len(set(ids)), f"Duplicate feature IDs in {pack_path.name}"


# ─── Scoring weights validation ─────────────────────────────────────────


class TestScoring:
    def test_scoring_weights_exist(self, pack_path: Path):
        scoring_file = pack_path / "scoring" / "scoring-weights.json"
        assert scoring_file.exists(), f"Missing scoring-weights.json in {pack_path.name}"

    def test_scoring_required_fields(self, pack_path: Path):
        with open(pack_path / "scoring" / "scoring-weights.json", encoding="utf-8") as f:
            data = json.load(f)
        assert "scoring_model" in data, "Missing 'scoring_model' in scoring-weights.json"
        model = data["scoring_model"]
        required = ["name", "ar_name", "description", "dimensions", "thresholds", "confidence_rules"]
        for field in required:
            assert field in model, f"Missing '{field}' in scoring_model"

    def test_scoring_dimensions_have_sub_factors(self, pack_path: Path):
        with open(pack_path / "scoring" / "scoring-weights.json", encoding="utf-8") as f:
            data = json.load(f)
        dimensions = data["scoring_model"]["dimensions"]
        assert len(dimensions) > 0, "Must have at least one dimension"
        for dim_name, dim in dimensions.items():
            assert "sub_factors" in dim, f"Dimension '{dim_name}' missing 'sub_factors'"
            assert len(dim["sub_factors"]) > 0, f"Dimension '{dim_name}' has no sub_factors"

    def test_scoring_dimension_weights_sum(self, pack_path: Path):
        with open(pack_path / "scoring" / "scoring-weights.json", encoding="utf-8") as f:
            data = json.load(f)
        dimensions = data["scoring_model"]["dimensions"]
        total_weight = sum(d.get("weight", 0) for d in dimensions.values())
        assert abs(total_weight - 1.0) < 0.01, (
            f"Dimension weights must sum to 1.0, got {total_weight}"
        )

    def test_scoring_thresholds(self, pack_path: Path):
        with open(pack_path / "scoring" / "scoring-weights.json", encoding="utf-8") as f:
            data = json.load(f)
        thresholds = data["scoring_model"]["thresholds"]
        required_thresholds = ["hot", "warm", "cold", "min_confidence"]
        for t in required_thresholds:
            assert t in thresholds, f"Missing threshold '{t}'"

    def test_scoring_confidence_rules(self, pack_path: Path):
        with open(pack_path / "scoring" / "scoring-weights.json", encoding="utf-8") as f:
            data = json.load(f)
        rules = data["scoring_model"]["confidence_rules"]
        for level in ["high", "medium", "low"]:
            assert level in rules, f"Missing confidence rule for '{level}'"
            assert "min_signals" in rules[level]


# ─── Structural validation ──────────────────────────────────────────────


class TestStructure:
    def test_all_required_directories_exist(self, pack_path: Path):
        for d in REQUIRED_DIRS:
            assert (pack_path / d).is_dir(), f"Missing directory: {pack_path.name}/{d}"

    def test_no_extra_directories(self, pack_path: Path):
        allowed = set(REQUIRED_DIRS)
        for item in pack_path.iterdir():
            if item.is_dir():
                assert item.name in allowed, f"Unexpected directory: {pack_path.name}/{item.name}"

    def test_no_stray_files(self, pack_path: Path):
        allowed_files = {f.replace("/", "\\") for f in REQUIRED_FILES_TEMPLATE}
        for item in pack_path.rglob("*"):
            if item.is_file():
                rel = str(item.relative_to(pack_path))
                # Allow __init__.py in subdirs
                if "__init__" in rel or "conftest" in rel:
                    continue
                assert rel in allowed_files or rel.startswith("tests"), (
                    f"Unexpected file: {pack_path.name}/{rel}"
                )


# ─── Cross-pack consistency ─────────────────────────────────────────────


class TestCrossPackConsistency:
    def test_all_packs_have_same_structure(self):
        structures = {}
        for name in PACK_NAMES:
            paths = set()
            for p in (PACKS_DIR / name).rglob("*"):
                if p.is_file() and "__init__" not in p.name and "conftest" not in p.name:
                    paths.add(str(p.relative_to(PACKS_DIR / name)))
            structures[name] = paths
        ref = structures[PACK_NAMES[0]]
        for name, paths in structures.items():
            assert paths == ref, (
                f"Pack '{name}' has different structure than '{PACK_NAMES[0]}'"
            )

    def test_all_manifest_ids_unique(self):
        ids = []
        for name in PACK_NAMES:
            with open(PACKS_DIR / name / "manifest.json", encoding="utf-8") as f:
                ids.append(json.load(f)["id"])
        assert len(ids) == len(set(ids)), "Duplicate pack IDs across packs"

    def test_all_prompts_match_domain(self):
        for name in PACK_NAMES:
            for f in (PACKS_DIR / name / "prompts").iterdir():
                if f.suffix != ".json":
                    continue
                with open(f, encoding="utf-8") as fh:
                    prompt = json.load(fh)
                assert prompt["domain"] == name, (
                    f"Prompt domain '{prompt['domain']}' doesn't match pack name '{name}' in {f.name}"
                )
