import os
import json
import numpy as np
from pint import UnitRegistry
import logging
import trimesh # Still required for robust OBJ parsing

# Initialize unit registry for physical properties
ureg = UnitRegistry()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Configuration for Geometric Boundary Identification ---
# This tolerance defines how "close" a face's vertices must be to the min/max X-coordinate
# to be considered an inlet/outlet. Adjust this if your mesh has slight curves or
# if boundaries aren't perfectly planar at the X-extrema.
BOUNDARY_X_TOLERANCE = 1e-4 # meters (adjust as needed based on your mesh's scale)
# --------------------------------------------------------

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

    # We still need the boundary *properties* from the JSON, even if faces come from OBJ.
    if "boundary_properties_config" not in input_data or not isinstance(input_data["boundary_properties_config"], dict):
        logger.error("❌ ERROR: 'boundary_properties_config' section is missing or malformed in the input file. This is now required and must be a dictionary.")
        raise ValueError("❌ ERROR: 'boundary_properties_config' section is missing or malformed in the input file.")

    logger.info("Input data loaded and units processed.")
    return input_data

def parse_mesh_boundaries(mesh_file_path, tolerance=BOUNDARY_X_TOLERANCE):
    """
    Parses the OBJ mesh file to identify and return lists of face IDs for
    inlets, outlets, and walls based on geometric extents (min/max X-coordinates)
    with a given tolerance. Assumes flow is primarily along the X-axis.
    """
    logger.info(f"Parsing mesh file: {mesh_file_path} to determine boundary faces based on geometry with tolerance {tolerance}.")

    if not os.path.exists(mesh_file_path):
        logger.error(f"❌ ERROR: Mesh file '{mesh_file_path}' was not found.")
        raise FileNotFoundError(f"❌ ERROR: Mesh file '{mesh_file_path}' was not found.")

    try:
        # Load the mesh using trimesh
        mesh = trimesh.load(mesh_file_path)
    except Exception as e:
        logger.error(f"❌ ERROR: Failed to load mesh file '{mesh_file_path}'. Ensure it's a valid OBJ. Error: {e}")
        raise ValueError(f"❌ ERROR: Failed to load mesh file '{mesh_file_path}'. Error: {e}")

    if mesh.vertices is None or mesh.faces is None or len(mesh.faces) == 0:
        logger.error("❌ ERROR: Mesh loaded but contains no vertices or faces. Cannot determine boundaries.")
        raise ValueError("❌ ERROR: Mesh loaded but contains no vertices or faces.")

    # Calculate bounding box extents
    min_x = mesh.vertices[:, 0].min()
    max_x = mesh.vertices[:, 0].max()

    inlet_faces = []
    outlet_faces = []
    wall_faces = []

    # Iterate through each face and classify it
    for face_idx, face_vertices_indices in enumerate(mesh.faces):
        # Get the actual vertex coordinates for the current face
        face_vertices = mesh.vertices[face_vertices_indices]
        face_x_coords = face_vertices[:, 0]

        # Check if ALL vertices of this face are within the 'inlet' X-zone
        # i.e., all X-coordinates of the face are less than (min_x + tolerance)
        is_inlet_zone = np.all(face_x_coords <= (min_x + tolerance))

        # Check if ALL vertices of this face are within the 'outlet' X-zone
        # i.e., all X-coordinates of the face are greater than (max_x - tolerance)
        is_outlet_zone = np.all(face_x_coords >= (max_x - tolerance))


        if is_inlet_zone and is_outlet_zone:
            # This case indicates a very thin mesh or a closed domain where min/max X are very close.
            # Or a face that spans the entire domain. Classify as wall.
            logger.warning(f"⚠️ Face {face_idx} spans both min and max X-zones (within tolerance). Classifying as wall.")
            wall_faces.append(face_idx)
        elif is_inlet_zone:
            # Additional check: Ensure the face is actually *on* the min X boundary, not just in the zone.
            # At least one vertex must be very close to min_x.
            if np.any(np.isclose(face_x_coords, min_x, atol=tolerance)):
                inlet_faces.append(face_idx)
            else:
                wall_faces.append(face_idx)
        elif is_outlet_zone:
            # Additional check: Ensure the face is actually *on* the max X boundary.
            if np.any(np.isclose(face_x_coords, max_x, atol=tolerance)):
                outlet_faces.append(face_idx)
            else:
                wall_faces.append(face_idx)
        else:
            wall_faces.append(face_idx) # All other faces are walls

    if not inlet_faces:
        logger.warning(f"⚠️ No inlet faces identified based on X-coordinate range [{min_x}, {min_x+tolerance}]. Please check mesh geometry or 'BOUNDARY_X_TOLERANCE'.")
    if not outlet_faces:
        logger.warning(f"⚠️ No outlet faces identified based on X-coordinate range [{max_x-tolerance}, {max_x}]. Please check mesh geometry or 'BOUNDARY_X_TOLERANCE'.")
    if len(inlet_faces) + len(outlet_faces) + len(wall_faces) != len(mesh.faces):
        logger.error("❌ ERROR: Discrepancy in total classified faces vs. total mesh faces. Some faces might be unclassified.")
        raise RuntimeError("Face classification error.")

    logger.info(f"Mesh boundary faces identified: Inlet {len(inlet_faces)}, Outlet {len(outlet_faces)}, Wall {len(wall_faces)} (Total: {len(mesh.faces)}).")
    return inlet_faces, outlet_faces, wall_faces

def apply_boundary_conditions(input_data, dx_value, dt_value, mesh_file_path):
    """Assigns inlet, outlet, and wall boundary conditions based on input_data
       and simulation parameters dx, dt, and mesh boundary information from OBJ."""

    logger.info("Applying boundary conditions from input data and mesh parsing...")

    # Get boundary face IDs by parsing the actual mesh file
    inlet_faces, outlet_faces, wall_faces = parse_mesh_boundaries(mesh_file_path, tolerance=BOUNDARY_X_TOLERANCE)

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

    # Retrieve all boundary type and property information directly from input_data's new section
    boundary_props_config = input_data["boundary_properties_config"] # Already checked to be a dict

    # Validate required boundary condition sections
    required_boundaries_sections = ["inlet_boundary", "outlet_boundary", "wall_boundary"]
    for section_name in required_boundaries_sections:
        if section_name not in boundary_props_config or not isinstance(boundary_props_config[section_name], dict):
            logger.error(f"❌ ERROR: Required boundary section '{section_name}' is missing or malformed (not a dictionary) in 'boundary_properties_config' in the input file.")
            raise ValueError(f"❌ ERROR: Required boundary section '{section_name}' must be provided as a dictionary in input.")

    inlet_bc_props = boundary_props_config["inlet_boundary"]
    outlet_bc_props = boundary_props_config["outlet_boundary"]
    wall_bc_props = boundary_props_config["wall_boundary"]

    # Validate essential properties within boundary sections
    if "type" not in inlet_bc_props:
        logger.error("❌ ERROR: 'type' is missing for 'inlet_boundary' in 'boundary_properties_config'.")
        raise ValueError("❌ ERROR: 'type' is required for 'inlet_boundary'.")
    if "type" not in outlet_bc_props:
        logger.error("❌ ERROR: 'type' is missing for 'outlet_boundary' in 'boundary_properties_config'.")
        raise ValueError("❌ ERROR: 'type' is required for 'outlet_boundary'.")
    if "no_slip" not in wall_bc_props:
        logger.error("❌ ERROR: 'no_slip' is missing for 'wall_boundary' in 'boundary_properties_config'.")
        raise ValueError("❌ ERROR: 'no_slip' is required for 'wall_boundary'.")
    if "wall_properties" not in wall_bc_props or not isinstance(wall_bc_props["wall_properties"], dict):
        logger.error("❌ ERROR: 'wall_properties' is missing or malformed for 'wall_boundary' in 'boundary_properties_config'.")
        raise ValueError("❌ ERROR: 'wall_properties' is required for 'wall_boundary'.")
    if "roughness" not in wall_bc_props["wall_properties"]:
        logger.error("❌ ERROR: 'roughness' is missing for 'wall_properties' in 'wall_boundary' in 'boundary_properties_config'.")
        raise ValueError("❌ ERROR: 'roughness' is required for 'wall_properties'.")
    if "heat_transfer" not in wall_bc_props["wall_properties"]:
        logger.error("❌ ERROR: 'heat_transfer' is missing for 'wall_properties' in 'wall_boundary' in 'boundary_properties_config'.")
        raise ValueError("❌ ERROR: 'heat_transfer' is required for 'wall_properties'.")
    if "wall_functions" not in wall_bc_props:
        logger.error("❌ ERROR: 'wall_functions' is missing for 'wall_boundary' in 'boundary_properties_config'.")
        raise ValueError("❌ ERROR: 'wall_functions' is required for 'wall_boundary'.")
    if "velocity" not in outlet_bc_props:
        logger.error("❌ ERROR: 'velocity' is missing for 'outlet_boundary' in 'boundary_properties_config' (use null if velocity is unknown/calculated).")
        raise ValueError("❌ ERROR: 'velocity' is required for 'outlet_boundary' (can be null).")

    # Build the final boundary conditions dictionary
    boundary_conditions = {
        "inlet_faces": inlet_faces, # Populated from OBJ parsing
        "inlet_boundary": {
            "type": inlet_bc_props["type"],
            "pressure": inlet_pressure_magnitude,
            "fluid_properties": {
                "temperature": fluid_temperature_magnitude,
                "density": fluid_density_magnitude,
                "viscosity": fluid_viscosity_magnitude
            }
        },
        "outlet_faces": outlet_faces, # Populated from OBJ parsing
        "outlet_boundary": {
            "type": outlet_bc_props["type"],
            "velocity": outlet_bc_props["velocity"]
        },
        "wall_faces": wall_faces, # Populated from OBJ parsing
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

    logger.info("Boundary conditions structured successfully from input data and mesh parsing.")
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

    # Load fluid input data
    input_data = load_input_file(fluid_input_file_path)

    # Enforce numerical stability (CFL check only if fluid_velocity is provided in input)
    enforce_numerical_stability(input_data, dx, dt)

    # Generate boundary conditions, passing mesh_file_path to apply_boundary_conditions
    boundary_conditions = apply_boundary_conditions(input_data, dx, dt, mesh_file_path)

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
        logger.info("ℹ️ Running with default local paths for testing. Ensure 'fluid_simulation_input.json' and 'simulation_mesh.obj' exist at the specified paths.")
        # Adjust these paths if your local setup differs
        default_mesh_path = "../downloaded_simulation_files/simulation_mesh.obj"
        default_fluid_input_path = "../downloaded_simulation_files/fluid_simulation_input.json"

        # IMPORTANT: The user MUST provide fluid_simulation_input.json and simulation_mesh.obj externally.
        # If the files are missing or incomplete, the script will raise errors.

        # Create dummy input directory if it doesn't exist
        dummy_input_dir = os.path.dirname(default_fluid_input_path)
        if not os.path.exists(dummy_input_dir):
            os.makedirs(dummy_input_dir)
            logger.info(f"Created dummy input directory: {dummy_input_dir}")

        main(default_mesh_path, default_fluid_input_path)
