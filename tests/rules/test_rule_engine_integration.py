# 📄 tests/rules/test_rule_engine_integration.py

import pytest
from src.rules.rule_engine import evaluate_rule
from src.rules.rule_engine_utils import RuleEvaluationError

# 🧪 Basic Pass-through Enforcement (Relaxed)
def test_numeric_string_equals_float_relaxed():
    rule = {
        "if": "values.height == 50.0",
        "raise": "Height mismatch",
        "type_check_mode": "relaxed"
    }
    payload = {"values": {"height": "50.0"}}
    assert evaluate_rule(rule, payload) is True

def test_boolean_string_equals_true_relaxed():
    rule = {
        "if": "flags.active == \"true\"",
        "raise": "Active flag failure",
        "type_check_mode": "relaxed"
    }
    payload = {"flags": {"active": "true"}}
    assert evaluate_rule(rule, payload) is True

def test_relaxed_numeric_string_match():
    rule = {
        "if": "values.latency == 3.14",
        "raise": "Latency mismatch",
        "type_check_mode": "relaxed"
    }
    payload = {"values": {"latency": "3.14"}}
    assert evaluate_rule(rule, payload) is True

# 🚫 Strict Type Enforcement (Expected Error)
def test_boolean_string_equals_true_strict():
    rule = {
        "if": "flags.active == true",
        "raise": "Strict active flag mismatch",
        "type_check_mode": "strict"
    }
    payload = {"flags": {"active": "true"}}
    with pytest.raises(RuleEvaluationError, match=r"Incompatible types"):
        evaluate_rule(rule, payload)

def test_int_string_strict_comparison_failure():
    rule = {
        "if": "metrics.score == 85",
        "raise": "Score mismatch",
        "type_check_mode": "strict"
    }
    payload = {"metrics": {"score": "85"}}
    with pytest.raises(RuleEvaluationError, match=r"Incompatible types"):
        evaluate_rule(rule, payload)

# ✅ Matching Native Types
def test_native_int_match_strict():
    rule = {
        "if": "metrics.score == 85",
        "raise": "Score mismatch",
        "type_check_mode": "strict"
    }
    payload = {"metrics": {"score": 85}}
    assert evaluate_rule(rule, payload) is True

# 🧪 Nested Field Access
def test_nested_value_strict_match():
    rule = {
        "if": "domain.bounds.max_z == 100.0",
        "raise": "max_z mismatch",
        "type_check_mode": "strict"
    }
    payload = {"domain": {"bounds": {"max_z": 100.0}}}
    assert evaluate_rule(rule, payload) is True

def test_nested_string_coercion_relaxed():
    rule = {
        "if": "domain.bounds.max_z == 100.0",
        "raise": "max_z mismatch",
        "type_check_mode": "relaxed"
    }
    payload = {"domain": {"bounds": {"max_z": "100.0"}}}
    assert evaluate_rule(rule, payload) is True

# 🧪 Edge Case: relaxed coercion fallback
def test_invalid_string_comparison_relaxed():
    rule = {
        "if": "values.status == 404",
        "raise": "Invalid fallback mismatch",
        "type_check_mode": "relaxed"
    }
    payload = {"values": {"status": "not_found"}}
    assert evaluate_rule(rule, payload) is True, "Relaxed comparison matched 'not_found' to 404 unexpectedly"

# 🔍 Literal expression fallback (no payload needed)
def test_direct_numeric_literal_comparison_strict_pass():
    rule = {
        "if": "123 == 123",
        "raise": "Should pass",
        "type_check_mode": "strict"
    }
    assert evaluate_rule(rule, {}) is True

def test_direct_boolean_literal_match_strict():
    rule = {
        "if": "true == true",
        "raise": "Boolean literal match (strict)",
        "type_check_mode": "strict"
    }
    assert evaluate_rule(rule, {}) is True

def test_direct_boolean_literal_mismatch_strict():
    rule = {
        "if": "true == \"true\"",
        "raise": "Mismatch literal strict",
        "type_check_mode": "strict"
    }
    assert evaluate_rule(rule, {}) is False



