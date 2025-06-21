# test_edge_case_fuzzing.py

import json
import pytest
from hypothesis import given, strategies as st


@given(
    st.lists(
        st.fixed_dictionaries({
            "face_id": st.integers(min_value=0),
            "type": st.sampled_from(["inlet", "outlet", "wall", "", "unknown"]),
            "nodes": st.dictionaries(
                st.text(min_size=1, max_size=5),
                st.lists(st.floats(allow_nan=False, allow_infinity=False), min_size=3, max_size=3),
                min_size=0,
                max_size=5
            )
        }),
        min_size=0,
        max_size=10
    )
)
def test_boundary_faces_with_fuzzed_data(faces):
    """Ensure that generated boundary_faces structures are JSON serializable and safely processed."""
    test_mesh = {
        "type": "fuzzed",
        "nodes": 100,
        "edges": 150,
        "faces": 200,
        "volumes": 250,
        "boundary_faces": faces
    }

    try:
        json_str = json.dumps(test_mesh)
        loaded = json.loads(json_str)
        assert isinstance(loaded["boundary_faces"], list)
    except Exception as e:
        pytest.fail(f"Generated mesh was not JSON-serializable: {e}")


@given(
    st.fixed_dictionaries({
        "boundary_conditions": st.fixed_dictionaries({
            "inlet": st.fixed_dictionaries({
                "velocity": st.lists(st.floats(min_value=-1e9, max_value=1e9), min_size=3, max_size=3),
                "pressure": st.floats(min_value=0, allow_nan=False)
            }),
            "outlet": st.fixed_dictionaries({
                "pressure": st.floats(min_value=0, allow_nan=False)
            }),
            "wall": st.fixed_dictionaries({
                "no_slip": st.booleans()
            })
        }),
        "fluid_properties": st.fixed_dictionaries({
            "density": st.floats(min_value=0.0, allow_nan=False),
            "viscosity": st.floats(min_value=0.0, allow_nan=False),
            "thermodynamics": st.one_of(
                st.none(),
                st.fixed_dictionaries({
                    "model": st.sampled_from(["incompressible", "ideal_gas"]),
                    "adiabatic_index_gamma": st.floats(min_value=1.0, max_value=2.0),
                    "specific_gas_constant_J_per_kgK": st.floats(min_value=0.0, max_value=1000.0)
                })
            )
        }),
        "simulation_parameters": st.fixed_dictionaries({
            "time_step": st.floats(min_value=0.00001, max_value=10.0),
            "total_time": st.floats(min_value=0.01, max_value=10000.0),
            "solver": st.sampled_from(["explicit", "implicit"])
        })
    })
)
def test_minimal_input_roundtrip(input_data):
    """Ensure JSON with edge values round-trips correctly and remains structurally intact."""
    try:
        json_str = json.dumps(input_data)
        recovered = json.loads(json_str)
        assert "fluid_properties" in recovered
        assert recovered["simulation_parameters"]["time_step"] > 0
    except Exception as e:
        pytest.fail(f"Generated input structure is invalid: {e}")



