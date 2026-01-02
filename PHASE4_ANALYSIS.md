# Phase 4: Unified Architecture with TopologicPy Dictionary Metadata

**Date**: 2025-12-31
**Status**: 🚧 Planning & Implementation
**Goal**: Unify Phase 2 (rules.py) and Phase 3 (core.py) architectures while eliminating code duplication and standardizing on TopologicPy Dictionary for all metadata

---

## Executive Summary

Phase 4 consolidates the dual architectural evolution into a unified system that combines:
- **GraphShape** for immutable graph-centric transformations
- **LayoutState** for mutable geometry-centric pipelines
- **Shared utilities** (topologic_helpers.py) with extended shape builders
- **Single metadata source** (TopologicPy Dictionary only)
- **Bidirectional converters** for interoperability

### Key Changes

1. ✅ **Eliminate Duplication**: core.py imports from topologic_helpers.py (removes ~100 lines)
2. ✅ **Consolidate Builders**: Move all shape builders (circle, L, T, U) to topologic_helpers.py
3. ✅ **Create Converters**: New `converters.py` module for LayoutState ↔ GraphShape
4. ✅ **Metadata Strategy**: **TopologicPy Dictionary ONLY** (removes dual storage, single source of truth)

### Impact

- **Before**: 963 (core.py) + 575 (rules.py) + 439 (helpers) = **1,977 lines**
- **After**: ~600 (core.py) + 575 (rules.py) + ~650 (helpers) + ~200 (converters) = **~2,025 lines**
- **Net**: +48 lines BUT:
  - ✅ Zero duplication
  - ✅ Complete interoperability
  - ✅ Single metadata source
  - ✅ Shared shape builders

---

## Part 1: Metadata Architecture Decision

### Problem Statement

**Phase 2 Approach** (rules.py):
```python
# Single source: TopologicPy Dictionary
face = rectangular_face(5, 4, label="Kitchen", room_type="Kitchen")
room_type = get_metadata(face, "room_type")  # Read from Dictionary
```

**Phase 3 Approach** (core.py):
```python
# Dual storage: Python dict + TopologicPy Dictionary
shape = Shape(
    id="s1",
    face=face,
    room_type="Kitchen",      # Python attribute
    target_area=20.0,         # Python attribute
    metadata={"floor": 2}     # Python dict
)

# Can get out of sync!
shape.room_type = "Living"           # Python changed
get_metadata(shape.face, "room_type")  # Still "Kitchen"! 💥
```

### Decision: TopologicPy Dictionary Only

**Rationale**:

1. **Single Source of Truth**
   - Metadata persists through TopologicPy operations (merge, intersect, etc.)
   - No sync issues between Python objects and TopologicPy primitives
   - Serialization works automatically (TopologicPy export includes Dictionary)

2. **Consistency with Phase 2**
   - rules.py already uses this pattern successfully
   - Converters become trivial (no mapping layer needed)
   - GraphShape validation works directly on Faces

3. **Simplicity**
   - Less code (no sync methods needed)
   - Easier to reason about (one storage location)
   - Fewer bugs (can't have Python/Dictionary drift)

4. **Performance Trade-off Acceptable**
   - Dictionary access slower than Python attribute (~10x)
   - BUT: Most operations are geometric (TopologicPy), not metadata reads
   - Typical use: Read metadata once during transformation, not in tight loops

### New Shape Class Design

**Before** (Dual storage):
```python
@dataclass
class Shape:
    id: str
    face: Face
    room_type: str                # Python attribute
    target_area: float            # Python attribute
    shape_type: Optional[ShapeType] = None
    metadata: Dict[str, Any] = field(default_factory=dict)  # Python dict

    @property
    def area(self) -> float:
        return face_area(self.face)
```

**After** (TopologicPy Dictionary only):
```python
@dataclass
class Shape:
    """
    Lightweight wrapper around TopologicPy Face.

    ALL metadata stored in Face's TopologicPy Dictionary.
    Python attributes are just convenience accessors.

    Required Dictionary keys:
    - 'shape_id': Unique identifier (str)
    - 'room_type': Room label (str)
    - 'target_area': Target area in m² (float)
    - 'shape_type': ShapeType enum name (str)

    Optional Dictionary keys:
    - Any custom metadata
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
        """Shape type from Dictionary."""
        type_str = get_metadata(self.face, "shape_type")
        if type_str:
            return ShapeType[type_str]
        return recognize_shape_type(self.face)

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
        """Centroid as (x, y) tuple."""
        c = self.centroid
        x, y, z = vertex_coordinates(c)
        return (x, y)

    # --- Metadata Modification ---

    def set_metadata(self, **kwargs) -> None:
        """
        Update metadata in Face's Dictionary.

        Args:
            **kwargs: Key-value pairs to set

        Example:
            >>> shape.set_metadata(room_type="Living", floor=2)
        """
        self.face = set_metadata(self.face, **kwargs)

    def get_metadata(self, key: str, default=None):
        """Get metadata value from Face's Dictionary."""
        return get_metadata(self.face, key, default)

    def all_metadata(self) -> Dict[str, Any]:
        """Get all metadata as Python dict."""
        return get_all_metadata(self.face)

    # --- Area Validation ---

    def area_error(self) -> float:
        """Relative error between actual and target area."""
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
```

**Key Insight**: Shape becomes a **thin accessor wrapper** around Face. It provides ergonomic Python properties but stores nothing itself.

---

## Part 2: topologic_helpers.py Extensions

### New Shape Builders to Add

All builders from core.py move to topologic_helpers.py with consistent API:

```python
def circle_face(
    center_x: float,
    center_y: float,
    radius: float,
    num_segments: int = 32,
    label: Optional[str] = None,
    **metadata
) -> Face:
    """
    Create circular Face (polygon approximation).

    Args:
        center_x, center_y: Circle center
        radius: Radius
        num_segments: Polygon sides (default 32 for smooth circle)
        label: Optional label
        **metadata: Additional metadata for Dictionary

    Returns:
        Face with attached Dictionary

    Metadata automatically added:
        - label: If provided
        - center_x, center_y, radius: Geometry params
        - area: π*r²
        - shape_type: "CIRCLE"
    """
    # Generate polygon vertices
    vertices = []
    for i in range(num_segments):
        angle = 2 * math.pi * i / num_segments
        x = center_x + radius * math.cos(angle)
        y = center_y + radius * math.sin(angle)
        vertices.append(Vertex.ByCoordinates(x, y, 0))

    # Create wire and face
    from topologicpy.Wire import Wire
    wire = Wire.ByVertices(vertices, close=True)
    face = Face.ByWire(wire)

    # Build metadata
    meta = {
        "center_x": center_x,
        "center_y": center_y,
        "radius": radius,
        "area": math.pi * radius ** 2,
        "shape_type": "CIRCLE",
    }
    if label:
        meta["label"] = label
    meta.update(metadata)

    # Attach dictionary
    keys = list(meta.keys())
    values = list(meta.values())
    d = Dictionary.ByKeysValues(keys, values)
    face = Topology.SetDictionary(face, d)

    return face


def lshape_face(
    center_x: float,
    center_y: float,
    arm1_length: float,
    arm1_width: float,
    arm2_length: float,
    arm2_width: float,
    rotation: float = 0.0,
    label: Optional[str] = None,
    **metadata
) -> Face:
    """
    Create L-shaped Face.

    Configuration:
        ┌────────┐  ← arm1
        │        │
        │  ┌─────┘
        │  │ arm2
        │  │
        └──┘

    Returns:
        Face with 6 vertices, attached Dictionary

    Metadata automatically added:
        - shape_type: "L_SHAPE"
        - arm1_length, arm1_width, arm2_length, arm2_width
        - area: Computed from vertices
    """
    # (Implementation from core.py create_lshape_face)
    # ... vertex generation logic ...
    # ... metadata creation ...
    return face


def tshape_face(
    center_x: float,
    center_y: float,
    top_length: float,
    top_width: float,
    stem_length: float,
    stem_width: float,
    rotation: float = 0.0,
    label: Optional[str] = None,
    **metadata
) -> Face:
    """
    Create T-shaped Face.

    Configuration:
        ┌─────────┐ ← top
        │         │
        ├──┐  ┌───┤
           │  │ ← stem
           └──┘

    Returns:
        Face with 8 vertices, attached Dictionary

    Metadata automatically added:
        - shape_type: "T_SHAPE"
        - top_length, top_width, stem_length, stem_width
    """
    # (Implementation from core.py create_tshape_face)
    return face


def ushape_face(
    center_x: float,
    center_y: float,
    total_width: float,
    total_height: float,
    side_width: float,
    gap_width: float,
    rotation: float = 0.0,
    label: Optional[str] = None,
    **metadata
) -> Face:
    """
    Create U-shaped Face.

    Configuration:
        ┌───┐   ┌───┐
        │   │   │   │
        │   └───┘   │
        └───────────┘

    Returns:
        Face with 8 vertices, attached Dictionary

    Metadata automatically added:
        - shape_type: "U_SHAPE"
        - total_width, total_height, side_width, gap_width
    """
    # (Implementation from core.py create_ushape_face)
    return face


def polygon_face(
    vertices_coords: List[Tuple[float, float]],
    label: Optional[str] = None,
    **metadata
) -> Face:
    """
    Create generic polygon Face from vertex coordinates.

    Args:
        vertices_coords: List of (x, y) tuples
        label: Optional label
        **metadata: Additional metadata

    Returns:
        Face with attached Dictionary

    Metadata automatically added:
        - shape_type: "POLYGON"
        - num_vertices: Vertex count
        - area: Computed
    """
    # (Implementation from core.py create_polygon_face)
    return face
```

### New Shape Recognition Helper

```python
def recognize_shape_type(face: Face) -> str:
    """
    Recognize shape type from Face geometry.

    Returns shape_type as string (matches ShapeType enum names):
    - "RECTANGLE": 4 vertices
    - "L_SHAPE": 6 vertices
    - "T_SHAPE": 8 vertices (flat top)
    - "U_SHAPE": 8 vertices (gap at top)
    - "CIRCLE": 16+ vertices (polygon approximation)
    - "POLYGON": Other

    Args:
        face: TopologicPy Face

    Returns:
        Shape type name as string

    Example:
        >>> face = circle_face(0, 0, 5)
        >>> recognize_shape_type(face)
        'CIRCLE'
    """
    vertices = Face.Vertices(face)
    n = len(vertices)

    if n == 4:
        return "RECTANGLE"
    elif n == 6:
        return "L_SHAPE"
    elif n == 8:
        # Distinguish T vs U by analyzing top vertices
        coords = [Vertex.Coordinates(v) for v in vertices]
        y_values = [y for _, y, _ in coords]

        # Get top 4 vertices by y-coordinate
        sorted_y = sorted(enumerate(y_values), key=lambda x: x[1], reverse=True)
        top_4_indices = [idx for idx, _ in sorted_y[:4]]
        top_4_y = [y_values[idx] for idx in top_4_indices]

        # Y-range in top vertices
        y_range = max(top_4_y) - min(top_4_y)
        max_y = max(y_values)
        min_y = min(y_values)
        total_height = max_y - min_y

        # U-shape has gap (large Y variation in top vertices)
        if total_height > 0 and y_range / total_height > 0.2:
            return "U_SHAPE"
        else:
            return "T_SHAPE"
    elif n > 16:
        return "CIRCLE"
    else:
        return "POLYGON"
```

---

## Part 3: Refactored core.py

### New Structure

```python
"""
Shape Grammar Core - Refactored for Phase 4

ARCHITECTURE:
- LayoutState: Mutable transformation substrate
- Shape: Thin wrapper around TopologicPy Face
- ALL metadata in TopologicPy Dictionary (single source)
- Imports all helpers from topologic_helpers.py (no duplication)

CHANGES FROM PHASE 3:
- ✅ Removed duplicate helper functions (import from topologic_helpers)
- ✅ Removed shape builders (moved to topologic_helpers)
- ✅ Removed dual metadata storage (Dictionary only)
- ✅ Shape class is now just property accessors
"""

from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Any
from enum import Enum, auto

# TopologicPy imports
from topologicpy.Face import Face
from topologicpy.Vertex import Vertex
from topologicpy.Edge import Edge
from topologicpy.Topology import Topology

# Import ALL helpers (no duplication!)
from .topologic_helpers import (
    # Face creation
    rectangular_face,
    square_face,
    circle_face,
    lshape_face,
    tshape_face,
    ushape_face,
    polygon_face,

    # Metadata
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
# ENUMS
# ============================================================================

class ShapeType(Enum):
    """Shape type classification."""
    CIRCLE = auto()
    RECTANGLE = auto()
    L_SHAPE = auto()
    T_SHAPE = auto()
    U_SHAPE = auto()
    POLYGON = auto()


class Phase(Enum):
    """Transformation pipeline phases."""
    BUBBLE = 1       # Initial circle packing from graph
    RECTANGLES = 2   # Circles converted to rectangles
    ARRANGED = 3     # Rectangles aligned and arranged
    REFINED = 4      # Final refinement and validation


# ============================================================================
# SHAPE WRAPPER (Thin accessor around TopologicPy Face)
# ============================================================================

@dataclass
class Shape:
    """
    Lightweight wrapper around TopologicPy Face.

    ALL metadata stored in Face's TopologicPy Dictionary.
    No dual storage - single source of truth.

    Required Dictionary keys:
        - 'shape_id': Unique identifier (str)
        - 'room_type': Room label (str)
        - 'target_area': Target area in m² (float)
        - 'shape_type': ShapeType name (str)

    Example:
        >>> face = rectangular_face(5, 4, label="Kitchen",
        ...                         shape_id="s1", room_type="Kitchen", target_area=20)
        >>> shape = Shape(face)
        >>> shape.id
        's1'
        >>> shape.room_type
        'Kitchen'
        >>> shape.area
        20.0
    """
    face: Face

    # --- Convenience Properties (read from Dictionary) ---

    @property
    def id(self) -> str:
        return get_metadata(self.face, "shape_id", "unknown")

    @property
    def room_type(self) -> str:
        return get_metadata(self.face, "room_type", "Unknown")

    @property
    def target_area(self) -> float:
        return get_metadata(self.face, "target_area", 0.0)

    @property
    def shape_type(self) -> ShapeType:
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
        return face_area(self.face)

    @property
    def centroid(self) -> Vertex:
        return face_centroid(self.face)

    @property
    def centroid_xy(self) -> Tuple[float, float]:
        c = self.centroid
        x, y, z = vertex_coordinates(c)
        return (x, y)

    # --- Metadata Modification ---

    def set(self, **kwargs) -> None:
        """Update metadata in Dictionary."""
        self.face = set_metadata(self.face, **kwargs)

    def get(self, key: str, default=None):
        """Get metadata value."""
        return get_metadata(self.face, key, default)

    def all_metadata(self) -> Dict[str, Any]:
        """Get all metadata as dict."""
        return get_all_metadata(self.face)

    # --- Validation ---

    def area_error(self) -> float:
        if self.target_area <= 0:
            return 0.0
        return abs(self.area - self.target_area) / self.target_area

    # --- Geometry ---

    def vertices(self) -> List[Vertex]:
        return Face.Vertices(self.face)

    def edges(self) -> List[Edge]:
        return Face.Edges(self.face)


# ============================================================================
# LAYOUT EDGE
# ============================================================================

@dataclass
class LayoutEdge:
    """Lightweight edge between shapes."""
    source_id: str
    target_id: str
    relation: str = "CONNECTS"


# ============================================================================
# LAYOUT STATE (Transformation Substrate)
# ============================================================================

@dataclass
class LayoutState:
    """
    Mutable transformation substrate for shape grammar.

    Stores:
    - shapes: Dict[id -> Shape] (each Shape wraps a Face)
    - edges: List[LayoutEdge] (adjacency relationships)
    - phase: Current transformation phase

    All geometric data in TopologicPy Faces.
    All metadata in TopologicPy Dictionaries.
    """
    phase: Phase = Phase.BUBBLE
    shapes: Dict[str, Shape] = field(default_factory=dict)
    edges: List[LayoutEdge] = field(default_factory=list)
    is_valid: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    # --- Shape Management ---

    def add_shape(self, shape: Shape) -> None:
        """Add shape to layout."""
        self.shapes[shape.id] = shape
        self.is_valid = False

    def remove_shape(self, shape_id: str) -> None:
        """Remove shape and connected edges."""
        if shape_id in self.shapes:
            del self.shapes[shape_id]

        self.edges = [
            e for e in self.edges
            if e.source_id != shape_id and e.target_id != shape_id
        ]
        self.is_valid = False

    # --- Edge Management ---

    def add_edge(self, edge: LayoutEdge) -> None:
        """Add edge between shapes."""
        if edge.source_id not in self.shapes:
            raise ValueError(f"Source shape '{edge.source_id}' not found")
        if edge.target_id not in self.shapes:
            raise ValueError(f"Target shape '{edge.target_id}' not found")

        self.edges.append(edge)
        self.is_valid = False

    def get_neighbors(self, shape_id: str) -> List[str]:
        """Get neighboring shape IDs."""
        neighbors = []
        for edge in self.edges:
            if edge.source_id == shape_id:
                neighbors.append(edge.target_id)
            elif edge.target_id == shape_id:
                neighbors.append(edge.source_id)
        return neighbors

    def get_edges_for_shape(self, shape_id: str) -> List[LayoutEdge]:
        """Get all edges connected to shape."""
        return [
            e for e in self.edges
            if e.source_id == shape_id or e.target_id == shape_id
        ]

    # --- Geometry Queries ---

    def bounds(self) -> Tuple[float, float, float, float]:
        """Bounding box of all shapes."""
        if not self.shapes:
            return (0, 0, 0, 0)

        faces = [shape.face for shape in self.shapes.values()]
        return faces_bounding_box(faces)

    def total_area(self) -> float:
        """Total area of all shapes."""
        return sum(shape.area for shape in self.shapes.values())

    # --- Validation ---

    def validate(self, area_tolerance: float = 0.10) -> Dict[str, List[str]]:
        """
        Validate layout state.

        Checks:
        1. All shapes have positive area
        2. Area error within tolerance
        3. Edges reference existing shapes

        Returns:
            Dictionary of validation issues
        """
        issues = {
            'invalid_geometry': [],
            'area_mismatch': [],
            'invalid_edges': []
        }

        # Check shapes
        for shape_id, shape in self.shapes.items():
            if shape.area <= 0:
                issues['invalid_geometry'].append(
                    f"{shape_id}: Non-positive area ({shape.area:.2f}m²)"
                )

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

        self.is_valid = all(len(v) == 0 for v in issues.values())
        return issues

    def copy(self) -> 'LayoutState':
        """Deep copy of layout state."""
        import copy
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
    Create Shape from existing Face.

    Face must have required metadata in Dictionary:
    - shape_id
    - room_type
    - target_area
    """
    return Shape(face)


def create_circle_shape(
    shape_id: str,
    room_type: str,
    center_x: float,
    center_y: float,
    radius: float,
    target_area: Optional[float] = None
) -> Shape:
    """Create circular Shape."""
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
    """Create rectangular Shape."""
    area = target_area if target_area is not None else width * height

    # Use rectangular_face helper with rotation
    # Need to convert center coords to origin coords
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
    # For now, rectangular_face doesn't support rotation
    # Will need to add rotation parameter to rectangular_face in helpers

    return Shape(face)
```

**Key Changes**:
1. **No duplication**: All helpers imported
2. **No shape builders**: Moved to topologic_helpers.py
3. **Shape is thin wrapper**: Only Face + property accessors
4. **Single metadata source**: TopologicPy Dictionary only
5. **~400 lines removed**: From 963 → ~560 lines

---

## Part 4: Converter Module (NEW)

Create `src/grammar/converters.py`:

```python
"""
Bidirectional Converters: LayoutState ↔ GraphShape

Enables interoperability between Phase 2 (rules.py) and Phase 3 (core.py) architectures.

Use cases:
- Validate LayoutState using GraphShape.validate() (geometric consistency)
- Transform GraphShape using LayoutState pipeline (shape grammar)
- Export LayoutState as GraphShape for rule-based operations
"""

from typing import List, Tuple
from .core import LayoutState, Shape, LayoutEdge, Phase, ShapeType
from .rules import GraphShape
from .topologic_helpers import (
    get_metadata,
    set_metadata,
    face_area,
    recognize_shape_type,
)
from topologicpy.Face import Face
from topologicpy.Edge import Edge


# ============================================================================
# LayoutState → GraphShape
# ============================================================================

def layout_state_to_graph_shape(layout: LayoutState) -> GraphShape:
    """
    Convert LayoutState to GraphShape.

    Creates Cluster from Shape Faces and Graph from edges.
    Metadata already in Face Dictionaries (single source).

    Args:
        layout: LayoutState to convert

    Returns:
        GraphShape instance

    Example:
        >>> layout = LayoutState(...)
        >>> gs = layout_state_to_graph_shape(layout)
        >>> is_valid, issues = gs.validate()
    """
    # Extract faces (already have metadata in Dictionaries)
    faces = [shape.face for shape in layout.shapes.values()]

    # Extract adjacencies as (label, label) pairs
    adjacencies = []
    for edge in layout.edges:
        # Get labels from shape IDs
        # LayoutState uses shape_id, GraphShape uses label
        # Assume shape_id == label for now
        adjacencies.append((edge.source_id, edge.target_id))

    # Use GraphShape factory
    return GraphShape.from_faces_and_adjacencies(faces, adjacencies)


# ============================================================================
# GraphShape → LayoutState
# ============================================================================

def graph_shape_to_layout_state(
    gs: GraphShape,
    phase: Phase = Phase.ARRANGED
) -> LayoutState:
    """
    Convert GraphShape to LayoutState.

    Creates Shape wrappers around Faces and extracts edges from Graph.

    Args:
        gs: GraphShape to convert
        phase: Phase to assign to LayoutState (default ARRANGED)

    Returns:
        LayoutState instance

    Example:
        >>> gs = GraphShape.from_grid(20, 15, rows=2, cols=2)
        >>> layout = graph_shape_to_layout_state(gs, Phase.RECTANGLES)
    """
    # Create shapes from faces
    shapes = {}
    for face in gs.faces():
        # Get metadata from Dictionary
        shape_id = get_metadata(face, "label", "unknown")
        room_type = get_metadata(face, "room_type", shape_id)
        target_area = get_metadata(face, "target_area")

        # If target_area not in metadata, use actual area
        if target_area is None:
            target_area = face_area(face)
            # Update Dictionary
            face = set_metadata(face, target_area=target_area)

        # Ensure shape_id in Dictionary
        if not get_metadata(face, "shape_id"):
            face = set_metadata(face, shape_id=shape_id)

        # Ensure shape_type in Dictionary
        if not get_metadata(face, "shape_type"):
            shape_type_str = recognize_shape_type(face)
            face = set_metadata(face, shape_type=shape_type_str)

        # Create Shape wrapper
        shape = Shape(face)
        shapes[shape_id] = shape

    # Extract edges from graph
    edges = []
    for graph_edge in gs.edges():
        verts = Edge.Vertices(graph_edge)
        if len(verts) == 2:
            label1 = get_metadata(verts[0], "label")
            label2 = get_metadata(verts[1], "label")
            if label1 and label2:
                edges.append(LayoutEdge(label1, label2, "CONNECTS"))

    return LayoutState(
        phase=phase,
        shapes=shapes,
        edges=edges,
        is_valid=False
    )


# ============================================================================
# VALIDATION BRIDGE
# ============================================================================

def validate_layout_with_graph_shape(
    layout: LayoutState,
    tolerance: float = 0.01
) -> Tuple[bool, List[str]]:
    """
    Validate LayoutState using GraphShape geometric validation.

    Combines LayoutState.validate() (area errors) with
    GraphShape.validate() (overlaps, adjacency).

    Args:
        layout: LayoutState to validate
        tolerance: Geometric tolerance

    Returns:
        (is_valid, list_of_issues)

    Example:
        >>> is_valid, issues = validate_layout_with_graph_shape(layout)
        >>> if not is_valid:
        ...     for issue in issues:
        ...         print(f"  - {issue}")
    """
    all_issues = []

    # LayoutState validation (area, edges)
    layout_issues = layout.validate()
    for category, issue_list in layout_issues.items():
        all_issues.extend(issue_list)

    # GraphShape validation (overlaps, adjacency)
    gs = layout_state_to_graph_shape(layout)
    gs_valid, gs_issues = gs.validate(tolerance)
    all_issues.extend(gs_issues)

    return (len(all_issues) == 0, all_issues)
```

---

## Part 5: Migration Path & Breaking Changes

### Breaking Changes

1. **Shape constructor signature**
   ```python
   # OLD (Phase 3)
   shape = Shape(
       id="s1",
       face=face,
       room_type="Kitchen",
       target_area=20.0
   )

   # NEW (Phase 4)
   face = rectangular_face(
       5, 4,
       shape_id="s1",
       room_type="Kitchen",
       target_area=20.0
   )
   shape = Shape(face)
   ```

2. **Metadata modification**
   ```python
   # OLD
   shape.room_type = "Living"  # ❌ No longer works (property is read-only)

   # NEW
   shape.set(room_type="Living")  # ✅ Updates Dictionary
   ```

3. **Custom metadata**
   ```python
   # OLD
   shape.metadata["floor"] = 2

   # NEW
   shape.set(floor=2)  # ✅ Stores in Dictionary
   ```

4. **Shape creation helpers**
   ```python
   # OLD (core.py)
   from grammar.core import create_circle_face, create_rectangle_face

   # NEW (topologic_helpers.py)
   from grammar.topologic_helpers import circle_face, rectangular_face
   ```

### Migration Script

```python
# migrate_phase3_to_phase4.py

def migrate_shape_to_phase4(old_shape):
    """Convert Phase 3 Shape to Phase 4."""

    # Ensure all metadata in Dictionary
    face = old_shape.face
    face = set_metadata(
        face,
        shape_id=old_shape.id,
        room_type=old_shape.room_type,
        target_area=old_shape.target_area,
        shape_type=old_shape.shape_type.name,
        **old_shape.metadata  # Transfer custom metadata
    )

    # Create new Shape (just wrapper)
    return Shape(face)


def migrate_layout_state_to_phase4(old_layout):
    """Convert Phase 3 LayoutState to Phase 4."""

    new_shapes = {}
    for shape_id, old_shape in old_layout.shapes.items():
        new_shapes[shape_id] = migrate_shape_to_phase4(old_shape)

    return LayoutState(
        phase=old_layout.phase,
        shapes=new_shapes,
        edges=old_layout.edges.copy(),
        is_valid=old_layout.is_valid,
        metadata=old_layout.metadata.copy()
    )
```

---

## Part 6: Testing Strategy

### Unit Tests for Converters

```python
# tests/test_converters.py

def test_layout_to_graph_roundtrip():
    """Test LayoutState → GraphShape → LayoutState preserves data."""

    # Create LayoutState
    layout1 = LayoutState(phase=Phase.RECTANGLES)

    face1 = rectangular_face(5, 4, shape_id="s1", room_type="Kitchen", target_area=20)
    face2 = rectangular_face(6, 5, origin=(5, 0), shape_id="s2", room_type="Living", target_area=30)

    layout1.add_shape(Shape(face1))
    layout1.add_shape(Shape(face2))
    layout1.add_edge(LayoutEdge("s1", "s2"))

    # Convert to GraphShape
    gs = layout_state_to_graph_shape(layout1)

    assert gs.num_nodes() == 2
    assert gs.num_edges() == 1
    assert gs.total_area() == pytest.approx(50.0, rel=0.01)

    # Convert back to LayoutState
    layout2 = graph_shape_to_layout_state(gs, Phase.RECTANGLES)

    assert len(layout2.shapes) == 2
    assert len(layout2.edges) == 1
    assert layout2.total_area() == pytest.approx(50.0, rel=0.01)


def test_metadata_persistence_through_conversion():
    """Test custom metadata survives conversion."""

    # Create shape with custom metadata
    face = rectangular_face(
        5, 4,
        shape_id="s1",
        room_type="Kitchen",
        target_area=20,
        floor=2,
        has_window=True
    )

    shape1 = Shape(face)
    assert shape1.get("floor") == 2
    assert shape1.get("has_window") == True

    # Convert to GraphShape
    layout = LayoutState(shapes={"s1": shape1})
    gs = layout_state_to_graph_shape(layout)

    # Check metadata in GraphShape face
    gs_face = gs.get_face_by_label("s1")
    assert get_metadata(gs_face, "floor") == 2
    assert get_metadata(gs_face, "has_window") == True

    # Convert back
    layout2 = graph_shape_to_layout_state(gs)
    shape2 = layout2.shapes["s1"]

    assert shape2.get("floor") == 2
    assert shape2.get("has_window") == True
```

### Integration Tests

```python
# tests/test_phase4_integration.py

def test_graph_shape_rules_on_layout_state():
    """Test using GraphShape rules to transform LayoutState."""

    # Create LayoutState
    layout = LayoutState(phase=Phase.RECTANGLES)
    # ... add shapes ...

    # Convert to GraphShape for rule application
    gs = layout_state_to_graph_shape(layout)

    # Apply rule (when implemented)
    # split_rule = RuleLibrary.split_horizontal(ratio=0.5)
    # gs_new = split_rule.apply(gs, "s1")

    # Convert back to LayoutState
    # layout_new = graph_shape_to_layout_state(gs_new)

    # Validate
    is_valid, issues = validate_layout_with_graph_shape(layout)
    assert is_valid


def test_layout_state_validation_with_graph_shape():
    """Test enhanced validation using GraphShape."""

    # Create layout with overlapping shapes (invalid)
    face1 = rectangular_face(10, 10, origin=(0, 0), shape_id="s1", room_type="R1", target_area=100)
    face2 = rectangular_face(10, 10, origin=(5, 5), shape_id="s2", room_type="R2", target_area=100)

    layout = LayoutState(shapes={
        "s1": Shape(face1),
        "s2": Shape(face2)
    })

    # Validate
    is_valid, issues = validate_layout_with_graph_shape(layout)

    assert not is_valid
    assert any("Overlapping" in issue for issue in issues)
```

---

## Part 7: Implementation Checklist

### Phase 4.1: topologic_helpers.py Extensions
- [ ] Add `circle_face()` builder
- [ ] Add `lshape_face()` builder
- [ ] Add `tshape_face()` builder
- [ ] Add `ushape_face()` builder
- [ ] Add `polygon_face()` builder
- [ ] Add `recognize_shape_type()` function
- [ ] Test all builders with metadata persistence
- [ ] Update docstrings with examples

### Phase 4.2: core.py Refactoring
- [ ] Remove duplicate helper functions (lines 41-176)
- [ ] Import all helpers from topologic_helpers
- [ ] Remove shape builders (moved to helpers)
- [ ] Refactor Shape class to property accessors only
- [ ] Update convenience constructors (create_circle_shape, etc.)
- [ ] Update LayoutState to work with new Shape
- [ ] Test core.py in isolation

### Phase 4.3: Converter Module
- [ ] Create `src/grammar/converters.py`
- [ ] Implement `layout_state_to_graph_shape()`
- [ ] Implement `graph_shape_to_layout_state()`
- [ ] Implement `validate_layout_with_graph_shape()`
- [ ] Write unit tests for converters
- [ ] Test roundtrip conversions
- [ ] Test metadata persistence

### Phase 4.4: Test Updates
- [ ] Update `Test_Core_Shapes.ipynb` for new API
- [ ] Fix Shape construction calls
- [ ] Fix metadata access (shape.set() instead of direct assignment)
- [ ] Add converter tests
- [ ] Add integration tests
- [ ] Verify all 10 tests pass

### Phase 4.5: Documentation
- [ ] Update README with Phase 4 architecture
- [ ] Add migration guide from Phase 3
- [ ] Document converter usage patterns
- [ ] Add examples of GraphShape + LayoutState interop
- [ ] Update CLAUDE.md with new patterns

---

## Part 8: Performance Considerations

### Dictionary Access Performance

**Benchmark** (estimated):
```python
# Python attribute access
shape.room_type  # ~10 ns

# TopologicPy Dictionary access
get_metadata(face, "room_type")  # ~100 ns (10x slower)
```

**Impact Analysis**:
- Typical transformation loop: Read metadata once, compute geometry 100+ times
- Geometry operations (TopologicPy) dominate: ~1ms per Face operation
- Metadata reads: ~0.1μs per read
- **Conclusion**: 10x slower metadata access is negligible (<0.01% of total time)

### Memory Footprint

**Phase 3** (Dual storage):
```
Shape object: 200 bytes (Python object overhead)
+ id (str): 50 bytes
+ face (Face): 1000 bytes (TopologicPy)
+ room_type (str): 50 bytes
+ target_area (float): 8 bytes
+ shape_type (enum): 28 bytes
+ metadata (dict): 200 bytes
+ Face Dictionary: 500 bytes
= ~2,036 bytes per Shape
```

**Phase 4** (Single storage):
```
Shape object: 200 bytes (Python object overhead)
+ face (Face): 1000 bytes
+ Face Dictionary: 800 bytes (more metadata)
= ~2,000 bytes per Shape
```

**Conclusion**: Memory usage similar, slightly lower in Phase 4

---

## Part 9: Future Enhancements

### 9.1 GraphShape Rule Implementation

With converters in place, implement actual transformation rules:

```python
# rules.py

@staticmethod
def split_horizontal(ratio: float = 0.5) -> GraphShapeRule:
    """Split node horizontally using TopologicPy Face.Split."""

    def transform(gs: GraphShape, node_label: str, params: Dict) -> GraphShape:
        ratio = params.get('ratio', 0.5)

        # Get face to split
        face = gs.get_face_by_label(node_label)

        # Use TopologicPy Face.Split (if available)
        # OR implement manual subdivision

        # Create two new faces
        # Update graph topology
        # Return new GraphShape

        # (Full implementation)
        pass

    return GraphShapeRule(...)
```

### 9.2 Shape Grammar Transformation Rules

Implement actual shape transformations in core.py:

```python
# core.py

def circle_to_rectangle_rule(shape: Shape) -> Shape:
    """Transform circle shape to rectangle preserving area."""

    if shape.shape_type != ShapeType.CIRCLE:
        raise ValueError("Can only transform circles")

    # Get circle parameters
    radius = shape.get("radius")
    center_x = shape.get("center_x")
    center_y = shape.get("center_y")
    area = shape.target_area

    # Choose rectangle dimensions (aspect ratio 1.2)
    aspect = 1.2
    height = math.sqrt(area / aspect)
    width = aspect * height

    # Create rectangle face
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
```

### 9.3 Visualization Enhancements

```python
# visualization.py (NEW)

def visualize_layout_state(
    layout: LayoutState,
    show_labels: bool = True,
    show_edges: bool = True,
    color_by_phase: bool = False
):
    """Visualize LayoutState with phase-based coloring."""

    from topologicpy.Cluster import Cluster
    from topologicpy.Topology import Topology

    faces = [shape.face for shape in layout.shapes.values()]
    cluster = Cluster.ByTopologies(faces)

    # Color by phase
    if color_by_phase:
        phase_colors = {
            Phase.BUBBLE: "lightblue",
            Phase.RECTANGLES: "lightgreen",
            Phase.ARRANGED: "lightyellow",
            Phase.REFINED: "lightcoral"
        }
        # Apply colors to faces...

    Topology.Show(cluster, renderer="notebook")
```

---

## Summary

Phase 4 achieves:

✅ **Zero Duplication**: All helpers in topologic_helpers.py
✅ **Complete Interoperability**: LayoutState ↔ GraphShape converters
✅ **Single Metadata Source**: TopologicPy Dictionary only (no sync issues)
✅ **Shared Shape Builders**: Circle, L, T, U shapes available to both architectures
✅ **Cleaner Architecture**: Shape is thin wrapper, LayoutState is transformation substrate
✅ **Better Validation**: Combined LayoutState + GraphShape validation
✅ **Future-Proof**: Ready for rule implementations and shape grammar extensions

**Total Impact**:
- -363 lines from core.py (duplication removed)
- +211 lines to topologic_helpers.py (shape builders)
- +200 lines converters.py (new module)
- **Net**: +48 lines, infinite value 🚀

---

**Next Steps**: Implement Phase 4.1 → 4.2 → 4.3 → 4.4 → 4.5 sequentially.

