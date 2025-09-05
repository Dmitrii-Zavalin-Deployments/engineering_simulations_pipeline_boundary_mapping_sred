# 📄 src/rules/rule_config_parser.py

import yaml
from src.rules.config import debug_log  # ✅ Strategic Addition

class RuleConfigError(Exception):
    """Raised when validation rule configuration cannot be parsed properly."""
    pass

def load_rule_profile(path: str) -> list:
    """
    Loads a YAML-based validation profile and returns a list of normalized rule definitions.

    Each rule must contain:
        - "if": expression string
        - "raise": error message string
    Optional:
        - "strict_type_check": boolean flag (default: False)

    Parameters:
        path (str): Path to YAML file containing rule definitions

    Returns:
        list: List of validated and enriched rule dictionaries

    Raises:
        RuleConfigError: If the file cannot be read or is malformed
    """
    try:
        with open(path, "r") as f:
            content = yaml.safe_load(f)
        debug_log(f"Loaded rule profile from '{path}'")
    except Exception as e:
        raise RuleConfigError(f"Failed to load rule profile at '{path}': {e}")

    raw_rules = content.get("rules", [])
    if not isinstance(raw_rules, list):
        raise RuleConfigError(f"Invalid rule structure: expected list under 'rules' key")
    
    debug_log(f"Found {len(raw_rules)} rule(s) in profile")

    enriched_rules = []
    skipped_count = 0

    for i, rule in enumerate(raw_rules):
        expr = rule.get("if")
        msg = rule.get("raise", f"Rule {i} failed")
        strict = rule.get("strict_type_check", False)

        if not isinstance(expr, str):
            debug_log(f"Skipping malformed rule at index {i}: missing 'if' expression")
            skipped_count += 1
            continue

        enriched = {
            "if": expr,
            "raise": msg,
            "strict_type_check": bool(strict),
        }
        debug_log(f"Rule {i} parsed → {enriched}")
        enriched_rules.append(enriched)

    if skipped_count > 0:
        debug_log(f"{skipped_count} rule(s) skipped due to formatting issues")

    debug_log(f"Returning {len(enriched_rules)} enriched rule(s)")
    return enriched_rules



