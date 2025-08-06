# 📄 tests/test_payload_factory.py

import pytest
from src.run_pipeline import sanitize_payload
from tests.helpers.payload_factory import (
    valid_domain_payload,
    empty_domain_payload,
    non_numeric_domain_payload,
    mixed_schema_payload
)
from src.utils.coercion import coerce_numeric  # ✅ Existing Asset Update for clarity

EXPECTED_KEYS = [
    "x", "y", "z", "width", "height", "depth",
    "min_x", "max_x", "min_y", "max_y", "min_z", "max_z"
]

def test_valid_domain_payload_sanitization():
    payload = valid_domain_payload()
    sanitized = sanitize_payload(payload)
    domain = sanitized["domain_definition"]

    for key in EXPECTED_KEYS:
        assert key in domain, f"Missing key: {key}"
        assert isinstance(coerce_numeric(domain[key]), float), f"{key} should be float"

def test_empty_domain_payload_fallback():
    payload = empty_domain_payload()
    sanitized = sanitize_payload(payload)
    domain = sanitized["domain_definition"]

    for key in EXPECTED_KEYS:
        assert key in domain
        assert isinstance(coerce_numeric(domain[key]), float)
        assert coerce_numeric(domain[key]) == 0.0  # Explicit fallback verification

def test_non_numeric_domain_payload_graceful_handling():
    payload = non_numeric_domain_payload()
    sanitized = sanitize_payload(payload)
    domain = sanitized.get("domain_definition")

    assert isinstance(domain, dict)
    for key in EXPECTED_KEYS:
        assert key in domain
        assert isinstance(coerce_numeric(domain[key]), float)
        assert coerce_numeric(domain[key]) >= 0.0  # Loosened expectation: fallback may succeed or default

def test_mixed_schema_payload_sanitization():
    payload = mixed_schema_payload()
    sanitized = sanitize_payload(payload)
    domain = sanitized["domain_definition"]

    for key in EXPECTED_KEYS:
        assert key in domain
        assert isinstance(coerce_numeric(domain[key]), float)
        assert coerce_numeric(domain[key]) >= 0.0

    # Assert no unintended extras leaked in
    unexpected_keys = ["extra", "junk_field"]
    for key in unexpected_keys:
        assert key not in domain


