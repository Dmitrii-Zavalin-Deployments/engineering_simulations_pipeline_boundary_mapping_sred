# 📄 src/validation/validation_profile_expressions.py

def _evaluate_expression(lhs, rhs, operator: str, *, strict_type_check: bool = False):
    """
    Evaluates binary expressions with type safety and controlled fallback.

    Parameters:
        lhs (Any): Left-hand side value
        rhs (Any): Right-hand side value
        operator (str): Comparison operator (e.g., '==', '!=', '<', '>', '<=', '>=')
        strict_type_check (bool): Enforces strict type alignment if True; else allows coercion

    Returns:
        bool: Result of the comparison; False if type mismatch or operator error

    Examples:
        _evaluate_expression("123", 123, '==') ➝ True
        _evaluate_expression("hello", 100, '<') ➝ False
    """
    ops = {
        "==": lambda a, b: a == b,
        "!=": lambda a, b: a != b,
        "<":  lambda a, b: a < b,
        ">":  lambda a, b: a > b,
        "<=": lambda a, b: a <= b,
        ">=": lambda a, b: a >= b,
    }

    if strict_type_check and type(lhs) != type(rhs):
        return False

    # ✅ Fixed precedence bug for non-strict type mismatch
    if not strict_type_check and type(lhs) != type(rhs):
        try:
            if isinstance(lhs, (int, float)) or isinstance(rhs, (int, float)):
                lhs = float(lhs)
                rhs = float(rhs)
            else:
                lhs = str(lhs)
                rhs = str(rhs)
        except Exception:
            return False

    try:
        comparison_func = ops.get(operator)
        if not comparison_func:
            return False
        return comparison_func(lhs, rhs)
    except Exception:
        return False



