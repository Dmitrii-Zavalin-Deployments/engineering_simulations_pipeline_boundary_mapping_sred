// ----------------------------------------------------------------------
// GMSH SCRIPT: ROBUST BOUNDARY ASSIGNMENT VIA PHYSICAL GROUPS
// Fix: Corrected GetBoundingBox syntax to use array access [0] and [3].
// ----------------------------------------------------------------------

// Tolerance for floating point comparison (critical for boundary box check)
Epsilon = 1e-4;

// 1. Get the bounding box of the entire geometry.
// GetBoundingBox(0, 0) retrieves the bounding box for all entities.
// The result is an array: [Xmin, Ymin, Zmin, Xmax, Ymax, Zmax]
BB_Total[] = GetBoundingBox(0, 0);

// Access the array elements by index: 0 for Xmin, 3 for Xmax.
Xmin_Total = BB_Total[0];
Xmax_Total = BB_Total[3];

// 2. Initialize lists for the three groups
InletSurfaces[] = {};
OutletSurfaces[] = {};
WallSurfaces[] = {};

// Get a list of all Surfaces in the model (GMSH entity tag 2)
AllSurfaces[] = SelectionByTag(2);

For i In {0:#AllSurfaces[]-1}
Tag = AllSurfaces[i];

// Get the bounding box for the current Surface
// The result is an array: [Xmin, Ymin, Zmin, Xmax, Ymax, Zmax]
BB_Surface[] = GetBoundingBox(2, Tag);

// --- Classification Logic ---

// Inlet: Check if the surface is at the global Xmin (compare BB_Surface[0] vs Xmin_Total)
If (Abs(BB_Surface[0] - Xmin_Total) < Epsilon)
    InletSurfaces[] += {Tag};

// Outlet: Check if the surface is at the global Xmax (compare BB_Surface[3] vs Xmax_Total)
Else If (Abs(BB_Surface[3] - Xmax_Total) < Epsilon)
    OutletSurfaces[] += {Tag};

// Wall: Otherwise, it is a Wall
Else
    WallSurfaces[] += {Tag};
EndIf

EndFor

// 3. Create the Physical Groups using stable integer IDs.

If (#InletSurfaces[] > 0)
// Physical Tag 1 = Inlet (x_min)
Physical Surface(1) = InletSurfaces[];
EndIf

If (#OutletSurfaces[] > 0)
// Physical Tag 2 = Outlet (x_max)
Physical Surface(2) = OutletSurfaces[];
EndIf

If (#WallSurfaces[] > 0)
// Physical Tag 3 = Wall (The rest)
Physical Surface(3) = WallSurfaces[];
EndIf