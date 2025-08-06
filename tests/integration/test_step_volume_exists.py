# tests/integration/test_step_volume_exists.py

import os
import pytest

import gmsh

STEP_PATH = "data/testing-input-output/input.step"


@pytest.fixture(scope="module", autouse=True)
def init_gmsh():
    """Initialize and finalize Gmsh session for integration test."""
    gmsh.initialize()
    yield
    gmsh.finalize()


def test_step_file_exists():
    """Verify that the input STEP file is present on disk."""
    assert os.path.isfile(STEP_PATH), f"Missing STEP file at expected location: {STEP_PATH}"


def test_step_contains_volume():
    """Check that the STEP file includes at least one volume entity."""
    gmsh.model.add("test_model")
    gmsh.open(STEP_PATH)

    volumes = gmsh.model.getEntities(dim=3)
    assert volumes, f"No volumes found in STEP file: {STEP_PATH}"

    # Optional detail check (tag & type)
    for dim, tag in volumes:
        assert dim == 3
        assert isinstance(tag, int)



