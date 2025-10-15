# src/boundary_conditions.py

import gmsh
from .geometry import (
    assign_roles_to_faces
)
from .bc_generators import (
    generate_internal_bc_blocks,
    generate_external_bc_blocks
)

def load_geometry(step_path, debug=False):
    """
    Opens the STEP file and prepares the GMSH model.

    Args:
        step_path (str): Path to the STEP geometry file.
        debug (bool): If True, prints debug information.

    Raises:
        FileNotFoundError: If the STEP file does not exist.
    """
    gmsh.initialize()
    gmsh.model.add("boundary_model")
    gmsh.open(step_path)

    if debug:
        print(f"[DEBUG] Loaded STEP geometry from: {step_path}")


def generate_mesh(resolution=None, debug=False):
    """
    Sets mesh resolution and generates the 3D mesh.

    Args:
        resolution (float or None): Desired mesh resolution. If None, uses default.
        debug (bool): If True, prints debug information.
    """
    if resolution is not None:
        gmsh.option.setNumber("Mesh.CharacteristicLengthMin", resolution)
        gmsh.option.setNumber("Mesh.CharacteristicLengthMax", resolution)
        if debug:
            print(f"[DEBUG] Mesh resolution set to: {resolution}")

    gmsh.model.mesh.generate(3)

    if debug:
        print("[DEBUG] 3D mesh generated")


def get_surface_faces(debug=False):
    """
    Returns all 2D surface entities from the mesh.

    Args:
        debug (bool): If True, prints the number of surfaces found.

    Returns:
        list of tuples: Each tuple is (dim, tag) for a surface entity.
    """
    surfaces = gmsh.model.getEntities(2)

    if debug:
        print(f"[DEBUG] Extracted {len(surfaces)} surface entities")

    return surfaces


def get_x_bounds(debug=False):
    """
    Extracts x_min and x_max from the model bounding box.

    Args:
        debug (bool): If True, prints the extracted bounds.

    Returns:
        tuple: (x_min, x_max)
    """
    bounds = gmsh.model.getBoundingBox(3, 1)
    if len(bounds) == 7:
        _, x_min, _, _, x_max, _, _ = bounds
    else:
        x_min, _, _, x_max, _, _ = bounds if len(bounds) == 6 else [-1e9, 0, 0, 1e9, 0, 0]

    if debug:
        print(f"[DEBUG] Bounding box X-range: x_min={x_min}, x_max={x_max}")

    return x_min, x_max


def generate_boundary_conditions(step_path, velocity, pressure, no_slip, flow_region,
                                 padding_factor=0, resolution=None,
                                 threshold=0.9, tolerance=1e-6, debug=False):
    """
    Main entry point that orchestrates boundary condition generation.

    Args:
        step_path (str): Path to STEP file.
        velocity (list): Initial velocity vector.
        pressure (float): Initial pressure value.
        no_slip (bool): Whether to apply no-slip condition.
        flow_region (str): 'internal' or 'external'.
        padding_factor (float): Padding multiplier for external flow.
        resolution (float): Mesh resolution.
        threshold (float): Alignment threshold.
        tolerance (float): Coordinate tolerance.
        debug (bool): If True, prints debug information.

    Returns:
        list: Boundary condition blocks.
    """
    load_geometry(step_path, debug)
    generate_mesh(resolution, debug)
    surfaces = get_surface_faces(debug)
    x_min, x_max = get_x_bounds(debug)

    face_roles, face_geometry_data = assign_roles_to_faces(
        surfaces, x_min, x_max, threshold, tolerance, debug
    )

    axis_index = max(range(3), key=lambda i: abs(velocity[i]))
    is_positive_flow = velocity[axis_index] > 0

    bbox = gmsh.model.getBoundingBox(3, 1)
    min_bounds = [bbox[0], bbox[1], bbox[2]]  # x_min, y_min, z_min
    max_bounds = [bbox[3], bbox[4], bbox[5]]  # x_max, y_max, z_max

    if flow_region == "internal":
        return generate_internal_bc_blocks(
            surfaces, face_geometry_data, face_roles, velocity, pressure,
            no_slip, axis_index, is_positive_flow, min_bounds, max_bounds, debug
        )
    else:
        for face_id in face_roles:
            face_roles[face_id] = ("wall", "wall")
        return generate_external_bc_blocks(
            surfaces, face_roles, velocity, pressure,
            no_slip, axis_index, is_positive_flow, debug
        )



