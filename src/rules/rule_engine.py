# 📄 src/rules/rule_engine.py

import logging
from configs.rule_engine_defaults import get_type_check_mode
from src.validation.expression_utils import parse_literal, is_literal
from src.validation.expression_utils import is_symbolic_reference
from src.rules.operators import resolve_operator, OperatorError, SUPPORTED_OPERATORS
from src.rules.config import debug_log
from src.rules.rule_engine_utils import (
    RuleEvaluationError,
    get_nested_value
)
from src.rules.rule_engine_coercion import _coerce_types_for_comparison  # ✅ Moved logic
from src.utils.coercion import relaxed_equals

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# ✳️ Expression Evaluation Notes
# ------------------------------------------------------------------
# Supported expression format:
#   <lhs path> <operator> <rhs literal or path>
# Example:
#   resolution.dx == None
#   temperature < 150
#
# 🛑 Unsupported operators include:
# - Python-native logical operators: 'is', 'is not', 'in', 'not in', 'not', 'and', 'or'
# - Multi-part or chained expressions
# - List/collection membership checks (unless explicitly supported in operator registry)
#
# 🚧 All supported operators must appear in SUPPORTED_OPERATORS
#       → Controlled centrally in src.rules.operators
# ------------------------------------------------------------------

def _evaluate_expression(
    expression: str,
    payload: dict,
    *,
    strict_type_check: bool = False,
    relaxed_type_check: bool = False
) -> bool:
    debug_log(f"Evaluating expression: {expression}")
    parts = expression.strip().split(" ", 3)
    if len(parts) != 3:
        raise RuleEvaluationError(f"Unsupported expression format: '{expression}'")

    lhs_path, operator_str, rhs_literal = parts
    debug_log(f"Parsed expression: lhs='{lhs_path}', operator='{operator_str}', rhs='{rhs_literal}'")

    if operator_str not in SUPPORTED_OPERATORS:
        raise RuleEvaluationError(
            f"Unsupported operator: '{operator_str}' — allowed operators: {', '.join(SUPPORTED_OPERATORS)}"
        )

    if not payload and all(is_literal(x) for x in [lhs_path, rhs_literal]):
        lhs_val = parse_literal(lhs_path)
        rhs_val = parse_literal(rhs_literal)
        try:
            compare_fn = resolve_operator(operator_str)
            debug_log(f"Literal-only fast-path → {lhs_val} {operator_str} {rhs_val}")
            return compare_fn(lhs_val, rhs_val)
        except Exception as e:
            raise RuleEvaluationError(f"Literal comparison failed: {e}")

    try:
        lhs_value = get_nested_value(payload, lhs_path)
    except RuleEvaluationError as e:
        if relaxed_type_check:
            lhs_value = None
            logger.debug(f"Relaxed mode fallback for missing key '{lhs_path}': {e}")
            debug_log(f"Relaxed fallback: missing key '{lhs_path}', using None")
        else:
            raise

    try:
        compare_fn = resolve_operator(operator_str)
        debug_log(f"Resolved operator '{operator_str}' → {compare_fn}")
    except OperatorError:
        raise RuleEvaluationError(f"Operator resolution failed: {operator_str}")

    rhs_resolved_from_payload = False
    try:
        rhs_value = parse_literal(rhs_literal)
        debug_log(f"Parsed rhs literal: {rhs_value}")
    except ValueError as rhs_error:
        debug_log(f"Literal parsing failed for RHS: '{rhs_literal}' → {rhs_error}")
        if relaxed_type_check:
            debug_log(f"Attempting to resolve RHS path: {rhs_literal}")
            try:
                rhs_value = get_nested_value(payload, rhs_literal)
                rhs_resolved_from_payload = True
                debug_log(f"Fallback: Resolved RHS from payload key path '{rhs_literal}' → {rhs_value}")
            except RuleEvaluationError as e:
                logger.debug(f"Relaxed RHS fallback key resolution failed: {e}")
                rhs_value = None
                debug_log(f"Fallback: Using None for RHS '{rhs_literal}' due to resolution failure")
        else:
            raise RuleEvaluationError(f"Invalid RHS literal: '{rhs_literal}'")

    if relaxed_type_check and (
        lhs_value is None or rhs_value is None or
        is_symbolic_reference(lhs_path) or is_symbolic_reference(rhs_literal)
    ):
        debug_log("Skipping coercion: unresolved or symbolic path in relaxed mode")
        result = relaxed_equals(lhs_value, rhs_value)
        debug_log(f"Relaxed comparison → {lhs_value} ~ {rhs_value} → {result}")
        return result

    try:
        if strict_type_check:
            debug_log("Strict type check enabled")
            if type(lhs_value) != type(rhs_value):
                raise RuleEvaluationError(f"Incompatible types: {type(lhs_value)} vs {type(rhs_value)}")
        elif relaxed_type_check:
            debug_log("Relaxed type check enabled")
            if not rhs_resolved_from_payload:
                lhs_value, rhs_value = _coerce_types_for_comparison(lhs_value, rhs_value)
            else:
                debug_log("RHS was resolved from payload — skipping coercion on original string")
        else:
            debug_log("Default strict check")
            if type(lhs_value) != type(rhs_value):
                raise RuleEvaluationError(f"Type mismatch (default strict): {type(lhs_value)} vs {type(rhs_value)}")
    except Exception as e:
        raise RuleEvaluationError(f"Coercion error: {e}")

    try:
        if relaxed_type_check:
            debug_log("Using relaxed comparison logic")
            result = relaxed_equals(lhs_value, rhs_value)
            debug_log(f"Relaxed final comparison → {lhs_value} ~ {rhs_value} → {result}")
        else:
            result = compare_fn(lhs_value, rhs_value)
            debug_log(f"Strict final comparison → {lhs_value} {operator_str} {rhs_value} → {result}")
        return result
    except Exception as e:
        raise RuleEvaluationError(f"Comparison failed: {e}")

def evaluate_rule(rule: dict, payload: dict, *, strict_type_check: bool = False, relaxed_type_check: bool = False) -> bool:
    expression = rule.get("if")
    if not expression or not isinstance(expression, str):
        debug_log("Empty or malformed rule expression; returning True")
        return True

    if not (strict_type_check or relaxed_type_check):
        try:
            type_mode = get_type_check_mode(rule.get("type_check_mode"))
            debug_log(f"Resolved type check mode: {type_mode}")
        except Exception as config_error:
            logger.warning(f"Invalid type check mode override: {config_error}")
            type_mode = "strict"
            debug_log("Fallback type check mode: strict")

        strict_type_check = type_mode == "strict"
        relaxed_type_check = type_mode == "relaxed"

    return _evaluate_expression(
        expression,
        payload,
        strict_type_check=strict_type_check,
        relaxed_type_check=relaxed_type_check
    )



