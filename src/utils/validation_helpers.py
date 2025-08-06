# src/utils/validation_helpers.py

"""
Validation helper routines for input consistency and rule safety.

Includes reusable logic to pre-check values before coercion, casting, or expression evaluation.
Use these to avoid runtime errors and enforce reliable type handling across the system.
"""

from typing import Any


def is_valid_numeric_string(s: Any) -> bool:
    """
    Returns True if the input can be safely parsed as a float.

    Accepts int, float, str-representations of numeric values, or boolean primitives.
    Returns False for malformed strings, collections, or incompatible types.
    """
    try:
        # Defensive: skip types that shouldn't be coerced
        if isinstance(s, (list, dict, set, tuple)):
            return False
        float(s)
        return True
    except (ValueError, TypeError):
        return False


# --- Internal validation for edge-case literals (safe to remove if handled in external test suite)
if __name__ == "__main__":
    # ✅ Should return True
    assert is_valid_numeric_string("123") is True
    assert is_valid_numeric_string("0.0") is True
    assert is_valid_numeric_string("-42") is True
    assert is_valid_numeric_string("1e4") is True

    # ❌ Should return False
    assert is_valid_numeric_string("not_found") is False
    assert is_valid_numeric_string("NaNnot") is False
    assert is_valid_numeric_string("404error") is False
    assert is_valid_numeric_string("none") is False
    assert is_valid_numeric_string("1a") is False

    # ✅ Supported types
    assert is_valid_numeric_string(3.14) is True
    assert is_valid_numeric_string(10) is True
    assert is_valid_numeric_string(True) is True

    # ❌ Unsupported containers
    assert is_valid_numeric_string(["123"]) is False
    assert is_valid_numeric_string({"val": "123"}) is False

    print("All numeric string validation checks passed.")



