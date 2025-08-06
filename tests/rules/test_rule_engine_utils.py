# tests/rules/test_rule_engine_utils.py

import pytest
from src.rules import rule_engine_utils as utils
from src.rules.rule_engine_utils import RuleEvaluationError

# ---------------- is_symbolic_reference ----------------

def test_symbolic_valid_path():
    """✅ Detects symbolic reference like 'a.b'."""
    assert utils.is_symbolic_reference("user.age") is True

def test_symbolic_numeric_path():
    """✅ Excludes numeric string with dot."""
    assert utils.is_symbolic_reference("3.14") is False

def test_symbolic_non_string():
    """🚫 Non-string input is excluded."""
    assert utils.is_symbolic_reference(123.4) is False


# ---------------- get_nested_value ----------------

def test_nested_value_valid_resolution():
    """✅ Resolves path in nested dict."""
    payload = {"user": {"age": 30}}
    assert utils.get_nested_value(payload, "user.age") == 30

def test_nested_value_missing_key():
    """🚫 Missing key triggers RuleEvaluationError."""
    payload = {"user": {"age": 30}}
    with pytest.raises(RuleEvaluationError, match="Missing key"):
        utils.get_nested_value(payload, "user.name")

def test_nested_value_non_dict_intermediate():
    """🚫 Non-dict intermediate value raises error."""
    payload = {"user": "John"}
    with pytest.raises(RuleEvaluationError, match="Expected dict"):
        utils.get_nested_value(payload, "user.name")

def test_nested_value_null_mid_path():
    """🚫 None before final key raises error."""
    payload = {"user": {"name": None, "age": 30}}
    with pytest.raises(RuleEvaluationError, match="Null value"):
        utils.get_nested_value(payload, "user.name.first")


# ---------------- is_fullwidth_digit ----------------

def test_fullwidth_digit_true():
    """✅ Detects full-width Unicode digit."""
    assert utils.is_fullwidth_digit("１") is True

def test_fullwidth_digit_false_ascii():
    """✅ ASCII digit returns False."""
    assert utils.is_fullwidth_digit("1") is False

def test_fullwidth_digit_mixed():
    """🚫 Mixed input returns True only if full-width present."""
    assert utils.is_fullwidth_digit("１２3") is True


# ---------------- coerce_relaxed_type_if_needed ----------------

def test_relaxed_mode_false():
    """✅ Returns unchanged values if relaxed mode is off."""
    result = utils.coerce_relaxed_type_if_needed("5", 10, False)
    assert result == ("5", 10)

def test_relaxed_fullwidth_digit_left():
    """🚫 Left contains full-width digit → raise error."""
    with pytest.raises(RuleEvaluationError, match="full-width"):
        utils.coerce_relaxed_type_if_needed("１23", 5, True)

def test_relaxed_fullwidth_digit_right():
    """🚫 Right contains full-width digit → raise error."""
    with pytest.raises(RuleEvaluationError, match="full-width"):
        utils.coerce_relaxed_type_if_needed(5, "１23", True)

def test_relaxed_valid_string_to_float():
    """✅ Coerces left string to float if valid."""
    left, right = utils.coerce_relaxed_type_if_needed("3.0", 5, True)
    assert isinstance(left, float) and left == 3.0
    assert right == 5

def test_relaxed_valid_right_string():
    """✅ Coerces right string to float if valid."""
    left, right = utils.coerce_relaxed_type_if_needed(3, "5.5", True)
    assert left == 3
    assert right == 5.5

def test_relaxed_invalid_string_cast_left():
    """🚫 Invalid cast left string → raises error."""
    with pytest.raises(RuleEvaluationError, match="Incompatible coercion"):
        utils.coerce_relaxed_type_if_needed("bad", 2, True)

def test_relaxed_invalid_string_cast_right():
    """🚫 Invalid cast right string → raises error."""
    with pytest.raises(RuleEvaluationError, match="Incompatible coercion"):
        utils.coerce_relaxed_type_if_needed(2, "bad", True)

def test_relaxed_type_mismatch_but_not_string():
    """🚫 Mismatched types but not string/number → no coercion."""
    result = utils.coerce_relaxed_type_if_needed(["a"], {"b": 2}, True)
    assert result == (["a"], {"b": 2})



