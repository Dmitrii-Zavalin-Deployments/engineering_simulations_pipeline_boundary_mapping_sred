import json
import os

def merge_json_files(mesh_file, initial_file, output_file):
    """Merge mesh JSON and initial fluid simulation JSON into a correctly formatted JSON file."""

    # Get the workspace directory
    workspace_dir = os.getenv("GITHUB_WORKSPACE", ".")

    # Construct full paths for input/output files
    mesh_path = os.path.join(workspace_dir, "downloaded_simulation_files", mesh_file)
    initial_path = os.path.join(workspace_dir, "downloaded_simulation_files", initial_file)
    output_path = os.path.join(workspace_dir, "downloaded_simulation_files", output_file)

    # Load mesh data
    with open(mesh_path, 'r') as f:
        mesh_data = json.load(f)

    # Load initial simulation data
    with open(initial_path, 'r') as f:
        fluid_data = json.load(f)

    # Merge files into final structure
    final_data = {
        "mesh": mesh_data["mesh"],  # Preserve mesh structure
        "boundary_conditions": fluid_data["boundary_conditions"],  # Fluid conditions
        "fluid_properties": fluid_data["fluid_properties"],  # Fluid properties
        "simulation_parameters": fluid_data["simulation_parameters"]  # Simulation settings
    }

    # Save merged data to output file
    with open(output_path, 'w') as f:
        json.dump(final_data, f, indent=4)

    print(f"✅ Merged JSON saved to {output_path}")

# Example usage in GitHub Actions
if __name__ == "__main__":
    merge_json_files("mesh_data.json", "initial_data.json", "fluid_simulation_input.json")



