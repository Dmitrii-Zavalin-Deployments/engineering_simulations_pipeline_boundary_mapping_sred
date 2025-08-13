# src/override_loader.py

import os
import yaml
from typing import Dict, List

# ✅ Default override config path
OVERRIDE_PATH = os.path.join("configs", "overrides.yaml")

def load_override_config(path: str = OVERRIDE_PATH) -> Dict[str, List[int]]:
    """
    Load face-to-label override mappings from a YAML file.
    Expected format:
      x_min: [101, 102]
      y_max: [203]
      custom_label: [999]
    """
    if not os.path.isfile(path):
        print(f"[OverrideLoader] No override file found at: {path}")
        return {}

    with open(path, "r") as f:
        try:
            data = yaml.safe_load(f)
            return data if isinstance(data, dict) else {}
        except yaml.YAMLError as e:
            print(f"[OverrideLoader] YAML parsing error: {e}")
            return {}

def apply_overrides(boundary_data: Dict[str, List[int]], overrides: Dict[str, List[int]]) -> Dict[str, List[int]]:
    """
    Apply manual overrides to the boundary classification result.
    Overrides take precedence and overwrite existing face assignments.
    """
    updated = boundary_data.copy()

    for label, face_ids in overrides.items():
        if not isinstance(face_ids, list):
            continue
        updated[label] = face_ids

    # ✅ Rebuild apply_faces list based on override keys
    updated["apply_faces"] = sorted(list(overrides.keys()))

    # ✅ Rebuild faces list from all overridden face IDs
    all_ids = set()
    for ids in overrides.values():
        all_ids.update(ids)
    updated["faces"] = sorted(list(all_ids))

    return updated



