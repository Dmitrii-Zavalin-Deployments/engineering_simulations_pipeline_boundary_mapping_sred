# src/geometry.py

import gmsh

def classify_face_label(normal, face_id, debug):
    """
    Classifies a face based on its outward normal vector.
    Returns 'x_min', 'y_max', etc. for axis-aligned faces or 'wall' otherwise.
    """
    if debug:
        print(f"[DEBUG_LABEL] Starting classification for Face {face_id} with normal: {normal}")

    axis = ["x", "y", "z"]
    max_index = max(range(3), key=lambda i: abs(normal[i]))

    if debug:
        print(f"[DEBUG_LABEL] Face {face_id}: Max index found: {max_index} ({axis[max_index]}-axis). Max component: {normal[max_index]:.4f}") 

    if abs(normal[max_index]) < 0.95:
        if debug:
            print(f"[DEBUG_LABEL] Face {face_id}: Threshold FAILED ({abs(normal[max_index]):.4f} < 0.95). Returning 'wall'.")
        return "wall"

    if debug:
        print(f"[DEBUG_LABEL] Face {face_id}: Threshold PASSED.")

    direction = "min" if normal[max_index] < 0 else "max"

    if debug:
        print(f"[DEBUG_LABEL] Face {face_id}: Normal component sign is {'NEGATIVE' if normal[max_index] < 0 else 'POSITIVE'}. Assigned direction: {direction}")

    result = f"{axis[max_index]}_{direction}"

    if debug:
        print(f"[DEBUG_LABEL] Face {face_id}: Final label result: {result}")

    return result


def get_global_bounds(debug=False):
    """
    Returns the global bounding box limits of the imported geometry.
    Output: (x_min, x_max), (y_min, y_max), (z_min, z_max)
    """
    bounds = gmsh.model.getBoundingBox(3, 1)
    if len(bounds) == 7:
        _, x_min, y_min, z_min, x_max, y_max, z_max = bounds
    else:
        x_min, y_min, z_min, x_max, y_max, z_max = bounds if len(bounds) == 6 else [-1e9] * 3 + [1e9] * 3

    if debug:
        print(f"[DEBUG_BOUNDS] Bounding Box: x=({x_min}, {x_max}), y=({y_min}, {y_max}), z=({z_min}, {z_max})")

    return (x_min, x_max), (y_min, y_max), (z_min, z_max)


def detect_flow_axis(velocity, debug=False):
    """
    Detects the dominant flow axis from the velocity vector.
    Returns: axis_index (0=x, 1=y, 2=z), axis_label ('x', 'y', 'z'), is_positive_flow (bool)
    """
    vmag = sum(v**2 for v in velocity)**0.5
    if vmag == 0:
        raise ValueError("Velocity vector cannot be zero.")

    normalized = [v / vmag for v in velocity]
    axis_index = max(range(3), key=lambda i: abs(normalized[i]))
    axis_label = ["x", "y", "z"][axis_index]
    is_positive_flow = normalized[axis_index] > 0

    if debug:
        print(f"[DEBUG_FLOW] Velocity: {velocity}, Normalized: {normalized}")
        print(f"[DEBUG_FLOW] Dominant axis: {axis_label}, Positive flow: {is_positive_flow}")

    return axis_index, axis_label, is_positive_flow



