"""
Graph Grammar System for Shape Transformations

This module implements a rule-based system where graph transformations
drive shape transformations using TopologicPy primitives.

REFACTORED ARCHITECTURE:
- All geometry as TopologicPy Faces (no custom Rectangle classes)
- All topology as TopologicPy Graph (no networkx dependency)
- Helper functions for ergonomic Face creation
- GraphShape stores Cluster + Graph natively
"""

__version__ = "0.2.0"

# TopologicPy helpers (NEW)
from .topologic_helpers import (
    rectangular_face,
    square_face,
    get_metadata,
    set_metadata,
    get_all_metadata,
    face_centroid,
    faces_adjacent,
    faces_overlap,
    face_area,
    faces_bounding_box,
    graph_from_faces_and_adjacencies,
    vertex_coordinates,
    vertex_at,
)

# Graph-shape rules (REFACTORED)
from .rules import (
    GraphShape,
    GraphShapeRule,
    RuleLibrary,
)

__all__ = [
    # TopologicPy Helpers
    "rectangular_face",
    "square_face",
    "get_metadata",
    "set_metadata",
    "get_all_metadata",
    "face_centroid",
    "faces_adjacent",
    "faces_overlap",
    "face_area",
    "faces_bounding_box",
    "graph_from_faces_and_adjacencies",
    "vertex_coordinates",
    "vertex_at",
    # Rules
    "GraphShape",
    "GraphShapeRule",
    "RuleLibrary",
]
