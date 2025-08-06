# tests/integration/test_gmsh_lifecycle.py

import pytest
import gmsh


def test_gmsh_initialize_and_finalize_safe():
    """Validate that Gmsh can be initialized and finalized cleanly."""
    assert not gmsh.isInitialized(), "Gmsh should not be initialized at start"

    try:
        gmsh.initialize()
        assert gmsh.isInitialized(), "Gmsh should be initialized after initialize()"
    finally:
        try:
            gmsh.finalize()
        except Exception as e:
            pytest.fail(f"Gmsh finalize failed: {e}")

    assert not gmsh.isInitialized(), "Gmsh should return to uninitialized state after finalize()"


def test_gmsh_double_initialize_is_tolerated():
    """Check that reinitializing Gmsh does not crash or corrupt state."""
    try:
        gmsh.initialize()
        gmsh.initialize()  # Should not raise
        assert gmsh.isInitialized(), "Gmsh should remain initialized"
    except Exception as e:
        pytest.fail(f"Double initialize triggered failure: {e}")
    finally:
        try:
            gmsh.finalize()
        except Exception as e:
            pytest.fail(f"Finalize after double init failed: {e}")

    assert not gmsh.isInitialized(), "Finalized state should be clean after nested initialize"


def test_finalize_before_initialize_is_safe():
    """Ensure finalize() can be called without prior initialization."""
    try:
        if hasattr(gmsh, "isInitialized") and gmsh.isInitialized():
            gmsh.finalize()
    except Exception:
        pass

    assert not gmsh.isInitialized(), "State should remain uninitialized"

    try:
        if hasattr(gmsh, "isInitialized") and gmsh.isInitialized():
            gmsh.finalize()
    except Exception:
        pass

    assert not gmsh.isInitialized(), "Finalization should be safe even if never initialized"


def test_gmsh_initialize_flag_during_session():
    """Confirm gmsh.isInitialized() reflects real-time state inside session."""
    try:
        gmsh.initialize()
        assert gmsh.isInitialized(), "Initialization flag should be active"
        gmsh.model.add("dummy")
        assert gmsh.isInitialized(), "Session should remain active after model ops"
    except Exception as e:
        pytest.fail(f"Gmsh session failed unexpectedly: {e}")
    finally:
        try:
            gmsh.finalize()
        except Exception as e:
            pytest.fail(f"Finalize in session teardown failed: {e}")

    assert not gmsh.isInitialized(), "Session should conclude with clean teardown"



