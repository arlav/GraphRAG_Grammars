# GraphRAG + Shape Grammars: Implementation TODO List

## Phase 2: Shape Grammar Development (30 Actions)

### Module 1: Shape Library Foundation (8 actions)

#### Action 1: Project Setup
- [ ] Create directory structure
  ```bash
  mkdir -p src/{grammar,geometry,utils}
  mkdir -p tests notebooks data/{examples,outputs}
  touch src/grammar/{__init__.py,shapes.py,rules.py,constraints.py,materializer.py}
  touch src/geometry/{__init__.py,primitives.py,operations.py,compas_bridge.py}
  ```
- [ ] Set up virtual environment and dependencies
  ```bash
  python -m venv venv
  source venv/bin/activate
  pip install topologicpy kuzu pydantic
  pip install scikit-geometry  # May need conda
  pip install compas compas_cgal
  pip install numpy scipy matplotlib networkx
  pip install pytest pytest-cov
  ```
- [ ] Create `requirements.txt`
- [ ] Set up pytest configuration (`pytest.ini`)
- [ ] Initialize/verify git repo

#### Action 2: Shape Schema Design
- [ ] Implement `RoomFunction` enum in `shapes.py` (Living, Dining, Kitchen, Bedroom, Bathroom, Entrance, Hallway, Storage, Balcony)
- [ ] Implement `ShapeType` enum (rectangle, l_shape, polygon)
- [ ] Implement `BaseShape` Pydantic model with:
  - [ ] Fields: shape_type, room_function, min_area, max_area, aspect_ratio_range
  - [ ] Validators for area range (max >= min)
  - [ ] Validators for aspect ratio
  - [ ] Abstract methods: `generate_polygon()`, `validate_constraints()`
- [ ] Write docstrings for all classes (Google style)
- [ ] Create simple test to validate Pydantic schema works

#### Action 3: Implement Rectangular Rooms
- [ ] Implement `RectangularRoom` class extending `BaseShape`
  - [ ] Fields: width, height
  - [ ] Validators: minimum dimension 1.5m (building codes)
- [ ] Implement `generate_polygon(anchor, rotation)` method
  - [ ] Define corners as numpy array (counter-clockwise)
  - [ ] Apply rotation matrix if rotation != 0
  - [ ] Translate to anchor point
  - [ ] Convert to scikit-geometry Polygon
- [ ] Implement `validate_constraints()` method
  - [ ] Check area within [min_area, max_area]
  - [ ] Check aspect ratio within range
- [ ] Write comprehensive docstrings with examples

#### Action 4: Test Rectangular Rooms
- [ ] Write test: `test_rectangular_room_creation`
  - [ ] Create 5×4m room
  - [ ] Assert area = 20.0m²
  - [ ] Assert 4 vertices
  - [ ] Assert passes validation
- [ ] Write test: `test_rectangular_room_rotation`
  - [ ] Generate at 0°, 45°, 90°, 180°
  - [ ] Assert area preserved for all rotations
  - [ ] Assert vertices rotate correctly
- [ ] Write test: `test_rectangular_room_anchoring`
  - [ ] Generate at (0,0), (10,5), (-5,-5)
  - [ ] Assert bottom-left corner at anchor
- [ ] Write test: `test_rectangular_validation_fails`
  - [ ] Create room with invalid dimensions
  - [ ] Assert validation returns False
- [ ] Run: `pytest tests/test_shapes.py::test_rectangular -v`

#### Action 5: Implement L-Shaped Rooms
- [ ] Implement `LShapedRoom` class extending `BaseShape`
  - [ ] Fields: arm1_width, arm1_length, arm2_width, arm2_length
  - [ ] Design L-shape coordinate system (document with ASCII art)
- [ ] Implement `generate_polygon(anchor, rotation)` method
  - [ ] Define 6 vertices for L-shape (counter-clockwise)
  - [ ] Apply rotation matrix
  - [ ] Translate to anchor
  - [ ] Convert to scikit-geometry Polygon
- [ ] Implement `validate_constraints()` method
  - [ ] Check total area = arm1_area + arm2_area - overlap
  - [ ] Ensure within [min_area, max_area]
- [ ] Write comprehensive docstrings

#### Action 6: Test L-Shaped Rooms
- [ ] Write test: `test_l_shaped_room_creation`
  - [ ] Create L-shape with known dimensions
  - [ ] Assert area calculation correct
  - [ ] Assert 6 vertices
  - [ ] Assert passes validation
- [ ] Write test: `test_l_shaped_room_rotation`
  - [ ] Generate at 0°, 90°, 180°, 270°
  - [ ] Assert area preserved
- [ ] Write test: `test_l_shaped_various_configurations`
  - [ ] Test different arm length ratios
  - [ ] Verify all produce valid polygons
- [ ] Run: `pytest tests/test_shapes.py::test_l_shaped -v`

#### Action 7: Shape Assignment System
- [ ] Create `SHAPE_DEFAULTS` dictionary mapping RoomFunction → BaseShape
  - [ ] Living: RectangularRoom(5.0×4.0m, 15-30m²)
  - [ ] Kitchen: LShapedRoom(arms: 3.0×2.5m + 4.0×2.0m, 8-15m²)
  - [ ] Bedroom: RectangularRoom(3.5×3.0m, 9-20m², Swiss code compliance)
  - [ ] Bathroom: RectangularRoom(2.0×2.5m, 3.5-8m²)
  - [ ] Entrance: RectangularRoom(1.8×2.0m, 2-6m²)
  - [ ] Other room types as needed
- [ ] Implement `assign_shape(room_label: str, props: Dict) -> BaseShape`
  - [ ] Normalize label (lowercase, strip whitespace)
  - [ ] Match against RoomFunction enum values
  - [ ] Return copy of default shape
  - [ ] TODO: Adjust dimensions based on props['area'] if present
  - [ ] Fallback: generic 3×3m rectangle for unknown types
- [ ] Write tests for `assign_shape()`
  - [ ] Test each room type ("Living", "Kitchen", etc.)
  - [ ] Test case insensitivity ("BEDROOM", "bedroom")
  - [ ] Test partial matches ("Living Room" → Living)
  - [ ] Test unknown type returns default

#### Action 8: Shape Library Demo & Documentation
- [ ] Create demo notebook: `notebooks/02a_shape_library_demo.ipynb`
  - [ ] Import shape classes
  - [ ] Create examples of each shape type
  - [ ] Visualize with matplotlib (simple polygon plots)
  - [ ] Demo rotation (show same room at 0°, 45°, 90°)
  - [ ] Demo sizing variations (3×3m vs 5×4m living room)
  - [ ] Show shape assignment for various room labels
- [ ] Add README section on shape library usage
- [ ] Verify all tests pass: `pytest tests/test_shapes.py -v`
- [ ] Check coverage: `pytest --cov=src.grammar.shapes tests/test_shapes.py`
- [ ] Commit: `git add . && git commit -m "Add parametric shape library with tests"`

---

### Module 2: Constraint Solver - Initial Layout (5 actions)

#### Action 9: Data Structures for Optimization
- [ ] Create `constraints.py` file
- [ ] Implement `ShapeNode` dataclass
  - [ ] Fields: id, label, shape_template, polygon, position, rotation, fixed
  - [ ] position: np.ndarray (x, y)
  - [ ] rotation: float (degrees)
  - [ ] fixed: bool (if True, don't move during optimization)
- [ ] Implement `AdjacencyConstraint` dataclass
  - [ ] Fields: node_a (str), node_b (str), weight (float)
  - [ ] weight: importance of constraint (default 1.0)
- [ ] Write simple tests to instantiate these objects
- [ ] Write test: create ShapeNode with RectangularRoom template

#### Action 10: Force-Directed Layout Algorithm
- [ ] Implement `LayoutOptimizer` class skeleton
- [ ] Implement `compute_initial_positions(graph)` method
  - [ ] Convert adjacency constraints to NetworkX graph
  - [ ] Add nodes for each ShapeNode
  - [ ] Add edges for each AdjacencyConstraint (weighted)
  - [ ] Call `nx.spring_layout()` with appropriate k parameter
  - [ ] Scale positions by average room size (e.g., k = avg_width * 2)
  - [ ] Return dict: {node_id: np.array([x, y])}
- [ ] Write test with simple 3-node triangle graph
  - [ ] Create 3 ShapeNodes
  - [ ] Create 3 constraints (fully connected)
  - [ ] Compute initial positions
  - [ ] Assert positions are distinct
  - [ ] Assert positions form reasonable triangle
- [ ] Visualize initial positions with scatter plot

#### Action 11: Basic Optimizer Structure
- [ ] Implement `LayoutOptimizer.__init__(shapes, constraints)`
  - [ ] Store shapes as dict: {id: ShapeNode}
  - [ ] Store constraints as list
- [ ] Implement skeleton `optimize(max_iterations)` method
  - [ ] Call `compute_initial_positions()`
  - [ ] Update each ShapeNode's position
  - [ ] Generate polygons at new positions (call shape_template.generate_polygon())
  - [ ] Update ShapeNode.polygon
  - [ ] Return list of ShapeNodes (no actual optimization yet)
- [ ] Write test: verify shapes created at initial positions
  - [ ] Create 4-5 room graph
  - [ ] Run optimizer
  - [ ] Assert all shapes have non-None polygons
  - [ ] Assert positions are spread out (not all at origin)

#### Action 12: Visualization Infrastructure
- [ ] Create `src/utils/visualization.py`
- [ ] Define `ROOM_COLORS` dictionary
  - [ ] Living: '#FFE5B4' (peach)
  - [ ] Dining: '#FFDAB9' (peach puff)
  - [ ] Kitchen: '#FFA07A' (light salmon)
  - [ ] Bedroom: '#B0E0E6' (powder blue)
  - [ ] Bathroom: '#ADD8E6' (light blue)
  - [ ] Entrance: '#F0E68C' (khaki)
  - [ ] Hallway: '#F5F5DC' (beige)
  - [ ] Default: '#CCCCCC' (gray)
- [ ] Implement `visualize_layout(layout, save_path=None, show=True)`
  - [ ] Create matplotlib figure (12×12 inches)
  - [ ] For each room: create matplotlib Polygon patch
  - [ ] Color by room type
  - [ ] Add edge (black, linewidth=2)
  - [ ] Draw all patches with PatchCollection
  - [ ] Add text labels at polygon centroids (room name + area)
  - [ ] Set equal aspect ratio
  - [ ] Add grid, axis labels
  - [ ] Add title with metadata (# rooms, total area)
  - [ ] Save if save_path provided
  - [ ] Show if show=True
- [ ] Write test with mock layout data
- [ ] Generate example output image

#### Action 13: Initial Layout Integration Test
- [ ] Create end-to-end test: Graph → Initial Layout → Visualization
  - [ ] Create test with 4 rooms (2×2 grid topology)
  - [ ] Create ShapeNodes (all rectangles for simplicity)
  - [ ] Create adjacency constraints
  - [ ] Run optimizer (initial layout only, no alignment yet)
  - [ ] Visualize result
  - [ ] Save to `data/outputs/test_initial_layout.png`
- [ ] Test with additional topologies:
  - [ ] Linear chain: 3 rooms in a row
  - [ ] Star: 1 center room + 4 adjacent rooms
  - [ ] L-shape: 5 rooms forming an L
- [ ] Document force-directed layout approach in docstrings
- [ ] Commit: `git commit -m "Add initial layout with force-directed positioning"`

---

### Module 3: Constraint Solver - Alignment (5 actions)

#### Action 14: Edge Finding Algorithm
- [ ] Implement `find_closest_edges(poly_a: Polygon, poly_b: Polygon)` method
  - [ ] Extract edges from poly_a using `.edges` (scikit-geometry)
  - [ ] Extract edges from poly_b using `.edges`
  - [ ] For each pair of edges:
    - [ ] Compute midpoint of each edge
    - [ ] Compute Euclidean distance between midpoints
  - [ ] Return pair with minimum distance as (Segment2, Segment2)
- [ ] Write tests:
  - [ ] Test with two axis-aligned rectangles side-by-side (should find facing edges)
  - [ ] Test with rectangles at 45° rotation
  - [ ] Test with rectangle + L-shape
  - [ ] Assert returned edges are actually the closest
- [ ] Visualize edge pairs:
  - [ ] Draw two polygons
  - [ ] Highlight closest edges in red
  - [ ] Save visualization for debugging

#### Action 15: Edge Alignment - Rotation
- [ ] Implement `align_edge_to_edge(shape_a, shape_b, edge_a, edge_b)` - Part 1: Rotation
  - [ ] Extract edge vectors (target - source) for both edges
  - [ ] Compute angle of each vector using np.arctan2()
  - [ ] Compute rotation needed: angle_a - angle_b
  - [ ] Apply rotation to shape_b:
    - [ ] new_rotation = shape_b.rotation + rotation_needed
    - [ ] Regenerate polygon with new rotation
  - [ ] Return updated ShapeNode (position unchanged for now)
- [ ] Write tests:
  - [ ] Create two rectangles at random orientations (0°-360°)
  - [ ] Find closest edges
  - [ ] Apply rotation alignment
  - [ ] Assert: edge vectors are now parallel (dot product check)
  - [ ] Visualize before/after rotation
- [ ] Handle edge case: 180° flip (edges parallel but opposite direction)

#### Action 16: Edge Alignment - Translation
- [ ] Implement `align_edge_to_edge()` - Part 2: Translation
  - [ ] After rotation, compute translation vector
  - [ ] Goal: move shape_b so edge_b is collinear with edge_a
  - [ ] Method: translate edge_b.source to align with edge_a.source
  - [ ] Update shape_b.position
  - [ ] Regenerate polygon at new position
  - [ ] Return updated ShapeNode
- [ ] Write tests:
  - [ ] Two rectangles at random positions
  - [ ] After alignment, edges should be collinear
  - [ ] Check: distance between edge midpoints < 0.01m threshold
  - [ ] Check: edges overlap (share at least some segment)
- [ ] Visualize alignment process (3 stages: initial, rotated, translated)
- [ ] Test with various room pairs (rectangle-rectangle, rectangle-Lshape)

#### Action 17: Edge Length Matching
- [ ] Implement edge length adjustment in `align_edge_to_edge()`
  - [ ] After alignment, check if edges have different lengths
  - [ ] If length mismatch:
    - [ ] Option A: Scale shape_b proportionally to match edge length
    - [ ] Option B: Adjust only one dimension of shape_b
    - [ ] Ensure adjusted shape still satisfies area constraints
    - [ ] If can't satisfy: log warning, keep best approximation
- [ ] Write tests:
  - [ ] Align 3×3m room with 4×3m room
  - [ ] After adjustment, shared edge should have same length
  - [ ] Verify areas stay within [min_area, max_area]
  - [ ] Test constraint violation case: can't shrink room below min_area
- [ ] Handle edge cases:
  - [ ] Very small rooms (can't shrink further)
  - [ ] Extreme aspect ratios (reject if outside bounds)
- [ ] Document algorithm with diagrams/comments

#### Action 18: Alignment Integration & Testing
- [ ] Integrate `align_edge_to_edge()` into `optimize()` loop
  - [ ] After initial positioning, iterate through constraints
  - [ ] For each constraint: apply alignment to one shape
  - [ ] Update shapes dict with aligned version
  - [ ] Track total position change (for convergence check)
- [ ] Test alignment on simple pairs:
  - [ ] Two horizontal rectangles → should snap together
  - [ ] Two rectangles (one rotated 45°) → should align and snap
  - [ ] Rectangle + L-shape → should align to best edge
- [ ] Visualize before/after alignment for each test case
- [ ] Create debug mode: save visualization at each iteration
- [ ] Document alignment algorithm in DEVELOPMENT_PLAN.md
- [ ] Commit: `git commit -m "Add edge-to-edge alignment with rotation and translation"`

---

### Module 4: Global Optimization & COMPAS (5 actions)

#### Action 19: Iterative Optimization Loop
- [ ] Implement full `optimize(max_iterations=50)` method
  - [ ] Step 1: Initialize positions with force-directed layout
  - [ ] Step 2: Generate initial polygons
  - [ ] Step 3: For iteration in range(max_iterations):
    - [ ] changes_made = False
    - [ ] For each constraint in constraints:
      - [ ] Get shape_a and shape_b
      - [ ] Skip if both are fixed
      - [ ] Find closest edges
      - [ ] Align shape_b to shape_a (or vice versa if shape_a not fixed)
      - [ ] Check position change: if > threshold, set changes_made = True
      - [ ] Update shapes dict
    - [ ] If not changes_made: break (converged)
  - [ ] Step 4: Return final list of ShapeNodes
- [ ] Add logging: print iteration number, changes made
- [ ] Write test: 3-room linear layout should converge in < 10 iterations
- [ ] Test: verify convergence detection works (stops before max_iterations)

#### Action 20: COMPAS Integration Setup
- [ ] Create `src/geometry/compas_bridge.py`
- [ ] Implement `skgeom_to_compas(poly: SkPolygon) -> CompasPolygon`
  - [ ] Extract vertices from scikit-geometry polygon
  - [ ] Convert to COMPAS Point objects (x, y, 0)
  - [ ] Create COMPAS Polygon from points
  - [ ] Return CompasPolygon
- [ ] Implement `compas_to_skgeom(poly: CompasPolygon) -> SkPolygon`
  - [ ] Extract points from COMPAS polygon
  - [ ] Convert to scikit-geometry Point2 objects
  - [ ] Create scikit-geometry Polygon
  - [ ] Return SkPolygon
- [ ] Write conversion tests:
  - [ ] Round-trip test: skgeom → compas → skgeom
  - [ ] Assert vertices preserved (within floating point tolerance)
  - [ ] Test with rectangle, L-shape, irregular polygon
- [ ] Test with polygons containing holes (if needed)

#### Action 21: Overlap Detection with COMPAS
- [ ] Implement `check_overlap(poly_a: SkPolygon, poly_b: SkPolygon) -> bool`
  - [ ] Convert both to COMPAS polygons
  - [ ] Use `boolean_intersection(compas_a, compas_b)` from compas_cgal
  - [ ] Check if intersection result is non-empty
  - [ ] Return True if area of intersection > 0.01m² (tolerance)
  - [ ] Handle exceptions (CGAL can fail on degenerate cases)
- [ ] Add overlap checking to optimizer:
  - [ ] After each iteration, check all non-adjacent room pairs
  - [ ] If overlap detected, apply repulsion:
    - [ ] Compute vector from poly_a centroid to poly_b centroid
    - [ ] Move poly_b away by small distance (e.g., 0.5m)
  - [ ] Continue optimization
- [ ] Write tests:
  - [ ] Test with overlapping rectangles → should return True
  - [ ] Test with non-overlapping rectangles → should return False
  - [ ] Test with adjacent rectangles (touching but not overlapping) → should return False
- [ ] Add overlap penalty visualization (highlight overlapping rooms in red)

#### Action 22: Constraint Relaxation & Soft Constraints
- [ ] Implement soft constraint energy function
  - [ ] E_total = Σ w_i × distance(edge_a, edge_b)²
  - [ ] w_i = weight from AdjacencyConstraint
  - [ ] distance = gap between closest points on edges
- [ ] Implement `compute_layout_energy(shapes, constraints)` method
  - [ ] For each constraint: compute edge distance penalty
  - [ ] For each non-adjacent pair: compute overlap penalty
  - [ ] Return total energy
- [ ] Add gradient descent optimization (optional, alternative to greedy):
  - [ ] Compute energy gradient w.r.t. positions
  - [ ] Update positions in direction of negative gradient
  - [ ] Use scipy.optimize.minimize()
- [ ] Test with over-constrained graph:
  - [ ] Create impossible layout (e.g., 5 rooms all adjacent)
  - [ ] Verify optimizer produces reasonable approximation
  - [ ] No crashes, graceful degradation
- [ ] Document soft constraint approach in comments

#### Action 23: Complex Layout Testing
- [ ] Test with 6-8 room layouts of various topologies:
  - [ ] Star: 1 central room (living) + 5 surrounding (bedrooms, bath, kitchen, etc.)
  - [ ] Grid: 3×3 rooms (apartment with hallway)
  - [ ] Linear: 6 rooms in a row (railroad apartment)
  - [ ] Random: 8 rooms with random adjacencies
- [ ] For each test:
  - [ ] Run optimizer
  - [ ] Visualize result
  - [ ] Check: no gaps > 5cm
  - [ ] Check: no overlaps
  - [ ] Check: areas within constraints
  - [ ] Measure: convergence iterations, time elapsed
- [ ] Benchmark performance:
  - [ ] 5 rooms: target < 5 seconds
  - [ ] 10 rooms: target < 30 seconds
  - [ ] 15 rooms: target < 60 seconds
- [ ] Identify failure cases:
  - [ ] Document in TODO.md under "Known Limitations"
  - [ ] Examples: highly over-constrained, impossible geometries
- [ ] Commit: `git commit -m "Add global optimization with COMPAS overlap detection"`

---

### Module 5: Graph-to-Layout Pipeline (5 actions)

#### Action 24: TopologicPy Graph Extraction
- [ ] Create `src/grammar/materializer.py`
- [ ] Implement helper: `extract_graph_data(topologic_graph: TPGraph) -> tuple`
  - [ ] Extract vertices: `Graph.Vertices(topologic_graph)`
  - [ ] Extract edges: `Graph.Edges(topologic_graph)`
  - [ ] For each vertex:
    - [ ] Get dictionary: `Topology.Dictionary(vertex)`
    - [ ] Extract all key-value pairs from dictionary
    - [ ] Get label from 'label' or 'roomtype' or 'node_name' key
    - [ ] Store as dict: {vertex_index: {label, props}}
  - [ ] For each edge:
    - [ ] Get start vertex: `Graph.StartVertex(edge)`
    - [ ] Get end vertex: `Graph.EndVertex(edge)`
    - [ ] Find indices in vertex list
    - [ ] Store as tuple: (start_idx, end_idx)
  - [ ] Return: (vertex_data_list, edge_pairs_list)
- [ ] Write test with mock TopologicPy graph:
  - [ ] Create simple 3-node graph using TopologicPy API
  - [ ] Attach dictionaries to vertices
  - [ ] Extract data
  - [ ] Assert correct number of vertices/edges
  - [ ] Assert labels extracted correctly

#### Action 25: Shape Node Creation from Graph
- [ ] Implement `create_shape_nodes(vertex_data: list) -> list[ShapeNode]`
  - [ ] For each vertex_data item:
    - [ ] Get label from props
    - [ ] Call `assign_shape(label, props)` to get shape template
    - [ ] Create ShapeNode with:
      - [ ] id = f'n{index}'
      - [ ] label = extracted label
      - [ ] shape_template = assigned shape
      - [ ] polygon = None (will be generated later)
      - [ ] position = [0, 0] (will be set by optimizer)
      - [ ] rotation = 0
      - [ ] fixed = (index == 0) (fix first node as anchor)
    - [ ] Append to list
  - [ ] Return list of ShapeNodes
- [ ] Write test:
  - [ ] Create mock vertex data with various room types
  - [ ] Call create_shape_nodes()
  - [ ] Assert: number of ShapeNodes == number of vertices
  - [ ] Assert: correct shape types assigned (rectangles for bedrooms, L-shape for kitchen)
  - [ ] Assert: first node is fixed

#### Action 26: Constraint Creation from Edges
- [ ] Implement `create_constraints(edge_pairs: list, num_vertices: int) -> list[AdjacencyConstraint]`
  - [ ] For each (start_idx, end_idx) in edge_pairs:
    - [ ] Create AdjacencyConstraint with:
      - [ ] node_a = f'n{start_idx}'
      - [ ] node_b = f'n{end_idx}'
      - [ ] weight = 1.0 (default, could extract from edge properties later)
    - [ ] Append to list
  - [ ] Return list of AdjacencyConstraints
- [ ] Write test:
  - [ ] Create mock edge pairs
  - [ ] Call create_constraints()
  - [ ] Assert: number of constraints == number of edges
  - [ ] Assert: node_a and node_b IDs are correct
  - [ ] Assert: all weights are 1.0

#### Action 27: Complete Graph-to-Layout Pipeline
- [ ] Implement `graph_to_layout(topologic_graph: TPGraph) -> dict`
  - [ ] Step 1: Extract data
    - [ ] vertex_data, edge_pairs = extract_graph_data(topologic_graph)
  - [ ] Step 2: Create shape nodes
    - [ ] shape_nodes = create_shape_nodes(vertex_data)
  - [ ] Step 3: Create constraints
    - [ ] constraints = create_constraints(edge_pairs, len(vertex_data))
  - [ ] Step 4: Run optimizer
    - [ ] optimizer = LayoutOptimizer(shape_nodes, constraints)
    - [ ] optimized_shapes = optimizer.optimize(max_iterations=50)
  - [ ] Step 5: Format output
    - [ ] For each shape: extract polygon coordinates, area, label, props
    - [ ] Build dict with structure: {rooms: [...], adjacencies: [...], metadata: {...}}
  - [ ] Return formatted layout dict
- [ ] Write integration test:
  - [ ] Create mock TopologicPy graph (4 rooms: Living, Kitchen, Bedroom, Bathroom)
  - [ ] Add edges: Living-Kitchen, Living-Bedroom, Bedroom-Bathroom
  - [ ] Call graph_to_layout()
  - [ ] Assert: output has 4 rooms
  - [ ] Assert: each room has polygon, area, label
  - [ ] Assert: adjacencies match input edges
  - [ ] Visualize output with visualize_layout()

#### Action 28: GraphRAG Integration Testing
- [ ] Load actual Phase 1 output (from Kuzu_GraphRAG_New.ipynb)
  - [ ] Run one iteration of `graphrag_build_loop()`
  - [ ] Extract final snapshot: `result['snapshots'][-1]`
  - [ ] This is a TopologicPy Graph object
- [ ] Pass to `graph_to_layout()`
- [ ] Visualize result with `visualize_layout()`
- [ ] Validate output:
  - [ ] Check all rooms have polygons
  - [ ] Check no gaps/overlaps
  - [ ] Check areas reasonable
- [ ] Test with 5 different GraphRAG outputs:
  - [ ] 1-bedroom apartment
  - [ ] 2-bedroom apartment
  - [ ] 3-bedroom apartment
  - [ ] Studio apartment
  - [ ] Penthouse (large, 5+ rooms)
- [ ] For each: save visualization to `data/outputs/`
- [ ] Document any failures or issues
- [ ] Commit: `git commit -m "Add complete graph-to-layout pipeline with GraphRAG integration"`

---

### Module 6: Visualization, Export & Polish (6 actions)

#### Action 29: Enhanced Visualization
- [ ] Improve `visualize_layout()` function:
  - [ ] Add legend showing room types with colors
  - [ ] Add dimension annotations on room polygons (width × height)
  - [ ] Add north arrow (if orientation matters)
  - [ ] Add scale bar (e.g., "0 — 5m")
  - [ ] Improve fonts: title (16pt bold), labels (10pt), annotations (8pt)
  - [ ] Add subtle drop shadow to polygons (depth effect)
- [ ] Create multiple view modes:
  - [ ] `mode='colored'`: Color by room type (default)
  - [ ] `mode='area'`: Color by area (heatmap, matplotlib colormap)
  - [ ] `mode='bw'`: Black & white, architectural style (thick borders, no fill)
- [ ] Add parameter: `show_grid: bool` (default True)
- [ ] Add parameter: `show_labels: bool` (default True)
- [ ] Test all view modes with 10+ layouts
- [ ] Create gallery: save 20 example layouts in different styles

#### Action 30: SVG Export
- [ ] Install svgwrite: `pip install svgwrite`
- [ ] Implement `export_svg(layout: dict, output_path: str)`
  - [ ] Create SVG drawing with svgwrite
  - [ ] Set viewBox to match layout bounds (with padding)
  - [ ] For each room:
    - [ ] Create <polygon> element with vertices
    - [ ] Set fill color (from ROOM_COLORS)
    - [ ] Set stroke (black, width=2)
    - [ ] Add <text> element for room label at centroid
  - [ ] Add title, description metadata
  - [ ] Save to file
- [ ] Write test:
  - [ ] Export mock layout to SVG
  - [ ] Assert file created
  - [ ] Open in browser: verify visual correctness
- [ ] Test: open exported SVG in Inkscape, verify editability
- [ ] Export 10 examples to `data/outputs/*.svg`

#### Action 31: DXF Export for CAD
- [ ] Install ezdxf: `pip install ezdxf`
- [ ] Implement `export_dxf(layout: dict, output_path: str)`
  - [ ] Create DXF document: `ezdxf.new('R2010')`
  - [ ] Get modelspace: `doc.modelspace()`
  - [ ] Create layers (one per room type):
    - [ ] Layer "LIVING", "BEDROOM", "KITCHEN", etc.
    - [ ] Set layer colors
  - [ ] For each room:
    - [ ] Create LWPOLYLINE entity with polygon vertices
    - [ ] Assign to appropriate layer
    - [ ] Add TEXT entity for room label
  - [ ] Save document to file
- [ ] Write test:
  - [ ] Export mock layout to DXF
  - [ ] Assert file created
  - [ ] Open in FreeCAD or AutoCAD: verify correctness
- [ ] Test: verify layers are correct, text is readable
- [ ] Export examples to `data/outputs/*.dxf`

#### Action 32: Variation Generator
- [ ] Implement `generate_variations(topologic_graph: TPGraph, n_variations: int = 10) -> list[dict]`
  - [ ] For i in range(n_variations):
    - [ ] Extract graph data
    - [ ] Create shape nodes
    - [ ] Randomly sample dimensions:
      - [ ] For each shape: width = uniform(min_width, max_width)
      - [ ] height = area / width (keep area constant)
      - [ ] Ensure aspect ratio within bounds
    - [ ] Create constraints
    - [ ] Run optimizer with different random seed
    - [ ] Collect output layout
  - [ ] Return list of layout dicts
- [ ] Write test:
  - [ ] Generate 10 variations from one graph
  - [ ] Assert: all variations valid (no gaps/overlaps)
  - [ ] Assert: variations are diverse (not all identical)
  - [ ] Compute diversity metric: average pairwise difference in positions
- [ ] Visualize variations:
  - [ ] Create grid of subplots (2×5 or 3×4)
  - [ ] Show all variations side-by-side
  - [ ] Save as single image: `data/outputs/variations_grid.png`
- [ ] Analyze diversity:
  - [ ] Compute area variance for each room across variations
  - [ ] Compute position variance
  - [ ] Document results

#### Action 33: Comprehensive Demo Notebook
- [ ] Create `notebooks/03_shape_grammar_complete.ipynb`
  - [ ] Section 1: Setup
    - [ ] Imports
    - [ ] Load Swiss dwelling dataset sample
  - [ ] Section 2: Phase 1 - GraphRAG
    - [ ] Set up Kuzu database
    - [ ] Import example graphs
    - [ ] Run `graphrag_build_loop()` to generate new apartment
    - [ ] Visualize abstract graph (node-link diagram)
  - [ ] Section 3: Phase 2 - Shape Grammar
    - [ ] Convert TopologicPy graph to 2D layout
    - [ ] Call `graph_to_layout()`
    - [ ] Show optimization process (initial → final)
    - [ ] Visualize final layout (colored, area, b&w modes)
  - [ ] Section 4: Export
    - [ ] Export to SVG
    - [ ] Export to DXF
    - [ ] Show file paths
  - [ ] Section 5: Variations
    - [ ] Generate 10 variations
    - [ ] Show variation grid
    - [ ] Analyze diversity metrics
  - [ ] Section 6: Batch Processing
    - [ ] Generate 5 different apartment types
    - [ ] Show gallery of all layouts
- [ ] Test: run notebook end-to-end, verify no errors
- [ ] Add markdown explanations between code cells
- [ ] Include example outputs (images) in notebook

#### Action 34: Documentation & Final Polish
- [ ] Update `README.md`:
  - [ ] Add installation instructions (step-by-step)
  - [ ] Add "Quick Start" section with code example
  - [ ] Add API documentation links
  - [ ] Add gallery of example outputs (20 images)
- [ ] Generate API documentation:
  - [ ] Set up Sphinx: `pip install sphinx`
  - [ ] Configure sphinx: `sphinx-quickstart docs/`
  - [ ] Auto-generate from docstrings: `sphinx-apidoc -o docs/source src/`
  - [ ] Build HTML docs: `cd docs && make html`
  - [ ] Verify docs render correctly
- [ ] Write `DEVELOPMENT_PLAN.md` summary:
  - [ ] Add "Phase 2 Complete" section
  - [ ] Summarize achievements
  - [ ] List known limitations
  - [ ] Outline next steps (Phase 3)
- [ ] Create example gallery: `data/outputs/gallery.md`
  - [ ] Include 20+ layout images
  - [ ] Organize by apartment type
  - [ ] Add captions with metadata
- [ ] Run final test suite:
  - [ ] `pytest tests/ -v --cov=src`
  - [ ] Ensure > 90% coverage
  - [ ] Fix any failing tests
- [ ] Run linting:
  - [ ] `flake8 src/`
  - [ ] Fix any style issues
- [ ] Final commit: `git add . && git commit -m "Complete Phase 2: Shape grammar with full pipeline, visualization, and export"`
- [ ] Tag release: `git tag v0.2.0 -m "Phase 2: Shape Grammar Complete"`

---

## Phase 2 Validation Checklist (Verify Before Completion)

### Functional Requirements
- [ ] ✅ Can process TopologicPy graphs from GraphRAG (Phase 1 output)
- [ ] ✅ Adjacent rooms share boundaries (gap < 5cm tolerance)
- [ ] ✅ Non-adjacent rooms don't overlap (checked with COMPAS)
- [ ] ✅ Room areas within constraints (±10% tolerance)
- [ ] ✅ Works with 2-15 room layouts
- [ ] ✅ Converges in < 50 iterations for 10-room layout
- [ ] ✅ Runs in < 30 seconds for 10-room layout

### Quality Requirements
- [ ] ✅ 80%+ of generated layouts pass validation (no gaps/overlaps)
- [ ] ✅ Layouts are visually plausible (no weird angles, reasonable proportions)
- [ ] ✅ Can generate 10+ variations per graph
- [ ] ✅ Variations are diverse (not all identical)

### Code Quality Requirements
- [ ] ✅ All unit tests pass (`pytest tests/ -v`)
- [ ] ✅ Test coverage > 90% (`pytest --cov=src`)
- [ ] ✅ No linting errors (`flake8 src/`)
- [ ] ✅ Type hints on all public functions
- [ ] ✅ Docstrings on all public APIs (Google style)
- [ ] ✅ Example notebook runs without errors

### Documentation Requirements
- [ ] ✅ README.md with installation and quick start
- [ ] ✅ API documentation (Sphinx HTML)
- [ ] ✅ Complete example notebook (03_shape_grammar_complete.ipynb)
- [ ] ✅ Gallery of example outputs (20+ images)
- [ ] ✅ Known limitations documented in DEVELOPMENT_PLAN.md

---

## Phase 3 Preview: Next Steps

### 3D Extrusion (Future Actions)
- [ ] **Action 35**: Implement `layout_to_cells()` - Extrude 2D polygons to TopologicPy Cells
- [ ] **Action 36**: Implement `create_walls()` - Generate Faces for walls between rooms
- [ ] **Action 37**: Implement `add_apertures()` - Add doors on shared edges, windows on exterior
- [ ] **Action 38**: Implement `assemble_cellcomplex()` - Combine all Cells into single CellComplex
- [ ] **Action 39**: Implement `export_topologic_json()` - Export to TopologicPy JSON format
- [ ] **Action 40**: Test import in Grasshopper/Rhino

---

## Daily Development Workflow

```bash
# Start of work session
git pull origin main
source venv/bin/activate

# During development (after each action or small set of actions)
pytest tests/test_<module>.py -v  # Run tests for module you're working on
pytest --cov=src tests/           # Check overall coverage

# End of work session (or after completing each action)
git add .
git commit -m "Action X: Brief description"
git push origin main
```

## Progress Tracking

Track completion by checking off actions. Current status:

- **Module 1 (Actions 1-8)**: Shape Library Foundation — [ ] Not Started
- **Module 2 (Actions 9-13)**: Initial Layout — [ ] Not Started
- **Module 3 (Actions 14-18)**: Alignment — [ ] Not Started
- **Module 4 (Actions 19-23)**: Global Optimization — [ ] Not Started
- **Module 5 (Actions 24-28)**: Pipeline Integration — [ ] Not Started
- **Module 6 (Actions 29-34)**: Visualization & Polish — [ ] Not Started

**Phase 2 Complete**: [ ] All 34 actions completed and validated

---

**Last Updated**: 2025-10-23
**Version**: 1.0

---

## Phase 3: Shape Grammar Engine (NEW - 2025-12-29)

### Module 7: Core Data Structures (Week 1 - 5 days)

#### Action 35: LayoutState Foundation
- [ ] Create `src/grammar/core.py`
- [ ] Implement `Phase` enum (BUBBLE, RECTANGLES, ARRANGED, REFINED)
- [ ] Implement `EdgeType` enum (ADJACENCY, ALIGNMENT)
- [ ] Implement `Point` dataclass (x, y)
- [ ] Implement `Circle` dataclass (center, radius)
- [ ] Implement `Rectangle` dataclass (center, width, height, rotation)
- [ ] Write unit tests for all geometry classes

#### Action 36: Shape & LayoutState Classes
- [ ] Implement `Shape` dataclass (id, geometry, room_type, target_area, computed_area)
- [ ] Implement `LayoutEdge` dataclass (source_id, target_id, edge_type)
- [ ] Implement `LayoutState` dataclass (phase, shapes, edges, is_valid)
  - [ ] Methods: `add_shape()`, `add_edge()`, `validate()`, `bounds()`
- [ ] Write tests: create state, add shapes, validate
- [ ] Test serialization (to_dict, from_dict)

#### Action 37: Conversion Layer - LayoutState ↔ GraphShape
- [ ] Create `src/grammar/converters.py`
- [ ] Implement `layout_state_to_graphshape(state) -> GraphShape`
  - [ ] Convert Circle/Rectangle → TopologicPy Face
  - [ ] Create Cluster from faces
  - [ ] Create Graph from edges + centroids
- [ ] Implement `graphshape_to_layout_state(gs) -> LayoutState`
  - [ ] Extract faces → Rectangle geometry
  - [ ] Extract graph edges → LayoutEdge
- [ ] Test round-trip: LayoutState → GraphShape → LayoutState
- [ ] Verify geometry preservation (within tolerance)

#### Action 38: Bubble Diagram Integration
- [ ] Create `create_initial_state(circles: Dict, edges: List) -> LayoutState`
  - [ ] Convert CircleNode → Shape with Circle geometry
  - [ ] Convert edge list → LayoutEdge
  - [ ] Set phase = Phase.BUBBLE
- [ ] Test with Phase2_BubbleDiagram output
  - [ ] Load circles from `run_circle_packing()`
  - [ ] Create LayoutState
  - [ ] Verify all data preserved

#### Action 39: Visualization Integration Test
- [ ] Convert LayoutState (circles) → GraphShape
- [ ] Visualize with TopologicPy Plotly
  - [ ] `Plotly.Show(gs.cluster, gs.graph, renderer="notebook")`
  - [ ] Export to HTML: `renderer="browser", filepath="..."`
- [ ] Verify: circles render correctly, edges visible

---

### Module 8: Phase 1 Rules - Circle → Rectangle (Week 2 - 5 days)

#### Action 40: Rule Base Classes
- [ ] Create `src/grammar/rules.py`
- [ ] Implement `Match` dataclass (shape_ids, score, metadata)
- [ ] Implement `RuleResult` dataclass (success, modified_shapes, message)
- [ ] Implement `Rule` base class (abstract)
  - [ ] Properties: name, phase, priority
  - [ ] Methods: `match(state) -> List[Match]`, `apply(state, match) -> RuleResult`
  - [ ] Method: `can_apply(state) -> bool`

#### Action 41: Rule Registry
- [ ] Implement `RuleRegistry` class
  - [ ] Methods: `register(rule)`, `get_for_phase(phase)`, `get_all()`
  - [ ] Priority sorting
- [ ] Write tests: register rules, query by phase, priority order

#### Action 42: CircleToRectangle Rule Implementation
- [ ] Create `src/grammar/phase1_rules.py`
- [ ] Implement `get_default_aspect_ratio(room_type) -> float`
  - [ ] Living: 1.5, Bedroom: 1.3, Kitchen: 1.2, Bathroom: 1.0, etc.
- [ ] Implement `CircleToRectangleRule(Rule)`
  - [ ] `match()`: Find all Circle shapes
  - [ ] `apply()`: Convert to Rectangle preserving area
    - [ ] Compute width/height from area + aspect ratio
    - [ ] Center at circle center
    - [ ] Set rotation = 0
- [ ] Write tests:
  - [ ] Convert single circle → verify area preserved
  - [ ] Convert 10 circles → verify all converted
  - [ ] Test different room types → verify aspect ratios

#### Action 43: Engine Foundation
- [ ] Create `src/grammar/engine.py`
- [ ] Implement `EngineConfig` dataclass (max_iterations, tolerances, verbose)
- [ ] Implement `ExecutionResult` dataclass (success, final_state, iterations, rules_applied, validation_issues)
- [ ] Implement `ShapeGrammarEngine` class skeleton
  - [ ] `__init__(config)`: Setup registry, callbacks
  - [ ] `_setup_default_rules()`: Register Phase 1 rules
  - [ ] `register_rule(rule)`
  - [ ] `create_initial_state(circles, edges)`: Wrapper
  - [ ] `step(state) -> (bool, str)`: Apply single rule

#### Action 44: Phase 1 Execution & Testing
- [ ] Implement `_run_hybrid()` Phase 1 logic
  - [ ] Apply CircleToRectangle to all circles
  - [ ] Transition phase: BUBBLE → RECTANGLES
  - [ ] Validation check
- [ ] Test with mock data:
  - [ ] 3 circles → 3 rectangles
  - [ ] 10 circles → 10 rectangles
- [ ] Test with Phase2 bubble diagram output
  - [ ] Load circles from `run_circle_packing()`
  - [ ] Run Phase 1
  - [ ] Verify all rectangles, areas preserved
- [ ] Visualize:
  - [ ] Before: circles (Plotly)
  - [ ] After: rectangles (Plotly)
  - [ ] Export both to HTML

---

### Module 9: Phase 2 Rules - Rectangle Arrangement (Week 3 - 5 days)

#### Action 45: Edge Finding Algorithm
- [ ] Create `src/grammar/phase2_rules.py`
- [ ] Implement `find_closest_edges(rect_a: Rectangle, rect_b: Rectangle) -> (edge_a, edge_b)`
  - [ ] Get 4 edges of each rectangle
  - [ ] Compute pairwise distances (midpoint-to-midpoint)
  - [ ] Return closest pair
- [ ] Write tests:
  - [ ] Two horizontal rectangles → vertical edges closest
  - [ ] Rotated rectangles → verify correct edges found

#### Action 46: Alignment Computation
- [ ] Implement `compute_edge_angle(edge) -> float`
  - [ ] Return angle in degrees (0-360)
- [ ] Implement `compute_rotation_to_align(edge_a, edge_b) -> float`
  - [ ] Return rotation needed to make edges parallel
- [ ] Implement `compute_translation_to_align(edge_a, edge_b) -> Point`
  - [ ] Return offset to make edges collinear
- [ ] Write tests: verify angle/translation calculations

#### Action 47: AlignAdjacentRectangles Rule
- [ ] Implement `AlignAdjacentRectanglesRule(Rule)`
  - [ ] `match()`: Find pairs with adjacency edges
  - [ ] Scoring: closer pairs = higher score
  - [ ] `apply()`:
    - [ ] Find closest edges
    - [ ] Compute rotation
    - [ ] Rotate rect_b
    - [ ] Compute translation
    - [ ] Translate rect_b
    - [ ] Check overlap → separate if needed
- [ ] Write tests:
  - [ ] Align two random rectangles → verify shared edge
  - [ ] Test overlap detection → verify separation

#### Action 48: Overlap Detection & Resolution
- [ ] Implement `rectangles_overlap(rect_a, rect_b) -> bool`
  - [ ] Use SAT (Separating Axis Theorem) for rotated rects
  - [ ] Or convert to GraphShape → use TopologicPy Intersect()
- [ ] Implement `compute_separation_vector(rect_a, rect_b) -> Point`
  - [ ] Return vector to separate by min distance
- [ ] Write tests:
  - [ ] Overlapping rects → returns True
  - [ ] Touching rects → returns False
  - [ ] Test separation vector → verify correct direction

#### Action 49: Iterative Arrangement Engine
- [ ] Implement `_run_hybrid()` Phase 2 logic
  - [ ] Loop: apply AlignAdjacentRectangles
  - [ ] Priority: closest pairs first (score-based)
  - [ ] Convergence: no position changes > threshold
  - [ ] Max iterations: 100
- [ ] Test with 4-room graph (2×2 grid topology)
  - [ ] Verify all aligned
  - [ ] Measure iterations to convergence
- [ ] Test with 8-room graph (complex topology)
  - [ ] Verify final layout valid
  - [ ] Check overlaps, gaps

---

### Module 10: Refinement & Validation (Week 4 - 5 days)

#### Action 50: FillGapBetweenRectangles Rule
- [ ] Implement `compute_gap(rect_a, rect_b) -> float`
  - [ ] Distance between closest points on edges
- [ ] Implement `FillGapBetweenRectanglesRule(Rule)`
  - [ ] `match()`: Find pairs with gaps 0.01m - 0.5m
  - [ ] `apply()`: Translate rect_b to close gap
- [ ] Write tests:
  - [ ] Detect 0.2m gap → close to 0
  - [ ] Verify no overlap after closing

#### Action 51: Comprehensive Validation
- [ ] Implement `validate_layout_state(state) -> Dict[str, List[str]]`
  - [ ] Convert to GraphShape
  - [ ] Use `gs.find_overlaps()`
  - [ ] Use `gs.find_missing_adjacencies()`
  - [ ] Check area preservation (all shapes)
  - [ ] Return structured issues dict
- [ ] Write validation report formatter
  - [ ] Print human-readable summary
  - [ ] Export JSON report

#### Action 52: Metrics & Quality Scoring
- [ ] Implement `compute_layout_metrics(state) -> Dict`
  - [ ] Total area, avg room area
  - [ ] Overlap count, gap count
  - [ ] Alignment quality score
  - [ ] Compactness metric (bounding box ratio)
  - [ ] Aspect ratio stats (mean, std)
- [ ] Create metrics visualization
  - [ ] Bar charts for area distribution
  - [ ] Histogram for aspect ratios
  - [ ] Plotly dashboard

#### Action 53: End-to-End Testing
- [ ] Test suite: 1BR, 2BR, 3BR, 4BR apartments
  - [ ] Generate graphs from GraphRAG
  - [ ] Run bubble packing
  - [ ] Run shape grammar engine
  - [ ] Validate final layouts
- [ ] Success rate measurement
  - [ ] Count valid vs invalid layouts
  - [ ] Target: 80%+ success rate
- [ ] Performance benchmarking
  - [ ] 5 rooms: < 5s
  - [ ] 10 rooms: < 30s
  - [ ] 15 rooms: < 60s

#### Action 54: Failure Analysis
- [ ] Identify common failure modes
  - [ ] Document impossible topologies
  - [ ] Document convergence issues
- [ ] Create fallback strategies
  - [ ] Relaxed constraints for difficult cases
  - [ ] Manual intervention hooks
- [ ] Update known limitations in documentation

---

### Module 11: Visualization & Integration (Week 5 - 5 days)

#### Action 55: Step-by-Step Visualization
- [ ] Implement `visualize_transformation_steps(circles, edges, output_dir)`
  - [ ] Callback: save HTML after each rule application
  - [ ] Filename: `step_NNN_rulename.html`
  - [ ] Use TopologicPy Plotly with `renderer="browser"`
- [ ] Test: generate 50-step transformation
  - [ ] Verify all steps saved
  - [ ] Check HTML files render correctly

#### Action 56: Comparison Dashboards
- [ ] Implement `create_comparison_visualization(states: List[LayoutState])`
  - [ ] Side-by-side Plotly subplots
  - [ ] Shared axes for comparison
  - [ ] Metrics overlay (area, gaps, etc.)
- [ ] Create before/after comparison
  - [ ] Bubble diagram vs final layout
  - [ ] Export to single HTML file

#### Action 57: Variation Generator
- [ ] Implement `generate_layout_variations(circles, edges, n=10) -> List[LayoutState]`
  - [ ] Different random seeds for arrangement
  - [ ] Different aspect ratio distributions
  - [ ] Different alignment priorities
- [ ] Create variation gallery visualization
  - [ ] Grid of 10 layouts (2×5 or 3×4)
  - [ ] Plotly subplots
  - [ ] Export to `variations_gallery.html`

#### Action 58: GraphRAG Integration (End-to-End)
- [ ] Create `notebooks/Phase3_EndToEnd.ipynb`
  - [ ] Section 1: GraphRAG (Phase 1) → generate graph
  - [ ] Section 2: Bubble Diagram (Phase 2) → circle packing
  - [ ] Section 3: Shape Grammar (Phase 3) → transformation
  - [ ] Section 4: Visualization → Plotly renderings
  - [ ] Section 5: Export → save layouts
- [ ] Test with 5 apartment types
  - [ ] Studio, 1BR, 2BR, 3BR, 4BR
  - [ ] Generate and visualize all
  - [ ] Save gallery of results

#### Action 59: Documentation & Polish
- [ ] Update `README.md`
  - [ ] Add Phase 3 overview
  - [ ] Add code examples
  - [ ] Add gallery of example outputs
- [ ] Create `PHASE3_GUIDE.md`
  - [ ] Detailed API documentation
  - [ ] Usage examples
  - [ ] Troubleshooting guide
- [ ] Update `DEVELOPMENT_PLAN.md`
  - [ ] Mark Phase 3 complete
  - [ ] Outline Phase 4 (3D extrusion)

---

## Phase 3 Validation Checklist

### Functional Requirements
- [ ] ✅ Converts all circles to rectangles (100% success)
- [ ] ✅ Preserves area within 10% tolerance
- [ ] ✅ Aligns adjacent rectangles (shared edges within 0.5m)
- [ ] ✅ No overlaps in final layout
- [ ] ✅ Gaps < 0.5m between adjacent rooms
- [ ] ✅ Converges in < 100 iterations (10-room layout)

### Quality Requirements
- [ ] ✅ 80%+ layouts pass full validation
- [ ] ✅ Aspect ratios reasonable (1.0 - 2.0)
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
- [ ] ✅ No linting errors

---

**Phase 3 Progress**: 0/25 actions completed
**Estimated Duration**: 5 weeks
**Last Updated**: 2025-12-29
