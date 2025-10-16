# src/boundary_conditions.py

import gmsh
import numpy as np
from .bc_generators import (
    generate_internal_bc_blocks,
    generate_external_bc_blocks
)

def load_geometry(step_path, debug=False):
    gmsh.initialize()
    gmsh.model.add("boundary_model")
    gmsh.open(step_path)
    if debug:
        print(f"[DEBUG] Loaded STEP geometry from: {step_path}")

def generate_mesh(resolution=None, debug=False):
    if resolution is not None:
        gmsh.option.setNumber("Mesh.CharacteristicLengthMin", resolution)
        gmsh.option.setNumber("Mesh.CharacteristicLengthMax", resolution)
        if debug:
            print(f"[DEBUG] Mesh resolution set to: {resolution}")
    gmsh.model.mesh.generate(3)
    if debug:
        print("[DEBUG] 3D mesh generated")

def get_surface_faces(debug=False):
    surfaces = gmsh.model.getEntities(2)
    if debug:
        print(f"[DEBUG] Extracted {len(surfaces)} surface entities")
    return surfaces

def get_x_bounds(debug=False):
    bounds = gmsh.model.getBoundingBox(3, 1)
    if len(bounds) == 7:
        _, x_min, _, _, x_max, _, _ = bounds
    else:
        x_min, _, _, x_max, _, _ = bounds if len(bounds) == 6 else [-1e9, 0, 0, 1e9, 0, 0]
    if debug:
        print(f"[DEBUG] Bounding box X-range: x_min={x_min}, x_max={x_max}")
    return x_min, x_max

def generate_boundary_conditions(step_path, velocity, pressure, no_slip, flow_region,
                                 padding_factor=0, resolution=None,
                                 threshold=0.9, tolerance=1e-6, debug=False):
    load_geometry(step_path, debug)
    generate_mesh(resolution, debug)
    surfaces = get_surface_faces(debug)
    x_min, x_max = get_x_bounds(debug)

    axis_index = max(range(3), key=lambda i: abs(velocity[i]))
    is_positive_flow = velocity[axis_index] > 0
    axis_label = ["x", "y", "z"][axis_index]

    bbox = gmsh.model.getBoundingBox(3, 1)
    min_bounds = [bbox[0], bbox[1], bbox[2]]
    max_bounds = [bbox[3], bbox[4], bbox[5]]
    x_span = abs(x_max - x_min)

    face_roles = {}
    face_geometry_data = {}
    TOL = tolerance

    for dim, face_id in surfaces:
        try:
            _, node_coords, _ = gmsh.model.mesh.getNodes(dim, face_id)
            coords = node_coords.reshape(-1, 3)
        except Exception:
            if debug:
                print(f"[DEBUG] Face {face_id}: Failed to retrieve node data.")
            continue

        if coords.shape[0] < 3:
            if debug:
                print(f"[DEBUG] Face {face_id}: Skipped due to insufficient nodes.")
            continue

        centroid = np.mean(coords, axis=0).tolist()
        face_geometry_data[face_id] = {
            "p_centroid": centroid
        }

        x = centroid[0]
        ratio_min = abs(x - x_min) / x_span if x_span > 0 else 1.0
        ratio_max = abs(x - x_max) / x_span if x_span > 0 else 1.0

        if flow_region == "internal":
            if ratio_min < (1 - threshold):
                role = "inlet"
            elif ratio_max < (1 - threshold):
                role = "outlet"
            else:
                is_min_on_any_axis = any(abs(centroid[i] - min_bounds[i]) < TOL for i in range(3))
                is_max_on_any_axis = any(abs(centroid[i] - max_bounds[i]) < TOL for i in range(3))
                is_on_bounding_plane = is_min_on_any_axis or is_max_on_any_axis
                role = "skip" if is_on_bounding_plane else "wall"
        else:
            role = "wall"

        face_roles[face_id] = (role, "wall")

        if debug:
            print(f"[DEBUG] Face {face_id}: Centroid X = {x:.6f}, ratio_min = {ratio_min:.4f}, ratio_max = {ratio_max:.4f}, role = {role}")

    if flow_region == "internal":
        return generate_internal_bc_blocks(
            surfaces, face_geometry_data, face_roles, velocity, pressure,
            no_slip, axis_index, is_positive_flow, min_bounds, max_bounds, threshold, debug
        )

    # --- External Flow Handling ---
    boundary_conditions = []

    # Force all geometric faces to wall
    for face_id in face_roles:
        face_roles[face_id] = ("wall", "wall")

    obstacle_blocks = generate_external_bc_blocks(
        surfaces, face_roles, velocity, pressure,
        no_slip, axis_index, is_positive_flow, debug
    )
    boundary_conditions.extend(obstacle_blocks)

    # --- Synthesize Far-Field Boundaries ---
    if debug:
        print("[DEBUG_FLOW] Synthesizing external domain boundaries...")

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

    # --- Skipping Far-Field Walls ---
    if debug:
        print("[DEBUG_FLOW] Skipping synthesized far-field walls (y/z planes) for external flow.")

    return boundary_conditions



