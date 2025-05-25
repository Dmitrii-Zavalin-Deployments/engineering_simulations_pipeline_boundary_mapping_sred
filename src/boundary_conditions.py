import json

def merge_json_files(mesh_file, initial_file, output_file):
    """Merge mesh JSON and initial fluid simulation JSON into a correctly formatted JSON file."""

    # Load simulation mesh data
    with open(mesh_file, 'r') as f:
        mesh_data = json.load(f)

    # Load initial simulation data
    with open(initial_file, 'r') as f:
        fluid_data = json.load(f)

    # Merge files into final structure
    final_data = {
        "mesh": mesh_data["mesh"],  # Preserve mesh structure
        "boundary_conditions": fluid_data["boundary_conditions"],  # Fluid conditions
        "fluid_properties": fluid_data["fluid_properties"],  # Fluid properties
        "simulation_parameters": fluid_data["simulation_parameters"]  # Simulation settings
    }

    # Save merged data to output file
    with open(output_file, 'w') as f:
        json.dump(final_data, f, indent=4)

    print(f"✅ Merged JSON saved to {output_file}")

# Example usage
merge_json_files("simulation_mesh.json", "initial_data.json", "fluid_simulation_input.json")



