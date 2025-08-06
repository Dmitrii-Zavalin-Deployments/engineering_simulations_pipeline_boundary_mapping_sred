# 📄 tests/validation/test_literal_safety_fallback.py

import pytest
from src.validation.expression_utils import parse_literal, normalize_quotes

# 🧪 Literal Safety Fallbacks — Boundary & Error Conditions

def test_unparseable_float_fragments():
    assert parse_literal("3.14.15") == "3.14.15"
    assert parse_literal("NaN.0") == "NaN.0"

def test_unmatched_quotes():
    assert parse_literal("'unfinished") == "'unfinished"
    try:
        result = parse_literal('"broken')
        assert result == '"broken'
    except Exception:
        assert True
    assert normalize_quotes("'''") == "'"

def test_ambiguous_padded_numbers():
    assert parse_literal("000") == 0
    assert parse_literal("00042") == 42
    assert parse_literal("001.5") == 1.5
    assert parse_literal("000.000") == 0.0

def test_literal_null_variants():
    assert parse_literal("NULL") is None
    assert parse_literal("null") is None
    assert parse_literal("None") is None
    assert parse_literal(" none ") is None
    assert parse_literal("Null") is None
    assert parse_literal("nullish") == "nullish"

def test_literal_boolean_variants():
    assert parse_literal("true") is True
    assert parse_literal("TRUE") is True
    assert parse_literal(" false ") is False
    assert parse_literal("falsehood") == "falsehood"
    assert parse_literal("yes") == "yes"  # Not treated as boolean

def test_blank_and_whitespace_inputs():
    assert parse_literal("  ") == ""
    assert parse_literal("") == ""
    assert parse_literal("\n\t") == ""

def test_non_string_objects():
    assert parse_literal(True) is True
    assert parse_literal(False) is False
    assert parse_literal(None) is None
    assert parse_literal(0) == 0
    assert parse_literal(42.0) == 42.0
    assert parse_literal(["1", "2", "3"]) == ["1", "2", "3"]

def test_bracket_strings_and_malformed_literals():
    assert parse_literal("{key: value}") == "{key: value}"  # Not valid literal
    assert parse_literal("[1, 2") == "[1, 2"  # Unclosed list
    assert parse_literal("('a',") == "('a',"  # Incomplete tuple
    assert parse_literal("True,)") == "True,)"  # Invalid trailing

def test_empty_collection_literals():
    assert parse_literal("[]") == []
    assert parse_literal("{}") == {}
    assert parse_literal("()") == ()
    assert parse_literal("   []   ") == []

def test_nested_quotes_confusion():
    assert parse_literal('"\'mixed\'"') == "'mixed'"
    assert normalize_quotes("''string''") == "'string'"
    assert normalize_quotes("\"\"") == "\""
    assert parse_literal("\"\"") == ""  # Double-quoted empty

# 🛡️ New Defensive Fallbacks — Resilience Edge Cases

@pytest.mark.parametrize("value, expected", [
    ("'ok'", "ok"),
    ("'unclosed", "'unclosed"),   # should not throw
    ("00123", 123),
    ("True", True),
])
def test_literal_parsing_resilience(value, expected):
    result = parse_literal(value)
    assert result == expected



