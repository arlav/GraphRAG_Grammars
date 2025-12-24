"""
Basic Euclidean Shapes for Graph Grammar System

This module defines parametric 2D shapes with:
- Pure geometric definitions (no graphics dependencies)
- Immutable dataclasses (functional approach)
- TopologicPy integration (bidirectional conversion)
- Simple operations (subdivision, merging, transformation)

Philosophy: Start simple, build up. Rectangles and squares only for now.
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Any
import math


# =============================================================================
# BASIC GEOMETRIC PRIMITIVES
# =============================================================================

@dataclass(frozen=True)
class Point:
    """
    Immutable 2D point.

    Examples:
        >>> p = Point(3.0, 4.0)
        >>> p.distance_to(Point(0, 0))
        5.0
    """
    x: float
    y: float

    def distance_to(self, other: 'Point') -> float:
        """Euclidean distance to another point."""
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)

    def translate(self, dx: float, dy: float) -> 'Point':
        """Return new point translated by (dx, dy)."""
        return Point(self.x + dx, self.y + dy)

    def to_tuple(self) -> Tuple[float, float]:
        """Convert to tuple for compatibility."""
        return (self.x, self.y)

    @classmethod
    def from_tuple(cls, t: Tuple[float, float]) -> 'Point':
        """Create point from tuple."""
        return cls(t[0], t[1])


@dataclass(frozen=True)
class Segment:
    """
    Immutable line segment defined by two points.

    Examples:
        >>> seg = Segment(Point(0, 0), Point(4, 3))
        >>> seg.length()
        5.0
        >>> seg.midpoint()
        Point(x=2.0, y=1.5)
    """
    start: Point
    end: Point

    def length(self) -> float:
        """Length of the segment."""
        return self.start.distance_to(self.end)

    def midpoint(self) -> Point:
        """Midpoint of the segment."""
        return Point(
            (self.start.x + self.end.x) / 2,
            (self.start.y + self.end.y) / 2
        )

    def is_horizontal(self, tolerance: float = 1e-6) -> bool:
        """Check if segment is horizontal."""
        return abs(self.start.y - self.end.y) < tolerance

    def is_vertical(self, tolerance: float = 1e-6) -> bool:
        """Check if segment is vertical."""
        return abs(self.start.x - self.end.x) < tolerance

    def direction_vector(self) -> Tuple[float, float]:
        """Direction vector from start to end."""
        return (self.end.x - self.start.x, self.end.y - self.start.y)


# =============================================================================
# RECTANGLE - THE FUNDAMENTAL SHAPE
# =============================================================================

@dataclass(frozen=True)
class Rectangle:
    """
    Immutable axis-aligned rectangle.

    The fundamental shape in our grammar system. Defined by:
    - width, height (dimensions)
    - origin (bottom-left corner)

    All other shapes can be decomposed into rectangles.

    Properties:
        - Immutable (functional approach)
        - Axis-aligned (no rotation for simplicity)
        - Origin at bottom-left (consistent coordinate system)
        - Counter-clockwise vertex ordering

    Examples:
        >>> rect = Rectangle(4.0, 3.0, Point(0, 0))
        >>> rect.area()
        12.0
        >>> rect.vertices()
        [Point(0,0), Point(4,0), Point(4,3), Point(0,3)]
    """
    width: float
    height: float
    origin: Point = field(default_factory=lambda: Point(0.0, 0.0))
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate dimensions."""
        if self.width <= 0 or self.height <= 0:
            raise ValueError(f"Dimensions must be positive: width={self.width}, height={self.height}")

    # -------------------------------------------------------------------------
    # Basic Properties
    # -------------------------------------------------------------------------

    def area(self) -> float:
        """Area of the rectangle."""
        return self.width * self.height

    def perimeter(self) -> float:
        """Perimeter of the rectangle."""
        return 2 * (self.width + self.height)

    def aspect_ratio(self) -> float:
        """Aspect ratio (width / height)."""
        return self.width / self.height

    def centroid(self) -> Point:
        """Center point of the rectangle."""
        return Point(
            self.origin.x + self.width / 2,
            self.origin.y + self.height / 2
        )

    def is_square(self, tolerance: float = 1e-6) -> bool:
        """Check if rectangle is a square."""
        return abs(self.width - self.height) < tolerance

    # -------------------------------------------------------------------------
    # Geometric Queries
    # -------------------------------------------------------------------------

    def vertices(self) -> List[Point]:
        """
        Four corner vertices in counter-clockwise order.
        Starting from origin (bottom-left).

        Returns:
            [bottom-left, bottom-right, top-right, top-left]
        """
        x, y = self.origin.x, self.origin.y
        return [
            Point(x, y),                        # Bottom-left
            Point(x + self.width, y),           # Bottom-right
            Point(x + self.width, y + self.height),  # Top-right
            Point(x, y + self.height)           # Top-left
        ]

    def edges(self) -> List[Segment]:
        """
        Four edges in counter-clockwise order.

        Returns:
            [bottom, right, top, left]
        """
        verts = self.vertices()
        return [
            Segment(verts[0], verts[1]),  # Bottom
            Segment(verts[1], verts[2]),  # Right
            Segment(verts[2], verts[3]),  # Top
            Segment(verts[3], verts[0])   # Left
        ]

    def bounds(self) -> Tuple[float, float, float, float]:
        """
        Bounding box as (min_x, min_y, max_x, max_y).

        For axis-aligned rectangles, this is just the rectangle itself.
        """
        return (
            self.origin.x,
            self.origin.y,
            self.origin.x + self.width,
            self.origin.y + self.height
        )

    def contains_point(self, p: Point) -> bool:
        """Check if point is inside rectangle (inclusive of boundary)."""
        min_x, min_y, max_x, max_y = self.bounds()
        return min_x <= p.x <= max_x and min_y <= p.y <= max_y

    # -------------------------------------------------------------------------
    # Transformations (return new rectangles)
    # -------------------------------------------------------------------------

    def translate(self, dx: float, dy: float) -> 'Rectangle':
        """Translate rectangle by (dx, dy)."""
        new_origin = self.origin.translate(dx, dy)
        return Rectangle(self.width, self.height, new_origin, self.metadata.copy())

    def scale(self, scale_x: float, scale_y: Optional[float] = None) -> 'Rectangle':
        """
        Scale rectangle by factors.

        Args:
            scale_x: X-axis scale factor
            scale_y: Y-axis scale factor (defaults to scale_x for uniform scaling)
        """
        if scale_y is None:
            scale_y = scale_x

        return Rectangle(
            self.width * scale_x,
            self.height * scale_y,
            self.origin,
            self.metadata.copy()
        )

    def with_metadata(self, **kwargs) -> 'Rectangle':
        """Return new rectangle with updated metadata."""
        new_metadata = self.metadata.copy()
        new_metadata.update(kwargs)
        return Rectangle(self.width, self.height, self.origin, new_metadata)

    # -------------------------------------------------------------------------
    # Subdivision Operations (core grammar operations)
    # -------------------------------------------------------------------------

    def subdivide_horizontal(self, ratio: float = 0.5) -> Tuple['Rectangle', 'Rectangle']:
        """
        Subdivide rectangle horizontally (left | right).

        Args:
            ratio: Position of split (0 < ratio < 1)
                  0.5 = split in middle
                  0.3 = left is 30%, right is 70%

        Returns:
            (left_rect, right_rect)

        Examples:
            >>> rect = Rectangle(10, 8, Point(0, 0))
            >>> left, right = rect.subdivide_horizontal(0.4)
            >>> left.width, right.width
            (4.0, 6.0)
            >>> left.area() + right.area() == rect.area()
            True
        """
        if not 0 < ratio < 1:
            raise ValueError(f"Ratio must be in (0, 1), got {ratio}")

        split_width = self.width * ratio

        left = Rectangle(
            width=split_width,
            height=self.height,
            origin=self.origin,
            metadata={**self.metadata, 'subdivision': 'horizontal_left', 'ratio': ratio}
        )

        right = Rectangle(
            width=self.width - split_width,
            height=self.height,
            origin=Point(self.origin.x + split_width, self.origin.y),
            metadata={**self.metadata, 'subdivision': 'horizontal_right', 'ratio': 1-ratio}
        )

        return left, right

    def subdivide_vertical(self, ratio: float = 0.5) -> Tuple['Rectangle', 'Rectangle']:
        """
        Subdivide rectangle vertically (bottom | top).

        Args:
            ratio: Position of split (0 < ratio < 1)
                  0.5 = split in middle
                  0.3 = bottom is 30%, top is 70%

        Returns:
            (bottom_rect, top_rect)
        """
        if not 0 < ratio < 1:
            raise ValueError(f"Ratio must be in (0, 1), got {ratio}")

        split_height = self.height * ratio

        bottom = Rectangle(
            width=self.width,
            height=split_height,
            origin=self.origin,
            metadata={**self.metadata, 'subdivision': 'vertical_bottom', 'ratio': ratio}
        )

        top = Rectangle(
            width=self.width,
            height=self.height - split_height,
            origin=Point(self.origin.x, self.origin.y + split_height),
            metadata={**self.metadata, 'subdivision': 'vertical_top', 'ratio': 1-ratio}
        )

        return bottom, top

    def subdivide_grid(self, rows: int, cols: int) -> List[List['Rectangle']]:
        """
        Subdivide into uniform grid.

        Args:
            rows: Number of rows
            cols: Number of columns

        Returns:
            2D list of rectangles (row-major order)
            result[row][col] is the rectangle at (row, col)
        """
        cell_width = self.width / cols
        cell_height = self.height / rows

        grid = []
        for row in range(rows):
            row_rects = []
            for col in range(cols):
                origin = Point(
                    self.origin.x + col * cell_width,
                    self.origin.y + row * cell_height
                )
                cell = Rectangle(
                    width=cell_width,
                    height=cell_height,
                    origin=origin,
                    metadata={
                        **self.metadata,
                        'grid_position': (row, col),
                        'grid_size': (rows, cols)
                    }
                )
                row_rects.append(cell)
            grid.append(row_rects)

        return grid

    # -------------------------------------------------------------------------
    # Spatial Relations
    # -------------------------------------------------------------------------

    def overlaps(self, other: 'Rectangle', tolerance: float = 1e-6) -> bool:
        """Check if this rectangle overlaps with another."""
        min_x1, min_y1, max_x1, max_y1 = self.bounds()
        min_x2, min_y2, max_x2, max_y2 = other.bounds()

        # No overlap if one is to the left/right/above/below the other
        if max_x1 <= min_x2 + tolerance:  # self is left of other
            return False
        if min_x1 >= max_x2 - tolerance:  # self is right of other
            return False
        if max_y1 <= min_y2 + tolerance:  # self is below other
            return False
        if min_y1 >= max_y2 - tolerance:  # self is above other
            return False

        return True

    def is_adjacent_to(self, other: 'Rectangle', tolerance: float = 0.1) -> bool:
        """
        Check if rectangles share a boundary.

        Two rectangles are adjacent if they share an edge (or part of an edge)
        without overlapping.
        """
        # Check vertical adjacency (left-right)
        if abs(self.origin.x + self.width - other.origin.x) < tolerance:
            # self's right edge touches other's left edge
            # Check y-overlap
            y_overlap = min(
                self.origin.y + self.height,
                other.origin.y + other.height
            ) - max(self.origin.y, other.origin.y)
            if y_overlap > 0:
                return True

        if abs(other.origin.x + other.width - self.origin.x) < tolerance:
            # other's right edge touches self's left edge
            y_overlap = min(
                self.origin.y + self.height,
                other.origin.y + other.height
            ) - max(self.origin.y, other.origin.y)
            if y_overlap > 0:
                return True

        # Check horizontal adjacency (top-bottom)
        if abs(self.origin.y + self.height - other.origin.y) < tolerance:
            # self's top edge touches other's bottom edge
            x_overlap = min(
                self.origin.x + self.width,
                other.origin.x + other.width
            ) - max(self.origin.x, other.origin.x)
            if x_overlap > 0:
                return True

        if abs(other.origin.y + other.height - self.origin.y) < tolerance:
            # other's top edge touches self's bottom edge
            x_overlap = min(
                self.origin.x + self.width,
                other.origin.x + other.width
            ) - max(self.origin.x, other.origin.x)
            if x_overlap > 0:
                return True

        return False

    def shared_boundary(self, other: 'Rectangle', tolerance: float = 0.1) -> Optional[Segment]:
        """
        Get the shared boundary segment between adjacent rectangles.

        Returns None if rectangles are not adjacent.
        """
        # Check right edge of self with left edge of other
        if abs(self.origin.x + self.width - other.origin.x) < tolerance:
            y_min = max(self.origin.y, other.origin.y)
            y_max = min(self.origin.y + self.height, other.origin.y + other.height)
            if y_max > y_min:
                x = self.origin.x + self.width
                return Segment(Point(x, y_min), Point(x, y_max))

        # Check left edge of self with right edge of other
        if abs(other.origin.x + other.width - self.origin.x) < tolerance:
            y_min = max(self.origin.y, other.origin.y)
            y_max = min(self.origin.y + self.height, other.origin.y + other.height)
            if y_max > y_min:
                x = self.origin.x
                return Segment(Point(x, y_min), Point(x, y_max))

        # Check top edge of self with bottom edge of other
        if abs(self.origin.y + self.height - other.origin.y) < tolerance:
            x_min = max(self.origin.x, other.origin.x)
            x_max = min(self.origin.x + self.width, other.origin.x + other.width)
            if x_max > x_min:
                y = self.origin.y + self.height
                return Segment(Point(x_min, y), Point(x_max, y))

        # Check bottom edge of self with top edge of other
        if abs(other.origin.y + other.height - self.origin.y) < tolerance:
            x_min = max(self.origin.x, other.origin.x)
            x_max = min(self.origin.x + self.width, other.origin.x + other.width)
            if x_max > x_min:
                y = self.origin.y
                return Segment(Point(x_min, y), Point(x_max, y))

        return None

    # -------------------------------------------------------------------------
    # Serialization
    # -------------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'type': 'rectangle',
            'width': self.width,
            'height': self.height,
            'origin': {'x': self.origin.x, 'y': self.origin.y},
            'area': self.area(),
            'aspect_ratio': self.aspect_ratio(),
            'vertices': [{'x': p.x, 'y': p.y} for p in self.vertices()],
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'Rectangle':
        """Create rectangle from dictionary."""
        origin = Point(d['origin']['x'], d['origin']['y'])
        metadata = d.get('metadata', {})
        return cls(d['width'], d['height'], origin, metadata)


# =============================================================================
# SQUARE - SPECIAL CASE OF RECTANGLE
# =============================================================================

class Square(Rectangle):
    """
    Immutable square (special case of rectangle).

    Convenience class for when width == height.

    Examples:
        >>> sq = Square(5.0, Point(0, 0))
        >>> sq.area()
        25.0
        >>> sq.is_square()
        True
    """
    def __init__(self, size: float, origin: Point = Point(0.0, 0.0), metadata: Dict[str, Any] = None):
        """Create square with given size."""
        if metadata is None:
            metadata = {}
        # Use object.__setattr__ because parent dataclass is frozen
        object.__setattr__(self, 'width', size)
        object.__setattr__(self, 'height', size)
        object.__setattr__(self, 'origin', origin)
        object.__setattr__(self, 'metadata', {**metadata, 'is_square': True})


# =============================================================================
# POLYGON - GENERAL SHAPE (FUTURE)
# =============================================================================

class Polygon:
    """
    Immutable polygon defined by vertices.

    General polygon for future extensions (L-shapes, etc.).
    For now, just a placeholder with basic functionality.

    Examples:
        >>> triangle = Polygon([Point(0,0), Point(4,0), Point(2,3)])
        >>> len(triangle.vertices)
        3
    """
    def __init__(self, vertices: List[Point], metadata: Dict[str, Any] = None):
        """Create polygon from vertex list."""
        if len(vertices) < 3:
            raise ValueError("Polygon must have at least 3 vertices")

        if metadata is None:
            metadata = {}

        object.__setattr__(self, 'vertices', tuple(vertices))
        object.__setattr__(self, 'metadata', metadata)

    def edges(self) -> List[Segment]:
        """Get edges of polygon."""
        n = len(self.vertices)
        return [
            Segment(self.vertices[i], self.vertices[(i + 1) % n])
            for i in range(n)
        ]

    def bounds(self) -> Tuple[float, float, float, float]:
        """Bounding box (min_x, min_y, max_x, max_y)."""
        xs = [v.x for v in self.vertices]
        ys = [v.y for v in self.vertices]
        return (min(xs), min(ys), max(xs), max(ys))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'type': 'polygon',
            'vertices': [{'x': v.x, 'y': v.y} for v in self.vertices],
            'metadata': self.metadata
        }


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def merge_rectangles_bounding_box(rects: List[Rectangle]) -> Rectangle:
    """
    Merge multiple rectangles into their bounding box.

    Note: This creates a bounding box, not a precise merge.
    May include empty space if rectangles are not aligned.

    Args:
        rects: List of rectangles to merge

    Returns:
        Bounding box rectangle containing all input rectangles
    """
    if not rects:
        raise ValueError("Cannot merge empty list of rectangles")

    # Get all bounds
    all_bounds = [r.bounds() for r in rects]

    # Compute bounding box
    min_x = min(b[0] for b in all_bounds)
    min_y = min(b[1] for b in all_bounds)
    max_x = max(b[2] for b in all_bounds)
    max_y = max(b[3] for b in all_bounds)

    return Rectangle(
        width=max_x - min_x,
        height=max_y - min_y,
        origin=Point(min_x, min_y),
        metadata={'merged_from': len(rects)}
    )


def rectangles_to_polygon(rects: List[Rectangle]) -> Polygon:
    """
    Convert list of rectangles to single polygon.

    This is a simple union that creates a bounding polygon.
    For now, just returns bounding box vertices.

    Future: Use proper boolean union for complex shapes.
    """
    bbox = merge_rectangles_bounding_box(rects)
    return Polygon(bbox.vertices(), metadata={'source': 'rectangles_union'})


# =============================================================================
# TOPOLOGICPY INTEGRATION (FUTURE)
# =============================================================================

def rectangle_to_topologic_face(rect: Rectangle):
    """
    Convert Rectangle to TopologicPy Face.

    Note: Import here to avoid hard dependency on TopologicPy.
    """
    try:
        from topologicpy.Vertex import Vertex
        from topologicpy.Wire import Wire
        from topologicpy.Face import Face
        from topologicpy.Dictionary import Dictionary
        from topologicpy.Topology import Topology
    except ImportError:
        raise ImportError(
            "TopologicPy not installed. "
            "Install with: pip install topologicpy"
        )

    # Create vertices
    tp_vertices = [
        Vertex.ByCoordinates(p.x, p.y, 0.0)
        for p in rect.vertices()
    ]

    # Create wire (closed loop)
    wire = Wire.ByVertices(tp_vertices, close=True)

    # Create face
    face = Face.ByWire(wire)

    # Attach metadata
    metadata = {
        'shape_type': 'rectangle',
        'width': rect.width,
        'height': rect.height,
        'area': rect.area(),
        'origin_x': rect.origin.x,
        'origin_y': rect.origin.y,
        **rect.metadata
    }

    dict_obj = Dictionary.ByKeysValues(
        list(metadata.keys()),
        list(metadata.values())
    )
    face = Topology.SetDictionary(face, dict_obj)

    return face


def topologic_face_to_rectangle(face) -> Rectangle:
    """
    Extract Rectangle from TopologicPy Face.

    Assumes face was created from a rectangle.
    """
    try:
        from topologicpy.Dictionary import Dictionary
        from topologicpy.Topology import Topology
    except ImportError:
        raise ImportError(
            "TopologicPy not installed. "
            "Install with: pip install topologicpy"
        )

    # Get metadata
    dict_obj = Topology.Dictionary(face)
    if dict_obj is None:
        raise ValueError("Face has no dictionary metadata")

    metadata = {
        k: Dictionary.ValueAtKey(dict_obj, k)
        for k in Dictionary.Keys(dict_obj)
    }

    # Reconstruct rectangle
    return Rectangle(
        width=metadata['width'],
        height=metadata['height'],
        origin=Point(metadata['origin_x'], metadata['origin_y']),
        metadata={k: v for k, v in metadata.items()
                 if k not in ['shape_type', 'width', 'height', 'area', 'origin_x', 'origin_y']}
    )
