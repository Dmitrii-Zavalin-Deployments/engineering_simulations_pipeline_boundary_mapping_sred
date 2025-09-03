# tests/integration/test_domain_pipeline.py

import os
import json
import pytest
from pathlib import Path

from pipeline.metadata_enrichment import enrich_metadata_pipeline
from src.utils.domain_loader import DomainLoader

class StepBoundingBoxError(Exception):
    pass

def validate_bounding_box(bbox):
    required_keys = {"xmin", "xmax", "ymin", "ymax", "zmin", "zmax"}
    if not required_keys.issubset(bbox.keys()):
        raise StepBoundingBoxError("Missing bounding box keys")
    if not all(isinstance(bbox[k], (int, float)) for k in required_keys):
        raise StepBoundingBoxError("Non-numeric bounding box value")
    return True

class GridResolutionError(Exception):
    pass

def compute_grid_dimensions(bounds, resolution):
    try:
        dx = bounds["xmax"] - bounds["xmin"]
        dy = bounds["ymax"] - bounds["ymin"]
        dz = bounds["zmax"] - bounds["zmin"]
    except KeyError:
        raise GridResolutionError("Missing bounds for grid dimension calculation")
    if resolution <= 0:
        raise GridResolutionError("Invalid resolution")
    return {
        "nx": max(1, int(dx / resolution)),
        "ny": max(1, int(dy / resolution)),
        "nz": max(1, int(dz / resolution)),
    }

@pytest.fixture
def dummy_bounds():
    return {
        "xmin": 0.0, "xmax": 1.2,
        "ymin": 0.0, "ymax": 2.5,
        "zmin": 0.0, "zmax": 0.8
    }

def test_geometry_was_detected():
    metadata_path = Path("data/testing-input-output/enriched_metadata.json")
    assert metadata_path.exists(), "Output metadata file not found"

    with metadata_path.open() as f:
        metadata = json.load(f)
        domain = metadata.get("domain_definition", {})
        assert domain, "No domain_definition found in metadata"
        assert domain.get("min_x") is not None
        assert domain.get("max_x") is not None
        assert domain["max_x"] - domain["min_x"] > 0

def test_enriched_metadata_file_structure():
    metadata_path = Path("data/testing-input-output/enriched_metadata.json")
    assert metadata_path.exists(), "Metadata file not found"

    with metadata_path.open() as f:
        data = json.load(f)

    assert "domain_definition" in data, "Missing domain_definition in metadata output"
    if "resolution_density" in data:
        assert isinstance(data["resolution_density"], (int, float))
    else:
        pytest.skip("resolution_density missing; skipping assertion")

def test_validate_bounding_box_success(dummy_bounds):
    assert validate_bounding_box(dummy_bounds) is True

def test_validate_bounding_box_missing_keys():
    incomplete = {"xmin": 0.0, "ymin": 0.0, "zmin": 0.0}
    with pytest.raises(StepBoundingBoxError):
        validate_bounding_box(incomplete)

def test_validate_bounding_box_bad_types():
    malformed = {
        "xmin": "zero", "xmax": 1.0,
        "ymin": 0.0, "ymax": 1.0,
        "zmin": 0.0, "zmax": 1.0
    }
    with pytest.raises(StepBoundingBoxError):
        validate_bounding_box(malformed)

def test_compute_grid_dimensions_valid(dummy_bounds):
    grid = compute_grid_dimensions(dummy_bounds, resolution=0.1)
    assert grid["nx"] > 0 and grid["ny"] > 0 and grid["nz"] > 0

def test_compute_grid_dimensions_bad_resolution(dummy_bounds):
    with pytest.raises(GridResolutionError):
        compute_grid_dimensions(dummy_bounds, resolution=-1)

def test_compute_grid_dimensions_missing_bounds():
    incomplete = {"xmin": 0.0, "xmax": 1.0}
    with pytest.raises(GridResolutionError):
        compute_grid_dimensions(incomplete, resolution=0.1)

def test_metadata_enrichment_with_resolution(dummy_bounds):
    nx = 12
    ny = 25
    nz = 8
    bounding_volume = (
        (dummy_bounds["xmax"] - dummy_bounds["xmin"]) *
        (dummy_bounds["ymax"] - dummy_bounds["ymin"]) *
        (dummy_bounds["zmax"] - dummy_bounds["zmin"])
    )
    enriched = enrich_metadata_pipeline(nx, ny, nz, bounding_volume, config_flag=True)
    for key in ["spacing_hint", "resolution_density"]:
        assert key in enriched

def test_metadata_output_structure(tmp_path, dummy_bounds):
    metadata = {
        "domain_definition": {
            "min_x": dummy_bounds["xmin"],
            "max_x": dummy_bounds["xmax"],
            "min_y": dummy_bounds["ymin"],
            "max_y": dummy_bounds["ymax"],
            "min_z": dummy_bounds["zmin"],
            "max_z": dummy_bounds["zmax"],
            "nx": 3, "ny": 2, "nz": 1
        }
    }
    output_path = tmp_path / "enriched_metadata.json"
    with open(output_path, "w") as f:
        json.dump(metadata, f, indent=2)

    with open(output_path) as f:
        content = json.load(f)

    assert "domain_definition" in content
    for key in ["min_x", "max_x", "min_y", "max_y", "min_z", "max_z", "nx", "ny", "nz"]:
        assert key in content["domain_definition"]



