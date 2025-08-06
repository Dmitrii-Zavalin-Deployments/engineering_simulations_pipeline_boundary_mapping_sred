# 📄 src/rules/rule_engine_utils.py

import logging
import unicodedata  # ✅ Added for Unicode digit detection
from src.rules.config import debug_log

logger = logging.getLogger(__name__)

class RuleEvaluationError(Exception):
    """Raised when a rule evaluation fails due to missing keys or invalid logic."""
    pass

def is_symbolic_reference(val: str) -> bool:
    return isinstance(val, str) and '.' in val and not val.replace('.', '', 1).isdigit()

def get_nested_value(payload: dict, path: str):
    keys = path.split(".")
    value = payload
    for k in keys:
        if not isinstance(value, dict):
            raise RuleEvaluationError(
                f"Expected dict at '{k}' in path '{path}', but got {type(value)}"
            )
        if k not in value:
            raise RuleEvaluationError(f"Missing key in expression: {path}")
        value = value[k]
        if value is None and k != keys[-1]:
            raise RuleEvaluationError(
                f"Null value encountered at '{k}' in path '{path}'"
            )
        debug_log(f"Resolved key '{k}' → {value}")
    return value

def is_fullwidth_digit(s) -> bool:
    """Detect if a string contains full-width Unicode digits."""
    return any(unicodedata.east_asian_width(c) == 'F' for c in str(s))

def coerce_relaxed_type_if_needed(left, right, relaxed_mode: bool):
    """
    Applies stricter relaxed-mode fallback logic to prevent unintended coercion.
    Only allows string-to-numeric coercion if input is numerically valid.
    """
    if not relaxed_mode:
        return left, right

    # 🚫 Defensive rejection for Unicode-style digits
    if is_fullwidth_digit(left) or is_fullwidth_digit(right):
        raise RuleEvaluationError(
            f"Incompatible coercion: {left} or {right} contains full-width digits"
        )

    # Only coerce if types are mismatched: string vs number
    if isinstance(left, str) and isinstance(right, (int, float)):
        try:
            left = float(left)
        except ValueError:
            raise RuleEvaluationError(f"Incompatible coercion: '{left}' to {type(right)}")

    elif isinstance(right, str) and isinstance(left, (int, float)):
        try:
            right = float(right)
        except ValueError:
            raise RuleEvaluationError(f"Incompatible coercion: '{right}' to {type(left)}")

    return left, right



