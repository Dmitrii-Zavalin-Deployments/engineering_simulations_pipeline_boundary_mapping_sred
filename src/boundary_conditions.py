import json
import sys
import pyvista as pv
import numpy as np

CONFIG_FILE = "data/testing-input-output/boundary_conditions_config.json"

def load_config(config_file):
    """Loads inlet boundary condition values from external JSON, ensuring outlet data remains undefined."""
    print(f"🔍 Trying to load: {config_file}")  # Debugging output

    try:
        with open(config_file, "r") as f:
            config = json.load(f)
            print(f"✅ Loaded Config: {config}")  # Debugging output

            # Ensure pressure values are non-negative
            config["inlet"]["pressure"] = max(config["inlet"]["pressure"], 0)

            # Ensure outlet section exists but remains empty
            config.setdefault("outlet", {"velocity": [], "pressure": []})

            return config
    except (FileNotFoundError, json.JSONDecodeError):
        print(f"⚠️ Configuration file {config_file} not found or invalid. Stopping execution.")
        sys.exit(1)

def generate_boundary_conditions(mesh_file, output_file="data/testing-input-output/boundary_conditions.json"):
    """Processes the mesh and creates a structured boundary condition JSON file using improved region detection."""

    # Load mesh
    mesh = pv.read(mesh_file)
    print(f"🔍 Loaded Mesh: {mesh}")

    # Verify Mesh Integrity
    if mesh.n_points == 0:
        sys.exit("❌ Error: Mesh file is empty or corrupted.")

    # Load inlet boundary condition values
    config = load_config(CONFIG_FILE)

    # Initialize Boundary Conditions Structure
    boundary_conditions = {
        "inlet": {
            "region_id": [],
            "velocity": config["inlet"]["velocity"],
            "pressure": config["inlet"]["pressure"]
        },
        "outlet": {
            "region_id": [],
            "velocity": [],
            "pressure": []
        },  # Ensure outlet values remain empty
        "walls": {"region_id": [], "no_slip": True}
    }

    # Compute Percentiles for Improved Boundary Detection
    z_min, z_max = np.percentile(mesh.points[:, 2], [3, 97])  # Lower 3% → Inlet, Upper 3% → Outlet

    # Extract Surface Normals for Wall Detection
    normals = mesh.point_normals if mesh.n_points > 0 else None
    if normals is None:
        print("⚠️ No surface normals found. Wall detection might be inaccurate.")

    # Assign Boundary Regions
    for i, point in enumerate(mesh.points):
        if point[2] > z_max:
            boundary_conditions["outlet"]["region_id"].append(i)  # Outlet (Upper region)
        elif point[2] < z_min:
            boundary_conditions["inlet"]["region_id"].append(i)  # Inlet (Lower region)
        elif normals is not None and np.linalg.norm(normals[i][:2]) > 0.2:
            boundary_conditions["walls"]["region_id"].append(i)  # Walls (Horizontal components detection)

    # Save Boundary Conditions to JSON
    with open(output_file, "w") as f:
        json.dump(boundary_conditions, f, indent=4)

    # ✅ Print JSON to Logs for Visibility
    print("\n🔹 Generated Boundary Conditions:")
    print(json.dumps(boundary_conditions, indent=4))
    print(f"\n✅ Boundary conditions saved to {output_file}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("❌ Usage: python src/boundary_conditions.py <mesh.obj>")

    generate_boundary_conditions(sys.argv[1])
