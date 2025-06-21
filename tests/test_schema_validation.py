# test_schema_validation.py

import pytest
from jsonschema.exceptions import ValidationError


# === Initial Input Schema Tests ===

def test_valid_initial_input_passes_schema(input_schema_validator, valid_initial_input):
    """Test that a known-valid initial input file passes schema validation."""
    input_schema_validator.validate(valid_initial_input)


def test_missing_required_field_raises_error(input_schema_validator, invalid_initial_missing_fields):
    """Test that missing required fields are caught by schema validation."""
    with pytest.raises(ValidationError) as excinfo:
        input_schema_validator.validate(invalid_initial_missing_fields)
    assert "is a required property" in str(excinfo.value)


# === Mesh Schema Tests ===

def test_valid_mesh_input_passes_schema(mesh_schema_validator, valid_mesh_input):
    """Ensure valid mesh input conforms to the mesh schema."""
    mesh_schema_validator.validate(valid_mesh_input)


def test_invalid_mesh_fails_validation(mesh_schema_validator, invalid_mesh_bad_face):
    """Ensure mesh input with malformed face entry raises schema error."""
    with pytest.raises(ValidationError) as excinfo:
        mesh_schema_validator.validate(invalid_mesh_bad_face)
    assert "is not of type" in str(excinfo.value) or "is a required property" in str(excinfo.value)



