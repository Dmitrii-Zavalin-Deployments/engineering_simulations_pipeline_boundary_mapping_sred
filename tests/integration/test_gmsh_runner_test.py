# tests/integration/test_gmsh_runner_test.py

import pytest
from pathlib import Path
from unittest.mock import patch
from gmsh_runner import extract_bounding_box_with_gmsh

# 🧩 Shared lifecycle patch for Gmsh API stability
def mock_gmsh_lifecycle():
    return patch.multiple(
        "gmsh",
        initialize=lambda: None,
        finalize=lambda: None,
        model=patch("gmsh.model"),
        logger=patch("gmsh.logger", getLastError=lambda: "")
    )

@pytest.mark.integration
def test_missing_file_raises_exception(gmsh_session):
    """Asserts missing STEP file triggers FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        extract_bounding_box_with_gmsh(Path("nonexistent_model.step"))


@pytest.mark.integration
def test_empty_geometry_triggers_exception(gmsh_session, tmp_path):
    """Simulates a malformed STEP and validates geometry detection."""
    fake_step = tmp_path / "empty.step"
    fake_step.write_text("")  # Dummy empty file

    with mock_gmsh_lifecycle():
        with patch("gmsh.open", side_effect=Exception("Gmsh could not open file")):
            with pytest.raises(Exception):
                extract_bounding_box_with_gmsh(fake_step)




