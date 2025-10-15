# src/geometry.py


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

    # 1. Robustness Threshold
    if abs(normal[max_index]) < 0.95:
        if debug:
            print(f"[DEBUG_LABEL] Face {face_id}: Threshold FAILED ({abs(normal[max_index]):.4f} < 0.95). Returning 'wall'.")
        return "wall"

    if debug:
        print(f"[DEBUG_LABEL] Face {face_id}: Threshold PASSED.")

    # 2. Logic: Negative component -> min, Positive component -> max
    direction = "min" if normal[max_index] < 0 else "max"

    if debug:
        print(f"[DEBUG_LABEL] Face {face_id}: Normal component sign is {'NEGATIVE' if normal[max_index] < 0 else 'POSITIVE'}. Assigned direction: {direction}")

    result = f"{axis[max_index]}_{direction}"

    if debug:
        print(f"[DEBUG_LABEL] Face {face_id}: Final label result: {result}")

    return result



