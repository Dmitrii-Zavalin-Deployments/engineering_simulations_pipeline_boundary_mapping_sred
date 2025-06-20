# src/merge_json_files.py

import json
import os
import sys

def extract_boundary_faces(mesh_data, boundary_type):
    """Extracts face IDs based on boundary type."""
    faces = [
        face["face_id"]
        for face in mesh_data.get("boundary_faces", [])
        if face.get("type") == boundary_type
    ]
    print(f"[DEBUG] Extracted {len(faces)} {boundary_type} faces: {faces}")
    return faces

def validate_fluid_structure(merged):
    """Lightweight structural assertion to catch malformed outputs."""
    print("[DEBUG] Validating structure of merged data...")
    required_blocks = ["mesh", "boundary_conditions", "fluid_properties", "simulation_parameters"]
    for block in required_blocks:
        if block not in merged:
            raise ValueError(f"Missing top-level block: {block}")
    bc = merged["boundary_conditions"]
    for side in ["inlet", "outlet", "wall"]:
        if side not in bc:
            raise ValueError(f"Missing boundary condition for: {side}")
    if "velocity" not in bc["inlet"] or "pressure" not in bc["inlet"]:
        raise ValueError("Inlet must have both velocity and pressure.")
    print("[DEBUG] Structure validation passed.")

def merge_json_files(mesh_file, initial_file, output_file):
    """Merge mesh JSON and initial fluid simulation JSON into a structured output file."""

    workspace_dir = os.getenv("GITHUB_WORKSPACE", ".")
    print(f"[DEBUG] Workspace directory: {workspace_dir}")

    mesh_path = os.path.join(workspace_dir, "downloaded_simulation_files", mesh_file)
    initial_path = os.path.join(workspace_dir, "downloaded_simulation_files", initial_file)
    output_path = os.path.join(workspace_dir, "downloaded_simulation_files", output_file)

    print(f"[DEBUG] Loading mesh from: {mesh_path}")
    with open(mesh_path, 'r') as f:
        mesh_data = json.load(f)

    print(f"[DEBUG] Loading initial data from: {initial_path}")
    with open(initial_path, 'r') as f:
        fluid_data = json.load(f)

    print("[DEBUG] Top-level keys in initial data:", list(fluid_data.keys()))
    if "thermodynamics" in fluid_data:
        print("[DEBUG] ⚠️ Found top-level 'thermodynamics' block!")

    inlet_faces = extract_boundary_faces(mesh_data, "inlet")
    outlet_faces = extract_boundary_faces(mesh_data, "outlet")
    wall_faces = extract_boundary_faces(mesh_data, "wall")

    fluid_props = fluid_data.get("fluid_properties", {}).copy()
    print("[DEBUG] Keys in fluid_properties before patch:", list(fluid_props.keys()))

    thermo_top = fluid_data.get("thermodynamics")
    if thermo_top and "thermodynamics" not in fluid_props:
        fluid_props["thermodynamics"] = thermo_top
        print("[DEBUG] Injected top-level 'thermodynamics' into fluid_properties.")

    print("[DEBUG] Final fluid_properties keys:", list(fluid_props.keys()))

    final_data = {
        "mesh": mesh_data,
        "boundary_conditions": {
            "inlet": {
                "faces": inlet_faces,
                "velocity": fluid_data["boundary_conditions"]["inlet"]["velocity"],
                "pressure": fluid_data["boundary_conditions"]["inlet"]["pressure"]
            },
            "outlet": {
                "faces": outlet_faces,
                "pressure": fluid_data["boundary_conditions"]["outlet"]["pressure"]
            },
            "wall": {
                "faces": wall_faces,
                "no_slip": fluid_data["boundary_conditions"]["wall"]["no_slip"]
            }
        },
        "fluid_properties": fluid_props,
        "simulation_parameters": fluid_data.get("simulation_parameters", {})
    }

    print("[DEBUG] Assembled final_data keys:", list(final_data.keys()))
    print("[DEBUG] Top-level 'thermodynamics' still present? →", "thermodynamics" in final_data)

    try:
        validate_fluid_structure(final_data)
    except ValueError as e:
        print(f"❌ Structure validation failed: {e}")
        sys.exit(1)

    with open(output_path, 'w') as f:
        json.dump(final_data, f, indent=4)

    print(f"✅ Merged JSON saved to {output_path}")

if __name__ == "__main__":
    merge_json_files("mesh_data.json", "initial_data.json", "fluid_simulation_input.json")



