// ----------------------------------------------------------------------
// GMSH SCRIPT: ROBUST BOUNDARY ASSIGNMENT VIA PHYSICAL GROUPS
// This logic defines Inlet/Outlet based on stable coordinates (Xmin/Xmax),
// which is immune to the mesh distortions caused by broken geometry.
// ----------------------------------------------------------------------

// Tolerance for floating point comparison (critical for boundary box check)
Epsilon = 1e-4;

// 1. Get the bounding box of the entire geometry (tags 0, 0, 0 finds the whole model)
BB_Total = GetBoundingBox(0, 0, 0, 0, 0, 0, 0);
Xmin_Total = BB_Total.XMin;
Xmax_Total = BB_Total.XMax;

// 2. Initialize lists for the three groups
InletSurfaces[] = {};
OutletSurfaces[] = {};
WallSurfaces[] = {};

// Get a list of all Surfaces in the model (GMSH entity tag 2)
AllSurfaces[] = SelectionByTag(2);

For i In {0:#AllSurfaces[]-1}
Tag = AllSurfaces[i];

// Get the bounding box for the current Surface
BB_Surface = GetBoundingBox(2, Tag, 0, 0, 0, 0, 0, 0);

// --- Classification Logic ---

// Inlet: Check if the surface is at the global Xmin
If (Abs(BB_Surface.XMin - Xmin_Total) < Epsilon)
    InletSurfaces[] += {Tag};

// Outlet: Check if the surface is at the global Xmax
Else If (Abs(BB_Surface.XMax - Xmax_Total) < Epsilon)
    OutletSurfaces[] += {Tag};

// Wall: Otherwise, it is a Wall
Else
    WallSurfaces[] += {Tag};
EndIf

EndFor

// 3. Create the Physical Groups using stable integer IDs.
// These IDs (1, 2, 3) are what your Python script must read from the .msh file.

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


