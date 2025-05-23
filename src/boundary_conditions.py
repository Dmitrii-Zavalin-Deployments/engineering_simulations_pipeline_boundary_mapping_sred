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
    """Reads input JSON file with fluid properties and simulation settings."""
    if not os.path.exists(file_path):
        logger.error(f"❌ ERROR: The input file '{file_path}' was not found.")
        raise FileNotFoundError(f"❌ ERROR: The input file '{file_path}' was not found.")

    logger.info(f"Loading input data from: {file_path}")
    with open(file_path, 'r') as file:
        input_data = json.load(file)

    # All required fluid properties must be present
    required_fluid_properties = ["static_pressure", "temperature", "density", "viscosity"]
    for prop in required_fluid_properties:
        if prop not in input_data:
            logger.error(f"❌ ERROR: Required fluid property '{prop}' not found in input data.")
            raise ValueError(f"❌ ERROR: Required fluid property '{prop}' not found in input data.")

    input_data["static_pressure"] *= ureg.pascal
    input_data["density"] *= ureg.kilogram / ureg.meter**3
    input_data["viscosity"] *= ureg.pascal * ureg.second
    input_data["temperature"] *= ureg.kelvin

    # Ensure simulation_settings exist, it can be empty but must be a dict
    if "simulation_settings" not in input_data or not isinstance(input_data["simulation_settings"], dict):
        logger.error("❌ ERROR: 'simulation_settings' section is missing or malformed in the input file. It must be a dictionary.")
        raise ValueError("❌ ERROR: 'simulation_settings' section is missing or malformed in the input file.")

    # Ensure boundary_conditions_input exist and are structured
    if "boundary_conditions_input" not in input_data or not isinstance(input_data["boundary_conditions_input"], dict):
        logger.error("❌ ERROR: 'boundary_conditions_input' section is missing or malformed in the input file. This is now required and must be a dictionary.")
        raise ValueError("❌ ERROR: 'boundary_conditions_input' section is missing or malformed in the input file.")

    logger.info("Input data loaded and units processed.")
    return input_data

def parse_mesh_boundaries(input_data):
    """
    Function to retrieve boundary face IDs from the input_data.
    All face IDs must be explicitly provided in the input JSON.
    """
    logger.info("Retrieving mesh boundary faces from input data.")

    bc_input = input_data["boundary_conditions_input"]

    required_face_lists = ["inlet_faces", "outlet_faces", "wall_faces"]
    for face_list_name in required_face_lists:
        if face_list_name not in bc_input or not isinstance(bc_input[face_list_name], list):
            logger.error(f"❌ ERROR: Required face list '{face_list_name}' is missing or not a list under 'boundary_conditions_input' in the input file.")
            raise ValueError(f"❌ ERROR: Required face list '{face_list_name}' must be provided as a list in the input JSON.")

    inlet_faces = bc_input["inlet_faces"]
    outlet_faces = bc_input["outlet_faces"]
    wall_faces = bc_input["wall_faces"]

    logger.info("Mesh boundary faces retrieved from input.")
    return inlet_faces, outlet_faces, wall_faces

def apply_boundary_conditions(input_data, dx_value, dt_value):
    """Assigns inlet, outlet, and wall boundary conditions based on input_data
       and simulation parameters dx, dt."""

    logger.info("Applying boundary conditions from input data...")

    # Get boundary face IDs
    inlet_faces, outlet_faces, wall_faces = parse_mesh_boundaries(input_data)

    # Extract magnitudes from Pint quantities for JSON serialization
    inlet_pressure_magnitude = input_data["static_pressure"].to(ureg.pascal).magnitude
    fluid_temperature_magnitude = input_data["temperature"].to(ureg.kelvin).magnitude
    fluid_density_magnitude = input_data["density"].to(ureg.kilogram / ureg.meter**3).magnitude
    fluid_viscosity_magnitude = input_data["viscosity"].to(ureg.pascal * ureg.second).magnitude

    # Suggested time step is now explicitly retrieved from simulation_settings in input_data
    simulation_settings = input_data["simulation_settings"] # Already checked to be a dict in load_input_file
    if "suggested_time_step" not in simulation_settings:
        logger.error("❌ ERROR: 'suggested_time_step' is missing from 'simulation_settings' in the input file. This is required.")
        raise ValueError("❌ ERROR: 'suggested_time_step' is required in simulation_settings.")
    suggested_time_step_magnitude = simulation_settings["suggested_time_step"]


    # Retrieve all boundary type and property information directly from input_data
    boundary_conditions_input = input_data["boundary_conditions_input"] # Already checked to be a dict

    # Validate required boundary condition sections
    required_boundaries_sections = ["inlet_boundary", "outlet_boundary", "wall_boundary"]
    for section_name in required_boundaries_sections:
        if section_name not in boundary_conditions_input or not isinstance(boundary_conditions_input[section_name], dict):
            logger.error(f"❌ ERROR: Required boundary section '{section_name}' is missing or malformed (not a dictionary) in 'boundary_conditions_input' in the input file.")
            raise ValueError(f"❌ ERROR: Required boundary section '{section_name}' must be provided as a dictionary in input.")

    inlet_bc_props = boundary_conditions_input["inlet_boundary"]
    outlet_bc_props = boundary_conditions_input["outlet_boundary"]
    wall_bc_props = boundary_conditions_input["wall_boundary"]

    # Validate essential properties within boundary sections
    if "type" not in inlet_bc_props:
        logger.error("❌ ERROR: 'type' is missing for 'inlet_boundary' in the input file.")
        raise ValueError("❌ ERROR: 'type' is required for 'inlet_boundary'.")
    if "type" not in outlet_bc_props:
        logger.error("❌ ERROR: 'type' is missing for 'outlet_boundary' in the input file.")
        raise ValueError("❌ ERROR: 'type' is required for 'outlet_boundary'.")
    if "no_slip" not in wall_bc_props:
        logger.error("❌ ERROR: 'no_slip' is missing for 'wall_boundary' in the input file.")
        raise ValueError("❌ ERROR: 'no_slip' is required for 'wall_boundary'.")
    if "wall_properties" not in wall_bc_props or not isinstance(wall_bc_props["wall_properties"], dict):
        logger.error("❌ ERROR: 'wall_properties' is missing or malformed for 'wall_boundary' in the input file.")
        raise ValueError("❌ ERROR: 'wall_properties' is required for 'wall_boundary'.")
    if "roughness" not in wall_bc_props["wall_properties"]:
        logger.error("❌ ERROR: 'roughness' is missing for 'wall_properties' in 'wall_boundary' in the input file.")
        raise ValueError("❌ ERROR: 'roughness' is required for 'wall_properties'.")
    if "heat_transfer" not in wall_bc_props["wall_properties"]:
        logger.error("❌ ERROR: 'heat_transfer' is missing for 'wall_properties' in 'wall_boundary' in the input file.")
        raise ValueError("❌ ERROR: 'heat_transfer' is required for 'wall_properties'.")
    if "wall_functions" not in wall_bc_props:
        logger.error("❌ ERROR: 'wall_functions' is missing for 'wall_boundary' in the input file.")
        raise ValueError("❌ ERROR: 'wall_functions' is required for 'wall_boundary'.")
    if "velocity" not in outlet_bc_props: # Check for velocity specifically for outlet
        logger.error("❌ ERROR: 'velocity' is missing for 'outlet_boundary' in the input file (use null if velocity is unknown/calculated).")
        raise ValueError("❌ ERROR: 'velocity' is required for 'outlet_boundary' (can be null).")


    # Build the final boundary conditions dictionary
    boundary_conditions = {
        "inlet_faces": inlet_faces,
        "inlet_boundary": {
            "type": inlet_bc_props["type"],
            "pressure": inlet_pressure_magnitude,
            "fluid_properties": {
                "temperature": fluid_temperature_magnitude,
                "density": fluid_density_magnitude,
                "viscosity": fluid_viscosity_magnitude
            }
        },
        "outlet_faces": outlet_faces,
        "outlet_boundary": {
            "type": outlet_bc_props["type"],
            "velocity": outlet_bc_props["velocity"]
        },
        "wall_faces": wall_faces,
        "wall_boundary": {
            "no_slip": wall_bc_props["no_slip"],
            "wall_properties": {
                "roughness": wall_bc_props["wall_properties"]["roughness"],
                "heat_transfer": wall_bc_props["wall_properties"]["heat_transfer"]
            },
            "wall_functions": wall_bc_props["wall_functions"]
        },
        "simulation_settings": simulation_settings # This will include only what's in the input
    }

    # Ensure cell_storage_format is directly taken from simulation_settings if present
    # No more typo, and no default if missing
    if "cell_storage_format" not in simulation_settings:
        logger.warning("⚠️ 'cell_storage_format' not found in simulation_settings. It will be omitted from the output.")
    # The entire simulation_settings dict is assigned, so individual keys are handled.

    logger.info("Boundary conditions structured successfully from input data.")
    return boundary_conditions

def enforce_numerical_stability(input_data, dx, dt):
    """
    Checks CFL condition for numerical stability. Requires 'fluid_velocity'
    to be explicitly provided in the input data for this check.
    If 'fluid_velocity' is not present, the check is skipped and a warning is logged.
    """
    if "fluid_velocity" not in input_data:
        logger.warning("⚠️ Skipping CFL check: 'fluid_velocity' not found in input data. Cannot calculate CFL.")
        return # Skip the check if velocity isn't provided

    if not isinstance(input_data["fluid_velocity"], (int, float)):
        logger.error("❌ ERROR: 'fluid_velocity' in input data must be a numerical value.")
        raise ValueError("❌ ERROR: 'fluid_velocity' must be a numerical value for CFL check.")

    characteristic_velocity_magnitude = input_data["fluid_velocity"] # Assumed to be in m/s directly from input
    logger.info(f"Performing CFL check using fluid_velocity: {characteristic_velocity_magnitude} m/s.")

    cfl_value = characteristic_velocity_magnitude * dt.to(ureg.second).magnitude / dx.to(ureg.meter).magnitude
    logger.info(f"Calculated CFL value: {cfl_value:.4f}.")

    if cfl_value > 1:
        logger.error(f"❌ ERROR: CFL condition violated – CFL = {cfl_value:.4f}. Adjust time-step or grid spacing.")
        raise ValueError(f"❌ ERROR: CFL condition violated – CFL = {cfl_value:.4f}. Adjust time-step or grid spacing.")
    logger.info("CFL condition satisfied.")

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

def main(mesh_file_path, fluid_input_file_path, dx=0.01 * ureg.meter, dt=0.001 * ureg.second):
    """Executes boundary condition processing pipeline."""

    logger.info("Starting boundary condition processing pipeline.")

    # Load input data from fluid_simulation_input.json
    input_data = load_input_file(fluid_input_file_path)

    # Enforce numerical stability (CFL check only if fluid_velocity is provided in input)
    enforce_numerical_stability(input_data, dx, dt)

    # Generate boundary conditions
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
        logger.info("ℹ️ Running with default local paths for testing. Ensure 'fluid_simulation_input.json' exists at the specified path.")
        # Adjust these paths if your local setup differs
        default_mesh_path = "../downloaded_simulation_files/simulation_mesh.obj" # Still a placeholder; actual parsing would go here.
        default_fluid_input_path = "../downloaded_simulation_files/fluid_simulation_input.json"

        # Create dummy input directory if it doesn't exist
        dummy_input_dir = os.path.dirname(default_fluid_input_path)
        if not os.path.exists(dummy_input_dir):
            os.makedirs(dummy_input_dir)
            logger.info(f"Created dummy input directory: {dummy_input_dir}")

        # IMPORTANT: This block no longer creates a dummy fluid_simulation_input.json
        # The user MUST provide it externally at default_fluid_input_path.
        # If the file is missing or incomplete, the script will raise errors.

        main(default_mesh_path, default_fluid_input_path)
