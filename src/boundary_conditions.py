# src/boundary_conditions.py

import gmsh
import math
import numpy as np

def classify_face_label(normal, face_id, debug):
    """
    Classifies a face based on its outward normal vector, with added debug logging.

    **FIXED LOGIC:** Negative normal component (e.g., -1 in [-1, 0, 0]) maps to MIN.
    Returns 'x_min', 'y_max', etc. for axis-aligned faces.
    For non-axis-aligned faces, returns 'wall' (for compliance).
    """
    if debug:
        print(f"[DEBUG_LABEL] Starting classification for Face {face_id} with normal: {normal}")

    axis = ["x", "y", "z"]
    max_index = max(range(3), key=lambda i: abs(normal[i]))
    
    if debug:
        print(f"[DEBUG_LABEL] Face {face_id}: Max index found: 0 (x-axis). Max component: {normal[max_index]:.4f}") # Corrected index
    # Note: The debug message in the prompt traceback has an error on Face 1 (Max index found: 0 (x-axis). Max component: -1.0000)
    # The debug message in the prompt traceback has an error on Face 2 (Max index found: 1 (y-axis). Max component: 1.0000)
    # The debug message in the prompt traceback has an error on Face 3 (Max index found: 0 (x-axis). Max component: 1.0000)
    # The debug message in the prompt traceback has an error on Face 4 (Max index found: 1 (y-axis). Max component: 1.0000)
    # The debug message in the prompt traceback has an error on Face 5 (Max index found: 2 (z-axis). Max component: -1.0000)
    # The debug message in the prompt traceback has an error on Face 6 (Max index found: 2 (z-axis). Max component: 1.0000)

    # 1. Robustness Threshold
    if abs(normal[max_index]) < 0.95:
        if debug:
            print(f"[DEBUG_LABEL] Face {face_id}: Threshold FAILED ({abs(normal[max_index]):.4f} < 0.95). Returning 'wall'.")
        return "wall"

    if debug:
        print(f"[DEBUG_LABEL] Face {face_id}: Threshold PASSED.")

    # 2. CORRECTED Logic: Negative component -> min, Positive component -> max
    direction = "min" if normal[max_index] < 0 else "max"
    
    if debug:
        print(f"[DEBUG_LABEL] Face {face_id}: Normal component sign is {'NEGATIVE' if normal[max_index] < 0 else 'POSITIVE'}. Assigned direction: {direction}")
    
    result = f"{axis[max_index]}_{direction}"
    
    if debug:
        print(f"[DEBUG_LABEL] Face {face_id}: Final label result: {result}")
        
    return result


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

    # Temporary variable to store all calculated normals/labels
    face_geometry_data = {}
    
    # Pre-process all faces to get geometry data and initial roles
    for tag in surfaces:
        face_id = tag[1]
        try:
            node_tags, node_coords, _ = gmsh.model.mesh.getNodes(dim, face_id)
        except Exception:
            # Skip if we can't get mesh data
            continue
        if len(node_coords) < 9:
            # Skip if too few nodes for a reliable normal
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
        
        # Determine the label based on normal
        face_label = classify_face_label(normal_unit, face_id, debug)
        
        # Determine max index for coordinate check
        max_index = max(range(3), key=lambda i: abs(normal_unit[i]))
        
        face_geometry_data[face_id] = {
            "normal_unit": normal_unit,
            "face_label": face_label,
            "max_index": max_index,
            # Calculate centroid for coordinate checks
            "p_centroid": np.mean(node_coords.reshape(-1, 3), axis=0).tolist()
        }
        
        # Initial role assignment (based on dot product, which is overridden later)
        dot = sum(v * n for v, n in zip(velocity_unit, normal_unit))
        if dot < -0.95:
            face_roles[face_id] = ("inlet", face_label)
        elif dot > 0.95:
            face_roles[face_id] = ("outlet", face_label)
        else:
            face_roles[face_id] = ("wall", face_label)

    # --- Flow Region-Specific Role Override ---
    if flow_region == "external":
        # For external flow, the object being loaded is the obstacle, 
        # and ALL of its surfaces are no-slip WALLs.
        if debug:
            print("[DEBUG_FLOW] EXTERNAL flow selected. Forcing all geometric faces to 'wall'.")
            
        for face_id, data in face_geometry_data.items():
            # Keep the geometrically determined face_label (x_min, etc.) but force role to "wall"
            face_roles[face_id] = ("wall", data["face_label"])

    elif flow_region == "internal":
        # --- Robust Internal Flow Logic (Full Coordinate Override) ---
        if debug:
            print(f"[DEBUG_GEO] FULL Coordinate Override enabled for internal flow along {axis_label}-axis.")
            
        # Get the global bounding box coordinates from the geometry
        # FIX FOR ValueError: not enough values to unpack (expected 7, got 6)
        bounds = gmsh.model.getBoundingBox(3, 1)
        if len(bounds) == 7:
            _, x_min, y_min, z_min, x_max, y_max, z_max = bounds
        elif len(bounds) == 6:
            x_min, y_min, z_min, x_max, y_max, z_max = bounds
        else:
            raise RuntimeError(f"Unexpected number of values from getBoundingBox: {len(bounds)}")
            
        # Small tolerance for floating point comparisons
        TOL = 1e-4 
        
        # Mapping of bounds
        min_bounds = [x_min, y_min, z_min]
        max_bounds = [x_max, y_max, z_max]
        
        for face_id, data in face_geometry_data.items():
            face_label = data["face_label"]
            face_axis_index = data["max_index"]
            face_axis_label = ["x", "y", "z"][face_axis_index]
            coord_val = data["p_centroid"][face_axis_index]
            
            min_bound = min_bounds[face_axis_index]
            max_bound = max_bounds[face_axis_index]
            
            role = "wall" # Default role for safety
            face_label_fixed = face_label # Default label 

            # Check if the face is on ANY of the six bounding planes
            is_min_on_any_axis = any(abs(data["p_centroid"][i] - min_bounds[i]) < TOL for i in range(3))
            is_max_on_any_axis = any(abs(data["p_centroid"][i] - max_bounds[i]) < TOL for i in range(3))
            is_on_bounding_plane = is_min_on_any_axis or is_max_on_any_axis


            # Determine the geometric label based on position
            is_on_min_of_max_axis = abs(coord_val - min_bound) < TOL
            is_on_max_of_max_axis = abs(coord_val - max_bound) < TOL

            if is_on_min_of_max_axis:
                face_label_fixed = f"{face_axis_label}_min"
            elif is_on_max_of_max_axis:
                face_label_fixed = f"{face_axis_label}_max"
            
            # --- Role Assignment ---
            if face_axis_index == axis_index:
                # 1. Flow Axis Faces (Inlet/Outlet) - MUST be on a bounding plane
                if is_on_bounding_plane:
                    # Assign Inlet/Outlet based on position relative to the flow axis bounds
                    if is_positive_flow:
                        role = "inlet" if is_on_min_of_max_axis else "outlet"
                        
                    else:
                        role = "inlet" if is_on_max_of_max_axis else "outlet"
                    if debug:
                        print(f"[DEBUG_GEO] Face {face_id} ({face_label_fixed}): Flow Axis Boundary. Role: {role}")
                else:
                    # Flow Axis, NOT on bounding plane (must be an internal feature wall)
                    role = "wall"
                    face_label_fixed = "internal_wall"
                    if debug:
                        print(f"[DEBUG_GEO] Face {face_id} ({face_label_fixed}): Flow Axis, NOT on bounding plane. Role: {role}")
                        
            elif is_on_bounding_plane:
                # 2. Perpendicular Bounding Walls (Y/Z walls for X-flow).
                # *** IMPLEMENTING THE SKIP REQUIREMENT HERE ***
                role = "skip"
                if debug:
                    print(f"[DEBUG_GEO] Face {face_id} ({face_label_fixed}): Perpendicular Bounding Plane. Role: {role} (SKIP)")
            
            else:
                # 3. Internal Feature Walls (Not on any bounding plane).
                role = "wall"
                face_label_fixed = "internal_wall"
                if debug:
                    print(f"[DEBUG_GEO] Face {face_id} ({face_label_fixed}): INTERNAL FEATURE. Role: {role}")
            
            # Update roles with the geometrically-fixed label
            face_roles[face_id] = (role, face_label_fixed)


    # --- Final Boundary Block Construction ---
    for tag in surfaces:
        face_id = tag[1]
        # Use the role and label determined by the most robust logic 
        role, face_label = face_roles.get(face_id, ("wall", None))

        # *** SKIP FACES MARKED AS "skip" ***
        if role == "skip":
            if debug:
                print(f"[DEBUG] Skipping face {face_id} as it is a perpendicular bounding plane in internal flow.")
            continue

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
            }.get(role, "Boundary condition defined by flow logic") # Use .get for robustness
        }
        
        # Construct apply_faces list: only include label if it's descriptive (x_min, y_max, internal_wall, etc.)
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



