# src/bc_generators.py

def generate_internal_bc_blocks(
    surfaces, face_geometry_data, face_roles,
    velocity, pressure, no_slip,
    axis_index, is_positive_flow,
    min_bounds, max_bounds,
    debug=False
):
    """
    Generates boundary condition blocks for internal flow.

    Args:
        surfaces (list): List of surface entities (dim, tag).
        face_geometry_data (dict): Metadata for each face.
        face_roles (dict): Role and label for each face.
        velocity (list): Initial velocity vector.
        pressure (float): Initial pressure value.
        no_slip (bool): Whether to apply no-slip condition.
        axis_index (int): Dominant flow axis index (0=x, 1=y, 2=z).
        is_positive_flow (bool): Direction of flow along axis.
        min_bounds (list): Minimum bounding box coordinates.
        max_bounds (list): Maximum bounding box coordinates.
        debug (bool): If True, prints debug info.

    Returns:
        list: Boundary condition blocks.
    """
    blocks = []

    for dim, face_id in surfaces:
        role, label = face_roles.get(face_id, ("wall", "wall"))
        metadata = face_geometry_data.get(face_id, {})

        block = {
            "id": face_id,
            "type": role,
            "label": label,
            "velocity": velocity if role == "inlet" else [0, 0, 0],
            "pressure": pressure if role == "outlet" else None,
            "no_slip": no_slip if role == "wall" else None,
            "geometry": metadata
        }

        if debug:
            print(f"[DEBUG] Internal BC block for face {face_id}: {block}")

        blocks.append(block)

    return blocks


def generate_external_bc_blocks(
    surfaces, face_roles,
    velocity, pressure, no_slip,
    axis_index, is_positive_flow,
    debug=False
):
    """
    Generates boundary condition blocks for external flow.

    Args:
        surfaces (list): List of surface entities (dim, tag).
        face_roles (dict): Role and label for each face.
        velocity (list): Initial velocity vector.
        pressure (float): Initial pressure value.
        no_slip (bool): Whether to apply no-slip condition.
        axis_index (int): Dominant flow axis index (0=x, 1=y, 2=z).
        is_positive_flow (bool): Direction of flow along axis.
        debug (bool): If True, prints debug info.

    Returns:
        list: Boundary condition blocks.
    """
    blocks = []

    for dim, face_id in surfaces:
        role, label = face_roles.get(face_id, ("wall", "wall"))

        block = {
            "id": face_id,
            "type": role,
            "label": label,
            "velocity": [0, 0, 0],
            "pressure": None,
            "no_slip": no_slip if role == "wall" else None,
            "geometry": {
                "normal_unit": [0, 0, 0],
                "face_label": label,
                "max_index": 0,
                "p_centroid": [None, None, None]
            }
        }

        if debug:
            print(f"[DEBUG] External BC block for face {face_id}: {block}")

        blocks.append(block)

    return blocks



