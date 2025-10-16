# tests/unit/test_bc_generators.py

import pytest
from src import bc_generators


def test_generate_internal_bc_blocks_classifies_all_roles():
    """Should classify inlet, outlet, and wall faces correctly based on centroid X-position."""
    surfaces = [(2, 101), (2, 102), (2, 103)]
    face_geometry_data = {
        101: {"p_centroid": [0.0, 0.5, 0.5]},  # inlet
        102: {"p_centroid": [10.0, 0.5, 0.5]}, # outlet
        103: {"p_centroid": [5.0, 0.5, 0.5]}   # wall
    }
    face_roles = {}  # unused in this function
    velocity = [1.0, 0.0, 0.0]
    pressure = 101325
    no_slip = True
    axis_index = 0
    is_positive_flow = True
    min_bounds = [0.0, 0.0, 0.0]
    max_bounds = [10.0, 1.0, 1.0]

    blocks = bc_generators.generate_internal_bc_blocks(
        surfaces, face_geometry_data, face_roles,
        velocity, pressure, no_slip,
        axis_index, is_positive_flow,
        min_bounds, max_bounds,
        threshold=0.9,
        debug=False
    )

    roles = {b["role"] for b in blocks}
    assert "inlet" in roles
    assert "outlet" in roles
    assert "wall" in roles
    assert sum(len(b["faces"]) for b in blocks) == 3


def test_generate_internal_bc_blocks_missing_centroid_defaults_to_wall():
    """Should classify face with missing centroid as wall."""
    surfaces = [(2, 201)]
    face_geometry_data = {
        201: {"p_centroid": [None, None, None]}
    }
    blocks = bc_generators.generate_internal_bc_blocks(
        surfaces, face_geometry_data, {},
        [1.0, 0.0, 0.0], 101325, True,
        0, True,
        [0.0, 0.0, 0.0], [10.0, 1.0, 1.0],
        debug=False
    )
    assert len(blocks) == 1
    assert blocks[0]["role"] == "wall"
    assert 201 in blocks[0]["faces"]


def test_generate_internal_bc_blocks_skips_bounding_plane_faces():
    """Should skip wall faces that lie exactly on bounding box planes."""
    surfaces = [(2, 301)]
    face_geometry_data = {
        301: {"p_centroid": [0.0, 0.0, 0.0]}  # on bounding box min
    }
    blocks = bc_generators.generate_internal_bc_blocks(
        surfaces, face_geometry_data, {},
        [1.0, 0.0, 0.0], 101325, True,
        0, True,
        [0.0, 0.0, 0.0], [10.0, 1.0, 1.0],
        debug=False
    )
    assert blocks == []


def test_generate_external_bc_blocks_applies_wall_to_all_faces():
    """Should apply wall condition to all faces in external flow."""
    surfaces = [(2, 401), (2, 402)]
    face_roles = {}  # unused
    blocks = bc_generators.generate_external_bc_blocks(
        surfaces, face_roles,
        [1.0, 0.0, 0.0], 101325, True,
        0, True,
        debug=False
    )
    assert len(blocks) == 1
    assert blocks[0]["role"] == "wall"
    assert set(blocks[0]["faces"]) == {401, 402}
    assert blocks[0]["no_slip"] is True
    assert blocks[0]["velocity"] == [0.0, 0.0, 0.0]


def test_generate_external_bc_blocks_empty_surface_list():
    """Should return empty list when no surfaces are provided."""
    blocks = bc_generators.generate_external_bc_blocks(
        [], {}, [1.0, 0.0, 0.0], 101325, True,
        0, True,
        debug=False
    )
    assert blocks == []



