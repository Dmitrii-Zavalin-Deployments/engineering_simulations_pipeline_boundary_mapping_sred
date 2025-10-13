# src/gmsh_runner.py

import argparse
import json
import os
import gmsh
from src.boundary_conditions import generate_boundary_conditions
from src.utils.gmsh_input_check import validate_step_has_volumes, ValidationError

# ✅ Exposed for test patching
FLOW_DATA_PATH = "data/testing-input-output/flow_data.json"

def main():
    parser = argparse.ArgumentParser(description="Gmsh STEP parser for boundary condition metadata")
    parser.add_argument("--step", type=str, required=True, help="Path to STEP file")
    parser.add_argument("--resolution", type=float, help="Grid resolution in millimeters (model units)")
    parser.add_argument("--flow_region", type=str, choices=["internal", "external"], default="internal", help="Flow context for boundary classification")
    parser.add_argument("--padding_factor", type=int, default=5, help="Number of voxel layers to pad for external (if used)")
    parser.add_argument("--no_slip", type=lambda x: x.lower() == "true", default=True, help="Boundary condition: no-slip (True) or slip (False)")
    parser.add_argument("--initial_velocity", nargs=3, type=float, required=True, help="Initial velocity vector [vx vy vz] for inlet classification")
    parser.add_argument("--initial_pressure", type=float, required=True, help="Initial pressure value in Pascals for inlet condition")
    parser.add_argument("--output", type=str, required=True, help="Path to write boundary_conditions.json")
    parser.add_argument("--debug", action="store_true", help="Print full boundary condition structure for debugging")

    args = parser.parse_args()

    print(f"[INFO] Running boundary condition generation with:")
    print(f"       STEP file       : {args.step}")
    print(f"       Resolution      : {args.resolution}")
    print(f"       Flow region     : {args.flow_region}")
    print(f"       Padding factor  : {args.padding_factor}")
    print(f"       No-slip         : {args.no_slip}")
    print(f"       Initial velocity: {args.initial_velocity}")
    print(f"       Initial pressure: {args.initial_pressure}")
    print(f"       Output path     : {args.output}")
    print(f"       Debug mode      : {args.debug}")

    flow_data_path = FLOW_DATA_PATH
    if not os.path.isfile(flow_data_path):
        raise FileNotFoundError(f"Missing flow_data.json at expected location: {flow_data_path}")
    if args.debug:
        print(f"[DEBUG] Found flow_data.json at: {flow_data_path}")

    with open(flow_data_path, "r") as f:
        model_data = json.load(f)
    if args.debug:
        print(f"[DEBUG] Loaded model_data from flow_data.json")

    model_data["model_properties"]["flow_region"] = args.flow_region
    model_data["model_properties"]["no_slip"] = args.no_slip
    model_data["initial_conditions"]["velocity"] = args.initial_velocity
    model_data["initial_conditions"]["pressure"] = args.initial_pressure
    if args.debug:
        print(f"[DEBUG] Injected CLI overrides into model_data")

    gmsh.initialize()
    if args.debug:
        print("[DEBUG] Gmsh initialized")

    try:
        validate_step_has_volumes(args.step)
        if args.debug:
            print("[DEBUG] STEP file volume validation passed")

        result = generate_boundary_conditions(
            step_path=args.step,
            velocity=args.initial_velocity,
            pressure=args.initial_pressure,
            no_slip=args.no_slip,
            flow_region=args.flow_region,
            resolution=args.resolution,
            debug=args.debug
        )
        if args.debug:
            print("[DEBUG] Boundary condition generation completed")

        if not result or not isinstance(result, list):
            raise RuntimeError("❌ Boundary condition generation failed or returned empty result.")

        print(f"[INFO] Generated {len(result)} boundary condition blocks.")
        print(f"[INFO] Roles included: {sorted(set(b['role'] for b in result))}")

        if args.debug:
            print("[DEBUG] Full boundary condition output:")
            print(json.dumps(result, indent=2))

        with open(args.output, "w") as f:
            json.dump(result, f, indent=2)
        print(f"[INFO] Boundary conditions written to: {args.output}")
        if args.debug:
            print(f"[DEBUG] Output file successfully written: {args.output}")

    except (FileNotFoundError, ValidationError) as e:
        raise RuntimeError(f"❌ STEP file validation failed: {e}")
    except Exception as e:
        print(f"[ERROR] Unexpected failure: {e}")
        raise
    finally:
        if gmsh.isInitialized():
            try:
                gmsh.finalize()
                if args.debug:
                    print("[DEBUG] Gmsh finalized successfully")
            except Exception as e:
                print(f"[WARN] Gmsh finalization error: {e}")

if __name__ == "__main__":
    main()



