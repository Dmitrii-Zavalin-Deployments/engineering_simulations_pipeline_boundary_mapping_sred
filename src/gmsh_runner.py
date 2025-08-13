# src/gmsh_runner.py

# -------------------------------------------------------------------
# Gmsh-based geometry processor for STEP domain extraction pipeline
# -------------------------------------------------------------------

try:
    import gmsh
except ImportError:
    raise RuntimeError("Gmsh module not found. Run: pip install gmsh==4.11.1")

import json
import os
import numpy as np

# ✅ Import volume integrity checker
from src.utils.gmsh_input_check import validate_step_has_volumes
# ✅ Import fallback resolution profile loader
from src.utils.input_validation import load_resolution_profile
# ✅ Import face classifier
from src.bbox_classifier import classify_faces


def extract_bounding_box_with_gmsh(step_path, resolution=None):
    """
    Parses STEP geometry with Gmsh and returns domain_definition
    including bounding box, grid resolution, and boundary conditions.

    Parameters:
        step_path (str or Path): Path to STEP file
        resolution (float or None): Grid resolution in meters. If None, fallback profile will be used.

    Returns:
        dict: {"domain_definition": {...}} matching schema
    """
    if not os.path.isfile(step_path):
        raise FileNotFoundError(f"STEP file not found: {step_path}")

    if resolution is None:
        try:
            profile = load_resolution_profile()
            resolution = profile.get("default_resolution", {}).get("dx", 0.01)
        except Exception:
            resolution = 0.01

    gmsh.initialize()
    try:
        gmsh.model.add("domain_model")
        gmsh.logger.start()

        validate_step_has_volumes(step_path)

        gmsh.open(str(step_path))

        volumes = gmsh.model.getEntities(3)
        entity_tag = volumes[0][1]

        min_x, min_y, min_z, max_x, max_y, max_z = gmsh.model.getBoundingBox(3, entity_tag)

        if (max_x - min_x) <= 0 or (max_y - min_y) <= 0 or (max_z - min_z) <= 0:
            raise ValueError("Invalid geometry: bounding box has zero size.")

        nx = max(1, int((max_x - min_x) / resolution))
        ny = max(1, int((max_y - min_y) / resolution))
        nz = max(1, int((max_z - min_z) / resolution))

        # ✅ Extract surface faces and vertices with validation
        faces = []
        surface_entities = gmsh.model.getEntities(2)
        for dim, tag in surface_entities:
            node_data = gmsh.model.mesh.getNodes(dim, tag)
            coords_raw = node_data[1] if node_data else []
            if coords_raw is not None and len(coords_raw) >= 9:
                try:
                    coords = coords_raw.reshape(-1, 3)
                    face_vertices = coords.tolist()
                    faces.append({"id": tag, "vertices": face_vertices})
                except Exception:
                    continue
            else:
                continue

        # ✅ Classify face directions
        bc_raw = classify_faces(faces)
        bc = bc_raw.get("boundary_conditions", {})

        # 🧩 Ensure all required boundary condition fields exist
        boundary_conditions = {
            "x_min": bc.get("x_min", "none"),
            "x_max": bc.get("x_max", "none"),
            "y_min": bc.get("y_min", "none"),
            "y_max": bc.get("y_max", "none"),
            "z_min": bc.get("z_min", "none"),
            "z_max": bc.get("z_max", "none"),
            "faces": bc.get("faces", []),
            "type": bc.get("type", "dirichlet"),
            "apply_faces": bc.get("apply_faces", []),
            "apply_to": bc.get("apply_to", ["pressure"]),
            "pressure": bc.get("pressure", 0.0),
            "velocity": bc.get("velocity", [0.0, 0.0, 0.0]),
            "no_slip": bc.get("no_slip", False)
        }

        return {
            "domain_definition": {
                "min_x": min_x,
                "max_x": max_x,
                "min_y": min_y,
                "max_y": max_y,
                "min_z": min_z,
                "max_z": max_z,
                "nx": nx,
                "ny": ny,
                "nz": nz,
                "boundary_conditions": boundary_conditions
            }
        }
    finally:
        gmsh.finalize()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Gmsh STEP parser for domain metadata")
    parser.add_argument("--step", type=str, required=True, help="Path to STEP file")
    parser.add_argument("--resolution", type=float, help="Grid resolution in meters")
    parser.add_argument("--output", type=str, help="Path to write domain JSON")

    args = parser.parse_args()

    result = extract_bounding_box_with_gmsh(args.step, resolution=args.resolution)

    print(json.dumps(result, indent=2))

    if args.output:
        with open(args.output, "w") as f:
            json.dump(result, f, indent=2)



