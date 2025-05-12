import json
import unittest
import jsonschema
import pyvista as pv
import numpy as np

BOUNDARY_CONDITIONS_FILE = "testing-input-output/boundary_conditions.json"
CONFIG_FILE = "testing-input-output/boundary_conditions_config.json"
MESH_FILE = "testing-input-output/testing-Body.obj"

class TestBoundaryConditions(unittest.TestCase):
    """Unit tests for boundary_conditions.json validation."""

    def setUp(self):
        """Load boundary conditions and config before each test."""
        with open(BOUNDARY_CONDITIONS_FILE, "r") as f:
            self.bc_data = json.load(f)
        
        with open(CONFIG_FILE, "r") as f:
            self.config = json.load(f)

        self.mesh = pv.read(MESH_FILE)

    def test_json_schema(self):
        """Validates JSON structure using a predefined schema."""
        schema = {
            "type": "object",
            "properties": {
                "inlet": {"type": "object", "required": ["region_id", "velocity", "pressure"]},
                "outlet": {"type": "object", "required": ["region_id", "velocity", "pressure"]},
                "walls": {"type": "object", "required": ["region_id", "no_slip"]}
            },
            "required": ["inlet", "outlet", "walls"]
        }
        jsonschema.validate(instance=self.bc_data, schema=schema)

    def test_boundary_classification(self):
        """Ensures inlet, outlet, and walls are correctly classified."""
        inlet_points = set(self.bc_data["inlet"]["region_id"])
        outlet_points = set(self.bc_data["outlet"]["region_id"])

        z_min = np.percentile(self.mesh.points[:, 2], 3)
        z_max = np.percentile(self.mesh.points[:, 2], 97)

        for i, point in enumerate(self.mesh.points):
            if i in inlet_points and point[2] > z_min:
                self.fail(f"❌ Point {i} incorrectly classified as inlet")
            if i in outlet_points and point[2] < z_max:
                self.fail(f"❌ Point {i} incorrectly classified as outlet")

    def test_config_consistency(self):
        """Checks that inlet/outlet velocities and pressures match the configuration file."""
        self.assertEqual(self.bc_data["inlet"]["velocity"], self.config["inlet"]["velocity"], "❌ Inlet velocity mismatch!")
        self.assertEqual(self.bc_data["inlet"]["pressure"], self.config["inlet"]["pressure"], "❌ Inlet pressure mismatch!")
        self.assertEqual(self.bc_data["outlet"]["velocity"], self.config["outlet"]["velocity"], "❌ Outlet velocity mismatch!")
        self.assertEqual(self.bc_data["outlet"]["pressure"], self.config["outlet"]["pressure"], "❌ Outlet pressure mismatch!")

    def test_mesh_integrity(self):
        """Ensures the mesh is valid and contains points before processing."""
        self.assertGreater(self.mesh.n_points, 0, "❌ Mesh file is empty or corrupted.")

    def test_edge_cases(self):
        """Verifies behavior with extreme velocity and pressure values."""
        extreme_config = {
            "inlet": {"velocity": [0.0, 0.0, 0.0], "pressure": -50000},
            "outlet": {"velocity": [9999.0, 0.0, 0.0], "pressure": 999999}
        }
        self.bc_data["inlet"]["velocity"] = extreme_config["inlet"]["velocity"]
        self.bc_data["inlet"]["pressure"] = extreme_config["inlet"]["pressure"]
        self.bc_data["outlet"]["velocity"] = extreme_config["outlet"]["velocity"]
        self.bc_data["outlet"]["pressure"] = extreme_config["outlet"]["pressure"]

        self.assertGreater(self.bc_data["outlet"]["pressure"], 0, "❌ Outlet pressure should be positive!")
        self.assertGreaterEqual(self.bc_data["inlet"]["pressure"], 0, "❌ Inlet pressure should not be negative!")

if __name__ == "__main__":
    unittest.main()



