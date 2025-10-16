# tests/test_domain_definition_writer.py

import pytest
from src.domain_definition_writer import validate_domain_bounds, DomainValidationError


def test_valid_domain_bounds():
    """Should pass when all bounds are valid and max > min."""
    domain = {
        "min_x": 0.0, "max_x": 10.0,
        "min_y": 1.0, "max_y": 5.0,
        "min_z": 2.0, "max_z": 3.0
    }
    validate_domain_bounds(domain)  # Should not raise


@pytest.mark.parametrize("missing_key", [
    "min_x", "max_x", "min_y", "max_y", "min_z", "max_z"
])
def test_missing_domain_keys(missing_key):
    """Should raise DomainValidationError when any expected key is missing."""
    domain = {
        "min_x": 0.0, "max_x": 10.0,
        "min_y": 1.0, "max_y": 5.0,
        "min_z": 2.0, "max_z": 3.0
    }
    domain.pop(missing_key)
    with pytest.raises(DomainValidationError, match="Missing domain bounds"):
        validate_domain_bounds(domain)


@pytest.mark.parametrize("axis,min_val,max_val,expected_error", [
    ("x", "a", 10.0, "Non-numeric bounds"),
    ("y", 1.0, "b", "Non-numeric bounds"),
    ("z", None, 3.0, "Missing domain bounds"),
    ("z", 2.0, None, "Missing domain bounds")
])
def test_non_numeric_bounds(axis, min_val, max_val, expected_error):
    """Should raise DomainValidationError when bounds are non-numeric or missing."""
    domain = {
        "min_x": 0.0, "max_x": 10.0,
        "min_y": 1.0, "max_y": 5.0,
        "min_z": 2.0, "max_z": 3.0
    }
    domain[f"min_{axis}"] = min_val
    domain[f"max_{axis}"] = max_val
    with pytest.raises(DomainValidationError, match=expected_error):
        validate_domain_bounds(domain)


@pytest.mark.parametrize("axis,min_val,max_val", [
    ("x", 10.0, 5.0),
    ("y", 5.0, 2.0),
    ("z", 3.0, 1.0)
])
def test_max_less_than_min(axis, min_val, max_val):
    """Should raise DomainValidationError when max < min for any axis."""
    domain = {
        "min_x": 0.0, "max_x": 10.0,
        "min_y": 1.0, "max_y": 5.0,
        "min_z": 2.0, "max_z": 3.0
    }
    domain[f"min_{axis}"] = min_val
    domain[f"max_{axis}"] = max_val
    with pytest.raises(DomainValidationError, match=f"Invalid domain: max_{axis}"):
        validate_domain_bounds(domain)


def test_string_castable_bounds():
    """Should pass when bounds are strings that can be cast to float."""
    domain = {
        "min_x": "0.0", "max_x": "10.0",
        "min_y": "1.0", "max_y": "5.0",
        "min_z": "2.0", "max_z": "3.0"
    }
    validate_domain_bounds(domain)


