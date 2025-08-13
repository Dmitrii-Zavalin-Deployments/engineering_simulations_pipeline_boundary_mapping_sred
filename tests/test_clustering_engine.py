# tests/test_clustering_engine.py

import unittest
from src.clustering_engine import cluster_faces

class TestClusteringEngine(unittest.TestCase):
    def setUp(self):
        # ✅ Create mock faces with normals pointing in distinct directions
        self.mock_faces = [
            {"id": 1, "vertices": [[0, 0, 0], [1, 0, 0], [0, 1, 0]]},  # Z+
            {"id": 2, "vertices": [[0, 0, 0], [0, 1, 0], [0, 0, 1]]},  # X+
            {"id": 3, "vertices": [[0, 0, 0], [0, 0, 1], [1, 0, 0]]},  # Y+
            {"id": 4, "vertices": [[0, 0, 0], [-1, 0, 0], [0, -1, 0]]},  # Z-
            {"id": 5, "vertices": [[0, 0, 0], [0, -1, 0], [0, 0, -1]]},  # X-
            {"id": 6, "vertices": [[0, 0, 0], [0, 0, -1], [-1, 0, 0]]},  # Y-
        ]

    def test_cluster_faces_output_structure(self):
        clusters = cluster_faces(self.mock_faces, n_clusters=3)

        # ✅ Output should be a dictionary of cluster labels
        self.assertIsInstance(clusters, dict)
        for key, face_ids in clusters.items():
            self.assertTrue(key.startswith("cluster_"))
            self.assertIsInstance(face_ids, list)
            for fid in face_ids:
                self.assertIsInstance(fid, int)

    def test_cluster_faces_grouping_behavior(self):
        clusters = cluster_faces(self.mock_faces, n_clusters=3)

        # ✅ Total face count should match input
        total_faces = sum(len(v) for v in clusters.values())
        self.assertEqual(total_faces, len(self.mock_faces))

    def test_cluster_faces_empty_input(self):
        clusters = cluster_faces([], n_clusters=3)

        # ✅ Should return empty dict
        self.assertEqual(clusters, {})

    def test_cluster_faces_insufficient_vertices(self):
        malformed_faces = [
            {"id": 7, "vertices": [[0, 0, 0]]},  # Only one vertex
            {"id": 8, "vertices": []},          # No vertices
        ]
        clusters = cluster_faces(malformed_faces, n_clusters=2)

        # ✅ Should return empty dict due to invalid geometry
        self.assertEqual(clusters, {})

    def test_cluster_faces_consistency(self):
        # ✅ Run clustering twice and check deterministic behavior
        clusters1 = cluster_faces(self.mock_faces, n_clusters=3)
        clusters2 = cluster_faces(self.mock_faces, n_clusters=3)

        self.assertEqual(clusters1.keys(), clusters2.keys())
        self.assertEqual(
            sorted([sorted(v) for v in clusters1.values()]),
            sorted([sorted(v) for v in clusters2.values()])
        )

if __name__ == "__main__":
    unittest.main()



