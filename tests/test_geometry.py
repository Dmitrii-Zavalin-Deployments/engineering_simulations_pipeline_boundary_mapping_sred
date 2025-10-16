# tests/test_geometry.py

import pytest
import numpy as np
from src import geometry


def test_build_face_metadata_with_valid_coords():
    """Should compute centroid and return metadata dictionary."""
    coords = np.array([[0.0, 0.0, 0.0], [1.0, 1.0, 1.0]])
    result = geometry.build_face_metadata(face_id=101, coords=coords, label="wall")
    assert result["face_label"] == "wall"
    assert result["p_centroid"] == [0.5, 0.5, 0.5]
    assert result["normal_unit"] == [0, 0, 0]
    assert result["max_index"] == 0


def test_build_face_metadata_with_empty_coords():
    """Should return None centroid when coords are empty."""
    coords = np.array([]).reshape(0, 3)
    result = geometry.build_face_metadata(face_id=102, coords=coords, label="wall")
    assert result["p_centroid"] == [None, None, None]


@pytest.mark.parametrize("centroid,x_min,x_max,expected", [
    ([0.0, 0.5, 0.5], 0.0, 10.0, ("inlet", "x_min")),
    ([10.0, 0.5, 0.5], 0.0, 10.0, ("outlet", "x_max")),
    ([5.0, 0.5, 0.5], 0.0, 10.0, ("wall", "wall"))
])
def test_classify_face_by_centroid_roles(centroid, x_min, x_max, expected):
    """Should classify face role based on X-position."""
    role, label = geometry.classify_face_by_centroid(centroid, x_min, x_max, threshold=0.9)
    assert (role, label) == expected

def test_assign_roles_skips_faces_with_insufficient_nodes(monkeypatch):
    """Should skip faces with fewer than 3 nodes."""
    surfaces = [(2, 301)]
    monkeypatch.setattr("gmsh.model.getBoundingBox", lambda dim, tag: [0.0, 0.0, 0.0, 10.0, 1.0, 1.0])
    monkeypatch.setattr("gmsh.model.mesh.getNodes", lambda dim, tag: (None, np.array([[1.0, 1.0, 1.0]]).flatten(), None))

    face_roles, face_geometry_data = geometry.assign_roles_to_faces(
        surfaces, x_min=0.0, x_max=10.0, threshold=0.9, tolerance=1e-6, debug=False
    )

    assert face_roles == {}
    assert face_geometry_data == {}



