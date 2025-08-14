# tests/test_create_inlet_boundary.py

import unittest
import tempfile
import json
import os
from src.create_inlet_boundary import (
    load_flow_data,
    load_boundary_config,
    inject_inlet_boundary,
    save_boundary_config
)

class TestCreateInletBoundary(unittest.TestCase):

    def setUp(self):
        # Sample flow data
        self.flow_data = {
            "initial_conditions": {
                "initial_velocity": [0.602695, -0.122614, 13.4851],
                "initial_pressure": 146.221
            }
        }

        # Sample boundary config
        self.boundary_config = {
            "boundaries": [
                {"name": "wall", "apply_faces": ["x_max"], "type": "no-slip"}
            ]
        }

    def test_load_flow_data(self):
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as f:
            json.dump(self.flow_data, f)
            f.flush()
            velocity, pressure = load_flow_data(f.name)
        os.unlink(f.name)

        self.assertEqual(velocity, [0.602695, -0.122614, 13.4851])
        self.assertEqual(pressure, 146.221)

    def test_inject_inlet_boundary(self):
        velocity = self.flow_data["initial_conditions"]["initial_velocity"]
        pressure = self.flow_data["initial_conditions"]["initial_pressure"]

        updated_config = inject_inlet_boundary(self.boundary_config, velocity, pressure)

        inlet_blocks = [b for b in updated_config["boundaries"] if b["name"] == "inlet"]
        self.assertEqual(len(inlet_blocks), 1)
        self.assertEqual(inlet_blocks[0]["velocity"], velocity)
        self.assertEqual(inlet_blocks[0]["pressure"], pressure)
        self.assertEqual(inlet_blocks[0]["apply_faces"], ["x_min"])
        self.assertEqual(inlet_blocks[0]["type"], "velocity-pressure-inlet")

    def test_save_and_load_boundary_config(self):
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as f:
            save_boundary_config(f.name, self.boundary_config)
            f.flush()
            loaded_config = load_boundary_config(f.name)
        os.unlink(f.name)

        self.assertEqual(loaded_config, self.boundary_config)

    def test_overwrite_existing_inlet(self):
        velocity = [1.0, 0.0, 0.0]
        pressure = 100.0

        config_with_inlet = {
            "boundaries": [
                {"name": "inlet", "apply_faces": ["x_min"], "type": "velocity-pressure-inlet", "velocity": [0,0,0], "pressure": 0}
            ]
        }

        updated_config = inject_inlet_boundary(config_with_inlet, velocity, pressure)
        inlet_blocks = [b for b in updated_config["boundaries"] if b["name"] == "inlet"]

        self.assertEqual(len(inlet_blocks), 1)
        self.assertEqual(inlet_blocks[0]["velocity"], velocity)
        self.assertEqual(inlet_blocks[0]["pressure"], pressure)

if __name__ == "__main__":
    unittest.main()



