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
    Overrides are merged with existing assignments and conflicts are logged.
    """
    updated = boundary_data.copy()
    valid_labels = {"x_min", "x_max", "y_min", "y_max", "z_min", "z_max"}

    for label, face_ids in overrides.items():
        if not isinstance(face_ids, list):
            print(f"[OverrideLoader] Skipping invalid override for '{label}' — not a list")
            continue

        if label not in valid_labels:
            print(f"[OverrideLoader] Warning: '{label}' is not a recognized boundary label")

        existing_ids = set(updated.get(label, []))
        override_ids = set(face_ids)

        # ✅ Log shadowed assignments
        shadowed = existing_ids.intersection(override_ids)
        if shadowed:
            print(f"[OverrideLoader] Shadowed faces in '{label}': {sorted(list(shadowed))}")

        # ✅ Merge strategy: union of existing and override
        merged_ids = sorted(list(existing_ids.union(override_ids)))
        updated[label] = merged_ids

    # ✅ Rebuild apply_faces list based on all non-empty labels
    updated["apply_faces"] = sorted([label for label, ids in updated.items() if isinstance(ids, list) and ids])

    # ✅ Rebuild faces list from all assigned face IDs
    all_ids = set()
    for key, ids in updated.items():
        if isinstance(ids, list):
            all_ids.update(ids)
    updated["faces"] = sorted(list(all_ids))

    return updated



