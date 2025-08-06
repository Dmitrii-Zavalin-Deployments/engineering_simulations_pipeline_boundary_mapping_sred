# tests/utils/test_validation_helpers.py

import unittest
from src.utils.validation_helpers import is_valid_numeric_string

class TestIsValidNumericString(unittest.TestCase):

    # ✅ Valid numeric formats
    def test_integer_string(self):
        self.assertTrue(is_valid_numeric_string("42"))

    def test_negative_integer(self):
        self.assertTrue(is_valid_numeric_string("-17"))

    def test_float_string(self):
        self.assertTrue(is_valid_numeric_string("3.14159"))

    def test_negative_float(self):
        self.assertTrue(is_valid_numeric_string("-0.001"))

    def test_float_with_leading_dot(self):
        self.assertTrue(is_valid_numeric_string(".5"))

    def test_float_with_trailing_dot(self):
        self.assertTrue(is_valid_numeric_string("5."))

    def test_scientific_notation(self):
        self.assertTrue(is_valid_numeric_string("6.02e23"))

    def test_spaces_trimmed(self):
        self.assertTrue(is_valid_numeric_string("   123.45   "))

    def test_plus_prefix(self):
        self.assertTrue(is_valid_numeric_string("+88"))

    def test_zero(self):
        self.assertTrue(is_valid_numeric_string("0"))

    def test_bool_true_false(self):
        self.assertTrue(is_valid_numeric_string(True))   # Interprets as 1.0
        self.assertTrue(is_valid_numeric_string(False))  # Interprets as 0.0

    def test_native_int_float(self):
        self.assertTrue(is_valid_numeric_string(100))
        self.assertTrue(is_valid_numeric_string(5.5))

    # 🔬 Special float-like tokens (Python allows them)
    def test_nan_and_inf(self):
        self.assertTrue(is_valid_numeric_string("NaN"))
        self.assertTrue(is_valid_numeric_string("inf"))
        self.assertTrue(is_valid_numeric_string("-inf"))

    # 🚫 Invalid or malformed cases
    def test_alpha_string(self):
        self.assertFalse(is_valid_numeric_string("not_a_number"))

    def test_alphanumeric_mixed(self):
        self.assertFalse(is_valid_numeric_string("123abc"))

    def test_symbol_injection(self):
        self.assertFalse(is_valid_numeric_string("$100.00"))

    def test_thousand_separator(self):
        self.assertFalse(is_valid_numeric_string("1,000"))

    def test_empty_string(self):
        self.assertFalse(is_valid_numeric_string(""))

    def test_none_input(self):
        self.assertFalse(is_valid_numeric_string(None))

    def test_list_input(self):
        self.assertFalse(is_valid_numeric_string([123]))

    def test_dict_input(self):
        self.assertFalse(is_valid_numeric_string({"val": 42}))

    def test_set_input(self):
        self.assertFalse(is_valid_numeric_string({1, 2, 3}))

    def test_tuple_input(self):
        self.assertFalse(is_valid_numeric_string((3.14,)))

    def test_object_input(self):
        class Dummy:
            pass
        self.assertFalse(is_valid_numeric_string(Dummy()))



