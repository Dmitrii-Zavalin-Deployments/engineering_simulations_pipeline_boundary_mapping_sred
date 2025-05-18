import os
import json
from pint import UnitRegistry

# Initialize unit registry for physical properties
ureg = UnitRegistry()

# Load input file containing fluid properties
def load_input_file(file_path):
    """Reads input JSON file with fluid properties and mesh configuration."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Error: The input file '{file_path}' was not found.")
    
    with open(file_path, 'r') as file:
        input_data = json.load(file)

    # Ensure correct mapping for pressure
    if "static_pressure" in input_data:
        input_data["pressure"] = input_data["static_pressure"]

    # Convert units correctly
    input_data["fluid_velocity"] *= ureg.meter / ureg.second
    input_data["pressure"] *= ureg.pascal
    input_data["density"] *= ureg.kilogram / ureg.meter**3
    input_data["viscosity"] *= ureg.pascal * ureg.second
    return input_data

# Apply boundary conditions based on input data
def apply_boundary_conditions(input_data):
    """Assigns inlet, outlet, and wall boundary conditions."""
    boundary_conditions = {
        "inlet_boundary": {"velocity": input_data["fluid_velocity"]},
        "outlet_boundary": {"pressure": input_data["pressure"]},
        "walls": {"velocity": 0 * ureg.meter / ureg.second},  # No-slip condition
    }
    return boundary_conditions

# Numerical stability enforcement via CFL condition
def enforce_numerical_stability(input_data, dx, dt):
    """Checks CFL condition for numerical stability."""
    cfl_value = input_data["fluid_velocity"] * dt / dx
    assert cfl_value <= 1, "CFL condition violated: time-step too large!"

# Generate output file based on computed boundary conditions
def save_output_file(boundary_conditions, output_file_path):
    """Writes computed boundary conditions to output JSON file."""
    # Convert Pint quantities to numerical values for JSON compatibility
    formatted_output = {key: {sub_key: float(value.magnitude) for sub_key, value in val.items()}
                        for key, val in boundary_conditions.items()}

    with open(output_file_path, 'w') as file:
        json.dump(formatted_output, file, indent=4)

# Main function: Load input, process boundary conditions, enforce stability, and save output
def main(input_file_path, output_file_path, dx=0.01 * ureg.meter, dt=0.001 * ureg.second):
    """Executes boundary condition processing pipeline."""
    # Load input data
    input_data = load_input_file(input_file_path)

    # Enforce numerical stability
    enforce_numerical_stability(input_data, dx, dt)

    # Process boundary conditions
    boundary_conditions = apply_boundary_conditions(input_data)

    # Save results to output file
    save_output_file(boundary_conditions, output_file_path)

# Example usage: Processing input file and generating output
if __name__ == "__main__":
    input_file_path = "data/testing-input-output/fluid_simulation_input.json"
    output_file_path = "data/testing-input-output/boundary_conditions.json"  # Updated output filename
    main(input_file_path, output_file_path)
