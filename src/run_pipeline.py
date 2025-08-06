# src/run_pipeline.py

"""📄 STEP-driven domain generation pipeline — module mode compatible"""

import sys
import os
import json
from pathlib import Path

from src.gmsh_runner import extract_bounding_box_with_gmsh
from src.domain_definition_writer import validate_domain_bounds, DomainValidationError
from src.logger_utils import log_checkpoint, log_error, log_success, log_warning
from src.utils.coercion import coerce_numeric
from src.utils.input_validation import validate_step_file

DEFAULT_RESOLUTION = 0.01  # meters
IO_DIRECTORY = Path(__file__).parent.parent.resolve() / "data/testing-input-output"

# ✅ Allow dynamic override from environment
env_output_path = os.getenv("OUTPUT_PATH")
OUTPUT_PATH = Path(env_output_path) if env_output_path else IO_DIRECTORY / "domain_metadata.json"

__all__ = ["sanitize_payload"]

TEST_MODE_ENABLED = os.getenv("PIPELINE_TEST_MODE", "false").lower() == "true"
ENV_RESOLUTION = os.getenv("PIPELINE_RESOLUTION_OVERRIDE")
PRELOADED_RESOLUTION = float(ENV_RESOLUTION) if ENV_RESOLUTION else None


def conditional_exit(code=0):
    if TEST_MODE_ENABLED:
        log_checkpoint(f"🚦 TEST MODE ACTIVE: exit({code}) suppressed")
    else:
        sys.exit(code)


def default_domain():
    return {
        "x": 0.0, "y": 0.0, "z": 0.0,
        "width": 0.0, "height": 0.0, "depth": 0.0
    }


def sanitize_payload(metadata: dict) -> dict:
    metadata.setdefault("domain_definition", default_domain())
    domain = metadata["domain_definition"]

    x = coerce_numeric(domain.get("x") or domain.get("min_x")) or 0.0
    y = coerce_numeric(domain.get("y") or domain.get("min_y")) or 0.0
    z = coerce_numeric(domain.get("z") or domain.get("min_z")) or 0.0

    width_val = coerce_numeric(domain.get("width"))
    if width_val is None:
        log_warning(f"Width coercion failed → fallback applied [raw: {domain.get('width')}]")
    max_x_val = coerce_numeric(domain.get("max_x"))
    width = max(0.0, width_val if width_val is not None else (max_x_val or 0.0) - x)

    height_val = coerce_numeric(domain.get("height"))
    if height_val is None:
        log_warning(f"Height coercion failed → fallback applied [raw: {domain.get('height')}]")
    max_y_val = coerce_numeric(domain.get("max_y"))
    height = max(0.0, height_val if height_val is not None else (max_y_val or 0.0) - y)

    depth_val = coerce_numeric(domain.get("depth"))
    if depth_val is None:
        log_warning(f"Depth coercion failed → fallback applied [raw: {domain.get('depth')}]")
    max_z_val = coerce_numeric(domain.get("max_z"))
    depth = max(0.0, depth_val if depth_val is not None else (max_z_val or 0.0) - z)

    min_x = coerce_numeric(x)
    max_x = coerce_numeric(x + width)
    min_y = coerce_numeric(y)
    max_y = coerce_numeric(y + height)
    min_z = coerce_numeric(z)
    max_z = coerce_numeric(z + depth)

    return {
        "domain_definition": {
            "x": x, "y": y, "z": z,
            "width": width, "height": height, "depth": depth,
            "min_x": min_x, "max_x": max_x,
            "min_y": min_y, "max_y": max_y,
            "min_z": min_z, "max_z": max_z
        }
    }


def enforce_domain_rules(domain: dict):
    if domain.get("max_x") < domain.get("min_x"):
        raise ValueError("max_x must be ≥ min_x")
    if domain.get("max_y") < domain.get("min_y"):
        raise ValueError("max_y must be ≥ min_y")
    if domain.get("max_z") < domain.get("min_z"):
        raise ValueError("max_z must be ≥ min_z")


def main(resolution=None):
    log_checkpoint("🔧 Pipeline script has entered main()")
    log_checkpoint("🚀 STEP-driven pipeline initialized (Gmsh backend)")

    global IO_DIRECTORY
    if not isinstance(IO_DIRECTORY, Path):
        IO_DIRECTORY = Path(IO_DIRECTORY)

    if not IO_DIRECTORY.exists():
        log_error(f"Input directory not found: {IO_DIRECTORY}", fatal=True)
        conditional_exit(1)

    step_files = list(IO_DIRECTORY.glob("*.step"))
    if len(step_files) == 0:
        log_error("No STEP files found", fatal=True)
        conditional_exit(1)
    elif len(step_files) > 1:
        log_error("Multiple STEP files detected — provide exactly one", fatal=True)
        conditional_exit(1)

    step_path = step_files[0]
    log_checkpoint(f"📄 Using STEP file: {step_path.name}")

    validate_step_file(step_path)

    try:
        log_checkpoint("📂 Calling Gmsh geometry parser...")
        domain_definition = extract_bounding_box_with_gmsh(str(step_path), resolution)
        log_checkpoint(f"📐 Domain extracted: {domain_definition}")
    except Exception as e:
        log_error(f"Gmsh geometry extraction failed:\n{e}", fatal=True)
        conditional_exit(1)

    try:
        validate_domain_bounds(domain_definition)
        log_success("Domain bounds validated successfully")
    except DomainValidationError as err:
        log_error(f"Domain bounds validation failed:\n{err}", fatal=True)
        conditional_exit(1)

    metadata = {"domain_definition": domain_definition}
    payload = sanitize_payload(metadata)
    domain = payload["domain_definition"]

    for key in ["min_x", "max_x", "min_y", "max_y", "min_z", "max_z"]:
        val = domain.get(key)
        if isinstance(val, str):
            try:
                domain[key] = float(val)
                log_checkpoint(f"🔧 Coerced {key} from string to float: {val} → {domain[key]}")
            except ValueError:
                log_error(f"Failed to coerce {key}: {val}", fatal=True)
                conditional_exit(1)
        else:
            log_checkpoint(f"✅ {key} is already {type(val).__name__}: {val}")

    try:
        log_checkpoint("🔎 Enforcing domain validation rules (native Python)...")
        enforce_domain_rules(domain)
        log_success("✅ Domain validation passed")
    except ValueError as e:
        log_error(f"Validation failed: {e}", fatal=True)
        conditional_exit(1)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(payload, f, indent=2)
    log_success(f"Metadata written to {OUTPUT_PATH}")

    log_checkpoint("🏁 Pipeline completed successfully")
    conditional_exit(0)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="STEP-driven domain pipeline (Gmsh backend)")
    parser.add_argument("--resolution", type=float,
                        help="Voxel resolution in meters (default: auto via profile or env override)")
    args = parser.parse_args()
    main(resolution=args.resolution or PRELOADED_RESOLUTION)



