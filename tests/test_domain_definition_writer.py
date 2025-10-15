# tests/test_domain_definition_writer.py

import pytest
from src.domain_definition_writer import validate_domain_bounds, DomainValidationError

def test_valid_bounds_pass():
    domain = {
        "min_x": 0.0, "max_x": 10.0,
        "min_y": 0.0, "max_y": 5.0,
        "min_z": 1.0, "max_z": 2.0
    }
    # Should not raise
    validate_domain_bounds(domain)

@pytest.mark.parametrize("missing_key", [
    "min_x", "max_x", "min_y", "max_y", "min_z", "max_z"
])
def test_missing_key_raises(missing_key):
    domain = {
        "min_x": 0.0, "max_x": 10.0,
        "min_y": 0.0, "max_y": 5.0,
        "min_z": 1.0, "max_z": 2.0
    }
    domain.pop(missing_key)
    with pytest.raises(DomainValidationError, match=f"Missing domain bounds for axis"):
        validate_domain_bounds(domain)

@pytest.mark.parametrize("bad_key,value,expected_error", [
    ("min_x", "abc", "Non-numeric bounds for axis"),
    ("max_y", None, "Missing domain bounds for axis 'y'"),
    ("min_z", [1, 2], "Non-numeric bounds for axis"),
])
def test_non_numeric_values_raise(bad_key, value, expected_error):
    domain = {
        "min_x": 0.0, "max_x": 10.0,
        "min_y": 0.0, "max_y": 5.0,
        "min_z": 1.0, "max_z": 2.0
    }
    domain[bad_key] = value
    with pytest.raises(DomainValidationError, match=expected_error):
        validate_domain_bounds(domain)

@pytest.mark.parametrize("axis,min_val,max_val", [
    ("x", 5.0, 4.0),
    ("y", 2.0, 1.0),
    ("z", 9.0, 3.0),
])
def test_invalid_bounds_raise(axis, min_val, max_val):
    domain = {
        "min_x": 0.0, "max_x": 10.0,
        "min_y": 0.0, "max_y": 5.0,
        "min_z": 1.0, "max_z": 2.0
    }
    domain[f"min_{axis}"] = min_val
    domain[f"max_{axis}"] = max_val
    with pytest.raises(DomainValidationError, match=f"Invalid domain: max_{axis}"):
        validate_domain_bounds(domain)

def test_string_casting_allowed_if_logically_valid():
    domain = {
        "min_x": "0.0", "max_x": "1.0",
        "min_y": "2.0", "max_y": "3.0",
        "min_z": "4.0", "max_z": "5.0"
    }
    # Should not raise
    validate_domain_bounds(domain)



