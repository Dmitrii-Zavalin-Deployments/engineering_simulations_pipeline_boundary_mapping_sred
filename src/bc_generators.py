# src/bc_generators.py

# Placeholder for complex data structure types, usually passed in kwargs
TOL = 1000 # Re-define tolerance for local use

def generate_internal_bc_blocks(surfaces, face_geometry_data, face_roles, velocity, pressure, no_slip, axis_index, is_positive_flow, min_bounds, max_bounds, debug):
    """Generates boundary condition blocks for internal flow, grouping faces."""
    
    boundary_conditions = []
    grouped_blocks = {}
    
    # axis_label = ["x", "y", "z"][axis_index] # Not used, commented out
    
    # 1. Recalculate/Override Roles based on bounds (Logic extracted from main function)
    for face_id, data in face_geometry_data.items():
        face_label = data["face_label"]
        face_axis_index = data["max_index"]
        face_axis_label = ["x", "y", "z"][face_axis_index]
        coord_val = data["p_centroid"][face_axis_index]

        min_bound = min_bounds[face_axis_index]
        max_bound = max_bounds[face_axis_index]

        role = "wall" # Default assumption
        face_label_fixed = "wall" 

        # The bounding plane checks below are sufficient for role assignment
        is_min_bound_face = abs(coord_val - min_bound) < TOL
        is_max_bound_face = abs(coord_val - max_bound) < TOL

        # -----------------------------------------------------------
        # CORRECTED Role Assignment Logic
        # -----------------------------------------------------------

        if face_axis_index == axis_index:
            # This face is aligned with the flow axis (e.g., X_min, X_max if flow is X)
            if is_min_bound_face:
                # If flow is positive (+X), INLET is at X_min. If flow is negative (-X), OUTLET is at X_min.
                role = "inlet" if is_positive_flow else "outlet"
                face_label_fixed = f"{face_axis_label}_min"
            elif is_max_bound_face:
                # If flow is positive (+X), OUTLET is at X_max. If flow is negative (-X), INLET is at X_max.
                role = "outlet" if is_positive_flow else "inlet"
                face_label_fixed = f"{face_axis_label}_max"
            else:
                # Internal wall feature oriented on the flow axis (e.g., a cap or internal vertical segment)
                role = "wall"
                face_label_fixed = "wall" # Grouped with other internal walls
        
        elif is_min_bound_face or is_max_bound_face:
            # This face is on a perpendicular bounding plane (e.g., Y_min, Z_max faces on the box boundary)
            # In internal flow, these bounding box faces should typically be SKIPPED
            # as the flow is enclosed by the internal geometry walls.
            role = "skip"
            face_label_fixed = "skip" 

        else:
            # All other faces are interior walls, curved surfaces, or features not on the bounding box.
            role = "wall"
            face_label_fixed = "wall" 
        
        # Final assignment
        face_roles[face_id] = (role, face_label_fixed)
    # End of Role Override

    # 2. Group faces and build blocks
    for tag in surfaces:
        face_id = tag[1]
        # face_label now holds the correct geometric identifier (e.g., 'x_min') or 'wall' or 'skip'
        role, face_label = face_roles.get(face_id, ("wall", "wall")) 

        if role == "skip":
            if debug:
                 print(f"[DEBUG] Skipping face {face_id} with role 'skip'")
            continue
            
        group_key = (role, face_label)
        
        if group_key not in grouped_blocks:
            block = {
                "role": role,
                "type": "dirichlet" if role in ["inlet", "wall"] else "neumann",
                "faces": [face_id],
                # Outlet only applies to pressure (Neumann). Inlet applies to velocity/pressure (Dirichlet).
                "apply_to": ["velocity", "pressure"] if role == "inlet" else ["pressure"] if role == "outlet" else ["velocity"],
                "comment": {
                    "inlet": "Defines inlet flow parameters for velocity and pressure",
                    "outlet": "Defines outlet flow behavior with pressure gradient",
                    "wall": "Defines near-wall flow parameters with no-slip condition"
                }.get(role, "Boundary condition defined by flow logic")
            }
            
            # Use face_label for apply_faces, which will be 'x_min', 'x_max' for Inlet/Outlet, 
            # and 'wall' for internal walls.
            apply_faces_list = []
            if face_label in ["x_min", "x_max", "y_min", "y_max", "z_min", "z_max"]:
                apply_faces_list = [face_label]
            elif role == "wall" and face_label == "wall":
                apply_faces_list = ["wall"]
            else:
                # Fallback, should not happen with corrected logic
                apply_faces_list = ["wall"] 

            if role == "inlet":
                block["velocity"] = velocity
                block["pressure"] = int(pressure)
            elif role == "outlet":
                # apply_to is already set to ["pressure"] above
                pass 
            elif role == "wall":
                block["velocity"] = [0.0, 0.0, 0.0]
                block["no_slip"] = no_slip
            
            block["apply_faces"] = apply_faces_list
            grouped_blocks[group_key] = block
            
        else:
            grouped_blocks[group_key]["faces"].append(face_id)
            if debug:
                print(f"[DEBUG] Grouped face {face_id} into existing block with key {group_key}")

    boundary_conditions.extend(list(grouped_blocks.values()))
    return boundary_conditions


def generate_external_bc_blocks(surfaces, face_roles, velocity, pressure, no_slip, axis_index, is_positive_flow, debug):
    """Generates boundary condition blocks for external flow, synthesizing far-field."""
    
    boundary_conditions = []
    
    # 1. Real Faces (Obstacle Walls)
    for tag in surfaces:
        face_id = tag[1]
        role, _ = face_roles.get(face_id, ("wall", "wall")) 

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
            "apply_faces": ["wall"]
        }
        boundary_conditions.append(block)


    # 2. Synthesize FAR-FIELD Boundaries 
    if debug:
        print("[DEBUG_FLOW] Synthesizing external domain boundaries...")

    axis_label = ["x", "y", "z"][axis_index]
    
    # Define labels perpendicular to the flow axis
    perpendicular_axes = [
        f"{a}_{d}" 
        for i, a in enumerate(["x", "y", "z"]) 
        for d in ["min", "max"] 
        if i != axis_index
    ]

    synthesized_id = -1

    # Inlet
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

    # Outlet
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

    # Far-Field Walls
    for label in perpendicular_axes:
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
        
    return boundary_conditions



