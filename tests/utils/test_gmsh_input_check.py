# tests/utils/test_gmsh_input_check.py

import pytest
import os
from unittest import mock
from src.utils import gmsh_input_check
from src.utils.gmsh_input_check import ValidationError, validate_step_has_volumes, log_surface_deviation


@pytest.fixture(autouse=True)
def gmsh_session():
    import gmsh
    gmsh.initialize()
    yield
    gmsh.finalize()


def test_validate_step_with_valid_mock_dict(monkeypatch):
    """Should pass when a valid dict with 'solids' is provided and file exists."""
    monkeypatch.setattr(os.path, "isfile", lambda path: True)
    monkeypatch.setattr("gmsh.open", lambda path: None)
    monkeypatch.setattr("gmsh.model.getEntities", lambda dim: [(3, 1)])

    step_dict = {"solids": ["mock_solid"]}
    validate_step_has_volumes(step_dict)  # Should not raise


def test_validate_step_with_missing_solids_key():
    """Should raise KeyError when 'solids' key is missing in dict."""
    with pytest.raises(KeyError, match="Missing or invalid 'solids' list"):
        validate_step_has_volumes({})


def test_validate_step_with_invalid_solids_type():
    """Should raise KeyError when 'solids' is not a list."""
    with pytest.raises(KeyError, match="Missing or invalid 'solids' list"):
        validate_step_has_volumes({"solids": "not_a_list"})


def test_validate_step_with_missing_file(monkeypatch):
    """Should raise FileNotFoundError when file path does not exist."""
    monkeypatch.setattr(os.path, "isfile", lambda path: False)
    with pytest.raises(FileNotFoundError):
        validate_step_has_volumes("nonexistent.step")


def test_validate_step_with_no_volumes(monkeypatch):
    """Should raise ValidationError when STEP file has no 3D volumes."""
    monkeypatch.setattr(os.path, "isfile", lambda path: True)
    monkeypatch.setattr("gmsh.open", lambda path: None)
    monkeypatch.setattr("gmsh.model.getEntities", lambda dim: [])

    with pytest.raises(ValidationError, match="contains no 3D volumes"):
        validate_step_has_volumes("valid_but_empty.step")


def test_log_surface_deviation_basic_output(capsys):
    """Should print diagnostic info for borderline match."""
    log_surface_deviation(surface_tag=42, deviation_ratio=0.85)
    captured = capsys.readouterr()
    assert "[DIAG] Surface 42: BORDERLINE MATCH (0.85 aligned)" in captured.out


def test_log_surface_deviation_with_coords(capsys):
    """Should print deviation stats when x_coords and anchor are provided."""
    log_surface_deviation(surface_tag=1, deviation_ratio=0.9, x_coords=[1.0, 1.1, 0.9], anchor=1.0)
    captured = capsys.readouterr()
    assert "Node deviation from anchor" in captured.out


def test_log_surface_deviation_debug_mode(capsys):
    """Should print full X-coord spread in debug mode."""
    log_surface_deviation(surface_tag=99, deviation_ratio=0.95, x_coords=[1.0, 1.2], anchor=1.0, debug=True)
    captured = capsys.readouterr()
    assert "[DEBUG_DIAG] Surface 99" in captured.out



