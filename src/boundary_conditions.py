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
        # Debug printing consistency
        print(f"[DEBUG_LABEL] Face {face_id}: Max index found: {max_index} ({axis[max_index]}-axis). Max component: {normal[max_index]:.4f}") 

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


def generate_boundary_conditions(step_path, velocity, pressure, no_slip, flow_region, padding_factor=0, resolution=None, debug=False):
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
            
    # --- Bounding Box Setup (Needed for both internal and external flow) ---
    bounds = gmsh.model.getBoundingBox(3, 1)
    if len(bounds) == 7:
        _, x_min, y_min, z_min, x_max, y_max, z_max = bounds
    elif len(bounds) == 6:
        x_min, y_min, z_min, x_max, y_max, z_max = bounds
    else:
        # Fallback to extreme values if bounds fail (shouldn't happen)
        x_min, y_min, z_min, x_max, y_max, z_max = -1e9, -1e9, -1e9, 1e9, 1e9, 1e9
        
    # Small tolerance for floating point comparisons
    TOL = 1e-4 
    min_bounds = [x_min, y_min, z_min]
    max_bounds = [x_max, y_max, z_max]


    # --- Flow Region-Specific Role Override ---
    if flow_region == "external":
        # For external flow, the object being loaded is the obstacle.
        if debug:
            print("[DEBUG_FLOW] EXTERNAL flow selected. Forcing all geometric faces to 'wall' and synthesizing far-field boundaries.")
            
            # Integrate padding factor logic for visualization/downstream systems
            if padding_factor > 0 and resolution is not None:
                pad = padding_factor * resolution
                comp_min_x = x_min - pad
                comp_min_y = y_min - pad
                comp_min_z = z_min - pad
                comp_max_x = x_max + pad
                comp_max_y = y_max + pad
                comp_max_z = z_max + pad
                print(f"[DEBUG] Computational box bounds (Padded): min=({comp_min_x:.3f}, {comp_min_y:.3f}, {comp_min_z:.3f}), max=({comp_max_x:.3f}, {comp_max_y:.3f}, {comp_max_z:.3f})")

        for face_id, data in face_geometry_data.items():
            # Force role to "wall" and label to "wall" for simple grouping
            face_roles[face_id] = ("wall", "wall")

    elif flow_region == "internal":
        # --- Robust Internal Flow Logic (Full Coordinate Override) ---
        if debug:
            print(f"[DEBUG_GEO] FULL Coordinate Override enabled for internal flow along {axis_label}-axis.")
            
        
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
                    face_label_fixed = "wall" 
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
                face_label_fixed = "wall"
                if debug:
                    print(f"[DEBUG_GEO] Face {face_id} ({face_label_fixed}): INTERNAL FEATURE. Role: {role}")
            
            # Update roles with the geometrically-fixed label
            face_roles[face_id] = (role, face_label_fixed)


    # --- Final Boundary Block Construction (Grouping Faces) ---
    boundary_conditions = []
    
    # 1. Handle Real Faces (ID > 0)
    if flow_region == "internal":
        # INTERNAL: Group faces with the same role and geometric label (like the original code)
        grouped_blocks = {}
        
        for tag in surfaces:
            face_id = tag[1]
            role, face_label = face_roles.get(face_id, ("wall", "wall")) 

            if role == "skip":
                if debug:
                    print(f"[DEBUG] Skipping face {face_id} as it is a perpendicular bounding plane in internal flow.")
                continue
                
            # The key for grouping should be the role and the descriptive label
            group_key = (role, face_label)
            
            if group_key not in grouped_blocks:
                # Create a new block template
                block = {
                    "role": role,
                    "type": "dirichlet" if role in ["inlet", "wall"] else "neumann",
                    "faces": [face_id],
                    "apply_to": ["velocity", "pressure"] if role == "inlet" else ["pressure"] if role == "outlet" else ["velocity"],
                    "comment": {
                        "inlet": "Defines inlet flow parameters for velocity and pressure",
                        "outlet": "Defines outlet flow behavior with pressure gradient",
                        "wall": "Defines near-wall flow parameters with no-slip condition"
                    }.get(role, "Boundary condition defined by flow logic")
                }
                
                # Construct apply_faces list based on the label
                apply_faces_list = []
                if face_label in ["x_min", "x_max", "y_min", "y_max", "z_min", "z_max"]:
                    apply_faces_list = [face_label]
                elif role == "wall" and face_label == "wall":
                    apply_faces_list = ["wall"] 

                if role == "inlet":
                    block["velocity"] = velocity
                    block["pressure"] = int(pressure)
                elif role == "outlet":
                    block["apply_to"] = ["pressure"] 
                elif role == "wall":
                    block["velocity"] = [0.0, 0.0, 0.0]
                    block["no_slip"] = no_slip
                
                block["apply_faces"] = apply_faces_list
                grouped_blocks[group_key] = block
                
            else:
                # Append the face_id to the existing block's list
                grouped_blocks[group_key]["faces"].append(face_id)
                if debug:
                    print(f"[DEBUG] Grouped face {face_id} into existing block with key {group_key}")

        boundary_conditions.extend(list(grouped_blocks.values()))


    elif flow_region == "external":
        # EXTERNAL: Separate ALL obstacle faces for max flexibility (as decided for external flow)
        for tag in surfaces:
            face_id = tag[1]
            role, face_label = face_roles.get(face_id, ("wall", "wall")) 

            # In external flow, all loaded faces are walls, and none are skipped
            if role != "wall": continue
                
            # Create a new block for THIS face (NO grouping)
            block = {
                "role": role,
                "type": "dirichlet",
                "faces": [face_id], 
                "apply_to": ["velocity"],
                "comment": f"Obstacle Wall Face {face_id} with no-slip condition",
                "velocity": [0.0, 0.0, 0.0],
                "no_slip": no_slip, 
                "apply_faces": "wall"
            }
            boundary_conditions.append(block)


    # --- Synthesize FAR-FIELD Boundaries for External Flow (Crucial for a complete model) ---
    if flow_region == "external":
        if debug:
            print("[DEBUG_FLOW] Synthesizing external domain boundaries...")
            
        # Define labels perpendicular to the flow axis
        perpendicular_axes = [
            f"{a}_{d}" 
            for i, a in enumerate(["x", "y", "z"]) 
            for d in ["min", "max"] 
            if i != axis_index # Exclude the dominant flow axis (x_min, x_max in this case)
        ]
        
        synthesized_id = -1
        
        # --- Synthesize Inlet/Outlet ---
        
        # Inlet (e.g., x_min in positive X flow)
        inlet_label = f"{axis_label}_min" if is_positive_flow else f"{axis_label}_max"
        
        boundary_conditions.append({
            "role": "inlet",
            "type": "dirichlet",
            "faces": [synthesized_id],
            "apply_to": ["velocity", "pressure"],
            "comment": "Synthesized Far-Field Inlet (boundary of the computational box)",
            "velocity": velocity,
            "pressure": int(pressure),
            "apply_faces": [inlet_label]
        })
        if debug:
            print(f"[DEBUG_FLOW] Added synthesized Inlet (ID {synthesized_id}) with label {inlet_label}")
        synthesized_id -= 1

        # Outlet (e.g., x_max in positive X flow)
        outlet_label = f"{axis_label}_max" if is_positive_flow else f"{axis_label}_min"
        
        boundary_conditions.append({
            "role": "outlet",
            "type": "neumann",
            "faces": [synthesized_id],
            "apply_to": ["pressure"],
            "comment": "Synthesized Far-Field Outlet (boundary of the computational box)",
            "apply_faces": [outlet_label]
        })
        if debug:
            print(f"[DEBUG_FLOW] Added synthesized Outlet (ID {synthesized_id}) with label {outlet_label}")
        synthesized_id -= 1

        # --- Synthesize Far-Field Walls (Symmetry/Slip Walls) - SEPARATED BLOCKS (as agreed) ---
        
        for label in perpendicular_axes:
            # Create a separate block for each far-field face
            boundary_conditions.append({
                "role": "wall", 
                "type": "dirichlet", 
                "faces": [synthesized_id], 
                "apply_to": ["velocity"],
                "comment": f"Synthesized Far-Field Wall ({label})",
                "velocity": [0.0, 0.0, 0.0],
                "no_slip": no_slip, 
                "apply_faces": [label]
            })
            if debug:
                print(f"[DEBUG_FLOW] Added synthesized Far-Field Wall (ID {synthesized_id}) with label {label}")
            synthesized_id -= 1 


    if debug:
        print("[DEBUG] Final boundary condition blocks:")
        for b in boundary_conditions:
            print(b)

    return boundary_conditions



