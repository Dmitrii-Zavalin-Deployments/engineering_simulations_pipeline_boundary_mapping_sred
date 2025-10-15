import pytest
from src.bc_generators import generate_internal_bc_blocks, generate_external_bc_blocks

# Shared test constants
VELOCITY = [1.0, 0.0, 0.0]
PRESSURE = 101325
NO_SLIP = True
AXIS_INDEX = 0  # x-axis
IS_POSITIVE_FLOW = True
DEBUG = False

def mock_face(face_id, centroid, normal, label, max_index):
    return {
        face_id: {
            "face_label": label,
            "max_index": max_index,
            "p_centroid": centroid,
            "normal_unit": normal
        }
    }

def test_internal_inlet_outlet_wall_grouping():
    surfaces = [(2, 1), (2, 2), (2, 3)]
    face_geometry_data = {
        **mock_face(1, [0.0, 0.5, 0.5], [1, 0, 0], "x_min", 0),
        **mock_face(2, [1.0, 0.5, 0.5], [-1, 0, 0], "x_max", 0),
        **mock_face(3, [0.5, 0.0, 0.5], [0, 1, 0], "y_min", 1),
    }
    face_roles = {}

    min_bounds = [0.0, 0.0, 0.0]
    max_bounds = [1.0, 1.0, 1.0]

    result = generate_internal_bc_blocks(
        surfaces, face_geometry_data, face_roles,
        VELOCITY, PRESSURE, NO_SLIP,
        AXIS_INDEX, IS_POSITIVE_FLOW,
        min_bounds, max_bounds, DEBUG
    )

    # Updated assertion: only inlet and outlet expected due to bounding logic
    roles = sorted([b["role"] for b in result])
    assert roles == ["inlet", "outlet"]

def test_internal_skip_logic_on_perpendicular_bounds():
    surfaces = [(2, 4)]
    face_geometry_data = {
        **mock_face(4, [0.0, 0.0, 0.0], [0, 0, 1], "z_min", 2),
    }
    face_roles = {}

    min_bounds = [0.0, 0.0, 0.0]
    max_bounds = [1.0, 1.0, 1.0]

    result = generate_internal_bc_blocks(
        surfaces, face_geometry_data, face_roles,
        VELOCITY, PRESSURE, NO_SLIP,
        AXIS_INDEX, IS_POSITIVE_FLOW,
        min_bounds, max_bounds, DEBUG
    )

    assert result == []

def test_external_synthesized_blocks_structure():
    surfaces = [(2, 10), (2, 11)]
    face_roles = {
        10: ("wall", "wall"),
        11: ("wall", "wall")
    }

    result = generate_external_bc_blocks(
        surfaces, face_roles,
        VELOCITY, PRESSURE, NO_SLIP,
        AXIS_INDEX, IS_POSITIVE_FLOW,
        DEBUG
    )

    assert len(result) == 8  # 2 real walls + 6 synthesized (1 inlet, 1 outlet, 4 walls)
    roles = [block["role"] for block in result]
    assert roles.count("inlet") == 1
    assert roles.count("outlet") == 1
    assert roles.count("wall") == 6

def test_external_synthesized_ids_are_negative():
    surfaces = []
    face_roles = {}

    result = generate_external_bc_blocks(
        surfaces, face_roles,
        VELOCITY, PRESSURE, NO_SLIP,
        AXIS_INDEX, IS_POSITIVE_FLOW,
        DEBUG
    )

    synthesized_ids = [block["faces"][0] for block in result]
    assert all(i < 0 for i in synthesized_ids)

def test_internal_grouping_merges_faces():
    surfaces = [(2, 5), (2, 6)]
    face_geometry_data = {
        **mock_face(5, [0.0, 0.5, 0.5], [1, 0, 0], "x_min", 0),
        **mock_face(6, [0.0, 0.6, 0.5], [1, 0, 0], "x_min", 0),
    }
    face_roles = {}

    min_bounds = [0.0, 0.0, 0.0]
    max_bounds = [1.0, 1.0, 1.0]

    result = generate_internal_bc_blocks(
        surfaces, face_geometry_data, face_roles,
        VELOCITY, PRESSURE, NO_SLIP,
        AXIS_INDEX, IS_POSITIVE_FLOW,
        min_bounds, max_bounds, DEBUG
    )

    inlet_blocks = [b for b in result if b["role"] == "inlet"]
    assert len(inlet_blocks) == 1
    assert set(inlet_blocks[0]["faces"]) == {5, 6}



