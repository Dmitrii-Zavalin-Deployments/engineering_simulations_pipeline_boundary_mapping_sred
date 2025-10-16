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
    Generates boundary condition blocks for internal flow using centroid-based inlet/outlet classification.

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

    x_min = min_bounds[0]
    x_max = max_bounds[0]
    x_span = abs(x_max - x_min)
    TOL = 1e-6  # Use same tolerance as classification

    for dim, face_id in surfaces:
        metadata = face_geometry_data.get(face_id, {})
        centroid = metadata.get("p_centroid", [None, None, None])

        if centroid is None or None in centroid:
            if debug:
                print(f"[DEBUG] Face {face_id}: Missing centroid, defaulting to wall.")
            wall_faces.append(face_id)
            continue

        x = centroid[0]
        ratio_min = abs(x - x_min) / x_span if x_span > 0 else 1.0
        ratio_max = abs(x - x_max) / x_span if x_span > 0 else 1.0

        if debug:
            print(f"[DEBUG] Face {face_id}: Centroid X = {x:.6f}, ratio_min = {ratio_min:.4f}, ratio_max = {ratio_max:.4f}")

        if ratio_min < (1 - threshold):
            inlet_faces.append(face_id)
            if debug:
                print(f"[DEBUG] Face {face_id}: Classified as INLET")
        elif ratio_max < (1 - threshold):
            outlet_faces.append(face_id)
            if debug:
                print(f"[DEBUG] Face {face_id}: Classified as OUTLET")
        else:
            # Check if wall face lies on any bounding box plane
            is_min_on_any_axis = any(abs(centroid[i] - min_bounds[i]) < TOL for i in range(3))
            is_max_on_any_axis = any(abs(centroid[i] - max_bounds[i]) < TOL for i in range(3))
            is_on_bounding_plane = is_min_on_any_axis or is_max_on_any_axis

            if is_on_bounding_plane:
                if debug:
                    print(f"[DEBUG] Skipping face {face_id} (centroid on bounding box plane)")
                continue  # Skip this face
            else:
                wall_faces.append(face_id)
                if debug:
                    print(f"[DEBUG] Face {face_id}: Classified as WALL")

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
            "apply_faces": ["x_min"]
        })

    if outlet_faces:
        blocks.append({
            "role": "outlet",
            "type": "neumann",
            "faces": outlet_faces,
            "apply_to": ["pressure"],
            "comment": "Defines outlet flow behavior with pressure gradient",
            "apply_faces": ["x_max"]
        })

    if wall_faces:
        blocks.append({
            "role": "wall",
            "type": "dirichlet",
            "faces": wall_faces,
            "apply_to": ["velocity"],
            "comment": "Applies no-slip condition to internal wall surfaces",
            "no_slip": no_slip,
            "apply_faces": "wall"
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



