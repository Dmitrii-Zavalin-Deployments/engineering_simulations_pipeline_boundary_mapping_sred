# src/gmsh_runner.py

# -------------------------------------------------------------------
# Gmsh-based geometry processor for STEP domain boundary condition extraction
# -------------------------------------------------------------------

try:
    import gmsh
except ImportError:
    raise RuntimeError("Gmsh module not found. Run: pip install gmsh==4.11.1")

import json
import os
import numpy as np

from src.utils.gmsh_input_check import validate_step_has_volumes
from src.utils.input_validation import load_resolution_profile
from src.bbox_classifier import classify_faces
from src.schema_writer import generate_boundary_block, write_boundary_json
from src.override_loader import load_override_config, apply_overrides


def extract_boundary_conditions_from_step(step_path, resolution=None):
    """
    Parses STEP geometry with Gmsh and returns boundary_conditions
    metadata for simulation input.

    Parameters:
        step_path (str or Path): Path to STEP file
        resolution (float or None): Grid resolution in meters. Used for bounding box validation.

    Returns:
        dict: boundary_conditions dictionary matching schema
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
        classified = classify_faces(faces)

        # 🧩 Apply overrides if available
        try:
            overrides = load_override_config()
            bc = classified.get("boundary_conditions", {})
            bc_updated = apply_overrides(bc, overrides)
            classified["boundary_conditions"] = bc_updated
        except Exception as e:
            print(f"[Override] Skipped due to error: {e}")

        # ✅ Generate schema-compliant block
        boundary_block = generate_boundary_block(classified)

        return boundary_block
    finally:
        gmsh.finalize()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Gmsh STEP parser for boundary condition metadata")
    parser.add_argument("--step", type=str, required=True, help="Path to STEP file")
    parser.add_argument("--resolution", type=float, help="Grid resolution in meters")
    parser.add_argument("--output", type=str, help="Path to write boundary_conditions JSON")

    args = parser.parse_args()

    result = extract_boundary_conditions_from_step(args.step, resolution=args.resolution)

    print(json.dumps(result, indent=2))

    if args.output:
        write_boundary_json(args.output, result)



