# tests/test_bbox_classifier.py

import unittest
from src.bbox_classifier import classify_faces

class TestBBoxClassifier(unittest.TestCase):
    def test_classify_faces_basic(self):
        faces = [
            {"id": 1, "vertices": [[0, 0, 0], [1, 0, 0], [0, 1, 0]]},  # Z+
            {"id": 2, "vertices": [[0, 0, 0], [0, 1, 0], [0, 0, 1]]},  # X+
            {"id": 3, "vertices": [[0, 0, 0], [0, 0, 1], [1, 0, 0]]},  # Y+
        ]
        result = classify_faces(faces)
        bc = result["boundary_conditions"]

        self.assertIn(1, bc["z_max"])
        self.assertIn(2, bc["x_max"])
        self.assertIn(3, bc["y_max"])

    def test_unknown_direction(self):
        faces = [
            {"id": 4, "vertices": [[0, 0, 0], [1, 1, 0], [0, 1, 1]]},  # Diagonal
        ]
        result = classify_faces(faces)
        bc = result["boundary_conditions"]
        self.assertNotIn(4, bc["x_max"])
        self.assertNotIn(4, bc["y_max"])
        self.assertNotIn(4, bc["z_max"])

    def test_face_with_insufficient_vertices(self):
        faces = [
            {"id": 5, "vertices": []},  # Malformed face
            {"id": 6, "vertices": [[0, 0, 0]]},  # Only one vertex
            {"id": 7, "vertices": [[0, 0, 0], [1, 0, 0]]}  # Only two vertices
        ]
        result = classify_faces(faces)
        bc = result["boundary_conditions"]

        # Ensure all malformed faces are tracked and do not crash
        self.assertIn(5, bc["faces"])
        self.assertIn(6, bc["faces"])
        self.assertIn(7, bc["faces"])

if __name__ == "__main__":
    unittest.main()



