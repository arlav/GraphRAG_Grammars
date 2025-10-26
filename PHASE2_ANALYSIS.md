# Phase 2: Graph-to-Shape Grammar System

## Executive Summary

**Goal**: Transform abstract adjacency graphs from Phase 1 into 2D geometric floor plans using shape grammar rules.

**Status**: 🚧 **IN PROGRESS** (Started: 2025-10-26)

**Input**: Valid apartment adjacency graph (nodes + edges) from `Kuzu_GraphRAG_03.ipynb`
**Output**: 2D floor plan with positioned room polygons

---

## Phase 2 Overview

### The Challenge

Phase 1 produces abstract topology:
```
Graph:
  Entrance → Kitchen
  Kitchen → Living Room
  Living Room → Bedroom
  Kitchen → Bathroom
```

Phase 2 must generate concrete 2D geometry:
```
Floor Plan:
┌──────┬────────────┐
│Entry │  Kitchen   │
├──────┴─────┬──────┤
│  Living    │ Bath │
│   Room     ├──────┤
│            │Bedrm │
└────────────┴──────┘
```

### Key Requirements

1. **Respect Adjacencies**: Connected rooms in graph must share boundaries in 2D
2. **Respect Areas**: Room sizes match metadata from Phase 1 (e.g., bedroom ≈ 13m²)
3. **Valid Geometry**: No overlaps, no gaps, proper polygon topology
4. **Visual Plausibility**: Rooms look reasonable (rectangular, good proportions)

---

## Phase 2 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    PHASE 2 PIPELINE                          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Input: Phase 1 Graph                                        │
│  ┌──────────────────┐                                        │
│  │ n0: Entrance     │                                        │
│  │ n1: Kitchen      │                                        │
│  │ n2: Living       │                                        │
│  │ n3: Bedroom      │                                        │
│  │ edges: [...]     │                                        │
│  └──────────────────┘                                        │
│           │                                                   │
│           ▼                                                   │
│  ┌──────────────────────────────────────┐                   │
│  │  P2.1: Parametric Room Shape Library  │                   │
│  │  • RoomShape dataclass               │                   │
│  │  • ROOM_DEFAULTS (area, aspect)      │                   │
│  │  • create_room_shape()               │                   │
│  └──────────────────────────────────────┘                   │
│           │                                                   │
│           ▼                                                   │
│  ┌──────────────────────────────────────┐                   │
│  │  P2.2: Initial Placement (BFS)        │                   │
│  │  • PlacedRoom dataclass              │                   │
│  │  • place_rooms_bfs()                 │                   │
│  │  • compute_adjacent_position()       │                   │
│  └──────────────────────────────────────┘                   │
│           │                                                   │
│           ▼                                                   │
│  ┌──────────────────────────────────────┐                   │
│  │  P2.3: Boundary Alignment             │                   │
│  │  • align_shared_boundaries()         │                   │
│  │  • find_closest_edges()              │                   │
│  │  • compute_alignment_offset()        │                   │
│  └──────────────────────────────────────┘                   │
│           │                                                   │
│           ▼                                                   │
│  ┌──────────────────────────────────────┐                   │
│  │  P2.4: Parametric Variation           │                   │
│  │  • Aspect ratio randomization        │                   │
│  │  • Directional placement bias        │                   │
│  │  • Area tolerance (±10%)             │                   │
│  └──────────────────────────────────────┘                   │
│           │                                                   │
│           ▼                                                   │
│  ┌──────────────────────────────────────┐                   │
│  │  P2.5: Visualization & Export         │                   │
│  │  • visualize_floor_plan() (mpl)      │                   │
│  │  • export_to_topologic() (faces)     │                   │
│  └──────────────────────────────────────┘                   │
│           │                                                   │
│           ▼                                                   │
│  Output: 2D Floor Plan                                       │
│  ┌──────────────────┐                                        │
│  │ List[PlacedRoom] │                                        │
│  │ TopologicPy Face │                                        │
│  │ Matplotlib viz   │                                        │
│  └──────────────────┘                                        │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementation Tasks

### Phase 2.1: Parametric Room Shape Library

**Status**: ✅ **COMPLETE** (2025-10-26)

**Goal**: Create library of 2D parametric shapes for different room types

**Approach**: Rectangular rooms with area and aspect ratio constraints

#### Deliverables

- [x] `RoomShape` dataclass
  ```python
  @dataclass
  class RoomShape:
      room_type: str
      target_area: float
      aspect_ratio: float
      width: float
      height: float
  ```

- [x] `ROOM_DEFAULTS` dictionary (from Swiss dataset analysis)
  ```python
  ROOM_DEFAULTS = {
      "Entrance": {"area": 4.0, "aspect": 1.0},
      "Kitchen": {"area": 8.0, "aspect": 1.2},
      "Living": {"area": 20.0, "aspect": 1.5},
      "Bedroom": {"area": 13.0, "aspect": 1.3},
      "Bathroom": {"area": 5.0, "aspect": 1.0},
      "Corridor": {"area": 3.0, "aspect": 2.5},
      "Balcony": {"area": 6.0, "aspect": 1.8}
  }
  ```

- [x] `create_room_shape(node: dict) -> RoomShape` function
  - Extract area from node metadata (props)
  - Use ROOM_DEFAULTS as fallback
  - Compute width/height from area and aspect ratio

- [x] `RoomShape.to_polygon()` method
  - Convert to 4-corner polygon at given origin

#### Tests

- [x] Generate shapes for all room types
- [x] Verify computed areas match target areas
- [x] Test with missing metadata (fallback to defaults)
- [x] Visual verification with matplotlib

---

### Phase 2.2: Initial Placement Algorithm

**Status**: ✅ **COMPLETE** (2025-10-26)

**Goal**: Place room shapes on 2D canvas using graph structure

**Approach**: BFS traversal from seed room, place neighbors adjacent

#### Deliverables

- [x] `PlacedRoom` dataclass
  ```python
  @dataclass
  class PlacedRoom:
      node_id: str
      shape: RoomShape
      origin: Tuple[float, float]  # Bottom-left corner
      polygon: List[Tuple[float, float]]
  ```

- [x] `place_rooms_bfs(nodes, edges, seed_id) -> Dict[str, PlacedRoom]`
  - Create shapes for all nodes
  - Build adjacency list
  - BFS traversal placing neighbors adjacent to current room
  - Cycle through directions: right, top, left, bottom

- [x] `compute_adjacent_position(current, neighbor_shape, direction) -> (x, y)`
  - Direction 0: right of current room
  - Direction 1: top of current room
  - Direction 2: left of current room
  - Direction 3: bottom of current room

#### Tests

- [x] Place 3-room linear graph (Entrance-Kitchen-Living)
- [x] Place 4-room graph with branching
- [x] Visualize with matplotlib (polygons + labels)
- [x] Verify all rooms placed (no missing nodes)
- [x] Test directional placement (all 4 directions)

---

### Phase 2.3: Boundary Alignment & Topology Refinement

**Status**: ⏳ **PENDING**

**Goal**: Adjust positions so adjacent rooms share boundaries (no gaps)

**Challenge**: BFS placement creates gaps between rooms

#### Deliverables

- [ ] `align_shared_boundaries(placed, edges) -> Dict[str, PlacedRoom]`
  - For each edge, find closest polygon edges
  - Compute alignment offset (gap distance)
  - Shift room to close gap
  - Propagate adjustments to connected rooms

- [ ] `find_closest_edges(poly_a, poly_b) -> (edge_a, edge_b)`
  - For rectangles: 4 edges each
  - Find pair with minimum distance
  - Return edge segments: ((x1,y1), (x2,y2))

- [ ] `compute_alignment_offset(edge_a, edge_b) -> (dx, dy)`
  - Project edge_b onto edge_a
  - Compute gap distance
  - Return offset to close gap

- [ ] `shift_room(room, offset) -> PlacedRoom`
  - Update origin by offset
  - Recompute polygon

#### Tests

- [ ] Align 2-room graph, verify no gap (measure distance)
- [ ] Align 4-room graph, verify all boundaries aligned
- [ ] Test with rooms of different sizes
- [ ] Visualize before/after alignment

---

### Phase 2.4: Parametric Variation & Optimization

**Status**: ⏳ **PENDING**

**Goal**: Add variation for diverse floor plans

#### Variation Strategies

1. **Aspect Ratio Variation**: Randomize within bounds (e.g., 1.0-1.5)
2. **Placement Direction Bias**: Prefer directions for specific room types
3. **Area Tolerance**: Allow ±10% variation from target area

#### Deliverables

- [ ] `create_room_shape_with_variation(node, variation=0.1) -> RoomShape`
  - Randomize area: `base_area * uniform(1-v, 1+v)`
  - Randomize aspect: `base_aspect * uniform(0.9, 1.3)`

- [ ] `place_rooms_with_smart_directions(nodes, edges, seed) -> Dict[str, PlacedRoom]`
  - Direction scoring based on room type
  - Bedrooms prefer top/right (away from entrance)
  - Bathrooms prefer corners
  - Kitchens prefer left of living room

- [ ] Direction preference rules (`DIRECTION_PREFERENCES`)

#### Tests

- [ ] Generate 10 variants of same graph
- [ ] Measure area variance (should be ≈10%)
- [ ] Measure aspect ratio variance
- [ ] Visual diversity check (human inspection)

---

### Phase 2.5: Visualization & TopologicPy Integration

**Status**: ⏳ **PENDING**

**Goal**: Visualize and export floor plans

#### Deliverables

- [ ] `visualize_floor_plan(placed, edges)`
  - Matplotlib figure with colored polygons
  - Room labels at centroids
  - Adjacency edges as dashed lines
  - Color coding by room type
  - Grid and axis labels

- [ ] `get_centroid(polygon) -> (cx, cy)`

- [ ] `export_to_topologic(placed) -> List[Face]`
  - Convert each placed room to TopologicPy Face
  - Attach metadata dictionary (room_id, room_type, area, etc.)
  - Return list of Face objects

- [ ] Color palette for room types

#### Tests

- [ ] Visualize 3-room apartment
- [ ] Visualize 8-room apartment
- [ ] Export to TopologicPy, verify loadable
- [ ] Check metadata preservation
- [ ] Test with Phase 3 pipeline (3D extrusion)

---

### Phase 2.6: End-to-End Integration

**Status**: ⏳ **PENDING**

**Goal**: Connect Phase 1 → Phase 2 in single notebook

#### Deliverables

- [ ] New notebook: `Phase2_Graph_to_Shape.ipynb`
  - Cell 1: Import and run Phase 1 graph generation
  - Cell 2: Extract nodes and edges from Kuzu
  - Cell 3: Run Phase 2 shape grammar pipeline
  - Cell 4: Visualize 2D floor plan
  - Cell 5: Export to TopologicPy
  - Cell 6: Validation checks

- [ ] Helper function: `extract_graph_from_kuzu(mgr, graph_id)`

- [ ] Helper function: `phase2_pipeline(nodes, edges) -> (placed, faces)`

#### Tests

- [ ] Generate and visualize 5 different apartment types:
  - Studio apartment
  - 1-bedroom apartment
  - 2-bedroom apartment
  - 3-bedroom apartment
  - 4-bedroom apartment

- [ ] Validation for each:
  - All rooms placed
  - No overlaps
  - Adjacencies respected
  - Total area ≈ sum of room areas

- [ ] Export test: Load faces in Phase 3 notebook

---

## Success Criteria

### Phase 2 Complete When:

1. ✅ **Geometric Validity**
   - All rooms from graph placed as 2D polygons
   - No overlapping rooms
   - Adjacent rooms share boundaries (tolerance < 0.1m)
   - Total area ≈ sum of room areas (tolerance ±5%)

2. ✅ **Topological Correctness**
   - Graph adjacencies preserved in 2D layout
   - All edges from Phase 1 visible as shared boundaries

3. ✅ **Visual Plausibility**
   - Floor plans look "reasonable" to human eye
   - Rooms have realistic proportions (aspect ratio 1.0-2.0)
   - Layout follows common apartment patterns

4. ✅ **Parametric Flexibility**
   - Can generate 10+ variants of same graph
   - Area/aspect parameters adjustable
   - Different placement strategies available

5. ✅ **Integration**
   - Seamless connection to Phase 1 output
   - Export compatible with Phase 3 (3D extrusion)
   - End-to-end notebook runs without errors

---

## Implementation Progress

### ✅ Completed Actions

**P2.1: Parametric Room Shape Library** (2025-10-26)
- Created `RoomShape` dataclass with area/aspect parameterization
- Implemented mathematical foundation: `height = √(area/aspect)`, `width = aspect × height`
- Created `ROOM_DEFAULTS` dictionary with 15+ room types from Swiss dataset
- Implemented `create_room_shape()` function with metadata extraction
- Added `normalize_room_type()` helper for label matching
- Comprehensive test suite with 4 test scenarios:
  - Basic shape creation (area, aspect, dimensions)
  - All default room types coverage
  - Node parsing (dict props, JSON string props, missing data)
  - Visual verification with matplotlib
- All tests passing ✅
- Documented in notebook: `Phase2_Graph_to_Shape.ipynb`

---

### ✅ Completed Actions

**P2.2: Initial Placement Algorithm** (2025-10-26)
- Created `PlacedRoom` dataclass with node_id, shape, origin, polygon
- Implemented `compute_adjacent_position()` for 4-directional placement
- Implemented `place_rooms_bfs()` with BFS traversal and direction cycling
- Comprehensive test suite with 5 test scenarios:
  - PlacedRoom creation and centroid calculation
  - Directional placement (all 4 directions verified)
  - Linear graph placement (3 rooms)
  - Branching graph placement (4 rooms)
  - Visual verification with matplotlib
- All tests passing ✅
- Documented in notebook: `Phase2_Graph_to_Shape_v2.ipynb`

### ⏳ Current Work

**Task**: Phase 2.3 - Boundary Alignment & Topology Refinement

**Status**: Ready to begin

**Next Steps**:
1. Implement boundary alignment functions
2. Test gap closure on simple graphs
3. Handle potential overlaps

---

## Technical Notes

### Room Shape Geometry

For simplicity, Phase 2 uses **axis-aligned rectangles** for all rooms. This is a reasonable approximation because:

1. Most rooms in Swiss dataset are approximately rectangular
2. Simplifies boundary alignment (only horizontal/vertical edges)
3. Faster computation than arbitrary polygons
4. Phase 3 can add complexity (non-rectangular rooms, angled walls)

### Coordinate System

- **Origin**: Bottom-left corner of each room
- **Axes**: X = right, Y = up
- **Units**: Meters
- **Precision**: 2 decimal places (cm accuracy)

### Area Calculation

```python
# For rectangle:
area = width * height

# Given area and aspect ratio:
aspect = width / height
area = width * height = aspect * height * height
height = sqrt(area / aspect)
width = aspect * height
```

### Adjacency Detection

Two rooms are adjacent if:
1. They share an edge in Phase 1 graph
2. Their polygons share a boundary segment (edge-to-edge distance < 0.1m)

---

## Known Challenges & Solutions

### Challenge 1: Gap Accumulation

**Problem**: Sequential BFS placement causes gaps to accumulate as graph grows

**Solution**: Global optimization pass after initial placement
- Use iterative refinement (multiple alignment passes)
- Minimize total gap energy: `Σ distance(adjacent_edges)`

### Challenge 2: Overlapping Rooms

**Problem**: Boundary alignment can cause rooms to overlap

**Solution**: Collision detection + backtracking
- Check for polygon overlap after each shift
- If overlap detected, try alternative alignment direction
- Use smaller offset (partial alignment)

### Challenge 3: Non-Planar Graphs

**Problem**: Some graphs cannot be laid out in 2D without edge crossings

**Solution**: Heuristic placement with "best effort"
- Allow small gaps/overlaps if unavoidable
- Report warning to user
- Suggest graph simplification

---

## Future Enhancements (Post-Phase 2)

1. **Non-Rectangular Rooms**
   - L-shaped rooms
   - Polygons with > 4 vertices

2. **Optimization-Based Placement**
   - Use optimization solver (e.g., scipy.optimize)
   - Minimize: gaps + overlaps + boundary irregularity

3. **Multi-Floor Support**
   - Extend to multiple floors
   - Staircase alignment

4. **Style Transfer**
   - Learn room arrangements from Swiss dataset
   - Generate layouts matching specific styles

---

**Last Updated**: 2025-10-26
**Current Status**: 🚧 Phase 2 in progress, P2.1 ✅ P2.2 ✅, P2.3 next
**Target Completion**: TBD
