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

# Load input file containing fluid properties and simulation settings
def load_input_file(file_path):
    """Reads input JSON file with fluid properties and mesh configuration."""
    if not os.path.exists(file_path):
        logger.error(f"❌ ERROR: The input file '{file_path}' was not found.")
        raise FileNotFoundError(f"❌ ERROR: The input file '{file_path}' was not found.")

    logger.info(f"Loading input data from: {file_path}")
    with open(file_path, 'r') as file:
        input_data = json.load(file)

    # Validate required fields and apply defaults where necessary
    # Note: 'fluid_velocity' and 'static_pressure' are now handled specifically for boundary types
    # and might not need global defaults if they are always provided by the user for a specific boundary
    input_data = process_input_data(input_data) # Renamed to avoid confusion with internal validation below

    # Convert raw input values to Pint quantities
    # Only convert if they are directly in input_data and not meant for specific boundary sections yet
    if "static_pressure" in input_data:
        input_data["static_pressure"] *= ureg.pascal
    if "density" in input_data:
        input_data["density"] *= ureg.kilogram / ureg.meter**3
    if "viscosity" in input_data:
        input_data["viscosity"] *= ureg.pascal * ureg.second

    # Add default temperature if not present in input, as it's required for fluid_properties
    if "temperature" not in input_data:
        input_data["temperature"] = 298 * ureg.kelvin # Default temperature in Kelvin
        logger.warning("⚠️ 'temperature' not found in input data. Defaulting to 298 K.")
    else:
        input_data["temperature"] *= ureg.kelvin # Assume input temperature is in Kelvin if present

    logger.info("Input data loaded and units processed.")
    return input_data

# Validate and process input data (renamed for clarity)
def process_input_data(input_data):
    """Validates required fields and ensures defaults where necessary,
       especially for simulation_settings."""

    # Ensure simulation_settings exist and apply defaults for its sub-fields
    if "simulation_settings" not in input_data:
        input_data["simulation_settings"] = {}
        logger.warning("⚠️ 'simulation_settings' not found in input data. Adding empty dict.")

    default_simulation_settings = {
        "flow_type": "transient",
        "time_integration_method": "implicit",
        "suggested_time_step": 0.001,
        "CFL_condition": "adaptive",
        "turbulence_model": "RANS_k-epsilon",
        "pressure_velocity_coupling": "SIMPLE",
        "spatial_discretization": "second_order",
        "flux_scheme": "upwind",
        "mesh_type": "unstructured",
        "cell_storage_format": "cell-centered",
        "residual_tolerance": 1e-6,
        "max_iterations": 5000
    }

    for key, value in default_simulation_settings.items():
        if key not in input_data["simulation_settings"]:
            input_data["simulation_settings"][key] = value
            logger.warning(f"⚠️ Missing '{key}' in simulation_settings. Defaulting to: {value}")

    # Add default for "fluid_velocity" if not present at top level, for CFL calculation
    if "fluid_velocity" not in input_data:
        input_data["fluid_velocity"] = [0.0, 0.0, 0.0]
        logger.warning(f"⚠️ Missing 'fluid_velocity' in input data. Defaulting to: {input_data['fluid_velocity']}")
    # Ensure fluid_velocity is always a list of floats before converting to Pint Quantity later
    input_data["fluid_velocity"] = np.array(input_data["fluid_velocity"], dtype=float).tolist()

    return input_data

# Apply boundary conditions based on input data and desired output structure
def apply_boundary_conditions(input_data, dx_value, dt_value):
    """Assigns inlet, outlet, and wall boundary conditions based on input_data
       and simulation parameters dx, dt, targeting the specified output structure."""

    logger.info("Applying boundary conditions...")

    # *** IMPORTANT: These face IDs are still hardcoded. ***
    # In a real application, you would parse simulation_mesh.obj (or a supplementary file)
    # here to dynamically determine these face IDs based on geometric location,
    # face normals, or group definitions in the mesh file.
    inlet_faces = [308, 310, 311, 312, 313, 314, 315]
    outlet_faces = [97, 100, 101, 102, 103, 104, 105, 106, 107]
    wall_faces = list(range(21)) # Example: from 0 to 20 as in the desired output

    # Extract magnitudes from Pint quantities for JSON serialization
    inlet_pressure_magnitude = input_data["static_pressure"].to(ureg.pascal).magnitude
    fluid_temperature_magnitude = input_data["temperature"].to(ureg.kelvin).magnitude
    fluid_density_magnitude = input_data["density"].to(ureg.kilogram / ureg.meter**3).magnitude
    fluid_viscosity_magnitude = input_data["viscosity"].to(ureg.pascal * ureg.second).magnitude

    # Use the fluid_velocity from input_data as the outlet velocity, as per desired output
    # Convert to Pint Quantity (NumPy array of quantities) first, then get magnitude list
    outlet_velocity_magnitude = (np.array(input_data["fluid_velocity"]) * ureg.meter / ureg.second).to(ureg.meter / ureg.second).magnitude.tolist()

    # Suggested time step from the main function's dt parameter (magnitude only)
    suggested_time_step_magnitude = dt_value.to(ureg.second).magnitude

    # Extract simulation settings directly from input_data
    simulation_settings = input_data.get("simulation_settings", {})

    boundary_conditions = {
        "inlet_faces": inlet_faces,
        "inlet_boundary": {
            "type": "pressure_inlet",
            "pressure": inlet_pressure_magnitude,
            "fluid_properties": {
                "temperature": fluid_temperature_magnitude,
                "density": fluid_density_magnitude,
                "viscosity": fluid_viscosity_magnitude
            }
        },
        "outlet_faces": outlet_faces,
        "outlet_boundary": {
            "type": "velocity_outlet",
            "velocity": outlet_velocity_magnitude
        },
        "wall_faces": wall_faces,
        "wall_boundary": {
            "no_slip": True,
            "wall_properties": {
                "roughness": 0.002, # Default roughness, could be configurable
                "heat_transfer": False # Default heat transfer, could be configurable
            },
            "wall_functions": "standard" # Added as per desired output
        },
        "simulation_settings": {
            "flow_type": simulation_settings.get("flow_type"),
            "time_integration_method": simulation_settings.get("time_integration_method"),
            "suggested_time_step": suggested_time_step_magnitude, # Uses dt from main for consistency
            "CFL_condition": simulation_settings.get("CFL_condition"),
            "turbulence_model": simulation_settings.get("turbulence_model"),
            "pressure_velocity_coupling": simulation_settings.get("pressure_velocity_coupling"),
            "spatial_discretization": simulation_settings.get("spatial_discretization"),
            "flux_scheme": simulation_settings.get("flux_scheme"),
            "mesh_type": simulation_settings.get("mesh_type"),
            "cell_storage_format": simulation_settings.get("cell_storage_format"),
            "residual_tolerance": simulation_settings.get("residual_tolerance"),
            "max_iterations": simulation_settings.get("max_iterations")
        }
    }
    logger.info("Boundary conditions structured successfully.")
    return boundary_conditions

# Ensure numerical stability via CFL condition
def enforce_numerical_stability(input_data, dx, dt):
    """Checks CFL condition for numerical stability."""
    # Ensure fluid_velocity is a numerical array for norm calculation
    # input_data["fluid_velocity"] is a NumPy array (converted from list), use it directly
    fluid_velocity_array_magnitude = np.linalg.norm(input_data["fluid_velocity"]) # Use directly, as it's just the magnitude

    cfl_value = fluid_velocity_array_magnitude * dt.magnitude / dx.magnitude
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

    # Enforce numerical stability (using the fluid_velocity from input_data)
    enforce_numerical_stability(input_data, dx, dt)

    # Generate boundary conditions (passing dx and dt for simulation settings)
    boundary_conditions = apply_boundary_conditions(input_data, dx, dt)

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
            "fluid_velocity": [3.0, 0.0, 0.0], # Changed to 3.0 to match desired output
            "static_pressure": 101325,
            "density": 1000,
            "viscosity": 0.001002,
            "temperature": 298,
            "simulation_settings": { # Added simulation_settings for the dummy file
                "flow_type": "transient",
                "time_integration_method": "implicit",
                "suggested_time_step": 0.001,
                "CFL_condition": "adaptive",
                "turbulence_model": "RANS_k-epsilon",
                "pressure_velocity_coupling": "SIMPLE",
                "spatial_discretization": "second_order",
                "flux_scheme": "upwind",
                "mesh_type": "unstructured",
                "cell_storage_format": "cell-centered",
                "residual_tolerance": 1e-6,
                "max_iterations": 5000
            }
        }
        if not os.path.exists(default_fluid_input_path):
            with open(default_fluid_input_path, 'w') as f:
                json.dump(dummy_fluid_input_content, f, indent=4)
            logger.info(f"Created dummy fluid input file for testing: {default_fluid_input_path}")

        # No need to create a dummy mesh file for this script's current functionality
        # as it doesn't parse it.

        main(default_mesh_path, default_fluid_input_path)
