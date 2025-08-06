# 📄 tests/helpers/payload_factory.py

"""
Payload factory fixtures for domain sanitizer tests.

These are raw input payloads meant to test pre-sanitization behavior.
They intentionally include legacy keys (e.g. min_x, nx) and malformed values
to validate sanitizer robustness and fallback logic.
"""

# 🧪 Expression Payload Support (Strategic Addition)
from tests.conftest import get_payload_with_defaults

def payload_for_expression_tests(overrides=None):
    """
    Provides reusable fallback payloads for rule evaluation and expression tests,
    with optional injection of key-specific overrides.

    Parameters:
        overrides (dict): Optional dictionary to override defaults.

    Returns:
        dict: Composite payload suitable for relaxed or strict rule tests.
    """
    return get_payload_with_defaults(overrides)


def valid_domain_payload():
    """Structured geometry definition using legacy bounds — before sanitization."""
    return {
        "domain_definition": {
            "min_x": 0.0, "max_x": 3.0,
            "min_y": 0.0, "max_y": 2.0,
            "min_z": 0.0, "max_z": 1.0
            # Optional: legacy resolution or dimensions
            # "nx": 3, "ny": 2, "nz": 1
        }
    }

def empty_domain_payload():
    """Edge case: empty domain section — sanitizer should inject defaults."""
    return {
        "domain_definition": {}
    }

def non_numeric_domain_payload():
    """Invalid values simulating corrupted or misconfigured input."""
    return {
        "domain_definition": {
            "min_x": "left",     # string label
            "max_x": "right",    # string label
            "min_y": None,       # null value
            "max_y": True,       # boolean
            "min_z": [],         # list
            "max_z": {}          # dict
        }
    }

def mixed_schema_payload():
    """Combines stringified floats, symbolic values, and extra metadata."""
    return {
        "domain_definition": {
            "min_x": "0.0",      # stringified float
            "max_x": 3.0,        # native float
            "min_y": 0.0,
            "max_y": "2.0",
            "min_z": "invalid_float",  # invalid string
            "max_z": 1.0
        },
        "extra": {
            "notes": "spatial context",
            "version": "1.0.3"
        }
    }


