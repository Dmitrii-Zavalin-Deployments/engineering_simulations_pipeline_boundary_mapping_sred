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

    # --- START: Primary V.n Classification Logic ---
    for tag in surfaces:
        face_id = tag[1]
        try:
            # We must get nodes to compute the normal vector
            node_tags, node_coords, _ = gmsh.model.mesh.getNodes(dim, face_id)
        except Exception:
            # Skip surfaces that fail node extraction
            continue
        if len(node_coords) < 9:
            # Need at least 3 nodes (9 coordinates) to compute a normal
            continue

        p1 = np.array(node_coords[0:3])
        p2 = np.array(node_coords[3:6])
        p3 = np.array(node_coords[6:9])
        v1 = p2 - p1
        v2 = p3 - p1
        
        # Compute face normal (cross product)
        normal = np.cross(v1, v2)
        nmag = np.linalg.norm(normal)
        if nmag == 0:
            continue
        normal_unit = (normal / nmag).tolist()
        
        # Calculate dot product: Alignment with initial velocity
        dot = sum(v * n for v, n in zip(velocity_unit, normal_unit))
        face_label = classify_face_label(normal_unit)

        if dot > 0.95:
            # Normal is ALIGNED with V -> Flow is entering
            face_roles[face_id] = ("inlet", face_label)
        elif dot < -0.95:
            # Normal is OPPOSED to V -> Flow is exiting
            face_roles[face_id] = ("outlet", face_label)
        else:
            # Normal is ORTHOGONAL to V -> Wall (or internal cylindrical surface)
            face_roles[face_id] = ("wall", face_label) 

        if debug:
            print(f"[DEBUG] Face {face_id} normal: {normal_unit} | Dot: {dot:.3f} | Role: {face_roles[face_id][0]}")

    # --- END: Primary V.n Classification Logic ---


    # --- START: REMOVED INCORRECT FALLBACK LOGIC ---
    # The redundant 'if flow_region == "internal":' block that overrode the 
    # V.n classification and inverted the roles is removed.
    # The dot product method above is sufficient and physically correct.
    # --- END: REMOVED INCORRECT FALLBACK LOGIC ---


    # --- START: Boundary Condition Block Construction ---
    for tag in surfaces:
        face_id = tag[1]
        # Use face_label from V.n classification, defaulting to 'wall'
        role, face_label = face_roles.get(face_id, ("wall", None))

        # Hybrid Dirichlet/Neumann Strategy
        block = {
            "role": role,
            # Dirichlet for Inlet/Wall, Neumann for Outlet
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
            # Ensure pressure is an integer if required by the schema (as in the original code)
            block["pressure"] = int(pressure) 
            block["apply_faces"] = [face_label] if face_label else []
        elif role == "outlet":
            # Neumann outlet requires no velocity/pressure values, only 'apply_faces'
            block["apply_faces"] = [face_label] if face_label else []
        elif role == "wall":
            # CORRECTED: Velocity MUST be [0.0, 0.0, 0.0] for no-slip condition
            block["velocity"] = [0.0, 0.0, 0.0]
            block["no_slip"] = no_slip
            # Add apply_faces for walls if they are axis-aligned
            if face_label:
                block["apply_faces"] = [face_label]
            
        boundary_conditions.append(block)
        if debug:
            print(f"[DEBUG] Appended boundary block for face {face_id}: {block}")

    if debug:
        print("[DEBUG] Final boundary condition blocks:")
        for b in boundary_conditions:
            print(b)
    # --- END: Boundary Condition Block Construction ---

    return boundary_conditions

def classify_face_label(normal):
    """Classifies axis-aligned faces (e.g., x_min, y_max) based on the normal vector."""
    axis = ["x", "y", "z"]
    # Find the axis with the largest absolute component (dominant direction)
    max_index = max(range(3), key=lambda i: abs(normal[i]))
    # Determine min/max based on the SIGN of the dominant component
    # Gmsh/CAD convention: Normal OUT of the volume is usually positive.
    # If normal is positive, it's the max face (e.g., [1,0,0] is x_max)
    # If normal is negative, it's the min face (e.g., [-1,0,0] is x_min)
    direction = "max" if normal[max_index] > 0 else "min"
    return f"{axis[max_index]}_{direction}"


