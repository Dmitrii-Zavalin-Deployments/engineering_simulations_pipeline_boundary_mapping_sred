# tests/test_bbox_classifier.py

import unittest
import numpy as np
from unittest.mock import patch

from src.bbox_classifier import (
    compute_face_normal,
    angle_between,
    classify_face_direction,
    classify_faces
)


class TestBBoxClassifier(unittest.TestCase):

    def test_compute_face_normal_valid(self):
        vertices = [
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0]
        ]
        normal = compute_face_normal(vertices)
        expected = np.array([0.0, 0.0, 1.0])
        np.testing.assert_array_almost_equal(normal, expected)

    def test_compute_face_normal_insufficient_vertices(self):
        vertices = [[0.0, 0.0, 0.0]]
        normal = compute_face_normal(vertices)
        np.testing.assert_array_equal(normal, np.zeros(3))

    def test_angle_between_vectors(self):
        v1 = np.array([1, 0, 0])
        v2 = np.array([0, 1, 0])
        angle = angle_between(v1, v2)
        self.assertAlmostEqual(angle, 90.0, places=2)

    @patch("src.bbox_classifier.CONFIG", {
        "fallback_boundary_type": "wall"
    })
    def test_classify_face_direction_x_min(self):
        normal = -np.array([1, 0, 0])
        thresholds = {"x": 0.95, "y": 0.95, "z": 0.95}
        label = classify_face_direction(normal, thresholds)
        self.assertEqual(label, "x_min")

    @patch("src.bbox_classifier.CONFIG", {
        "fallback_boundary_type": "wall"
    })
    def test_classify_face_direction_fallback(self):
        normal = np.array([0.5, 0.5, 0.5])
        thresholds = {"x": 0.95, "y": 0.95, "z": 0.95}
        label = classify_face_direction(normal, thresholds)
        self.assertEqual(label, "wall")

    @patch("src.bbox_classifier.CONFIG", {
        "directional_thresholds": {"x": 0.95, "y": 0.95, "z": 0.95},
        "default_boundary_map": {
            "x_min": "inlet",
            "x_max": "outlet",
            "y_min": "wall",
            "y_max": "wall",
            "z_min": "wall",
            "z_max": "wall"
        },
        "allow_multiple_faces_per_direction": True,
        "log_classification_details": False,
        "enable_fallback_clustering": False,
        "fallback_boundary_type": "wall"
    })
    def test_classify_faces_basic(self):
        faces = [
            {"id": 1, "vertices": [[0, 0, 0], [1, 0, 0], [0, 1, 0]]},  # z+
            {"id": 2, "vertices": [[0, 0, 0], [0, 1, 0], [0, 0, 1]]}   # x+
        ]
        result = classify_faces(faces)
        self.assertIn("boundary_conditions", result)
        bc = result["boundary_conditions"]
        self.assertIn("apply_faces", bc)
        self.assertIn("faces", bc)
        self.assertIn("x_max", bc)
        self.assertIn("z_max", bc)
        self.assertEqual(sorted(bc["faces"]), [1, 2])
        self.assertIn("x_max", bc["apply_faces"])
        self.assertIn("z_max", bc["apply_faces"])


if __name__ == "__main__":
    unittest.main()


