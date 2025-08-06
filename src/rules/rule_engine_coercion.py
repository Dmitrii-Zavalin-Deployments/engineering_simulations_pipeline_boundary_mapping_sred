# src/rules/rule_engine_coercion.py

from src.rules.config import debug_log
from src.rules.rule_engine_utils import RuleEvaluationError
from src.validation.expression_utils import is_symbolic_reference
from src.utils.validation_helpers import is_valid_numeric_string

def _coerce_types_for_comparison(left, right):
    """
    Coerces comparable values for relaxed rule evaluation.
    Applies defensive guards against symbolic references and non-numeric strings.
    Blocks unsafe coercion when operand types mismatch or values are unresolved.
    """
    try:
        debug_log(f"Attempting type coercion: left={left} ({type(left)}), right={right} ({type(right)})")

        if left is None or right is None:
            debug_log("Skipping coercion due to unresolved operand")
            return left, right

        if isinstance(left, str) and is_symbolic_reference(left):
            raise RuleEvaluationError(f"Cannot coerce unresolved reference: {left}")
        if isinstance(right, str) and is_symbolic_reference(right):
            raise RuleEvaluationError(f"Cannot coerce unresolved reference: {right}")

        if isinstance(left, bool) or isinstance(right, bool):
            coerced = bool(left), bool(right)
            debug_log(f"Coerced to boolean: {coerced}")
            return coerced

        # ⛔ Avoid invalid string-to-numeric coercion in relaxed mode
        if isinstance(left, str) and isinstance(right, (int, float)) and not is_valid_numeric_string(left):
            debug_log("Blocked invalid string-to-numeric coercion (left)")
            return left, right
        if isinstance(right, str) and isinstance(left, (int, float)) and not is_valid_numeric_string(right):
            debug_log("Blocked invalid string-to-numeric coercion (right)")
            return left, right

        if isinstance(left, (int, float)) and isinstance(right, str):
            if is_valid_numeric_string(right):
                right_coerced = type(left)(right)
                debug_log(f"Coerced right str to numeric: {right_coerced}")
                return left, right_coerced

        if isinstance(right, (int, float)) and isinstance(left, str):
            if is_valid_numeric_string(left):
                left_coerced = type(right)(left)
                debug_log(f"Coerced left str to numeric: {left_coerced}")
                return left_coerced, right

        if isinstance(left, str) and isinstance(right, str):
            for num_type in (int, float):
                if is_valid_numeric_string(left) and is_valid_numeric_string(right):
                    try:
                        left_num = num_type(left)
                        right_num = num_type(right)
                        debug_log(f"Coerced both strings to {num_type}: {left_num}, {right_num}")
                        return left_num, right_num
                    except Exception:
                        continue

        debug_log("Coercion fallback: using original values")
        return left, right

    except Exception as e:
        raise RuleEvaluationError(f"Type coercion failed in relaxed mode: {e}")



