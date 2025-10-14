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
        # Note: A non-zero velocity is required for this robust logic to work
        # as the flow axis cannot be determined if V=0.
        raise ValueError("Initial velocity vector cannot be zero.")
    velocity_unit = [v / vmag for v in velocity]
    if debug:
        print(f"[DEBUG] Normalized velocity vector: {velocity_unit}")

    face_roles = {}
    
    # --- Robust Logic: Determine Flow Axis and Direction ---
    # Find the dominant flow axis (X, Y, or Z) for the internal flow logic
    # This assumes V is nearly axis-aligned for typical duct flow analysis.
    axial_velocity_component = max(abs(v) for v in velocity)
    axis_index = velocity.index(axial_velocity_component) if axial_velocity_component in velocity else velocity.index(-axial_velocity_component) if -axial_velocity_component in velocity else 0
    axis_label = ["x", "y", "z"][axis_index]
    is_positive_flow = velocity[axis_index] > 0
    
    if debug:
        print(f"[DEBUG] Determined dominant flow axis: {axis_label}, positive direction: {is_positive_flow}")

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
        
        # --- ORIGINAL PHYSICS CHECK (FIXED SIGN): Now uses correct V.n logic ---
        # Note: This block is ignored if flow_region == "internal" below, 
        # but serves as the correct logic for external flow (if that were needed).
        if dot < -0.95: # V opposite n: Flow is entering
            face_roles[face_id] = ("inlet", face_label)
        elif dot > 0.95: # V aligned with n: Flow is exiting
            face_roles[face_id] = ("outlet", face_label)
        else:
            face_roles[face_id] = ("wall", face_label) # Retain the label

    # --- Robust Internal Flow Logic (Overrides the initial check for compliance) ---
    if flow_region == "internal":
        if debug:
            print(f"[DEBUG] Overriding to geometric check for internal flow along {axis_label}-axis.")

        for tag in surfaces:
            face_id = tag[1]
            
            # Re-calculate normal and label for current face (needed if 'surfaces' loop above was complex)
            # Re-calculating face_label is necessary for the geometric check below
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
            face_label = classify_face_label(normal_unit)
            
            # 1. Check if the face is one of the axial boundaries (x_min, x_max, etc.)
            if face_label.startswith(axis_label + "_"):
                is_min_face = face_label.endswith("_min")

                # Condition for INLET: Flow is entering this face
                # Example: V > 0 and face is x_min  OR  V < 0 and face is x_max
                is_inlet = (is_positive_flow and is_min_face) or \
                           (not is_positive_flow and not is_min_face)

                if is_inlet:
                    face_roles[face_id] = ("inlet", face_label)
                    if debug:
                        print(f"[DEBUG] Assigned INLET to face {face_id} ({face_label})")
                else:
                    face_roles[face_id] = ("outlet", face_label)
                    if debug:
                        print(f"[DEBUG] Assigned OUTLET to face {face_id} ({face_label})")
            else:
                # 2. All other faces (Y, Z boundaries, internal duct wall) are WALLS
                face_roles[face_id] = ("wall", face_label)
                if debug:
                    print(f"[DEBUG] Assigned WALL to face {face_id} ({face_label})")


    # --- Final Boundary Block Construction ---
    for tag in surfaces:
        face_id = tag[1]
        # Use .get with a default to ensure all surfaces get a role
        role, face_label = face_roles.get(face_id, ("wall", None))

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

        if role == "inlet":
            block["velocity"] = velocity
            block["pressure"] = int(pressure)
            block["apply_faces"] = [face_label] if face_label else []
        elif role == "outlet":
            # Add apply_faces tag for outlet for clarity
            block["apply_faces"] = [face_label] if face_label else []
        elif role == "wall":
            block["velocity"] = [0.0, 0.0, 0.0]
            block["no_slip"] = no_slip
            # FIX: Add apply_faces tag for wall to retain label information
            block["apply_faces"] = [face_label] if face_label else []


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
    
    Example: [-1, 0, 0] -> 'x_min'
    Example: [0, 1, 0] -> 'y_max'
    """
    axis = ["x", "y", "z"]
    max_index = max(range(3), key=lambda i: abs(normal[i]))
    
    # Check if the normal is pointing in the negative direction of the axis (e.g., -X)
    # The 'max' label is assigned if the dominant normal component is negative (e.g., -1 in [-1,0,0])
    # The 'min' label is assigned if the dominant normal component is positive (e.g., 1 in [1,0,0])
    direction = "max" if normal[max_index] < 0 else "min"
    
    return f"{axis[max_index]}_{direction}"