import pytest
from src.rules.rule_engine import evaluate_rule, RuleEvaluationError

# ✅ Valid Rule – Matches Value
def test_rule_evaluates_successfully():
    rule = {"if": "data.val == 42", "raise": "Value mismatch"}
    payload = {"data": {"val": 42}}
    assert evaluate_rule(rule, payload) is True

# ❌ Invalid Value – Should Trigger
def test_rule_fails_on_incorrect_value():
    rule = {"if": "data.flag == true", "raise": "Flag mismatch"}
    payload = {"data": {"flag": False}}
    assert evaluate_rule(rule, payload) is False

# 🧪 Type Coercion – Relaxed (Updated)
def test_rule_passes_with_coercion():
    rule = {"if": "stats.count == 100", "raise": "Count mismatch"}
    payload = {"stats": {"count": "100"}}
    result = evaluate_rule(rule, payload, relaxed_type_check=True)
    assert result is True  # ✅ Fixed: Rule passed

# 🚫 Strict Type Enforcement – Fail Expected (Updated)
def test_strict_type_check_fails_on_coercible_mismatch():
    rule = {
        "if": "stats.count == 100",
        "raise": "Strict count mismatch",
        "strict_type_check": True,
    }
    payload = {"stats": {"count": "100"}}
    with pytest.raises(RuleEvaluationError, match="Incompatible types") as exc:
        evaluate_rule(rule, payload, strict_type_check=True)
    assert "Incompatible types" in str(exc.value)

# ✅ Strict Match – Same Native Type
def test_strict_type_check_passes_on_native_match():
    rule = {
        "if": "stats.count == 100",
        "raise": "Strict count mismatch",
        "strict_type_check": True,
    }
    payload = {"stats": {"count": 100}}
    assert evaluate_rule(rule, payload, strict_type_check=True) is True

# 🧪 Fallback Handling – Non-Expression
def test_rule_with_non_expression_returns_true():
    rule = {"if": "", "raise": "Malformed rule"}
    payload = {"x": 1}
    assert evaluate_rule(rule, payload) is True

# 🚫 Malformed Expression – Missing Operator
def test_rule_with_invalid_expression_format():
    rule = {"if": "x_is_5", "raise": "Bad format"}
    payload = {"x_is_5": True}
    with pytest.raises(RuleEvaluationError, match="Unsupported expression format") as exc:
        evaluate_rule(rule, payload)
    assert "Unsupported expression format" in str(exc.value)

# 🚫 Missing Key – Nested Path
def test_rule_with_missing_key():
    rule = {"if": "user.email == 'abc'", "raise": "Email missing"}
    payload = {"user": {}}
    with pytest.raises(RuleEvaluationError, match="Missing key") as exc:
        evaluate_rule(rule, payload)
    assert "Missing key" in str(exc.value)

# 🚫 Operator Error – Unsupported Symbol (Updated)
def test_rule_with_bad_operator():
    rule = {"if": "a ++ b", "raise": "Bad operator"}
    payload = {"a": 1, "b": 2}
    with pytest.raises(RuleEvaluationError, match="Unsupported operator") as err:
        evaluate_rule(rule, payload)
    assert "Unsupported operator" in str(err.value)

# 🧪 Literal Handling – Null Comparison
def test_null_literal_passes():
    rule = {"if": "meta.info == null", "raise": "Info not null"}
    payload = {"meta": {"info": None}}
    assert evaluate_rule(rule, payload) is True

# 🚫 Type Mismatch – Incompatible Operation
def test_incompatible_type_error_strict_mode():
    rule = {
        "if": "meta.score == 'high'",
        "raise": "Score type mismatch",
        "strict_type_check": True,
    }
    payload = {"meta": {"score": 85}}
    with pytest.raises(RuleEvaluationError, match="Incompatible types") as exc:
        evaluate_rule(rule, payload, strict_type_check=True)
    assert "Incompatible types" in str(exc.value)

# 🆕 Strict Type Enforcement – Explicit Flag Without Rule Embedding
def test_rule_fails_with_strict_type_check_flag_only():
    rule = {"if": "stats.count == 100", "raise": "Flag-only coercion test"}
    payload = {"stats": {"count": "100"}}
    with pytest.raises(RuleEvaluationError, match="Incompatible types") as exc:
        evaluate_rule(rule, payload, strict_type_check=True)
    assert "Incompatible types" in str(exc.value)



