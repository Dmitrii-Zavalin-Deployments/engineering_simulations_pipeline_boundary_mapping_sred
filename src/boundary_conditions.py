import gmsh
import math

def generate_boundary_conditions(step_path, velocity, pressure, no_slip, flow_region, resolution=None, debug=False):
    gmsh.open(step_path)

    # Extract all faces from the geometry
    dim = 2  # surface dimension
    surfaces = gmsh.model.getEntities(dim)
    boundary_conditions = []

    # Normalize velocity vector
    vmag = math.sqrt(sum(v**2 for v in velocity))
    if vmag == 0:
        raise ValueError("Initial velocity vector cannot be zero.")
    velocity_unit = [v / vmag for v in velocity]

    for tag in surfaces:
        face_id = tag[1]
        normal = gmsh.model.getNormal(dim, face_id)
        if not normal or len(normal) != 3:
            continue

        # Normalize face normal
        nmag = math.sqrt(sum(n**2 for n in normal))
        if nmag == 0:
            continue
        normal_unit = [n / nmag for n in normal]

        # Dot product to classify
        dot = sum(v * n for v, n in zip(velocity_unit, normal_unit))
        role = "wall"
        if dot > 0.95:
            role = "inlet"
        elif dot < -0.95:
            role = "outlet"

        # Determine face label
        face_label = classify_face_label(normal_unit)

        block = {
            "role": role,
            "type": "dirichlet" if role in ["inlet", "wall"] else "neumann",
            "apply_faces": [face_label] if face_label else [],
            "faces": [face_id],
            "apply_to": ["velocity", "pressure"] if role == "inlet" else ["pressure"] if role == "outlet" else ["velocity"],
            "velocity": velocity if role in ["inlet", "wall"] else None,
            "pressure": pressure if role == "inlet" else None,
            "no_slip": no_slip if role == "wall" else None,
            "comment": f"{role.capitalize()} face aligned with normal {normal_unit}"
        }

        # Remove unused fields
        if block["velocity"] is None:
            del block["velocity"]
        if block["pressure"] is None:
            del block["pressure"]
        if block["no_slip"] is None:
            del block["no_slip"]

        boundary_conditions.append(block)

    if debug:
        print("[DEBUG] Boundary condition blocks:")
        for b in boundary_conditions:
            print(b)

    return boundary_conditions

def classify_face_label(normal):
    # Heuristic mapping based on axis alignment
    axis = ["x", "y", "z"]
    max_index = max(range(3), key=lambda i: abs(normal[i]))
    direction = "min" if normal[max_index] < 0 else "max"
    return f"{axis[max_index]}_{direction}"



