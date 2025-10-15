# src/bc_generators.py

def generate_internal_bc_blocks(
    surfaces, face_geometry_data, face_roles,
    velocity, pressure, no_slip,
    axis_index, is_positive_flow,
    min_bounds, max_bounds,
    threshold=0.9,
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
        threshold (float): Alignment threshold for wall filtering.
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
        elif role == "wall":
            wall_faces.append(face_id)
        elif role == "skip":
            if debug:
                print(f"[DEBUG] Skipping face {face_id} (label: {label}) due to perpendicular bounding plane.")
        else:
            if debug:
                print(f"[DEBUG] Face {face_id} has unrecognized role: {role}. Defaulting to skip.")

    blocks = []

    if inlet_faces:
        blocks.append({
            "role": "inlet",
            "type": "dirichlet",
            "faces": inlet_faces,
            "apply_to": ["velocity", "pressure"],
            "comment": "Defines inlet flow parameters for velocity and pressure",
            "velocity": velocity,
            "pressure": int(pressure),
            "apply_faces": "x_min"
        })

    if outlet_faces:
        blocks.append({
            "role": "outlet",
            "type": "neumann",
            "faces": outlet_faces,
            "apply_to": ["pressure"],
            "comment": "Defines outlet flow behavior with pressure gradient",
            "apply_faces": "x_max"
        })

    if wall_faces:
        blocks.append({
            "role": "wall",
            "type": "dirichlet",
            "faces": wall_faces,
            "apply_to": ["velocity"],
            "comment": "Applies no-slip condition to internal wall surfaces",
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



