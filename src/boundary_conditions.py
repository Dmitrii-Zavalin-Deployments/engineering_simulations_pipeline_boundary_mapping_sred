# src/boundary_conditions.py

import gmsh
import math
import numpy as np
from .geometry import classify_face_label
from .bc_generators import generate_internal_bc_blocks, generate_external_bc_blocks

def generate_boundary_conditions(step_path, velocity, pressure, no_slip, flow_region, padding_factor=0, resolution=None, debug=False):
    gmsh.open(step_path)
    if debug:
        print(f"[DEBUG] Opened STEP file: {step_path}")

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

    # 2. Flow and Axis Determination
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
            axis_index = 0 
            
    axis_label = ["x", "y", "z"][axis_index]
    is_positive_flow = velocity[axis_index] > 0

    if debug:
        print(f"[DEBUG] Determined dominant flow axis: {axis_label}, positive direction: {is_positive_flow}")

    # 3. Geometric Data Pre-processing
    face_roles = {}
    face_geometry_data = {}
    
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
        normal = np.cross(p2 - p1, p3 - p1)
        nmag = np.linalg.norm(normal)
        if nmag == 0:
            continue
            
        normal_unit = (normal / nmag).tolist()
        face_label = classify_face_label(normal_unit, face_id, debug)
        max_index = max(range(3), key=lambda i: abs(normal_unit[i]))
        
        face_geometry_data[face_id] = {
            "normal_unit": normal_unit,
            "face_label": face_label,
            "max_index": max_index,
            "p_centroid": np.mean(node_coords.reshape(-1, 3), axis=0).tolist()
        }
        
        # Initial role assignment (will be overridden)
        dot = sum(v * n for v, n in zip(velocity_unit, normal_unit))
        if dot < -0.95:
            face_roles[face_id] = ("inlet", face_label)
        elif dot > 0.95:
            face_roles[face_id] = ("outlet", face_label)
        else:
            face_roles[face_id] = ("wall", face_label)

    # 4. Bounding Box Setup
    bounds = gmsh.model.getBoundingBox(3, 1)
    # [Handle bounds extraction as before]
    if len(bounds) == 7:
        _, x_min, y_min, z_min, x_max, y_max, z_max = bounds
    else:
        x_min, y_min, z_min, x_max, y_max, z_max = bounds if len(bounds) == 6 else [-1e9] * 3 + [1e9] * 3
        
    min_bounds = [x_min, y_min, z_min]
    max_bounds = [x_max, y_max, z_max]
    TOL = 1e-4 # Tolerance moved to bc_generators

    # 5. Delegate to Flow-Specific Generator
    boundary_conditions = []
    
    if flow_region == "internal":
        boundary_conditions = generate_internal_bc_blocks(
            surfaces, face_geometry_data, face_roles, velocity, pressure, 
            no_slip, axis_index, is_positive_flow, min_bounds, max_bounds, debug
        )
    elif flow_region == "external":
        # Force all geometric faces to "wall" BEFORE passing to generator
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



