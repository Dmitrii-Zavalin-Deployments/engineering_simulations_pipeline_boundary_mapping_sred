# 📄 src/rules/config.py

"""
Configuration flags and global toggles used throughout rule evaluation modules.

Includes:
- Debug mode for verbose output during expression parsing and type coercion
- Future extension hooks for environment or feature flags
"""

import os

# ✅ Debug logging toggle (CI-driven only, no .env required)
ENABLE_RULE_DEBUG = os.getenv("ENABLE_RULE_DEBUG") == "true"

def debug_log(message: str):
    """
    Emits diagnostic messages if debug mode is enabled.
    Used by rule parsing and coercion routines.
    """
    if ENABLE_RULE_DEBUG:
        print(f"[Rule Debug] {message}")



