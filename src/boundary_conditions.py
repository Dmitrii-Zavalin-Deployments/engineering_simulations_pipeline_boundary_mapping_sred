# src/boundary_conditions.py

import gmsh

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



