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


def validate_step_has_volumes(step_path):
    """
    Checks if a STEP file contains at least one 3D volume.

    Args:
        step_path (str or dict): Either a file path or injected STEP payload (test-only)

    Raises:
        FileNotFoundError: If the file path is invalid.
        KeyError: If STEP input dict is malformed.
    """
    import os

    if isinstance(step_path, dict):
        if "solids" not in step_path or not isinstance(step_path["solids"], list):
            raise KeyError("Missing or invalid 'solids' list in STEP payload")
        step_path = "mock/path/to/geometry.step"

    if not os.path.isfile(step_path):
        raise FileNotFoundError(f"STEP file not found: {step_path}")

    gmsh.model.add("volume_check_model")
    gmsh.open(str(step_path))

    volumes = gmsh.model.getEntities(3)
    if not volumes:
        raise ValidationError(f"STEP file contains no 3D volumes: {step_path}")


def log_surface_deviation(surface_tag, deviation_ratio, x_coords=None, anchor=None, debug=False):
    """
    Logs diagnostic info for borderline surface alignment cases.

    Args:
        surface_tag (int): GMSH surface ID
        deviation_ratio (float): Ratio of nodes aligned to anchor
        x_coords (list or np.ndarray): Optional list of X-coordinates for spread analysis
        anchor (float): Optional anchor value (e.g., X_min or X_max)
        debug (bool): If True, prints detailed diagnostics
    """
    status = "BORDERLINE MATCH"
    print(f"[DIAG] Surface {surface_tag}: {status} ({deviation_ratio:.2f} aligned)")

    if x_coords is not None and anchor is not None:
        import numpy as np
        x_coords = np.array(x_coords)
        deviations = np.abs(x_coords - anchor)
        max_dev = np.max(deviations)
        mean_dev = np.mean(deviations)
        print(f"[DIAG] Surface {surface_tag}: Node deviation from anchor → max={max_dev:.6f}, mean={mean_dev:.6f}")

    if debug:
        print(f"[DEBUG_DIAG] Surface {surface_tag}: Full X-coord spread → {x_coords.tolist() if hasattr(x_coords, 'tolist') else x_coords}")



