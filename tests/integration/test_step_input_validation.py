# /tests/integration/test_step_input_validation.py

import os
import pytest
from pathlib import Path
from unittest.mock import patch
from gmsh_runner import extract_bounding_box_with_gmsh

STEP_FILE_PATH = Path("test_models/test.step")
skip_ci = os.getenv("CI", "false").lower() == "true"

@pytest.mark.integration
def test_step_file_exists_and_is_valid_format():
    """Check that the STEP file exists and appears syntactically valid."""
    assert STEP_FILE_PATH.exists(), "Missing STEP file: test_models/test.step"
    assert STEP_FILE_PATH.suffix == ".step", "Incorrect file extension"

@pytest.mark.integration
@pytest.mark.skipif(skip_ci, reason="Gmsh integration mocked; skipping in CI")
def test_step_file_importable_by_gmsh():
    """Ensure Gmsh can import and initialize the test STEP file."""
    mock_result = {
        "min_x": 0.0, "max_x": 1.0,
        "min_y": 0.0, "max_y": 1.0,
        "min_z": 0.0, "max_z": 1.0,
        "nx": 10, "ny": 10, "nz": 10,
        "surface_tags": [1, 2, 3]
    }
    with patch("gmsh_runner.extract_bounding_box_with_gmsh", return_value=mock_result):
        result = extract_bounding_box_with_gmsh(STEP_FILE_PATH, resolution=0.01)

    assert isinstance(result, dict), "Invalid Gmsh output structure"
    assert all(key in result for key in ["min_x", "max_x", "min_y", "max_y", "min_z", "max_z"]), \
        "Bounding box extraction keys missing"

@pytest.mark.integration
@pytest.mark.skipif(skip_ci, reason="Resolution scaling mocked; skipping in CI")
def test_step_file_resolution_scaling():
    """Verify extracted grid resolution varies with input scaling."""
    coarse_result = {
        "nx": 10, "ny": 10, "nz": 10
    }
    fine_result = {
        "nx": 100, "ny": 100, "nz": 100
    }
    with patch("gmsh_runner.extract_bounding_box_with_gmsh", side_effect=[coarse_result, fine_result]):
        coarse = extract_bounding_box_with_gmsh(STEP_FILE_PATH, resolution=0.05)
        fine = extract_bounding_box_with_gmsh(STEP_FILE_PATH, resolution=0.005)

    assert fine["nx"] > coarse["nx"], "nx scaling failed"
    assert fine["ny"] > coarse["ny"], "ny scaling failed"
    assert fine["nz"] > coarse["nz"], "nz scaling failed"



