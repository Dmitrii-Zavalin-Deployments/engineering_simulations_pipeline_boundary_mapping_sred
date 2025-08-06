# 📄 tests/conftest.py

import sys
import pathlib
import pytest
import gmsh
import yaml
from unittest.mock import patch, mock_open

# Adds src/ directory to sys.path for all tests
SRC_PATH = pathlib.Path(__file__).resolve().parents[1] / "src"
if SRC_PATH.exists():
    sys.path.insert(0, str(SRC_PATH))


@pytest.fixture(scope="function")
def gmsh_session():
    """
    Provides an initialized and finalized Gmsh session around each test.
    """
    gmsh.initialize()
    yield
    gmsh.finalize()


# ✅ Strategic Addition: Reusable lifecycle patch fixture
@pytest.fixture(scope="function")
def mock_gmsh_lifecycle():
    """
    Mocks essential Gmsh lifecycle components to prevent initialization errors.
    
    Usage:
        def test_something(mock_gmsh_lifecycle):
            with mock_gmsh_lifecycle:
                ...
    """
    with patch("gmsh.initialize"), \
         patch("gmsh.finalize"), \
         patch("gmsh.model.add"), \
         patch("gmsh.logger.getLastError", return_value=""):
        yield


# 🧪 Fixture: Injects mocked STEP asset into temp test path
@pytest.fixture(scope="function")
def mock_step_file(tmp_path):
    fixture_path = pathlib.Path(__file__).parent / "fixtures" / "mock_geometry" / "mock_geometry.step"
    target_path = tmp_path / "mock_geometry.step"
    target_path.write_bytes(fixture_path.read_bytes())
    return str(target_path)


@pytest.fixture(scope="function")
def mock_validate_step_file():
    with patch("os.path.isfile", return_value=True):
        with patch("src.utils.input_validation.validate_step_file", return_value=True) as mock_func:
            yield mock_func


@pytest.fixture(scope="function")
def mock_gmsh_volume():
    with patch("gmsh.open", return_value=None):
        with patch("gmsh.model.getEntities", return_value=[(3, 1)]):
            yield True


@pytest.fixture(scope="function")
def mock_gmsh_entities_empty():
    with patch("gmsh.open", return_value=None):
        with patch("gmsh.model.getEntities", return_value=[]):
            yield True


@pytest.fixture(scope="function")
def mock_gmsh_full_lifecycle():
    with patch("gmsh.initialize", return_value=None), \
         patch("gmsh.model.add", return_value=None), \
         patch("gmsh.logger.getLastError", return_value=""), \
         patch("gmsh.open", return_value=None), \
         patch("gmsh.model.getEntities", return_value=[(3, 1)]):
        yield True


@pytest.fixture
def load_mock_profile():
    def _loader(yaml_text):
        mocked_open = mock_open(read_data=yaml_text)
        with patch("builtins.open", mocked_open):
            with open("fake/path/profile.yaml") as f:
                return yaml.safe_load(f)
    return _loader


def get_payload_with_defaults(overrides=None):
    base = {
        "hello": "world",
        "flag": True,
        "thresholds": {"warn_val": 150, "max_val": 150},
        "limits": {"upper": 10.0, "lower": 5.0},
        "metrics": {"score": 0.3},
        "values": {"x": 5},
        "system": {"subsystem": {"value": 42}},
        "expected": {"value": 42},
        "config": {"enabled": "true"},
        "domain_definition": {"max_z": 100.0, "min_z": 90.5},
        "a": {"b": 10},
        "x": {"y": 10},
        "rules": {"status_code": "not_a_number", "expected_code": 200},
    }

    if overrides:
        for key, value in overrides.items():
            if isinstance(base.get(key), dict) and not isinstance(value, dict):
                raise TypeError(f"Cannot override structured key '{key}' with scalar value: {value}")
            elif isinstance(base.get(key), dict) and isinstance(value, dict):
                base[key].update(value)
            else:
                base[key] = value
    return base



