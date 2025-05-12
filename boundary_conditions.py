import json
import sys
import pyvista as pv

def generate_boundary_conditions(mesh_file, output_file="testing-input-output/boundary_conditions.json"):
    """Processes the mesh and creates a structured boundary condition JSON file."""

    # Load the mesh
    mesh = pv.read(mesh_file)

    # Example logic: Identify boundary regions based on surface normals or position
    boundary_conditions = {
        "inlet": {"region_id": [], "velocity": [1.0, 0.0, 0.0]},
        "outlet": {"region_id": [], "pressure": 101325},
        "walls": {"region_id": [], "no_slip": True}
    }

    # Example: Loop through mesh points and assign regions (simplified)
    for i, point in enumerate(mesh.points):
        if point[2] > 0.9:  # Example condition: top surface is the outlet
            boundary_conditions["outlet"]["region_id"].append(i)
        elif point[2] < 0.1:  # Example condition: bottom surface is the inlet
            boundary_conditions["inlet"]["region_id"].append(i)
        else:
            boundary_conditions["walls"]["region_id"].append(i)

    # Save boundary conditions to JSON
    with open(output_file, "w") as f:
        json.dump(boundary_conditions, f, indent=4)

    # ✅ Print JSON to logs for visibility
    print("\n🔹 Generated Boundary Conditions:")
    print(json.dumps(boundary_conditions, indent=4))

    print(f"\n✅ Boundary conditions saved to {output_file}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("❌ Usage: python boundary_conditions.py <mesh.obj>")
        sys.exit(1)

    mesh_file = sys.argv[1]
    generate_boundary_conditions(mesh_file)


