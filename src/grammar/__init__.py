"""
Graph Grammar System for Shape Transformations

This module implements a rule-based system where graph transformations
drive shape transformations.
"""

__version__ = "0.1.0"

from .shapes import (
    Rectangle,
    Square,
    Polygon,
    Point,
    Segment,
)

from .rules import (
    GraphShapeRule,
    RuleLibrary,
    GraphShape,
)

__all__ = [
    # Shapes
    "Rectangle",
    "Square",
    "Polygon",
    "Point",
    "Segment",
    # Rules
    "GraphShapeRule",
    "RuleLibrary",
    "GraphShape",
]
