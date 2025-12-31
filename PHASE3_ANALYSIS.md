# Phase 3: Shape Grammar Engine - From Bubbles to Layouts

**Date**: 2025-12-29
**Status**: 🎯 **ACTIVE DEVELOPMENT** - Shape grammar transformation system
**Architecture**: LayoutState + GraphShape + Rule Engine + TopologicPy Visualization

---

## Executive Summary

Phase 3 implements a **rule-based shape grammar engine** that transforms bubble diagrams (circle packing) into valid floor plan layouts (arranged rectangles). This system bridges Phase 1 (GraphRAG) and Phase 2 (Bubble Diagrams) with a production-ready transformation pipeline.

### Core Innovation

**Dual Representation Architecture**:
```
Circle Packing (Phase 2)
        ↓
  [LayoutState] ← Rule Engine → [Validation]
        ↓
  GraphShape (Geometry)
        ↓
TopologicPy (Faces + Graph)
        ↓
  Plotly + pyvis (Visualization)
```

**Key Insight**: Use **LayoutState** for transformations, **GraphShape** for geometry validation, and **TopologicPy** for visualization - each structure optimized for its purpose.

---

## Architecture Overview

### 1.1 Three-Layer Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Layer 1: Transformation                    │
│                      (LayoutState)                           │
│  - Phase tracking (Bubble → Rectangles → Arranged)         │
│  - Rule application logic                                    │
│  - Constraint checking                                       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                   Layer 2: Geometry                          │
│                     (GraphShape)                             │
│  - TopologicPy Face objects                                 │
│  - Graph adjacency representation                            │
│  - Overlap/gap detection                                     │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  Layer 3: Visualization                      │
│               (TopologicPy Plotly + pyvis)                   │
│  - Plotly.Show() for geometric rendering                    │
│  - pyvis for graph topology                                  │
│  - HTML export for sharing                                   │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Data Structure Integration

**LayoutState** (Transformation layer):
```python
@dataclass
class LayoutState:
    phase: Phase  # BUBBLE | RECTANGLES | ARRANGED | REFINED
    shapes: Dict[str, Shape]  # id → Shape(geometry, room_type, area)
    edges: List[LayoutEdge]   # Adjacency relationships
    is_valid: bool            # Validation flag
```

**GraphShape** (Geometry layer):
```python
@dataclass
class GraphShape:
    cluster: Cluster          # TopologicPy Cluster of Faces
    graph: Graph              # TopologicPy Graph

    def validate() -> Tuple[bool, List[str]]
    def total_area() -> float
    def bounding_box() -> Tuple[float, float, float, float]
```

**Conversion Flow**:
```
LayoutState.shapes (Circle/Rectangle geometry)
        ↓
    to_graphshape()
        ↓
GraphShape.cluster (TopologicPy Faces)
        ↓
    Plotly.Show() / pyvis.Show()
```

---

## Phase 1: Circle → Rectangle Transformation

### 2.1 Rule: CircleToRectangle

**Purpose**: Convert circle shapes to rectangles while preserving area and preparing for adjacency alignment.

**Pattern Matching**:
```python
class CircleToRectangleRule(Rule):
    name = "circle_to_rectangle"
    phase = Phase.BUBBLE
    priority = 100  # High priority - foundational

    def match(self, state: LayoutState) -> List[Match]:
        """Match any circle shape."""
        matches = []
        for shape_id, shape in state.shapes.items():
            if isinstance(shape.geometry, Circle):
                matches.append(Match(
                    shape_ids=[shape_id],
                    score=1.0  # All circles equally valid
                ))
        return matches
```

**Transformation Logic**:
```python
def apply(self, state: LayoutState, match: Match) -> RuleResult:
    """Convert circle to rectangle."""
    shape_id = match.shape_ids[0]
    circle_shape = state.shapes[shape_id]
    circle = circle_shape.geometry

    # 1. Compute rectangle dimensions preserving area
    area = circle_shape.target_area
    aspect_ratio = get_default_aspect_ratio(circle_shape.room_type)

    # area = width * height
    # aspect = width / height
    # → height = sqrt(area / aspect)
    # → width = aspect * height
    height = math.sqrt(area / aspect_ratio)
    width = aspect_ratio * height

    # 2. Center rectangle at circle center
    rect = Rectangle(
        center=circle.center,
        width=width,
        height=height,
        rotation=0  # Initially axis-aligned
    )

    # 3. Update shape
    circle_shape.geometry = rect
    circle_shape.computed_area = width * height

    return RuleResult(
        success=True,
        modified_shapes=[shape_id],
        message=f"Converted {circle_shape.room_type} to rectangle ({width:.2f}×{height:.2f})"
    )
```

**Validation**:
- ✅ Area preserved: `|rect.area - circle.area| < tolerance`
- ✅ Aspect ratio within bounds: `min_aspect <= width/height <= max_aspect`
- ✅ Position preserved: Rectangle center = Circle center

---

## Phase 2: Rectangle Arrangement

### 3.1 Rule: AlignAdjacentRectangles

**Purpose**: Align rectangles that should be adjacent (connected in graph) by rotating and translating them to share edges.

**Pattern Matching**:
```python
class AlignAdjacentRectanglesRule(Rule):
    name = "align_adjacent_rectangles"
    phase = Phase.RECTANGLES
    priority = 90

    def match(self, state: LayoutState) -> List[Match]:
        """Match pairs of rectangles with adjacency edges."""
        matches = []

        for edge in state.edges:
            if edge.edge_type != EdgeType.ADJACENCY:
                continue

            shape_a = state.shapes[edge.source_id]
            shape_b = state.shapes[edge.target_id]

            if not (isinstance(shape_a.geometry, Rectangle) and
                    isinstance(shape_b.geometry, Rectangle)):
                continue

            # Compute alignment quality score
            score = self._compute_alignment_score(shape_a, shape_b)

            matches.append(Match(
                shape_ids=[edge.source_id, edge.target_id],
                score=score,
                metadata={'edge': edge}
            ))

        return matches

    def _compute_alignment_score(self, shape_a, shape_b) -> float:
        """
        Score = 1 / distance_between_centers
        Higher score = closer together → higher priority
        """
        rect_a = shape_a.geometry
        rect_b = shape_b.geometry

        dist = math.sqrt(
            (rect_a.center.x - rect_b.center.x)**2 +
            (rect_a.center.y - rect_b.center.y)**2
        )

        return 1.0 / (dist + 0.1)  # Avoid division by zero
```

**Transformation Logic**:
```python
def apply(self, state: LayoutState, match: Match) -> RuleResult:
    """Align two rectangles by rotating/translating."""
    id_a, id_b = match.shape_ids
    shape_a = state.shapes[id_a]
    shape_b = state.shapes[id_b]

    rect_a = shape_a.geometry
    rect_b = shape_b.geometry

    # 1. Find closest edge pair
    edge_a, edge_b = self._find_closest_edges(rect_a, rect_b)

    # 2. Compute rotation needed to make edges parallel
    angle_a = self._edge_angle(edge_a)
    angle_b = self._edge_angle(edge_b)
    rotation_needed = angle_a - angle_b

    # 3. Rotate rect_b
    rect_b.rotation += rotation_needed

    # 4. Translate rect_b so edges are collinear
    offset = self._compute_translation_to_align_edges(edge_a, edge_b)
    rect_b.center = Point(
        rect_b.center.x + offset.x,
        rect_b.center.y + offset.y
    )

    # 5. Check for overlap after alignment
    if self._rectangles_overlap(rect_a, rect_b):
        # Separate slightly (leave 0.1m gap)
        separation_vector = self._compute_separation_vector(rect_a, rect_b)
        rect_b.center = Point(
            rect_b.center.x + separation_vector.x,
            rect_b.center.y + separation_vector.y
        )

    return RuleResult(
        success=True,
        modified_shapes=[id_b],  # Only moved rect_b
        message=f"Aligned {shape_a.room_type} and {shape_b.room_type}"
    )
```

### 3.2 Rule: FillGapBetweenRectangles

**Purpose**: Detect and fill small gaps between adjacent rectangles by slightly scaling/translating them.

**Pattern Matching**:
```python
class FillGapBetweenRectanglesRule(Rule):
    name = "fill_gap_between_rectangles"
    phase = Phase.ARRANGED
    priority = 50

    def match(self, state: LayoutState) -> List[Match]:
        """Match pairs with small gaps."""
        matches = []

        for edge in state.edges:
            if edge.edge_type != EdgeType.ADJACENCY:
                continue

            shape_a = state.shapes[edge.source_id]
            shape_b = state.shapes[edge.target_id]

            gap = self._compute_gap(shape_a.geometry, shape_b.geometry)

            if 0.01 < gap < 0.5:  # Small but non-zero gap
                matches.append(Match(
                    shape_ids=[edge.source_id, edge.target_id],
                    score=1.0 / gap,  # Smaller gaps = higher priority
                    metadata={'gap': gap}
                ))

        return matches
```

**Transformation Logic**:
```python
def apply(self, state: LayoutState, match: Match) -> RuleResult:
    """Close gap by translating one rectangle."""
    id_a, id_b = match.shape_ids
    shape_b = state.shapes[id_b]
    gap = match.metadata['gap']

    # Translate shape_b toward shape_a by gap distance
    direction = self._compute_gap_direction(
        state.shapes[id_a].geometry,
        shape_b.geometry
    )

    shape_b.geometry.center = Point(
        shape_b.geometry.center.x + direction.x * gap,
        shape_b.geometry.center.y + direction.y * gap
    )

    return RuleResult(
        success=True,
        modified_shapes=[id_b],
        message=f"Closed {gap:.3f}m gap"
    )
```

---

## Integration: LayoutState ↔ GraphShape

### 4.1 Conversion Functions

**LayoutState → GraphShape**:
```python
def layout_state_to_graphshape(state: LayoutState) -> GraphShape:
    """
    Convert LayoutState to GraphShape for validation/visualization.

    Process:
    1. Convert each Shape → TopologicPy Face
    2. Create Cluster from all faces
    3. Create Graph from edges + face centroids
    4. Return GraphShape
    """
    from topologicpy.Face import Face
    from topologicpy.Cluster import Cluster
    from topologicpy.Graph import Graph
    from grammar.topologic_helpers import rectangular_face

    faces = []

    # Convert shapes to faces
    for shape_id, shape in state.shapes.items():
        if isinstance(shape.geometry, Rectangle):
            rect = shape.geometry

            face = rectangular_face(
                width=rect.width,
                height=rect.height,
                origin=(rect.center.x - rect.width/2, rect.center.y - rect.height/2),
                label=shape.room_type
            )
            faces.append(face)

        elif isinstance(shape.geometry, Circle):
            # For visualization: approximate circle as octagon
            circ = shape.geometry
            face = create_circle_face(circ.center, circ.radius, label=shape.room_type)
            faces.append(face)

    # Create cluster
    cluster = Cluster.ByTopologies(faces)

    # Create graph
    adjacencies = [
        (edge.source_id, edge.target_id)
        for edge in state.edges
        if edge.edge_type == EdgeType.ADJACENCY
    ]

    graph = graph_from_faces_and_adjacencies(faces, adjacencies)

    return GraphShape(cluster=cluster, graph=graph)
```

**GraphShape → LayoutState**:
```python
def graphshape_to_layout_state(gs: GraphShape) -> LayoutState:
    """
    Convert GraphShape back to LayoutState.

    Use case: Load saved layout for further transformation.
    """
    from topologicpy.Dictionary import Dictionary
    from topologicpy.Topology import Topology

    state = LayoutState(phase=Phase.ARRANGED)

    # Extract faces
    faces = gs.faces()

    for face in faces:
        # Get metadata
        metadata_dict = Topology.Dictionary(face)
        keys = Dictionary.Keys(metadata_dict)
        values = Dictionary.Values(metadata_dict)
        metadata = dict(zip(keys, values))

        # Extract geometry
        vertices = Face.Vertices(face)
        # Compute bounding box → Rectangle approximation
        # ... (geometry extraction logic)

        shape = Shape(
            id=metadata.get('label', 'room'),
            geometry=rect,
            room_type=metadata.get('label', 'Room'),
            target_area=metadata.get('area', 0.0)
        )
        state.add_shape(shape)

    # Extract edges
    graph_edges = Graph.Edges(gs.graph)
    # ... (edge extraction logic)

    return state
```

### 4.2 Validation Integration

```python
def validate_layout_state(state: LayoutState) -> Dict[str, List[str]]:
    """
    Validate LayoutState using GraphShape geometric checks.

    Returns dict of validation issues:
    {
        'overlaps': [...],
        'gaps': [...],
        'missing_adjacency': [...],
        'area_mismatch': [...]
    }
    """
    # Convert to GraphShape
    gs = layout_state_to_graphshape(state)

    # Use GraphShape validation methods
    overlaps = gs.find_overlaps()  # Uses TopologicPy Intersect()
    gaps = gs.find_gaps()
    missing_adj = gs.find_missing_adjacencies()

    # Area validation
    area_issues = []
    for shape_id, shape in state.shapes.items():
        actual = shape.computed_area
        target = shape.target_area
        error = abs(actual - target) / target

        if error > 0.1:  # 10% tolerance
            area_issues.append(
                f"{shape.room_type}: {actual:.2f}m² vs {target:.2f}m² (error: {error*100:.1f}%)"
            )

    return {
        'overlaps': overlaps,
        'gaps': gaps,
        'missing_adjacency': missing_adj,
        'area_mismatch': area_issues
    }
```

---

## Engine Execution Flow

### 5.1 Hybrid Execution Strategy

```python
def run_shape_grammar_engine(
    circles: Dict[str, CircleNode],
    edges: List[dict]
) -> LayoutState:
    """
    Main entry point for shape grammar transformation.

    Execution Strategy:
    1. Phase 1 (BUBBLE → RECTANGLES):
       - Apply CircleToRectangle rule to ALL circles
       - Deterministic, parallel application

    2. Phase 2 (RECTANGLES → ARRANGED):
       - Iteratively apply AlignAdjacentRectangles
       - Priority order: closest pairs first
       - Continue until convergence or max iterations

    3. Phase 3 (ARRANGED → REFINED):
       - Apply FillGapBetweenRectangles
       - Apply aspect ratio refinement rules
       - Final validation

    Returns:
        Final LayoutState with arranged rectangles
    """
    config = EngineConfig(
        max_iterations_per_phase=100,
        convergence_threshold=0.01,
        area_tolerance=0.10,
        adjacency_tolerance=0.5,
        strategy=ExecutionStrategy.HYBRID,
        verbose=True
    )

    engine = ShapeGrammarEngine(config)

    # Create initial state from bubble diagram
    state = engine.create_initial_state(circles, edges)

    # Run transformation
    result = engine.run(state, target_phase=Phase.ARRANGED)

    if not result.success:
        print(f"⚠️  Transformation incomplete:")
        for issue_type, issues in result.validation_issues.items():
            if issues:
                print(f"  {issue_type}: {len(issues)}")

    return result.final_state
```

### 5.2 Visualization at Each Step

```python
def visualize_transformation_steps(
    circles: Dict[str, CircleNode],
    edges: List[dict],
    output_dir: str = "viz_outputs/transformation"
):
    """
    Run transformation with visualization at each step.

    Generates:
    - step_000_bubbles.html (initial circles)
    - step_001_rectangles.html (after C2R)
    - step_002_aligned.html (after first alignment)
    - ...
    - step_NNN_final.html (final layout)
    """
    from topologicpy.Plotly import Plotly
    from pathlib import Path

    Path(output_dir).mkdir(parents=True, exist_ok=True)

    engine = ShapeGrammarEngine()
    state = engine.create_initial_state(circles, edges)

    step = 0

    # Callback: visualize after each rule application
    def on_rule_applied(rule_name: str, current_state: LayoutState):
        nonlocal step
        step += 1

        # Convert to GraphShape
        gs = layout_state_to_graphshape(current_state)

        # Visualize with Plotly
        filepath = f"{output_dir}/step_{step:03d}_{rule_name}.html"

        Plotly.Show(
            gs.cluster,
            gs.graph,
            renderer="browser",
            filepath=filepath,
            faceOpacity=0.7,
            title=f"Step {step}: {rule_name}"
        )

        print(f"  Saved: {filepath}")

    engine.on_rule_applied = on_rule_applied

    # Run transformation
    result = engine.run(state)

    print(f"\n✅ Generated {step} visualization steps")
    return result.final_state
```

---

## Implementation Roadmap

### Week 1: Core Data Structures

**Day 1-2: LayoutState & Shape Classes**
- [ ] Implement `LayoutState` dataclass (phase, shapes, edges, validation)
- [ ] Implement `Shape` dataclass (id, geometry, room_type, area)
- [ ] Implement geometry classes: `Point`, `Circle`, `Rectangle`
- [ ] Unit tests: creation, serialization, validation

**Day 3-4: Conversion Layer**
- [ ] Implement `layout_state_to_graphshape()`
- [ ] Implement `graphshape_to_layout_state()`
- [ ] Test round-trip: LayoutState → GraphShape → LayoutState
- [ ] Verify geometry preservation

**Day 5: Integration with Bubble Diagram**
- [ ] Implement `create_initial_state(circles, edges)`
- [ ] Test with Phase2_BubbleDiagram output
- [ ] Verify all circle data preserved in LayoutState

---

### Week 2: Phase 1 Rules (Circle → Rectangle)

**Day 1-2: CircleToRectangle Rule**
- [ ] Implement `CircleToRectangleRule` class
- [ ] Pattern matching (all circles)
- [ ] Area-preserving transformation logic
- [ ] Aspect ratio assignment per room type
- [ ] Unit tests: area preservation, aspect ratios

**Day 3: Rule Registry & Engine Foundation**
- [ ] Implement `RuleRegistry` (register, get_for_phase, get_all)
- [ ] Implement `ShapeGrammarEngine` skeleton
- [ ] Implement `step()` method (single rule application)
- [ ] Test: manually step through C2R transformations

**Day 4-5: Phase 1 Execution**
- [ ] Implement `_run_hybrid()` Phase 1 logic
- [ ] Test with 5-room apartment
- [ ] Test with 10-room apartment
- [ ] Visualize: before (circles) → after (rectangles)

---

### Week 3: Phase 2 Rules (Rectangle Arrangement)

**Day 1-2: AlignAdjacentRectangles Rule**
- [ ] Implement edge finding algorithm
- [ ] Implement rotation computation
- [ ] Implement translation computation
- [ ] Test: align two rectangles (verify tangency)

**Day 3: Overlap Detection & Resolution**
- [ ] Implement `_rectangles_overlap()` check
- [ ] Implement separation logic
- [ ] Test: prevent overlaps during alignment

**Day 4-5: Iterative Arrangement Engine**
- [ ] Implement `_run_hybrid()` Phase 2 logic
- [ ] Convergence detection (position delta < threshold)
- [ ] Priority scoring (closest pairs first)
- [ ] Test: 6-room apartment arrangement
- [ ] Measure convergence iterations

---

### Week 4: Refinement & Polish

**Day 1-2: FillGapBetweenRectangles Rule**
- [ ] Implement gap detection
- [ ] Implement gap closing (translation)
- [ ] Test: close 0.1m gaps without overlap

**Day 3: Validation & Metrics**
- [ ] Implement comprehensive validation
- [ ] Metrics: total area, overlap count, gap count, iteration count
- [ ] Validation reports (structured JSON)

**Day 4-5: End-to-End Testing**
- [ ] Test: 1BR, 2BR, 3BR, 4BR apartments
- [ ] Generate variations (different random seeds)
- [ ] Measure success rate (% valid layouts)
- [ ] Performance benchmarking

---

### Week 5: Visualization & Integration

**Day 1-2: Step-by-Step Visualization**
- [ ] Implement `visualize_transformation_steps()`
- [ ] Plotly HTML export at each step
- [ ] Create animation (slideshow of steps)
- [ ] Test: generate 50-step transformation gallery

**Day 3: Comparison Dashboards**
- [ ] Before/after comparison (bubble vs layout)
- [ ] Variation comparison (10 layouts from same graph)
- [ ] Metrics dashboard (areas, gaps, iterations)

**Day 4-5: Integration with GraphRAG (Phase 1)**
- [ ] End-to-end pipeline: GraphRAG → Bubble → Layout
- [ ] Test with actual Kuzu GraphRAG output
- [ ] Generate 20 apartment layouts
- [ ] Measure quality metrics

---

## Success Criteria

### Functional Requirements
- [ ] ✅ Converts all circles to rectangles (100% success rate)
- [ ] ✅ Preserves area within 10% tolerance
- [ ] ✅ Aligns adjacent rectangles (shared edges)
- [ ] ✅ No overlaps in final layout
- [ ] ✅ Gaps < 0.5m between adjacent rooms
- [ ] ✅ Converges in < 100 iterations for 10-room layout

### Quality Requirements
- [ ] ✅ 80%+ layouts pass full validation
- [ ] ✅ Aspect ratios reasonable (1.0 - 2.0 range)
- [ ] ✅ Layouts visually plausible
- [ ] ✅ Can generate 10+ variations per graph

### Performance Requirements
- [ ] ✅ 5-room layout: < 5 seconds
- [ ] ✅ 10-room layout: < 30 seconds
- [ ] ✅ 15-room layout: < 60 seconds

### Code Quality
- [ ] ✅ 90%+ test coverage
- [ ] ✅ All unit tests pass
- [ ] ✅ Docstrings on all public APIs
- [ ] ✅ Type hints throughout

---

## Visualization Strategy

### TopologicPy Plotly (Primary)

**Use for**:
- Geometric layouts (2D floor plans)
- 3D extrusions (future)
- Side-by-side comparisons
- Animation sequences

**Example**:
```python
gs = layout_state_to_graphshape(final_state)

Plotly.Show(
    gs.cluster,
    gs.graph,
    renderer="notebook",  # Or "browser" for HTML
    faceOpacity=0.7,
    edgeColor='black',
    width=1000,
    height=800,
    title="Final Floor Plan Layout"
)
```

### TopologicPy pyvis (Secondary)

**Use for**:
- Graph topology analysis
- Degree distribution
- Connectivity visualization
- Network physics simulation

**Example**:
```python
Graph.Show(
    gs.graph,
    layout='spring',
    nodeColor='blue',
    edgeColor='gray',
    nodeLabels=True
)
```

### No External Libraries

- ✅ **Plotly**: Built into TopologicPy
- ✅ **pyvis**: Built into TopologicPy
- ❌ **Bokeh**: Not needed (Plotly sufficient)
- ❌ **PyVista**: Future for 3D mesh analysis

---

## File Structure

```
GraphRAG_Grammars/
├── src/
│   └── grammar/
│       ├── __init__.py
│       ├── core.py                    # LayoutState, Shape, Phase enums
│       ├── rules.py                   # Rule base class, RuleRegistry
│       ├── phase1_rules.py            # CircleToRectangle rule
│       ├── phase2_rules.py            # Alignment rules
│       ├── engine.py                  # ShapeGrammarEngine
│       ├── converters.py              # LayoutState ↔ GraphShape
│       └── topologic_helpers.py       # (existing) Face utilities
├── notebooks/
│   ├── Phase2_BubbleDiagram.ipynb     # (existing) Circle packing
│   ├── Phase3_ShapeGrammar.ipynb      # NEW: Transformation demo
│   └── Phase3_Variations.ipynb        # NEW: Generate variations
├── tests/
│   ├── test_layout_state.py
│   ├── test_rules.py
│   ├── test_engine.py
│   └── test_converters.py
├── viz_outputs/
│   └── transformations/               # Step-by-step HTML files
├── PHASE3_ANALYSIS.md                 # This document
└── TODO.md                            # Updated task list
```

---

## Next Steps

### Immediate (This Week)
1. ✅ Create `src/grammar/core.py` (LayoutState, Shape, enums)
2. ✅ Create `src/grammar/converters.py` (LayoutState ↔ GraphShape)
3. ✅ Test conversion with Phase2_BubbleDiagram output
4. ✅ Verify TopologicPy Plotly visualization works

### Week 2 Goals
- [ ] Implement CircleToRectangle rule
- [ ] Implement basic engine (step() method)
- [ ] Generate first transformation: circles → rectangles
- [ ] Visualize with Plotly

### Week 3 Goals
- [ ] Implement AlignAdjacentRectangles rule
- [ ] Implement iterative engine loop
- [ ] Generate first valid layout (all aligned)
- [ ] Measure convergence

---

**Last Updated**: 2025-12-29
**Status**: 🎯 READY FOR IMPLEMENTATION
**Next Action**: Create `src/grammar/core.py` with LayoutState dataclass
**Estimated Timeline**: 5 weeks to production-ready system

---
