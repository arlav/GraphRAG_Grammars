# Refactoring Plan: TopologicPy-Native Architecture

**Date**: 2025-12-25
**Goal**: Refactor GraphRAG Grammars to use TopologicPy conventions throughout, not just for visualization

---

## 1. Current Architecture Analysis

### 1.1 Current Approach
```
Custom Python Classes → Conversion Layer → TopologicPy (visualization only)

shapes.py: Rectangle/Square/Point dataclasses
rules.py: GraphShape with dict of shapes + networkx graph
visualization: graphshape_to_topologic() converts at render time
```

### 1.2 Problems with Current Approach

❌ **Dual data structures**: Python objects AND TopologicPy objects
❌ **Late conversion**: TopologicPy only used for visualization
❌ **Metadata duplication**: Python dicts AND Topologic Dictionaries
❌ **Redundant graph**: networkx graph AND Topologic Graph
❌ **Not leveraging TopologicPy**: Custom methods instead of built-in Topology methods

### 1.3 What TopologicPy Conventions Mean

Based on TopologicPy documentation and usage patterns:

1. **Topology as primary structure**
   - Everything is a Topology (Vertex, Edge, Face, Cell, etc.)
   - No custom geometry classes

2. **Dictionary for metadata**
   - All properties stored via `Dictionary.ByKeysValues()`
   - Attached via `Topology.SetDictionary()`
   - Retrieved via `Topology.Dictionary()`

3. **Graph for relationships**
   - Use `Graph.ByVerticesEdges()` for topology
   - Vertices at significant points (centroids, corners)
   - Edges represent relationships

4. **Operations use Topology methods**
   - Adjacency: `Topology.SharedEdges()`
   - Overlap: `Topology.Intersect()`
   - Area: `Face.Area()`
   - Centroid: `Topology.Centroid()`

5. **Visualization**
   - `Topology.Show(topologies, graph, ...)` for dual view

---

## 2. Refactoring Plan - Iteration 1: Full Native

### Concept
Replace ALL custom classes with TopologicPy primitives

```python
# BEFORE (current)
rect = Rectangle(5, 4, Point(0, 0))
gs = GraphShape(shapes={'A': rect}, edges=[])

# AFTER (iteration 1)
face = Face.ByVertices([v1, v2, v3, v4])
graph = Graph.ByVerticesEdges([vertex_at_centroid], [])
gs = GraphShape(cluster=Cluster.ByTopologies([face]), graph=graph)
```

### Pros
✅ Pure TopologicPy - no custom classes
✅ Single source of truth
✅ Leverages all Topology methods

### Cons
❌ **Verbose**: Creating `Face.ByVertices()` requires 4 Vertex objects
❌ **Loss of parametric power**: `Rectangle(w, h)` is clearer than vertex lists
❌ **Immutability loss**: Can't use `frozen=True` with TopologicPy objects
❌ **Ergonomics**: Harder to create common shapes

### Verdict
❌ **TOO EXTREME** - Loses too much ergonomic value

---

## 3. Refactoring Plan - Iteration 2: Pydantic Wrappers

### Concept
Pydantic models wrap TopologicPy objects, providing validation + convenience

```python
from pydantic import BaseModel

class RoomFace(BaseModel):
    """Wrapper around Topologic Face"""
    face: Face  # TopologicPy Face
    width: float
    height: float
    label: str

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def rectangular(cls, width, height, origin=(0,0), label=""):
        vertices = [...]  # Create 4 vertices
        face = Face.ByVertices(vertices)
        return cls(face=face, width=width, height=height, label=label)
```

### Pros
✅ Validation via Pydantic
✅ Convenient factory methods
✅ Type hints and IDE support

### Cons
❌ **Metadata duplication**: In Pydantic fields AND Topologic Dictionary
❌ **Complexity**: Extra layer to maintain
❌ **Unclear value**: What does Pydantic add beyond validation?

### Verdict
⚠️ **OVER-ENGINEERED** - Pydantic doesn't add enough value for the complexity

---

## 4. Refactoring Plan - Iteration 3: FINAL - Helper Functions + Pure Topologic

### 🎯 CORE PHILOSOPHY

**"TopologicPy primitives everywhere, Python functions for ergonomics"**

1. **NO custom classes for geometry** - Everything is `Face`, `Vertex`, `Edge`
2. **Topologic Graph is the ONLY graph** - Remove networkx dependency
3. **GraphShape wraps Cluster + Graph** - Minimal Pydantic wrapper for convenience
4. **Helper functions create Topologies** - `rectangular_face()`, `square_face()`
5. **All operations delegate to Topology methods** - Leverage built-in functionality

---

### 4.1 New File Structure

#### `src/grammar/topologic_helpers.py` (NEW)
Helper functions to create TopologicPy primitives ergonomically

```python
"""
TopologicPy Helper Functions

Convenience functions for creating and manipulating TopologicPy primitives.
All functions return pure TopologicPy objects (Face, Vertex, Graph, etc.)
"""

from topologicpy.Vertex import Vertex
from topologicpy.Edge import Edge
from topologicpy.Face import Face
from topologicpy.Topology import Topology
from topologicpy.Dictionary import Dictionary
from topologicpy.Cluster import Cluster
from topologicpy.Graph import Graph


# ============================================================================
# FACE CREATION HELPERS
# ============================================================================

def rectangular_face(
    width: float,
    height: float,
    origin: tuple[float, float] = (0.0, 0.0),
    label: str | None = None,
    **metadata
) -> Face:
    """
    Create a rectangular Face with optional metadata.

    Args:
        width: Width of rectangle
        height: Height of rectangle
        origin: Bottom-left corner (x, y)
        label: Optional label for the face
        **metadata: Additional key-value pairs to store

    Returns:
        Face with attached Dictionary containing metadata

    Example:
        >>> kitchen = rectangular_face(5, 4, origin=(0, 0), label="Kitchen", area=20)
    """
    x, y = origin

    # Create vertices (counter-clockwise from bottom-left)
    vertices = [
        Vertex.ByCoordinates(x, y, 0),
        Vertex.ByCoordinates(x + width, y, 0),
        Vertex.ByCoordinates(x + width, y + height, 0),
        Vertex.ByCoordinates(x, y + height, 0),
    ]

    # Create face
    face = Face.ByVertices(vertices)

    # Build metadata dictionary
    meta = {
        "width": width,
        "height": height,
        "origin_x": x,
        "origin_y": y,
        "area": width * height,
    }

    if label:
        meta["label"] = label

    meta.update(metadata)

    # Attach dictionary to face
    keys = list(meta.keys())
    values = list(meta.values())
    d = Dictionary.ByKeysValues(keys, values)
    face = Topology.SetDictionary(face, d)

    return face


def square_face(
    size: float,
    origin: tuple[float, float] = (0.0, 0.0),
    label: str | None = None,
    **metadata
) -> Face:
    """
    Create a square Face (convenience wrapper for rectangular_face).

    Example:
        >>> bathroom = square_face(3, origin=(10, 0), label="Bathroom")
    """
    return rectangular_face(size, size, origin, label, is_square=True, **metadata)


# ============================================================================
# METADATA UTILITIES
# ============================================================================

def get_metadata(topology: Topology, key: str, default=None):
    """
    Get metadata value from Topology's Dictionary.

    Args:
        topology: Any Topology object with attached Dictionary
        key: Metadata key to retrieve
        default: Value to return if key not found

    Returns:
        Metadata value or default

    Example:
        >>> label = get_metadata(face, "label", "Unknown")
    """
    d = Topology.Dictionary(topology)
    if not d:
        return default

    keys = Dictionary.Keys(d)
    if key not in keys:
        return default

    values = Dictionary.Values(d)
    return values[keys.index(key)]


def set_metadata(topology: Topology, **kwargs) -> Topology:
    """
    Add/update metadata on a Topology.

    Merges new metadata with existing Dictionary.

    Args:
        topology: Topology to modify
        **kwargs: Key-value pairs to add

    Returns:
        Topology with updated Dictionary

    Example:
        >>> face = set_metadata(face, room_type="Kitchen", floor=2)
    """
    # Get existing dictionary
    existing_dict = Topology.Dictionary(topology)

    if existing_dict:
        existing_keys = Dictionary.Keys(existing_dict)
        existing_values = Dictionary.Values(existing_dict)
        existing_data = dict(zip(existing_keys, existing_values))
    else:
        existing_data = {}

    # Merge with new data
    existing_data.update(kwargs)

    # Create new dictionary
    keys = list(existing_data.keys())
    values = list(existing_data.values())
    new_dict = Dictionary.ByKeysValues(keys, values)

    return Topology.SetDictionary(topology, new_dict)


# ============================================================================
# GEOMETRIC QUERIES (delegating to TopologicPy)
# ============================================================================

def face_centroid(face: Face) -> Vertex:
    """
    Get centroid of a Face as a Vertex.

    Example:
        >>> centroid = face_centroid(kitchen_face)
        >>> x, y, z = Vertex.Coordinates(centroid)
    """
    return Topology.Centroid(face)


def faces_adjacent(face1: Face, face2: Face, tolerance: float = 0.01) -> bool:
    """
    Check if two Faces share an edge (are adjacent).

    Uses TopologicPy's SharedEdges to detect shared boundaries.

    Args:
        face1: First Face
        face2: Second Face
        tolerance: Distance tolerance for adjacency

    Returns:
        True if faces share at least one edge

    Example:
        >>> adjacent = faces_adjacent(kitchen, living_room)
    """
    shared = Topology.SharedEdges(face1, face2)
    return len(shared) > 0


def faces_overlap(face1: Face, face2: Face, tolerance: float = 0.01) -> bool:
    """
    Check if two Faces overlap (intersect with non-zero area).

    Args:
        face1: First Face
        face2: Second Face
        tolerance: Minimum area to consider as overlap

    Returns:
        True if faces overlap

    Example:
        >>> overlapping = faces_overlap(room1, room2)
    """
    intersection = Topology.Intersect(face1, face2)
    if not intersection:
        return False

    # Check if intersection has meaningful area
    try:
        area = Face.Area(intersection)
        return area > tolerance
    except:
        return False


def face_area(face: Face) -> float:
    """
    Get area of a Face.

    Example:
        >>> area = face_area(bedroom)
    """
    return Face.Area(face)


def faces_bounding_box(faces: list[Face]) -> tuple[float, float, float, float]:
    """
    Calculate bounding box containing all faces.

    Args:
        faces: List of Face objects

    Returns:
        (min_x, min_y, max_x, max_y)

    Example:
        >>> bbox = faces_bounding_box([kitchen, living, bedroom])
    """
    all_coords = []

    for face in faces:
        vertices = Face.Vertices(face)
        for vertex in vertices:
            x, y, z = Vertex.Coordinates(vertex)
            all_coords.append((x, y))

    if not all_coords:
        return (0, 0, 0, 0)

    xs = [c[0] for c in all_coords]
    ys = [c[1] for c in all_coords]

    return (min(xs), min(ys), max(xs), max(ys))


# ============================================================================
# GRAPH CONSTRUCTION
# ============================================================================

def graph_from_faces_and_adjacencies(
    faces: list[Face],
    adjacencies: list[tuple[str, str]]
) -> Graph:
    """
    Create a Topologic Graph from faces and adjacency pairs.

    Creates vertices at face centroids and edges for each adjacency.
    Metadata from faces is copied to corresponding graph vertices.

    Args:
        faces: List of Face objects (must have 'label' metadata)
        adjacencies: List of (label1, label2) tuples

    Returns:
        Topologic Graph with vertices at centroids

    Example:
        >>> faces = [kitchen_face, living_face, bedroom_face]
        >>> adjacencies = [("Kitchen", "Living"), ("Living", "Bedroom")]
        >>> graph = graph_from_faces_and_adjacencies(faces, adjacencies)
    """
    # Build face lookup by label
    face_dict = {}
    vertex_dict = {}

    for face in faces:
        label = get_metadata(face, "label")
        if not label:
            continue

        face_dict[label] = face

        # Create vertex at centroid
        centroid = face_centroid(face)

        # Copy face metadata to vertex
        face_meta_dict = Topology.Dictionary(face)
        if face_meta_dict:
            centroid = Topology.SetDictionary(centroid, face_meta_dict)

        vertex_dict[label] = centroid

    # Create edges
    graph_edges = []
    for label1, label2 in adjacencies:
        if label1 in vertex_dict and label2 in vertex_dict:
            edge = Edge.ByVertices([vertex_dict[label1], vertex_dict[label2]])
            graph_edges.append(edge)

    # Create graph
    vertices_list = list(vertex_dict.values())

    if not graph_edges:
        # Graph requires at least one edge, create a dummy edge if needed
        if len(vertices_list) >= 2:
            dummy_edge = Edge.ByVertices([vertices_list[0], vertices_list[1]])
            graph_edges = [dummy_edge]

    if not graph_edges:
        raise ValueError("Cannot create graph without edges and at least 2 vertices")

    graph = Graph.ByVerticesEdges(vertices_list, graph_edges)

    return graph
```

#### `src/grammar/rules.py` (REFACTORED)
GraphShape using pure TopologicPy

```python
"""
Graph-Shape Grammar Rules

Implements GraphShape class that maintains synchronized graph topology
and geometric shapes using TopologicPy primitives.
"""

from pydantic import BaseModel, Field
from typing import Optional

from topologicpy.Cluster import Cluster
from topologicpy.Graph import Graph
from topologicpy.Face import Face
from topologicpy.Vertex import Vertex
from topologicpy.Edge import Edge
from topologicpy.Topology import Topology

from .topologic_helpers import (
    rectangular_face,
    square_face,
    get_metadata,
    face_centroid,
    faces_adjacent,
    faces_overlap,
    face_area,
    faces_bounding_box,
    graph_from_faces_and_adjacencies,
)


class GraphShape(BaseModel):
    """
    Dual graph-geometry representation using TopologicPy primitives.

    Architecture:
    - cluster: Cluster of Faces (room geometries)
    - graph: Graph connecting room centroids (topology)

    All geometry is stored as TopologicPy Faces, all topology as TopologicPy Graph.
    No custom classes, no networkx dependency.

    Example:
        >>> faces = [
        ...     rectangular_face(5, 4, origin=(0, 0), label="Kitchen"),
        ...     rectangular_face(6, 5, origin=(5, 0), label="Living"),
        ... ]
        >>> adjacencies = [("Kitchen", "Living")]
        >>> gs = GraphShape.from_faces_and_adjacencies(faces, adjacencies)
    """

    cluster: Cluster
    graph: Graph

    class Config:
        arbitrary_types_allowed = True  # Allow TopologicPy types

    # ========================================================================
    # PROPERTIES - Delegate to TopologicPy
    # ========================================================================

    def faces(self) -> list[Face]:
        """Get all faces from cluster."""
        return Cluster.Topologies(self.cluster)

    def vertices(self) -> list[Vertex]:
        """Get all graph vertices (at room centroids)."""
        return Graph.Vertices(self.graph)

    def edges(self) -> list[Edge]:
        """Get all graph edges (room adjacencies)."""
        return Graph.Edges(self.graph)

    def total_area(self) -> float:
        """Calculate total area of all faces."""
        return sum(face_area(f) for f in self.faces())

    def bounding_box(self) -> tuple[float, float, float, float]:
        """Get bounding box (min_x, min_y, max_x, max_y)."""
        return faces_bounding_box(self.faces())

    # ========================================================================
    # VALIDATION - Using TopologicPy methods
    # ========================================================================

    def find_overlaps(self, tolerance: float = 0.01) -> list[tuple[str, str]]:
        """
        Find all pairs of overlapping faces.

        Returns:
            List of (label1, label2) tuples for overlapping faces
        """
        overlaps = []
        faces = self.faces()

        for i, face1 in enumerate(faces):
            for face2 in faces[i+1:]:
                if faces_overlap(face1, face2, tolerance):
                    label1 = get_metadata(face1, "label", "unknown")
                    label2 = get_metadata(face2, "label", "unknown")
                    overlaps.append((label1, label2))

        return overlaps

    def find_missing_adjacencies(self, tolerance: float = 0.01) -> list[tuple[str, str]]:
        """
        Find geometric adjacencies not represented in graph.

        Returns:
            List of (label1, label2) tuples for faces that are adjacent
            but don't have a corresponding graph edge
        """
        missing = []
        faces = self.faces()

        # Build set of existing edges from graph
        existing_edges = set()
        for edge in self.edges():
            verts = Edge.Vertices(edge)
            if len(verts) == 2:
                label1 = get_metadata(verts[0], "label")
                label2 = get_metadata(verts[1], "label")
                if label1 and label2:
                    existing_edges.add(tuple(sorted([label1, label2])))

        # Check all face pairs
        for i, face1 in enumerate(faces):
            for face2 in faces[i+1:]:
                if faces_adjacent(face1, face2, tolerance):
                    label1 = get_metadata(face1, "label", "unknown")
                    label2 = get_metadata(face2, "label", "unknown")
                    edge_key = tuple(sorted([label1, label2]))

                    if edge_key not in existing_edges:
                        missing.append((label1, label2))

        return missing

    def validate(self, tolerance: float = 0.01) -> tuple[bool, list[str]]:
        """
        Validate graph-shape consistency.

        Checks:
        1. No overlapping faces
        2. Graph edges correspond to geometric adjacencies

        Returns:
            (is_valid, list_of_issues)
        """
        issues = []

        # Check overlaps
        overlaps = self.find_overlaps(tolerance)
        for label1, label2 in overlaps:
            issues.append(f"Overlapping faces: {label1} ↔ {label2}")

        # Check that graph edges have geometric adjacency
        for edge in self.edges():
            verts = Edge.Vertices(edge)
            if len(verts) != 2:
                continue

            label1 = get_metadata(verts[0], "label")
            label2 = get_metadata(verts[1], "label")

            if not label1 or not label2:
                continue

            # Find corresponding faces
            faces = self.faces()
            face1 = next((f for f in faces if get_metadata(f, "label") == label1), None)
            face2 = next((f for f in faces if get_metadata(f, "label") == label2), None)

            if face1 and face2:
                if not faces_adjacent(face1, face2, tolerance):
                    issues.append(f"Graph edge without geometric adjacency: {label1} ↔ {label2}")

        return (len(issues) == 0, issues)

    # ========================================================================
    # FACTORY METHODS
    # ========================================================================

    @classmethod
    def from_faces_and_adjacencies(
        cls,
        faces: list[Face],
        adjacencies: list[tuple[str, str]]
    ) -> "GraphShape":
        """
        Create GraphShape from faces and adjacency pairs.

        Args:
            faces: List of Face objects (must have 'label' metadata)
            adjacencies: List of (label1, label2) adjacency tuples

        Returns:
            GraphShape instance

        Example:
            >>> faces = [
            ...     rectangular_face(5, 4, label="Kitchen"),
            ...     rectangular_face(6, 5, label="Living"),
            ... ]
            >>> adjacencies = [("Kitchen", "Living")]
            >>> gs = GraphShape.from_faces_and_adjacencies(faces, adjacencies)
        """
        cluster = Cluster.ByTopologies(faces)
        graph = graph_from_faces_and_adjacencies(faces, adjacencies)

        return cls(cluster=cluster, graph=graph)

    @classmethod
    def from_grid(
        cls,
        base_width: float,
        base_height: float,
        rows: int,
        cols: int,
        origin: tuple[float, float] = (0.0, 0.0)
    ) -> "GraphShape":
        """
        Create GraphShape from grid subdivision.

        Subdivides a rectangle into rows×cols cells with mesh topology.

        Args:
            base_width: Width of base rectangle
            base_height: Height of base rectangle
            rows: Number of rows
            cols: Number of columns
            origin: Bottom-left corner of base rectangle

        Returns:
            GraphShape with grid layout

        Example:
            >>> gs = GraphShape.from_grid(20, 15, rows=3, cols=3)
        """
        cell_width = base_width / cols
        cell_height = base_height / rows

        faces = []
        adjacencies = []

        x0, y0 = origin

        for r in range(rows):
            for c in range(cols):
                label = f"room_{r}_{c}"

                face = rectangular_face(
                    cell_width,
                    cell_height,
                    origin=(x0 + c * cell_width, y0 + r * cell_height),
                    label=label,
                    row=r,
                    col=c
                )
                faces.append(face)

                # Add adjacencies
                if c > 0:  # Left neighbor
                    adjacencies.append((label, f"room_{r}_{c-1}"))
                if r > 0:  # Bottom neighbor
                    adjacencies.append((label, f"room_{r-1}_{c}"))

        return cls.from_faces_and_adjacencies(faces, adjacencies)

    @classmethod
    def from_horizontal_split(
        cls,
        base_width: float,
        base_height: float,
        ratios: list[float],
        labels: Optional[list[str]] = None,
        origin: tuple[float, float] = (0.0, 0.0)
    ) -> "GraphShape":
        """
        Create GraphShape from horizontal subdivision.

        Splits a rectangle horizontally into sections with linear topology.

        Args:
            base_width: Width of base rectangle
            base_height: Height of base rectangle
            ratios: Width ratios for each section (must sum to 1.0)
            labels: Optional labels for each section
            origin: Bottom-left corner of base rectangle

        Returns:
            GraphShape with linear layout

        Example:
            >>> gs = GraphShape.from_horizontal_split(
            ...     30, 10,
            ...     ratios=[0.3, 0.4, 0.3],
            ...     labels=["Entrance", "Living", "Bedroom"]
            ... )
        """
        # Normalize ratios
        total = sum(ratios)
        ratios = [r / total for r in ratios]

        if labels is None:
            labels = [f"section_{i}" for i in range(len(ratios))]

        faces = []
        adjacencies = []

        x0, y0 = origin
        current_x = x0

        for i, (ratio, label) in enumerate(zip(ratios, labels)):
            section_width = base_width * ratio

            face = rectangular_face(
                section_width,
                base_height,
                origin=(current_x, y0),
                label=label,
                section_index=i
            )
            faces.append(face)

            # Add adjacency to previous section
            if i > 0:
                adjacencies.append((labels[i-1], label))

            current_x += section_width

        return cls.from_faces_and_adjacencies(faces, adjacencies)


# ============================================================================
# LEGACY COMPATIBILITY (optional - for gradual migration)
# ============================================================================

# If needed, we can provide adapters for old code:
# def graphshape_from_old_format(shapes_dict, edges_list) -> GraphShape:
#     """Convert old dict-based format to new TopologicPy format"""
#     pass
```

#### `src/grammar/shapes.py` (DEPRECATED or REMOVED)
This file can be:
- **Option A**: Deleted entirely (clean break)
- **Option B**: Kept for legacy compatibility with deprecation warnings
- **Option C**: Converted to thin wrappers around topologic_helpers

**Recommendation**: Option A (delete) for clean architecture

---

### 4.2 Migration Impact on Notebooks

#### `00_Simple_Shapes.ipynb`
**Before**:
```python
from grammar.shapes import Rectangle, Square, Point

rect = Rectangle(5, 4, Point(0, 0))
print(f"Area: {rect.area()}")
```

**After**:
```python
from grammar.topologic_helpers import rectangular_face, get_metadata, face_area

face = rectangular_face(5, 4, origin=(0, 0), label="Room1")
print(f"Area: {face_area(face)}")
```

**Changes Required**:
- Replace all `Rectangle()` calls with `rectangular_face()`
- Replace `Square()` calls with `square_face()`
- Replace `.area()` with `face_area()`
- Replace `.centroid()` with `face_centroid()`
- Replace `.is_adjacent_to()` with `faces_adjacent()`

#### `01_Graphs_On_Shapes.ipynb`
**Before**:
```python
shapes = {
    'Kitchen': Rectangle(5, 4, Point(0, 0)),
    'Living': Rectangle(6, 5, Point(5, 0))
}
edges = [('Kitchen', 'Living')]
gs = GraphShape(shapes=shapes, edges=edges)

# Conversion at viz time
faces, topo_graph, vertices = graphshape_to_topologic(gs)
```

**After**:
```python
from grammar.topologic_helpers import rectangular_face
from grammar.rules import GraphShape

faces = [
    rectangular_face(5, 4, origin=(0, 0), label='Kitchen'),
    rectangular_face(6, 5, origin=(5, 0), label='Living')
]
adjacencies = [('Kitchen', 'Living')]
gs = GraphShape.from_faces_and_adjacencies(faces, adjacencies)

# Already TopologicPy - no conversion needed!
Topology.Show(gs.cluster, gs.graph, sagitta=0.05, ...)
```

**Changes Required**:
- Replace dict of shapes + list of edges with list of faces + list of adjacencies
- Remove `graphshape_to_topologic()` helper (no longer needed!)
- Simplify visualization (direct access to `.cluster` and `.graph`)

---

### 4.3 Benefits of This Approach

✅ **Pure TopologicPy**: All geometry is Faces, all topology is Graph
✅ **No conversion layer**: Already in TopologicPy format
✅ **Leverages Topology methods**: Use built-in `SharedEdges()`, `Intersect()`, etc.
✅ **Single source of truth**: Metadata only in Dictionary
✅ **Ergonomic**: Helper functions make creation easy
✅ **Maintainable**: Less code, clearer architecture
✅ **Extensible**: Easy to add new TopologicPy features
✅ **Minimal Pydantic**: Only for validation and convenience methods

---

### 4.4 Migration Strategy

**Phase 1: Create New Files**
1. Create `src/grammar/topologic_helpers.py`
2. Refactor `src/grammar/rules.py` to use new helpers
3. Test new GraphShape in isolation

**Phase 2: Update Notebooks**
4. Update `01_Graphs_On_Shapes.ipynb` (main target)
5. Update `00_Simple_Shapes.ipynb` (optional - could keep as tutorial)

**Phase 3: Cleanup**
6. Remove or deprecate `src/grammar/shapes.py`
7. Update imports in any other files
8. Update tests

---

## 5. Code Comparison: Before vs After

### Creating a Simple Floor Plan

**BEFORE (Current)**:
```python
# Step 1: Create Python objects
from grammar.shapes import Rectangle, Point
from grammar.rules import GraphShape

shapes = {
    'Kitchen': Rectangle(5, 4, Point(0, 0)),
    'Living': Rectangle(6, 5, Point(5, 0)),
    'Bedroom': Rectangle(5, 4, Point(11, 0))
}

edges = [
    ('Kitchen', 'Living'),
    ('Living', 'Bedroom')
]

gs = GraphShape(shapes=shapes, edges=edges)

# Step 2: Convert to TopologicPy for visualization
faces, topo_graph, vertices = graphshape_to_topologic(gs)
cluster = Cluster.ByTopologies(faces)

# Step 3: Visualize
Topology.Show(cluster, topo_graph, sagitta=0.05, ...)
```

**AFTER (TopologicPy-Native)**:
```python
# Step 1: Create TopologicPy objects directly
from grammar.topologic_helpers import rectangular_face
from grammar.rules import GraphShape

faces = [
    rectangular_face(5, 4, origin=(0, 0), label='Kitchen'),
    rectangular_face(6, 5, origin=(5, 0), label='Living'),
    rectangular_face(5, 4, origin=(11, 0), label='Bedroom')
]

adjacencies = [
    ('Kitchen', 'Living'),
    ('Living', 'Bedroom')
]

gs = GraphShape.from_faces_and_adjacencies(faces, adjacencies)

# Step 2: Visualize (no conversion needed!)
Topology.Show(gs.cluster, gs.graph, sagitta=0.05, ...)
```

**Difference**:
- ❌ Removed: Python Rectangle class, conversion layer, dict of shapes
- ✅ Added: Direct TopologicPy Face creation, simpler visualization
- **Result**: Fewer lines, clearer intent, true TopologicPy conventions

---

### Validation

**BEFORE (Current)**:
```python
# Custom validation using Python methods
overlaps = []
for n1, n2 in combinations(shapes.keys(), 2):
    if shapes[n1].overlaps(shapes[n2]):  # Custom method
        overlaps.append((n1, n2))
```

**AFTER (TopologicPy-Native)**:
```python
# Validation using TopologicPy methods
overlaps = gs.find_overlaps()  # Uses Topology.Intersect() internally
```

**Difference**:
- Delegates to TopologicPy's built-in `Topology.Intersect()`
- More reliable (uses library's proven geometry algorithms)

---

## 6. Implementation Checklist

### Files to Create
- [ ] `src/grammar/topologic_helpers.py` - Helper functions
  - [ ] `rectangular_face()` - Create rectangular Face
  - [ ] `square_face()` - Create square Face
  - [ ] `get_metadata()` - Get value from Dictionary
  - [ ] `set_metadata()` - Add/update Dictionary
  - [ ] `face_centroid()` - Get centroid
  - [ ] `faces_adjacent()` - Check adjacency via SharedEdges
  - [ ] `faces_overlap()` - Check overlap via Intersect
  - [ ] `face_area()` - Get area
  - [ ] `faces_bounding_box()` - Calculate bbox
  - [ ] `graph_from_faces_and_adjacencies()` - Create Graph

### Files to Refactor
- [ ] `src/grammar/rules.py` - Refactor GraphShape
  - [ ] Update to store `cluster: Cluster` and `graph: Graph`
  - [ ] Remove networkx dependency
  - [ ] Update `total_area()`, `bounding_box()`
  - [ ] Update `find_overlaps()`, `find_missing_adjacencies()`, `validate()`
  - [ ] Update `from_grid()`, `from_horizontal_split()`
  - [ ] Add `from_faces_and_adjacencies()` factory

### Files to Update
- [ ] `01_Graphs_On_Shapes.ipynb` - Main notebook
  - [ ] Update imports
  - [ ] Replace Rectangle with rectangular_face
  - [ ] Update GraphShape creation to use new API
  - [ ] Remove graphshape_to_topologic() helper
  - [ ] Simplify visualization cells

### Files to Remove/Deprecate
- [ ] `src/grammar/shapes.py` - Old Rectangle/Square classes
  - [ ] Option A: Delete entirely ✅ RECOMMENDED
  - [ ] Option B: Add deprecation warnings
  - [ ] Option C: Convert to thin wrappers

### Testing
- [ ] Unit tests for topologic_helpers.py
- [ ] Unit tests for refactored GraphShape
- [ ] Integration test: Create grid, validate, visualize
- [ ] Run all notebook cells

---

## 7. Questions for Review

Before implementing, please confirm:

1. **Approach**: Is "helper functions + pure TopologicPy" the right balance?
2. **shapes.py fate**: Delete entirely or keep deprecated wrappers?
3. **Pydantic usage**: Is minimal Pydantic wrapper for GraphShape acceptable?
4. **Metadata strategy**: All in Topologic Dictionary, or some in Pydantic fields?
5. **Backward compatibility**: Need adapters for old code?
6. **00_Simple_Shapes.ipynb**: Keep as Rectangle tutorial or refactor too?

---

## 8. Summary

### Key Decisions

| Aspect | Current | Proposed |
|--------|---------|----------|
| Geometry | Rectangle dataclass | Topologic Face |
| Topology | networkx.Graph | Topologic Graph |
| Metadata | Python dict | Topologic Dictionary |
| Validation | Custom methods | Topology.Intersect(), SharedEdges() |
| Conversion | At visualization time | Not needed (native) |
| Ergonomics | Class constructors | Helper functions |

### Philosophy

**"TopologicPy all the way down, Python for ergonomics"**

- No custom geometry classes
- No duplicate data structures
- Leverage TopologicPy's proven algorithms
- Helper functions for common patterns
- Minimal Pydantic for convenience

This approach respects TopologicPy conventions while maintaining developer ergonomics.

---

**Next Step**: Review this plan, iterate if needed, then implement.
