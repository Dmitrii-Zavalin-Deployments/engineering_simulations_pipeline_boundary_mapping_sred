import unittest
import numpy as np
import unittest.mock as mock
import os
import json

# Import the functions directly
from src.boundary_conditions import load_input_file, parse_mesh_boundaries, apply_boundary_conditions, enforce_numerical_stability, ureg

class TestBoundaryConditionIntegration(unittest.TestCase):

    # Correct order for patching setUp: mock_open_file comes first after self
    @mock.patch('builtins.open', new_callable=mock.mock_open)
    @mock.patch('os.path.exists', return_value=True)
    def setUp(self, mock_exists, mock_open_file): # mock_exists is now the second argument
        """Set up mock input data and common mock objects for boundary condition validation."""

        # Mock input data structure that matches the expected JSON structure
        self.mock_fluid_input_data = {
            "fluid_velocity": 2.5,
            "static_pressure": 101325,
            "temperature": 298,
            "density": 1000,
            "viscosity": 0.001002,
            "simulation_settings": {
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
                "residual_tolerance": 1e-06,
                "max_iterations": 5000
            },
            "boundary_properties_config": {
                "inlet_boundary": {
                    "type": "pressure_inlet"
                },
                "outlet_boundary": {
                    "type": "velocity_outlet",
                    "velocity": None
                },
                "wall_boundary": {
                    "no_slip": True,
                    "wall_properties": {
                        "roughness": 0.002,
                        "heat_transfer": False
                    },
                    "wall_functions": "standard"
                }
            }
        }
        # Reset mock_open to provide the actual JSON data for tests that call load_input_file
        mock_open_file.return_value.__enter__.return_value.read.return_value = json.dumps(self.mock_fluid_input_data)

        # Mock mesh data for trimesh.load
        self.mock_mesh_data_x_axis = mock.Mock()
        self.mock_mesh_data_x_axis.vertices = np.array([
            [0, 0, 0], [0, 1, 0], [0, 0, 1], # Inlet faces (min X)
            [1, 0, 0], [1, 1, 0], [1, 0, 1], # Outlet faces (max X)
            [0, 0, 0], [1, 0, 0], [0.5, 0.5, 0.5], # Wall faces (mid-domain)
            [0, 1, 0], [1, 1, 0], [0.5, 0.5, 0.5],
            [0, 0, 1], [1, 0, 1], [0.5, 0.5, 0.5],
            [0, 1, 1], [1, 1, 1], [0.5, 0.5, 0.5],
            [0, 1, 0], [0, 1, 1], [0, 0, 1] # Another set of inlet
        ])
        # Faces connecting vertices (simplified for testing, actual faces aren't calculated)
        self.mock_mesh_data_x_axis.faces = np.array([
            [0, 1, 2], # Represents an inlet face
            [3, 4, 5], # Represents an outlet face
            [6, 7, 8], [9, 10, 11], [12, 13, 14], [15, 16, 17], # Walls
            [18, 19, 20] # Another inlet face to ensure multiple are found
        ])

        self.mock_mesh_data_y_axis = mock.Mock()
        self.mock_mesh_data_y_axis.vertices = np.array([
            [0, 0, 0], [1, 0, 0], [0, 0, 1], # Inlet faces (min Y)
            [0, 1, 0], [1, 1, 0], [0, 1, 1], # Outlet faces (max Y)
            [0, 0, 0], [0, 1, 0], [0.5, 0.5, 0.5], # Walls
        ])
        self.mock_mesh_data_y_axis.faces = np.array([
            [0, 1, 2], # Inlet
            [3, 4, 5], # Outlet
            [6, 7, 8]  # Wall
        ])

        self.mock_mesh_data_z_axis = mock.Mock()
        self.mock_mesh_data_z_axis.vertices = np.array([
            [0, 0, 0], [1, 0, 0], [0, 1, 0], # Inlet faces (min Z)
            [0, 0, 1], [1, 0, 1], [0, 1, 1], # Outlet faces (max Z)
            [0, 0, 0], [0, 0, 1], [0.5, 0.5, 0.5], # Walls
        ])
        self.mock_mesh_data_z_axis.faces = np.array([
            [0, 1, 2], # Inlet
            [3, 4, 5], # Outlet
            [6, 7, 8]  # Wall
        ])

    @mock.patch('trimesh.load')
    @mock.patch('os.path.exists', return_value=True)
    @mock.patch('builtins.open', new_callable=mock.mock_open)
    def test_apply_boundary_conditions_success(self, mock_open_file, mock_exists, mock_trimesh_load):
        """
        Tests that apply_boundary_conditions runs successfully and produces
        a well-structured output with correct data types and values.
        """
        # Configure mock_open_file to return the mock input data
        mock_open_file.return_value.__enter__.return_value.read.return_value = json.dumps(self.mock_fluid_input_data)

        # Configure trimesh.load to return the mock mesh data
        mock_trimesh_load.return_value = self.mock_mesh_data_x_axis

        dx_val = 0.01 * ureg.meter
        dt_val = 0.001 * ureg.second
        mesh_file_path = "mock_mesh.obj"
        input_file_path = "mock_input.json"

        boundary_conditions = apply_boundary_conditions(
            load_input_file(input_file_path), dx_val, dt_val, mesh_file_path
        )

        self.assertIsInstance(boundary_conditions, dict)
        self.assertIn("inlet_faces", boundary_conditions)
        self.assertIn("outlet_faces", boundary_conditions)
        self.assertIn("wall_faces", boundary_conditions)
        self.assertIsInstance(boundary_conditions["inlet_faces"], list)
        self.assertIsInstance(boundary_conditions["outlet_faces"], list)
        self.assertIsInstance(boundary_conditions["wall_faces"], list)

        # Verify that faces are classified (mock_mesh_data_x_axis has 2 inlet, 1 outlet, 4 wall faces)
        self.assertGreater(len(boundary_conditions["inlet_faces"]), 0)
        self.assertGreater(len(boundary_conditions["outlet_faces"]), 0)
        self.assertGreater(len(boundary_conditions["wall_faces"]), 0)

        # Check a few specific values
        self.assertEqual(boundary_conditions["inlet_boundary"]["pressure"], 101325)
        self.assertEqual(boundary_conditions["outlet_boundary"]["velocity"], None)
        self.assertTrue(boundary_conditions["wall_boundary"]["no_slip"])
        self.assertEqual(boundary_conditions["simulation_settings"]["suggested_time_step"], 0.001)


    @mock.patch('trimesh.load')
    @mock.patch('os.path.exists', return_value=True)
    @mock.patch('builtins.open', new_callable=mock.mock_open) # Need to mock open for load_input_file in this test
    def test_parse_mesh_boundaries_picks_correct_axis(self, mock_open_file, mock_exists, mock_trimesh_load):
        """
        Tests that parse_mesh_boundaries correctly identifies boundaries
        on the X, Y, or Z axis based on which one has distinct inlet/outlet.
        """
        # Configure mock_open_file to return the mock input data for load_input_file
        mock_open_file.return_value.__enter__.return_value.read.return_value = json.dumps(self.mock_fluid_input_data)

        # Test X-axis preferred
        mock_trimesh_load.return_value = self.mock_mesh_data_x_axis
        inlet, outlet, wall = parse_mesh_boundaries("mock_mesh.obj")
        self.assertGreater(len(inlet), 0, "Should find inlets on X-axis")
        self.assertGreater(len(outlet), 0, "Should find outlets on X-axis")
        self.assertGreater(len(wall), 0, "Should find walls on X-axis")
        # Ensure the sum matches total faces
        self.assertEqual(len(inlet) + len(outlet) + len(wall), len(self.mock_mesh_data_x_axis.faces))

        # Test Y-axis preferred (reset mock)
        mock_trimesh_load.reset_mock()
        mock_trimesh_load.return_value = self.mock_mesh_data_y_axis
        inlet, outlet, wall = parse_mesh_boundaries("mock_mesh.obj")
        self.assertGreater(len(inlet), 0, "Should find inlets on Y-axis")
        self.assertGreater(len(outlet), 0, "Should find outlets on Y-axis")
        self.assertGreater(len(wall), 0, "Should find walls on Y-axis")
        self.assertEqual(len(inlet) + len(outlet) + len(wall), len(self.mock_mesh_data_y_axis.faces))

        # Test Z-axis preferred (reset mock)
        mock_trimesh_load.reset_mock()
        mock_trimesh_load.return_value = self.mock_mesh_data_z_axis
        inlet, outlet, wall = parse_mesh_boundaries("mock_mesh.obj")
        self.assertGreater(len(inlet), 0, "Should find inlets on Z-axis")
        self.assertGreater(len(outlet), 0, "Should find outlets on Z-axis")
        self.assertGreater(len(wall), 0, "Should find walls on Z-axis")
        self.assertEqual(len(inlet) + len(outlet) + len(wall), len(self.mock_mesh_data_z_axis.faces))


    # These tests don't need the full setUp mocking since they only call enforce_numerical_stability
    # which only needs the input_data (dict) and dx, dt (pint quantities)
    def test_enforce_numerical_stability_passes(self):
        """Validate CFL condition passes for stable parameters."""
        input_data = {"fluid_velocity": 0.5} # Low velocity, should pass
        dx = 0.01 * ureg.meter
        dt = 0.001 * ureg.second

        # Should not raise an error
        try:
            enforce_numerical_stability(input_data, dx, dt)
        except ValueError:
            self.fail("enforce_numerical_stability raised ValueError unexpectedly for stable parameters!")

    def test_enforce_numerical_stability_fails_cfl(self):
        """Validate CFL condition fails for unstable parameters."""
        input_data = {"fluid_velocity": 50.0} # High velocity, should fail
        dx = 0.01 * ureg.meter
        dt = 0.001 * ureg.second

        # Use a regex that matches the core message, ignoring the prefix
        with self.assertRaisesRegex(ValueError, "CFL condition violated"):
            enforce_numerical_stability(input_data, dx, dt)

    def test_enforce_numerical_stability_skips_without_fluid_velocity(self):
        """Ensure CFL check is skipped if fluid_velocity is missing."""
        input_data = {"some_other_key": 100} # fluid_velocity is missing
        dx = 0.01 * ureg.meter
        dt = 0.001 * ureg.second

        # Should not raise an error and should log a warning (which we don't assert here)
        try:
            enforce_numerical_stability(input_data, dx, dt)
        except Exception as e:
            self.fail(f"enforce_numerical_stability raised an unexpected exception: {e}")

    @mock.patch('os.path.exists', return_value=True)
    @mock.patch('builtins.open', new_callable=mock.mock_open)
    def test_load_input_file_missing_boundary_config(self, mock_open_file, mock_exists):
        """Tests error handling for missing 'boundary_properties_config'."""
        malformed_input = self.mock_fluid_input_data.copy()
        del malformed_input["boundary_properties_config"]
        mock_open_file.return_value.__enter__.return_value.read.return_value = json.dumps(malformed_input)

        with self.assertRaisesRegex(ValueError, "'boundary_properties_config' section is missing or malformed"):
            load_input_file("mock_input.json")

    @mock.patch('os.path.exists', return_value=True)
    @mock.patch('builtins.open', new_callable=mock.mock_open)
    def test_load_input_file_missing_fluid_property(self, mock_open_file, mock_exists):
        """Tests error handling for missing required fluid properties."""
        malformed_input = self.mock_fluid_input_data.copy()
        del malformed_input["density"] # Remove a required property
        mock_open_file.return_value.__enter__.return_value.read.return_value = json.dumps(malformed_input)

        with self.assertRaisesRegex(ValueError, "Required fluid property 'density' not found"):
            load_input_file("mock_input.json")

    @mock.patch('trimesh.load')
    @mock.patch('os.path.exists', return_value=True)
    @mock.patch('builtins.open', new_callable=mock.mock_open)
    def test_apply_boundary_conditions_missing_suggested_time_step(self, mock_open_file, mock_exists, mock_trimesh_load):
        """Tests error handling for missing 'suggested_time_step' in simulation_settings."""
        malformed_input = self.mock_fluid_input_data.copy()
        malformed_input["simulation_settings"] = malformed_input["simulation_settings"].copy() # Create a copy to modify
        del malformed_input["simulation_settings"]["suggested_time_step"]
        mock_open_file.return_value.__enter__.return_value.read.return_value = json.dumps(malformed_input)

        mock_trimesh_load.return_value = self.mock_mesh_data_x_axis # Needs a mock mesh

        dx_val = 0.01 * ureg.meter
        dt_val = 0.001 * ureg.second
        mesh_file_path = "mock_mesh.obj"
        input_file_path = "mock_input.json"

        with self.assertRaisesRegex(ValueError, "'suggested_time_step' is required in simulation_settings"):
            apply_boundary_conditions(
                load_input_file(input_file_path), dx_val, dt_val, mesh_file_path
            )


if __name__ == "__main__":
    unittest.main()
