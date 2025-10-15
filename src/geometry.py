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


def classify_face(x_coords, x_min, x_max, threshold=0.9, tolerance=1e-6):
    """
    Classifies a face as 'inlet', 'outlet', or 'wall' based on X-coordinate alignment.

    Args:
        x_coords (np.ndarray): X-coordinates of the face's nodes.
        x_min (float): Minimum X-bound of the model.
        x_max (float): Maximum X-bound of the model.
        threshold (float): Ratio threshold for alignment.
        tolerance (float): Coordinate tolerance for matching.

    Returns:
        tuple: (role, label) where role is 'inlet', 'outlet', or 'wall', and label is 'x_min', 'x_max', or 'wall'.
    """
    def aligned(x, anchor): return abs(x - anchor) < tolerance

    count_min = sum(aligned(x, x_min) for x in x_coords)
    count_max = sum(aligned(x, x_max) for x in x_coords)

    ratio_min = count_min / len(x_coords) if len(x_coords) > 0 else 0
    ratio_max = count_max / len(x_coords) if len(x_coords) > 0 else 0

    if ratio_min >= threshold:
        return "inlet", "x_min"
    elif ratio_max >= threshold:
        return "outlet", "x_max"
    else:
        return "wall", "wall"


def build_face_metadata(face_id, x_coords, role, label):
    """
    Constructs the metadata dictionary for a classified face.

    Args:
        face_id (int): The tag of the surface entity.
        x_coords (np.ndarray): X-coordinates of the face's nodes.
        role (str): Assigned role ('inlet', 'outlet', 'wall').
        label (str): Assigned label ('x_min', 'x_max', 'wall').

    Returns:
        dict: Metadata dictionary for the face.
    """
    if x_coords.size > 0:
        p_centroid = [np.mean(x_coords), 0, 0]
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

    for dim, face_id in surfaces:
        x_coords = get_x_coords(face_id)

        if x_coords.size > 0:
            role, label = classify_face(x_coords, x_min, x_max, threshold, tolerance)
        else:
            role, label = "wall", "wall"

        if debug:
            print(f"[DEBUG] Face {face_id} classified as: {role} ({label})")

        face_roles[face_id] = (role, label)
        face_geometry_data[face_id] = build_face_metadata(face_id, x_coords, role, label)

    return face_roles, face_geometry_data



