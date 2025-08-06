# 📄 src/utils/input_validation.py

import os
import yaml
from pathlib import Path
from typing import Union

__all__ = ["validate_step_file", "load_resolution_profile"]

# 🧩 Patch-safe alias (optional, for test access robustness)
_validate_step_file_internal = None  # Will be assigned after definition

def validate_step_file(path: Union[str, bytes, os.PathLike]) -> bool:
    """
    Validates the existence and type of a STEP file path input.

    Args:
        path (Union[str, bytes, os.PathLike]): The file path to validate.

    Returns:
        bool: True if the STEP file exists and path is valid.

    Raises:
        TypeError: If the input is not a valid path-like type.
        FileNotFoundError: If the path does not exist or is not a file.

    Example:
        >>> validate_step_file("geometry/part.step")
        True
    """
    if not isinstance(path, (str, bytes, os.PathLike)) or not path:
        raise TypeError(
            f"Expected STEP file path as str, bytes, or os.PathLike; got {type(path).__name__}"
        )

    if not os.path.isfile(path):
        raise FileNotFoundError(f"STEP file not found: {path}")

    return True

# 🔗 Patch-safe alias (used only for deep test injection, not public API)
_validate_step_file_internal = validate_step_file


def load_resolution_profile(path: Union[str, Path, None] = None) -> dict:
    """
    Loads resolution configuration from a YAML file.

    Args:
        path (Union[str, Path, None]): Optional override for profile path.

    Returns:
        dict: Parsed resolution profile dictionary.

    Raises:
        FileNotFoundError: If the YAML file does not exist.
        yaml.YAMLError: If the file is not a valid YAML document.

    Example:
        >>> res = load_resolution_profile()
        >>> res["default_resolution"]["dx"]
        0.1
    """
    default_path = Path(path or "configs/validation/resolution_profile.yaml")

    if not default_path.is_file():
        raise FileNotFoundError(f"Missing resolution profile: {default_path}")

    try:
        with default_path.open("r") as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in resolution profile: {e}")



