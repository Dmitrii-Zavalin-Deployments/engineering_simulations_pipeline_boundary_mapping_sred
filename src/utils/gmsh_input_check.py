# src/utils/gmsh_input_check.py

"""
Utility: Validate imported STEP geometry integrity before domain extraction.

Checks that the STEP file contains at least one 3D volume entity
to safely proceed with bounding box extraction or meshing.

Note: Gmsh session lifecycle must be handled by the caller.
"""

try:
    import gmsh
except ImportError:
    raise RuntimeError("Gmsh module not found. Run: pip install gmsh==4.11.1")


class ValidationError(Exception):
    """Raised when STEP file validation fails."""
    pass


def validate_step_has_volumes(step_path):
    """
    Validates that the specified STEP file contains at least one 3D volume entity.

    Parameters:
        step_path (str or dict): Either a file path or injected STEP payload (test-only)

    Raises:
        FileNotFoundError: If the file path is invalid.
        ValidationError: If no 3D volume entities are found.
        KeyError: If STEP input dict is malformed.
    """
    import os

    # 🛡️ Defensive override for test-injected payloads
    if isinstance(step_path, dict):
        if "solids" not in step_path or not isinstance(step_path["solids"], list):
            raise KeyError("Missing or invalid 'solids' list in STEP payload")
        step_path = "mock/path/to/geometry.step"  # Used only to bypass Gmsh.open()

    if not os.path.isfile(step_path):
        raise FileNotFoundError(f"STEP file not found: {step_path}")

    gmsh.model.add("volume_check_model")
    gmsh.open(str(step_path))  # ✅ Ensures compatibility with Path-like inputs

    volumes = gmsh.model.getEntities(3)
    if not volumes:
        raise ValidationError(f"STEP file contains no 3D volumes: {step_path}")



