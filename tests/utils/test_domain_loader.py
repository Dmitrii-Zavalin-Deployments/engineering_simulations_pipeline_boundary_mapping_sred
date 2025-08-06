# tests/utils/test_domain_loader.py

import pytest
from src.utils.domain_loader import DomainLoader

# ---------------- __init__ ----------------

def test_init_default_state():
    """✅ DomainLoader initializes with empty structures."""
    dl = DomainLoader()
    assert dl._bbox == {}
    assert dl._surface_tags == []

def test_init_custom_values():
    """✅ DomainLoader stores custom inputs."""
    bbox = {"xmin": 0, "xmax": 1}
    surfaces = [1, 2, 3]
    dl = DomainLoader(bounding_box=bbox, surface_tags=surfaces)
    assert dl._bbox == bbox
    assert dl._surface_tags == surfaces


# ---------------- has_geometry ----------------

def test_has_geometry_with_bbox():
    """✅ True if bbox populated."""
    dl = DomainLoader(bounding_box={"xmin": 1})
    assert dl.has_geometry() is True

def test_has_geometry_with_surfaces():
    """✅ True if surface tags present."""
    dl = DomainLoader(surface_tags=[42])
    assert dl.has_geometry() is True

def test_has_geometry_empty():
    """🚫 Returns False if no geometry."""
    dl = DomainLoader()
    assert dl.has_geometry() is False


# ---------------- surface_count ----------------

def test_surface_count_zero():
    """✅ Surface count returns zero."""
    dl = DomainLoader(surface_tags=[])
    assert dl.surface_count == 0

def test_surface_count_multiple():
    """✅ Surface count returns expected length."""
    dl = DomainLoader(surface_tags=[1, 2, 3, 4])
    assert dl.surface_count == 4


# ---------------- bounding_box ----------------

def test_bounding_box_contents():
    """✅ bounding_box property returns expected dict."""
    bbox = {"xmin": 0, "xmax": 9}
    dl = DomainLoader(bounding_box=bbox)
    assert dl.bounding_box == bbox


# ---------------- from_step ----------------

@pytest.fixture
def mock_gmsh(monkeypatch):
    """🚧 Mock Gmsh functions for from_step testing."""
    class MockModel:
        def add(name): pass
        def getEntities(dim):
            if dim == 3:
                return [(3, 99)]
            elif dim == 2:
                return [(2, 1), (2, 2)]
            return []
        def getBoundingBox(dim, tag):
            return (0, 1, 2, 3, 4, 5)

    monkeypatch.setattr("gmsh.initialize", lambda: None)
    monkeypatch.setattr("gmsh.open", lambda path: None)
    monkeypatch.setattr("gmsh.finalize", lambda: None)
    monkeypatch.setattr("gmsh.model", MockModel)

def test_from_step_volume_bbox(mock_gmsh):
    """✅ Uses bounding box from first volume entity."""
    loader = DomainLoader.from_step("fake_path.step")
    assert loader.bounding_box["xmax"] == 3
    assert loader.surface_count == 2

def test_from_step_surface_fallback(monkeypatch):
    """✅ Uses surface bounding box if no volume entities."""
    class MockModel:
        def add(name): pass
        def getEntities(dim):
            if dim == 3: return []
            if dim == 2: return [(2, 42)]
            return []
        def getBoundingBox(dim, tag):
            return (10, 20, 30, 40, 50, 60)

    monkeypatch.setattr("gmsh.initialize", lambda: None)
    monkeypatch.setattr("gmsh.open", lambda path: None)
    monkeypatch.setattr("gmsh.finalize", lambda: None)
    monkeypatch.setattr("gmsh.model", MockModel)

    loader = DomainLoader.from_step("fake_path.step")
    assert loader.bounding_box["zmax"] == 60
    assert loader.surface_count == 1

def test_from_step_no_entities(monkeypatch):
    """🚫 No bounding box or surface tags if no entities."""
    class MockModel:
        def add(name): pass
        def getEntities(dim): return []
        def getBoundingBox(dim, tag): return (0, 0, 0, 0, 0, 0)

    monkeypatch.setattr("gmsh.initialize", lambda: None)
    monkeypatch.setattr("gmsh.open", lambda path: None)
    monkeypatch.setattr("gmsh.finalize", lambda: None)
    monkeypatch.setattr("gmsh.model", MockModel)

    loader = DomainLoader.from_step("empty_path.step")
    assert loader.bounding_box == {}
    assert loader.surface_count == 0



