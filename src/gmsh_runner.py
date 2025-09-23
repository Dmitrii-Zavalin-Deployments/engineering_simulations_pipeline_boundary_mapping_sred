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
from scipy.spatial import cKDTree

from src.utils.gmsh_input_check import validate_step_has_volumes
from src.utils.input_validation import load_resolution_profile
from src.bbox_classifier import classify_faces
from src.schema_writer import generate_boundary_block, write_boundary_json


def classify_geometry(min_dim, max_dim, volume_count):
    if volume_count > 1:
        return "solid"
    if max_dim / min_dim > 10:
        return "shell"
    return "solid"


def estimate_wall_thickness(surface_tags):
    coords = [gmsh.model.mesh.getNodes(2, tag)[1].reshape(-1, 3) for tag in surface_tags]
    sampled = [c[np.random.choice(len(c), min(500, len(c)), replace=False)] for c in coords]
    min_dist = float('inf')
    for i in range(len(sampled)):
        tree = cKDTree(sampled[i])
        for j in range(i + 1, len(sampled)):
            dist, _ = tree.query(sampled[j], k=1)
            min_dist = min(min_dist, np.min(dist))
    return round(min_dist, 5)


def generate_resolution_sweep(min_dim, wall_thickness=None, geometry_type="solid", steps=5):
    if geometry_type == "shell" and wall_thickness:
        base_res = wall_thickness / 2
    else:
        base_res = min_dim / 20
    return [round(base_res * (0.5 ** i), 5) for i in range(steps)]


def evaluate_mesh_quality():
    types, elementTags, _ = gmsh.model.mesh.getElements(3)
    if not elementTags or not elementTags[0]:
        return {"min": 0.0, "avg": 0.0, "std": 0.0}
    qualities = gmsh.model.mesh.getElementQualities(elementTags[0])
    return {
        "min": round(min(qualities), 4),
        "avg": round(sum(qualities) / len(qualities), 4),
        "std": round(np.std(qualities), 4)
    }


def extract_boundary_conditions_from_step(step_path, resolution=None):
    if not os.path.isfile(step_path):
        raise FileNotFoundError(f"STEP file not found: {step_path}")
    print(f"[GmshRunner] STEP file found: {step_path}")

    gmsh.initialize()
    try:
        gmsh.model.add("domain_model")
        gmsh.logger.start()

        validate_step_has_volumes(step_path)
        print(f"[GmshRunner] STEP file validated for volumes")

        gmsh.open(str(step_path))
        print(f"[GmshRunner] STEP file opened")

        # 🧼 Geometry healing and cleanup
        gmsh.model.occ.removeAllDuplicates()
        gmsh.model.occ.synchronize()
        gmsh.model.mesh.classifySurfaces(angle=30 * np.pi / 180.)
        gmsh.model.mesh.createGeometry()
        gmsh.option.setNumber("Geometry.Tolerance", 1e-6)

        volumes = gmsh.model.getEntities(3)
        if not volumes:
            raise ValueError("No valid volumes found for meshing.")
        entity_tag = volumes[0][1]

        min_x, min_y, min_z, max_x, max_y, max_z = gmsh.model.getBoundingBox(3, entity_tag)
        dims = [max_x - min_x, max_y - min_y, max_z - min_z]
        min_dim = min(dims)
        max_dim = max(dims)
        volume_count = len(volumes)

        geometry_type = classify_geometry(min_dim, max_dim, volume_count)
        surface_tags = [tag for dim, tag in gmsh.model.getEntities(2)]
        wall_thickness = estimate_wall_thickness(surface_tags) if geometry_type == "shell" else None

        sweep = generate_resolution_sweep(min_dim, wall_thickness, geometry_type)
        results = []

        for res in sweep:
            gmsh.model.mesh.clear()
            gmsh.option.setNumber("Mesh.CharacteristicLengthMax", res)
            gmsh.option.setNumber("Mesh.CharacteristicLengthMin", res / 10)
            gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 1)
            gmsh.option.setNumber("Mesh.MeshSizeFactor", 1.0)
            gmsh.option.setNumber("Mesh.MinimumCirclePoints", 10)
            gmsh.option.setNumber("Mesh.Algorithm3D", 1)  # MeshAdapt for robustness

            try:
                gmsh.model.mesh.generate(3)
                quality = evaluate_mesh_quality()
                results.append({"resolution": res, "quality": quality})
                print(f"[GmshRunner] Mesh generated at resolution {res} → quality: {quality}")
                break  # Stop at first successful resolution
            except Exception as e:
                results.append({"resolution": res, "error": str(e)})
                print(f"[GmshRunner] Mesh failed at resolution {res}: {e}")

        with open("geometry_resolution_advice.json", "w") as f:
            json.dump({"resolution_candidates": sweep, "quality_metrics": results}, f, indent=2)

        # 🛡️ Ensure surface mesh is generated before extracting nodes
        gmsh.model.mesh.generate(2)

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
    parser.add_argument("--resolution", type=float, help="Grid resolution in meters (optional override)")
    parser.add_argument("--output", type=str, help="Path to write boundary_conditions JSON")

    args = parser.parse_args()

    result = extract_boundary_conditions_from_step(args.step, resolution=args.resolution)

    print(json.dumps(result, indent=2))

    if args.output:
        write_boundary_json(args.output, result)



