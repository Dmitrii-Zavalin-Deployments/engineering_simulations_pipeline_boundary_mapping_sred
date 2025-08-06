# ✅ tests/validation/test_expression_utils.py

import pytest
from validation.expression_utils import parse_literal


# 🔢 Numeric Types
def test_integer_literals():
    assert parse_literal("42") == 42
    assert parse_literal("-17") == -17
    assert parse_literal("0") == 0
    assert parse_literal("00123") == 123  # Leading zeros
    assert parse_literal("  99  ") == 99

def test_float_literals():
    assert parse_literal("3.14") == 3.14
    assert parse_literal("-0.001") == -0.001
    assert parse_literal("2.") == 2.0
    assert parse_literal(".5") == 0.5
    assert parse_literal("  0.0  ") == 0.0


# 🧵 String Conversion
def test_quoted_string_literals():
    assert parse_literal("'hello'") == "hello"
    assert parse_literal('"world"') == "world"
    assert parse_literal("'42'") == "42"
    assert parse_literal('"false"') == "false"
    assert parse_literal(" ' spaced ' ") == " spaced "
    assert parse_literal("''") == ""  # Empty quoted string
    assert parse_literal('" "') == " "  # Space inside quotes

def test_unquoted_string_literals():
    assert parse_literal("unquoted") == "unquoted"
    assert parse_literal("hello world") == "hello world"
    assert parse_literal("TRUEish") == "TRUEish"


# ✅ Boolean Types
def test_boolean_literals():
    assert parse_literal("true") is True
    assert parse_literal("TRUE") is True
    assert parse_literal("false") is False
    assert parse_literal("False") is False
    assert parse_literal("  true ") is True


# 🚫 Null Values
def test_null_literals():
    assert parse_literal("null") is None
    assert parse_literal("None") is None
    assert parse_literal("  null ") is None
    assert parse_literal("NULL") is None


# 🧼 Already Parsed Inputs
def test_non_string_inputs():
    assert parse_literal(10) == 10
    assert parse_literal(True) is True
    assert parse_literal(None) is None
    assert parse_literal(3.5) == 3.5


# 🤔 Fallbacks & Edge Cases
def test_fallback_behavior():
    assert parse_literal("not_a_literal") == "not_a_literal"
    assert parse_literal("  ") == ""  # Empty string after strip
    assert parse_literal("") == ""  # Fully empty
    assert parse_literal("3.14.15") == "3.14.15"  # Invalid float
    assert parse_literal("'broken") == "'broken"  # Unmatched single quote
    assert parse_literal('"unfinished') == '"unfinished'  # Unmatched double quote



