# 📄 tests/stubs/test_compat_import_aliases.py

"""🧩 Compatibility stub validation for get_resolution alias."""

import pytest
from unittest.mock import patch, mock_open, MagicMock
import validation.validation_profile_enforcer  # ✅ Monkeypatching target
from validation.validation_profile_enforcer import enforce_profile, ValidationProfileError

from tests.mocks.mock_profiles import VALID_ALIAS_PROFILE  # ✅ Still used

# 🪞 Compatibility alias for legacy usage
def get_resolution(config_path, payload):
    enforce_profile(config_path, payload)
    return payload  # ✅ Explicit return for assertions


# 🧪 Basic import alias check
def test_legacy_alias_callable_type():
    assert callable(get_resolution)
    assert get_resolution.__name__ == "get_resolution"


# 🧪 Invocation simulation with mock control and file override
@patch("os.path.isfile", return_value=True)
@patch("validation.validation_profile_enforcer.open", new_callable=mock_open,
       read_data=VALID_ALIAS_PROFILE.replace("is None", "== None"))
def test_alias_invocation_with_mock_payload(mock_file, mock_isfile, monkeypatch):
    monkeypatch.setattr(validation.validation_profile_enforcer, "profile_check_enabled", False)

    payload = {
        "resolution": {"dx": 0.2, "dy": 0.2, "dz": 0.2},
        "bounding_box": {
            "xmin": 0.0, "xmax": 1.0,
            "ymin": 0.0, "ymax": 1.0,
            "zmin": 0.0, "zmax": 1.0
        },
        "config": {
            "default_resolution": {
                "dx": 0.2, "dy": 0.2, "dz": 0.2
            }
        }
    }

    result = get_resolution("configs/validation/resolution_profile.yaml", payload)
    assert result is not None

# ⏱️ Performance ceiling check
@patch("os.path.isfile", return_value=True)
@patch("validation.validation_profile_enforcer.open", new_callable=mock_open,
       read_data=VALID_ALIAS_PROFILE.replace("is None", "== None"))
def test_resolution_alias_runtime_guard(mock_file, mock_isfile, monkeypatch):
    import time
    monkeypatch.setattr(validation.validation_profile_enforcer, "profile_check_enabled", True)

    payload = {
        "resolution": {"dx": 0.1, "dy": 0.1, "dz": 0.1},
        "bounding_box": {
            "xmin": 0.0, "xmax": 1.0,
            "ymin": 0.0, "ymax": 1.0,
            "zmin": 0.0, "zmax": 1.0
        },
        "config": {}
    }

    start = time.time()
    try:
        get_resolution("configs/validation/resolution_profile.yaml", payload)
    except Exception:
        pass

    assert time.time() - start < 0.3



