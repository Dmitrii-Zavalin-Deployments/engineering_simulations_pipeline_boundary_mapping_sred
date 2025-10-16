# src/geometry.py

import gmsh
import numpy as np

def get_x_coords(face_id):
    """
    Returns the X-coordinates of all nodes on a given surface.

    Args:
        face_id (int): The tag of the surface entity.

    Returns:
        np.ndarray: Array of X-coordinates for the surface's nodes.
    """
    try:
        _, node_coords, _ = gmsh.model.mesh.getNodes(2, face_id)
        coords = node_coords.reshape(-1, 3)
        return coords[:, 0]
    except Exception:
        return np.array([])


def classify_face(x_coords, x_min, x_max, threshold=0.9, tolerance=1e-6, debug=False):
    """
    Classifies a face as 'inlet', 'outlet', or 'wall' based on X-coordinate alignment.

    Args:
        x_coords (np.ndarray): X-coordinates of the face's nodes.
        x_min (float): Minimum X-bound of the model.
        x_max (float): Maximum X-bound of the model.
        threshold (float): Ratio threshold for alignment.
        tolerance (float): Coordinate tolerance for matching.
        debug (bool): If True, prints classification info.

    Returns:
        tuple: (role, label) where role is 'inlet', 'outlet', or 'wall', and label is 'x_min', 'x_max', or 'wall'.
    """
    def aligned(x, anchor): return abs(x - anchor) < tolerance

    count_min = sum(aligned(x, x_min) for x in x_coords)
    count_max = sum(aligned(x, x_max) for x in x_coords)

    ratio_min = count_min / len(x_coords) if len(x_coords) > 0 else 0
    ratio_max = count_max / len(x_coords) if len(x_coords) > 0 else 0

    if debug:
        print(f"[DEBUG_CLASSIFY] x_min = {x_min:.6f}, x_max = {x_max:.6f}")
        print(f"[DEBUG_CLASSIFY] count_min = {count_min}, ratio_min = {ratio_min:.4f}")
        print(f"[DEBUG_CLASSIFY] count_max = {count_max}, ratio_max = {ratio_max:.4f}")
        print(f"[DEBUG_CLASSIFY] Threshold = {threshold}, Tolerance = {tolerance}")

    if ratio_min >= threshold:
        if debug:
            print(f"[DEBUG_CLASSIFY] → Classified as INLET (x_min)")
        return "inlet", "x_min"
    elif ratio_max >= threshold:
        if debug:
            print(f"[DEBUG_CLASSIFY] → Classified as OUTLET (x_max)")
        return "outlet", "x_max"
    else:
        if debug:
            print(f"[DEBUG_CLASSIFY] → Classified as WALL")
        return "wall", "wall"


def build_face_metadata(face_id, coords, role, label):
    """
    Constructs the metadata dictionary for a classified face.

    Args:
        face_id (int): The tag of the surface entity.
        coords (np.ndarray): Full 3D coordinates of the face's nodes.
        role (str): Assigned role ('inlet', 'outlet', 'wall').
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

        x_coords = coords[:, 0]
        if debug:
            print(f"[DEBUG] Face {face_id}: Node count = {len(x_coords)}")
            print(f"[DEBUG] Face {face_id}: x_min = {x_min:.6f}, x_max = {x_max:.6f}")
            print(f"[DEBUG] Face {face_id}: X-coords sample = {x_coords[:5]}...")

        role, label = classify_face(x_coords, x_min, x_max, threshold, tolerance, debug)

        metadata = build_face_metadata(face_id, coords, role, label)
        centroid = metadata["p_centroid"]

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



