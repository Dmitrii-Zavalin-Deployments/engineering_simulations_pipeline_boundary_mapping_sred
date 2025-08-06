# tests/integration/test_gmsh_version.py

import re
import pytest
from unittest.mock import patch
import gmsh

EXPECTED_VERSION = "4.11.1"


def get_installed_gmsh_version():
    """Extracts the installed gmsh version string."""
    try:
        version_str = gmsh.__version__ if hasattr(gmsh, "__version__") else gmsh.__file__
        match = re.search(r"\d+\.\d+\.\d+", version_str)
        if match:
            return match.group(0)
    except Exception:
        pass
    return None


def test_gmsh_version_exact_match():
    """Test that the installed gmsh version matches the expected pinned version."""
    version = get_installed_gmsh_version()
    assert version is not None, "Unable to determine Gmsh version"
    assert version == EXPECTED_VERSION, f"Gmsh version mismatch: found {version}, expected {EXPECTED_VERSION}"



