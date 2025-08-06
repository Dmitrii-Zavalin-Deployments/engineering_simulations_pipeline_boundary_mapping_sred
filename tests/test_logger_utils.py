# tests/test_logger_utils.py

import pytest
import sys
import builtins
from unittest.mock import patch
from src import logger_utils as log


# ----------- log_checkpoint -----------

def test_log_checkpoint_default(capsys):
    """✅ Basic checkpoint logging with default emoji and newline."""
    log.log_checkpoint("Hello world")
    output = capsys.readouterr().out
    assert "🪵" in output and "Hello world" in output and output.endswith("\n")

def test_log_checkpoint_no_newline(capsys):
    """✅ Logging without newline."""
    log.log_checkpoint("Inline message", newline=False)
    output = capsys.readouterr().out
    assert output.endswith("Inline message")

def test_log_checkpoint_custom_emoji(capsys):
    """✅ Logging with custom emoji prefix."""
    log.log_checkpoint("Custom tag", emoji="🔔")
    output = capsys.readouterr().out
    assert output.startswith("🔔 [")

def test_log_checkpoint_empty_message(capsys):
    """🚫 Handles empty string gracefully."""
    log.log_checkpoint("")
    output = capsys.readouterr().out
    assert "]" in output  # Timestamp still present

def test_log_checkpoint_non_string(capsys):
    """🚫 Converts non-string message input safely."""
    log.log_checkpoint(12345)
    output = capsys.readouterr().out
    assert "12345" in output


# ----------- log_error -----------

def test_log_error_non_fatal(capsys):
    """✅ Prints error without exiting."""
    log.log_error("Sample error", fatal=False)
    output = capsys.readouterr().out
    assert "❌ ERROR: Sample error" in output
    assert "💥" in output

def test_log_error_fatal_exit(monkeypatch):
    """✅ Exits when fatal is True."""
    monkeypatch.setattr(sys, "exit", lambda code: (_ for _ in ()).throw(SystemExit(code)))
    with pytest.raises(SystemExit) as excinfo:
        log.log_error("Fatal error", fatal=True)
    assert excinfo.value.code == 1


# ----------- log_success -----------

def test_log_success_output(capsys):
    """✅ Prints success message with stars."""
    log.log_success("All good")
    output = capsys.readouterr().out
    assert "✅ All good" in output and "🌟" in output


# ----------- log_info -----------

def test_log_info_output(capsys):
    """✅ Prints info message with 🧾 emoji."""
    log.log_info("FYI notice")
    output = capsys.readouterr().out
    assert "🧾" in output and "FYI notice" in output


# ----------- log_warning -----------

def test_log_warning_output(capsys):
    """✅ Prints warning with label and emoji."""
    log.log_warning("Disk space low")
    output = capsys.readouterr().out
    assert "⚠️ WARNING: Disk space low" in output



