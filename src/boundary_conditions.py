# src/boundary_conditions.py

import gmsh
import math
import numpy as np

def generate_boundary_conditions(step_path, velocity, pressure, no_slip, flow_region, resolution=None, debug=False):
    gmsh.open(step_path)
    if debug:
        print(f"[DEBUG] Opened STEP file: {step_path}")

    if resolution:
        gmsh.option.setNumber("Mesh.CharacteristicLengthMin", resolution)
        gmsh.option.setNumber("Mesh.CharacteristicLengthMax", resolution)
        if debug:
            print(f"[DEBUG] Mesh resolution set to: {resolution}")

    gmsh.model.mesh.generate(3)
    if debug:
        print("[DEBUG] 3D mesh generated")

    dim = 2  # surface dimension
    surfaces = gmsh.model.getEntities(dim)
    if debug:
        print(f"[DEBUG] Extracted {len(surfaces)} surface entities")

    boundary_conditions = []

    vmag = math.sqrt(sum(v**2 for v in velocity))
    if vmag == 0:
        raise ValueError("Initial velocity vector cannot be zero.")
    velocity_unit = [v / vmag for v in velocity]
    if debug:
        print(f"[DEBUG] Normalized velocity vector: {velocity_unit}")

    face_roles = {}

    # --- Robust Logic: Determine Flow Axis and Direction ---
    axial_velocity_component = max(abs(v) for v in velocity)
    
    # Safely find the index of the dominant component
    try:
        axis_index = velocity.index(axial_velocity_component)
    except ValueError:
        try:
            axis_index = velocity.index(-axial_velocity_component)
        except ValueError:
            axis_index = 0 
            
    axis_label = ["x", "y", "z"][axis_index]
    is_positive_flow = velocity[axis_index] > 0

    if debug:
        print(f"[DEBUG] Determined dominant flow axis: {axis_label}, positive direction: {is_positive_flow}")

    # The physics-based check below is ignored when flow_region="internal" 
    # but is retained for completeness/non-internal regions.
    for tag in surfaces:
        face_id = tag[1]
        try:
            node_tags, node_coords, _ = gmsh.model.mesh.getNodes(dim, face_id)
        except Exception:
            continue
        if len(node_coords) < 9:
            continue

        p1 = np.array(node_coords[0:3])
        p2 = np.array(node_coords[3:6])
        p3 = np.array(node_coords[6:9])
        v1 = p2 - p1
        v2 = p3 - p1
        normal = np.cross(v1, v2)
        nmag = np.linalg.norm(normal)
        if nmag == 0:
            continue
        normal_unit = (normal / nmag).tolist()
        dot = sum(v * n for v, n in zip(velocity_unit, normal_unit))
        face_label = classify_face_label(normal_unit)

        # Corrected Physics Check (Dot < 0 is Inlet, Dot > 0 is Outlet)
        if dot < -0.95:
            face_roles[face_id] = ("inlet", face_label)
        elif dot > 0.95:
            face_roles[face_id] = ("outlet", face_label)
        else:
            face_roles[face_id] = ("wall", face_label)

    # --- Robust Internal Flow Logic (Approach 3 Override) ---
    if flow_region == "internal":
        if debug:
            print(f"[DEBUG] Overriding to geometric check for internal flow along {axis_label}-axis.")

        for tag in surfaces:
            face_id = tag[1]
            try:
                node_tags, node_coords, _ = gmsh.model.mesh.getNodes(dim, face_id)
            except Exception:
                continue
            if len(node_coords) < 9:
                continue
            p1 = np.array(node_coords[0:3])
            p2 = np.array(node_coords[3:6])
            p3 = np.array(node_coords[6:9])
            v1 = p2 - p1
            v2 = p3 - p1
            normal = np.cross(v1, v2)
            nmag = np.linalg.norm(normal)
            if nmag == 0:
                continue
            normal_unit = (normal / nmag).tolist()
            face_label = classify_face_label(normal_unit) # Recalculate label using the corrected function

            if face_label.startswith(axis_label + "_"):
                is_min_face = face_label.endswith("_min")
                is_inlet = (is_positive_flow and is_min_face) or (not is_positive_flow and not is_min_face)

                if is_inlet:
                    face_roles[face_id] = ("inlet", face_label)
                    if debug:
                        print(f"[DEBUG] Assigned INLET to face {face_id} ({face_label})")
                else:
                    face_roles[face_id] = ("outlet", face_label)
                    if debug:
                        print(f"[DEBUG] Assigned OUTLET to face {face_id} ({face_label})")
            else:
                # Assign role 'wall' and retain the label (which will be 'wall' if non-axis-aligned)
                face_roles[face_id] = ("wall", face_label)
                if debug:
                    print(f"[DEBUG] Assigned WALL to face {face_id} ({face_label})")

    # --- Final Boundary Block Construction ---
    for tag in surfaces:
        face_id = tag[1]
        role, face_label = face_roles.get(face_id, ("wall", None))

        # Determine if the label is descriptive (i.e., not the simple 'wall' fallback)
        is_descriptive_label = face_label and face_label not in ["wall"]

        block = {
            "role": role,
            "type": "dirichlet" if role in ["inlet", "wall"] else "neumann",
            "faces": [face_id],
            "apply_to": ["velocity", "pressure"] if role == "inlet" else ["pressure"] if role == "outlet" else ["velocity"],
            "comment": {
                "inlet": "Defines inlet flow parameters for velocity and pressure",
                "outlet": "Defines outlet flow behavior with pressure gradient",
                "wall": "Defines near-wall flow parameters with no-slip condition"
            }[role]
        }
        
        # Construct apply_faces list: only include label if it's descriptive (x_min, y_max, etc.)
        apply_faces_list = [face_label] if is_descriptive_label else []

        if role == "inlet":
            block["velocity"] = velocity
            block["pressure"] = int(pressure)
            block["apply_faces"] = apply_faces_list
        elif role == "outlet":
            block["apply_faces"] = apply_faces_list
        elif role == "wall":
            block["velocity"] = [0.0, 0.0, 0.0]
            block["no_slip"] = no_slip
            block["apply_faces"] = apply_faces_list

        boundary_conditions.append(block)
        if debug:
            print(f"[DEBUG] Appended boundary block for face {face_id}: {block}")

    if debug:
        print("[DEBUG] Final boundary condition blocks:")
        for b in boundary_conditions:
            print(b)

    return boundary_conditions

def classify_face_label(normal):
    """
    Classifies a face based on its outward normal vector.

    Returns 'x_min', 'y_max', etc. for axis-aligned faces.
    For non-axis-aligned faces, returns 'wall' to enforce compliance 
    and prevent non-descriptive labels in apply_faces.
    """
    axis = ["x", "y", "z"]
    max_index = max(range(3), key=lambda i: abs(normal[i]))

    # 1. Robustness Threshold: If normal is NOT strongly aligned with an axis (< 0.95), 
    # return the simple role 'wall' as the label.
    if abs(normal[max_index]) < 0.95:
        return "wall"

    # 2. Corrected Logic: Negative normal component (e.g., -1 in [-1, 0, 0]) means MINIMUM face (x_min)
    direction = "min" if normal[max_index] < 0 else "max"
    return f"{axis[max_index]}_{direction}"



