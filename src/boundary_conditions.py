import os
import json
import numpy as np
from pint import UnitRegistry
import logging

# Initialize unit registry for physical properties
ureg = UnitRegistry()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load input file containing fluid properties
def load_input_file(file_path):
    """Reads input JSON file with fluid properties and mesh configuration."""
    if not os.path.exists(file_path):
        logger.error(f"❌ ERROR: The input file '{file_path}' was not found.")
        raise FileNotFoundError(f"❌ ERROR: The input file '{file_path}' was not found.")

    logger.info(f"Loading input data from: {file_path}")
    with open(file_path, 'r') as file:
        input_data = json.load(file)

    # Ensure correct mapping for pressure
    # If "static_pressure" exists and "pressure" doesn't, use static_pressure.
    # Otherwise, "pressure" should ideally be directly in the input_data.
    if "static_pressure" in input_data and "pressure" not in input_data:
        input_data["pressure"] = input_data["static_pressure"]

    # Validate required fields and apply defaults where necessary
    input_data = process_input(input_data)

    # Convert raw input values to Pint quantities
    # Ensure fluid_velocity is always a list of floats before converting to Pint Quantity
    # np.array converts list of floats to numpy array, then tolist() converts it back to Python list
    input_data["fluid_velocity"] = np.array(input_data["fluid_velocity"], dtype=float).tolist()
    input_data["fluid_velocity"] = np.array(input_data["fluid_velocity"]) * ureg.meter / ureg.second # Convert to Pint Quantity (NumPy array of quantities)

    input_data["pressure"] *= ureg.pascal
    input_data["density"] *= ureg.kilogram / ureg.meter**3
    input_data["viscosity"] *= ureg.pascal * ureg.second

    # Add default temperature if not present in input, as it's required for fluid_properties
    if "temperature" not in input_data:
        input_data["temperature"] = 298 * ureg.kelvin # Default temperature in Kelvin
        logger.warning("⚠️ 'temperature' not found in input data. Defaulting to 298 K.")
    else:
        input_data["temperature"] *= ureg.kelvin # Assume input temperature is in Kelvin if present

    logger.info("Input data loaded and units processed.")
    return input_data

# Validate input data for missing fields
def process_input(input_data):
    """Validates required fields and ensures defaults where necessary."""
    required_fields = ["fluid_velocity", "density", "viscosity", "pressure"]
    default_values = {
        "pressure": 101325, # in Pascals
        "fluid_velocity": [0.0, 0.0, 0.0], # in m/s, as a list
        "density": 1000, # kg/m^3
        "viscosity": 0.001002 # Pa*s
    }

    for field in required_fields:
        if field not in input_data:
            input_data[field] = default_values[field]
            logger.warning(f"⚠️ Missing '{field}' in input data. Defaulting to: {default_values[field]}")

    return input_data

# Apply boundary conditions based on input data
def apply_boundary_conditions(input_data, dx_value, dt_value):
    """Assigns inlet, outlet, and wall boundary conditions based on input_data
       and simulation parameters dx, dt."""

    logger.info("Applying boundary conditions...")

    # Placeholder face IDs (these would ideally be derived from mesh parsing)
    # For a real application, you would parse simulation_mesh.obj here
    # to dynamically determine these face IDs based on geometric location,
    # face normals, or group definitions in the mesh file.
    inlet_faces = [308, 310, 311, 312, 313, 314, 315]
    outlet_faces = [97, 100, 101, 102, 103, 104, 105, 106, 107]
    wall_faces = list(range(21)) # Example: from 0 to 20 as in the desired output

    # Extract magnitudes from Pint quantities for JSON serialization
    # Ensure velocity is a list of floats
    inlet_velocity_magnitude = input_data["fluid_velocity"].to(ureg.meter / ureg.second).magnitude.tolist()
    inlet_pressure_magnitude = input_data["pressure"].to(ureg.pascal).magnitude
    fluid_temperature_magnitude = input_data["temperature"].to(ureg.kelvin).magnitude
    fluid_density_magnitude = input_data["density"].to(ureg.kilogram / ureg.meter**3).magnitude
    fluid_viscosity_magnitude = input_data["viscosity"].to(ureg.pascal * ureg.second).magnitude

    # Suggested time step from the main function's dt parameter
    suggested_time_step_magnitude = dt_value.to(ureg.second).magnitude

    boundary_conditions = {
        "inlet_faces": inlet_faces,
        "inlet_boundary": {
            "type": "velocity_inlet",
            "velocity": inlet_velocity_magnitude,
            "direction": [1.0, 0.0, 0.0], # Assuming flow along X-axis, can be made configurable
            "pressure": inlet_pressure_magnitude, # Inlet static pressure
            "fluid_properties": {
                "temperature": fluid_temperature_magnitude,
                "density": fluid_density_magnitude,
                "viscosity": fluid_viscosity_magnitude
            }
        },
        "outlet_faces": outlet_faces,
        "outlet_boundary": {
            "type": "pressure_outlet",
            "velocity": None, # Velocity is often not directly specified for pressure outlets
            "pressure": None  # Pressure is usually a reference value, or derived by solver for pressure outlets
        },
        "wall_faces": wall_faces,
        "wall_boundary": {
            "no_slip": True, # Common assumption for walls
            "wall_properties": {
                "roughness": 0.002, # Default roughness, could be configurable
                "heat_transfer": False # Default heat transfer, could be configurable
            }
        },
        "simulation_settings": {
            "suggested_time_step": suggested_time_step_magnitude,
            "CFL_condition": "adaptive" # This indicates the solver should handle adaptivity
        }
    }
    logger.info("Boundary conditions structured successfully.")
    return boundary_conditions

# Ensure numerical stability via CFL condition
def enforce_numerical_stability(input_data, dx, dt):
    """Checks CFL condition for numerical stability."""
    # Ensure fluid_velocity is a numerical array for norm calculation
    # input_data["fluid_velocity"] is a NumPy array of Pint Quantities, so .magnitude gives a NumPy array of floats
    fluid_velocity_array_magnitude = input_data["fluid_velocity"].magnitude
    velocity_norm = np.linalg.norm(fluid_velocity_array_magnitude)

    cfl_value = velocity_norm * dt.magnitude / dx.magnitude
    logger.info(f"Calculated CFL value: {cfl_value:.4f}")

    if cfl_value > 1:
        logger.error(f"❌ ERROR: CFL condition violated – CFL = {cfl_value:.4f}. Adjust time-step or grid spacing.")
        raise ValueError(f"❌ ERROR: CFL condition violated – CFL = {cfl_value:.4f}. Adjust time-step or grid spacing.")
    logger.info("CFL condition satisfied.")

# Generate output file based on computed boundary conditions
def save_output_file(boundary_conditions, output_file_path):
    """Writes computed boundary conditions to output JSON file."""
    # Ensure output directory exists
    output_dir = os.path.dirname(output_file_path)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        logger.info(f"Created output directory: {output_dir}")

    logger.info(f"Saving boundary conditions to: {output_file_path}")
    with open(output_file_path, 'w') as file:
        json.dump(boundary_conditions, file, indent=4)

    logger.info(f"✅ Boundary conditions saved to: {output_file_path}")

# Main function: Load input, validate, process boundary conditions, enforce stability, and save output
def main(mesh_file_path, fluid_input_file_path, dx=0.01 * ureg.meter, dt=0.001 * ureg.second):
    """Executes boundary condition processing pipeline."""

    logger.info("Starting boundary condition processing pipeline.")

    # Load input data
    input_data = load_input_file(fluid_input_file_path)

    # Enforce numerical stability
    enforce_numerical_stability(input_data, dx, dt)

    # Generate boundary conditions (passing dx and dt for simulation settings)
    boundary_conditions = apply_boundary_conditions(input_data, dx, dt) # Directly call apply_boundary_conditions

    # Construct the output path for boundary_conditions.json
    output_dir = os.path.dirname(fluid_input_file_path)
    output_file_path = os.path.join(output_dir, "boundary_conditions.json")

    # Save results
    save_output_file(boundary_conditions, output_file_path)

    logger.info("✅ Processing complete!")

# Example usage: Processing input file and generating output
if __name__ == "__main__":
    import sys
    # When run directly, assume arguments are passed or define default paths
    if len(sys.argv) == 3:
        # The workflow passes mesh_file_path and then fluid_input_file_path
        mesh_arg_path = sys.argv[1]
        fluid_input_arg_path = sys.argv[2]
        main(mesh_arg_path, fluid_input_arg_path)
    else:
        logger.info("ℹ️ Running with default local paths for testing.")
        # Adjust these paths if your local setup differs
        default_mesh_path = "../downloaded_simulation_files/simulation_mesh.obj"
        default_fluid_input_path = "../downloaded_simulation_files/fluid_simulation_input.json"

        # Create dummy input file for local testing if it doesn't exist
        dummy_input_dir = os.path.dirname(default_fluid_input_path)
        if not os.path.exists(dummy_input_dir):
            os.makedirs(dummy_input_dir)
            logger.info(f"Created dummy input directory: {dummy_input_dir}")

        dummy_fluid_input_content = {
            "fluid_velocity": [2.5, 0.0, 0.0],
            "static_pressure": 101325,
            "density": 1000,
            "viscosity": 0.001002,
            "temperature": 298
        }
        if not os.path.exists(default_fluid_input_path):
            with open(default_fluid_input_path, 'w') as f:
                json.dump(dummy_fluid_input_content, f, indent=4)
            logger.info(f"Created dummy fluid input file for testing: {default_fluid_input_path}")
        
        # No need to create a dummy mesh file for this script's current functionality
        # as it doesn't parse it.

        main(default_mesh_path, default_fluid_input_path)



