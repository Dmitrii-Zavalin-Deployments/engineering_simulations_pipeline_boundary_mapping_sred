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
    if volume_count > 1 and max_dim / min_dim < 5:
        return "solid"
    elif max_dim / min_dim > 10:
        return "shell"
    else:
        return "ambiguous"


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

    max_elements = int(os.getenv("MAX_ELEMENT_COUNT", "10000000"))
    algorithms_to_try = [1, 4, 5, 6, 7]

    gmsh.initialize()
    try:
        gmsh.model.add("domain_model")
        gmsh.logger.start()

        validate_step_has_volumes(step_path)
        print(f"[GmshRunner] STEP file validated for volumes")

        gmsh.open(str(step_path))
        print(f"[GmshRunner] STEP file opened")

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
        print(f"[GmshRunner] Geometry classified as: {geometry_type}")

        surface_tags = [tag for dim, tag in gmsh.model.getEntities(2)]
        wall_thickness = estimate_wall_thickness(surface_tags) if geometry_type == "shell" else None

        sweep = generate_resolution_sweep(min_dim, wall_thickness, geometry_type, steps=7 if geometry_type == "ambiguous" else 5)
        results = []
        algorithm_used = None

        for res in sweep:
            for algo in algorithms_to_try:
                gmsh.model.mesh.clear()
                gmsh.option.setNumber("Mesh.CharacteristicLengthMax", res)
                gmsh.option.setNumber("Mesh.CharacteristicLengthMin", res / 10)
                gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 1)
                gmsh.option.setNumber("Mesh.MeshSizeFactor", 1.0)
                gmsh.option.setNumber("Mesh.MinimumCirclePoints", 10)
                gmsh.option.setNumber("Mesh.Algorithm3D", algo)

                try:
                    gmsh.model.mesh.generate(3)
                    quality = evaluate_mesh_quality()
                    element_count = len(gmsh.model.mesh.getElements(3)[1][0])
                    results.append({
                        "resolution": res,
                        "algorithm": algo,
                        "quality": quality,
                        "element_count": element_count
                    })
                    print(f"[GmshRunner] Mesh succeeded with algorithm {algo} at resolution {res} → quality: {quality}")
                    if quality["min"] > 0.05 and element_count < max_elements:
                        algorithm_used = algo
                        break
                except Exception as e:
                    results.append({"resolution": res, "algorithm": algo, "error": str(e)})
                    print(f"[GmshRunner] Algorithm {algo} failed at resolution {res}: {e}")
            if algorithm_used is not None:
                break

        with open("geometry_resolution_advice.json", "w") as f:
            json.dump({
                "resolution_candidates": sweep,
                "quality_metrics": results,
                "algorithm_used": algorithm_used
            }, f, indent=2)

        faces = []
        surface_entities = gmsh.model.getEntities(2)
        print(f"[GmshRunner] Surface entities found: {len(surface_entities)}")

        for dim, tag in surface_entities:
            bbox = gmsh.model.getBoundingBox(dim, tag)
            volume = (bbox[3] - bbox[0]) * (bbox[4] - bbox[1]) * (bbox[5] - bbox[2])
            node_data = gmsh.model.mesh.getNodes(dim, tag)
            node_count = len(node_data[1]) // 3 if node_data else 0

            if volume < 1e-9 or node_count < 10:
                print(f"[GmshRunner] Skipping surface {tag} — degenerate or unmeshable")
                continue

            try:
                coords = node_data[1].reshape(-1, 3)
                face_vertices = coords.tolist()
                faces.append({"id": tag, "vertices": face_vertices})
            except Exception as e:
                print(f"[GmshRunner] Failed to reshape nodes for surface {tag}: {e}")
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



