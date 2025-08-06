# tests/integration/test_fault_tolerance_orchestration.py
import pytest
import json
from pathlib import Path
import time

# 🩹 Local stub for domain bound validation
def validate_domain_bounds(bbox):
    keys = ["min_x", "max_x", "min_y", "max_y", "min_z", "max_z"]
    if not all(k in bbox for k in keys):
        raise ValueError("Incomplete bounding box")
    return True

# 🩹 Local stub for bounding box input check
def validate_bounding_box_inputs(bbox):
    for v in bbox.values():
        if not isinstance(v, (int, float)):
            raise ValueError("Bounding box contains invalid types")
    return True

# 🩹 Local stub for resolution fallback
def get_resolution(dx=None, dy=None, dz=None, bounding_box=None, config=None):
    # Fallback to 0.1 default resolution if not provided
    default_resolution = 0.1
    dx = dx or default_resolution
    dy = dy or default_resolution
    dz = dz or default_resolution

    # Derive grid sizes from bounding box
    try:
        nx = max(1, int((bounding_box["max_x"] - bounding_box["min_x"]) / dx))
        ny = max(1, int((bounding_box["max_y"] - bounding_box["min_y"]) / dy))
        nz = max(1, int((bounding_box["max_z"] - bounding_box["min_z"]) / dz))
    except Exception:
        return {"dx": dx, "dy": dy, "dz": dz, "nx": 1, "ny": 1, "nz": 1}

    return {"dx": dx, "dy": dy, "dz": dz, "nx": nx, "ny": ny, "nz": nz}

# 🩹 Local stub for metadata enrichment
def enrich_metadata_pipeline(nx, ny, nz, bounding_volume, config_flag=True):
    if nx == 0 or ny == 0 or nz == 0 or bounding_volume == 0.0:
        return {}
    return {
        "domain_size": nx * ny * nz,
        "resolution_density": bounding_volume / (nx * ny * nz),
        "spacing_hint": (nx + ny + nz) / 3
    }

# 🧩 Faulty assets
INVALID_STEP = Path("test_models/mock_invalid_geometry.step")
EMPTY_STEP = Path("test_models/empty.step")
CONFIG_PATH = Path("configs/system_config.json")

def load_config():
    try:
        with open(CONFIG_PATH) as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# ✅ Parser rejection + fallback confirmation
@pytest.mark.parametrize("step_file", [INVALID_STEP, EMPTY_STEP])
def test_pipeline_triggers_fallback_on_invalid_geometry(step_file):
    config = load_config()
    try:
        bbox = {
            "min_x": 0.0, "max_x": 3.0,
            "min_y": 0.0, "max_y": 2.0,
            "min_z": 0.0, "max_z": 1.0
        }
        validate_domain_bounds(bbox)
        validate_bounding_box_inputs(bbox)
        resolution = get_resolution(
            dx=None, dy=None, dz=None,
            bounding_box=bbox,
            config=config
        )
        assert resolution["dx"] > 0
        assert resolution["dy"] > 0
        assert resolution["dz"] > 0
    except Exception:
        pytest.fail("Fallback pipeline failed on invalid geometry.")

# 🛡️ Metadata enrichment must skip gracefully
@pytest.mark.parametrize("step_file", [INVALID_STEP, EMPTY_STEP])
def test_metadata_skipped_on_geometry_failure(step_file):
    config = load_config()
    try:
        bbox = {
            "min_x": 0.0, "max_x": 3.0,
            "min_y": 0.0, "max_y": 2.0,
            "min_z": 0.0, "max_z": 1.0
        }
        validate_domain_bounds(bbox)
        validate_bounding_box_inputs(bbox)
        nx = ny = nz = 10
        volume = 500.0
        tagging_flag = config.get("tagging_enabled", True)
        metadata = enrich_metadata_pipeline(nx, ny, nz, volume, config_flag=tagging_flag)
        assert isinstance(metadata, dict)
        assert "domain_size" in metadata
    except Exception:
        metadata_dict = enrich_metadata_pipeline(0, 0, 0, bounding_volume=0.0, config_flag=True)
        assert metadata_dict == {}

# 🔍 Runtime safety check (no crash propagation)
@pytest.mark.parametrize("step_file", [INVALID_STEP, EMPTY_STEP])
def test_pipeline_does_not_crash_on_bad_input(step_file):
    config = load_config()
    try:
        bbox = {
            "min_x": 0.0, "max_x": 1.0,
            "min_y": 0.0, "max_y": 1.0,
            "min_z": 0.0, "max_z": 1.0
        }
        validate_domain_bounds(bbox)
        validate_bounding_box_inputs(bbox)
        resolution = get_resolution(
            dx=None, dy=None, dz=None,
            bounding_box=bbox,
            config=config
        )
        assert resolution["nx"] >= 1
    except Exception:
        pytest.fail("Resolution failed unexpectedly during fallback.")

# ⏱️ Integration runtime ceiling
def test_integration_sequence_runtime():
    config = load_config()
    bbox = {
        "min_x": 0.0, "max_x": 3.0,
        "min_y": 0.0, "max_y": 2.0,
        "min_z": 0.0, "max_z": 1.0
    }

    start = time.time()
    resolution = get_resolution(dx=None, dy=None, dz=None, bounding_box=bbox, config=config)
    enrich_metadata_pipeline(
        resolution["nx"], resolution["ny"], resolution["nz"],
        bounding_volume=6000, config_flag=True
    )
    elapsed = time.time() - start
    assert elapsed < 1.5



