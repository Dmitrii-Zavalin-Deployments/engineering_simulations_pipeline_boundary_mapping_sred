# src/geometry.py

import gmsh
import numpy as np

def build_face_metadata(face_id, coords, label):
    """
    Constructs the metadata dictionary for a face.

    Args:
        face_id (int): The tag of the surface entity.
        coords (np.ndarray): Full 3D coordinates of the face's nodes.
        label (str): Assigned label ('x_min', 'x_max', 'wall').

    Returns:
        dict: Metadata dictionary for the face.
    """
    if coords.size > 0:
        p_centroid = np.mean(coords, axis=0).tolist()
    else:
        p_centroid = [None, None, None]

    return {
        "normal_unit": [0, 0, 0],
        "face_label": label,
        "max_index": 0,
        "p_centroid": p_centroid
    }


def classify_face_by_centroid(centroid, x_min, x_max, threshold=0.9, debug=False):
    """
    Classifies a face as 'inlet', 'outlet', or 'wall' based on centroid X-position.

    Args:
        centroid (list): Centroid coordinates [x, y, z].
        x_min (float): Minimum X-bound of the model.
        x_max (float): Maximum X-bound of the model.
        threshold (float): Ratio threshold for alignment.
        debug (bool): If True, prints classification info.

    Returns:
        tuple: (role, label)
    """
    x = centroid[0]
    x_span = abs(x_max - x_min)
    ratio_min = abs(x - x_min) / x_span if x_span > 0 else 1.0
    ratio_max = abs(x - x_max) / x_span if x_span > 0 else 1.0

    if debug:
        print(f"[DEBUG_CLASSIFY] Centroid X = {x:.6f}, ratio_min = {ratio_min:.4f}, ratio_max = {ratio_max:.4f}")

    if ratio_min < (1 - threshold):
        return "inlet", "x_min"
    elif ratio_max < (1 - threshold):
        return "outlet", "x_max"
    else:
        return "wall", "wall"


def assign_roles_to_faces(surfaces, x_min, x_max, threshold=0.9, tolerance=1e-6, debug=False):
    """
    Loops through all surfaces, classifies each, and builds face_roles and face_geometry_data.

    Args:
        surfaces (list of tuples): List of surface entities (dim, tag).
        x_min (float): Minimum X-bound of the model.
        x_max (float): Maximum X-bound of the model.
        threshold (float): Ratio threshold for alignment.
        tolerance (float): Coordinate tolerance for matching.
        debug (bool): If True, prints classification info.

    Returns:
        tuple: (face_roles, face_geometry_data)
    """
    face_roles = {}
    face_geometry_data = {}

    bbox = gmsh.model.getBoundingBox(3, 1)
    min_bounds = [bbox[0], bbox[1], bbox[2]]
    max_bounds = [bbox[3], bbox[4], bbox[5]]
    TOL = tolerance

    for dim, face_id in surfaces:
        try:
            _, node_coords, _ = gmsh.model.mesh.getNodes(dim, face_id)
            coords = node_coords.reshape(-1, 3)
        except Exception:
            if debug:
                print(f"[DEBUG] Face {face_id}: Failed to retrieve node data.")
            continue

        if coords.shape[0] < 3:
            if debug:
                print(f"[DEBUG] Face {face_id}: Skipped due to insufficient nodes ({coords.shape[0]}).")
            continue

        centroid = np.mean(coords, axis=0).tolist()
        role, label = classify_face_by_centroid(centroid, x_min, x_max, threshold, debug)
        metadata = build_face_metadata(face_id, coords, label)

        if debug:
            print(f"[DEBUG] Face {face_id}: Centroid = {centroid}")

        is_min_on_any_axis = any(abs(centroid[i] - min_bounds[i]) < TOL for i in range(3))
        is_max_on_any_axis = any(abs(centroid[i] - max_bounds[i]) < TOL for i in range(3))
        is_on_bounding_plane = is_min_on_any_axis or is_max_on_any_axis

        if debug:
            print(f"[DEBUG] Face {face_id}: Bounding plane check → min: {is_min_on_any_axis}, max: {is_max_on_any_axis}")

        if role == "wall" and is_on_bounding_plane:
            role = "skip"
            label = "skip"
            if debug:
                print(f"[DEBUG] Face {face_id}: Overridden to SKIP due to bounding plane alignment.")

        face_roles[face_id] = (role, label)
        face_geometry_data[face_id] = metadata

        if debug:
            print(f"[DEBUG] Face {face_id} FINAL classification: {role} ({label})")
            print("-" * 60)

    return face_roles, face_geometry_data



