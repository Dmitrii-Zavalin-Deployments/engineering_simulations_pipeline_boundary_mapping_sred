# conftest.py

import json
import os
import pytest
from pathlib import Path
from jsonschema import Draft202012Validator, validate


# === Paths ===

@pytest.fixture(scope="session")
def schema_dir():
    return Path(__file__).parent.parent / "schema"


@pytest.fixture(scope="session")
def data_dir():
    return Path(__file__).parent / "test_data"


# === Schema Loaders ===

@pytest.fixture(scope="session")
def initial_data_schema(schema_dir):
    with open(schema_dir / "initial_data.schema.json", "r") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def mesh_data_schema(schema_dir):
    with open(schema_dir / "mesh_data.schema.json", "r") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def input_schema_validator(initial_data_schema):
    return Draft202012Validator(initial_data_schema)


@pytest.fixture(scope="session")
def mesh_schema_validator(mesh_data_schema):
    return Draft202012Validator(mesh_data_schema)


# === Sample JSON Inputs ===

@pytest.fixture
def valid_initial_input(data_dir):
    with open(data_dir / "valid_initial.json", "r") as f:
        return json.load(f)


@pytest.fixture
def invalid_initial_missing_fields(data_dir):
    with open(data_dir / "invalid_initial_missing_fields.json", "r") as f:
        return json.load(f)


@pytest.fixture
def valid_mesh_input(data_dir):
    with open(data_dir / "valid_mesh.json", "r") as f:
        return json.load(f)


@pytest.fixture
def invalid_mesh_bad_face(data_dir):
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



