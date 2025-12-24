# Graph Grammars → Shape Grammars: Iterative Development Plan v2.0

**Date**: 2025-12-23
**Status**: 🎯 **NEW APPROACH** - Rule-based transformation system
**Philosophy**: Build fundamental understanding through iterative exploration

---

## Executive Summary

### The New Paradigm

This plan represents a fundamental shift from **graph-to-shape conversion** to **graph-driven shape transformation**:

```
┌─────────────────────────────────────────────────────────────────┐
│                    OLD APPROACH (Abandoned)                      │
│  Graph (topology) ──────▶ Shape (geometry)                      │
│  One-directional conversion, constraint satisfaction             │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    NEW APPROACH (This Plan)                      │
│                                                                   │
│  Graph (topology) ◀────▶ Shape (geometry)                       │
│         │                     │                                   │
│         │ Transform Graph     │ Shape Updates                    │
│         ▼                     ▼                                   │
│  Graph Rules ─────────▶ Shape Rules                             │
│  (add node,           (split rectangle,                          │
│   merge nodes,         merge regions,                            │
│   split edges)         extrude boundary)                         │
│                                                                   │
│  Bidirectional, rule-based, compositional                        │
└─────────────────────────────────────────────────────────────────┘
```

### Core Principles

1. **Start Simple**: Rectangles and squares only, parametric + Topologic
2. **Dual Representation**: Every shape has BOTH a graph AND geometry
3. **Rules First**: Define transformation rules explicitly before implementing
4. **Iterative Testing**: Each step has clear validation criteria
5. **Notebook-Driven**: Exploratory development in Jupyter, extract to modules later

---

## Phase 0: Foundations (Week 1)

**Goal**: Establish basic shape and graph creation with dual representation

### Milestone 0.1: Simple Parametric Shapes

**Notebook**: `00_Simple_Shapes.ipynb`

#### Learning Objectives
- Understand parametric shape definition
- Create shapes in both raw Python and TopologicPy
- Visualize shapes with pyvis (via TopologicPy)
- Establish testing patterns

#### Implementation Steps

**Step 0.1.1: Rectangle Class (Pure Python)**
```python
@dataclass
class Rectangle:
    """Parametric rectangle definition."""
    width: float
    height: float
    origin: Tuple[float, float] = (0.0, 0.0)

    @property
    def area(self) -> float:
        return self.width * self.height

    @property
    def vertices(self) -> List[Tuple[float, float]]:
        """Counter-clockwise vertices starting from origin."""
        x, y = self.origin
        return [
            (x, y),
            (x + self.width, y),
            (x + self.width, y + self.height),
            (x, y + self.height)
        ]

    def to_dict(self) -> dict:
        """Serialize for visualization/storage."""
        return {
            'type': 'rectangle',
            'width': self.width,
            'height': self.height,
            'origin': self.origin,
            'area': self.area,
            'vertices': self.vertices
        }
```

**Tests**:
- [ ] Create 3×4 rectangle at origin → area = 12
- [ ] Create 5×5 square at (10, 10) → 4 vertices offset correctly
- [ ] Test serialization → dict → deserialize → same rectangle

**Step 0.1.2: TopologicPy Face Creation**
```python
def rectangle_to_topologic_face(rect: Rectangle) -> Face:
    """Convert parametric rectangle to TopologicPy Face."""
    from topologicpy.Vertex import Vertex
    from topologicpy.Wire import Wire
    from topologicpy.Face import Face
    from topologicpy.Dictionary import Dictionary
    from topologicpy.Topology import Topology

    # Create vertices
    tp_vertices = [
        Vertex.ByCoordinates(x, y, 0.0)
        for x, y in rect.vertices
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
        'area': rect.area,
        'origin_x': rect.origin[0],
        'origin_y': rect.origin[1]
    }

    dict_obj = Dictionary.ByKeysValues(
        list(metadata.keys()),
        list(metadata.values())
    )
    face = Topology.SetDictionary(face, dict_obj)

    return face

def topologic_face_to_rectangle(face: Face) -> Rectangle:
    """Extract parametric rectangle from TopologicPy Face."""
    from topologicpy.Dictionary import Dictionary
    from topologicpy.Topology import Topology

    # Get metadata
    dict_obj = Topology.Dictionary(face)
    metadata = {
        k: Dictionary.ValueAtKey(dict_obj, k)
        for k in Dictionary.Keys(dict_obj)
    }

    # Reconstruct rectangle
    return Rectangle(
        width=metadata['width'],
        height=metadata['height'],
        origin=(metadata['origin_x'], metadata['origin_y'])
    )
```

**Tests**:
- [ ] Rectangle → TopologicPy Face → Rectangle (round-trip)
- [ ] Face area matches parametric area
- [ ] Face vertices match parametric vertices (within tolerance)
- [ ] Metadata preserved through conversion

**Step 0.1.3: Visualization with TopologicPy + pyvis**
```python
def visualize_shapes(shapes: List[Rectangle], title: str = "Shapes",
                     output_path: str = "shapes_viz.html"):
    """
    Visualize rectangles using TopologicPy's pyvis integration.

    Creates interactive HTML visualization showing:
    - Rectangle faces (2D geometry)
    - Labels and metadata
    - Interactive pan/zoom
    """
    from topologicpy.Face import Face
    from topologicpy.Graph import Graph as TPGraph
    from topologicpy.Vertex import Vertex
    from topologicpy.Plotly import Plotly

    # Convert rectangles to TopologicPy Faces
    faces = []
    for i, rect in enumerate(shapes):
        face = rectangle_to_topologic_face(rect)
        faces.append(face)

    # Create a CellComplex or Cluster to hold all faces
    from topologicpy.Cluster import Cluster
    cluster = Cluster.ByTopologies(faces)

    # Visualize using Plotly (TopologicPy's built-in viz)
    # Plotly.Show creates interactive HTML visualization
    Plotly.Show(
        cluster,
        renderer="notebook",  # For Jupyter
        showScale=True,
        width=800,
        height=800,
        camera=[0, 0, 100],  # Top-down view for 2D
        target=[0, 0, 0],
        backgroundColor='white',
        faceColor='lightblue',
        edgeColor='black',
        vertexColor='red'
    )

    # Alternative: Export to HTML file for standalone viewing
    Plotly.ExportToHTML(
        cluster,
        path=output_path,
        title=title
    )

    return cluster
```

**Tests**:
- [ ] Visualize 5 random rectangles → all visible in interactive view
- [ ] Pan/zoom works in HTML output
- [ ] Labels readable
- [ ] Export to HTML for documentation

**Note**: TopologicPy's Plotly integration provides:
- Interactive 3D/2D visualization
- Pan, zoom, rotate controls
- Hover tooltips (can show metadata)
- Export to HTML (shareable, no Python needed to view)

**Deliverable**: `00_Simple_Shapes.ipynb` with 3 sections:
1. Parametric rectangles (creation, properties, tests)
2. TopologicPy conversion (bidirectional, tests)
3. Visualization (matplotlib, examples)

---

### Milestone 0.2: Simple Graphs on Shapes

**Notebook**: `01_Graphs_On_Shapes.ipynb`

#### Learning Objectives
- Understand graph-shape duality
- Create TopologicPy graphs overlaid on shapes
- Establish node-to-shape and edge-to-boundary mappings

#### Conceptual Foundation

**Key Insight**: A shape configuration can be represented as a graph where:
- **Nodes** = Individual shapes (e.g., rooms)
- **Edges** = Adjacency relationships (e.g., shared boundaries)
- **Graph embedded in 2D** = Nodes have spatial positions

**Example**:
```
Shapes:                    Graph:
┌───┬───┐                 n0 ─── n1
│ 0 │ 1 │                  │      │
├───┼───┤                  │      │
│ 2 │ 3 │                 n2 ─── n3
└───┴───┘
```

#### Implementation Steps

**Step 0.2.1: Graph-Shape Data Structure**
```python
@dataclass
class GraphShape:
    """A configuration of shapes with an overlaid graph."""
    shapes: Dict[str, Rectangle]  # node_id → Rectangle
    edges: List[Tuple[str, str]]  # List of (node_a, node_b) pairs

    def get_neighbors(self, node_id: str) -> List[str]:
        """Get all nodes adjacent to given node."""
        neighbors = []
        for a, b in self.edges:
            if a == node_id:
                neighbors.append(b)
            elif b == node_id:
                neighbors.append(a)
        return neighbors

    def get_shared_boundary(self, node_a: str, node_b: str) -> Optional[Segment]:
        """Get shared boundary segment between two adjacent rectangles."""
        if (node_a, node_b) not in self.edges and (node_b, node_a) not in self.edges:
            return None

        rect_a = self.shapes[node_a]
        rect_b = self.shapes[node_b]

        # Find which edges of the rectangles overlap
        # (Implementation: check all 4 edges of each rectangle)
        return self._find_overlapping_edge(rect_a, rect_b)

    def to_networkx(self):
        """Convert to NetworkX graph for analysis."""
        import networkx as nx
        G = nx.Graph()

        for node_id, rect in self.shapes.items():
            G.add_node(node_id,
                      pos=(rect.origin[0] + rect.width/2,
                           rect.origin[1] + rect.height/2),
                      width=rect.width,
                      height=rect.height,
                      area=rect.area)

        for a, b in self.edges:
            G.add_edge(a, b)

        return G
```

**Tests**:
- [ ] Create 2×2 grid of rectangles (4 nodes, 4 edges)
- [ ] Verify adjacency: each interior node has 4 neighbors
- [ ] Verify graph connectivity (all nodes reachable from n0)
- [ ] Export to NetworkX, visualize with `nx.draw()`

**Step 0.2.2: TopologicPy Graph Creation**
```python
def graphshape_to_topologic(gs: GraphShape) -> Tuple[List[Face], Graph]:
    """
    Convert GraphShape to TopologicPy representation.

    Returns:
        - List of TopologicPy Faces (one per shape)
        - TopologicPy Graph encoding adjacencies
    """
    from topologicpy.Graph import Graph as TPGraph
    from topologicpy.Vertex import Vertex as TPVertex
    from topologicpy.Edge import Edge as TPEdge

    # Create Faces for shapes
    faces = {
        node_id: rectangle_to_topologic_face(rect)
        for node_id, rect in gs.shapes.items()
    }

    # Create graph vertices (at face centroids)
    vertices = {}
    for node_id, face in faces.items():
        # Get centroid of face
        centroid = Topology.Centroid(face)
        vertices[node_id] = centroid

    # Create edges
    tp_edges = []
    for a, b in gs.edges:
        edge = Edge.ByVertices([vertices[a], vertices[b]])
        tp_edges.append(edge)

    # Create graph
    graph = TPGraph.ByVerticesEdges(
        list(vertices.values()),
        tp_edges
    )

    # Attach node_id metadata to graph vertices
    # (so we can map back to shapes)
    for node_id, vertex in vertices.items():
        d = Dictionary.ByKeysValues(['node_id'], [node_id])
        vertex = Topology.SetDictionary(vertex, d)

    return list(faces.values()), graph
```

**Tests**:
- [ ] Create 3×3 grid GraphShape
- [ ] Convert to TopologicPy
- [ ] Verify: 9 faces, 12 edges in graph
- [ ] Verify: metadata preserved (can map graph vertex → shape)

**Step 0.2.3: Visualization of Graph + Shapes with TopologicPy**
```python
def visualize_graphshape(gs: GraphShape, title: str = "Graph + Shapes",
                        output_path: str = "graphshape_viz.html"):
    """
    Visualize both shapes and graph overlay using TopologicPy.

    Creates interactive HTML with:
    - Faces (shapes/rectangles)
    - Graph (topology overlay)
    - Metadata in hover tooltips
    """
    from topologicpy.Plotly import Plotly
    from topologicpy.Cluster import Cluster
    from topologicpy.Color import Color

    # Convert to TopologicPy representation
    faces, graph = graphshape_to_topologic(gs)

    # Create cluster of faces for visualization
    face_cluster = Cluster.ByTopologies(faces)

    # Method 1: Visualize shapes (faces) only
    Plotly.Show(
        face_cluster,
        renderer="notebook",
        width=800,
        height=800,
        camera=[0, 0, 100],
        target=[0, 0, 0],
        backgroundColor='white',
        faceColor='lightblue',
        faceOpacity=0.7,
        edgeColor='black',
        edgeWidth=2,
        showFaces=True,
        showEdges=True,
        showVertices=True
    )

    # Method 2: Visualize graph structure
    # TopologicPy Graph.Show() uses pyvis for interactive network viz
    from topologicpy.Graph import Graph as TPGraph

    TPGraph.Show(
        graph,
        renderer="notebook",
        showNodes=True,
        showEdges=True,
        nodeColor='red',
        edgeColor='blue',
        nodeSize=10,
        edgeWidth=2,
        nodeLabels=True,  # Show node_id from metadata
        layout='spring',   # Options: 'spring', 'circular', 'hierarchical'
        width=800,
        height=800
    )

    # Method 3: Combined visualization (overlay)
    # Create a topology that combines both faces and graph
    from topologicpy.Topology import Topology

    # Add graph vertices/edges to the face cluster
    combined = Topology.SelfMerge(face_cluster)

    Plotly.Show(
        combined,
        renderer="notebook",
        width=1200,
        height=800,
        camera=[0, 0, 100],
        backgroundColor='white',
        faceColor='lightblue',
        faceOpacity=0.5,
        edgeColor='darkblue',
        edgeWidth=3,
        vertexColor='red',
        vertexSize=8,
        showFaces=True,
        showEdges=True,
        showVertices=True
    )

    # Export combined view to HTML
    Plotly.ExportToHTML(
        combined,
        path=output_path,
        title=title
    )

    return face_cluster, graph

# Alternative: Use pyvis directly for pure graph visualization
def visualize_graph_pyvis(gs: GraphShape, output_path: str = "graph_viz.html"):
    """
    Visualize graph using pyvis (via TopologicPy).

    Creates interactive network diagram with physics simulation.
    """
    from topologicpy.Graph import Graph as TPGraph

    # Convert GraphShape to TopologicPy Graph
    _, tp_graph = graphshape_to_topologic(gs)

    # Export to pyvis HTML (interactive physics-based layout)
    TPGraph.ExportToPyVis(
        tp_graph,
        path=output_path,
        layout='physics',  # Options: 'physics', 'hierarchical', 'random'
        nodeSize=25,
        nodeColor='#97C2FC',
        edgeColor='#848484',
        edgeWidth=2,
        showButtons=True,  # Show configuration panel
        notebook=False     # Set True if running in Jupyter
    )

    print(f"Interactive graph saved to: {output_path}")
    print("Open in browser to interact (drag nodes, zoom, pan)")
```

**Tests**:
- [ ] Visualize 2×2 grid → interactive view renders correctly
- [ ] Graph edges align with shape adjacencies (visual check)
- [ ] Can drag graph nodes in pyvis visualization
- [ ] Hover tooltips show metadata (node_id, area, etc.)
- [ ] Export to HTML and verify opens in browser
- [ ] Test physics layout vs. spring layout

**Note**: TopologicPy provides multiple visualization backends:
- **Plotly**: 3D/2D geometric visualization (faces, edges, vertices)
- **pyvis**: Interactive network graphs (physics-based layout)
- **Both**: Can combine geometric + topological views

**Deliverable**: `01_Graphs_On_Shapes.ipynb` with:
1. GraphShape data structure
2. TopologicPy conversion
3. Visualization (shapes, graph, overlay)
4. Examples: 2×2 grid, 3×3 grid, L-shape, T-shape

---

## Phase 1: Graph Grammar Rules (Week 2)

**Goal**: Define and implement basic graph transformation rules

### Milestone 1.1: Graph Transformation Rules

**Notebook**: `02_Graph_Rules.ipynb`

#### Learning Objectives
- Understand graph grammar formalism
- Implement rule pattern matching
- Test rule application
- Visualize before/after transformations

#### Theoretical Foundation

**Graph Grammar Rule** = (L, R, K) where:
- **L** = Left-hand side (pattern to match)
- **R** = Right-hand side (replacement)
- **K** = Interface (preserved elements)

**Example Rule: "Split Node"**
```
L: Single node             R: Two nodes connected
   ●                          ● ─ ●

Rule: Find node with degree 2, split into two connected nodes
```

#### Implementation Steps

**Step 1.1.1: Rule Definition Schema**
```python
@dataclass
class GraphRule:
    """A graph transformation rule."""
    name: str
    description: str

    # Pattern matching
    pattern: Callable[[nx.Graph, str], bool]  # (graph, node_id) → match?

    # Transformation
    apply: Callable[[GraphShape, str], GraphShape]  # (graphshape, node_id) → new graphshape

    # Metadata
    preserves_planarity: bool = True
    preserves_connectivity: bool = True

class RuleLibrary:
    """Collection of graph transformation rules."""

    @staticmethod
    def split_node_horizontally() -> GraphRule:
        """Split a rectangular node into two horizontal rectangles."""
        def pattern(G: nx.Graph, node_id: str) -> bool:
            # Match any node (could add constraints later)
            return node_id in G.nodes()

        def apply(gs: GraphShape, node_id: str) -> GraphShape:
            """Split node horizontally (left | right)."""
            rect = gs.shapes[node_id]

            # Create two new rectangles
            new_width = rect.width / 2

            left_rect = Rectangle(
                width=new_width,
                height=rect.height,
                origin=rect.origin
            )

            right_rect = Rectangle(
                width=new_width,
                height=rect.height,
                origin=(rect.origin[0] + new_width, rect.origin[1])
            )

            # Create new node IDs
            left_id = f"{node_id}_L"
            right_id = f"{node_id}_R"

            # Build new shapes dict
            new_shapes = gs.shapes.copy()
            del new_shapes[node_id]
            new_shapes[left_id] = left_rect
            new_shapes[right_id] = right_rect

            # Update edges: replace references to node_id
            new_edges = []
            for a, b in gs.edges:
                if a == node_id:
                    new_edges.append((left_id, b))
                    new_edges.append((right_id, b))
                elif b == node_id:
                    new_edges.append((a, left_id))
                    new_edges.append((a, right_id))
                else:
                    new_edges.append((a, b))

            # Add edge between split nodes
            new_edges.append((left_id, right_id))

            return GraphShape(shapes=new_shapes, edges=new_edges)

        return GraphRule(
            name="split_horizontal",
            description="Split rectangular node into two horizontal rectangles (left | right)",
            pattern=pattern,
            apply=apply
        )

    @staticmethod
    def split_node_vertically() -> GraphRule:
        """Split a rectangular node into two vertical rectangles."""
        # Similar to split_horizontal but divide height instead of width
        # ... (implementation similar to above)
        pass

    @staticmethod
    def merge_adjacent_nodes() -> GraphRule:
        """Merge two adjacent nodes into single larger rectangle."""
        def pattern(G: nx.Graph, node_id: str) -> bool:
            # Match nodes with at least one neighbor
            return len(list(G.neighbors(node_id))) > 0

        def apply(gs: GraphShape, node_id: str, neighbor_id: str) -> GraphShape:
            """Merge node_id with neighbor_id."""
            rect_a = gs.shapes[node_id]
            rect_b = gs.shapes[neighbor_id]

            # Compute bounding box of merged rectangles
            min_x = min(rect_a.origin[0], rect_b.origin[0])
            min_y = min(rect_a.origin[1], rect_b.origin[1])
            max_x = max(rect_a.origin[0] + rect_a.width,
                       rect_b.origin[0] + rect_b.width)
            max_y = max(rect_a.origin[1] + rect_a.height,
                       rect_b.origin[1] + rect_b.height)

            merged_rect = Rectangle(
                width=max_x - min_x,
                height=max_y - min_y,
                origin=(min_x, min_y)
            )

            # Create new node ID
            merged_id = f"{node_id}+{neighbor_id}"

            # Build new shapes dict
            new_shapes = gs.shapes.copy()
            del new_shapes[node_id]
            del new_shapes[neighbor_id]
            new_shapes[merged_id] = merged_rect

            # Update edges
            new_edges = []
            for a, b in gs.edges:
                if a in [node_id, neighbor_id]:
                    new_a = merged_id
                else:
                    new_a = a

                if b in [node_id, neighbor_id]:
                    new_b = merged_id
                else:
                    new_b = b

                # Skip self-loops
                if new_a != new_b:
                    edge = (new_a, new_b)
                    if edge not in new_edges and (new_b, new_a) not in new_edges:
                        new_edges.append(edge)

            return GraphShape(shapes=new_shapes, edges=new_edges)

        return GraphRule(
            name="merge_adjacent",
            description="Merge two adjacent nodes into single rectangle",
            pattern=pattern,
            apply=apply
        )
```

**Tests**:
- [ ] **Split Horizontal**: 4×6 rect → two 2×6 rects, verify areas sum correctly
- [ ] **Split Vertical**: 6×4 rect → two 6×2 rects
- [ ] **Merge**: Two adjacent 2×2 rects → one 4×2 or 2×4 rect (depending on layout)
- [ ] **Edge preservation**: After split, original neighbors connected to both new nodes
- [ ] **Graph properties**: Connectivity preserved after all transformations

**Step 1.1.2: Rule Application Engine**
```python
class GraphGrammar:
    """Engine for applying graph transformation rules."""

    def __init__(self, rules: List[GraphRule]):
        self.rules = {rule.name: rule for rule in rules}

    def apply_rule(self, gs: GraphShape, rule_name: str,
                   target_node: str, **kwargs) -> GraphShape:
        """Apply named rule to target node."""
        if rule_name not in self.rules:
            raise ValueError(f"Unknown rule: {rule_name}")

        rule = self.rules[rule_name]

        # Check pattern matches
        G = gs.to_networkx()
        if not rule.pattern(G, target_node):
            raise ValueError(f"Pattern does not match for node {target_node}")

        # Apply transformation
        new_gs = rule.apply(gs, target_node, **kwargs)

        return new_gs

    def apply_sequence(self, gs: GraphShape,
                      sequence: List[Tuple[str, str]]) -> GraphShape:
        """
        Apply sequence of rules.

        Args:
            sequence: List of (rule_name, target_node) tuples

        Returns:
            Final GraphShape after all transformations
        """
        current = gs
        for rule_name, target_node in sequence:
            current = self.apply_rule(current, rule_name, target_node)
        return current
```

**Tests**:
- [ ] Create 2×2 grid
- [ ] Apply sequence: split n0 horizontally, split n1 vertically
- [ ] Verify final configuration has 6 nodes (2+1 + 2+1 = 4+2)
- [ ] Visualize each step
- [ ] Test error handling: apply rule to non-existent node

**Deliverable**: `02_Graph_Rules.ipynb` with:
1. Rule library (split_h, split_v, merge)
2. GraphGrammar engine
3. Examples: single rule, rule sequences
4. Visualization of transformations (before → after)

---

### Milestone 1.2: Shape Rules from Graph Rules

**Notebook**: `03_Shape_Rules.ipynb`

#### Learning Objectives
- Understand how graph transformations drive shape transformations
- Implement shape subdivision algorithms
- Ensure shape consistency with graph structure

#### Key Insight

**Shape transformations are DERIVED from graph transformations**:

```
Graph Rule: Split node n0     →  Shape Rule: Subdivide rectangle R0
   ●                                ┌─────┐         ┌──┬──┐
   │                                │  R0 │         │R0│R0│
   ●                                │     │    →    │_L│_R│
                                    └─────┘         └──┴──┘
```

**The graph transformation DEFINES the shape transformation.**

#### Implementation Steps

**Step 1.2.1: Shape Subdivision Rules**
```python
class ShapeRules:
    """Shape transformations derived from graph rules."""

    @staticmethod
    def subdivide_horizontal(rect: Rectangle, ratio: float = 0.5) -> Tuple[Rectangle, Rectangle]:
        """
        Subdivide rectangle horizontally.

        Args:
            rect: Rectangle to subdivide
            ratio: Position of split (0 < ratio < 1)

        Returns:
            (left_rect, right_rect)
        """
        split_x = rect.origin[0] + rect.width * ratio

        left = Rectangle(
            width=rect.width * ratio,
            height=rect.height,
            origin=rect.origin
        )

        right = Rectangle(
            width=rect.width * (1 - ratio),
            height=rect.height,
            origin=(split_x, rect.origin[1])
        )

        return left, right

    @staticmethod
    def subdivide_vertical(rect: Rectangle, ratio: float = 0.5) -> Tuple[Rectangle, Rectangle]:
        """Subdivide rectangle vertically."""
        split_y = rect.origin[1] + rect.height * ratio

        bottom = Rectangle(
            width=rect.width,
            height=rect.height * ratio,
            origin=rect.origin
        )

        top = Rectangle(
            width=rect.width,
            height=rect.height * (1 - ratio),
            origin=(rect.origin[0], split_y)
        )

        return bottom, top

    @staticmethod
    def merge_rectangles(rect_a: Rectangle, rect_b: Rectangle) -> Rectangle:
        """
        Merge two rectangles into bounding box.

        Note: Only produces valid rectangle if original rects are aligned.
        """
        min_x = min(rect_a.origin[0], rect_b.origin[0])
        min_y = min(rect_a.origin[1], rect_b.origin[1])
        max_x = max(rect_a.origin[0] + rect_a.width,
                   rect_b.origin[0] + rect_b.width)
        max_y = max(rect_a.origin[1] + rect_a.height,
                   rect_b.origin[1] + rect_b.height)

        return Rectangle(
            width=max_x - min_x,
            height=max_y - min_y,
            origin=(min_x, min_y)
        )
```

**Tests**:
- [ ] Subdivide 10×8 rect at ratio=0.3 → 3×8 and 7×8
- [ ] Subdivide 10×8 rect vertically at 0.5 → two 10×4
- [ ] Areas conserved: original = sum(subdivided)
- [ ] Merge two 4×4 rects side-by-side → 8×4
- [ ] Test alignment check: merging non-aligned rects → warning

**Step 1.2.2: Parameterized Rules**
```python
@dataclass
class ParametricRule:
    """Graph rule with shape parameters."""
    graph_rule: GraphRule
    shape_params: Dict[str, Any]  # e.g., {'split_ratio': 0.6}

    def apply(self, gs: GraphShape, target_node: str) -> GraphShape:
        """Apply rule with parameters."""
        # Get shape parameters
        ratio = self.shape_params.get('split_ratio', 0.5)

        # Apply graph rule (which calls shape subdivision with ratio)
        # This requires modifying GraphRule.apply to accept params
        return self.graph_rule.apply(gs, target_node, ratio=ratio)

# Example: Parameterized split rule
def split_horizontal_parameterized(ratio: float = 0.5) -> GraphRule:
    """Split rule with configurable ratio."""
    def apply(gs: GraphShape, node_id: str, ratio: float = ratio) -> GraphShape:
        rect = gs.shapes[node_id]

        # Use ShapeRules
        left, right = ShapeRules.subdivide_horizontal(rect, ratio)

        left_id = f"{node_id}_L"
        right_id = f"{node_id}_R"

        new_shapes = gs.shapes.copy()
        del new_shapes[node_id]
        new_shapes[left_id] = left
        new_shapes[right_id] = right

        # Update edges (same as before)
        new_edges = []
        for a, b in gs.edges:
            if a == node_id:
                new_edges.append((left_id, b))
                new_edges.append((right_id, b))
            elif b == node_id:
                new_edges.append((a, left_id))
                new_edges.append((a, right_id))
            else:
                new_edges.append((a, b))
        new_edges.append((left_id, right_id))

        return GraphShape(shapes=new_shapes, edges=new_edges)

    return GraphRule(
        name=f"split_horizontal_r{ratio}",
        description=f"Split horizontal with ratio {ratio}",
        pattern=lambda G, n: True,
        apply=apply
    )
```

**Tests**:
- [ ] Split with ratio 0.3 → left is 30%, right is 70%
- [ ] Split with ratio 0.7 → left is 70%, right is 30%
- [ ] Chain splits: split at 0.5, then split left half at 0.5 → 25%, 25%, 50%
- [ ] Visualize different ratios on same starting rectangle

**Deliverable**: `03_Shape_Rules.ipynb` with:
1. Shape subdivision functions
2. Parameterized graph rules
3. Examples: varying split ratios
4. Area conservation tests

---

## Phase 2: Complex Transformations (Week 3)

**Goal**: Implement multi-step transformations and emergence

### Milestone 2.1: Recursive Subdivision

**Notebook**: `04_Recursive_Subdivision.ipynb`

#### Learning Objectives
- Implement recursive rule application
- Generate hierarchical structures
- Understand emergence from simple rules

#### Implementation Steps

**Step 2.1.1: Recursive Grammar**
```python
class RecursiveGrammar:
    """Apply rules recursively to generate complex structures."""

    def __init__(self, grammar: GraphGrammar):
        self.grammar = grammar

    def subdivide_grid(self, initial: GraphShape,
                       depth: int,
                       rule_sequence: List[str]) -> List[GraphShape]:
        """
        Recursively subdivide starting configuration.

        Args:
            initial: Starting GraphShape (e.g., single rectangle)
            depth: Number of recursive levels
            rule_sequence: Rules to apply at each level (e.g., ['split_h', 'split_v'])

        Returns:
            List of GraphShapes at each level (level 0 = initial, level depth = final)
        """
        levels = [initial]
        current = initial

        for level in range(depth):
            # Get rule for this level (cycle through sequence)
            rule_name = rule_sequence[level % len(rule_sequence)]

            # Apply rule to ALL nodes at current level
            # (This creates a new generation)
            new_shapes = {}
            new_edges = []

            for node_id in current.shapes.keys():
                # Apply rule to this node
                result = self.grammar.apply_rule(current, rule_name, node_id)

                # Collect new shapes and edges
                # (Need to handle ID collisions - add level prefix)
                for new_id, shape in result.shapes.items():
                    prefixed_id = f"L{level}_{new_id}"
                    new_shapes[prefixed_id] = shape

                for a, b in result.edges:
                    new_edges.append((f"L{level}_{a}", f"L{level}_{b}"))

            current = GraphShape(shapes=new_shapes, edges=new_edges)
            levels.append(current)

        return levels
```

**Tests**:
- [ ] Start with 10×10 square
- [ ] Depth 1: split horizontal → 2 rectangles
- [ ] Depth 2: split each vertically → 4 rectangles (2×2 grid)
- [ ] Depth 3: split each horizontally → 8 rectangles
- [ ] Verify: n nodes at level k = 2^k
- [ ] Visualize progression: 1 → 2 → 4 → 8 → 16

**Step 2.1.2: Binary Space Partition (BSP)**
```python
def generate_bsp_tree(width: float, height: float,
                      depth: int,
                      min_size: float = 2.0) -> GraphShape:
    """
    Generate Binary Space Partition (classic dungeon generation algorithm).

    Algorithm:
    1. Start with single rectangle
    2. Randomly split horizontal or vertical
    3. Recursively subdivide children
    4. Stop when depth reached or rectangle too small
    """
    import random

    def split_recursive(rect: Rectangle, current_depth: int,
                       node_id: str, shapes: dict, edges: list):
        """Recursive helper."""
        # Base case: max depth or too small
        if current_depth >= depth or rect.width < min_size or rect.height < min_size:
            shapes[node_id] = rect
            return

        # Choose split direction
        if rect.width > rect.height:
            # Prefer horizontal split for wide rectangles
            direction = 'horizontal' if random.random() < 0.7 else 'vertical'
        else:
            direction = 'vertical' if random.random() < 0.7 else 'horizontal'

        # Choose split ratio (random in range [0.3, 0.7])
        ratio = random.uniform(0.3, 0.7)

        # Split
        if direction == 'horizontal':
            left, right = ShapeRules.subdivide_horizontal(rect, ratio)
            left_id = f"{node_id}_L"
            right_id = f"{node_id}_R"

            # Recurse
            split_recursive(left, current_depth + 1, left_id, shapes, edges)
            split_recursive(right, current_depth + 1, right_id, shapes, edges)

            edges.append((left_id, right_id))
        else:
            bottom, top = ShapeRules.subdivide_vertical(rect, ratio)
            bottom_id = f"{node_id}_B"
            top_id = f"{node_id}_T"

            split_recursive(bottom, current_depth + 1, bottom_id, shapes, edges)
            split_recursive(top, current_depth + 1, top_id, shapes, edges)

            edges.append((bottom_id, top_id))

    # Start recursion
    initial = Rectangle(width=width, height=height, origin=(0, 0))
    shapes = {}
    edges = []
    split_recursive(initial, 0, "root", shapes, edges)

    return GraphShape(shapes=shapes, edges=edges)
```

**Tests**:
- [ ] Generate BSP with depth=3 → ~8 rooms
- [ ] Verify: all rooms between min_size and initial_size
- [ ] Verify: tree structure (each node has 0 or 2 children)
- [ ] Generate 10 BSPs → verify variability
- [ ] Visualize: show tree structure + spatial layout

**Deliverable**: `04_Recursive_Subdivision.ipynb` with:
1. Recursive grammar engine
2. BSP tree generator
3. Examples: uniform subdivision, random BSP
4. Visualization of multi-level hierarchies

---

### Milestone 2.2: Rule Composition

**Notebook**: `05_Rule_Composition.ipynb`

#### Learning Objectives
- Combine multiple rules into higher-level transformations
- Create "macro" rules from sequences
- Understand compositional rule design

#### Implementation Steps

**Step 2.2.1: Rule Sequences as New Rules**
```python
class CompositeRule(GraphRule):
    """A rule composed of multiple sub-rules."""

    def __init__(self, name: str, description: str,
                 sub_rules: List[Tuple[GraphRule, Callable]]):
        """
        Args:
            sub_rules: List of (rule, node_selector) pairs
            node_selector: Function (GraphShape, previous_result) → target_node
        """
        self.sub_rules = sub_rules

        def pattern(G, node_id):
            # Composite rules match based on first sub-rule
            return sub_rules[0][0].pattern(G, node_id)

        def apply(gs, node_id):
            current = gs
            for rule, selector in sub_rules:
                # Select target node for this rule
                target = selector(current, node_id)
                # Apply rule
                current = rule.apply(current, target)
            return current

        super().__init__(name, description, pattern, apply)

# Example: "Split Cross" = split horizontally, then split each piece vertically
def split_cross_rule():
    """Create a cross-shaped subdivision (+ pattern)."""
    h_split = split_horizontal_parameterized(0.5)
    v_split = split_node_vertically()  # Assume this exists

    sub_rules = [
        (h_split, lambda gs, n: n),  # Split original node
        (v_split, lambda gs, n: f"{n}_L"),  # Split left piece
        (v_split, lambda gs, n: f"{n}_R"),  # Split right piece
    ]

    return CompositeRule(
        name="split_cross",
        description="Split into 4 pieces in + pattern",
        sub_rules=sub_rules
    )
```

**Tests**:
- [ ] Apply "split_cross" to 8×8 square → four 4×4 squares
- [ ] Verify graph structure: 4 nodes, edges forming cross
- [ ] Create "split_3x3" composite → 9 equal squares
- [ ] Test error handling: rule fails mid-sequence

**Step 2.2.2: Conditional Rules**
```python
class ConditionalRule(GraphRule):
    """Rule that applies different transformations based on conditions."""

    def __init__(self, name: str,
                 condition: Callable[[GraphShape, str], bool],
                 true_rule: GraphRule,
                 false_rule: GraphRule):
        """
        Args:
            condition: Test function (GraphShape, node_id) → bool
            true_rule: Apply if condition is True
            false_rule: Apply if condition is False
        """
        self.condition = condition
        self.true_rule = true_rule
        self.false_rule = false_rule

        def pattern(G, node_id):
            # Pattern matches if either branch matches
            return self.true_rule.pattern(G, node_id) or self.false_rule.pattern(G, node_id)

        def apply(gs, node_id):
            if self.condition(gs, node_id):
                return self.true_rule.apply(gs, node_id)
            else:
                return self.false_rule.apply(gs, node_id)

        super().__init__(name, f"Conditional: {true_rule.name} | {false_rule.name}",
                        pattern, apply)

# Example: Split wide rectangles horizontally, tall ones vertically
def adaptive_split_rule():
    """Split based on aspect ratio."""
    def is_wide(gs: GraphShape, node_id: str) -> bool:
        rect = gs.shapes[node_id]
        return rect.width > rect.height

    h_split = split_horizontal_parameterized(0.5)
    v_split = split_node_vertically()

    return ConditionalRule(
        name="adaptive_split",
        condition=is_wide,
        true_rule=h_split,
        false_rule=v_split
    )
```

**Tests**:
- [ ] Apply adaptive_split to 10×5 rect → splits horizontally (two 5×5)
- [ ] Apply adaptive_split to 5×10 rect → splits vertically (two 5×5)
- [ ] Chain adaptive splits → creates grid of ~square cells
- [ ] Visualize: show adaptation based on shape

**Deliverable**: `05_Rule_Composition.ipynb` with:
1. Composite rules
2. Conditional rules
3. Examples: cross split, 3×3 split, adaptive split
4. Gallery of composed transformations

---

## Phase 3: Integration with GraphRAG (Week 4)

**Goal**: Connect graph grammar system to Phase 1 GraphRAG output

### Milestone 3.1: GraphRAG → Graph Grammar Pipeline

**Notebook**: `06_GraphRAG_Integration.ipynb`

#### Learning Objectives
- Import TopologicPy graphs from GraphRAG
- Apply shape grammar rules to generated graphs
- Create initial room layouts

#### Implementation Steps

**Step 3.1.1: Import GraphRAG Output**
```python
def graphrag_to_graphshape(topologic_graph) -> GraphShape:
    """
    Convert GraphRAG output (TopologicPy Graph) to GraphShape.

    Strategy:
    - Each graph node → Rectangle (initial size from metadata)
    - Graph edges → shape adjacencies
    - Initial layout: place rectangles using graph positions
    """
    from topologicpy.Graph import Graph as TPGraph
    from topologicpy.Topology import Topology
    from topologicpy.Dictionary import Dictionary

    # Extract vertices and edges
    vertices = TPGraph.Vertices(topologic_graph)
    edges = TPGraph.Edges(topologic_graph)

    # Build GraphShape
    shapes = {}
    edge_list = []

    for i, vertex in enumerate(vertices):
        # Get metadata
        d = Topology.Dictionary(vertex)
        if d:
            props = {k: Dictionary.ValueAtKey(d, k) for k in Dictionary.Keys(d)}
        else:
            props = {}

        # Extract properties
        label = props.get('label', f'room_{i}')
        area = props.get('area', 10.0)  # Default 10m²

        # Estimate rectangle dimensions (assume square-ish, aspect ~1.2)
        aspect = 1.2
        height = (area / aspect) ** 0.5
        width = aspect * height

        # Get position (if available from GraphRAG v03 spatial prediction)
        x = props.get('x', i * (width + 1))  # Fallback: space them out
        y = props.get('y', 0)

        # Create rectangle
        rect = Rectangle(width=width, height=height, origin=(x, y))

        node_id = f"n{i}"
        shapes[node_id] = rect

    # Build edge list
    # (Need to map TopologicPy vertices to node IDs)
    vertex_to_id = {v: f"n{i}" for i, v in enumerate(vertices)}

    for edge in edges:
        start = TPGraph.StartVertex(edge)
        end = TPGraph.EndVertex(edge)

        start_id = vertex_to_id.get(start)
        end_id = vertex_to_id.get(end)

        if start_id and end_id:
            edge_list.append((start_id, end_id))

    return GraphShape(shapes=shapes, edges=edge_list)
```

**Tests**:
- [ ] Load GraphRAG output from `Kuzu_GraphRAG_03.ipynb`
- [ ] Convert to GraphShape
- [ ] Verify: node count matches, edges match
- [ ] Visualize initial layout (before any rules)
- [ ] Check: rectangles sized according to area metadata

**Step 3.1.2: Apply Grammar Rules to Layout**
```python
def layout_apartment(graphshape: GraphShape,
                     style: str = "compact") -> GraphShape:
    """
    Apply shape grammar rules to create spatial layout.

    Args:
        graphshape: Initial GraphShape from GraphRAG
        style: Layout style ('compact', 'spacious', 'linear')

    Returns:
        GraphShape with adjusted room geometries
    """
    grammar = GraphGrammar([
        split_horizontal_parameterized(0.5),
        split_node_vertically(),
        merge_adjacent_nodes(),
        adaptive_split_rule()
    ])

    # Apply style-specific transformations
    if style == "compact":
        # Merge adjacent small rooms
        # Find pairs of rooms with total area < 15m²
        for node_id in graphshape.shapes:
            neighbors = graphshape.get_neighbors(node_id)
            for neighbor in neighbors:
                area_sum = graphshape.shapes[node_id].area + graphshape.shapes[neighbor].area
                if area_sum < 15:
                    graphshape = grammar.apply_rule(graphshape, "merge_adjacent",
                                                   node_id, neighbor_id=neighbor)
                    break

    elif style == "spacious":
        # Split large rooms
        for node_id in list(graphshape.shapes.keys()):
            if graphshape.shapes[node_id].area > 25:
                graphshape = grammar.apply_rule(graphshape, "adaptive_split", node_id)

    return graphshape
```

**Tests**:
- [ ] Generate 2BR apartment with GraphRAG
- [ ] Convert to GraphShape
- [ ] Apply "compact" style → verify merges happen
- [ ] Apply "spacious" style → verify splits happen
- [ ] Visualize before/after

**Deliverable**: `06_GraphRAG_Integration.ipynb` with:
1. GraphRAG import function
2. Layout styling rules
3. Examples: 3 apartment types × 3 styles = 9 layouts
4. Comparison with original GraphRAG output

---

### Milestone 3.2: Validation & Metrics

**Notebook**: `07_Validation.ipynb`

#### Learning Objectives
- Define quality metrics for generated layouts
- Validate graph-shape consistency
- Test against architectural constraints

#### Implementation Steps

**Step 3.2.1: Consistency Checks**
```python
class LayoutValidator:
    """Validate GraphShape configurations."""

    @staticmethod
    def check_graph_shape_consistency(gs: GraphShape) -> Dict[str, bool]:
        """Verify graph and shapes are consistent."""
        checks = {}

        # Check 1: All nodes in graph have shapes
        checks['all_nodes_have_shapes'] = all(
            node_id in gs.shapes for node_id, _ in gs.edges
        ) and all(
            node_id in gs.shapes for _, node_id in gs.edges
        )

        # Check 2: No overlapping shapes
        shapes_list = list(gs.shapes.values())
        checks['no_overlaps'] = True
        for i, rect_a in enumerate(shapes_list):
            for rect_b in shapes_list[i+1:]:
                if rectangles_overlap(rect_a, rect_b):
                    checks['no_overlaps'] = False
                    break

        # Check 3: Adjacent nodes share boundary
        checks['adjacencies_valid'] = True
        for a, b in gs.edges:
            if not rectangles_adjacent(gs.shapes[a], gs.shapes[b]):
                checks['adjacencies_valid'] = False
                break

        # Check 4: Graph is connected
        G = gs.to_networkx()
        checks['graph_connected'] = nx.is_connected(G)

        return checks

    @staticmethod
    def compute_metrics(gs: GraphShape) -> Dict[str, float]:
        """Compute quality metrics."""
        metrics = {}

        # Total area
        metrics['total_area'] = sum(rect.area for rect in gs.shapes.values())

        # Area distribution (std dev)
        areas = [rect.area for rect in gs.shapes.values()]
        metrics['area_std'] = np.std(areas)
        metrics['area_mean'] = np.mean(areas)

        # Aspect ratios
        aspects = [rect.width / rect.height for rect in gs.shapes.values()]
        metrics['aspect_mean'] = np.mean(aspects)
        metrics['aspect_std'] = np.std(aspects)

        # Compactness (ratio of area to bounding box)
        min_x = min(r.origin[0] for r in gs.shapes.values())
        min_y = min(r.origin[1] for r in gs.shapes.values())
        max_x = max(r.origin[0] + r.width for r in gs.shapes.values())
        max_y = max(r.origin[1] + r.height for r in gs.shapes.values())
        bbox_area = (max_x - min_x) * (max_y - min_y)
        metrics['compactness'] = metrics['total_area'] / bbox_area

        # Graph metrics
        G = gs.to_networkx()
        metrics['num_nodes'] = G.number_of_nodes()
        metrics['num_edges'] = G.number_of_edges()
        metrics['avg_degree'] = sum(dict(G.degree()).values()) / G.number_of_nodes()

        return metrics

def rectangles_overlap(a: Rectangle, b: Rectangle) -> bool:
    """Check if two rectangles overlap."""
    # No overlap if one is to the left/right/above/below the other
    if a.origin[0] + a.width <= b.origin[0]:  # a is left of b
        return False
    if b.origin[0] + b.width <= a.origin[0]:  # b is left of a
        return False
    if a.origin[1] + a.height <= b.origin[1]:  # a is below b
        return False
    if b.origin[1] + b.height <= a.origin[1]:  # b is below a
        return False
    return True

def rectangles_adjacent(a: Rectangle, b: Rectangle, tolerance: float = 0.1) -> bool:
    """Check if two rectangles share a boundary."""
    # Check if they share a vertical edge
    if abs(a.origin[0] + a.width - b.origin[0]) < tolerance:
        # a's right edge touches b's left edge
        # Check y-overlap
        y_overlap = min(a.origin[1] + a.height, b.origin[1] + b.height) - max(a.origin[1], b.origin[1])
        if y_overlap > 0:
            return True

    if abs(b.origin[0] + b.width - a.origin[0]) < tolerance:
        # b's right edge touches a's left edge
        y_overlap = min(a.origin[1] + a.height, b.origin[1] + b.height) - max(a.origin[1], b.origin[1])
        if y_overlap > 0:
            return True

    # Check if they share a horizontal edge
    if abs(a.origin[1] + a.height - b.origin[1]) < tolerance:
        # a's top edge touches b's bottom edge
        x_overlap = min(a.origin[0] + a.width, b.origin[0] + b.width) - max(a.origin[0], b.origin[0])
        if x_overlap > 0:
            return True

    if abs(b.origin[1] + b.height - a.origin[1]) < tolerance:
        # b's top edge touches a's bottom edge
        x_overlap = min(a.origin[0] + a.width, b.origin[0] + b.width) - max(a.origin[0], b.origin[0])
        if x_overlap > 0:
            return True

    return False
```

**Tests**:
- [ ] Validate 2×2 grid → all checks pass
- [ ] Introduce overlap → check fails
- [ ] Remove edge → adjacency check fails
- [ ] Compute metrics for 10 generated layouts
- [ ] Compare metrics across styles (compact vs spacious)

**Deliverable**: `07_Validation.ipynb` with:
1. Consistency validators
2. Metric computation
3. Test suite (10+ layouts)
4. Metric comparison charts

---

## Phase 4: Advanced Topics (Week 5-6)

### Milestone 4.1: Non-Rectangular Shapes

**Notebook**: `08_Lshapes_Polygons.ipynb`

#### Goal
- Extend beyond rectangles to L-shapes and arbitrary polygons
- Implement more complex subdivision rules
- Handle non-convex shapes

*(Detailed plan to be developed)*

---

### Milestone 4.2: 3D Extrusion

**Notebook**: `09_3D_Extrusion.ipynb`

#### Goal
- Extrude 2D GraphShapes to 3D using TopologicPy
- Create Cells (3D volumes) from rectangles
- Add walls, doors, windows
- Export to TopologicPy JSON

*(Detailed plan to be developed)*

---

### Milestone 4.3: Streamlit Application

**Goal**: Interactive web app for exploring graph grammars

#### Features
- Upload GraphRAG output or draw custom graph
- Select and apply transformation rules
- Real-time visualization
- Export results (SVG, DXF, Topologic JSON)

*(Detailed plan to be developed)*

---

## Success Criteria

### Phase 0 Complete When:
- [ ] Can create parametric rectangles
- [ ] Can convert to/from TopologicPy Faces
- [ ] Can overlay graphs on shapes
- [ ] Visualization works (shapes, graphs, overlay)
- [ ] All tests pass

### Phase 1 Complete When:
- [ ] Rule library has 5+ transformation rules
- [ ] Can apply rules individually and in sequences
- [ ] Shape transformations driven by graph transformations
- [ ] Parameterized rules work (split ratios)
- [ ] All tests pass

### Phase 2 Complete When:
- [ ] Recursive subdivision works
- [ ] BSP tree generation works
- [ ] Composite and conditional rules work
- [ ] Can generate complex layouts from simple rules
- [ ] All tests pass

### Phase 3 Complete When:
- [ ] GraphRAG output successfully imported
- [ ] Shape grammar rules improve layouts
- [ ] Validation checks all pass
- [ ] Metrics show quality improvement
- [ ] All tests pass

---

## Testing Strategy

### Unit Tests (per Notebook)
Each notebook should have a "Tests" section with:
- [ ] Creation tests (can we create the objects?)
- [ ] Transformation tests (do rules work correctly?)
- [ ] Consistency tests (graph and shapes match?)
- [ ] Round-trip tests (serialize → deserialize)
- [ ] Visualization tests (can we see the results?)

### Integration Tests
After each phase:
- [ ] End-to-end pipeline works
- [ ] Results are reproducible
- [ ] Performance is acceptable (< 10s for typical operations)

### Visual Regression Tests
- Save reference images for key examples
- Compare new outputs to references
- Flag significant visual changes

---

## Development Workflow

### Daily Workflow
```bash
# Morning: Start session
cd /Users/arlav/GitHub/GraphRAG_Grammars
source venv/bin/activate  # if using venv
jupyter lab

# Work in notebook for current milestone
# Run cells, test, visualize
# Document insights

# End of day: Extract code to modules (if ready)
# Update this DEVELOPMENT_PLAN_V2.md with progress
git add .
git commit -m "Milestone X.Y: Description"
git push
```

### Notebook → Module Extraction
When a notebook is stable:
1. Extract reusable classes/functions to `src/grammar/*.py`
2. Add unit tests in `tests/`
3. Update notebook to import from module
4. Verify notebook still works
5. Commit both notebook and module

### Progress Tracking
Update this file weekly with:
- ✅ Completed milestones
- 🚧 In-progress work
- ⏳ Blocked items
- 📝 Key insights/decisions

---

## Open Questions & Design Decisions

### Q1: Should we support non-rectangular shapes in Phase 0-1?
**Decision**: No, start with rectangles only. Add L-shapes and polygons in Phase 4.
**Rationale**: Simpler geometry, easier to reason about adjacency, faster iteration.

### Q2: How to handle shape adjacency when rules break alignments?
**Example**: Merge two non-aligned rectangles → bounding box includes gaps
**Decision**: Add alignment/adjustment step after transformations
**Alternative**: Reject transformations that break adjacency (stricter)

### Q3: Should graph transformations automatically update shapes?
**Decision**: Yes, graph rules include shape transformation logic
**Rationale**: Ensures graph-shape consistency by construction

### Q4: How to integrate with existing PHASE2 notebooks?
**Decision**: This is a parallel exploration. If successful, replace old approach.
**Timeline**: Evaluate after Phase 1 complete (Week 2 end)

---

## Dependencies

### Python Packages
```bash
# Core dependencies
pip install topologicpy  # Includes plotly, pyvis for visualization
pip install networkx     # Graph analysis (used by TopologicPy)
pip install numpy        # Numerical operations
pip install pytest       # Testing framework
pip install jupyter      # Notebook environment
pip install ipywidgets   # Interactive widgets in notebooks

# Note: plotly and pyvis are bundled with topologicpy
# No need to install matplotlib - using TopologicPy's viz instead
```

### Future Dependencies (Phase 4)
```bash
pip install shapely    # For advanced polygon operations (if needed)
pip install streamlit  # For web app interface
# Note: TopologicPy can export to various formats already (JSON, HTML)
```

### Visualization Stack (All via TopologicPy)

**Plotly** (Geometric Visualization):
- 2D/3D shape visualization
- Faces, edges, vertices rendering
- Camera controls (pan, zoom, rotate)
- Export to HTML
- Usage: `Plotly.Show()`, `Plotly.ExportToHTML()`

**pyvis** (Network Visualization):
- Interactive graph visualization
- Physics-based layout
- Drag nodes, zoom, pan
- Configuration panel
- Usage: `Graph.Show()`, `Graph.ExportToPyVis()`

**Benefits**:
- ✅ Interactive (no static images)
- ✅ Shareable (HTML files work in any browser)
- ✅ No additional dependencies (built into TopologicPy)
- ✅ Jupyter-friendly (renders inline)
- ✅ Metadata tooltips (hover to see properties)

---

## Expected Outputs

### Week 1 (Phase 0)
- 2 notebooks: `00_Simple_Shapes.ipynb`, `01_Graphs_On_Shapes.ipynb`
- Gallery: 10+ interactive HTML visualizations (shapes + graphs)
- Deliverables: `shapes_viz.html`, `graphshape_viz.html`, `graph_viz.html`

### Week 2 (Phase 1)
- 3 notebooks: `02_Graph_Rules.ipynb`, `03_Shape_Rules.ipynb`, `05_Rule_Composition.ipynb`
- Rule library: 8+ transformation rules
- Gallery: 20+ interactive before/after transformations (HTML)
- Deliverables: Rule transformation visualizations showing graph → shape changes

### Week 3 (Phase 2)
- 2 notebooks: `04_Recursive_Subdivision.ipynb`, `05_Rule_Composition.ipynb` (extended)
- Generated layouts: 50+ BSP trees, recursive grids
- Interactive visualizations: Multi-level hierarchy exploration (pyvis network + Plotly geometry)

### Week 4 (Phase 3)
- 2 notebooks: `06_GraphRAG_Integration.ipynb`, `07_Validation.ipynb`
- Integrated pipeline: GraphRAG → Grammar → Validated Layout
- Metrics: Performance comparison vs old approach
- Deliverables: Interactive dashboard showing layout quality metrics

---

## Risk Mitigation

### Risk 1: Graph transformations don't produce valid 2D layouts
**Mitigation**: Start with simple transformations (split/merge). Add validation early.

### Risk 2: Too complex, takes too long to implement
**Mitigation**: Each phase is standalone. Can stop after Phase 1 if needed.

### Risk 3: Doesn't integrate well with GraphRAG
**Mitigation**: Test integration in Phase 3. Adjust if needed.

---

## Success Metrics

### Qualitative
- Layouts look "architectural" (rectangular rooms, reasonable proportions)
- Graph transformations are intuitive
- System is extensible (easy to add new rules)

### Quantitative
- 90%+ of generated layouts pass validation
- Rule application < 1s per transformation
- Can generate 100+ unique layouts from same starting graph

---

**Last Updated**: 2025-12-23
**Current Phase**: 0 (Foundations)
**Next Milestone**: 0.1 (Simple Parametric Shapes)
