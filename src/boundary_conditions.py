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

        if dot > 0.95:
            face_roles[face_id] = ("inlet", face_label)
        elif dot < -0.95:
            face_roles[face_id] = ("outlet", face_label)
        else:
            face_roles[face_id] = ("wall", None)

    # ✅ Always enforce fallback for internal flow
    if flow_region == "internal":
        if debug:
            print("[DEBUG] Enforcing fallback inlet/outlet roles for internal flow")

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

            if debug:
                print(f"[DEBUG] Face {face_id} normal: {normal_unit} → label: {face_label}")

            if face_label == "x_min":
                face_roles[face_id] = ("inlet", "x_min")
                if debug:
                    print(f"[DEBUG] Fallback assigned inlet to face {face_id} (x_min)")
            elif face_label == "x_max":
                face_roles[face_id] = ("outlet", "x_max")
                if debug:
                    print(f"[DEBUG] Fallback assigned outlet to face {face_id} (x_max)")
            else:
                face_roles[face_id] = ("wall", None)

    for tag in surfaces:
        face_id = tag[1]
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
            block["pressure"] = int(pressure)
            block["apply_faces"] = [face_label] if face_label else []
        elif role == "wall":
            block["velocity"] = [0.0, 0.0, 0.0]
            block["no_slip"] = no_slip

        boundary_conditions.append(block)
        if debug:
            print(f"[DEBUG] Appended boundary block for face {face_id}: {block}")

    if debug:
        print("[DEBUG] Final boundary condition blocks:")
        for b in boundary_conditions:
            print(b)

    return boundary_conditions

def classify_face_label(normal):
    axis = ["x", "y", "z"]
    max_index = max(range(3), key=lambda i: abs(normal[i]))
    direction = "max" if normal[max_index] < 0 else "min"  # ✅ Flipped logic
    return f"{axis[max_index]}_{direction}"



