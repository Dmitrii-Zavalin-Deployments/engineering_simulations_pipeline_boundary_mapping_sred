# 📄 tests/validation/test_validation_profile_expressions.py

import os
import pytest

# ✅ Test Enhancement: Enable debug mode globally during expression tests
os.environ["ENABLE_RULE_DEBUG"] = "true"

from src.rules.rule_engine import (
    get_nested_value,
    _evaluate_expression,
    RuleEvaluationError
)

# 🧪 Centralized payload and config import
from tests.conftest import get_payload_with_defaults
from configs.rule_engine_defaults import get_type_check_flags

# 🧪 Assertion Wrapper
from tests.helpers.assertions import assert_expression
from src.utils.coercion import relaxed_equals  # ✅ NEW: Added for direct logic test

# 🔍 Nested Key Access
def test_get_nested_value_success():
    payload = {"a": {"b": {"c": 42}}}
    assert get_nested_value(payload, "a.b.c") == 42

def test_get_nested_value_missing_key():
    payload = {"a": {"b": {"c": 42}}}
    with pytest.raises(RuleEvaluationError) as e:
        get_nested_value(payload, "a.x.c")
    assert "Missing key" in str(e.value)

# 🔧 Expression Evaluation — Core
@pytest.mark.parametrize("expr, payload, expected", [
    ("values.x == 5", {"values": {"x": 5}}, True),
    ("data.flag != \"true\"", {"data": {"flag": "true"}}, True),  # ✅ FIXED
    ("limits.upper > 5.0", {"limits": {"upper": 10.0, "lower": 5.0}}, True),
    ("metrics.score < 0.5", {"metrics": {"score": "0.3"}}, True),
    ("config.enabled == \"true\"", {"config": {"enabled": "true"}}, True),
])
def test_evaluate_expression_basic(expr, payload, expected):
    flags = get_type_check_flags("relaxed")
    result = _evaluate_expression(expr, payload, **flags)
    assert result is expected

# 🧪 Type Coercion
def test_expression_evaluation_type_coercion_float_str():
    payload = get_payload_with_defaults({
        "domain_definition": {
            "max_z": "100.0",
            "min_z": "90.5"
        }
    })
    flags = get_type_check_flags("relaxed")
    assert_expression("domain_definition.max_z >= domain_definition.min_z", payload, flags)

def test_expression_evaluation_type_coercion_int_str():
    payload = get_payload_with_defaults({
        "thresholds": {
            "max_val": "150",
            "warn_val": "150"
        }
    })
    flags = get_type_check_flags("relaxed")
    assert_expression("thresholds.max_val == thresholds.warn_val", payload, flags)

def test_expression_evaluation_type_coercion_mixed_types():
    payload = get_payload_with_defaults({
        "a": {"b": "10"},
        "x": {"y": "10"}
    })
    flags = get_type_check_flags("relaxed")
    assert_expression("a.b == x.y", payload, flags)

# 🚫 Failure & Exceptions
def test_expression_evaluation_incompatible_types():
    payload = {"flag": "false"}
    flags = get_type_check_flags("strict")
    with pytest.raises(RuleEvaluationError):
        _evaluate_expression("flag == true", payload, **flags)

def test_expression_evaluation_unsupported_operator():
    payload = {"meta": {"score": 85}}
    with pytest.raises(RuleEvaluationError) as err:
        _evaluate_expression("meta.score %% 80", payload)
    assert "Unsupported operator" in str(err.value)

def test_expression_evaluation_missing_key_path():
    payload = {"data": {"valid": True}}
    with pytest.raises(RuleEvaluationError) as err:
        _evaluate_expression("data.missing_key == true", payload)
    assert "Missing key" in str(err.value)

def test_expression_evaluation_missing_key_relaxed_fallback():
    payload = {"a": {"x": "value"}}
    flags = get_type_check_flags("relaxed")
    assert_expression("a.missing == null", payload, flags)

def test_expression_evaluation_nested_key_resolution():
    payload = get_payload_with_defaults({
        "expected": {"value": "42"},
        "system": {"subsystem": {"value": "42"}}
    })
    flags = get_type_check_flags("relaxed")
    assert_expression("system.subsystem.value == expected.value", payload, flags)

def test_literal_vs_native_equivalence():
    payload = {"flag": True, "count": 123}
    flags = get_type_check_flags("relaxed")
    assert_expression("flag == true", payload, flags)
    assert_expression("count == 123", payload, flags)

def test_literal_comparison_strict_type_enabled():
    payload = {"flag": True, "count": 123}
    flags = get_type_check_flags("strict")
    assert_expression("flag == true", payload, flags)
    assert_expression("count == 123", payload, flags)
    with pytest.raises(RuleEvaluationError):
        _evaluate_expression("flag == 1", payload, **flags)

def test_literal_comparison_strict_type_disabled():
    payload = {"flag": "true", "count": "123"}
    flags = get_type_check_flags("relaxed")
    assert_expression("flag == \"true\"", payload, flags)
    assert_expression("count == 123", payload, flags)

@pytest.mark.parametrize("expression,payload,mode,expected", [
    ("x.val == 100", {"x": {"val": 100}}, "strict", True),
    ("x.val == 100", {"x": {"val": "100"}}, "relaxed", True),
    ("x.flag == true", {"x": {"flag": True}}, "strict", True),
    ("x.flag == true", {"x": {"flag": "true"}}, "relaxed", True),
])
def test_strict_vs_relaxed_behavior(expression, payload, mode, expected):
    flags = get_type_check_flags(mode)
    result = _evaluate_expression(expression, payload, **flags)
    assert result is expected

def test_non_expression_literal_equality():
    flags = get_type_check_flags("relaxed")
    assert_expression("123 == 123", {}, flags)
    assert_expression("'hello' == 'hello'", {}, flags)
    payload = {"hello": "world"}
    assert_expression("hello == 'world'", payload, flags)

def test_literal_mismatch_fallback():
    payload = {"hello": "world"}
    flags = get_type_check_flags("relaxed")
    result = _evaluate_expression("'hello' == 100", payload, **flags)
    assert result is False
    with pytest.raises(RuleEvaluationError):
        _evaluate_expression("true == \"true\"", payload, **get_type_check_flags("strict"))

def test_invalid_operator_literal_case():
    with pytest.raises(RuleEvaluationError) as err:
        _evaluate_expression("false %% true", {})
    assert "Unsupported operator" in str(err.value)

# ✅ NEW: Direct unit test for relaxed_equals coercion logic
def test_relaxed_equals_coercion():
    assert relaxed_equals("42", 42)
    assert relaxed_equals("true", True)
    assert relaxed_equals("90.5", 90.5)
    assert relaxed_equals("010", 10)
    assert not relaxed_equals("not_a_number", 200)
    assert not relaxed_equals("NaN", 200)  # ✅ ADDED



