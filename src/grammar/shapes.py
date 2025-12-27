"""
⚠️  DEPRECATED - This module is deprecated as of v0.2.0 ⚠️

This file contains the old Rectangle/Point/Square classes that have been
replaced with TopologicPy-native architecture.

MIGRATION GUIDE:
================

Import Changes:
- OLD: from grammar.shapes import Rectangle, Point
- NEW: from grammar.topologic_helpers import rectangular_face, get_metadata

Creating Shapes:
- OLD: rect = Rectangle(5, 4, Point(0, 0))
- NEW: face = rectangular_face(5, 4, origin=(0, 0), label="Room1")

Area:
- OLD: area = rect.area()
- NEW: area = face_area(face)

Centroid:
- OLD: centroid = rect.centroid()
- NEW: centroid = face_centroid(face)

Adjacency:
- OLD: rect1.is_adjacent_to(rect2)
- NEW: faces_adjacent(face1, face2)

Metadata:
- OLD: rect.metadata["key"]
- NEW: get_metadata(face, "key")

Graph-Shape Creation:
- OLD: GraphShape(shapes={'A': rect}, edges=[...])
- NEW: GraphShape.from_faces_and_adjacencies(faces=[face], adjacencies=[...])

The original code has been archived in:
  /src/grammar/archive/shapes_deprecated.py

For new code, use the TopologicPy-native helpers in topologic_helpers.py

Why the change?
===============
- Single source of truth (TopologicPy Faces, not Python objects)
- Leverages TopologicPy's proven geometry algorithms
- No conversion layer needed
- Simpler architecture (700+ lines → 300 lines of helpers)
- Metadata in TopologicPy Dictionary (not Python dicts)
"""

import warnings

warnings.warn(
    "The 'shapes' module is deprecated as of version 0.2.0. "
    "Use 'topologic_helpers' for TopologicPy-native geometry instead. "
    "See migration guide in this file's docstring.",
    DeprecationWarning,
    stacklevel=2
)

# Import from archive for backward compatibility
try:
    from .archive.shapes_deprecated import *
except ImportError:
    # Archive file doesn't exist yet, provide helpful error
    raise ImportError(
        "shapes module is deprecated. Please use topologic_helpers instead. "
        "See /src/grammar/shapes.py for migration guide."
    )
