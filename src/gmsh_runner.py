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


def extract_bounding_box_with_gmsh(*args, **kwargs):
    raise NotImplementedError("Stub for CI compatibility")


def extract_boundary_conditions_from_step(step_path, resolution=None):
    if not os.path.isfile(step_path):
        raise FileNotFoundError(f"STEP file not found: {step_path}")
    print(f"[GmshRunner] STEP file found: {step_path}")

    if resolution is None:
        try:
            profile = load_resolution_profile()
            resolution = profile.get("default_resolution", {}).get("dx", 0.01)
        except Exception:
            resolution = 0.01
    print(f"[GmshRunner] Using resolution: {resolution}")

    gmsh.initialize()
    try:
        gmsh.model.add("domain_model")
        gmsh.logger.start()

        validate_step_has_volumes(step_path)
        print(f"[GmshRunner] STEP file validated for volumes")

        gmsh.open(str(step_path))
        print(f"[GmshRunner] STEP file opened")

        volumes = gmsh.model.getEntities(3)
        print(f"[GmshRunner] Volume entities: {volumes}")
        entity_tag = volumes[0][1]

        min_x, min_y, min_z, max_x, max_y, max_z = gmsh.model.getBoundingBox(3, entity_tag)
        print(f"[GmshRunner] Bounding box: ({min_x}, {min_y}, {min_z}) → ({max_x}, {max_y}, {max_z})")

        if (max_x - min_x) <= 0 or (max_y - min_y) <= 0 or (max_z - min_z) <= 0:
            raise ValueError("Invalid geometry: bounding box has zero size.")

        gmsh.model.mesh.generate(3)
        print(f"[GmshRunner] Mesh generation completed")

        faces = []
        surface_entities = gmsh.model.getEntities(2)
        print(f"[GmshRunner] Surface entities found: {len(surface_entities)}")

        for dim, tag in surface_entities:
            node_data = gmsh.model.mesh.getNodes(dim, tag)
            coords_raw = node_data[1] if node_data else []
            print(f"[GmshRunner] Surface {tag} node count: {len(coords_raw)}")

            if coords_raw is not None and len(coords_raw) >= 9:
                try:
                    coords = coords_raw.reshape(-1, 3)
                    face_vertices = coords.tolist()
                    faces.append({"id": tag, "vertices": face_vertices})
                except Exception as e:
                    print(f"[GmshRunner] Failed to reshape nodes for surface {tag}: {e}")
                    continue
            else:
                print(f"[GmshRunner] Skipping surface {tag} due to insufficient node data")
                continue

        print(f"[GmshRunner] Total faces extracted: {len(faces)}")

        classified = classify_faces(faces)
        print(f"[GmshRunner] Classification result: {json.dumps(classified, indent=2)}")

        boundary_block = generate_boundary_block(classified)
        print(f"[SchemaWriter] Initial boundary block: {json.dumps(boundary_block, indent=2)}")

        flow_data_path = "data/testing-input-output/flow_data.json"
        if os.path.isfile(flow_data_path):
            try:
                with open(flow_data_path, "r") as f:
                    flow_data = json.load(f)
                velocity = flow_data["initial_conditions"]["initial_velocity"]
                pressure = flow_data["initial_conditions"]["initial_pressure"]

                boundary_block["apply_faces"] = ["x_min"]
                boundary_block["apply_to"] = ["velocity", "pressure"]
                boundary_block["velocity"] = velocity
                boundary_block["pressure"] = pressure
                boundary_block["no_slip"] = True

                print(f"[GmshRunner] Inlet boundary injected from flow_data.json")
            except Exception as e:
                print(f"[GmshRunner] Failed to inject inlet boundary: {e}")
        else:
            print(f"[GmshRunner] flow_data.json not found. Skipping inlet injection.")

        print(f"[SchemaWriter] Final boundary block: {json.dumps(boundary_block, indent=2)}")

        return boundary_block
    finally:
        gmsh.finalize()
        print(f"[GmshRunner] Gmsh finalized")


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



