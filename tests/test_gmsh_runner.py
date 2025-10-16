# tests/test_gmsh_runner.py

import pytest
import json
import os
import tempfile
import subprocess
from unittest import mock
from src import gmsh_runner


@pytest.fixture
def mock_flow_data(tmp_path):
    """Creates a mock flow_data.json file."""
    flow_data = {
        "model_properties": {
            "flow_region": "internal",
            "no_slip": True
        },
        "initial_conditions": {
            "velocity": [0.0, 0.0, 0.0],
            "pressure": 0.0
        }
    }
    path = tmp_path / "flow_data.json"
    with open(path, "w") as f:
        json.dump(flow_data, f)
    return str(path)


@pytest.fixture
def mock_step_file(tmp_path):
    """Creates a dummy STEP file path."""
    path = tmp_path / "input.step"
    path.write_text("dummy content")
    return str(path)


def test_missing_flow_data_file(monkeypatch):
    """Should raise FileNotFoundError if flow_data.json is missing."""
    monkeypatch.setattr("os.path.isfile", lambda path: False)
    with pytest.raises(FileNotFoundError):
        _ = gmsh_runner.main()


def test_step_validation_failure(monkeypatch, mock_flow_data, mock_step_file):
    """Should raise RuntimeError if STEP file fails validation."""
    monkeypatch.setattr("os.path.isfile", lambda path: True)
    monkeypatch.setattr("builtins.open", mock.mock_open(read_data=json.dumps({
        "model_properties": {}, "initial_conditions": {}
    })))
    monkeypatch.setattr("gmsh_runner.FLOW_DATA_PATH", mock_flow_data)
    monkeypatch.setattr("gmsh_runner.validate_step_has_volumes", lambda path: (_ for _ in ()).throw(gmsh_runner.ValidationError("Invalid STEP")))
    monkeypatch.setattr("gmsh.initialize", lambda: None)
    monkeypatch.setattr("gmsh.finalize", lambda: None)

    with pytest.raises(RuntimeError, match="STEP file validation failed"):
        gmsh_runner.main()


def test_successful_run(monkeypatch, mock_flow_data, mock_step_file, tmp_path):
    """Should run successfully and write output file."""
    output_path = tmp_path / "boundary_conditions.json"

    monkeypatch.setattr("os.path.isfile", lambda path: True)
    monkeypatch.setattr("builtins.open", mock.mock_open(read_data=json.dumps({
        "model_properties": {}, "initial_conditions": {}
    })))
    monkeypatch.setattr("gmsh_runner.FLOW_DATA_PATH", mock_flow_data)
    monkeypatch.setattr("gmsh_runner.validate_step_has_volumes", lambda path: True)
    monkeypatch.setattr("gmsh_runner.generate_boundary_conditions", lambda **kwargs: [{"type": "dirichlet", "role": "inlet", "faces": [1]}])
    monkeypatch.setattr("gmsh.initialize", lambda: None)
    monkeypatch.setattr("gmsh.finalize", lambda: None)

    args = [
        "src/gmsh_runner.py",
        "--step", mock_step_file,
        "--resolution", "0.5",
        "--flow_region", "internal",
        "--padding_factor", "5",
        "--no_slip", "True",
        "--initial_velocity", "1.0", "0.0", "0.0",
        "--initial_pressure", "101325",
        "--output", str(output_path)
    ]

    monkeypatch.setattr("sys.argv", args)
    gmsh_runner.main()

    assert output_path.exists()
    with open(output_path) as f:
        data = json.load(f)
    assert isinstance(data, list)
    assert data[0]["role"] == "inlet"



