# /src/domain_definition_writer.py

"""
Domain Definition Writer Module

Validates spatial domain parameters for simulation pipelines,
ensuring integrity between schema constraints and dynamic logic.
"""

from typing import Dict


class DomainValidationError(Exception):
    """Custom exception raised when domain bounds are inconsistent."""
    pass


def validate_domain_bounds(domain: Dict) -> None:
    """
    Runtime check to validate that max bounds are greater than min bounds
    across all axes (x, y, z). Raises DomainValidationError if invalid.

    Parameters:
        domain (dict): Dictionary containing domain fields.

    Expected Keys:
        min_x, max_x, min_y, max_y, min_z, max_z
    """
    axes = ["x", "y", "z"]
    for axis in axes:
        min_val = domain.get(f"min_{axis}")
        max_val = domain.get(f"max_{axis}")
        if min_val is None or max_val is None:
            raise DomainValidationError(f"Missing domain bounds for axis '{axis}'")
        try:
            min_val = float(min_val)
            max_val = float(max_val)
        except (TypeError, ValueError):
            raise DomainValidationError(f"Non-numeric bounds for axis '{axis}'")
        if max_val < min_val:
            raise DomainValidationError(
                f"Invalid domain: max_{axis} ({max_val}) < min_{axis} ({min_val})"
            )


# Optional usage example
if __name__ == "__main__":
    sample_domain = {
        "min_x": 0.0, "max_x": 10.0,
        "min_y": 0.0, "max_y": 5.0,
        "min_z": "2.0", "max_z": 1.0  # <-- Valid string cast, but will still fail logically
    }

    try:
        validate_domain_bounds(sample_domain)
        print("Domain bounds are valid ✅")
    except DomainValidationError as e:
        print(f"Validation failed ❌: {e}")



