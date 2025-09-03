# /tests/integration/test_step_input_validation.py

import pytest
from pathlib import Path
from gmsh_runner import extract_bounding_box_with_gmsh

STEP_FILE_PATH = Path("test_models/test.step")

@pytest.mark.integration
def test_step_file_exists_and_is_valid_format():
    """Check that the STEP file exists and appears syntactically valid."""
    assert STEP_FILE_PATH.exists(), "Missing STEP file: test_models/test.step"
    assert STEP_FILE_PATH.suffix == ".step", "Incorrect file extension"

@pytest.mark.integration
def test_step_file_importable_by_gmsh():
    """Ensure Gmsh can import and initialize the test STEP file."""
    try:
        result = extract_bounding_box_with_gmsh(STEP_FILE_PATH, resolution=0.01)
    except Exception as e:
        pytest.fail(f"Gmsh failed to import STEP file: {e}")

    assert isinstance(result, dict), "Invalid Gmsh output structure"
    assert all(key in result for key in ["min_x", "max_x", "min_y", "max_y", "min_z", "max_z"]), \
        "Bounding box extraction keys missing"

@pytest.mark.integration
def test_step_file_resolution_scaling():
    """Verify extracted grid resolution varies with input scaling."""
    coarse = extract_bounding_box_with_gmsh(STEP_FILE_PATH, resolution=0.05)
    fine = extract_bounding_box_with_gmsh(STEP_FILE_PATH, resolution=0.005)

    assert fine["nx"] > coarse["nx"]
    assert fine["ny"] > coarse["ny"]
    assert fine["nz"] > coarse["nz"]

@pytest.mark.integration
def test_step_file_surface_tags_optional():
    """Confirm optional surface_tags can be present and valid."""
    result = extract_bounding_box_with_gmsh(STEP_FILE_PATH, resolution=0.01)
    if "surface_tags" in result:
        assert isinstance(result["surface_tags"], list), "surface_tags should be a list"



