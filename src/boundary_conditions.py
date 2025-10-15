import gmsh
import math
import numpy as np
# Removed the dependency on classify_face_label since classification is now tag-based
from .bc_generators import generate_internal_bc_blocks, generate_external_bc_blocks

# GMSH Physical Tag definitions from src/gmsh_boundary_fix.geo
GMSH_TAG_TO_ROLE = {
    1: ("inlet", "x_min"),  # Physical Surface(1) is Inlet
    2: ("outlet", "x_max"), # Physical Surface(2) is Outlet
    3: ("wall", "wall")      # Physical Surface(3) is Wall
}

def generate_boundary_conditions(step_path, velocity, pressure, no_slip, flow_region, padding_factor=0, resolution=None, gmsh_fix_script_path=None, debug=False):
    # 🆕 Accept the new argument
    
    gmsh.open(step_path)
    if debug:
        print(f"[DEBUG] Opened STEP file: {step_path}")

    # 🆕 Execute the robust boundary assignment script
    if gmsh_fix_script_path:
        if debug:
            print(f"[DEBUG] Merging GMSH boundary fix script: {gmsh_fix_script_path}")
        gmsh.merge(gmsh_fix_script_path)
    
    # 1. Mesh Setup
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

    # 2. Flow and Axis Determination (Necessary for downstream BC blocks and model analysis)
    vmag = math.sqrt(sum(v**2 for v in velocity))
    if vmag == 0:
        raise ValueError("Initial velocity vector cannot be zero.")
    velocity_unit = [v / vmag for v in velocity]

    axial_velocity_component = max(abs(v) for v in velocity)
    try:
        axis_index = velocity.index(axial_velocity_component)
    except ValueError:
        try:
            axis_index = velocity.index(-axial_velocity_component)
        except ValueError:
            # Fallback if magnitude is used for classification
            axis_index = max(range(3), key=lambda i: abs(velocity[i]))
            
    axis_label = ["x", "y", "z"][axis_index]
    is_positive_flow = velocity[axis_index] > 0

    if debug:
        print(f"[DEBUG] Determined dominant flow axis: {axis_label}, positive direction: {is_positive_flow}")

    # 3. Robust Tag-Based Geometric Data Pre-processing
    # ❗ Replacing the old, unstable normal vector calculation logic
    face_roles = {}
    face_geometry_data = {}
    
    # Iterate through the stable Physical Tags defined in the GMSH fix script
    for tag_id, (role, label) in GMSH_TAG_TO_ROLE.items():
        try:
            surfaces_in_group = gmsh.model.getEntitiesForPhysicalGroup(dim, tag_id)
        except Exception as e:
            # Handle case where a Physical Group might not have been created (e.g., missing wall)
            if debug:
                 print(f"[DEBUG] Could not find Physical Group {tag_id} ({role}). Skipping. Error: {e}")
            continue

        if debug:
            print(f"[DEBUG] Physical Tag {tag_id} ({role}): {len(surfaces_in_group)} surfaces assigned.")
            
        for face_id in surfaces_in_group:
            # 🆕 The face role and label are now assigned based on the stable tag ID
            face_roles[face_id] = (role, label)

            # Gather minimal geometry data required by downstream generators (e.g., centroid)
            p_centroid = [0, 0, 0]
            try:
                node_tags, node_coords, _ = gmsh.model.mesh.getNodes(dim, face_id)
                if node_coords.size > 0:
                    p_centroid = np.mean(node_coords.reshape(-1, 3), axis=0).tolist()
            except Exception:
                pass # Centroid fallback is [0, 0, 0]

            face_geometry_data[face_id] = {
                # Normal and max_index are now placeholders, as they are no longer used for classification
                "normal_unit": [0, 0, 0], 
                "face_label": label,
                "max_index": 0, 
                "p_centroid": p_centroid
            }

    # 4. Bounding Box Setup
    # Bounds calculation remains useful for defining the overall simulation domain size
    bounds = gmsh.model.getBoundingBox(3, 1)
    if len(bounds) == 7:
        _, x_min, y_min, z_min, x_max, y_max, z_max = bounds
    else:
        # Fallback for internal geometry extraction
        x_min, y_min, z_min, x_max, y_max, z_max = bounds if len(bounds) == 6 else [-1e9] * 3 + [1e9] * 3
        
    min_bounds = [x_min, y_min, z_min]
    max_bounds = [x_max, y_max, z_max]
    TOL = 1e-4 # Tolerance moved to bc_generators

    # 5. Delegate to Flow-Specific Generator
    # ❗ Ensure all surfaces have a role before passing them to the generator
    if len(face_roles) != len(surfaces):
        unassigned_faces = [s[1] for s in surfaces if s[1] not in face_roles]
        if debug:
             print(f"[WARN] {len(unassigned_faces)} surface(s) were not assigned a Physical Tag. Forcing role='wall'.")
        for face_id in unassigned_faces:
             face_roles[face_id] = ("wall", "wall")

    boundary_conditions = []
    
    if flow_region == "internal":
        boundary_conditions = generate_internal_bc_blocks(
            surfaces, face_geometry_data, face_roles, velocity, pressure, 
            no_slip, axis_index, is_positive_flow, min_bounds, max_bounds, debug
        )
    elif flow_region == "external":
        # Force all geometric faces to "wall" BEFORE passing to generator
        # This is primarily for external flow boundary box setup later
        for face_id in face_roles:
            face_roles[face_id] = ("wall", "wall") 
            
        if padding_factor > 0 and resolution is not None and debug:
            pad = padding_factor * resolution
            print(f"[DEBUG] Computational box bounds (Padded): min=({x_min - pad:.3f}, {y_min - pad:.3f}, {z_min - pad:.3f}), max=({x_max + pad:.3f}, {y_max + pad:.3f}, {z_max + pad:.3f})")

        boundary_conditions = generate_external_bc_blocks(
            surfaces, face_roles, velocity, pressure, no_slip, axis_index, is_positive_flow, debug
        )


    if debug:
        print("[DEBUG] Final boundary condition blocks:")
        for b in boundary_conditions:
            print(b)

    return boundary_conditions



