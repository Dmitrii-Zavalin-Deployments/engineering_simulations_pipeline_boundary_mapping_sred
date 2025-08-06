# tests/rules/test_operators.py

import pytest
from src.rules import operators
from src.rules.operators import OperatorError

# ---------------- Operator functions ----------------

@pytest.mark.parametrize("a,b,func,result", [
    (1, 1, operators.op_eq, True),
    (1, 2, operators.op_ne, True),
    (1, 2, operators.op_lt, True),
    (2, 2, operators.op_le, True),
    (3, 2, operators.op_gt, True),
    (2, 2, operators.op_ge, True),
])
def test_comparison_functions(a, b, func, result):
    """✅ Basic comparison operator results."""
    assert func(a, b) == result

def test_op_in_membership():
    """✅ Checks inclusion in list and string."""
    assert operators.op_in("a", ["a", "b"]) is True
    assert operators.op_in("z", "xyz") is True

def test_op_not_in_membership():
    """✅ Checks negated membership."""
    assert operators.op_not_in("x", ["a", "b"]) is True
    assert operators.op_not_in("a", "xyz") is True

def test_op_matches_valid():
    """✅ Regex match returns expected boolean."""
    assert operators.op_matches("abc", r"\w+") is True
    assert operators.op_matches("123", r"\D+") is False

def test_op_matches_invalid_type():
    """🚫 Non-string pattern raises TypeError."""
    with pytest.raises(TypeError):
        operators.op_matches("test", 123)


# ---------------- normalize_operator ----------------

@pytest.mark.parametrize("raw,normalized", [
    ("===", "=="),
    ("!==", "!="),
    (">>", ">"),
    ("<<", "<"),
    (">==", ">="),
    ("<==", "<="),
    ("++", "+"),
    ("--", "-"),
    ("%%", "%"),
    (" in ", "in"),  # spacing stripped
    ("unknown", "unknown"),
])
def test_normalize_operator(raw, normalized):
    """✅ Operator strings are normalized correctly or returned unchanged."""
    assert operators.normalize_operator(raw) == normalized


# ---------------- resolve_operator ----------------

@pytest.mark.parametrize("op_str,expected_func", [
    ("==", operators.op_eq),
    ("!==", operators.op_ne),  # normalized
    ("matches", operators.op_matches),
])
def test_resolve_operator_valid(op_str, expected_func):
    """✅ Operator resolves to expected function."""
    assert operators.resolve_operator(op_str) == expected_func

def test_resolve_operator_invalid():
    """🚫 Unsupported operator raises error."""
    with pytest.raises(OperatorError) as exc:
        operators.resolve_operator("~~~")
    assert "Unsupported comparison operator" in str(exc.value)

def test_resolve_operator_strip_and_normalize():
    """✅ Handles surrounding whitespace and normalization."""
    assert operators.resolve_operator(" >== ") == operators.op_ge



