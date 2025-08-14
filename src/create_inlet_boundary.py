# src/create_inlet_boundary.py

import json
import argparse
import sys
from pathlib import Path

def load_flow_data(flow_data_path):
    try:
        with open(flow_data_path, 'r') as f:
            data = json.load(f)
        velocity = data["initial_conditions"]["initial_velocity"]
        pressure = data["initial_conditions"]["initial_pressure"]
        return velocity, pressure
    except Exception as e:
        print(f"❌ Error loading flow data: {e}")
        sys.exit(1)

def load_boundary_config(boundary_config_path):
    try:
        with open(boundary_config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"⚠️ Boundary config not found at {boundary_config_path}. Creating new structure.")
        return {"boundaries": []}
    except Exception as e:
        print(f"❌ Error loading boundary config: {e}")
        sys.exit(1)

def inject_inlet_boundary(boundary_config, velocity, pressure):
    inlet_block = {
        "name": "inlet",
        "apply_faces": ["x_min"],
        "type": "velocity-pressure-inlet",
        "velocity": velocity,
        "pressure": pressure
    }

    # Remove existing inlet block if present
    boundary_config["boundaries"] = [
        b for b in boundary_config.get("boundaries", [])
        if b.get("name") != "inlet"
    ]

    # Append new inlet block
    boundary_config["boundaries"].append(inlet_block)
    return boundary_config

def save_boundary_config(boundary_config_path, boundary_config):
    try:
        with open(boundary_config_path, 'w') as f:
            json.dump(boundary_config, f, indent=2)
        print(f"✅ Inlet boundary injected into {boundary_config_path}")
    except Exception as e:
        print(f"❌ Error saving boundary config: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Inject inlet boundary using flow_data.json")
    parser.add_argument("--flow-data", required=True, help="Path to flow_data.json")
    parser.add_argument("--boundary-config", required=True, help="Path to boundary_conditions_gmsh.json")
    args = parser.parse_args()

    velocity, pressure = load_flow_data(args.flow_data)
    boundary_config = load_boundary_config(args.boundary_config)
    updated_config = inject_inlet_boundary(boundary_config, velocity, pressure)
    save_boundary_config(args.boundary_config, updated_config)

if __name__ == "__main__":
    main()



