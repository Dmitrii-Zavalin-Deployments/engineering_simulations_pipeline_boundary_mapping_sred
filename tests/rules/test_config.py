# tests/rules/test_config.py

import os
import builtins
import pytest

import src.rules.config as config

# ---------------- ENABLE_RULE_DEBUG ----------------

def test_debug_flag_enabled(monkeypatch):
    """✅ Debug flag is set when environment variable is 'true'."""
    monkeypatch.setenv("ENABLE_RULE_DEBUG", "true")
    # Reload module to apply env change
    import importlib
    importlib.reload(config)
    assert config.ENABLE_RULE_DEBUG is True

def test_debug_flag_disabled(monkeypatch):
    """✅ Debug flag is False if env var missing or not 'true'."""
    monkeypatch.delenv("ENABLE_RULE_DEBUG", raising=False)
    import importlib
    importlib.reload(config)
    assert config.ENABLE_RULE_DEBUG is False

def test_debug_flag_invalid_value(monkeypatch):
    """✅ Debug flag is False on non-true values."""
    monkeypatch.setenv("ENABLE_RULE_DEBUG", "yes")
    import importlib
    importlib.reload(config)
    assert config.ENABLE_RULE_DEBUG is False


# ---------------- debug_log ----------------

def test_debug_log_enabled(monkeypatch, capsys):
    """✅ Emits log message when debug mode is enabled."""
    monkeypatch.setenv("ENABLE_RULE_DEBUG", "true")
    import importlib
    importlib.reload(config)
    config.debug_log("hello debug!")
    captured = capsys.readouterr()
    assert "[Rule Debug] hello debug!" in captured.out

def test_debug_log_disabled(monkeypatch, capsys):
    """✅ Does not emit message when debug mode is disabled."""
    monkeypatch.setenv("ENABLE_RULE_DEBUG", "false")
    import importlib
    importlib.reload(config)
    config.debug_log("silent mode")
    captured = capsys.readouterr()
    assert captured.out == ""

def test_debug_log_empty_string(monkeypatch, capsys):
    """🚫 Gracefully handles empty string input."""
    monkeypatch.setenv("ENABLE_RULE_DEBUG", "true")
    import importlib
    importlib.reload(config)
    config.debug_log("")
    captured = capsys.readouterr()
    assert "[Rule Debug] " in captured.out

def test_debug_log_non_string(monkeypatch, capsys):
    """🚫 Accepts non-string input and casts for output."""
    monkeypatch.setenv("ENABLE_RULE_DEBUG", "true")
    import importlib
    importlib.reload(config)
    config.debug_log(123)
    captured = capsys.readouterr()
    assert "[Rule Debug] 123" in captured.out



