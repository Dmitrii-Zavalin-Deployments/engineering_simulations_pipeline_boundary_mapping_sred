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
    inlet_faces = []
    outlet_faces = []
    wall_faces = []
    inlet_labels = []
    outlet_labels = []

    for dim, face_id in surfaces:
        role, label = face_roles.get(face_id, ("wall", "wall"))
        if role == "inlet":
            inlet_faces.append(face_id)
            inlet_labels.append(label)
        elif role == "outlet":
            outlet_faces.append(face_id)
            outlet_labels.append(label)
        else:
            wall_faces.append(face_id)

    blocks = []

    if inlet_faces:
        blocks.append({
            "role": "inlet",
            "type": "dirichlet",
            "faces": inlet_faces,
            "apply_to": ["velocity", "pressure"],
            "comment": "Defines inlet flow parameters for velocity and pressure",
            "velocity": velocity,
            "pressure": pressure,
            "apply_faces": sorted(set(inlet_labels))
        })

    if outlet_faces:
        blocks.append({
            "role": "outlet",
            "type": "neumann",
            "faces": outlet_faces,
            "apply_to": ["pressure"],
            "comment": "Defines outlet flow behavior with pressure gradient",
            "apply_faces": sorted(set(outlet_labels))
        })

    if wall_faces:
        blocks.append({
            "role": "wall",
            "type": "dirichlet",
            "faces": wall_faces,
            "apply_to": ["velocity"],
            "comment": "Applies no-slip condition to wall surfaces",
            "no_slip": no_slip,
            "apply_faces": ["wall"]
        })

    if debug:
        for block in blocks:
            print(f"[DEBUG] Final BC block: {block}")

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
    wall_faces = [face_id for _, face_id in surfaces]
    blocks = []

    if wall_faces:
        blocks.append({
            "role": "wall",
            "type": "dirichlet",
            "faces": wall_faces,
            "apply_to": ["velocity"],
            "comment": "Applies no-slip condition to all external walls",
            "no_slip": no_slip,
            "apply_faces": ["wall"]
        })

    if debug:
        for block in blocks:
            print(f"[DEBUG] External BC block: {block}")

    return blocks



