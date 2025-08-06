# tests/utils/test_coercion.py

import pytest
from src.utils.coercion import (
    coerce_numeric, coerce_boolean, coerce_string,
    safe_float, relaxed_cast, relaxed_equals
)

# ---------------- coerce_numeric ----------------

def test_numeric_native_int():
    """✅ Native integer is coerced to float."""
    assert coerce_numeric(5) == 5.0

def test_numeric_valid_string(monkeypatch):
    """✅ Valid numeric string is coerced."""
    monkeypatch.setattr("src.utils.coercion.is_valid_numeric_string", lambda v: True)
    assert coerce_numeric("3.14") == 3.14

def test_numeric_invalid_string(monkeypatch):
    """🚫 String fails is_valid_numeric_string check."""
    monkeypatch.setattr("src.utils.coercion.is_valid_numeric_string", lambda v: False)
    assert coerce_numeric("abc") is None

def test_numeric_parse_failure(monkeypatch):
    """🚫 Valid numeric string fails float conversion."""
    monkeypatch.setattr("src.utils.coercion.is_valid_numeric_string", lambda v: True)
    assert coerce_numeric("1e1000") is None


# ---------------- coerce_boolean ----------------

@pytest.mark.parametrize("input_val,expected", [
    (True, True),
    (False, False),
    ("true", True),
    ("1", True),
    ("false", False),
    ("0", False),
])
def test_boolean_known_values(input_val, expected):
    """✅ Recognized boolean forms are coerced properly."""
    assert coerce_boolean(input_val) == expected

def test_boolean_unknown_string():
    """🚫 Unrecognized string falls back to lowercase."""
    assert coerce_boolean("maybe") == "maybe"

def test_boolean_str_cast_failure():
    """🚫 Defensive fallback returns None for str() failure."""
    class BadStr:
        def __str__(self): raise ValueError("intentional failure")

    assert coerce_boolean(BadStr()) is None  # ✅ Strict fallback check

# ---------------- coerce_string ----------------

def test_string_native_str():
    """✅ String input is stripped."""
    assert coerce_string("  test ") == "test"

def test_string_non_string():
    """✅ Non-string converted via str()."""
    assert coerce_string(123) == "123"

# ---------------- safe_float ----------------

def test_safe_float_valid():
    """✅ Parses valid float."""
    assert safe_float("3.0") == 3.0

def test_safe_float_invalid():
    """🚫 Returns None on error."""
    assert safe_float("abc") is None


# ---------------- relaxed_cast ----------------

def test_relaxed_cast_native_match():
    """✅ Returns native value."""
    assert relaxed_cast(True, bool) is True

def test_relaxed_cast_string_to_bool():
    """✅ Converts string to bool."""
    assert relaxed_cast("true", bool) is True
    assert relaxed_cast("false", bool) is False

def test_relaxed_cast_string_to_int():
    """✅ Converts digit string to int."""
    assert relaxed_cast("42", int) == 42

def test_relaxed_cast_string_to_float():
    """✅ Converts string to float."""
    assert relaxed_cast("4.2", float) == 4.2

def test_relaxed_cast_nan():
    """🚫 Rejects NaN parsing."""
    assert relaxed_cast("nan", float) is None

def test_relaxed_cast_fallback_success():
    """✅ Uses fallback type constructor."""
    assert relaxed_cast(1, str) == "1"

def test_relaxed_cast_fallback_failure():
    """🚫 All paths fail returns None."""
    class Bad: pass
    assert relaxed_cast(Bad(), float) is None


# ---------------- relaxed_equals ----------------

def test_relaxed_equals_match_bool():
    """✅ Both values match as bool."""
    assert relaxed_equals("true", True)

def test_relaxed_equals_match_int():
    """✅ Both values match as int."""
    assert relaxed_equals("42", 42)

def test_relaxed_equals_match_float():
    """✅ Both values match as float."""
    assert relaxed_equals("3.14", 3.14)

def test_relaxed_equals_match_string():
    """✅ Both values match as string."""
    assert relaxed_equals("abc", "abc")

def test_relaxed_equals_nan_blocked():
    """🚫 Unsafe string blocks comparison."""
    assert relaxed_equals("nan", "nan") is False

def test_relaxed_equals_no_match():
    """🚫 No common coercion results in False."""
    assert relaxed_equals("123", False) is False



