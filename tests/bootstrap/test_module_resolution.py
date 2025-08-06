# tests/bootstrap/test_module_resolution.py

"""🔍 Bootstrap sanity checks for sys.path module resolution."""

import importlib
import importlib.util
import time
import pytest

CRITICAL_MODULES = [
    "pipeline.metadata_enrichment",
    "utils.gmsh_input_check",
    "validation.expression_utils"
]

@pytest.mark.parametrize("module_path", CRITICAL_MODULES)
def test_individual_importability(module_path):
    """✅ Each critical module must be importable without error."""
    try:
        mod = importlib.import_module(module_path)
        assert mod is not None, f"{module_path} resolved to None"
    except ModuleNotFoundError as e:
        pytest.fail(f"{module_path} failed to import: {e}")
    except Exception as e:
        pytest.fail(f"Unexpected error importing {module_path}: {e}")

def test_bulk_import_under_time_limit():
    """⏱️ All modules should import together in <0.5 seconds."""
    start = time.time()
    for path in CRITICAL_MODULES:
        importlib.import_module(path)
    elapsed = time.time() - start
    assert elapsed < 0.5, f"Bulk import exceeded runtime threshold: {elapsed:.2f}s"

def test_src_module_importable():
    """🔧 Defensive check: ensure 'src' module is discoverable in CI."""
    assert importlib.util.find_spec("src") is not None

def test_src_package_discoverable():
    """🧭 Guard: confirm 'src.utils.coercion' is visible to the runtime."""
    assert importlib.util.find_spec("src.utils.coercion") is not None



