# src/boundary_conditions.py

import gmsh
import math
import numpy as np
from .bc_generators import generate_internal_bc_blocks, generate_external_bc_blocks

GMSH_TAG_TO_ROLE = {
    1: ("inlet", "x_min"),
    2: ("outlet", "x_max"),
    3: ("wall", "wall")
}

def is_surface_aligned(x_coords, anchor_x, tolerance=1e-6, threshold=0.9):
    count_aligned = sum(abs(x - anchor_x) < tolerance for x in x_coords)
    ratio = count_aligned / len(x_coords)
    return ratio >= threshold, ratio

def generate_boundary_conditions(step_path, velocity, pressure, no_slip, flow_region,
                                 padding_factor=0, resolution=None, gmsh_fix_script_path=None,
                                 debug=False, threshold=0.9, tolerance=1e-6):

    gmsh.open(step_path)
    if debug:
        print(f"[DEBUG] Opened STEP file: {step_path}")

    if gmsh_fix_script_path:
        if debug:
            print(f"[DEBUG] Merging GMSH boundary fix script: {gmsh_fix_script_path}")
        gmsh.merge(gmsh_fix_script_path)

    if resolution:
        gmsh.option.setNumber("Mesh.CharacteristicLengthMin", resolution)
        gmsh.option.setNumber("Mesh.CharacteristicLengthMax", resolution)
        if debug:
            print(f"[DEBUG] Mesh resolution set to: {resolution}")

    gmsh.model.mesh.generate(3)
    if debug:
        print("[DEBUG] 3D mesh generated")

    dim = 2
    surfaces = gmsh.model.getEntities(dim)
    if debug:
        print(f"[DEBUG] Extracted {len(surfaces)} surface entities")

    vmag = math.sqrt(sum(v**2 for v in velocity))
    if vmag == 0:
        raise ValueError("Initial velocity vector cannot be zero.")
    [v / vmag for v in velocity]

    axial_velocity_component = max(abs(v) for v in velocity)
    try:
        axis_index = velocity.index(axial_velocity_component)
    except ValueError:
        try:
            axis_index = velocity.index(-axial_velocity_component)
        except ValueError:
            axis_index = max(range(3), key=lambda i: abs(velocity[i]))

    axis_label = ["x", "y", "z"][axis_index]
    is_positive_flow = velocity[axis_index] > 0

    if debug:
        print(f"[DEBUG] Determined dominant flow axis: {axis_label}, positive direction: {is_positive_flow}")

    bounds = gmsh.model.getBoundingBox(3, 1)
    if len(bounds) == 7:
        _, x_min, y_min, z_min, x_max, y_max, z_max = bounds
    else:
        x_min, y_min, z_min, x_max, y_max, z_max = bounds if len(bounds) == 6 else [-1e9] * 3 + [1e9] * 3

    min_bounds = [x_min, y_min, z_min]
    max_bounds = [x_max, y_max, z_max]

    face_roles = {}
    face_geometry_data = {}

    for surface in surfaces:
        face_id = surface[1]
        try:
            node_tags, node_coords, _ = gmsh.model.mesh.getNodes(dim, face_id)
            coords = node_coords.reshape(-1, 3)
            x_coords = coords[:, 0]
        except Exception:
            x_coords = np.array([])

        role = "wall"
        label = "wall"
        alignment_result = None

        if x_coords.size > 0:
            is_inlet, ratio_inlet = is_surface_aligned(x_coords, x_min, tolerance, threshold)
            is_outlet, ratio_outlet = is_surface_aligned(x_coords, x_max, tolerance, threshold)

            if is_inlet:
                role, label = "inlet", "x_min"
                alignment_result = ratio_inlet
            elif is_outlet:
                role, label = "outlet", "x_max"
                alignment_result = ratio_outlet

            if debug and alignment_result and 0.85 <= alignment_result < threshold:
                print(f"[DEBUG] Surface {face_id} borderline match ({alignment_result:.2f}) for {role}")

        face_roles[face_id] = (role, label)

        p_centroid = [0, 0, 0]
        if x_coords.size > 0:
            p_centroid = np.mean(coords, axis=0).tolist()

        face_geometry_data[face_id] = {
            "normal_unit": [0, 0, 0],
            "face_label": label,
            "max_index": 0,
            "p_centroid": p_centroid
        }

    boundary_conditions = []

    if flow_region == "internal":
        boundary_conditions = generate_internal_bc_blocks(
            surfaces, face_geometry_data, face_roles, velocity, pressure,
            no_slip, axis_index, is_positive_flow, min_bounds, max_bounds, debug
        )
    elif flow_region == "external":
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



