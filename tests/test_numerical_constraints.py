# test_numerical_constraints.py

import pytest


def test_time_step_positive_and_nonzero(example_initial_input):
    """Ensure the simulation time step is greater than zero."""
    dt = example_initial_input["simulation_parameters"]["time_step"]
    assert isinstance(dt, (float, int)) and dt > 0, "Time step must be > 0"


def test_total_time_positive(example_initial_input):
    """Ensure total simulation time is positive."""
    T = example_initial_input["simulation_parameters"]["total_time"]
    assert isinstance(T, (float, int)) and T > 0, "Total time must be > 0"


def test_explicit_solver_safe_time_step(example_initial_input):
    """
    For an explicit solver, enforce a basic CFL-like constraint:
    time_step must be below a safety threshold based on velocity magnitude.
    """
    sim = example_initial_input["simulation_parameters"]
    solver = sim.get("solver", "")
    if solver == "explicit":
        velocity = example_initial_input["boundary_conditions"]["inlet"]["velocity"]
        U_mag = sum(v**2 for v in velocity) ** 0.5
        dt = sim["time_step"]

        max_velocity = max(1.0, U_mag)
        max_allowed_dt = 1.0 / max_velocity  # Placeholder safety threshold
        assert dt < max_allowed_dt, (
            f"Time step {dt} too large for inlet velocity magnitude {U_mag:.3f}. "
            "Explicit solvers require small time steps for stability."
        )


@pytest.mark.parametrize("solver", ["explicit", "implicit"])
def test_solver_behavior_allowed(example_initial_input, solver):
    """Assert that solver choice is recognized and supported."""
    configured_solver = example_initial_input["simulation_parameters"]["solver"]
    assert configured_solver in ["explicit", "implicit"], "Invalid solver type"
    if configured_solver == solver:
        assert True  # Placeholder for future solver-specific assertions


def test_total_iterations_is_reasonable(example_initial_input):
    """
    Catch overly aggressive simulation lengths (e.g. billions of steps).
    Warn if total iterations > 1 million.
    """
    dt = example_initial_input["simulation_parameters"]["time_step"]
    T = example_initial_input["simulation_parameters"]["total_time"]
    total_steps = T / dt

    assert total_steps < 1e6, f"Total simulation steps ({total_steps:.0f}) is excessive"



