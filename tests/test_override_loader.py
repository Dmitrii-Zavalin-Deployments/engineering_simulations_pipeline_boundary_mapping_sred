# tests/test_override_loader.py

import unittest
from src.override_loader import apply_overrides

class TestOverrideLoader(unittest.TestCase):
    def setUp(self):
        # ✅ Simulated classifier output
        self.classified = {
            "x_min": [101],
            "x_max": [102],
            "y_min": [103],
            "y_max": [104],
            "z_min": [105],
            "z_max": [106],
            "faces": [101, 102, 103, 104, 105, 106],
            "apply_faces": ["x_min", "x_max", "y_min", "y_max", "z_min", "z_max"]
        }

    def test_apply_valid_overrides(self):
        overrides = {
            "x_min": [201, 202],
            "y_max": [203]
        }

        updated = apply_overrides(self.classified, overrides)

        # ✅ Overrides should replace original values
        self.assertEqual(updated["x_min"], [201, 202])
        self.assertEqual(updated["y_max"], [203])

        # ✅ apply_faces should reflect override keys
        self.assertEqual(sorted(updated["apply_faces"]), ["x_min", "y_max"])

        # ✅ faces should include all overridden IDs
        self.assertEqual(sorted(updated["faces"]), [201, 202, 203])

    def test_override_with_empty_dict(self):
        overrides = {}
        updated = apply_overrides(self.classified, overrides)

        # ✅ Should retain original values
        self.assertEqual(updated["x_min"], [101])
        self.assertEqual(updated["faces"], [101, 102, 103, 104, 105, 106])
        self.assertEqual(sorted(updated["apply_faces"]), ["x_min", "x_max", "y_min", "y_max", "z_min", "z_max"])

    def test_override_with_non_list_values(self):
        overrides = {
            "x_min": "invalid",
            "y_max": None,
            "z_max": 999
        }

        updated = apply_overrides(self.classified, overrides)

        # ✅ Should ignore non-list overrides
        self.assertEqual(updated["x_min"], [101])
        self.assertEqual(updated["y_max"], [104])
        self.assertEqual(updated["z_max"], [106])

        # ✅ apply_faces and faces should remain unchanged
        self.assertEqual(sorted(updated["apply_faces"]), ["x_min", "x_max", "y_min", "y_max", "z_min", "z_max"])
        self.assertEqual(sorted(updated["faces"]), [101, 102, 103, 104, 105, 106])

    def test_override_with_new_labels(self):
        overrides = {
            "custom_wall": [301, 302],
            "symmetry_plane": [303]
        }

        updated = apply_overrides(self.classified, overrides)

        # ✅ New labels should be added
        self.assertEqual(updated["custom_wall"], [301, 302])
        self.assertEqual(updated["symmetry_plane"], [303])

        # ✅ apply_faces should include new labels
        self.assertIn("custom_wall", updated["apply_faces"])
        self.assertIn("symmetry_plane", updated["apply_faces"])

        # ✅ faces should include all new IDs
        self.assertIn(301, updated["faces"])
        self.assertIn(303, updated["faces"])

if __name__ == "__main__":
    unittest.main()



