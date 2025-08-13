# src/schema_writer.py

import json
import os
from typing import Dict, Any
from jsonschema import validate, ValidationError

# ✅ Path to schema definition
SCHEMA_PATH = os.path.join("schemas", "domain_schema.json")

def load_schema() -> Dict[str, Any]:
    """
    Load the domain boundary condition schema.
    """
    with open(SCHEMA_PATH, "r") as f:
        return json.load(f)

def validate_boundary_conditions(data: Dict[str, Any]) -> bool:
    """
    Validate boundary condition data against the domain schema.
    Returns True if valid, raises ValidationError if invalid.
    """
    schema = load_schema()
    validate(instance=data, schema=schema)
    return True

def generate_boundary_block(classified: Dict[str, Any]) -> Dict[str, Any]:
    """
    Construct the final boundary_conditions block from classified face data.
    Ensures schema compliance and prepares for simulation export.
    """
    bc = classified.get("boundary_conditions", {})
    block = {
        "x_min": bc.get("x_min", "none"),
        "x_max": bc.get("x_max", "none"),
        "y_min": bc.get("y_min", "none"),
        "y_max": bc.get("y_max", "none"),
        "z_min": bc.get("z_min", "none"),
        "z_max": bc.get("z_max", "none"),
        "faces": bc.get("faces", []),
        "type": "dirichlet",
        "apply_faces": bc.get("apply_faces", []),
        "apply_to": ["pressure", "velocity"],
        "pressure": 0.0,
        "velocity": [0.0, 0.0, 0.0],
        "no_slip": True
    }

    # ✅ Validate before returning
    validate_boundary_conditions(block)
    return block

def write_boundary_json(output_path: str, boundary_block: Dict[str, Any]) -> None:
    """
    Write the boundary condition block to a JSON file.
    """
    with open(output_path, "w") as f:
        json.dump(boundary_block, f, indent=2)
    print(f"[SchemaWriter] Boundary conditions written to: {output_path}")



