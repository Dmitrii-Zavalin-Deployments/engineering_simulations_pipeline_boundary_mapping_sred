# test_physics_validation.py

import pytest


def test_pressure_and_density_positive(example_initial_input):
    """Ensure pressure and density values are physically valid (positive)."""
    bc = example_initial_input["boundary_conditions"]
    fluid = example_initial_input["fluid_properties"]

    # Inlet pressure
    assert bc["inlet"]["pressure"] > 0, "Inlet pressure must be > 0"
    # Outlet pressure
    assert bc["outlet"]["pressure"] > 0, "Outlet pressure must be > 0"
    # Fluid density
    assert fluid["density"] > 0, "Density must be > 0"


def test_viscosity_valid(example_initial_input):
    """Validate fluid viscosity is positive and a real number."""
    viscosity = example_initial_input["fluid_properties"]["viscosity"]
    assert isinstance(viscosity, (int, float))
    assert viscosity > 0, "Viscosity must be > 0"


def test_velocity_vector_valid(example_initial_input):
    """Ensure the inlet velocity is a 3D vector of numeric components."""
    velocity = example_initial_input["boundary_conditions"]["inlet"]["velocity"]
    assert isinstance(velocity, list) and len(velocity) == 3
    assert all(isinstance(v, (int, float)) for v in velocity)


def test_ideal_gas_model_requires_parameters(example_initial_input):
    """If fluid is ideal gas, check presence of gamma and R_s."""
    thermodynamics = example_initial_input["fluid_properties"]["thermodynamics"]
    model = thermodynamics.get("model", "")
    if model == "ideal_gas":
        assert "adiabatic_index_gamma" in thermodynamics, "Missing gamma for ideal_gas"
        assert "specific_gas_constant_J_per_kgK" in thermodynamics, "Missing R_s for ideal_gas"
        assert thermodynamics["adiabatic_index_gamma"] > 1
        assert thermodynamics["specific_gas_constant_J_per_kgK"] > 0


def test_wall_no_slip_behavior(example_initial_input):
    """Check that no_slip walls do not define velocity erroneously."""
    wall = example_initial_input["boundary_conditions"]["wall"]
    assert isinstance(wall.get("no_slip"), bool), "Wall no_slip must be boolean"
    # Future: check mesh input to ensure no velocity is applied on no-slip walls


@pytest.mark.parametrize("field", ["time_step", "total_time"])
def test_simulation_parameters_are_positive(example_initial_input, field):
    """Check simulation time parameters are greater than zero."""
    value = example_initial_input["simulation_parameters"].get(field)
    assert isinstance(value, (int, float)) and value > 0, f"{field} must be > 0"


def test_solver_value_is_valid(example_initial_input):
    """Ensure solver is one of the accepted types."""
    solver = example_initial_input["simulation_parameters"].get("solver")
    assert solver in ["explicit", "implicit"], f"Unsupported solver value: {solver}"



