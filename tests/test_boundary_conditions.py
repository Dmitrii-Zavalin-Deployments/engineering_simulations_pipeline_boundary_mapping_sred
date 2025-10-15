# tests/test_boundary_conditions.py

import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from src.boundary_conditions import generate_boundary_conditions

# Shared test constants
VELOCITY = [1.0, 0.0, 0.0]
PRESSURE = 101325
NO_SLIP = True
AXIS_INDEX = 0
IS_POSITIVE_FLOW = True
DEBUG = False

@patch("src.boundary_conditions.gmsh")
def test_zero_velocity_raises_error(mock_gmsh):
    with pytest.raises(ValueError, match="Initial velocity vector cannot be zero."):
        generate_boundary_conditions(
            "dummy.step", [0.0, 0.0, 0.0], PRESSURE, NO_SLIP, "internal"
        )

@patch("src.boundary_conditions.gmsh")
def test_internal_flow_triggers_internal_generator(mock_gmsh):
    mock_gmsh.model.getEntities.return_value = [(2, 1)]
    mock_gmsh.model.mesh.getNodes.return_value = (
        [1, 2, 3],
        np.array([0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0]),
        []
    )
    mock_gmsh.model.getBoundingBox.return_value = [0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0]

    result = generate_boundary_conditions(
        "dummy.step", VELOCITY, PRESSURE, NO_SLIP, "internal", resolution=0.5
    )
    assert isinstance(result, list)
    assert all("role" in block for block in result)

@patch("src.boundary_conditions.gmsh")
def test_external_flow_triggers_external_generator(mock_gmsh):
    mock_gmsh.model.getEntities.return_value = [(2, 1)]
    mock_gmsh.model.mesh.getNodes.return_value = (
        [1, 2, 3],
        np.array([0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0]),
        []
    )
    mock_gmsh.model.getBoundingBox.return_value = [0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0]

    result = generate_boundary_conditions(
        "dummy.step", VELOCITY, PRESSURE, NO_SLIP, "external", resolution=0.5, padding_factor=2
    )
    assert isinstance(result, list)
    assert any(block["role"] == "inlet" for block in result)
    assert any(block["role"] == "outlet" for block in result)

@patch("src.boundary_conditions.gmsh")
def test_missing_nodes_skipped_safely(mock_gmsh):
    mock_gmsh.model.getEntities.return_value = [(2, 1)]
    mock_gmsh.model.mesh.getNodes.return_value = (
        [1],
        np.array([0.0, 0.0, 0.0]),  # insufficient for normal calculation
        []
    )
    mock_gmsh.model.getBoundingBox.return_value = [0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0]

    result = generate_boundary_conditions(
        "dummy.step", VELOCITY, PRESSURE, NO_SLIP, "internal"
    )
    assert result == []

@patch("src.boundary_conditions.gmsh")
def test_invalid_normal_skipped(mock_gmsh):
    mock_gmsh.model.getEntities.return_value = [(2, 1)]
    mock_gmsh.model.mesh.getNodes.return_value = (
        [1, 2, 3],
        np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),  # zero-length vectors
        []
    )
    mock_gmsh.model.getBoundingBox.return_value = [0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0]

    result = generate_boundary_conditions(
        "dummy.step", VELOCITY, PRESSURE, NO_SLIP, "internal"
    )
    assert result == []

@patch("src.boundary_conditions.gmsh")
def test_bounding_box_fallback(mock_gmsh):
    mock_gmsh.model.getEntities.return_value = []
    mock_gmsh.model.getBoundingBox.return_value = [0.0, 0.0, 0.0, 1.0, 1.0, 1.0]  # 6 values

    result = generate_boundary_conditions(
        "dummy.step", VELOCITY, PRESSURE, NO_SLIP, "external"
    )
    assert isinstance(result, list)

@patch("src.boundary_conditions.gmsh")
def test_debug_output_triggers_prints(mock_gmsh, capsys):
    mock_gmsh.model.getEntities.return_value = [(2, 1)]
    mock_gmsh.model.mesh.getNodes.return_value = (
        [1, 2, 3],
        np.array([0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0]),
        []
    )
    mock_gmsh.model.getBoundingBox.return_value = [0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0]

    generate_boundary_conditions(
        "dummy.step", VELOCITY, PRESSURE, NO_SLIP, "internal", debug=True
    )
    captured = capsys.readouterr()
    assert "[DEBUG]" in captured.out



