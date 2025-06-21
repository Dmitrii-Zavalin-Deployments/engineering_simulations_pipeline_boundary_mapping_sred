# conftest.py

import json
import pytest
from pathlib import Path


# === Paths ===

@pytest.fixture(scope="session")
def data_dir():
    return Path(__file__).parent / "test_data"


# === Sample JSON Inputs (assumed schema-compliant) ===

@pytest.fixture
def example_initial_input(data_dir):
    with open(data_dir / "valid_initial.json", "r") as f:
        return json.load(f)


@pytest.fixture
def example_mesh_input(data_dir):
    with open(data_dir / "valid_mesh.json", "r") as f:
        return json.load(f)


@pytest.fixture
def invalid_initial_physics(data_dir):
    with open(data_dir / "invalid_initial_missing_fields.json", "r") as f:
        return json.load(f)


@pytest.fixture
def invalid_mesh_physics(data_dir):
    with open(data_dir / "invalid_mesh_bad_face.json", "r") as f:
        return json.load(f)


# === Utility Functions ===

def load_json(path):
    with open(path, "r") as f:
        return json.load(f)


@pytest.fixture
def temp_output_dir(tmp_path_factory):
    """Creates a temporary directory for writing test outputs."""
    return tmp_path_factory.mktemp("outputs")



