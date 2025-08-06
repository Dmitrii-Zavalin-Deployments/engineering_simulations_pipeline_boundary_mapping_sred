# src/validation/expression_utils.py

import ast

__all__ = [
    "parse_literal",
    "is_literal",
    "normalize_quotes",
    "is_symbolic_reference",
    "is_valid_numeric_literal"
]

def normalize_quotes(expr: str) -> str:
    """
    Cleans up deeply nested or redundant quote tokens.

    Examples:
        normalize_quotes("'''hello'''") returns "'hello'"
        normalize_quotes("''string''") returns "'string'"
        normalize_quotes('""data""') returns '"data"'
    """
    expr = expr.strip()
    expr = expr.replace("'''", "'").replace('"""', '"')
    expr = expr.replace("''", "'").replace('""', '"')
    return expr

def parse_literal(value: str):
    """
    Safely converts a string representation into its Python literal equivalent.

    Supported conversions:
        parse_literal("42") returns 42
        parse_literal("3.14") returns 3.14
        parse_literal("'hello'") returns "hello"
        parse_literal('"world"') returns "world"
        parse_literal("true") returns True
        parse_literal("null") returns None
        parse_literal("00123") returns 123
    """
    if not isinstance(value, str):
        return value

    val = normalize_quotes(value).strip()
    val_lower = val.lower()

    if val_lower == "true":
        return True
    if val_lower == "false":
        return False
    if val_lower in {"null", "none"}:
        return None

    if (val.startswith("'") and val.endswith("'")) or (val.startswith('"') and val.endswith('"')):
        return val[1:-1]

    if val.isdigit():
        return int(val)

    try:
        return ast.literal_eval(val)
    except Exception:
        return val

def is_literal(token: str) -> bool:
    """
    Determines whether the token represents a primitive literal.
    """
    token = token.strip().lower()
    if token in {"true", "false", "null", "none"}:
        return True
    if token.isnumeric():
        return True
    if (token.startswith("'") and token.endswith("'")) or (token.startswith('"') and token.endswith('"')):
        return True
    return False

def is_symbolic_reference(val: str) -> bool:
    """
    Detects whether a string is a symbolic reference (e.g. 'x.y') rather than a literal.

    Enhanced to exclude numeric-like strings mistakenly classified as symbolic.

    Examples:
        is_symbolic_reference("x.y") → True
        is_symbolic_reference("42") → False
        is_symbolic_reference("150") → False
        is_symbolic_reference("system.status.code") → True
        is_symbolic_reference("true") → False
    """
    if not isinstance(val, str):
        return False

    val = val.strip()
    if val.lower() in {"true", "false", "null", "none"}:
        return False

    try:
        float(val)
        return False
    except ValueError:
        return "." in val or "[" in val or "]" in val

def is_valid_numeric_literal(val: str) -> bool:
    """
    Determines if a string can safely be coerced into a numeric literal.
    """
    try:
        float(val)
        return True
    except Exception:
        return False



