# src/gmsh_runner.py

import argparse
import json
import os
import gmsh
from src.gmsh_geometry import extract_geometry_mask
from src.utils.gmsh_input_check import validate_step_has_volumes, ValidationError

# ✅ Exposed for test patching
FLOW_DATA_PATH = "data/testing-input-output/flow_data.json"

def main():
    parser = argparse.ArgumentParser(description="Gmsh STEP parser for geometry mask metadata")
    parser.add_argument("--step", type=str, required=True, help="Path to STEP file")
    parser.add_argument("--resolution", type=float, help="Grid resolution in millimeters (model units)")
    parser.add_argument("--flow_region", type=str, choices=["internal", "external"], default="internal", help="Flow context for masking")
    parser.add_argument("--padding_factor", type=int, default=5, help="Number of voxel layers to pad for external")
    parser.add_argument("--no_slip", type=lambda x: x.lower() == "true", default=True, help="Boundary condition: no-slip (True) or slip (False)")
    parser.add_argument("--output", type=str, help="Path to write geometry mask JSON")
    parser.add_argument("--debug", action="store_true", help="Print full geometry mask structure for debugging")

    args = parser.parse_args()

    print(f"[INFO] Running Gmsh mask extraction with:")
    print(f"       STEP file       : {args.step}")
    print(f"       Resolution      : {args.resolution}")
    print(f"       Flow region     : {args.flow_region}")
    print(f"       Padding factor  : {args.padding_factor}")
    print(f"       No-slip         : {args.no_slip}")
    print(f"       Output path     : {args.output}")
    print(f"       Debug mode      : {args.debug}")

    # ✅ Use module-level constant for test patching
    flow_data_path = FLOW_DATA_PATH
    if not os.path.isfile(flow_data_path):
        raise FileNotFoundError(f"Missing flow_data.json at expected location: {flow_data_path}")

    with open(flow_data_path, "r") as f:
        model_data = json.load(f)

    # Inject CLI overrides
    model_data["model_properties"]["flow_region"] = args.flow_region
    model_data["model_properties"]["no_slip"] = args.no_slip

    # Initialize Gmsh and validate STEP file
    gmsh.initialize()
    try:
        validate_step_has_volumes(args.step)

        # Proceed with geometry masking
        result = extract_geometry_mask(
            step_path=args.step,
            resolution=args.resolution,
            flow_region=args.flow_region,
            padding_factor=args.padding_factor,
            no_slip=args.no_slip,
            model_data=model_data,
            debug=args.debug
        )

        # Post-process boundary voxels based on no_slip flag
        boundary_count = result["geometry_mask_flat"].count(-1)
        print(f"[DEBUG] Found {boundary_count} boundary voxels (value = -1) before applying no_slip policy.")

        if boundary_count > 0:
            if args.no_slip:
                result["geometry_mask_flat"] = [0 if v == -1 else v for v in result["geometry_mask_flat"]]
                print("[INFO] Boundary voxels reclassified as solid (0) due to no_slip = True.")
            else:
                result["geometry_mask_flat"] = [1 if v == -1 else v for v in result["geometry_mask_flat"]]
                print("[INFO] Boundary voxels reclassified as fluid (1) due to no_slip = False.")

        # Remove boundary from mask_encoding
        if "boundary" in result["mask_encoding"]:
            del result["mask_encoding"]["boundary"]

        # Show updated flow region and comment if fallback occurred
        updated_region = model_data["model_properties"].get("flow_region")
        region_comment = model_data["model_properties"].get("flow_region_comment", "")
        print(f"[INFO] Final flow region used: {updated_region}")
        if region_comment:
            print(f"[INFO] Flow region comment: {region_comment}")

        print("[INFO] Final geometry mask:")
        print(json.dumps(result, indent=2))

        if args.output:
            with open(args.output, "w") as f:
                json.dump(result, f, indent=2)
            print(f"[INFO] Geometry mask written to: {args.output}")

    except (FileNotFoundError, ValidationError) as e:
        raise RuntimeError(f"❌ STEP file validation failed: {e}")
    except Exception as e:
        print(f"[ERROR] Unexpected failure: {e}")
        raise
    finally:
        if gmsh.isInitialized():
            try:
                gmsh.finalize()
            except Exception as e:
                print(f"[WARN] Gmsh finalization error: {e}")

if __name__ == "__main__":
    main()



