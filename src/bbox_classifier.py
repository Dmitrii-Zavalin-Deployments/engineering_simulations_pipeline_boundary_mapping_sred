import numpy as np
import math
from typing import List, Dict, Tuple

DEFAULT_ANGLE_THRESHOLD_DEGREES = 15.0

def compute_face_normal(vertices: List[List[float]]) -> np.ndarray:
    """
    Compute the normal vector of a face given its vertices.
    Assumes the face is planar and defined by at least 3 vertices.
    """
    v0, v1, v2 = np.array(vertices[:3])
    normal = np.cross(v1 - v0, v2 - v0)
    norm = np.linalg.norm(normal)
    return normal / norm if norm != 0 else np.zeros(3)

def angle_between(v1: np.ndarray, v2: np.ndarray) -> float:
    """
    Compute the angle in degrees between two vectors.
    """
    dot = np.dot(v1, v2)
    norm_product = np.linalg.norm(v1) * np.linalg.norm(v2)
    cos_theta = np.clip(dot / norm_product, -1.0, 1.0)
    return math.degrees(math.acos(cos_theta))

def classify_face_direction(normal: np.ndarray, threshold: float = DEFAULT_ANGLE_THRESHOLD_DEGREES) -> str:
    """
    Classify the direction of a face normal relative to bbox axes.
    Returns one of: 'x_min', 'x_max', 'y_min', 'y_max', 'z_min', 'z_max', or 'unknown'
    """
    axis_map = {
        'x_min': -np.array([1, 0, 0]),
        'x_max':  np.array([1, 0, 0]),
        'y_min': -np.array([0, 1, 0]),
        'y_max':  np.array([0, 1, 0]),
        'z_min': -np.array([0, 0, 1]),
        'z_max':  np.array([0, 0, 1]),
    }

    for label, axis in axis_map.items():
        angle = angle_between(normal, axis)
        if angle <= threshold:
            return label
    return 'unknown'

def classify_faces(faces: List[Dict], threshold: float = DEFAULT_ANGLE_THRESHOLD_DEGREES) -> Dict:
    """
    Classify all faces and return boundary condition mapping.
    Each face dict must contain: {'id': int, 'vertices': List[List[float]]}
    """
    result = {
        "boundary_conditions": {
            "faces": [],
            "x_min": [],
            "x_max": [],
            "y_min": [],
            "y_max": [],
            "z_min": [],
            "z_max": [],
        }
    }

    for face in faces:
        normal = compute_face_normal(face["vertices"])
        label = classify_face_direction(normal, threshold)
        result["boundary_conditions"]["faces"].append(face["id"])
        if label != "unknown":
            result["boundary_conditions"][label].append(face["id"])

    return result



