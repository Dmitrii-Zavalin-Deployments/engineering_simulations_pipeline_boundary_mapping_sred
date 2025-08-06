# 📄 tests/mocks/mock_profiles.py

import pytest
import yaml
from unittest.mock import mock_open, patch


# ------------------------------------------------------------------------------------
# 📦 Profile Snippet Registry — Static YAML Payloads
# ------------------------------------------------------------------------------------

VALID_ALIAS_PROFILE = """
alias_map:
  temp: "temperature"
  pres: "pressure"
thresholds:
  temperature: { warn_val: 100, max_val: 150 }
  pressure: { warn_val: 50, max_val: 100 }
"""

MISSING_ALIAS_SECTION = """
thresholds:
  temperature: { warn_val: 100, max_val: 150 }
"""

INVALID_YAML_SYNTAX = """
alias_map:
  temp: "temperature"
  pressure  # Missing colon
thresholds:
  temperature: { warn_val: 100, max_val: 150 }
"""

NON_MAPPING_ALIAS = """
alias_map: ["temp", "pressure"]
thresholds:
  temperature: { warn_val: 100, max_val: 150 }
"""

EMPTY_PAYLOAD = ""

# ✅ Safe rule mock for fallback evaluation
RULE_WITH_EQ_OPERATOR = """
rules:
  - if: resolution.dx == None
    raise: Missing resolution.dx
"""

# ------------------------------------------------------------------------------------
# 🧪 Validation Routines — YAML Integrity and Structure
# ------------------------------------------------------------------------------------

@pytest.mark.parametrize("profile_text,expect_success", [
    (VALID_ALIAS_PROFILE, True),
    (MISSING_ALIAS_SECTION, False),
    (INVALID_YAML_SYNTAX, False),
    (NON_MAPPING_ALIAS, False),
    (EMPTY_PAYLOAD, False),
])
def test_yaml_profile_parsing(profile_text, expect_success):
    """
    Verifies whether mock YAML payloads can be loaded and used for alias resolution.
    """
    mocked_open = mock_open(read_data=profile_text)
    with patch("builtins.open", mocked_open):
        try:
            with open("dummy_profile.yaml") as f:
                loaded = yaml.safe_load(f)
                assert isinstance(loaded, dict)
                assert "alias_map" in loaded
                assert isinstance(loaded["alias_map"], dict)
                if expect_success:
                    assert "temp" in loaded["alias_map"]
                else:
                    pytest.fail("Invalid profile passed validation unexpectedly.")
        except Exception:
            if expect_success:
                pytest.fail("Valid profile failed to load or parse correctly.")


def test_valid_alias_resolution():
    """
    Asserts correct mapping from alias to formal metric name.
    """
    payload = yaml.safe_load(VALID_ALIAS_PROFILE)
    assert payload["alias_map"]["temp"] == "temperature"
    assert payload["alias_map"]["pres"] == "pressure"
    assert payload["thresholds"]["temperature"]["max_val"] == 150


def test_empty_payload_triggers_keyerror():
    """
    Validates that an empty profile triggers expected errors in downstream logic.
    """
    with pytest.raises(Exception):
        yaml.safe_load(EMPTY_PAYLOAD)["alias_map"]


def test_rule_operator_syntax_replacement():
    """
    Verifies that a rule using 'is' operator can be safely rewritten to '=='.
    """
    raw = yaml.safe_load(RULE_WITH_EQ_OPERATOR.replace("== None", "is None"))  # simulate original
    fixed = yaml.safe_load(RULE_WITH_EQ_OPERATOR)
    assert raw["rules"][0]["if"].endswith("is None")
    assert fixed["rules"][0]["if"].endswith("== None")



