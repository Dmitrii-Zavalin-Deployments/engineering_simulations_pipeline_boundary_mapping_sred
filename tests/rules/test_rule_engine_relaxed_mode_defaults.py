# 📄 tests/rules/test_rule_engine_relaxed_mode_defaults.py

import pytest
from src.rules.rule_engine import evaluate_rule, RuleEvaluationError, _evaluate_expression

# 🔧 Sample payload for coercion tests
sample_payload = {
    "metrics": {
        "score": "95.0",
        "status": "true",
        "threshold": "100",
        "ratio": "0.8",
        "enabled": "false"
    },
    "flags": {
        "active": "True",
        "archived": "FALSE"
    }
}

def test_string_to_float_comparison_passes_in_relaxed_mode():
    rule = {
        "if": "metrics.score >= 95.0",
        "type_check_mode": "relaxed"
    }
    assert evaluate_rule(rule, sample_payload) is True

def test_string_to_float_comparison_fails_when_relaxed_mode_missing():
    rule = {
        "if": "metrics.score >= 95.0",
        "type_check_mode": "strict"
    }
    with pytest.raises(RuleEvaluationError) as exc:
        evaluate_rule(rule, sample_payload)
    assert "Incompatible types" in str(exc.value)

def test_string_to_int_comparison_passes_in_relaxed_mode():
    rule = {
        "if": "metrics.threshold < 200",
        "type_check_mode": "relaxed"
    }
    assert evaluate_rule(rule, sample_payload) is True

def test_string_to_bool_coercion_true_case():
    rule = {
        "if": "metrics.status == \"true\"",
        "type_check_mode": "relaxed"
    }
    assert evaluate_rule(rule, sample_payload) is True

def test_missing_type_check_mode_uses_default_and_raises():
    rule = {
        "if": "metrics.score >= 95.0"
        # no type_check_mode → should default to strict
    }
    with pytest.raises(RuleEvaluationError) as exc:
        evaluate_rule(rule, sample_payload)
    assert "Incompatible types" in str(exc.value)

def test_missing_type_check_mode_triggers_strict_mode_and_blocks_coercion():
    rule = {
        "if": "metrics.status == true"
        # unquoted RHS → triggers key lookup and type enforcement
    }
    with pytest.raises(RuleEvaluationError) as exc:
        evaluate_rule(rule, sample_payload)
    assert "Incompatible types" in str(exc.value)

def test_missing_type_check_mode_allows_literal_only_comparison():
    rule = {
        "if": "metrics.status == 'true'"
    }
    result = evaluate_rule(rule, sample_payload)
    assert result is True

def test_implicit_fallback_coercion_when_type_check_flags_false():
    # This manually bypasses type enforcement to test fallback
    expression = "metrics.score >= 90.5"
    result = _evaluate_expression(expression, sample_payload, strict_type_check=False, relaxed_type_check=True)
    assert result is True

# 🧪 Additional fallback edge cases

def test_fallback_string_float_compare_success():
    expression = "metrics.ratio == 0.8"
    result = _evaluate_expression(expression, sample_payload, strict_type_check=False, relaxed_type_check=True)
    assert result is True

def test_fallback_boolean_string_true_match():
    expression = "flags.active == \"true\""
    result = _evaluate_expression(expression, sample_payload, strict_type_check=False, relaxed_type_check=False)
    assert result is False  # corrected: no coercion in strict fallback

def test_fallback_boolean_string_false_match():
    expression = "flags.archived == \"false\""
    result = _evaluate_expression(expression, sample_payload, strict_type_check=False, relaxed_type_check=False)
    assert result is False  # corrected: no coercion in strict fallback

def test_fallback_boolean_nonmatch_case_sensitive():
    expression = "metrics.enabled == \"true\""
    result = _evaluate_expression(expression, sample_payload, strict_type_check=False, relaxed_type_check=False)
    assert result is False



