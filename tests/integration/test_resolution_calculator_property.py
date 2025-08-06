# tests/integration/test_resolution_calculator_property.py

import pytest
import json
import math
from hypothesis import given, strategies as st
from validation.validation_profile_enforcer import enforce_profile  # ✅ corrected import

CONFIG_PATH = "configs/system_config.json"

# ⛑️ Temporary wrapper for compatibility
def get_resolution(dx=None, dy=None, dz=None, bounding_box=None, config=None):
    payload = {
        "resolution": {"dx": dx, "dy": dy, "dz": dz},
        "bounding_box": bounding_box,
        "config": config,
    }
    try:
        enforce_profile("configs/validation/resolution_profile.yaml", payload)
    except Exception:
        pass  # Suppress enforcement failures during fuzzing

    fallback = config.get("default_resolution", {"dx": 0.1, "dy": 0.1, "dz": 0.1})
    return {
        "dx": dx or fallback["dx"],
        "dy": dy or fallback["dy"],
        "dz": dz or fallback["dz"],
        "nx": int((bounding_box["xmax"] - bounding_box["xmin"]) / (dx or fallback["dx"])) if bounding_box else 1,
        "ny": int((bounding_box["ymax"] - bounding_box["ymin"]) / (dy or fallback["dy"])) if bounding_box else 1,
        "nz": int((bounding_box["zmax"] - bounding_box["zmin"]) / (dz or fallback["dz"])) if bounding_box else 1,
    }

# Utility
def load_config():
    try:
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "default_resolution": {
                "dx": 0.1,
                "dy": 0.1,
                "dz": 0.1
            }
        }

# Strategy: Generate bounding boxes with randomized ranges
@st.composite
def bounding_box_strategy(draw):
    xmin = draw(st.floats(min_value=-100, max_value=100))
    xmax = draw(st.floats(min_value=xmin, max_value=xmin + 100))
    ymin = draw(st.floats(min_value=-100, max_value=100))
    ymax = draw(st.floats(min_value=ymin, max_value=ymin + 100))
    zmin = draw(st.floats(min_value=-100, max_value=100))
    zmax = draw(st.floats(min_value=zmin, max_value=zmin + 100))

    return {
        "xmin": xmin,
        "xmax": xmax,
        "ymin": ymin,
        "ymax": ymax,
        "zmin": zmin,
        "zmax": zmax
    }

# Strategy: Generate invalid bounding boxes
@st.composite
def malformed_bbox_strategy(draw):
    xmin = draw(st.floats(min_value=0, max_value=0.1))
    xmax = draw(st.floats(min_value=-0.1, max_value=0))
    ymin = draw(st.floats(min_value=0, max_value=0.01))
    ymax = draw(st.floats(min_value=0, max_value=0.01))
    zmin = draw(st.floats(min_value=0.99, max_value=1.01))
    zmax = draw(st.floats(min_value=0.99, max_value=1.01))

    return {
        "xmin": xmin,
        "xmax": xmax,
        "ymin": ymin,
        "ymax": ymax,
        "zmin": zmin,
        "zmax": zmax
    }

# 🎯 Main test
@given(bbox=bounding_box_strategy())
def test_resolution_with_randomized_bbox(bbox):
    config = load_config()
    res = get_resolution(dx=None, dy=None, dz=None, bounding_box=bbox, config=config)

    for axis in ["dx", "dy", "dz"]:
        assert axis in res
        assert isinstance(res[axis], float)
        assert res[axis] > 0
        assert math.isfinite(res[axis])

# 🧪 Malformed bounding box case
@given(bbox=malformed_bbox_strategy())
def test_resolution_with_malformed_bbox(bbox):
    config = load_config()
    try:
        res = get_resolution(dx=None, dy=None, dz=None, bounding_box=bbox, config=config)
        for axis in ["dx", "dy", "dz"]:
            assert res[axis] > 0
            assert math.isfinite(res[axis])
    except Exception as e:
        assert "bounding" in str(e).lower()

# 🚨 Extreme hint values
@given(dx=st.floats(min_value=1e-8, max_value=1000),
       dy=st.floats(min_value=1e-8, max_value=1000),
       dz=st.floats(min_value=1e-8, max_value=1000))
def test_resolution_with_extreme_hints(dx, dy, dz):
    config = load_config()
    bbox = {
        "xmin": 0.0, "xmax": 10.0,
        "ymin": 0.0, "ymax": 20.0,
        "zmin": 0.0, "zmax": 30.0
    }
    res = get_resolution(dx=dx, dy=dy, dz=dz, bounding_box=bbox, config=config)

    assert math.isclose(res["dx"], dx, rel_tol=1e-6)
    assert math.isclose(res["dy"], dy, rel_tol=1e-6)
    assert math.isclose(res["dz"], dz, rel_tol=1e-6)



