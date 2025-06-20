# src/merge_json_files.py

import json
import os
import sys

def extract_boundary_faces(mesh_data, boundary_type):
    """Extracts face IDs based on boundary type."""
    return [
        face["face_id"]
        for face in mesh_data.get("boundary_faces", [])
        if face.get("type") == boundary_type
    ]

def validate_fluid_structure(merged):
    """Lightweight structural assertion to catch malformed outputs."""
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

def merge_json_files(mesh_file, initial_file, output_file):
    """Merge mesh JSON and initial fluid simulation JSON into a structured output file."""

    # Get workspace directory (GitHub or local fallback)
    workspace_dir = os.getenv("GITHUB_WORKSPACE", ".")

    # Construct full paths
    mesh_path = os.path.join(workspace_dir, "downloaded_simulation_files", mesh_file)
    initial_path = os.path.join(workspace_dir, "downloaded_simulation_files", initial_file)
    output_path = os.path.join(workspace_dir, "downloaded_simulation_files", output_file)

    # Load input files
    with open(mesh_path, 'r') as f:
        mesh_data = json.load(f)

    with open(initial_path, 'r') as f:
        fluid_data = json.load(f)

    # Extract face IDs by type
    inlet_faces = extract_boundary_faces(mesh_data, "inlet")
    outlet_faces = extract_boundary_faces(mesh_data, "outlet")
    wall_faces = extract_boundary_faces(mesh_data, "wall")

    # Assemble final merged structure
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
        "fluid_properties": fluid_data.get("fluid_properties", {}),
        "simulation_parameters": fluid_data.get("simulation_parameters", {})
    }

    # Inline structure check
    try:
        validate_fluid_structure(final_data)
    except ValueError as e:
        print(f"❌ Structure validation failed: {e}")
        sys.exit(1)

    # Save result
    with open(output_path, 'w') as f:
        json.dump(final_data, f, indent=4)

    print(f"✅ Merged JSON saved to {output_path}")

if __name__ == "__main__":
    merge_json_files("mesh_data.json", "initial_data.json", "fluid_simulation_input.json")



