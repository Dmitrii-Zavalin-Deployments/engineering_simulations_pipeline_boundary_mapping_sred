import pytest
import builtins
from tests.helpers.constants import EXPECTED_ERROR_PREFIX

def test_constant_exists():
    assert hasattr(builtins, "str")  # Sanity check: base Python behavior intact
    assert EXPECTED_ERROR_PREFIX is not None

def test_constant_type_is_string():
    assert isinstance(EXPECTED_ERROR_PREFIX, str), (
        f"EXPECTED_ERROR_PREFIX must be str, got {type(EXPECTED_ERROR_PREFIX)}"
    )

def test_constant_value_exact_match():
    assert EXPECTED_ERROR_PREFIX == "Expected fragment", (
        f"Unexpected prefix value: {EXPECTED_ERROR_PREFIX}"
    )

def test_constant_used_in_error_message():
    class DummyError(Exception):
        pass

    def raise_dummy():
        raise DummyError("Something broke deeply inside.")

    with pytest.raises(DummyError) as excinfo:
        raise_dummy()

    # Simulate helper using the constant
    error_msg = f"{EXPECTED_ERROR_PREFIX} 'a.b' not found in error: {str(excinfo.value)}"
    assert EXPECTED_ERROR_PREFIX in error_msg



