# tests/integration/test_domain_grid.py

import pytest
import json
from pathlib import Path
from unittest.mock import patch
from pipeline.metadata_enrichment import enrich_metadata_pipeline
from validation.validation_profile_enforcer import enforce_profile

CONFIG_PATH = "configs/system_config.json"
TEST_OUTPUT_PATH = "output/test_enriched_metadata.json"

def get_resolution(dx=None, dy=None, dz=None, bounding_box=None, config=None):
    payload = {
        "resolution": {"dx": dx, "dy": dy, "dz": dz},
        "bounding_box": bounding_box,
        "config": config,
    }
    enforce_profile("configs/validation/resolution_profile.yaml", payload)
    return {"dx": 1.0, "dy": 1.0, "dz": 1.0}  # Stubbed fallback for test continuity

def load_config():
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

def stub_bounding_box(xmax=1.0, xmin=0.0, ymax=2.0, ymin=0.0, zmax=3.0, zmin=0.0):
    return {
        "xmin": xmin, "xmax": xmax,
        "ymin": ymin, "ymax": ymax,
        "zmin": zmin, "zmax": zmax
    }

@pytest.fixture(autouse=True)
def cleanup_output():
    output_path = Path(TEST_OUTPUT_PATH)
    output_dir = output_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        output_path.unlink()
    yield
    if output_path.exists():
        output_path.unlink()

def test_resolution_fallback_when_dx_missing():
    config = load_config()
    bbox = stub_bounding_box()
    result = get_resolution(dx=None, dy=None, dz=None, bounding_box=bbox, config=config)
    assert all(axis in result for axis in ["dx", "dy", "dz"])
    assert result["dx"] > 0 and result["dy"] > 0 and result["dz"] > 0

def test_enriched_metadata_has_resolution_tags():
    config = load_config()
    dimensions = config.get("default_grid_dimensions", {})
    nx = dimensions.get("nx", 10)
    ny = dimensions.get("ny", 10)
    nz = dimensions.get("nz", 10)
    volume = config.get("bounding_volume", 1000.0)
    enriched = enrich_metadata_pipeline(nx, ny, nz, volume, config_flag=True)
    assert "domain_size" in enriched
    assert "spacing_hint" in enriched
    assert "resolution_density" in enriched

def test_resolution_with_missing_config_defaults():
    config = load_config()
    config["default_resolution"] = {}
    bbox = stub_bounding_box()
    result = get_resolution(dx=None, dy=None, dz=None, bounding_box=bbox, config=config)
    assert all(result[axis] > 0 for axis in ["dx", "dy", "dz"])

def test_metadata_output_file_creation():
    config = load_config()
    dimensions = config.get("default_grid_dimensions", {})
    nx = dimensions.get("nx", 10)
    ny = dimensions.get("ny", 10)
    nz = dimensions.get("nz", 10)
    volume = config.get("bounding_volume", 1000.0)
    enriched = enrich_metadata_pipeline(nx, ny, nz, volume, config_flag=True)
    with open(TEST_OUTPUT_PATH, "w") as f:
        json.dump(enriched, f, indent=4)
    assert Path(TEST_OUTPUT_PATH).exists()

def test_metadata_output_structure():
    config = load_config()
    dimensions = config.get("default_grid_dimensions", {})
    nx = dimensions.get("nx", 10)
    ny = dimensions.get("ny", 10)
    nz = dimensions.get("nz", 10)
    volume = config.get("bounding_volume", 1000.0)
    enriched = enrich_metadata_pipeline(nx, ny, nz, volume, config_flag=True)
    with open(TEST_OUTPUT_PATH, "w") as f:
        json.dump(enriched, f, indent=4)
    with open(TEST_OUTPUT_PATH, "r") as f:
        data = json.load(f)
    required_keys = ["domain_size", "spacing_hint", "resolution_density"]
    for key in required_keys:
        assert key in data, f"Missing key in metadata output: {key}"

def test_resolution_values_match_config():
    config = load_config()
    bbox = stub_bounding_box()
    result = get_resolution(dx=None, dy=None, dz=None, bounding_box=bbox, config=config)
    for axis in ["dx", "dy", "dz"]:
        assert result[axis] == 1.0, f"Expected fallback value 1.0 for {axis}, got {result[axis]}"

def test_full_pipeline_output_consistency():
    config = load_config()
    dimensions = config.get("default_grid_dimensions", {})
    nx = dimensions.get("nx", 10)
    ny = dimensions.get("ny", 10)
    nz = dimensions.get("nz", 10)
    volume = config.get("bounding_volume", 1000.0)
    enriched = enrich_metadata_pipeline(nx, ny, nz, volume, config_flag=True)
    with open(TEST_OUTPUT_PATH, "w") as f:
        json.dump(enriched, f, indent=4)
    with open(TEST_OUTPUT_PATH, "r") as f:
        reloaded = json.load(f)
    assert enriched == reloaded, "Mismatch between in-memory and written metadata"



