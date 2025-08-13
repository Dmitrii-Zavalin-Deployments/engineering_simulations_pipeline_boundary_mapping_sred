# src/bbox_classifier.py

import numpy as np
import math
import json
import os
from typing import List, Dict

# ✅ Load external configuration
CONFIG_PATH = os.path.join("configs", "classifier_config.json")

def load_classifier_config():
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

CONFIG = load_classifier_config()

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

def classify_face_direction(normal: np.ndarray, thresholds: Dict[str, float]) -> str:
    """
    Classify the direction of a face normal relative to bbox axes.
    Returns one of: 'x_min', 'x_max', 'y_min', 'y_max', 'z_min', 'z_max', or fallback type.
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
        if angle <= math.degrees(math.acos(thresholds[label[0]])):
            return label

    return CONFIG.get("fallback_boundary_type", "wall")

def classify_faces(faces: List[Dict]) -> Dict:
    """
    Classify all faces and return boundary condition mapping.
    Each face dict must contain: {'id': int, 'vertices': List[List[float]]}
    """
    thresholds = CONFIG.get("directional_thresholds", {"x": 0.95, "y": 0.95, "z": 0.95})
    boundary_map = CONFIG.get("default_boundary_map", {})
    allow_multiple = CONFIG.get("allow_multiple_faces_per_direction", True)
    verbose = CONFIG.get("log_classification_details", False)

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
        direction_label = classify_face_direction(normal, thresholds)

        result["boundary_conditions"]["faces"].append(face["id"])
        if direction_label in result["boundary_conditions"]:
            result["boundary_conditions"][direction_label].append(face["id"])
        else:
            result["boundary_conditions"][direction_label] = [face["id"]]

        if verbose:
            print(f"[Classifier] Face {face['id']} → {direction_label} (normal: {normal})")

    # ✅ Map to CFD boundary types
    mapped_conditions = {
        key: boundary_map.get(key, CONFIG.get("fallback_boundary_type", "wall"))
        for key in result["boundary_conditions"]
        if key != "faces"
    }

    result["boundary_conditions"].update(mapped_conditions)

    return result



