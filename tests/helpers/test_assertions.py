# tests/helpers/test_assertions.py

import pytest
from tests.helpers.assertions import assert_error_contains
from tests.helpers.constants import EXPECTED_ERROR_PREFIX

class CustomError(Exception):
    pass

def raise_custom_error(message):
    raise CustomError(message)

def test_error_contains_expected_phrase():
    with pytest.raises(CustomError) as exc:
        raise_custom_error("Missing key in expression: a.b")

    assert_error_contains(exc, "Missing key in expression")

def test_error_contains_exact_word():
    with pytest.raises(CustomError) as exc:
        raise_custom_error("Unsupported operator: ++")

    assert_error_contains(exc, "Unsupported operator")

def test_error_missing_phrase_triggers_failure():
    with pytest.raises(AssertionError) as exc:
        with pytest.raises(CustomError) as raised:
            raise_custom_error("Null value encountered in domain_definition.bbox")

        # This phrase does not exist in the exception string
        assert_error_contains(raised, "Some unrelated error")

    assert EXPECTED_ERROR_PREFIX in str(exc.value)



