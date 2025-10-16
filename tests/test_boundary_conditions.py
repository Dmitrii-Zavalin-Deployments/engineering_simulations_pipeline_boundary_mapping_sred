# tests/test_boundary_conditions.py

import pytest
import numpy as np
from unittest import mock
from src import boundary_conditions


@pytest.fixture(autouse=True)
def gmsh_session():
    import gmsh
    gmsh.initialize()
    yield
    gmsh.finalize()


def test_load_geometry_invokes_gmsh_open(monkeypatch):
    """Should initialize Gmsh and open the STEP file."""
    monkeypatch.setattr("gmsh.open", lambda path: None)
    monkeypatch.setattr("gmsh.model.add", lambda name: None)
    boundary_conditions.load_geometry("mock.step", debug=True)


def test_generate_mesh_sets_resolution(monkeypatch):
    """Should set mesh resolution when provided."""
    set_number_calls = []

    def mock_set_number(key, value):
        set_number_calls.append((key, value))

    monkeypatch.setattr("gmsh.option.setNumber", mock_set_number)
    monkeypatch.setattr("gmsh.model.mesh.generate", lambda dim: None)

    boundary_conditions.generate_mesh(resolution=0.5, debug=True)
    assert ("Mesh.CharacteristicLengthMin", 0.5) in set_number_calls
    assert ("Mesh.CharacteristicLengthMax", 0.5) in set_number_calls


def test_get_surface_faces_returns_entities(monkeypatch):
    """Should return surface entities from Gmsh."""
    monkeypatch.setattr("gmsh.model.getEntities", lambda dim: [(2, 101), (2, 102)])
    result = boundary_conditions.get_surface_faces(debug=True)
    assert result == [(2, 101), (2, 102)]


def test_get_x_bounds_handles_standard_bbox(monkeypatch):
    """Should extract x_min and x_max from bounding box."""
    monkeypatch.setattr("gmsh.model.getBoundingBox", lambda dim, tag: [0, 0.0, 0, 10, 1.0, 0])
    x_min, x_max = boundary_conditions.get_x_bounds(debug=True)
    assert x_min == 0.0
    assert x_max == 10.0

def test_generate_boundary_conditions_external_flow(monkeypatch):
    """Should generate wall, synthesized inlet, and outlet blocks for external flow."""
    surfaces = [(2, 301), (2, 302)]
    monkeypatch.setattr("gmsh.model.getEntities", lambda dim: surfaces)
    monkeypatch.setattr("gmsh.model.getBoundingBox", lambda dim, tag: [0.0, 0.0, 0.0, 10.0, 1.0, 1.0])
    monkeypatch.setattr("gmsh.model.mesh.getNodes", lambda dim, tag: (None, np.array([[5.0, 0.5, 0.5]]).flatten(), None))
    monkeypatch.setattr("gmsh.model.mesh.generate", lambda dim: None)
    monkeypatch.setattr("gmsh.open", lambda path: None)
    monkeypatch.setattr("gmsh.model.add", lambda name: None)

    blocks = boundary_conditions.generate_boundary_conditions(
        step_path="mock.step",
        velocity=[1.0, 0.0, 0.0],
        pressure=101325,
        no_slip=True,
        flow_region="external",
        resolution=0.5,
        debug=False
    )

    roles = [b["role"] for b in blocks]
    assert "wall" in roles
    assert "inlet" in roles
    assert "outlet" in roles
    assert sum("synthesized" in b["comment"].lower() for b in blocks if "comment" in b) >= 2



