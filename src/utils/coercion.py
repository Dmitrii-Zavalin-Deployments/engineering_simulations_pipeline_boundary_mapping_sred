# src/utils/coercion.py

"""
Type coercion helpers tailored for rule evaluation.

Used to convert raw values during expression parsing and logical comparisons.
Ensures safety and consistency for numeric and boolean operations under strict or relaxed modes.

Available Methods:
- coerce_numeric(value)
- coerce_boolean(value)
- coerce_string(value)
- safe_float(value)
- relaxed_cast(value, target_type)
- relaxed_equals(lhs, rhs)
"""

import math
from typing import Any, Union, Optional
from src.rules.config import debug_log
from src.utils.validation_helpers import is_valid_numeric_string

def coerce_numeric(value: Any) -> Optional[float]:
    try:
        result = float(value)
        if math.isnan(result) or math.isinf(result):
            debug_log(f"[numeric] Rejected invalid float → result: {result} → returning None")
            return None
        debug_log(f"[numeric] Coerced native → {result}")
        return result
    except (ValueError, TypeError) as e:
        debug_log(f"[numeric] Native coercion failed for '{value}' → None | {e}")

    if is_valid_numeric_string(value):
        try:
            result = float(str(value).strip())
            if math.isnan(result) or math.isinf(result):
                debug_log(f"[numeric] Rejected string coercion → '{value}' → result: {result} → returning None")
                return None
            debug_log(f"[numeric] Coerced string '{value}' → {result}")
            return result
        except Exception as e:
            debug_log(f"[numeric] Coercion fallback failed for '{value}' → None | {e}")

    debug_log(f"[numeric] Rejected non-numeric value: '{value}'")
    return None

def coerce_boolean(value: Any) -> Union[bool, str, None]:
    try:
        str_value = str(value).strip().lower()
    except Exception as e:
        debug_log(f"[boolean] Coercion error from type {type(value).__name__} → returning None | {e}")
        return None

    if str_value in ("true", "1"):
        debug_log(f"[boolean] Interpreted input → True")
        return True
    elif str_value in ("false", "0"):
        debug_log(f"[boolean] Interpreted input → False")
        return False

    debug_log(f"[boolean] Unrecognized boolean form → fallback: '{str_value}'")
    return str_value

def coerce_string(value: Any) -> str:
    try:
        result = value.strip() if isinstance(value, str) else str(value)
        debug_log(f"[string] Coerced '{value}' → '{result}'")
        return result
    except Exception as e:
        debug_log(f"[string] Failed to coerce '{value}' → fallback: '' | {e}")
        return ""


def safe_float(value: Any) -> Optional[float]:
    try:
        result = float(value)
        debug_log(f"[safe_float] Parsed '{value}' → {result}")
        return result
    except Exception as e:
        debug_log(f"[safe_float] Failed to parse '{value}' → None | {e}")
        return None


def relaxed_cast(value: Any, target_type: type) -> Optional[Any]:
    """
    Defensive relaxed-mode type casting.
    Handles common encodings like "true", "123", etc. without raising.
    Returns None for unsafe or unrecognized cases.
    """
    try:
        if isinstance(value, target_type):
            debug_log(f"[relaxed_cast] Native {target_type.__name__} detected → {value}")
            return value

        if isinstance(value, str):
            stripped = value.strip().lower()
            if target_type == bool:
                if stripped in ("true", "1"):
                    debug_log(f"[relaxed_cast] Interpreted '{value}' → True")
                    return True
                elif stripped in ("false", "0"):
                    debug_log(f"[relaxed_cast] Interpreted '{value}' → False")
                    return False
            elif target_type == int and stripped.isdigit():
                result = int(stripped)
                debug_log(f"[relaxed_cast] Parsed '{value}' → {result}")
                return result
            elif target_type == float:
                try:
                    result = float(stripped)
                    if math.isnan(result):
                        debug_log(f"[relaxed_cast] Rejected NaN parsing for '{value}'")
                        return None
                    debug_log(f"[relaxed_cast] Parsed '{value}' → {result}")
                    return result
                except ValueError:
                    pass

        result = target_type(value)
        debug_log(f"[relaxed_cast] Fallback cast '{value}' → {result}")
        return result
    except Exception as e:
        debug_log(f"[relaxed_cast] Failed to cast '{value}' to {target_type.__name__} → None | {e}")
        return None


def relaxed_equals(lhs: Any, rhs: Any) -> bool:
    """
    Centralized relaxed comparison logic.
    Attempts to cast both values to a common type and compares the result.
    """
    for unsafe in ("nan", "not_a_number"):
        if isinstance(lhs, str) and lhs.strip().lower() == unsafe:
            debug_log(f"[relaxed_equals] Unsafe lhs input detected → '{lhs}' → rejecting comparison")
            return False
        if isinstance(rhs, str) and rhs.strip().lower() == unsafe:
            debug_log(f"[relaxed_equals] Unsafe rhs input detected → '{rhs}' → rejecting comparison")
            return False

    for target_type in (bool, int, float, str):
        lhs_cast = relaxed_cast(lhs, target_type)
        rhs_cast = relaxed_cast(rhs, target_type)
        if lhs_cast is not None and rhs_cast is not None and lhs_cast == rhs_cast:
            debug_log(f"[relaxed_equals] Matched via {target_type.__name__} → {lhs_cast} == {rhs_cast}")
            return True
    debug_log(f"[relaxed_equals] No match: {lhs} != {rhs}")
    return False



