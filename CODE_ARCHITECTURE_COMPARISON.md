# Code Architecture Comparison: Grammar System Evolution

**Date**: 2025-12-31
**Files Analyzed**:
- `src/grammar/core.py` (963 lines) - NEW Phase 3 implementation
- `src/grammar/rules.py` (575 lines) - Phase 2 graph-shape rules
- `src/grammar/shapes.py` (71 lines) - DEPRECATED wrapper
- `src/grammar/topologic_helpers.py` (439 lines) - Phase 2 helper utilities

---

## Executive Summary

The grammar system has evolved through **two major architectural iterations**:

1. **Phase 2 Architecture** (rules.py + topologic_helpers.py):
   - GraphShape dual representation (topology + geometry)
   - TopologicPy Cluster + Graph
   - Transformation rules framework (not fully implemented)
   - Focus: Graph transformations that modify geometric layouts

2. **Phase 3 Architecture** (core.py):
   - LayoutState mutable transformation substrate
   - Individual Shape wrappers around TopologicPy Faces
   - Shape grammar transformations (circle → rectangle → arranged)
   - Focus: Geometric transformations with lightweight graph tracking

**Key Difference**: Phase 2 = Graph-centric (transform graph, geometry follows) vs Phase 3 = Geometry-centric (transform shapes, track adjacencies)

---

## Comparative Architecture Table

| **Aspect** | **core.py (Phase 3)** | **rules.py (Phase 2)** | **topologic_helpers.py** | **shapes.py** |
|------------|----------------------|------------------------|--------------------------|---------------|
| **Purpose** | Shape grammar transformation substrate | Graph-shape dual transformations | TopologicPy convenience wrappers | Deprecated legacy interface |
| **Lines of Code** | 963 | 575 | 439 | 71 (deprecation notice) |
| **Primary Data Structure** | `LayoutState` (dict of Shapes + edges) | `GraphShape` (Cluster + Graph dual) | Standalone helper functions | N/A (deprecated) |
| **Geometric Primitive** | TopologicPy `Face` wrapped in `Shape` | TopologicPy `Face` in `Cluster` | Raw TopologicPy `Face` | N/A |
| **Topology Representation** | Lightweight `LayoutEdge` list | Full TopologicPy `Graph` | Graph construction helper | N/A |
| **Metadata Storage** | Both `Shape.metadata` dict + `Face` Dictionary | Only TopologicPy `Dictionary` | Only TopologicPy `Dictionary` | N/A |
| **Shape Types** | Enum: CIRCLE, RECTANGLE, L/T/U_SHAPE | Not typed (generic Faces) | Not typed | N/A |
| **Shape Creation** | 6 builder functions (circle, rect, L, T, U, polygon) | 2 helper functions (rectangular_face, square_face) | Same 2 helpers | N/A |
| **Phase System** | Yes: BUBBLE → RECTANGLES → ARRANGED → REFINED | No phase concept | N/A | N/A |
| **Transformation Model** | Sequential shape transformations | Graph rule application (pattern + transform) | N/A (utilities only) | N/A |
| **Validation** | LayoutState.validate() (area, edges) | GraphShape.validate() (overlaps, adjacency) | N/A | N/A |
| **Dependencies** | TopologicPy + dataclasses + enum | TopologicPy + Pydantic + topologic_helpers | TopologicPy only | N/A |
| **State Mutability** | Mutable (LayoutState editable) | Immutable (transformations return new GraphShape) | N/A | N/A |
| **Visualization Integration** | Via Topology.Show() | Via Topology.Show() or Plotly | N/A | N/A |
| **Status** | ✅ Active development (Phase 3) | ✅ Stable (Phase 2) | ✅ Active (shared utility) | ❌ Deprecated |

---

## Detailed Structural Analysis

### 1. **core.py** (Phase 3 Shape Grammar System)

**Architecture Pattern**: Three-layer geometry + transformation substrate

```
Layer 1: TopologicPy Primitive Helpers (Lines 41-176)
├── vertex_coordinates(), create_vertex()
├── distance_between_vertices()
├── face_area(), face_centroid(), face_vertices(), face_edges()
└── Purpose: Wrap TopologicPy API for ergonomics

Layer 2: Shape Builders (Lines 177-510)
├── create_circle_face()      # 32-segment polygon
├── create_rectangle_face()   # 4 vertices + rotation
├── create_lshape_face()      # 6 vertices
├── create_tshape_face()      # 8 vertices
├── create_ushape_face()      # 8 vertices
├── create_polygon_face()     # Generic N-gon
└── Purpose: Build TopologicPy Faces with attached metadata

Layer 3: Layout Structures (Lines 511-892)
├── ShapeType (enum)          # CIRCLE, RECTANGLE, L_SHAPE, etc.
├── Phase (enum)              # BUBBLE, RECTANGLES, ARRANGED, REFINED
├── Shape (dataclass)         # Wraps Face + metadata + room_type
├── LayoutEdge (dataclass)    # source_id, target_id, relation
├── LayoutState (dataclass)   # Collection of Shapes + edges
│   ├── add_shape(), remove_shape()
│   ├── add_edge(), get_neighbors()
│   ├── bounds(), total_area()
│   └── validate()
└── Purpose: Mutable transformation substrate

Convenience Functions (Lines 893-963)
├── create_circle_shape()
├── create_rectangle_shape()
└── Purpose: Quick Shape creation from parameters
```

**Key Design Decisions**:
1. **Shape wrapper class** provides dual storage: `Face` (TopologicPy geometry) + `metadata` (Python dict)
2. **LayoutState mutability** enables incremental transformations (add/remove shapes)
3. **Shape recognition** via vertex count heuristics (4=rect, 6=L, 8=T/U, 32+=circle)
4. **Phase tracking** guides transformation pipeline
5. **Lightweight edges** (just ID pairs) instead of full TopologicPy Graph

---

### 2. **rules.py** (Phase 2 Graph-Shape Dual System)

**Architecture Pattern**: Graph-centric transformation rules

```
GraphShape Class (Lines 54-435)
├── Core Data:
│   ├── cluster: Cluster       # Face geometries
│   ├── graph: Graph           # Topology (vertices at centroids)
│   └── Invariants: graph ↔ geometry consistency
│
├── Queries (Lines 100-181):
│   ├── faces(), vertices(), edges()
│   ├── num_nodes(), num_edges(), total_area()
│   ├── bounding_box()
│   ├── get_face_by_label(), get_vertex_by_label()
│   ├── get_neighbors(), degree()
│   └── Purpose: Query both representations
│
├── Validation (Lines 186-278):
│   ├── find_overlaps()
│   ├── find_missing_adjacencies()
│   ├── validate()
│   └── Purpose: Check graph ↔ shape consistency
│
└── Factory Methods (Lines 283-435):
    ├── from_faces_and_adjacencies()
    ├── from_grid()            # Grid subdivision
    ├── from_horizontal_split() # Linear subdivision
    └── Purpose: Create valid GraphShape instances

GraphShapeRule Class (Lines 442-491)
├── name, description
├── pattern: (GraphShape, node) -> bool
├── transform: (GraphShape, node, params) -> GraphShape
├── can_apply(), apply()
└── Purpose: Define reusable transformation rules

RuleLibrary Class (Lines 493-543)
├── split_horizontal()
└── Purpose: Standard rule catalog (NOT IMPLEMENTED)

Utilities (Lines 549-575)
├── apply_rule_to_all_nodes()
├── find_applicable_nodes()
└── Purpose: Batch rule application
```

**Key Design Decisions**:
1. **Dual representation** maintains both Cluster (geometry) and Graph (topology) in sync
2. **Pydantic model** for data validation (vs dataclass in core.py)
3. **Immutable transformations** (rules return new GraphShape instances)
4. **Pattern matching** framework for rule applicability
5. **TopologicPy Graph** for full topology (vs lightweight edges in core.py)
6. **Factory methods** for common layout patterns (grid, horizontal split)

---

### 3. **topologic_helpers.py** (Shared Utility Layer)

**Architecture Pattern**: Pure functional helpers

```
Face Creation (Lines 24-106)
├── rectangular_face(width, height, origin, label, **metadata)
├── square_face(size, origin, label, **metadata)
└── Purpose: Create Faces with attached Dictionaries

Metadata Utilities (Lines 112-199)
├── get_metadata(topology, key, default)
├── set_metadata(topology, **kwargs)
├── get_all_metadata(topology) -> dict
└── Purpose: TopologicPy Dictionary abstraction

Geometric Queries (Lines 205-318)
├── face_centroid(face) -> Vertex
├── faces_adjacent(face1, face2, tolerance) -> bool
├── faces_overlap(face1, face2, tolerance) -> bool
├── face_area(face) -> float
├── faces_bounding_box(faces) -> (min_x, min_y, max_x, max_y)
└── Purpose: Delegate to TopologicPy geometry methods

Graph Construction (Lines 324-392)
├── graph_from_faces_and_adjacencies(faces, adjacencies) -> Graph
└── Purpose: Build TopologicPy Graph from Face list

Vertex Utilities (Lines 398-439)
├── vertex_coordinates(vertex) -> (x, y, z)
├── vertex_at(x, y, z, **metadata) -> Vertex
└── Purpose: Vertex creation and coordinate extraction
```

**Key Design Decisions**:
1. **No state** - all functions pure (input → output)
2. **Thin wrappers** around TopologicPy API (ergonomics layer)
3. **Shared by both architectures** (rules.py and core.py both import)
4. **Type hints** using Python 3.10+ syntax (`list[Face]` vs `List[Face]`)
5. **Keyword arguments** for metadata flexibility

---

### 4. **shapes.py** (Deprecated)

**Status**: Migration guide only (71 lines of deprecation warnings)

**Purpose**:
- Provides backward compatibility imports from archive
- Documents migration path from old Rectangle/Point classes to TopologicPy-native Faces
- Warns users to use topologic_helpers.py instead

**Historical Context**:
- Original architecture used custom `Rectangle`, `Point`, `Square` classes
- Refactored in v0.2.0 to use TopologicPy primitives directly
- Reduced code from ~700 lines to 300 lines of helpers

---

## Syntax & Style Comparison

| **Aspect** | **core.py** | **rules.py** | **topologic_helpers.py** |
|------------|-------------|--------------|--------------------------|
| **Imports** | Standard lib + TopologicPy | Pydantic + TopologicPy + helpers | TopologicPy only |
| **Type Hints** | Extensive (List, Dict, Tuple, Optional) | Extensive (Pydantic models) | Extensive (3.10+ syntax) |
| **Classes** | 4 (enums + dataclasses) | 3 (Pydantic models + dataclass) | 0 (functions only) |
| **Dataclasses** | 3 (Shape, LayoutEdge, LayoutState) | 1 (GraphShapeRule) | 0 |
| **Pydantic Models** | 0 | 1 (GraphShape) | 0 |
| **Enums** | 2 (Phase, ShapeType) | 0 | 0 |
| **Functions** | 30+ (helpers + builders + convenience) | 5 (utilities) | 15 (pure helpers) |
| **Methods** | 20+ (LayoutState methods) | 15+ (GraphShape methods) | N/A |
| **Docstrings** | ✅ Google style with examples | ✅ Google style with examples | ✅ Google style with examples |
| **Comments** | Heavy (architectural boundaries) | Moderate | Light (self-documenting) |
| **Line Length** | <100 chars | <100 chars | <100 chars |
| **Naming Convention** | snake_case (functions), PascalCase (classes) | Same | Same |

---

## Functional Overlap Analysis

### Functions Present in BOTH core.py and topologic_helpers.py:

| **Function** | **core.py** | **topologic_helpers.py** | **Difference** |
|--------------|-------------|--------------------------|----------------|
| `face_area()` | Line 93 | Line 273 | Identical (both delegate to `Face.Area()`) |
| `face_centroid()` | Line 101 | Line 205 | Identical (both delegate to `Topology.Centroid()`) |
| `vertex_coordinates()` | Line 48 | Line 398 | Identical (both delegate to `Vertex.Coordinates()`) |
| `create_vertex()` | Line 57 | None | core.py has, helpers doesn't |
| `rectangular_face()` | None (create_rectangle_face) | Line 24 | **Different**: core.py has rotation param, helpers doesn't |

**Observation**: **CODE DUPLICATION DETECTED**
- `face_area`, `face_centroid`, `vertex_coordinates` are duplicated
- core.py SHOULD import from topologic_helpers.py instead
- Duplication increases maintenance burden

---

## Metadata Storage Comparison

### Phase 2 (rules.py + helpers): Single Source (TopologicPy Dictionary)

```python
# Create face with metadata
face = rectangular_face(5, 4, label="Kitchen", area=20, floor=2)

# Retrieve metadata
label = get_metadata(face, "label")           # "Kitchen"
area = get_metadata(face, "area")             # 20
all_meta = get_all_metadata(face)             # {'label': 'Kitchen', ...}
```

**Pros**:
- ✅ Single source of truth
- ✅ Persists through TopologicPy operations
- ✅ Serializable with TopologicPy exports

**Cons**:
- ❌ Slower access (Dictionary.Keys() + index lookup)
- ❌ No type safety

---

### Phase 3 (core.py): Dual Storage (Shape dict + Face Dictionary)

```python
# Create shape
shape = create_rectangle_shape(
    shape_id="s1",
    room_type="Kitchen",
    center_x=5.0,
    center_y=5.0,
    width=4.0,
    height=5.0
)

# Access metadata
shape.room_type                                # "Kitchen" (Python attribute)
shape.target_area                              # 20.0 (Python attribute)
shape.area                                     # 20.0 (computed from Face)
shape.metadata["custom_key"]                   # Custom data (Python dict)

# Face Dictionary still exists
get_metadata(shape.face, "room_type")          # "Kitchen" (from Dictionary)
```

**Pros**:
- ✅ Fast Python attribute access
- ✅ Type-safe properties (IDE autocomplete)
- ✅ Separation of semantics (room_type) vs geometry (Face)

**Cons**:
- ❌ Dual storage (can get out of sync)
- ❌ Larger memory footprint
- ❌ Shape wrapper not serializable (only Face is)

---

## Transformation Philosophy Comparison

### Phase 2 (rules.py): Graph-Centric Rules

**Model**:
```
User → Rule → GraphShape → New GraphShape
         ↓
   Pattern Match (node fits rule?)
         ↓
   Transform (graph + shapes simultaneously)
         ↓
   Return new instance (immutable)
```

**Example**:
```python
# Define rule
split_rule = RuleLibrary.split_horizontal(ratio=0.5)

# Apply to node "n0" in existing graph-shape
new_gs = split_rule.apply(graphshape, "n0")

# Original graphshape unchanged (immutable)
assert graphshape.num_nodes() == 1
assert new_gs.num_nodes() == 2  # n0 split into n0_L, n0_R
```

**Use Cases**:
- ✅ Graph subdivisions (split, merge, extrude)
- ✅ Rule-based generative design
- ✅ Reversible transformations (transform stack)

---

### Phase 3 (core.py): Geometry-Centric Transformations

**Model**:
```
Bubble Diagram → Circle Packing
       ↓
LayoutState (BUBBLE phase)
       ↓
Transform: Circle → Rectangle (shape substitution)
       ↓
LayoutState (RECTANGLES phase)
       ↓
Transform: Align + Arrange (positional adjustment)
       ↓
LayoutState (ARRANGED phase)
       ↓
Transform: Refine edges (topology cleanup)
       ↓
LayoutState (REFINED phase) → Export
```

**Example**:
```python
# Start with circles from bubble diagram
layout = LayoutState(phase=Phase.BUBBLE)
layout.add_shape(create_circle_shape("s0", "Kitchen", 0, 0, 2.5))
layout.add_shape(create_circle_shape("s1", "Living", 6, 0, 3.0))
layout.add_edge(LayoutEdge("s0", "s1", "CONNECTS"))

# Transform: Convert circles to rectangles
for shape_id, shape in layout.shapes.items():
    if shape.shape_type == ShapeType.CIRCLE:
        # Create rectangle with same area
        rect_shape = circle_to_rectangle(shape)
        layout.shapes[shape_id] = rect_shape

layout.phase = Phase.RECTANGLES

# Transform: Arrange rectangles (align adjacencies)
align_rectangles(layout)
layout.phase = Phase.ARRANGED
```

**Use Cases**:
- ✅ Sequential transformations (pipeline)
- ✅ Shape substitution (circle → rectangle)
- ✅ Geometric arrangement (packing, alignment)

---

## Validation Strategy Comparison

### Phase 2 (rules.py): Dual Consistency Checking

```python
is_valid, issues = graphshape.validate(tolerance=0.01)

# Checks:
# 1. No overlapping Faces
# 2. Graph edges ↔ geometric adjacency
# 3. All graph vertices have corresponding Faces
```

**Focus**: Graph-shape consistency (invariant maintenance)

---

### Phase 3 (core.py): Area Preservation + Edge Validity

```python
issues = layout_state.validate(area_tolerance=0.10)

# Checks:
# 1. All shapes have positive area
# 2. Area error < 10% (actual vs target)
# 3. Edges reference existing shapes
```

**Focus**: Transformation quality (area preservation, valid references)

---

## Import Dependency Graph

```
core.py
  └── TopologicPy (direct)

rules.py
  ├── TopologicPy (direct)
  ├── Pydantic (data validation)
  └── topologic_helpers.py (face creation, metadata, graph construction)

topologic_helpers.py
  └── TopologicPy (direct)

shapes.py
  └── archive.shapes_deprecated (backward compatibility)
```

**Observation**:
- ❌ core.py does NOT import topologic_helpers.py (misses shared utilities)
- ✅ rules.py correctly imports topologic_helpers.py
- ⚠️ Code duplication between core.py and topologic_helpers.py

---

## Recommendations for Unification

### 1. **Eliminate Duplication**

**Action**: Make core.py import from topologic_helpers.py

```python
# core.py (lines 41-176)
# BEFORE: Custom implementations
def face_area(face: Face) -> float:
    area = Face.Area(face)
    return area if area is not None else 0.0

# AFTER: Import from helpers
from .topologic_helpers import (
    face_area,
    face_centroid,
    vertex_coordinates,
    rectangular_face,
    get_metadata,
    set_metadata,
)
```

**Impact**: Reduces core.py by ~100 lines

---

### 2. **Consolidate Shape Builders**

**Action**: Move shape builders from core.py to topologic_helpers.py

```python
# topologic_helpers.py (new section)

def circle_face(center_x, center_y, radius, num_segments=32, label=None, **metadata):
    """Create circular Face (polygon approximation)."""
    # Implementation from core.py create_circle_face()
    ...

def lshape_face(center_x, center_y, arm1_length, arm1_width, ...):
    """Create L-shaped Face."""
    # Implementation from core.py create_lshape_face()
    ...

# ... T-shape, U-shape, polygon
```

**Impact**:
- ✅ Shared builders available to both architectures
- ✅ Single source of truth for shape creation
- ✅ core.py focuses on LayoutState logic only

---

### 3. **Bridge Phase 2 ↔ Phase 3**

**Action**: Add conversion functions

```python
# converters.py (NEW MODULE)

def layout_state_to_graph_shape(layout: LayoutState) -> GraphShape:
    """Convert LayoutState to GraphShape for validation."""
    faces = [shape.face for shape in layout.shapes.values()]
    adjacencies = [(e.source_id, e.target_id) for e in layout.edges]
    return GraphShape.from_faces_and_adjacencies(faces, adjacencies)

def graph_shape_to_layout_state(gs: GraphShape, phase: Phase) -> LayoutState:
    """Convert GraphShape to LayoutState for transformation."""
    shapes = {}
    for face in gs.faces():
        label = get_metadata(face, "label")
        room_type = get_metadata(face, "room_type", label)
        area = face_area(face)

        shape = Shape(
            id=label,
            face=face,
            room_type=room_type,
            target_area=area,
            shape_type=recognize_shape_type(face)
        )
        shapes[label] = shape

    # Extract edges from graph
    edges = []
    for graph_edge in gs.edges():
        verts = Edge.Vertices(graph_edge)
        label1 = get_metadata(verts[0], "label")
        label2 = get_metadata(verts[1], "label")
        edges.append(LayoutEdge(label1, label2, "CONNECTS"))

    return LayoutState(phase=phase, shapes=shapes, edges=edges)
```

**Impact**:
- ✅ Use GraphShape validation in Phase 3
- ✅ Use LayoutState transformations in Phase 2
- ✅ Best of both worlds

---

### 4. **Standardize Metadata Strategy**

**Decision Required**: Choose ONE approach

**Option A: TopologicPy Dictionary Only** (Phase 2 style)
- ✅ Simpler
- ❌ Slower access

**Option B: Hybrid (Python dict + Dictionary)** (Phase 3 style)
- ✅ Fast access
- ❌ Dual storage complexity

**Recommendation**: Keep hybrid BUT add sync mechanism

```python
# Shape class (core.py)
def sync_to_face(self):
    """Synchronize Python metadata to Face Dictionary."""
    set_metadata(
        self.face,
        room_type=self.room_type,
        target_area=self.target_area,
        shape_type=self.shape_type.name,
        **self.metadata
    )

def sync_from_face(self):
    """Load Python metadata from Face Dictionary."""
    self.room_type = get_metadata(self.face, "room_type", self.room_type)
    self.target_area = get_metadata(self.face, "target_area", self.target_area)
    # ...
```

---

## Summary: Architecture Evolution

### Phase 1 (Deprecated)
- Custom Rectangle/Point classes
- No TopologicPy integration
- ~700 lines of geometry code

### Phase 2 (rules.py + topologic_helpers.py)
- **Graph-centric** dual representation
- TopologicPy primitives throughout
- Rule-based transformations (framework only)
- Immutable transformations
- ~1000 lines total

### Phase 3 (core.py)
- **Geometry-centric** transformation substrate
- Shape grammar pipeline (BUBBLE → RECTANGLES → ARRANGED → REFINED)
- Mutable LayoutState
- Rich shape typing (CIRCLE, L/T/U-shapes)
- ~963 lines (with duplication)

### Ideal Future (Unified)
- Shared utilities (topologic_helpers.py)
- Dual architectures available:
  - GraphShape for rule-based transformations
  - LayoutState for sequential pipelines
- Converters between representations
- No code duplication
- ~1200 lines total (net reduction)

---

## Key Insights

`★ Insight ─────────────────────────────────────`
**Architectural Duality Reflects Use Cases**

The two architectures aren't competing - they solve different problems:

1. **GraphShape (rules.py)** = Spatial planning system
   - "Split this room in half"
   - "Merge these two adjacent spaces"
   - "Subdivide layout into grid"
   - Focus: Topological operations on existing geometry

2. **LayoutState (core.py)** = Generative synthesis system
   - "Convert bubble diagram to floor plan"
   - "Arrange these rectangles to minimize gaps"
   - "Refine this layout to match constraints"
   - Focus: Sequential geometric transformations

The duplication exists because core.py was developed independently without leveraging the existing Phase 2 infrastructure. Proper integration would give users BOTH tools in a unified system.
`─────────────────────────────────────────────────`

---

**End of Analysis**
