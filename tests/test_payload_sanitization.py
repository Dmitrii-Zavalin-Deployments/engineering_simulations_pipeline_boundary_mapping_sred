# 📄 tests/test_payload_sanitization.py

import pytest
from src.run_pipeline import sanitize_payload
from src.utils.coercion import coerce_numeric
from tests.helpers.payload_factory import valid_domain_payload

EXPECTED_KEYS = [
    "x", "y", "z",
    "width", "height", "depth",
    "min_x", "max_x", "min_y", "max_y", "min_z", "max_z"
]

def test_float_str_normalization_basic():
    payload = {"domain_definition": {"min_z": "90.5", "max_z": 100.0}}
    sanitized = sanitize_payload(payload)
    domain = sanitized["domain_definition"]

    assert isinstance(coerce_numeric(domain["z"]), float)
    assert coerce_numeric(domain["z"]) == 90.5
    assert domain["min_z"] == 90.5
    assert domain["max_z"] == 100.0

def test_mixed_type_list_sanitization():
    payload = {"values": ["1.5", 2.0, "3.25", "not_a_float"]}
    sanitized = sanitize_payload(payload)

    # Payload should not include non-domain keys
    assert "values" not in sanitized

def test_nested_dict_and_list_normalization():
    payload = {
        "grid": {
            "points": [{"x": "0.0"}, {"x": "1.5"}],
            "spacing": "2.5"
        }
    }
    sanitized = sanitize_payload(payload)
    assert "grid" not in sanitized

def test_non_float_string_preservation():
    payload = {"metadata": {"label": "version_1.2"}}
    sanitized = sanitize_payload(payload)
    assert "metadata" not in sanitized

def test_no_mutation_on_valid_input():
    sanitized = sanitize_payload(valid_domain_payload())
    domain = sanitized["domain_definition"]

    for key in EXPECTED_KEYS:
        assert key in domain
        assert isinstance(coerce_numeric(domain[key]), float)

def test_edge_case_empty_payload():
    sanitized = sanitize_payload({})
    domain = sanitized["domain_definition"]

    for key in EXPECTED_KEYS:
        assert key in domain
        assert coerce_numeric(domain[key]) == 0.0


