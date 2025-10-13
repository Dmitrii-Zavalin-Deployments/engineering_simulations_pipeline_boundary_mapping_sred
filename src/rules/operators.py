# 📄 src/rules/operators.py

import re

class OperatorError(Exception):
    """Raised when an unsupported or malformed operator is invoked."""

# 🔗 Centralized operator function definitions
def op_eq(a, b): return a == b
def op_ne(a, b): return a != b
def op_lt(a, b): return a < b
def op_le(a, b): return a <= b
def op_gt(a, b): return a > b
def op_ge(a, b): return a >= b
def op_in(a, b): return a in b
def op_not_in(a, b): return a not in b

def op_matches(a, b):
    """Regex match — assumes 'b' is a regex pattern"""
    if not isinstance(b, str):
        raise TypeError("Regex pattern must be a string")
    return re.fullmatch(b, str(a)) is not None

# 📦 Central registry of supported comparison operators
SUPPORTED_OPERATORS = {
    "==": op_eq,
    "!=": op_ne,
    "<": op_lt,
    "<=": op_le,
    ">": op_gt,
    ">=": op_ge,
    "in": op_in,
    "not in": op_not_in,
    "matches": op_matches,
}

def normalize_operator(op: str) -> str:
    """
    Normalize malformed or legacy-style operators to supported ones.

    Examples:
        '===' → '=='
        '!==', '>>', '%%' → normalized alternatives

    Parameters:
        op (str): Operator string possibly needing normalization

    Returns:
        str: Normalized operator string
    """
    alt_map = {
        "===": "==",
        "!==": "!=",
        ">>": ">",
        "<<": "<",
        ">==": ">=",
        "<==": "<=",
        "++": "+",
        "--": "-",
        "%%": "%",
    }
    return alt_map.get(op.strip(), op.strip())

def resolve_operator(op: str):
    """
    Retrieve the comparison function for a given operator.

    Parameters:
        op (str): Raw or normalized operator

    Returns:
        function: Callable comparison function

    Raises:
        OperatorError: If operator is malformed or unsupported
    """
    original = op.strip()
    normalized = normalize_operator(original)

    if normalized not in SUPPORTED_OPERATORS:
        raise OperatorError(
            f"Unsupported comparison operator: '{original}' → normalized as '{normalized}'"
        )
    return SUPPORTED_OPERATORS[normalized]



