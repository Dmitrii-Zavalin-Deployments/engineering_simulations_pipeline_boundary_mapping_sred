import json
import unittest
import jsonschema
import pyvista as pv
import numpy as np

# ✅ Updated configuration file path
BOUNDARY_CONDITIONS_FILE = "data/testing-input-output/boundary_conditions_config.json"
CONFIG_FILE = "data/testing-input-output/boundary_conditions_config.json"
MESH_FILE = "data/testing-input-output/testing-Body.obj"

class TestBoundaryConditions(unittest.TestCase):
    """Unit tests for boundary_conditions.json validation."""

    def setUp(self):
        """Load boundary conditions and config before each test."""
        with open(BOUNDARY_CONDITIONS_FILE, "r") as f:
            self.bc_data = json.load(f)
        
        with open(CONFIG_FILE, "r") as f:
            self.config = json.load(f)

        self.mesh = pv.read(MESH_FILE)

        # Ensure pressure values are non-negative in configuration
        self.config["inlet"]["pressure"] = max(self.config["inlet"]["pressure"], 0)

        # Ensure outlet section exists but remains empty
        self.config.setdefault("outlet", {})
        self.config["outlet"]["velocity"] = []
        self.config["outlet"]["pressure"] = []

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
                self.fail(f"❌ Point {i} incorrectly classified as inlet (Height {point[2]})")
            if i in outlet_points and point[2] < z_max:
                self.fail(f"❌ Point {i} incorrectly classified as outlet (Height {point[2]})")

    def test_config_consistency(self):
        """Checks that inlet velocities and pressures match the configuration file."""
        self.assertEqual(self.bc_data["inlet"]["velocity"], self.config["inlet"]["velocity"], "❌ Inlet velocity mismatch!")
        self.assertEqual(self.bc_data["inlet"]["pressure"], self.config["inlet"]["pressure"], "❌ Inlet pressure mismatch!")

    def test_outlet_section_empty(self):
        """Ensures outlet exists but remains unassigned."""
        self.assertIn("outlet", self.bc_data, "❌ Outlet section missing!")

        # Validate outlet velocity and pressure are empty lists
        self.assertEqual(self.bc_data["outlet"]["velocity"], [], "❌ Outlet velocity should be empty!")
        self.assertEqual(self.bc_data["outlet"]["pressure"], [], "❌ Outlet pressure should be empty!")

        # Ensure outlet exists as a properly formatted dictionary
        self.assertIsInstance(self.bc_data["outlet"], dict, "❌ Outlet section should be a dictionary!")

    def test_mesh_integrity(self):
        """Ensures the mesh is valid and contains points before processing."""
        self.assertGreater(self.mesh.n_points, 0, "❌ Mesh file is empty or corrupted.")

if __name__ == "__main__":
    unittest.main()
