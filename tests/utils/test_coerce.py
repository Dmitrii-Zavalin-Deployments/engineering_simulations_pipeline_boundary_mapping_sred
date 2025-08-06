# tests/utils/test_coerce.py

import unittest
from src.utils.coercion import coerce_numeric, relaxed_equals


class TestCoerceNumeric(unittest.TestCase):

    def test_valid_float_string(self):
        self.assertEqual(coerce_numeric("3.14"), 3.14)

    def test_valid_integer_string(self):
        self.assertEqual(coerce_numeric("42"), 42.0)

    def test_negative_float_string(self):
        self.assertEqual(coerce_numeric("-2.5"), -2.5)

    def test_negative_integer_string(self):
        self.assertEqual(coerce_numeric("-10"), -10.0)

    def test_string_with_spaces(self):
        self.assertEqual(coerce_numeric("  7.0  "), 7.0)

    def test_leading_zeros(self):
        self.assertEqual(coerce_numeric("000123"), 123.0)

    def test_non_numeric_string(self):
        self.assertIsNone(coerce_numeric("not_a_number"))

    def test_empty_string(self):
        self.assertIsNone(coerce_numeric(""))

    def test_none_input(self):
        self.assertIsNone(coerce_numeric(None))

    def test_boolean_true(self):
        self.assertEqual(coerce_numeric(True), 1.0)

    def test_boolean_false(self):
        self.assertEqual(coerce_numeric(False), 0.0)

    def test_float_input(self):
        self.assertEqual(coerce_numeric(8.9), 8.9)

    def test_int_input(self):
        self.assertEqual(coerce_numeric(100), 100.0)

    def test_list_input(self):
        self.assertIsNone(coerce_numeric([1, 2]))

    def test_dict_input(self):
        self.assertIsNone(coerce_numeric({"x": 5}))

    def test_numeric_string_with_suffix(self):
        self.assertIsNone(coerce_numeric("10kg"))

    def test_scientific_notation(self):
        self.assertEqual(coerce_numeric("1e3"), 1000.0)

    def test_overflow_value(self):
        try:
            val = coerce_numeric("1e5000")
            self.assertIsNone(val)
        except Exception as e:
            self.fail(f"Overflow raised unexpected error: {e}")

    def test_infinity_string(self):
        self.assertIsNone(coerce_numeric("inf"))

    def test_negative_infinity_string(self):
        self.assertIsNone(coerce_numeric("-inf"))

    def test_nan_string(self):
        result = coerce_numeric("NaN")
        self.assertIsNone(result)  # ✅ Clarified fallback assertion

    def test_relaxed_equals_nan_behavior(self):
        self.assertFalse(relaxed_equals("not_a_number", 0))
        self.assertFalse(relaxed_equals("NaN", 42))
        self.assertTrue(relaxed_equals("false", False))
        self.assertFalse(relaxed_equals("false", True))



