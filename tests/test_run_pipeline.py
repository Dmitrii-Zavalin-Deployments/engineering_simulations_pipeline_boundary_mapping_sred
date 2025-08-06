# tests/test_run_pipeline.py

import json
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
from src.run_pipeline import sanitize_payload, main, DEFAULT_RESOLUTION
from src.utils.coercion import coerce_numeric


class TestSanitizePayload(unittest.TestCase):
    def test_complete_domain(self):
        raw = {"domain_definition": {"x": "1", "y": "2", "z": "3", "width": "4", "height": "5", "depth": "6"}}
        expected = {
            "domain_definition": {
                "x": 1.0, "y": 2.0, "z": 3.0,
                "width": 4.0, "height": 5.0, "depth": 6.0,
                "min_x": 1.0, "max_x": 5.0,
                "min_y": 2.0, "max_y": 7.0,
                "min_z": 3.0, "max_z": 9.0
            }
        }
        result = sanitize_payload(raw)
        self.assertEqual(result, expected)

    def test_missing_fields(self):
        raw = {"domain_definition": {"x": "1"}}
        result = sanitize_payload(raw)
        domain = result["domain_definition"]
        self.assertEqual(domain["x"], 1.0)
        self.assertEqual(domain["y"], 0.0)
        self.assertEqual(domain["z"], 0.0)
        self.assertEqual(domain["width"], 0.0)
        self.assertEqual(domain["height"], 0.0)
        self.assertEqual(domain["depth"], 0.0)
        self.assertEqual(domain["min_x"], 1.0)
        self.assertEqual(domain["max_x"], 1.0)
        self.assertEqual(domain["min_y"], 0.0)
        self.assertEqual(domain["max_y"], 0.0)
        self.assertEqual(domain["min_z"], 0.0)
        self.assertEqual(domain["max_z"], 0.0)

    def test_empty_metadata(self):
        result = sanitize_payload({})
        domain = result["domain_definition"]
        self.assertEqual(domain["x"], 0.0)
        self.assertEqual(domain["y"], 0.0)
        self.assertEqual(domain["z"], 0.0)
        self.assertEqual(domain["width"], 0.0)
        self.assertEqual(domain["height"], 0.0)
        self.assertEqual(domain["depth"], 0.0)
        self.assertEqual(domain["min_x"], 0.0)
        self.assertEqual(domain["max_x"], 0.0)
        self.assertEqual(domain["min_y"], 0.0)
        self.assertEqual(domain["max_y"], 0.0)
        self.assertEqual(domain["min_z"], 0.0)
        self.assertEqual(domain["max_z"], 0.0)

    def test_width_clamping_on_misaligned_bounds(self):
        raw = {"domain_definition": {"min_x": "1.0", "max_x": "0.0"}}
        result = sanitize_payload(raw)
        domain = result["domain_definition"]
        self.assertEqual(domain["width"], 0.0)
        self.assertEqual(domain["min_x"], 1.0)
        self.assertEqual(domain["max_x"], 1.0)

    def test_fallback_on_invalid_width(self):
        raw = {"domain_definition": {"x": "1", "max_x": "5", "width": "invalid"}}
        result = sanitize_payload(raw)
        width = result["domain_definition"]["width"]
        self.assertEqual(width, 4.0)
        self.assertEqual(result["domain_definition"]["min_x"], 1.0)
        self.assertEqual(result["domain_definition"]["max_x"], 5.0)

    @patch("src.run_pipeline.coerce_numeric", side_effect=lambda val: None if val is None or val == "invalid" else float(val))
    def test_mocked_coercion_fallback(self, mock_coerce):
        raw = {
            "domain_definition": {
                "x": "1", "y": "0", "z": "0",
                "width": "invalid", "max_x": "5",
                "height": "0", "depth": "0"
            }
        }
        result = sanitize_payload(raw)
        domain = result["domain_definition"]
        self.assertEqual(domain["width"], 4.0)
        self.assertEqual(domain["min_x"], 1.0)
        self.assertEqual(domain["max_x"], 5.0)
        mock_coerce.assert_any_call("invalid")


class TestPipelineMain(unittest.TestCase):
    def test_pipeline_output_is_valid(self):
        output_path = Path("data/testing-input-output/enriched_metadata.json")
        assert output_path.exists(), "Pipeline output file missing"

        with output_path.open() as f:
            metadata = json.load(f)

        required_keys = ["min_x", "max_x", "min_y", "max_y", "min_z", "max_z"]
        for key in required_keys:
            assert key in metadata.get("domain_definition", {}), f"Missing {key} in output"

    @patch("src.run_pipeline.sys.exit", side_effect=SystemExit)
    @patch("pathlib.Path.exists", return_value=False)
    @patch("src.run_pipeline.log_error")
    def test_main_input_directory_missing(self, mock_log_error, mock_exists, mock_exit):
        with self.assertRaises(SystemExit):
            main(resolution=DEFAULT_RESOLUTION)
        mock_log_error.assert_called()
        mock_exit.assert_called_once_with(1)
        args, kwargs = mock_log_error.call_args
        self.assertIn("Input directory not found", args[0])
        self.assertTrue(kwargs.get("fatal"))

    def test_safe_list_indexing_guard(self):
        result_list = ["alpha", "beta", "gamma"]
        index = 1
        self.assertEqual(result_list[index], "beta")


