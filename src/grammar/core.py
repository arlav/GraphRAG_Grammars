"""
Core data structures for the shape grammar engine - Phase 4 Refactored

ARCHITECTURE (Phase 4):
- LayoutState: Mutable transformation substrate for shape grammar pipeline
- Shape: Thin wrapper around TopologicPy Face with property accessors
- ALL metadata stored in TopologicPy Dictionary (single source of truth)
- ALL helpers imported from topologic_helpers.py (zero duplication)

CHANGES FROM PHASE 3:
- ✅ Removed duplicate helper functions (imported from topologic_helpers)
- ✅ Removed shape builders (moved to topologic_helpers)
- ✅ Removed dual metadata storage (Dictionary only)
- ✅ Shape class is now just property accessors over Face Dictionary

Author: GraphRAG Shape Grammar Engine
Date: 2025-12-31 (Phase 4 Refactor)
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Tuple, Optional, Any
import copy

# TopologicPy imports
from topologicpy.Face import Face
from topologicpy.Vertex import Vertex
from topologicpy.Edge import Edge

# Import ALL helpers from topologic_helpers (no duplication!)
from .topologic_helpers import (
    # Face creation builders
    rectangular_face,
    square_face,
    circle_face,
    lshape_face,
    tshape_face,
    ushape_face,
    polygon_face,

    # Metadata utilities
    get_metadata,
    set_metadata,
    get_all_metadata,

    # Geometry queries
    face_centroid,
    face_area,
    faces_adjacent,
    faces_overlap,
    faces_bounding_box,
    vertex_coordinates,

    # Shape recognition
    recognize_shape_type,
)


# ============================================================================
# ENUMERATIONS
# ============================================================================

class Phase(Enum):
    """Transformation phases in the shape grammar pipeline."""
    BUBBLE = 1      # Initial circle packing from graph
    RECTANGLES = 2  # Circles converted to rectangles
    ARRANGED = 3    # Rectangles aligned and arranged
    REFINED = 4     # Final refinement and validation


class ShapeType(Enum):
    """Shape type classification for geometry recognition."""
    CIRCLE = auto()
    RECTANGLE = auto()
    L_SHAPE = auto()
    T_SHAPE = auto()
    U_SHAPE = auto()
    POLYGON = auto()


# ============================================================================
# SHAPE WRAPPER (Thin accessor around TopologicPy Face)
# ============================================================================

@dataclass
class Shape:
    """
    Lightweight wrapper around TopologicPy Face.

    ALL metadata stored in Face's TopologicPy Dictionary (single source of truth).
    No dual storage - Shape provides only property accessors for ergonomics.

    Required Dictionary keys:
        - 'shape_id': Unique identifier (str)
        - 'room_type': Room label (str)
        - 'target_area': Target area in m² (float)
        - 'shape_type': ShapeType name as string (str)

    The Shape object itself stores NO data except the Face reference.
    All properties read directly from Face.Dictionary on each access.

    Example:
        >>> # Create face with metadata
        >>> face = rectangular_face(
        ...     5, 4,
        ...     label="Kitchen",
        ...     shape_id="s1",
        ...     room_type="Kitchen",
        ...     target_area=20
        ... )
        >>> # Wrap in Shape
        >>> shape = Shape(face)
        >>> shape.id            # Reads from Dictionary
        's1'
        >>> shape.room_type     # Reads from Dictionary
        'Kitchen'
        >>> shape.area          # Computed from Face geometry
        20.0
        >>> shape.set(floor=2)  # Updates Dictionary
    """
    face: Face  # TopologicPy Face (contains ALL metadata in Dictionary)

    # --- Convenience Properties (read from Dictionary) ---

    @property
    def id(self) -> str:
        """Shape ID from Dictionary."""
        return get_metadata(self.face, "shape_id", "unknown")

    @property
    def room_type(self) -> str:
        """Room type from Dictionary."""
        return get_metadata(self.face, "room_type", "Unknown")

    @property
    def target_area(self) -> float:
        """Target area from Dictionary."""
        return get_metadata(self.face, "target_area", 0.0)

    @property
    def shape_type(self) -> ShapeType:
        """
        Shape type from Dictionary, with fallback to geometry recognition.

        Returns ShapeType enum value.
        """
        type_str = get_metadata(self.face, "shape_type")
        if type_str:
            try:
                return ShapeType[type_str]
            except KeyError:
                pass

        # Fallback: recognize from geometry
        type_str = recognize_shape_type(self.face)
        return ShapeType[type_str]

    @property
    def area(self) -> float:
        """Actual area computed from Face geometry."""
        return face_area(self.face)

    @property
    def centroid(self) -> Vertex:
        """Centroid as TopologicPy Vertex."""
        return face_centroid(self.face)

    @property
    def centroid_xy(self) -> Tuple[float, float]:
        """Centroid as (x, y) tuple for convenience."""
        c = self.centroid
        x, y, z = vertex_coordinates(c)
        return (x, y)

    # --- Metadata Modification ---

    def set(self, **kwargs) -> None:
        """
        Update metadata in Face's Dictionary.

        Modifies the Face in-place by creating new Dictionary with updated values.

        Args:
            **kwargs: Key-value pairs to set in Dictionary

        Example:
            >>> shape.set(room_type="Living", floor=2, has_window=True)
        """
        self.face = set_metadata(self.face, **kwargs)

    def get(self, key: str, default=None):
        """
        Get metadata value from Face's Dictionary.

        Args:
            key: Metadata key to retrieve
            default: Value to return if key not found

        Returns:
            Metadata value or default
        """
        return get_metadata(self.face, key, default)

    def all_metadata(self) -> Dict[str, Any]:
        """
        Get all metadata as Python dict.

        Returns:
            Dictionary of all metadata key-value pairs
        """
        return get_all_metadata(self.face)

    # --- Validation ---

    def area_error(self) -> float:
        """
        Relative error between actual and target area.

        Returns:
            Error as fraction (0.1 = 10% error)
        """
        if self.target_area <= 0:
            return 0.0
        return abs(self.area - self.target_area) / self.target_area

    # --- Geometry Queries ---

    def vertices(self) -> List[Vertex]:
        """Get Face vertices."""
        return Face.Vertices(self.face)

    def edges(self) -> List[Edge]:
        """Get Face edges."""
        return Face.Edges(self.face)

    def __repr__(self) -> str:
        return (
            f"Shape(id={self.id}, "
            f"type={self.shape_type.name}, "
            f"room={self.room_type}, "
            f"area={self.area:.1f}m²)"
        )


# ============================================================================
# LAYOUT EDGE
# ============================================================================

@dataclass
class LayoutEdge:
    """
    Lightweight edge between shapes in layout.

    Represents adjacency or connection relationships without full TopologicPy Graph.
    Useful for mutable transformations where topology is tracked but not geometry.

    Attributes:
        source_id: Source shape ID
        target_id: Target shape ID
        relation: Relationship type (e.g., "CONNECTS", "ADJACENT")
    """
    source_id: str
    target_id: str
    relation: str = "CONNECTS"

    def __repr__(self) -> str:
        return f"{self.source_id} --{self.relation}→ {self.target_id}"


# ============================================================================
# LAYOUT STATE (Transformation Substrate)
# ============================================================================

@dataclass
class LayoutState:
    """
    Mutable transformation substrate for shape grammar pipeline.

    Stores collection of Shapes (Face wrappers) and edges (adjacency relationships).
    Designed for incremental transformations through phases:
        BUBBLE → RECTANGLES → ARRANGED → REFINED

    All geometric data stored in TopologicPy Faces.
    All metadata stored in TopologicPy Dictionaries.
    Edges are lightweight (ID pairs) rather than full TopologicPy Graph.

    Attributes:
        phase: Current transformation phase
        shapes: Dictionary mapping shape_id → Shape
        edges: List of LayoutEdge connections
        is_valid: Validation status (updated by validate())
        metadata: Custom metadata for entire layout

    Example:
        >>> # Create layout
        >>> layout = LayoutState(phase=Phase.BUBBLE)
        >>>
        >>> # Add shapes
        >>> face1 = circle_face(0, 0, 2.5, shape_id="s1", room_type="Kitchen", target_area=20)
        >>> layout.add_shape(Shape(face1))
        >>>
        >>> # Add edges
        >>> layout.add_edge(LayoutEdge("s1", "s2"))
        >>>
        >>> # Transform
        >>> layout.phase = Phase.RECTANGLES
        >>> # ... apply transformations ...
        >>>
        >>> # Validate
        >>> issues = layout.validate()
    """
    phase: Phase = Phase.BUBBLE
    shapes: Dict[str, Shape] = field(default_factory=dict)
    edges: List[LayoutEdge] = field(default_factory=list)
    is_valid: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    # ────────────────────────────────────────────────────────────
    # SHAPE MANAGEMENT
    # ────────────────────────────────────────────────────────────

    def add_shape(self, shape: Shape) -> None:
        """
        Add shape to layout.

        Args:
            shape: Shape instance to add
        """
        self.shapes[shape.id] = shape
        self.is_valid = False

    def remove_shape(self, shape_id: str) -> None:
        """
        Remove shape and all connected edges.

        Args:
            shape_id: ID of shape to remove
        """
        if shape_id in self.shapes:
            del self.shapes[shape_id]

        # Remove all edges connected to this shape
        self.edges = [
            e for e in self.edges
            if e.source_id != shape_id and e.target_id != shape_id
        ]
        self.is_valid = False

    # ────────────────────────────────────────────────────────────
    # EDGE MANAGEMENT
    # ────────────────────────────────────────────────────────────

    def add_edge(self, edge: LayoutEdge) -> None:
        """
        Add edge between shapes.

        Args:
            edge: LayoutEdge to add

        Raises:
            ValueError: If source or target shape not found
        """
        if edge.source_id not in self.shapes:
            raise ValueError(f"Source shape '{edge.source_id}' not found")
        if edge.target_id not in self.shapes:
            raise ValueError(f"Target shape '{edge.target_id}' not found")

        self.edges.append(edge)
        self.is_valid = False

    def get_neighbors(self, shape_id: str) -> List[str]:
        """
        Get IDs of neighboring shapes (connected by edges).

        Args:
            shape_id: Shape ID to query

        Returns:
            List of neighbor shape IDs
        """
        neighbors = []
        for edge in self.edges:
            if edge.source_id == shape_id:
                neighbors.append(edge.target_id)
            elif edge.target_id == shape_id:
                neighbors.append(edge.source_id)
        return neighbors

    def get_edges_for_shape(self, shape_id: str) -> List[LayoutEdge]:
        """
        Get all edges connected to a shape.

        Args:
            shape_id: Shape ID to query

        Returns:
            List of connected edges
        """
        return [
            e for e in self.edges
            if e.source_id == shape_id or e.target_id == shape_id
        ]

    # ────────────────────────────────────────────────────────────
    # GEOMETRY QUERIES (using TopologicPy via helpers)
    # ────────────────────────────────────────────────────────────

    def bounds(self) -> Tuple[float, float, float, float]:
        """
        Compute bounding box of all shapes.

        Returns:
            (min_x, min_y, max_x, max_y)
        """
        if not self.shapes:
            return (0, 0, 0, 0)

        faces = [shape.face for shape in self.shapes.values()]
        return faces_bounding_box(faces)

    def total_area(self) -> float:
        """
        Compute total area of all shapes.

        Returns:
            Sum of all shape areas in m²
        """
        return sum(shape.area for shape in self.shapes.values())

    # ────────────────────────────────────────────────────────────
    # VALIDATION
    # ────────────────────────────────────────────────────────────

    def validate(self, area_tolerance: float = 0.10) -> Dict[str, List[str]]:
        """
        Validate layout state.

        Checks:
        1. All shapes have positive area
        2. Area preservation (actual vs target within tolerance)
        3. Edges reference existing shapes

        Note: Geometric validation (overlaps, gaps) requires conversion
        to GraphShape which has TopologicPy's geometric methods.
        Use converters.validate_layout_with_graph_shape() for full validation.

        Args:
            area_tolerance: Acceptable relative error (default 10%)

        Returns:
            Dictionary of validation issues by category
        """
        issues = {
            'invalid_geometry': [],
            'area_mismatch': [],
            'invalid_edges': []
        }

        # Check shapes
        for shape_id, shape in self.shapes.items():
            # Geometry validity
            if shape.area <= 0:
                issues['invalid_geometry'].append(
                    f"{shape_id}: Non-positive area ({shape.area:.2f}m²)"
                )

            # Area preservation
            error = shape.area_error()
            if error > area_tolerance:
                issues['area_mismatch'].append(
                    f"{shape_id} ({shape.room_type}): "
                    f"area={shape.area:.2f}m² vs target={shape.target_area:.2f}m² "
                    f"(error: {error*100:.1f}%)"
                )

        # Check edges
        for edge in self.edges:
            if edge.source_id not in self.shapes:
                issues['invalid_edges'].append(
                    f"Edge references missing source: {edge.source_id}"
                )
            if edge.target_id not in self.shapes:
                issues['invalid_edges'].append(
                    f"Edge references missing target: {edge.target_id}"
                )

        # Update is_valid flag
        self.is_valid = all(len(v) == 0 for v in issues.values())

        return issues

    # ────────────────────────────────────────────────────────────
    # UTILITY METHODS
    # ────────────────────────────────────────────────────────────

    def copy(self) -> 'LayoutState':
        """Create a deep copy of this layout state."""
        return copy.deepcopy(self)

    def __repr__(self) -> str:
        return (
            f"LayoutState(phase={self.phase.name}, "
            f"shapes={len(self.shapes)}, "
            f"edges={len(self.edges)}, "
            f"valid={self.is_valid})"
        )


# ============================================================================
# CONVENIENCE CONSTRUCTORS
# ============================================================================

def create_shape_from_face(face: Face) -> Shape:
    """
    Create Shape wrapper from existing Face.

    Face must have required metadata in Dictionary:
    - shape_id (or label will be used)
    - room_type
    - target_area

    Args:
        face: TopologicPy Face with metadata

    Returns:
        Shape instance

    Example:
        >>> face = rectangular_face(5, 4, shape_id="s1", room_type="Kitchen", target_area=20)
        >>> shape = create_shape_from_face(face)
    """
    # Ensure shape_id exists (use label as fallback)
    if not get_metadata(face, "shape_id"):
        label = get_metadata(face, "label", "unknown")
        face = set_metadata(face, shape_id=label)

    # Ensure shape_type exists
    if not get_metadata(face, "shape_type"):
        shape_type_str = recognize_shape_type(face)
        face = set_metadata(face, shape_type=shape_type_str)

    return Shape(face)


def create_circle_shape(
    shape_id: str,
    room_type: str,
    center_x: float,
    center_y: float,
    radius: float,
    target_area: Optional[float] = None
) -> Shape:
    """
    Create circular Shape (convenience constructor).

    Args:
        shape_id: Unique identifier
        room_type: Room label
        center_x, center_y: Circle center
        radius: Circle radius
        target_area: Optional target area (defaults to πr²)

    Returns:
        Shape instance wrapping circular Face

    Example:
        >>> shape = create_circle_shape("s1", "Living", 0, 0, 3.0)
    """
    import math
    area = target_area if target_area is not None else math.pi * radius ** 2

    face = circle_face(
        center_x, center_y, radius,
        shape_id=shape_id,
        room_type=room_type,
        target_area=area,
        label=room_type
    )

    return Shape(face)


def create_rectangle_shape(
    shape_id: str,
    room_type: str,
    center_x: float,
    center_y: float,
    width: float,
    height: float,
    rotation: float = 0.0,
    target_area: Optional[float] = None
) -> Shape:
    """
    Create rectangular Shape (convenience constructor).

    Note: rectangular_face in topologic_helpers uses origin (bottom-left),
    so we convert from center coordinates.

    Args:
        shape_id: Unique identifier
        room_type: Room label
        center_x, center_y: Rectangle center
        width, height: Dimensions
        rotation: Rotation in degrees (not yet implemented in rectangular_face)
        target_area: Optional target area (defaults to width*height)

    Returns:
        Shape instance wrapping rectangular Face

    Example:
        >>> shape = create_rectangle_shape("s2", "Kitchen", 5, 5, 4, 3)
    """
    area = target_area if target_area is not None else width * height

    # Convert center coords to origin coords
    origin_x = center_x - width / 2
    origin_y = center_y - height / 2

    face = rectangular_face(
        width, height,
        origin=(origin_x, origin_y),
        shape_id=shape_id,
        room_type=room_type,
        target_area=area,
        label=room_type
    )

    # TODO: Apply rotation if needed
    # Current rectangular_face doesn't support rotation parameter
    # For now, rotation parameter is accepted but ignored

    return Shape(face)


# ============================================================================
# TRANSFORMATION HELPERS (Placeholders for future implementation)
# ============================================================================

def circle_to_rectangle(shape: Shape, aspect_ratio: float = 1.2) -> Shape:
    """
    Transform circle shape to rectangle preserving area.

    Args:
        shape: Circular shape to transform
        aspect_ratio: Width/height ratio (default 1.2)

    Returns:
        New rectangular shape with same area

    Raises:
        ValueError: If shape is not a circle

    Example:
        >>> circle = create_circle_shape("s1", "Kitchen", 0, 0, 2.5)
        >>> rectangle = circle_to_rectangle(circle)

    Note: This is a placeholder. Full implementation in transformation rules module.
    """
    if shape.shape_type != ShapeType.CIRCLE:
        raise ValueError(f"Can only transform circles, got {shape.shape_type}")

    import math

    # Get circle parameters
    radius = shape.get("radius", 1.0)
    center_x = shape.get("center_x", 0.0)
    center_y = shape.get("center_y", 0.0)
    area = shape.target_area

    # Calculate rectangle dimensions
    # area = width * height
    # aspect_ratio = width / height
    # => height = sqrt(area / aspect_ratio)
    # => width = aspect_ratio * height
    height = math.sqrt(area / aspect_ratio)
    width = aspect_ratio * height

    # Create rectangle at same center
    origin_x = center_x - width / 2
    origin_y = center_y - height / 2

    rect_face = rectangular_face(
        width, height,
        origin=(origin_x, origin_y),
        shape_id=shape.id,
        room_type=shape.room_type,
        target_area=area,
        shape_type="RECTANGLE",
        **shape.all_metadata()  # Preserve all metadata
    )

    return Shape(rect_face)
