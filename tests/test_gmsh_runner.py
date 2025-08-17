# tests/test_gmsh_runner.py

import unittest
import tempfile
import json
import os
from unittest.mock import patch, MagicMock

from src.gmsh_runner import extract_boundary_conditions_from_step


class TestGmshRunner(unittest.TestCase):

    def setUp(self):
        # Create a mock STEP file
        self.mock_step_path = tempfile.NamedTemporaryFile(suffix=".step", delete=False).name
        with open(self.mock_step_path, "w") as f:
            f.write("mock STEP content")

        # Create a mock flow_data.json
        self.mock_flow_data_path = "data/testing-input-output/flow_data.json"
        os.makedirs(os.path.dirname(self.mock_flow_data_path), exist_ok=True)
        with open(self.mock_flow_data_path, "w") as f:
            json.dump({
                "initial_conditions": {
                    "initial_velocity": [0.602695, -0.122614, 13.4851],
                    "initial_pressure": 146.221
                }
            }, f)

    def tearDown(self):
        os.remove(self.mock_step_path)
        if os.path.exists(self.mock_flow_data_path):
            os.remove(self.mock_flow_data_path)

    @patch("src.gmsh_runner.gmsh")
    @patch("src.gmsh_runner.validate_step_has_volumes")
    @patch("src.gmsh_runner.classify_faces")
    @patch("src.gmsh_runner.generate_boundary_block")
    def test_inlet_injection_logic(
        self, mock_generate_boundary_block, mock_classify_faces,
        mock_validate_step_has_volumes, mock_gmsh
    ):
        # Mock Gmsh behavior
        mock_gmsh.model.getEntities.side_effect = lambda dim: [(dim, 1)] if dim == 3 else [(dim, 2)]
        mock_gmsh.model.getBoundingBox.return_value = (0, 0, 0, 1, 1, 1)
        mock_gmsh.model.mesh.getNodes.return_value = ([], [0.0]*9)

        # Mock classification and boundary block
        mock_classify_faces.return_value = {"x_min": [1], "x_max": [2]}
        mock_generate_boundary_block.return_value = {
            "x_min": "inlet",
            "x_max": "outlet",
            "y_min": "wall",
            "y_max": "wall",
            "z_min": "wall",
            "z_max": "wall",
            "faces": [1, 2, 3, 4],
            "type": "dirichlet"
        }

        result = extract_boundary_conditions_from_step(self.mock_step_path)

        self.assertIn("apply_faces", result)
        self.assertIn("apply_to", result)
        self.assertIn("velocity", result)
        self.assertIn("pressure", result)
        self.assertEqual(result["apply_faces"], ["x_min"])
        self.assertEqual(result["apply_to"], ["velocity", "pressure"])
        self.assertEqual(result["velocity"], [0.602695, -0.122614, 13.4851])
        self.assertEqual(result["pressure"], 146.221)
        self.assertTrue(result["no_slip"])

    @patch("src.gmsh_runner.gmsh")
    @patch("src.gmsh_runner.validate_step_has_volumes")
    @patch("src.gmsh_runner.classify_faces")
    @patch("src.gmsh_runner.generate_boundary_block")
    def test_missing_flow_data_graceful_handling(
        self, mock_generate_boundary_block, mock_classify_faces,
        mock_validate_step_has_volumes, mock_gmsh
    ):
        # Remove flow_data.json
        if os.path.exists(self.mock_flow_data_path):
            os.remove(self.mock_flow_data_path)

        mock_gmsh.model.getEntities.side_effect = lambda dim: [(dim, 1)] if dim == 3 else [(dim, 2)]
        mock_gmsh.model.getBoundingBox.return_value = (0, 0, 0, 1, 1, 1)
        mock_gmsh.model.mesh.getNodes.return_value = ([], [0.0]*9)

        mock_classify_faces.return_value = {"x_min": [1], "x_max": [2]}
        mock_generate_boundary_block.return_value = {
            "x_min": "inlet",
            "x_max": "outlet",
            "y_min": "wall",
            "y_max": "wall",
            "z_min": "wall",
            "z_max": "wall",
            "faces": [1, 2, 3, 4],
            "type": "dirichlet"
        }

        result = extract_boundary_conditions_from_step(self.mock_step_path)

        self.assertNotIn("velocity", result)
        self.assertNotIn("pressure", result)
        self.assertNotIn("apply_faces", result)
        self.assertNotIn("apply_to", result)
        self.assertNotIn("no_slip", result)


if __name__ == "__main__":
    unittest.main()



