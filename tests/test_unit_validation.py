import unittest
import json
import numpy as np
from pint import UnitRegistry
import unittest.mock as mock
import os # Required for mocking os.path.exists

# Import the actual functions to be unit tested
from src.boundary_conditions import load_input_file, parse_mesh_boundaries, enforce_numerical_stability, ureg

class TestInputFileLoading(unittest.TestCase):
    """Tests for the load_input_file function."""

    @mock.patch('os.path.exists', return_value=True)
    @mock.patch('builtins.open', new_callable=mock.mock_open)
    def test_load_input_file_success(self, mock_open_file, mock_exists):
        """Tests that load_input_file successfully loads and processes valid input."""
        mock_data = {
            "fluid_velocity": 2.5,
            "static_pressure": 101325,
            "temperature": 298,
            "density": 1000,
            "viscosity": 0.001002,
            "simulation_settings": {
                "suggested_time_step": 0.001
            },
            "boundary_properties_config": {
                "inlet_boundary": {"type": "pressure_inlet"},
                "outlet_boundary": {"type": "velocity_outlet", "velocity": None},
                "wall_boundary": {"no_slip": True, "wall_properties": {"roughness": 0.002, "heat_transfer": False}, "wall_functions": "standard"}
            }
        }
        mock_open_file.return_value.__enter__.return_value.read.return_value = json.dumps(mock_data)

        loaded_data = load_input_file("dummy_path.json")

        self.assertIsInstance(loaded_data, dict)
        # Check if Pint quantities are correctly applied
        self.assertEqual(loaded_data["static_pressure"], 101325 * ureg.pascal)
        self.assertEqual(loaded_data["temperature"], 298 * ureg.kelvin)
        self.assertEqual(loaded_data["density"], 1000 * ureg.kilogram / ureg.meter**3)
        self.assertEqual(loaded_data["viscosity"], 0.001002 * ureg.pascal * ureg.second)
        self.assertIn("simulation_settings", loaded_data)
        self.assertIn("boundary_properties_config", loaded_data)

    @mock.patch('os.path.exists', return_value=False)
    def test_load_input_file_not_found(self, mock_exists):
        """Tests error handling when the input file does not exist."""
        with self.assertRaisesRegex(FileNotFoundError, "The input file 'non_existent.json' was not found"):
            load_input_file("non_existent.json")

    @mock.patch('os.path.exists', return_value=True)
    @mock.patch('builtins.open', new_callable=mock.mock_open)
    def test_load_input_file_missing_fluid_property(self, mock_open_file, mock_exists):
        """Tests error handling for missing required fluid properties."""
        malformed_data = {
            "fluid_velocity": 2.5,
            "static_pressure": 101325,
            "temperature": 298,
            "viscosity": 0.001002, # Density is missing
            "simulation_settings": {"suggested_time_step": 0.001},
            "boundary_properties_config": {"inlet_boundary": {"type": "pressure_inlet"}, "outlet_boundary": {"type": "velocity_outlet", "velocity": None}, "wall_boundary": {"no_slip": True, "wall_properties": {"roughness": 0.002, "heat_transfer": False}, "wall_functions": "standard"}}
        }
        mock_open_file.return_value.__enter__.return_value.read.return_value = json.dumps(malformed_data)

        with self.assertRaisesRegex(ValueError, "Required fluid property 'density' not found"):
            load_input_file("dummy_path.json")

    @mock.patch('os.path.exists', return_value=True)
    @mock.patch('builtins.open', new_callable=mock.mock_open)
    def test_load_input_file_malformed_simulation_settings(self, mock_open_file, mock_exists):
        """Tests error handling for missing or malformed simulation_settings."""
        malformed_data = {
            "fluid_velocity": 2.5,
            "static_pressure": 101325,
            "temperature": 298,
            "density": 1000,
            "viscosity": 0.001002,
            "simulation_settings": "not_a_dict", # Malformed
            "boundary_properties_config": {"inlet_boundary": {"type": "pressure_inlet"}, "outlet_boundary": {"type": "velocity_outlet", "velocity": None}, "wall_boundary": {"no_slip": True, "wall_properties": {"roughness": 0.002, "heat_transfer": False}, "wall_functions": "standard"}}
        }
        mock_open_file.return_value.__enter__.return_value.read.return_value = json.dumps(malformed_data)

        with self.assertRaisesRegex(ValueError, "'simulation_settings' section is missing or malformed"):
            load_input_file("dummy_path.json")

    @mock.patch('os.path.exists', return_value=True)
    @mock.patch('builtins.open', new_callable=mock.mock_open)
    def test_load_input_file_malformed_boundary_properties_config(self, mock_open_file, mock_exists):
        """Tests error handling for missing or malformed boundary_properties_config."""
        malformed_data = {
            "fluid_velocity": 2.5,
            "static_pressure": 101325,
            "temperature": 298,
            "density": 1000,
            "viscosity": 0.001002,
            "simulation_settings": {"suggested_time_step": 0.001},
            "boundary_properties_config": "not_a_dict" # Malformed
        }
        mock_open_file.return_value.__enter__.return_value.read.return_value = json.dumps(malformed_data)

        with self.assertRaisesRegex(ValueError, "'boundary_properties_config' section is missing or malformed"):
            load_input_file("dummy_path.json")

class TestMeshBoundaryParsing(unittest.TestCase):
    """Tests for the parse_mesh_boundaries function."""

    def setUp(self):
        # Define mock trimesh objects with simple vertices and faces
        # X-axis dominated mesh
        self.mock_mesh_x = mock.Mock()
        self.mock_mesh_x.vertices = np.array([
            [0, 0, 0], [0, 1, 0], [0, 0, 1], # Inlet candidates (min X) - Face 0
            [10, 0, 0], [10, 1, 0], [10, 0, 1], # Outlet candidates (max X) - Face 1
            [5, 5, 5], [5, 6, 5], [5, 5, 6] # Wall candidates - Face 2
        ])
        self.mock_mesh_x.faces = np.array([
            [0, 1, 2], # Inlet
            [3, 4, 5], # Outlet
            [6, 7, 8]  # Wall
        ])

        # Y-axis dominated mesh
        self.mock_mesh_y = mock.Mock()
        self.mock_mesh_y.vertices = np.array([
            [0, 0, 0], [1, 0, 0], [0, 0, 1], # Inlet candidates (min Y) - Face 0
            [0, 10, 0], [1, 10, 0], [0, 10, 1], # Outlet candidates (max Y) - Face 1
            [5, 5, 5], [5, 6, 5], [5, 5, 6] # Wall candidates - Face 2
        ])
        self.mock_mesh_y.faces = np.array([
            [0, 1, 2], # Inlet
            [3, 4, 5], # Outlet
            [6, 7, 8]  # Wall
        ])

        # Z-axis dominated mesh
        self.mock_mesh_z = mock.Mock()
        self.mock_mesh_z.vertices = np.array([
            [0, 0, 0], [1, 0, 0], [0, 1, 0], # Inlet candidates (min Z) - Face 0
            [0, 0, 10], [1, 0, 10], [0, 1, 10], # Outlet candidates (max Z) - Face 1
            [5, 5, 5], [5, 6, 5], [5, 5, 6] # Wall candidates - Face 2
        ])
        self.mock_mesh_z.faces = np.array([
            [0, 1, 2], # Inlet
            [3, 4, 5], # Outlet
            [6, 7, 8]  # Wall
        ])

        # Mesh with no clear inlet/outlet (e.g., all walls)
        self.mock_mesh_no_io = mock.Mock()
        self.mock_mesh_no_io.vertices = np.array([
            [0, 0, 0], [1, 0, 0], [0, 1, 0],
            [1, 1, 0], [0.5, 0.5, 0], [0.5, 0.5, 1] # A simple enclosed shape
        ])
        self.mock_mesh_no_io.faces = np.array([
            [0, 1, 4],
            [1, 3, 4],
            [3, 2, 4],
            [2, 0, 4],
            [0, 1, 5], # Faces that are not at extrema of any single axis
            [1, 3, 5],
            [3, 2, 5],
            [2, 0, 5]
        ])

    @mock.patch('trimesh.load')
    @mock.patch('os.path.exists', return_value=True)
    def test_parse_mesh_boundaries_x_axis(self, mock_exists, mock_trimesh_load):
        """Tests that parse_mesh_boundaries correctly identifies boundaries on the X-axis."""
        mock_trimesh_load.return_value = self.mock_mesh_x
        inlet_faces, outlet_faces, wall_faces = parse_mesh_boundaries("mock_mesh.obj")
        
        self.assertEqual(len(inlet_faces), 1)
        self.assertIn(0, inlet_faces) # Face 0 is at min X
        self.assertEqual(len(outlet_faces), 1)
        self.assertIn(1, outlet_faces) # Face 1 is at max X
        self.assertEqual(len(wall_faces), 1)
        self.assertIn(2, wall_faces) # Face 2 is a wall

    @mock.patch('trimesh.load')
    @mock.patch('os.path.exists', return_value=True)
    def test_parse_mesh_boundaries_y_axis(self, mock_exists, mock_trimesh_load):
        """Tests that parse_mesh_boundaries correctly identifies boundaries on the Y-axis."""
        mock_trimesh_load.return_value = self.mock_mesh_y
        inlet_faces, outlet_faces, wall_faces = parse_mesh_boundaries("mock_mesh.obj")
        
        self.assertEqual(len(inlet_faces), 1)
        self.assertIn(0, inlet_faces) # Face 0 is at min Y
        self.assertEqual(len(outlet_faces), 1)
        self.assertIn(1, outlet_faces) # Face 1 is at max Y
        self.assertEqual(len(wall_faces), 1)
        self.assertIn(2, wall_faces) # Face 2 is a wall

    @mock.patch('trimesh.load')
    @mock.patch('os.path.exists', return_value=True)
    def test_parse_mesh_boundaries_z_axis(self, mock_exists, mock_trimesh_load):
        """Tests that parse_mesh_boundaries correctly identifies boundaries on the Z-axis."""
        mock_trimesh_load.return_value = self.mock_mesh_z
        inlet_faces, outlet_faces, wall_faces = parse_mesh_boundaries("mock_mesh.obj")
        
        self.assertEqual(len(inlet_faces), 1)
        self.assertIn(0, inlet_faces) # Face 0 is at min Z
        self.assertEqual(len(outlet_faces), 1)
        self.assertIn(1, outlet_faces) # Face 1 is at max Z
        self.assertEqual(len(wall_faces), 1)
        self.assertIn(2, wall_faces) # Face 2 is a wall

    @mock.patch('trimesh.load')
    @mock.patch('os.path.exists', return_value=True)
    def test_parse_mesh_boundaries_no_io_found(self, mock_exists, mock_trimesh_load):
        """Tests that if no clear inlet/outlet is found, all faces are walls."""
        mock_trimesh_load.return_value = self.mock_mesh_no_io
        inlet_faces, outlet_faces, wall_faces = parse_mesh_boundaries("mock_mesh.obj")
        
        self.assertEqual(len(inlet_faces), 0)
        self.assertEqual(len(outlet_faces), 0)
        self.assertEqual(len(wall_faces), len(self.mock_mesh_no_io.faces)) # All faces become walls

    @mock.patch('trimesh.load', side_effect=Exception("Failed to load mesh"))
    @mock.patch('os.path.exists', return_value=True)
    def test_parse_mesh_boundaries_load_failure(self, mock_exists, mock_trimesh_load):
        """Tests error handling for mesh loading failures."""
        with self.assertRaisesRegex(ValueError, "Failed to load mesh file"):
            parse_mesh_boundaries("invalid_mesh.obj")

    @mock.patch('trimesh.load')
    @mock.patch('os.path.exists', return_value=False)
    def test_parse_mesh_boundaries_file_not_found(self, mock_exists, mock_trimesh_load):
        """Tests error handling when mesh file is not found."""
        with self.assertRaisesRegex(FileNotFoundError, "Mesh file 'non_existent.obj' was not found"):
            parse_mesh_boundaries("non_existent.obj")

class TestNumericalStability(unittest.TestCase):
    """Tests for the enforce_numerical_stability function."""

    def test_enforce_numerical_stability_passes(self):
        """Tests that CFL condition passes for valid parameters."""
        input_data = {"fluid_velocity": 0.5}
        dx = 0.01 * ureg.meter
        dt = 0.001 * ureg.second
        # Should not raise an exception
        enforce_numerical_stability(input_data, dx, dt)

    def test_enforce_numerical_stability_fails_cfl(self):
        """Tests that CFL condition fails and raises error for unstable parameters."""
        input_data = {"fluid_velocity": 50.0} # This will cause CFL > 1
        dx = 0.01 * ureg.meter
        dt = 0.001 * ureg.second
        with self.assertRaisesRegex(ValueError, "CFL condition violated"):
            enforce_numerical_stability(input_data, dx, dt)

    def test_enforce_numerical_stability_skips_without_fluid_velocity(self):
        """Tests that the CFL check is skipped if 'fluid_velocity' is missing."""
        input_data = {"some_other_property": 100}
        dx = 0.01 * ureg.meter
        dt = 0.001 * ureg.second
        # Should not raise an error, just skip the check
        try:
            enforce_numerical_stability(input_data, dx, dt)
        except Exception as e:
            self.fail(f"Unexpected exception raised: {e}")

    def test_enforce_numerical_stability_invalid_fluid_velocity_type(self):
        """Tests error handling for invalid fluid_velocity type."""
        input_data = {"fluid_velocity": "invalid"}
        dx = 0.01 * ureg.meter
        dt = 0.001 * ureg.second
        with self.assertRaisesRegex(ValueError, "'fluid_velocity' in input data must be a numerical value"):
            enforce_numerical_stability(input_data, dx, dt)


if __name__ == "__main__":
    unittest.main()
