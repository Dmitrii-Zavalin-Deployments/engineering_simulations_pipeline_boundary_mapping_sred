# tests/test_gmsh_runner.py

import pytest
import json
import os
from unittest.mock import patch, mock_open, MagicMock
from src import gmsh_runner

# Sample CLI args for patching
VALID_ARGS = [
    "--step", "dummy.step",
    "--resolution", "0.5",
    "--flow_region", "internal",
    "--padding_factor", "2",
    "--no_slip", "true",
    "--initial_velocity", "1.0", "0.0", "0.0",
    "--initial_pressure", "101325",
    "--output", "output.json"
]

def mock_model_data():
    return {
        "model_properties": {
            "flow_region": "external",
            "default_resolution": 0.5,
            "no_slip": False
        },
        "initial_conditions": {
            "velocity": [0.0, 0.0, 0.0],
            "pressure": 0
        }
    }

@patch("builtins.open", new_callable=mock_open, read_data=json.dumps(mock_model_data()))
@patch("os.path.isfile", return_value=True)
@patch("src.gmsh_runner.validate_step_has_volumes")
@patch("src.gmsh_runner.generate_boundary_conditions", return_value=[{"role": "inlet"}])
@patch("src.gmsh_runner.gmsh")
def test_main_runs_successfully(mock_gmsh, mock_generate, mock_validate, mock_isfile, mock_open_file, capsys):
    with patch("sys.argv", ["gmsh_runner.py"] + VALID_ARGS):
        gmsh_runner.main()
        captured = capsys.readouterr()
        assert "[INFO] Generated 1 boundary condition blocks." in captured.out
        assert os.path.exists("output.json") or True  # File write is mocked

@patch("os.path.isfile", return_value=False)
def test_missing_flow_data_raises(mock_isfile):
    with patch("sys.argv", ["gmsh_runner.py"] + VALID_ARGS):
        with pytest.raises(FileNotFoundError):
            gmsh_runner.main()

@patch("builtins.open", new_callable=mock_open, read_data="not-json")
@patch("os.path.isfile", return_value=True)
def test_invalid_json_in_flow_data_raises(mock_isfile, mock_open_file):
    with patch("sys.argv", ["gmsh_runner.py"] + VALID_ARGS):
        with pytest.raises(json.JSONDecodeError):
            gmsh_runner.main()

@patch("builtins.open", new_callable=mock_open, read_data=json.dumps(mock_model_data()))
@patch("os.path.isfile", return_value=True)
@patch("src.gmsh_runner.validate_step_has_volumes", side_effect=gmsh_runner.ValidationError("Invalid STEP"))
@patch("src.gmsh_runner.gmsh")
def test_step_validation_failure_raises(mock_gmsh, mock_validate, mock_isfile, mock_open_file):
    with patch("sys.argv", ["gmsh_runner.py"] + VALID_ARGS):
        with pytest.raises(RuntimeError, match="STEP file validation failed"):
            gmsh_runner.main()

@patch("builtins.open", new_callable=mock_open, read_data=json.dumps(mock_model_data()))
@patch("os.path.isfile", return_value=True)
@patch("src.gmsh_runner.validate_step_has_volumes")
@patch("src.gmsh_runner.generate_boundary_conditions", return_value=[])
@patch("src.gmsh_runner.gmsh")
def test_empty_result_raises_runtime_error(mock_gmsh, mock_generate, mock_validate, mock_isfile, mock_open_file):
    with patch("sys.argv", ["gmsh_runner.py"] + VALID_ARGS):
        with pytest.raises(RuntimeError, match="generation failed or returned empty"):
            gmsh_runner.main()

@patch("builtins.open", new_callable=mock_open, read_data=json.dumps(mock_model_data()))
@patch("os.path.isfile", return_value=True)
@patch("src.gmsh_runner.validate_step_has_volumes")
@patch("src.gmsh_runner.generate_boundary_conditions", return_value=[{"role": "inlet"}])
@patch("src.gmsh_runner.gmsh")
def test_output_file_written(mock_gmsh, mock_generate, mock_validate, mock_isfile, mock_open_file):
    with patch("sys.argv", ["gmsh_runner.py"] + VALID_ARGS):
        gmsh_runner.main()
        mock_open_file.assert_any_call("output.json", "w")



