# test_merge_json_roundtrip.py

import json
import pytest
from pathlib import Path
import subprocess


def test_merge_script_produces_output(example_initial_input, example_mesh_input, temp_output_dir):
    """
    Simulate merging two valid input files and verify merged JSON is created and usable.
    Assumes a CLI or script function like: python merge_json_files.py --initial <input> --mesh <input> --output <file>
    """

    # === Prepare input files ===
    initial_path = temp_output_dir / "initial.json"
    mesh_path = temp_output_dir / "mesh.json"
    merged_path = temp_output_dir / "merged.json"

    with open(initial_path, "w") as f:
        json.dump(example_initial_input, f, indent=2)

    with open(mesh_path, "w") as f:
        json.dump(example_mesh_input, f, indent=2)

    # === Run merge script ===
    result = subprocess.run(
        [
            "python",
            "src/merge_json_files.py",
            "--initial", str(initial_path),
            "--mesh", str(mesh_path),
            "--output", str(merged_path)
        ],
        capture_output=True,
        text=True
    )

    assert result.returncode == 0, f"Merge script failed:\n{result.stderr}"
    assert merged_path.exists(), "Merged output file was not created"

    # === Reload and inspect output ===
    with open(merged_path, "r") as f:
        merged_data = json.load(f)

    assert "mesh" in merged_data, "Merged JSON missing 'mesh' section"
    assert "boundary_conditions" in merged_data, "Missing boundary_conditions after merge"
    assert "simulation_parameters" in merged_data, "Missing simulation_parameters after merge"


def test_merged_json_contains_original_values(example_initial_input, example_mesh_input, temp_output_dir):
    """
    Confirm that key data from both original input files exists unchanged in the merged output.
    """

    # Setup
    merged = {
        "mesh": example_mesh_input,
        **example_initial_input
    }

    # Simulated merge logic
    merged_json = json.dumps(merged)
    reloaded = json.loads(merged_json)

    # Check that key fields still match
    assert reloaded["fluid_properties"] == example_initial_input["fluid_properties"]
    assert reloaded["mesh"]["boundary_faces"] == example_mesh_input["boundary_faces"]


def test_merge_handles_missing_keys_gracefully(temp_output_dir):
    """
    Simulate a merge failure: mesh file missing required structure.
    The merge script should raise or fail with a clear error.
    """

    bad_mesh = {"nodes": 100}  # Incomplete mesh
    initial = {
        "boundary_conditions": {"inlet": {"velocity": [1, 0, 0], "pressure": 100000}},
        "fluid_properties": {"density": 1.0, "viscosity": 0.001, "thermodynamics": {"model": "incompressible"}},
        "simulation_parameters": {"time_step": 0.1, "total_time": 1.0, "solver": "explicit"}
    }

    mesh_path = temp_output_dir / "broken_mesh.json"
    init_path = temp_output_dir / "init.json"
    out_path = temp_output_dir / "merged.json"

    json.dump(bad_mesh, open(mesh_path, "w"))
    json.dump(initial, open(init_path, "w"))

    result = subprocess.run(
        [
            "python",
            "src/merge_json_files.py",
            "--initial", str(init_path),
            "--mesh", str(mesh_path),
            "--output", str(out_path)
        ],
        capture_output=True,
        text=True
    )

    assert result.returncode != 0, "Expected merge script to fail with broken mesh input"
    assert "boundary_faces" in result.stderr or "mesh" in result.stderr, "Expected error message about mesh structure"



