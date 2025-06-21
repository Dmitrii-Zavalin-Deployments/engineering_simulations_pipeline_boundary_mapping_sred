# test_integration_pipeline.py

import json
import pytest
from pathlib import Path
from src.merge_json_files import merge_json_files


def test_pipeline_merge_and_output_integrity(example_initial_input, example_mesh_input, temp_output_dir):
    """
    Simulates the entire preprocessing pipeline:
    - Save mesh and initial input to disk
    - Run merge_json_files()
    - Confirm merged file is well-formed and contains correct keys
    """

    input_mesh = temp_output_dir / "mesh_input.json"
    input_initial = temp_output_dir / "initial_input.json"
    output_merged = temp_output_dir / "merged_result.json"

    # Write inputs to file
    with open(input_mesh, "w") as f:
        json.dump(example_mesh_input, f, indent=2)

    with open(input_initial, "w") as f:
        json.dump(example_initial_input, f, indent=2)

    # Run actual merge
    merge_json_files(
        mesh_file=str(input_mesh),
        initial_file=str(input_initial),
        output_file=str(output_merged)
    )

    assert output_merged.exists(), "Expected merged JSON output file was not created."

    # Load and validate output
    with open(output_merged) as f:
        merged = json.load(f)

    # Sanity checks
    assert "mesh" in merged
    assert "fluid_properties" in merged
    assert "boundary_conditions" in merged
    assert "simulation_parameters" in merged

    bc = merged["boundary_conditions"]
    assert set(bc.keys()) == {"inlet", "outlet", "wall"}
    assert isinstance(bc["inlet"].get("faces"), list)
    assert isinstance(merged["fluid_properties"].get("density"), (float, int))
    assert merged["simulation_parameters"]["solver"] in {"explicit", "implicit"}



