# tests/test_schema_writer.py

import unittest
import tempfile
import os
import json
import pytest
import jsonschema
from src.schema_writer import generate_boundary_block, validate_boundary_conditions, write_boundary_json

class TestSchemaWriter(unittest.TestCase):
    def setUp(self):
        # Minimal valid input from classifier
        self.valid_classified = {
            "boundary_conditions": {
                "x_min": "inlet",
                "x_max": "outlet",
                "y_min": "wall",
                "y_max": "wall",
                "z_min": "wall",
                "z_max": "wall",
                "faces": [1, 2, 3],
                "apply_faces": ["x_min", "x_max", "y_min", "y_max", "z_min", "z_max"]
            }
        }

    def test_generate_boundary_block_valid(self):
        block = generate_boundary_block(self.valid_classified)

        # ✅ Check required fields exist
        self.assertIn("x_min", block)
        self.assertIn("faces", block)
        self.assertIn("apply_faces", block)
        self.assertEqual(block["type"], "dirichlet")
        self.assertEqual(block["no_slip"], True)

        # ✅ Validate against schema
        self.assertTrue(validate_boundary_conditions(block))

    def test_missing_faces_field(self):
        malformed = {
            "boundary_conditions": {
                "x_min": "inlet",
                "x_max": "outlet",
                "apply_faces": ["x_min", "x_max"]
                # ❌ Missing "faces"
            }
        }
        block = generate_boundary_block(malformed)
        with pytest.raises(jsonschema.ValidationError):
            validate_boundary_conditions(block)

    def test_missing_apply_faces_field(self):
        malformed = {
            "boundary_conditions": {
                "x_min": "inlet",
                "x_max": "outlet",
                "faces": [1, 2]
                # ❌ Missing "apply_faces"
            }
        }
        block = generate_boundary_block(malformed)
        with pytest.raises(jsonschema.ValidationError):
            validate_boundary_conditions(block)

    def test_write_boundary_json(self):
        block = generate_boundary_block(self.valid_classified)

        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "boundary_output.json")
            write_boundary_json(path, block)

            # ✅ File should exist and contain valid JSON
            self.assertTrue(os.path.isfile(path))
            with open(path, "r") as f:
                data = json.load(f)
                self.assertEqual(data["type"], "dirichlet")
                self.assertEqual(data["no_slip"], True)

    def test_schema_enforcement_on_invalid_type(self):
        invalid_block = generate_boundary_block(self.valid_classified)
        invalid_block["type"] = "unsupported_type"  # ❌ Not allowed by schema

        with pytest.raises(jsonschema.ValidationError):
            validate_boundary_conditions(invalid_block)

if __name__ == "__main__":
    unittest.main()



