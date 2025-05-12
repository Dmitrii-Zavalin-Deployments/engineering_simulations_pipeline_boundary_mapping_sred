import json
import sys
import pyvista as pv
import numpy as np

CONFIG_FILE = "testing-input-output/boundary_conditions_config.json"

def load_config(config_file):
    """Loads inlet and outlet boundary condition values from external JSON, with error handling."""
    try:
        with open(config_file, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print(f"⚠️ Configuration file {config_file} not found or invalid. Using default values.")
        return {
            "inlet": {"velocity": [1.0, 0.0, 0.0], "pressure": 100000},
            "outlet": {"velocity": [0.0, 0.0, -1.0], "pressure": 101325}
        }

def generate_boundary_conditions(mesh_file, output_file="testing-input-output/boundary_conditions.json"):
    """Processes the mesh and creates a structured boundary condition JSON file using improved region detection."""

    # Load mesh
    mesh = pv.read(mesh_file)
    print(f"🔍 Loaded Mesh: {mesh}")

    # Verify Mesh Integrity
    if mesh.n_points == 0:
        print("❌ Error: Mesh file is empty or corrupted.")
        sys.exit(1)

    # Load velocity and pressure values from configuration file
    config = load_config(CONFIG_FILE)

    # Initialize Boundary Conditions Structure
    boundary_conditions = {
        "inlet": {"region_id": [], "velocity": config["inlet"]["velocity"], "pressure": config["inlet"]["pressure"]},
        "outlet": {"region_id": [], "velocity": config["outlet"]["velocity"], "pressure": config["outlet"]["pressure"]},
        "walls": {"region_id": [], "no_slip": True}
    }

    # Compute Percentiles for Improved Boundary Detection
    z_min = np.percentile(mesh.points[:, 2], 3)  # Lower 3% → Inlet
    z_max = np.percentile(mesh.points[:, 2], 97)  # Upper 3% → Outlet

    # Extract Surface Normals for Wall Detection
    normals = mesh.point_normals if mesh.n_points > 0 else None
    if normals is None:
        print("⚠️ No surface normals found. Wall detection might be inaccurate.")

    # Assign Boundary Regions
    for i, point in enumerate(mesh.points):
        if point[2] > z_max:  # Outlet (Upper region)
            boundary_conditions["outlet"]["region_id"].append(i)
        elif point[2] < z_min:  # Inlet (Lower region)
            boundary_conditions["inlet"]["region_id"].append(i)
        elif normals is not None and np.linalg.norm(normals[i][:2]) > 0.2:  # Walls (Horizontal components detection)
            boundary_conditions["walls"]["region_id"].append(i)

    # Save Boundary Conditions to JSON
    with open(output_file, "w") as f:
        json.dump(boundary_conditions, f, indent=4)

    # ✅ Print JSON to Logs for Visibility
    print("\n🔹 Generated Boundary Conditions:")
    print(json.dumps(boundary_conditions, indent=4))
    print(f"\n✅ Boundary conditions saved to {output_file}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("❌ Usage: python boundary_conditions.py <mesh.obj>")
        sys.exit(1)

    mesh_file = sys.argv[1]
    generate_boundary_conditions(mesh_file)




