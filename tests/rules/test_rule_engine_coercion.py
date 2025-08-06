# 📄 tests/rules/test_rule_engine_coercion.py

import pytest
from src.rules.rule_engine_utils import coerce_relaxed_type_if_needed, RuleEvaluationError

# 🧪 Basic Coercion Pass Cases
def test_string_to_float_success_relaxed():
    left, right = "3.14", 3.14
    result = coerce_relaxed_type_if_needed(left, right, relaxed_mode=True)
    assert result == (3.14, 3.14)

def test_int_vs_string_int_relaxed():
    left, right = 100, "100"
    result = coerce_relaxed_type_if_needed(left, right, relaxed_mode=True)
    assert result == (100.0, 100.0)

# 🚫 Coercion Failures
def test_non_numeric_string_to_float_failure():
    left, right = "banana", 3.14
    with pytest.raises(RuleEvaluationError, match=r"Incompatible coercion: 'banana'"):
        coerce_relaxed_type_if_needed(left, right, relaxed_mode=True)

def test_non_numeric_string_to_int_failure():
    left, right = "nullish", 404
    with pytest.raises(RuleEvaluationError, match=r"Incompatible coercion: 'nullish'"):
        coerce_relaxed_type_if_needed(left, right, relaxed_mode=True)

# ✅ Strict Mode: No Coercion Attempted
def test_strict_mode_skips_coercion():
    left, right = "123", 123
    result = coerce_relaxed_type_if_needed(left, right, relaxed_mode=False)
    assert result == ("123", 123)

# 🔁 Roundtrip Verification
@pytest.mark.parametrize("input_value, numeric_target", [
    ("42", 42),
    ("0.001", 0.001),
    ("85.0", 85),
    ("999", 999.0),
])
def test_relaxed_numeric_string_roundtrip(input_value, numeric_target):
    left, right = input_value, numeric_target
    coerced = coerce_relaxed_type_if_needed(left, right, relaxed_mode=True)
    assert abs(coerced[0] - coerced[1]) < 0.0001

# 🧪 Symmetric coercion checks
def test_right_string_coerced_to_float():
    left, right = 5.5, "5.5"
    result = coerce_relaxed_type_if_needed(left, right, relaxed_mode=True)
    assert result == (5.5, 5.5)

def test_right_string_coerced_to_int():
    left, right = 404, "404"
    result = coerce_relaxed_type_if_needed(left, right, relaxed_mode=True)
    assert result == (404.0, 404.0)

# 🛡️ Edge Case: Unicode numeric string
def test_unicode_numeric_string():
    left, right = "４２", 42  # Full-width Unicode digit
    with pytest.raises(RuleEvaluationError):
        coerce_relaxed_type_if_needed(left, right, relaxed_mode=True)

# 📌 Mixed-type safety: bool vs string
def test_string_vs_boolean_relaxed():
    left, right = "true", True
    with pytest.raises(RuleEvaluationError, match=r"Incompatible coercion: 'true'"):
        coerce_relaxed_type_if_needed(left, right, relaxed_mode=True)

def test_boolean_vs_string_strict():
    left, right = True, "false"
    result = coerce_relaxed_type_if_needed(left, right, relaxed_mode=False)
    assert result == (True, "false")



