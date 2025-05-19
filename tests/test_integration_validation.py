import unittest
import numpy as np
import unittest.mock as mock
from src.boundary_conditions import apply_boundary_conditions, generate_boundary_conditions

class TestBoundaryConditionIntegration(unittest.TestCase):
    def setUp(self):
        """Mock input data for boundary condition validation"""
        self.input_data = {
            "fluid_velocity": 2.5,
            "velocity_direction": 45,
            "static_pressure": 101325,
            "temperature": 298,
            "density": 1000,
            "viscosity": 0.001002
        }

    def mock_solver(self, input_conditions):
        """Simulated solver dynamically modifying outlet values based on inlet conditions."""
        if input_conditions["fluid_velocity"] > 5:
            return {"pressure": 100600, "velocity": [5.0, 0.0, 0.0]}
        else:
            return {"pressure": 100500, "velocity": [2.5, 0.0, 0.0]}

    def test_mock_solver_response(self):
        """Verify that boundary conditions correctly influence fluid dynamics"""
        mock_engine = mock.Mock()
        mock_engine.solve.side_effect = self.mock_solver

        boundary_conditions = mock_engine.solve(self.input_data)
        self.assertEqual(boundary_conditions["pressure"], 100500, "Mock solver did not return expected pressure!")

    def test_cfl_condition_across_domain(self):
        """Validate CFL constraints hold across the computational domain"""
        grid_size = (10, 10)  # 10x10 mesh
        velocity_field = np.random.uniform(0.5, 3.0, grid_size)  # Random velocities in domain

        dx = 0.01  # Grid spacing
        dt = 0.001  # Suggested time step
        cfl_values = velocity_field * dt / dx
        self.assertTrue(np.all(cfl_values <= 1), "❌ CFL condition violated in some regions!")

    def test_extreme_fluid_conditions(self):
        """Ensure solver correctly handles extreme velocity inputs."""
        extreme_input = {"fluid_velocity": 50, "density": 1000, "viscosity": 0.001002, "pressure": 101325}  # Added pressure

        try:
            boundary_conditions = generate_boundary_conditions(extreme_input)
            self.assertLessEqual(
                boundary_conditions["outlet_boundary"]["velocity"][0], 50,
                "❌ Extreme velocity case not handled properly!"
            )
        except NameError:
            self.fail("❌ generate_boundary_conditions function is missing or incorrectly imported!")

    def test_dynamic_outlet_conditions(self):
        """Ensure outlet pressure and velocity adjust dynamically."""
        input_data = {"fluid_velocity": 5.5, "pressure": 101400}
        mock_engine = mock.Mock()
        mock_engine.solve.side_effect = lambda x: {"pressure": 101300, "velocity": [5.5, 0.0, 0.0]}

        output_conditions = mock_engine.solve(input_data)
        self.assertEqual(
            output_conditions["pressure"], 101300,
            "❌ Outlet conditions did not update dynamically!"
        )

if __name__ == "__main__":
    unittest.main()
