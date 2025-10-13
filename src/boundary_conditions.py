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

    for tag in surfaces:
        face_id = tag[1]
        if debug:
            print(f"[DEBUG] Processing face ID: {face_id}")

        try:
            node_tags, node_coords, _ = gmsh.model.mesh.getNodes(dim, face_id)
            if debug:
                print(f"[DEBUG] Retrieved {len(node_tags)} nodes for face {face_id}")
        except Exception as e:
            if debug:
                print(f"[DEBUG] Failed to get nodes for face {face_id}: {e}")
            continue

        if len(node_coords) < 9:
            if debug:
                print(f"[DEBUG] Skipping face {face_id}: insufficient node coordinates")
            continue

        p1 = np.array(node_coords[0:3])
        p2 = np.array(node_coords[3:6])
        p3 = np.array(node_coords[6:9])
        v1 = p2 - p1
        v2 = p3 - p1
        normal = np.cross(v1, v2)
        nmag = np.linalg.norm(normal)
        if nmag == 0:
            if debug:
                print(f"[DEBUG] Skipping face {face_id}: degenerate normal")
            continue
        normal_unit = (normal / nmag).tolist()
        if debug:
            print(f"[DEBUG] Computed normal for face {face_id}: {normal_unit}")

        dot = sum(v * n for v, n in zip(velocity_unit, normal_unit))
        role = "wall"
        if dot > 0.95:
            role = "inlet"
        elif dot < -0.95:
            role = "outlet"
        if debug:
            print(f"[DEBUG] Classified face {face_id} as: {role}")

        face_label = classify_face_label(normal_unit)
        if debug:
            print(f"[DEBUG] Assigned face label: {face_label}")

        block = {
            "role": role,
            "type": "dirichlet" if role in ["inlet", "wall"] else "neumann",
            "apply_faces": [face_label] if face_label else [],
            "faces": [face_id],
            "apply_to": ["velocity", "pressure"] if role == "inlet" else ["pressure"] if role == "outlet" else ["velocity"],
            "velocity": velocity if role in ["inlet", "wall"] else None,
            "pressure": pressure if role == "inlet" else None,
            "no_slip": no_slip if role == "wall" else None,
            "comment": f"Defines {role} flow parameters based on face normal"
        }

        if block["velocity"] is None:
            del block["velocity"]
        if block["pressure"] is None:
            del block["pressure"]
        if block["no_slip"] is None:
            del block["no_slip"]

        boundary_conditions.append(block)
        if debug:
            print(f"[DEBUG] Appended boundary block for face {face_id}: {block}")

    # ✅ Fallback logic for solid internal flow
    has_inlet = any(b["role"] == "inlet" for b in boundary_conditions)
    has_outlet = any(b["role"] == "outlet" for b in boundary_conditions)

    if flow_region == "internal" and not has_inlet and not has_outlet:
        if debug:
            print("[DEBUG] No inlet/outlet detected — applying fallback for solid internal flow")

        inlet_label = "x_min"
        outlet_label = "x_max"

        for tag in surfaces:
            face_id = tag[1]
            node_tags, node_coords, _ = gmsh.model.mesh.getNodes(dim, face_id)
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

            if face_label == inlet_label:
                boundary_conditions.append({
                    "role": "inlet",
                    "type": "dirichlet",
                    "apply_faces": [inlet_label],
                    "faces": [face_id],
                    "apply_to": ["velocity", "pressure"],
                    "velocity": velocity,
                    "pressure": pressure,
                    "comment": "Defines inlet flow parameters for velocity and pressure"
                })
            elif face_label == outlet_label:
                boundary_conditions.append({
                    "role": "outlet",
                    "type": "neumann",
                    "apply_faces": [outlet_label],
                    "faces": [face_id],
                    "apply_to": ["pressure"],
                    "comment": "Defines outlet flow behavior with pressure gradient"
                })
            else:
                boundary_conditions.append({
                    "role": "wall",
                    "type": "dirichlet",
                    "apply_faces": [],
                    "faces": [face_id],
                    "apply_to": ["velocity"],
                    "velocity": [0.0, 0.0, 0.0],
                    "no_slip": no_slip,
                    "comment": "Defines near-wall flow parameters with no-slip condition"
                })

    if debug:
        print("[DEBUG] Final boundary condition blocks:")
        for b in boundary_conditions:
            print(b)

    return boundary_conditions

def classify_face_label(normal):
    axis = ["x", "y", "z"]
    max_index = max(range(3), key=lambda i: abs(normal[i]))
    direction = "min" if normal[max_index] < 0 else "max"
    return f"{axis[max_index]}_{direction}"



