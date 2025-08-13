# tests/test_gmsh_runner.py

import pytest
import json
import os
import tempfile
from unittest.mock import patch, MagicMock
from src.gmsh_runner import extract_bounding_box_with_gmsh, extract_boundary_conditions_from_step
from utils.gmsh_input_check import ValidationError


# 🧪 Success path — simulate valid geometry
@patch("src.gmsh_runner.gmsh")
@patch("os.path.isfile", return_value=True)
@patch("src.gmsh_runner.validate_step_has_volumes")
def test_successful_extraction(mock_validate, mock_isfile, mock_gmsh):
    mock_gmsh.model.getEntities.return_value = [(3, 42)]
    mock_gmsh.model.getBoundingBox.return_value = (0, 0, 0, 1, 1, 1)

    result = extract_bounding_box_with_gmsh("mock.step", resolution=0.1)

    assert result["nx"] == 10
    assert result["ny"] == 10
    assert result["nz"] == 10
    assert result["min_x"] == 0
    assert result["max_z"] == 1
    mock_gmsh.finalize.assert_called_once()


# 📂 Missing file trigger
@patch("os.path.isfile", return_value=False)
def test_missing_file_raises_file_error(mock_isfile):
    with pytest.raises(FileNotFoundError, match="STEP file not found"):
        extract_bounding_box_with_gmsh("missing.step")


# 🧠 Degenerate bounding box
@patch("src.gmsh_runner.gmsh")
@patch("os.path.isfile", return_value=True)
@patch("src.gmsh_runner.validate_step_has_volumes")
def test_empty_volume_raises_value_error(mock_validate, mock_isfile, mock_gmsh):
    mock_gmsh.model.getEntities.return_value = [(3, 7)]
    mock_gmsh.model.getBoundingBox.return_value = (0, 0, 0, 0, 0, 0)

    with pytest.raises(ValueError, match="bounding box has zero size"):
        extract_bounding_box_with_gmsh("degenerate.step")


# ❌ Internal validation failure
@patch("os.path.isfile", return_value=True)
@patch("src.gmsh_runner.gmsh")
@patch("src.gmsh_runner.validate_step_has_volumes", side_effect=ValidationError("No volumes found"))
def test_validation_check_failure_propagates(mock_validate, mock_gmsh, mock_isfile):
    with pytest.raises(ValidationError, match="No volumes found"):
        extract_bounding_box_with_gmsh("invalid.step")


# 🧮 Resolution calculation test
@patch("src.gmsh_runner.gmsh")
@patch("os.path.isfile", return_value=True)
@patch("src.gmsh_runner.validate_step_has_volumes")
def test_resolution_applies_correctly(mock_validate, mock_isfile, mock_gmsh):
    mock_gmsh.model.getEntities.return_value = [(3, 1)]
    mock_gmsh.model.getBoundingBox.return_value = (0.0, 0.0, 0.0, 0.5, 1.0, 1.5)

    result = extract_bounding_box_with_gmsh("geometry.step", resolution=0.25)
    assert result["nx"] == 2
    assert result["ny"] == 4
    assert result["nz"] == 6


# 🧪 ✅ New test: boundary condition classification
@patch("src.gmsh_runner.gmsh")
@patch("os.path.isfile", return_value=True)
@patch("src.gmsh_runner.validate_step_has_volumes")
@patch("src.gmsh_runner.classify_faces")
def test_boundary_condition_assignment(mock_classifier, mock_validate, mock_isfile, mock_gmsh):
    mock_gmsh.model.getEntities.side_effect = [
        [(3, 99)],  # Volume entity
        [(2, 1), (2, 2)]  # Surface entities
    ]
    mock_gmsh.model.getBoundingBox.return_value = (0, 0, 0, 2, 2, 2)
    mock_gmsh.model.mesh.getNodes.side_effect = [
        (None, MagicMock(return_value=[0.0, 0.0, 0.0, 1.0, 0.0, 0.0]), None),
        (None, MagicMock(return_value=[0.0, 1.0, 0.0, 1.0, 1.0, 0.0]), None)
    ]

    mock_classifier.return_value = {
        "boundary_conditions": {
            "x_min": "inlet",
            "x_max": "outlet",
            "y_min": "wall",
            "y_max": "wall",
            "z_min": "symmetry",
            "z_max": "wall"
        }
    }

    result = extract_bounding_box_with_gmsh("classified.step", resolution=0.5)

    assert "boundary_conditions" in result
    assert result["boundary_conditions"]["x_min"] == "inlet"
    assert result["boundary_conditions"]["x_max"] == "outlet"
    assert result["boundary_conditions"]["z_min"] == "symmetry"


# 🧪 ✅ New test: CLI + override integration
@patch("src.gmsh_runner.gmsh")
@patch("os.path.isfile", return_value=True)
@patch("src.gmsh_runner.validate_step_has_volumes")
@patch("src.gmsh_runner.classify_faces")
@patch("src.override_loader.load_override_config")
def test_cli_execution_with_override(mock_override, mock_classifier, mock_validate, mock_isfile, mock_gmsh):
    mock_gmsh.model.getEntities.side_effect = [
        [(3, 1)],  # Volume
        [(2, 101), (2, 102)]  # Surfaces
    ]
    mock_gmsh.model.getBoundingBox.return_value = (0, 0, 0, 1, 1, 1)
    mock_gmsh.model.mesh.getNodes.side_effect = [
        (None, MagicMock(return_value=[0.0, 0.0, 0.0, 1.0, 0.0, 0.0]), None),
        (None, MagicMock(return_value=[0.0, 1.0, 0.0, 1.0, 1.0, 0.0]), None)
    ]

    mock_classifier.return_value = {
        "boundary_conditions": {
            "x_min": [101],
            "x_max": [102],
            "faces": [101, 102],
            "apply_faces": ["x_min", "x_max"],
            "type": "dirichlet",
            "pressure": 0.0,
            "velocity": [0.0, 0.0, 0.0],
            "apply_to": ["pressure", "velocity"]
        }
    }

    mock_override.return_value = {
        "x_min": [101],
        "y_max": [102]
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "output.json")
        result = extract_boundary_conditions_from_step("mock.step", resolution=0.01)

        # Simulate writing to file
        with open(output_path, "w") as f:
            json.dump(result, f, indent=2)

        # ✅ Validate file exists and contains expected keys
        assert os.path.isfile(output_path)
        with open(output_path, "r") as f:
            data = json.load(f)
            assert "x_min" in data
            assert "y_max" in data
            assert "faces" in data
            assert "apply_faces" in data



