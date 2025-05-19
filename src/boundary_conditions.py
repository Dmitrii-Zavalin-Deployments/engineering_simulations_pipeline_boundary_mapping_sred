import os
import json
import numpy as np
from pint import UnitRegistry
from src.download_dropbox_files import download_files_from_dropbox  # Corrected import path

# Initialize unit registry for physical properties
ureg = UnitRegistry()

# Define Dropbox parameters
dropbox_folder = "/engineering_simulations_pipeline"
local_folder = "data/testing-input-output"
log_file_path = "data/dropbox_download_log.txt"

# Define Dropbox API credentials (ensure these are securely stored in environment variables)
refresh_token = os.getenv("DROPBOX_REFRESH_TOKEN")
client_id = os.getenv("DROPBOX_CLIENT_ID")
client_secret = os.getenv("DROPBOX_CLIENT_SECRET")

# Download required input files from Dropbox
def fetch_simulation_files():
    """Fetch simulation input files from Dropbox."""
    files_to_download = ["fluid_simulation_input.json", "simulation_mesh.obj"]

    if not refresh_token or not client_id or not client_secret:
        raise ValueError("❌ ERROR: Missing Dropbox API credentials! Ensure environment variables are set.")

    print("🔄 Downloading input files from Dropbox...")
    download_files_from_dropbox(dropbox_folder, local_folder, refresh_token, client_id, client_secret, log_file_path)

    # Verify files are downloaded
    for file in files_to_download:
        file_path = os.path.join(local_folder, file)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"❌ ERROR: Missing required file '{file}' after Dropbox download.")

# Load input file containing fluid properties
def load_input_file(file_path):
    """Reads input JSON file with fluid properties and mesh configuration."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"❌ ERROR: The input file '{file_path}' was not found.")

    with open(file_path, 'r') as file:
        input_data = json.load(file)

    # Ensure correct mapping for pressure
    if "static_pressure" in input_data:
        input_data["pressure"] = input_data["static_pressure"]

    # Validate required fields
    input_data = process_input(input_data)

    # Convert units correctly
    input_data["fluid_velocity"] = np.atleast_1d(np.array(input_data["fluid_velocity"], dtype=float)) * ureg.meter / ureg.second
    input_data["pressure"] *= ureg.pascal
    input_data["density"] *= ureg.kilogram / ureg.meter**3
    input_data["viscosity"] *= ureg.pascal * ureg.second

    return input_data

# Validate input data for missing fields
def process_input(input_data):
    """Validates required fields and ensures defaults where necessary."""
    required_fields = ["fluid_velocity", "density", "viscosity", "pressure"]
    default_values = {"pressure": 101325 * ureg.pascal, "fluid_velocity": np.array([0.0, 0.0, 0.0]) * ureg.meter / ureg.second}

    for field in required_fields:
        if field not in input_data:
            input_data[field] = default_values[field]

    return input_data

# Apply boundary conditions based on input data
def apply_boundary_conditions(input_data):
    """Assigns inlet, outlet, and wall boundary conditions."""
    if "pressure" not in input_data:
        raise KeyError("❌ ERROR: Missing 'pressure' field in input data.")

    boundary_conditions = {
        "inlet_boundary": {"velocity": input_data["fluid_velocity"]},
        "outlet_boundary": {
            "pressure": input_data["pressure"],
            "velocity": np.atleast_1d(input_data["fluid_velocity"])  # Ensure velocity remains an array
        },
        "walls": {"velocity": np.atleast_1d(0 * ureg.meter / ureg.second)},  # No-slip condition
    }
    return boundary_conditions

# Ensure numerical stability via CFL condition
def enforce_numerical_stability(input_data, dx, dt):
    """Checks CFL condition for numerical stability."""
    fluid_velocity_array = np.atleast_1d(np.array(input_data["fluid_velocity"].magnitude, dtype=float))  # Ensure array format
    velocity_norm = np.linalg.norm(fluid_velocity_array, axis=-1)  # Compute norm safely

    cfl_value = np.max(velocity_norm) * dt.magnitude / dx.magnitude  # Extract magnitude values for CFL enforcement

    if cfl_value > 1:  # Ensure proper numerical comparison
        raise ValueError(f"❌ ERROR: CFL condition violated – CFL = {cfl_value:.4f}. Adjust time-step or grid spacing.")

# Generate boundary conditions from input data
def generate_boundary_conditions(input_data):
    """Applies boundary conditions based on input properties."""
    return apply_boundary_conditions(input_data)

# Generate output file based on computed boundary conditions
def save_output_file(boundary_conditions, output_file_path):
    """Writes computed boundary conditions to output JSON file."""
    # Ensure output directory exists
    output_dir = os.path.dirname(output_file_path)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)  # Create directory if missing

    # Convert Pint quantities to numerical values for JSON compatibility
    formatted_output = {
        key: {sub_key: float(value.magnitude) if hasattr(value, 'magnitude') else value for sub_key, value in val.items()}
        for key, val in boundary_conditions.items()
    }

    with open(output_file_path, 'w') as file:
        json.dump(formatted_output, file, indent=4)

    print(f"✅ Boundary conditions saved to: {output_file_path}")

# Main function: Load input, validate, process boundary conditions, enforce stability, and save output
def main(input_file_path, output_file_path, dx=0.01 * ureg.meter, dt=0.001 * ureg.second):
    """Executes boundary condition processing pipeline."""
    
    print("🔄 Downloading required files from Dropbox...")
    fetch_simulation_files()  # Ensure simulation files are downloaded before proceeding

    print("🔄 Loading input data...")
    input_data = load_input_file(input_file_path)

    print("🔄 Enforcing numerical stability...")
    enforce_numerical_stability(input_data, dx, dt)

    print("🔄 Generating boundary conditions...")
    boundary_conditions = generate_boundary_conditions(input_data)

    print("🔄 Saving results...")
    save_output_file(boundary_conditions, output_file_path)

    print("✅ Processing complete!")

# Example usage: Processing input file and generating output
if __name__ == "__main__":
    input_file_path = "data/testing-input-output/fluid_simulation_input.json"
    output_file_path = "data/testing-input-output/boundary_conditions.json"
    main(input_file_path, output_file_path)



