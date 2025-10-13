# src/schema_writer.py

import json
import os
from typing import Dict, Any
from jsonschema import validate

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

def infer_velocity_vector(apply_faces: list) -> list:
    """
    Infer a velocity vector based on directional face labels.
    """
    direction_map = {
        "x_min": [1.0, 0.0, 0.0],
        "x_max": [-1.0, 0.0, 0.0],
        "y_min": [0.0, 1.0, 0.0],
        "y_max": [0.0, -1.0, 0.0],
        "z_min": [0.0, 0.0, 1.0],
        "z_max": [0.0, 0.0, -1.0]
    }

    for face in apply_faces:
        if face in direction_map:
            return direction_map[face]
    return [0.0, 0.0, 0.0]

def get_pressure_override() -> float:
    """
    Get pressure override from environment variable or fallback to default.
    """
    try:
        return float(os.getenv("BOUNDARY_PRESSURE", "0.0"))
    except ValueError:
        return 0.0

def generate_boundary_block(classified: Dict[str, Any]) -> Dict[str, Any]:
    """
    Construct the final boundary_conditions block from classified face data.
    Ensures schema compliance and prepares for simulation export.
    """
    bc = classified.get("boundary_conditions", {})
    apply_faces = bc.get("apply_faces", [])
    velocity = infer_velocity_vector(apply_faces)
    pressure = get_pressure_override()

    block = {
        "x_min": bc.get("x_min", "none"),
        "x_max": bc.get("x_max", "none"),
        "y_min": bc.get("y_min", "none"),
        "y_max": bc.get("y_max", "none"),
        "z_min": bc.get("z_min", "none"),
        "z_max": bc.get("z_max", "none"),
        "faces": bc.get("faces", []),
        "type": "dirichlet",
        "apply_faces": apply_faces,
        "apply_to": ["pressure", "velocity"],
        "pressure": pressure,
        "velocity": velocity,
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



