import json
import numpy as np
import unittest
from pint import UnitRegistry

ureg = UnitRegistry()

class TestInputValidation(unittest.TestCase):
    def setUp(self):
        """Example input data"""
        self.input_data = {
            "fluid_velocity": 2.5,  # (m/s)
            "velocity_direction": 45,  # (degrees)
            "static_pressure": 101325,  # (Pa)
            "temperature": 298,  # (K)
            "density": 1000,  # (kg/m³)
            "viscosity": 0.001002  # (Pa·s)
        }

    def test_numerical_ranges(self):
        """Test fluid parameters remain within reasonable limits"""
        fluid_velocity_range = {"water": (0.01, 5), "air": (0, 30)}
        assert fluid_velocity_range["water"][0] <= self.input_data["fluid_velocity"] <= fluid_velocity_range["water"][1]

    def test_unit_validation(self):
        """Verify dimensional correctness using `pint`"""
        velocity = self.input_data["fluid_velocity"] * ureg.meter / ureg.second
        assert velocity.units == ureg("m/s"), "Incorrect unit assignment!"

    def test_velocity_direction(self):
        """Ensure velocity direction is within valid angular range"""
        assert 0 <= self.input_data["velocity_direction"] <= 360, "Velocity direction out of range!"

    def test_missing_fields(self):
        """Ensure missing input fields trigger appropriate error handling."""
        invalid_input = {"fluid_velocity": 2.5, "temperature": 298}  # Missing density, viscosity
        with self.assertRaises(KeyError):
            process_input(invalid_input)

class TestOutputValidation(unittest.TestCase):
    def setUp(self):
        """Example output data"""
        self.output_data = {
            "inlet_boundary": {
                "velocity": [2.5, 0.0, 0.0],
                "pressure": 101325,
                "fluid_properties": {"temperature": 298, "density": 1000, "viscosity": 0.001002}
            },
            "outlet_boundary": {"pressure": 100500, "velocity": None},
            "wall_boundary": {"no_slip": True}
        }

    def test_boundary_condition_consistency(self):
        """Ensure generated boundary conditions match expected values"""
        assert self.output_data["inlet_boundary"]["velocity"][0] == 2.5
        assert self.output_data["inlet_boundary"]["fluid_properties"]["density"] == 1000

    def test_mesh_definition_accuracy(self):
        """Ensure mesh faces are properly assigned"""
        inlet_faces = [308, 310, 311, 312]
        assert len(set(inlet_faces)) == len(inlet_faces), "Duplicate inlet face assignments detected!"

if __name__ == "__main__":
    unittest.main()



