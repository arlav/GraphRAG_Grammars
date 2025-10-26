Topologic Graph Retrieval Augmented Generation + Grammars

## Executive Summary

This document outlines a comprehensive development plan for building a **Topologic GraphRAg system including shape** that generate layout graphs out of a graph database and then the layout itself.

Based on analysis of existing code and documentation, this project will implement a **jupyter notebook series** with distinct steps ensuring high maintainability, testability, and extensibility.


## Development Philosophy

- **Simplicity**: Write simple, straightforward code
- **Readability**: Make code easy to understand
- **Performance**: Consider performance without sacrificing readability
- **Maintainability**: Write code that's easy to update
- **Testability**: Ensure code is testable
- **Reusability**: Create reusable components and functions
- **Less Code = Less Debt**: Minimize code footprint

## Coding Best Practices

- **Early Returns**: Use to avoid nested conditions
- **Descriptive Names**: Use clear variable/function names (prefix handlers with "handle")
- **Constants Over Functions**: Use constants where possible
- **DRY Code**: Don't repeat yourself
- **Functional Style**: Prefer functional, immutable approaches when not verbose
- **Minimal Changes**: Only modify code related to the task at hand
- **Function Ordering**: Define composing functions before their components
- **TODO Comments**: Mark issues in existing code with "TODO:" prefix
- **Simplicity**: Prioritize simplicity and readability over clever solutions
- **Build Iteratively** Start with minimal functionality and verify it works before adding complexity
- **Run Tests**: Test your code frequently with realistic inputs and validate outputs
- **Build Test Environments**: Create testing environments for components that are difficult to validate directly
- **Functional Code**: Use functional and stateless approaches where they improve clarity
- **Clean logic**: Keep core logic clean and push implementation details to the edges
- **File Organsiation**: Balance file organization with simplicity - use an appropriate number of files for the project scale

## System Architecture

- use pydantic
- use topologicpy 
- use kuzu
- use streamlit

## Project Vision

Create a production-ready application that bridges the gap between:
- **SciKit Geometry** (Geometry Procdessing)
- **COMPAS framework** (Computational design)
- **Graph Analytics** (TopologicPy processing)
- **Graph Storage** (Kuzu graph database)
- **Blockchain Integration** (Ethereum tokenization)


## Codebases to use

- [TopologicPy](https://github.com/wassimj/topologicpy)
- [Kuzu](https://github.com/kuzudb/kuzu)
- [SciKit](https://github.com/scikit-geometry/scikit-geometry)
- [compas](Main library of the COMPAS framework and CAD integrations for Rhino/GH and Blender.)

## Previous files
- check the /previous files folders for good examples


## Current State Analysis

## Schema to use


### Existing Assets
- **README.md**: Well-defined architecture and feature requirements
- **Previous Work**: 
  - `graph_topo.py`: Comprehensive IFC processing with TopologicPy (1,465 lines)
  - `IFC_FIXES.md`: Detailed analysis of processing issues and solutions
  - `JSON_LD_Documentation.md`: JSON-LD export specifications -use these for the RDF exports
  - `GraphByIFCPath.ipynb`: Working Jupyter notebooks
  - `RDF_BOT_Export`: RDF export example
  - `RDF_BOT_Import`: RDF import example
  - `graph_topo_ld_graph.py` : Linked Data Schema example
  
### Key Insights from Previous Work


## Detailed Development Plan

### Phase 1: GraphRAG System Development ✅ COMPLETE

**Status**: ✅ **COMPLETE** (2025-10-26)

**Achievements**:
- ✅ Migrated from OpenAI to Claude API (Anthropic)
- ✅ Implemented graph validation (connectivity, completeness)
- ✅ Advanced v03 features (degree-based expansion, spatial prediction)
- ✅ Working notebook: `Kuzu_GraphRAG_03.ipynb`
- ✅ Dataset: 4,572 Swiss apartment floor plans loaded in Kuzu

**Capabilities**:
- Generate valid apartment adjacency graphs from dataset patterns
- Validate graphs for architectural correctness
- Predict spatial coordinates for new rooms
- Support diverse apartment types (studio, 1BR-4BR)

**See**: `PHASE1_ANALYSIS.md` for detailed documentation

---

### Phase 2: Graph-to-Shape Grammar System 🚧 IN PROGRESS

**Goal**: Transform abstract adjacency graphs into 2D geometric floor plans using shape grammar rules

**Input**: Valid apartment adjacency graph from Phase 1 (nodes + edges)
**Output**: 2D floor plan with positioned rooms as polygons

#### Overview

Phase 2 bridges the gap between:
- **Abstract topology** (Phase 1): "Kitchen connects to Living Room"
- **Concrete geometry** (Phase 2): Kitchen polygon (4m × 3m) placed adjacent to Living Room polygon (5m × 4m)

**Key Challenge**: Given only a graph (nodes = rooms, edges = adjacencies), generate plausible 2D room polygons that:
1. **Respect adjacencies**: Connected rooms share boundaries
2. **Respect areas**: Room size matches inherited area metadata (e.g., bedroom ≈ 13m²)
3. **Create valid geometry**: No overlaps, no gaps, proper topology
4. **Look plausible**: Rooms are approximately rectangular with reasonable proportions

---

#### Phase 2 Architecture

```
Phase 1 Graph                Shape Grammar             2D Floor Plan
┌─────────────┐             ┌──────────────┐          ┌──────────────┐
│ n0:Entrance │────────────▶│ 1. Room       │─────────▶│ ┌──┐ ┌────┐ │
│ n1:Kitchen  │             │    Shapes     │          │ │En│ │Kit │ │
│ n2:Living   │             │ 2. Placement  │          │ └──┘ └────┘ │
│ n3:Bedroom  │             │    Rules      │          │   ┌────────┐│
│             │             │ 3. Alignment  │          │   │ Living ││
│ edges:      │             │ 4. Refinement │          │   └────────┘│
│ En─Kit      │             │                │          │ ┌─────────┐ │
│ Kit─Living  │             └──────────────┘          │ │ Bedroom │ │
│ En─Living   │                                       │ └─────────┘ │
│ Living─Bed  │                                       └──────────────┘
└─────────────┘
```

---

#### Phase 2.1: Parametric Room Shape Library

**Goal**: Create a library of 2D parametric shapes representing different room types

**Approach**: Rectangular rooms with area and aspect ratio constraints

##### Implementation

```python
from dataclasses import dataclass
from typing import Tuple, List
import math

@dataclass
class RoomShape:
    """Parametric 2D room shape (rectangle for simplicity)"""
    room_type: str          # "Kitchen", "Bedroom", etc.
    target_area: float      # Target area in m² (from graph metadata)
    aspect_ratio: float     # Width/height ratio (1.0 = square, 1.5 = 3:2)
    width: float            # Computed width
    height: float           # Computed height

    @classmethod
    def from_area_and_aspect(cls, room_type: str, area: float, aspect: float = 1.2):
        """Create rectangular room from area and aspect ratio"""
        # area = width * height
        # aspect = width / height
        # => height = sqrt(area / aspect)
        # => width = aspect * height
        height = math.sqrt(area / aspect)
        width = aspect * height
        return cls(room_type, area, aspect, width, height)

    def to_polygon(self, origin: Tuple[float, float] = (0, 0)) -> List[Tuple[float, float]]:
        """Convert to polygon (4 corners) at given origin"""
        x, y = origin
        return [
            (x, y),
            (x + self.width, y),
            (x + self.width, y + self.height),
            (x, y + self.height)
        ]

# Room type defaults (from Swiss dataset analysis)
ROOM_DEFAULTS = {
    "Entrance": {"area": 4.0, "aspect": 1.0},    # Small, square
    "Kitchen": {"area": 8.0, "aspect": 1.2},     # Rectangular
    "Living": {"area": 20.0, "aspect": 1.5},     # Large, rectangular
    "Bedroom": {"area": 13.0, "aspect": 1.3},    # Medium, rectangular
    "Bathroom": {"area": 5.0, "aspect": 1.0},    # Small, square
    "Corridor": {"area": 3.0, "aspect": 2.5},    # Long, narrow
    "Balcony": {"area": 6.0, "aspect": 1.8},     # Rectangular
}

def create_room_shape(node: dict) -> RoomShape:
    """Create room shape from graph node metadata"""
    room_type = node.get("label", "Room")

    # Use inherited area from dataset if available
    props = node.get("props", {})
    if isinstance(props, str):
        props = json.loads(props)
    area = props.get("area", ROOM_DEFAULTS.get(room_type, {}).get("area", 10.0))
    aspect = ROOM_DEFAULTS.get(room_type, {}).get("aspect", 1.2)

    return RoomShape.from_area_and_aspect(room_type, area, aspect)
```

**Deliverable P2.1**:
- [ ] `RoomShape` dataclass with area/aspect parameterization
- [ ] `ROOM_DEFAULTS` dictionary with Swiss dataset statistics
- [ ] `create_room_shape()` function using graph metadata
- [ ] Test: Generate shapes for all room types, verify areas match

---

#### Phase 2.2: Initial Placement Algorithm

**Goal**: Place room shapes on a 2D canvas using graph structure

**Approach**: Start from seed room (entrance), expand breadth-first following adjacencies

##### Algorithm: BFS-Based Placement

```python
from collections import deque
from typing import Dict, Set, Tuple

@dataclass
class PlacedRoom:
    """Room with position on 2D canvas"""
    shape: RoomShape
    origin: Tuple[float, float]  # Bottom-left corner
    polygon: List[Tuple[float, float]]

def place_rooms_bfs(graph_nodes: list, graph_edges: list, seed_id: str = "n0") -> Dict[str, PlacedRoom]:
    """
    Place rooms on 2D canvas using BFS traversal of graph.

    Strategy:
    1. Place seed room at origin (0, 0)
    2. For each placed room, find unplaced neighbors
    3. Place neighbors adjacent to current room (right, top, left, bottom)
    4. Repeat until all rooms placed
    """
    # Create shapes for all nodes
    shapes = {n["id"]: create_room_shape(n) for n in graph_nodes}

    # Build adjacency list
    adj = {n["id"]: [] for n in graph_nodes}
    for edge in graph_edges:
        a, b = edge["a"], edge["b"]
        adj[a].append(b)
        adj[b].append(a)

    # Track placement
    placed: Dict[str, PlacedRoom] = {}
    queue = deque([seed_id])
    placed_set: Set[str] = {seed_id}

    # Place seed at origin
    seed_shape = shapes[seed_id]
    placed[seed_id] = PlacedRoom(
        shape=seed_shape,
        origin=(0, 0),
        polygon=seed_shape.to_polygon((0, 0))
    )

    # BFS placement
    direction_idx = 0  # Cycle through: right, top, left, bottom
    while queue:
        current_id = queue.popleft()
        current_room = placed[current_id]

        # Find unplaced neighbors
        for neighbor_id in adj[current_id]:
            if neighbor_id in placed_set:
                continue

            # Compute placement position (cycle through directions)
            neighbor_shape = shapes[neighbor_id]
            new_origin = compute_adjacent_position(
                current_room,
                neighbor_shape,
                direction=direction_idx % 4
            )

            # Place neighbor
            placed[neighbor_id] = PlacedRoom(
                shape=neighbor_shape,
                origin=new_origin,
                polygon=neighbor_shape.to_polygon(new_origin)
            )
            placed_set.add(neighbor_id)
            queue.append(neighbor_id)
            direction_idx += 1

    return placed

def compute_adjacent_position(
    current: PlacedRoom,
    neighbor_shape: RoomShape,
    direction: int
) -> Tuple[float, float]:
    """
    Compute position for neighbor adjacent to current room.
    Direction: 0=right, 1=top, 2=left, 3=bottom
    """
    x, y = current.origin
    w, h = current.shape.width, current.shape.height

    if direction == 0:  # Right
        return (x + w, y)
    elif direction == 1:  # Top
        return (x, y + h)
    elif direction == 2:  # Left
        return (x - neighbor_shape.width, y)
    else:  # Bottom
        return (x, y - neighbor_shape.height)
```

**Deliverable P2.2**:
- [ ] `PlacedRoom` dataclass with position + polygon
- [ ] `place_rooms_bfs()` function using graph adjacency
- [ ] `compute_adjacent_position()` for directional placement
- [ ] Test: Place simple 3-room graph, visualize with matplotlib
- [ ] Test: Place complex 8-room apartment, check all rooms placed

---

#### Phase 2.3: Boundary Alignment & Topology Refinement

**Goal**: Adjust room positions so adjacent rooms share boundaries (no gaps, no overlaps)

**Challenge**: Initial BFS placement creates gaps between rooms. Need to "snap" boundaries together.

##### Approach: Edge-Aligned Adjustment

```python
def align_shared_boundaries(placed_rooms: Dict[str, PlacedRoom], edges: list) -> Dict[str, PlacedRoom]:
    """
    Adjust room positions so adjacent rooms share boundaries.

    Strategy:
    1. For each edge (a, b), find shared boundary segment
    2. Compute gap/overlap distance
    3. Adjust room b to align with room a
    4. Propagate adjustments to connected rooms
    """
    adjusted = placed_rooms.copy()

    for edge in edges:
        room_a = adjusted[edge["a"]]
        room_b = adjusted[edge["b"]]

        # Find closest edge pair between polygons
        edge_a, edge_b = find_closest_edges(room_a.polygon, room_b.polygon)

        # Compute alignment offset
        offset = compute_alignment_offset(edge_a, edge_b)

        # Shift room_b to align with room_a
        adjusted[edge["b"]] = shift_room(room_b, offset)

    return adjusted

def find_closest_edges(poly_a: list, poly_b: list) -> Tuple[Tuple, Tuple]:
    """Find closest edge pair between two polygons"""
    # For rectangles: 4 edges each, find pair with minimum distance
    # Returns: ((a_start, a_end), (b_start, b_end))
    pass  # Implementation using edge-to-edge distance

def compute_alignment_offset(edge_a: Tuple, edge_b: Tuple) -> Tuple[float, float]:
    """Compute (dx, dy) to align edge_b with edge_a"""
    # Project edge_b onto edge_a, compute gap distance
    pass

def shift_room(room: PlacedRoom, offset: Tuple[float, float]) -> PlacedRoom:
    """Shift room by offset, update origin and polygon"""
    new_origin = (room.origin[0] + offset[0], room.origin[1] + offset[1])
    return PlacedRoom(
        shape=room.shape,
        origin=new_origin,
        polygon=room.shape.to_polygon(new_origin)
    )
```

**Deliverable P2.3**:
- [ ] `align_shared_boundaries()` function
- [ ] `find_closest_edges()` for polygon pairs
- [ ] `compute_alignment_offset()` using edge projection
- [ ] `shift_room()` helper function
- [ ] Test: Align 2-room graph, verify no gap
- [ ] Test: Align 4-room graph (Kitchen-Living-Bedroom-Bath), visualize

---

#### Phase 2.4: Parametric Variation & Optimization

**Goal**: Add variation to generated floor plans through parameter tuning

##### Variation Strategies

1. **Aspect Ratio Variation**
   - Randomize aspect ratios within bounds (e.g., 1.0-1.5 for bedrooms)
   - Creates visual diversity while maintaining area constraints

2. **Placement Direction Bias**
   - Prefer certain directions for specific room types
   - Example: Bedrooms prefer placement away from entrance

3. **Area Tolerance**
   - Allow ±10% area variation from target
   - More realistic room sizing

```python
import random

def create_room_shape_with_variation(node: dict, variation: float = 0.1) -> RoomShape:
    """Create room shape with parametric variation"""
    room_type = node.get("label", "Room")

    # Base parameters
    defaults = ROOM_DEFAULTS.get(room_type, {"area": 10.0, "aspect": 1.2})
    base_area = defaults["area"]
    base_aspect = defaults["aspect"]

    # Add variation
    area = base_area * random.uniform(1 - variation, 1 + variation)
    aspect = base_aspect * random.uniform(0.9, 1.3)  # Wider variation for aspect

    return RoomShape.from_area_and_aspect(room_type, area, aspect)

def place_rooms_with_smart_directions(
    graph_nodes: list,
    graph_edges: list,
    seed_id: str = "n0"
) -> Dict[str, PlacedRoom]:
    """
    Enhanced BFS placement with room-type-specific direction preferences.

    Example rules:
    - Bedrooms prefer top/right (away from entrance)
    - Kitchens prefer left of living room
    - Bathrooms prefer compact corners
    """
    # Similar to place_rooms_bfs() but with direction scoring
    pass
```

**Deliverable P2.4**:
- [ ] `create_room_shape_with_variation()` with area/aspect randomization
- [ ] `place_rooms_with_smart_directions()` with direction preferences
- [ ] Direction preference rules for each room type
- [ ] Test: Generate 10 variants of same graph, verify diversity
- [ ] Test: Measure area variance, ensure within ±10%

---

#### Phase 2.5: Visualization & TopologicPy Integration

**Goal**: Visualize generated 2D floor plans and export to TopologicPy format

##### Matplotlib Visualization

```python
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon

def visualize_floor_plan(placed_rooms: Dict[str, PlacedRoom], edges: list):
    """
    Visualize floor plan with matplotlib.
    - Rooms as colored polygons
    - Labels at centroids
    - Edges as dashed lines
    """
    fig, ax = plt.subplots(figsize=(12, 12))

    # Room colors by type
    colors = {
        "Entrance": "#ff9999",
        "Kitchen": "#ffcc99",
        "Living": "#99ccff",
        "Bedroom": "#99ff99",
        "Bathroom": "#cc99ff",
        "Corridor": "#cccccc",
        "Balcony": "#ffffcc"
    }

    # Draw rooms
    for room_id, placed in placed_rooms.items():
        room_type = placed.shape.room_type
        poly = MplPolygon(
            placed.polygon,
            facecolor=colors.get(room_type, "#dddddd"),
            edgecolor="black",
            linewidth=2,
            alpha=0.7
        )
        ax.add_patch(poly)

        # Label at centroid
        cx = sum(p[0] for p in placed.polygon) / 4
        cy = sum(p[1] for p in placed.polygon) / 4
        ax.text(cx, cy, room_type, ha="center", va="center", fontsize=10, weight="bold")

    # Draw adjacency edges (dashed)
    for edge in edges:
        a_center = get_centroid(placed_rooms[edge["a"]].polygon)
        b_center = get_centroid(placed_rooms[edge["b"]].polygon)
        ax.plot([a_center[0], b_center[0]], [a_center[1], b_center[1]],
                'k--', alpha=0.3, linewidth=1)

    ax.set_aspect("equal")
    ax.set_title("Generated Floor Plan (Phase 2)", fontsize=16, weight="bold")
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()

def get_centroid(polygon: List[Tuple[float, float]]) -> Tuple[float, float]:
    """Compute polygon centroid"""
    n = len(polygon)
    cx = sum(p[0] for p in polygon) / n
    cy = sum(p[1] for p in polygon) / n
    return (cx, cy)
```

##### TopologicPy Export

```python
from topologicpy.Vertex import Vertex
from topologicpy.Face import Face
from topologicpy.Topology import Topology
from topologicpy.Dictionary import Dictionary

def export_to_topologic(placed_rooms: Dict[str, PlacedRoom]) -> list:
    """
    Convert placed rooms to TopologicPy Face objects.
    Each room becomes a Face with metadata dictionary.
    """
    faces = []

    for room_id, placed in placed_rooms.items():
        # Create vertices from polygon
        vertices = [Vertex.ByCoordinates(p[0], p[1], 0) for p in placed.polygon]

        # Create face
        face = Face.ByVertices(vertices)

        # Attach metadata dictionary
        metadata = {
            "room_id": room_id,
            "room_type": placed.shape.room_type,
            "area": placed.shape.target_area,
            "width": placed.shape.width,
            "height": placed.shape.height,
            "origin_x": placed.origin[0],
            "origin_y": placed.origin[1]
        }

        keys = list(metadata.keys())
        values = list(metadata.values())
        d = Dictionary.ByKeysValues(keys, values)
        face = Topology.SetDictionary(face, d)

        faces.append(face)

    return faces
```

**Deliverable P2.5**:
- [ ] `visualize_floor_plan()` with matplotlib
- [ ] Color coding by room type
- [ ] Room labels at centroids
- [ ] `export_to_topologic()` function
- [ ] Test: Visualize 5-room apartment
- [ ] Test: Export to TopologicPy, verify metadata preserved

---

#### Phase 2.6: End-to-End Integration

**Goal**: Connect Phase 1 (graph generation) → Phase 2 (shape grammar) in single notebook

##### Integration Notebook: `Phase2_Graph_to_Shape.ipynb`

```python
# Cell 1: Import Phase 1 graph
from Kuzu_GraphRAG_03 import graphrag_build_loop, snapshot_full_graph

# Generate graph using Phase 1
result = graphrag_build_loop(
    mgr,
    working_graph_id="work_phase2_test",
    start_label="Entrance",
    description="2 bedroom apartment",
    max_steps=10
)

# Extract final graph
final_graph_nodes = list_working_nodes(mgr, "work_phase2_test")
final_graph_edges = list_working_edges(mgr, "work_phase2_test")

# Cell 2: Generate 2D floor plan (Phase 2)
placed_rooms = place_rooms_bfs(final_graph_nodes, final_graph_edges)
aligned_rooms = align_shared_boundaries(placed_rooms, final_graph_edges)

# Cell 3: Visualize
visualize_floor_plan(aligned_rooms, final_graph_edges)

# Cell 4: Export
faces = export_to_topologic(aligned_rooms)
print(f"✅ Generated {len(faces)} room faces")
```

**Deliverable P2.6**:
- [ ] New notebook: `Phase2_Graph_to_Shape.ipynb`
- [ ] End-to-end pipeline from graph → 2D geometry
- [ ] Test with 5 different apartment types
- [ ] Validation: All rooms placed, no overlaps, adjacencies respected
- [ ] Export test: TopologicPy faces loadable in Phase 3

---

### Phase 2 Success Criteria

**Phase 2 Complete When**:

1. **Geometric Validity** ✅
   - All rooms from graph are placed as 2D polygons
   - No overlapping rooms
   - Adjacent rooms share boundaries (within tolerance)
   - Total area approximately matches sum of room areas

2. **Topological Correctness** ✅
   - Graph adjacencies preserved as geometric adjacencies
   - All connections from Phase 1 visible in 2D layout

3. **Visual Plausibility** ✅
   - Floor plans look "reasonable" to human eye
   - Rooms have realistic proportions
   - Layout follows common apartment patterns

4. **Parametric Flexibility** ✅
   - Can generate variations of same graph
   - Area/aspect parameters adjustable
   - Different placement strategies available

5. **Integration** ✅
   - Seamless connection to Phase 1 output
   - Export compatible with Phase 3 (3D extrusion)

---

### Phase 3: 3D Development (Future)



