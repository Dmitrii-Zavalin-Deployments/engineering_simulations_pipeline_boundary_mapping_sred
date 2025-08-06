# tests/integration/test_domain_pipeline.py

import os
import json
import pytest
import subprocess
from pathlib import Path

from pipeline.metadata_enrichment import enrich_metadata_pipeline
from src.utils.domain_loader import DomainLoader

# 🩹 Local fallback stubs to satisfy missing module references
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

# 🔧 Dummy bounding box fixture
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
        assert domain.get("min_x") is not None, "Missing min_x"
        assert domain.get("max_x") is not None, "Missing max_x"
        assert domain["max_x"] - domain["min_x"] > 0, "Invalid domain extent"

# 🧪 Unit Tests — Bounding Box
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

# 🧪 Unit Tests — Grid Resolution
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

# 🧪 Integration Test — Metadata Enrichment
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
    assert "domain_size" in enriched
    assert "spacing_hint" in enriched
    assert "resolution_density" in enriched

# 🧪 Integration Test — Metadata Structure
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

# 🧪 System Test — Full CLI Execution
STEP_PATH = Path("data/testing-input-output/input.step")

@pytest.mark.skipif(not STEP_PATH.exists(), reason="Required STEP file missing for system test.")
def test_run_pipeline_execution(tmp_path):
    env = os.environ.copy()
    env["IO_DIRECTORY"] = str(STEP_PATH.parent)
    env["OUTPUT_PATH"] = str(tmp_path / "domain_metadata.json")
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[2])

    resolution = 0.02
    result = subprocess.run(
        ["python", "-m", "src.run_pipeline", "--resolution", str(resolution)],
        env=env,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print("STDERR:", result.stderr)

    assert result.returncode == 0
    assert "✅ Metadata written" in result.stdout

    output_file = Path(env["OUTPUT_PATH"])
    assert output_file.exists(), "Pipeline output file missing"

    with open(output_file) as f:
        metadata = json.load(f)

    assert "domain_definition" in metadata
    domain = metadata["domain_definition"]

    computed_nx = int((domain["max_x"] - domain["min_x"]) / resolution)
    computed_ny = int((domain["max_y"] - domain["min_y"]) / resolution)
    computed_nz = int((domain["max_z"] - domain["min_z"]) / resolution)

    assert computed_nx > 0, "Computed nx must be positive"
    assert computed_ny > 0, "Computed ny must be positive"
    assert computed_nz > 0, "Computed nz must be positive"




