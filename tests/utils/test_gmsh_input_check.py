# tests/utils/test_gmsh_input_check.py

import pytest
import os
from unittest.mock import patch, MagicMock
from src.utils.gmsh_input_check import (
    validate_step_has_volumes,
    ValidationError
)


# ---------- Core File Path Scenarios ----------

def test_valid_file_with_volumes(tmp_path):
    """✅ Valid .step file path and Gmsh returns volume entities."""
    step_path = tmp_path / "geometry.step"
    step_path.write_text("dummy content")

    with patch("os.path.isfile", return_value=True), \
         patch("gmsh.model.getEntities", return_value=[(3, 1)]), \
         patch("gmsh.model.add"), \
         patch("gmsh.open"):
        validate_step_has_volumes(str(step_path))  # Should pass without exception


def test_valid_file_without_volumes(tmp_path):
    """🚫 Valid .step file path but no volume entities present."""
    step_path = tmp_path / "geometry.step"
    step_path.write_text("dummy content")

    with patch("os.path.isfile", return_value=True), \
         patch("gmsh.model.getEntities", return_value=[]), \
         patch("gmsh.model.add"), \
         patch("gmsh.open"):
        with pytest.raises(ValidationError):
            validate_step_has_volumes(str(step_path))


def test_nonexistent_file_path():
    """🚫 Invalid file path triggers FileNotFoundError."""
    with patch("os.path.isfile", return_value=False):
        with pytest.raises(FileNotFoundError):
            validate_step_has_volumes("fake/path/to/missing.step")


# ---------- Dictionary Payload Scenarios ----------

def test_dict_payload_valid_solids():
    """✅ Valid STEP dict payload with 'solids' list passes."""
    payload = {"solids": ["mock_solid_entity"]}
    with patch("os.path.isfile", return_value=True), \
         patch("gmsh.model.getEntities", return_value=[(3, 1)]), \
         patch("gmsh.model.add"), \
         patch("gmsh.open"):
        validate_step_has_volumes(payload)  # Should pass


def test_dict_payload_missing_solids_key():
    """🚫 Dict payload missing 'solids' key triggers KeyError."""
    payload = {"foo": ["something"]}
    with pytest.raises(KeyError):
        validate_step_has_volumes(payload)


def test_dict_payload_invalid_solids_type():
    """🚫 Dict payload with non-list 'solids' triggers KeyError."""
    payload = {"solids": "not_a_list"}
    with pytest.raises(KeyError):
        validate_step_has_volumes(payload)


def test_dict_payload_empty_solids_list():
    """🚫 Dict payload with empty 'solids' should trigger ValidationError."""
    payload = {"solids": []}
    with patch("os.path.isfile", return_value=True), \
         patch("gmsh.model.getEntities", return_value=[]), \
         patch("gmsh.model.add"), \
         patch("gmsh.open"):
        with pytest.raises(ValidationError):
            validate_step_has_volumes(payload)


def test_dict_payload_valid_path_but_no_volumes():
    """🚫 Dict payload with valid path override but Gmsh returns no volumes."""
    payload = {"solids": ["dummy"]}
    with patch("os.path.isfile", return_value=True), \
         patch("gmsh.model.getEntities", return_value=[]), \
         patch("gmsh.model.add"), \
         patch("gmsh.open"):
        with pytest.raises(ValidationError):
            validate_step_has_volumes(payload)



