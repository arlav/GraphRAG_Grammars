#!/usr/bin/env python3
"""
Comprehensive Test Suite for TopologicPy-Native Refactoring

Tests the new architecture:
- topologic_helpers functions
- Refactored GraphShape class
- Factory methods
- Validation using TopologicPy methods
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Test imports
print("=" * 70)
print("TEST SUITE: TopologicPy-Native Architecture")
print("=" * 70)
print()

# Track test results
tests_passed = 0
tests_total = 0

def test(name, condition, details=""):
    """Helper to track test results"""
    global tests_passed, tests_total
    tests_total += 1

    if condition:
        print(f"✅ Test {tests_total}: {name}")
        if details:
            print(f"   {details}")
        tests_passed += 1
        return True
    else:
        print(f"❌ Test {tests_total}: {name}")
        if details:
            print(f"   {details}")
        return False

# =============================================================================
# SECTION 1: Import Tests
# =============================================================================

print("SECTION 1: Import Tests")
print("-" * 70)

try:
    from topologicpy.Vertex import Vertex
    from topologicpy.Edge import Edge
    from topologicpy.Face import Face
    from topologicpy.Graph import Graph
    from topologicpy.Topology import Topology
    from topologicpy.Cluster import Cluster
    from topologicpy.Dictionary import Dictionary
    TOPOLOGIC_AVAILABLE = True
    test("TopologicPy imports", True, "All TopologicPy modules imported successfully")
except ImportError as e:
    TOPOLOGIC_AVAILABLE = False
    test("TopologicPy imports", False, f"ImportError: {e}")
    print("\n⚠️  Cannot continue tests without TopologicPy")
    sys.exit(1)

try:
    from grammar.topologic_helpers import (
        rectangular_face,
        square_face,
        get_metadata,
        set_metadata,
        face_area,
        face_centroid,
        faces_adjacent,
        faces_overlap,
        faces_bounding_box,
        graph_from_faces_and_adjacencies,
    )
    test("topologic_helpers imports", True, "All helper functions imported")
except ImportError as e:
    test("topologic_helpers imports", False, f"ImportError: {e}")
    sys.exit(1)

try:
    from grammar.rules import GraphShape
    test("GraphShape import", True, "GraphShape class imported")
except ImportError as e:
    test("GraphShape import", False, f"ImportError: {e}")
    sys.exit(1)

print()

# =============================================================================
# SECTION 2: topologic_helpers Tests
# =============================================================================

print("SECTION 2: topologic_helpers Function Tests")
print("-" * 70)

# Test 2.1: rectangular_face creation
face1 = rectangular_face(5, 4, origin=(0, 0), label="Room1")
test(
    "rectangular_face() creates Face",
    "Face" in str(type(face1)),  # Check type name, not isinstance (topologic_core vs wrapper)
    f"Type: {type(face1)}"
)

# Test 2.2: Metadata attachment
label = get_metadata(face1, "label")
width = get_metadata(face1, "width")
height = get_metadata(face1, "height")
test(
    "Metadata correctly attached",
    label == "Room1" and width == 5 and height == 4,
    f"label={label}, width={width}, height={height}"
)

# Test 2.3: face_area calculation
area = face_area(face1)
test(
    "face_area() calculates correctly",
    abs(area - 20.0) < 0.01,
    f"Expected 20.0, got {area:.2f}"
)

# Test 2.4: face_centroid
centroid = face_centroid(face1)
coords = Vertex.Coordinates(centroid)
test(
    "face_centroid() returns Vertex",
    "Vertex" in str(type(centroid)) and abs(coords[0] - 2.5) < 0.01 and abs(coords[1] - 2.0) < 0.01,
    f"Centroid at ({coords[0]:.1f}, {coords[1]:.1f})"
)

# Test 2.5: square_face
square1 = square_face(4, origin=(10, 10), label="Square1")
square_area = face_area(square1)
test(
    "square_face() creates square Face",
    abs(square_area - 16.0) < 0.01,
    f"Area: {square_area:.2f}"
)

# Test 2.6: faces_adjacent (should not be adjacent)
face2 = rectangular_face(3, 3, origin=(10, 10), label="Room2")
adjacent = faces_adjacent(face1, face2)
test(
    "faces_adjacent() detects non-adjacent",
    not adjacent,
    f"Room1 and Room2 should not be adjacent"
)

# Test 2.7: faces_adjacent (should be adjacent)
face3 = rectangular_face(3, 4, origin=(5, 0), label="Room3")
adjacent_true = faces_adjacent(face1, face3)
test(
    "faces_adjacent() detects adjacent",
    adjacent_true,
    f"Room1 and Room3 share edge"
)

# Test 2.8: faces_overlap (should not overlap)
overlaps = faces_overlap(face1, face2)
test(
    "faces_overlap() detects non-overlapping",
    not overlaps,
    f"Room1 and Room2 do not overlap"
)

# Test 2.9: faces_bounding_box
bbox = faces_bounding_box([face1, face2, face3])
expected_bbox = (0, 0, 13, 13)  # Room1: (0,0)-(5,4), Room2: (10,10)-(13,13), Room3: (5,0)-(8,4)
test(
    "faces_bounding_box() calculates correctly",
    bbox[0] == 0 and bbox[1] == 0 and bbox[2] == 13 and bbox[3] == 13,
    f"BBox: {bbox}"
)

print()

# =============================================================================
# SECTION 3: GraphShape Tests
# =============================================================================

print("SECTION 3: GraphShape Class Tests")
print("-" * 70)

# Test 3.1: GraphShape.from_faces_and_adjacencies
test_faces = [
    rectangular_face(5, 4, origin=(0, 0), label="A"),
    rectangular_face(5, 4, origin=(5, 0), label="B"),
    rectangular_face(5, 4, origin=(10, 0), label="C"),
]
test_adjacencies = [("A", "B"), ("B", "C")]

gs = GraphShape.from_faces_and_adjacencies(test_faces, test_adjacencies)

test(
    "GraphShape.from_faces_and_adjacencies() creates instance",
    isinstance(gs, GraphShape),
    f"Type: {type(gs)}"
)

# Test 3.2: GraphShape has TopologicPy types
test(
    "GraphShape.cluster is Cluster",
    "Cluster" in str(type(gs.cluster)),
    f"Type: {type(gs.cluster)}"
)

test(
    "GraphShape.graph is Graph",
    "Graph" in str(type(gs.graph)),
    f"Type: {type(gs.graph)}"
)

# Test 3.3: GraphShape.num_nodes()
num_nodes = gs.num_nodes()
test(
    "GraphShape.num_nodes() returns correct count",
    num_nodes == 3,
    f"Expected 3, got {num_nodes}"
)

# Test 3.4: GraphShape.num_edges()
num_edges = gs.num_edges()
test(
    "GraphShape.num_edges() returns correct count",
    num_edges == 2,
    f"Expected 2, got {num_edges}"
)

# Test 3.5: GraphShape.total_area()
total_area = gs.total_area()
test(
    "GraphShape.total_area() sums correctly",
    abs(total_area - 60.0) < 0.01,
    f"Expected 60.0, got {total_area:.2f}"
)

# Test 3.6: GraphShape.bounding_box()
bbox = gs.bounding_box()
test(
    "GraphShape.bounding_box() calculates correctly",
    bbox == (0, 0, 15, 4),
    f"Expected (0, 0, 15, 4), got {bbox}"
)

# Test 3.7: GraphShape.get_face_by_label()
face_a = gs.get_face_by_label("A")
test(
    "GraphShape.get_face_by_label() retrieves Face",
    face_a is not None and get_metadata(face_a, "label") == "A",
    f"Retrieved face with label 'A'"
)

# Test 3.8: GraphShape.get_neighbors()
neighbors_b = gs.get_neighbors("B")
test(
    "GraphShape.get_neighbors() returns correct neighbors",
    set(neighbors_b) == {"A", "C"},
    f"B's neighbors: {neighbors_b}"
)

# Test 3.9: GraphShape.degree()
degree_b = gs.degree("B")
test(
    "GraphShape.degree() returns correct degree",
    degree_b == 2,
    f"B's degree: {degree_b}"
)

print()

# =============================================================================
# SECTION 4: Validation Tests
# =============================================================================

print("SECTION 4: Validation Tests")
print("-" * 70)

# Test 4.1: find_overlaps (no overlaps)
overlaps = gs.find_overlaps()
test(
    "GraphShape.find_overlaps() detects no overlaps",
    len(overlaps) == 0,
    f"Found {len(overlaps)} overlaps"
)

# Test 4.2: find_missing_adjacencies (no missing)
missing = gs.find_missing_adjacencies()
test(
    "GraphShape.find_missing_adjacencies() finds none",
    len(missing) == 0,
    f"Found {len(missing)} missing adjacencies"
)

# Test 4.3: validate (should be valid)
is_valid, issues = gs.validate()
test(
    "GraphShape.validate() returns valid",
    is_valid and len(issues) == 0,
    f"Valid: {is_valid}, Issues: {len(issues)}"
)

# Test 4.4: Create invalid GraphShape (overlapping faces)
invalid_faces = [
    rectangular_face(10, 10, origin=(0, 0), label="X"),
    rectangular_face(5, 5, origin=(2, 2), label="Y"),  # Overlaps with X
]
invalid_adjacencies = [("X", "Y")]
gs_invalid = GraphShape.from_faces_and_adjacencies(invalid_faces, invalid_adjacencies)

overlaps_invalid = gs_invalid.find_overlaps()
test(
    "GraphShape.find_overlaps() detects overlaps",
    len(overlaps_invalid) > 0,
    f"Found {len(overlaps_invalid)} overlaps"
)

print()

# =============================================================================
# SECTION 5: Factory Method Tests
# =============================================================================

print("SECTION 5: Factory Method Tests")
print("-" * 70)

# Test 5.1: from_grid
gs_grid = GraphShape.from_grid(20, 15, rows=2, cols=3)

test(
    "GraphShape.from_grid() creates correct grid",
    gs_grid.num_nodes() == 6 and gs_grid.num_edges() == 7,
    f"Nodes: {gs_grid.num_nodes()}, Edges: {gs_grid.num_edges()}"
)

# Test 5.2: Grid area conservation
grid_area = gs_grid.total_area()
test(
    "from_grid() conserves area",
    abs(grid_area - 300.0) < 0.01,
    f"Expected 300.0, got {grid_area:.2f}"
)

# Test 5.3: Grid has no overlaps
grid_overlaps = gs_grid.find_overlaps()
test(
    "from_grid() creates non-overlapping cells",
    len(grid_overlaps) == 0,
    f"Overlaps: {len(grid_overlaps)}"
)

# Test 5.4: from_horizontal_split
gs_split = GraphShape.from_horizontal_split(
    30, 10,
    ratios=[0.3, 0.4, 0.3],
    labels=["Left", "Middle", "Right"]
)

test(
    "GraphShape.from_horizontal_split() creates correct split",
    gs_split.num_nodes() == 3 and gs_split.num_edges() == 2,
    f"Nodes: {gs_split.num_nodes()}, Edges: {gs_split.num_edges()}"
)

# Test 5.5: Split area conservation
split_area = gs_split.total_area()
test(
    "from_horizontal_split() conserves area",
    abs(split_area - 300.0) < 0.01,
    f"Expected 300.0, got {split_area:.2f}"
)

# Test 5.6: Split creates linear topology (2 endpoints)
degrees_split = [gs_split.degree(get_metadata(f, "label")) for f in gs_split.faces()]
endpoints = [d for d in degrees_split if d == 1]
test(
    "from_horizontal_split() creates linear topology",
    len(endpoints) == 2,
    f"Endpoints: {len(endpoints)}"
)

print()

# =============================================================================
# SECTION 6: Graph Construction Tests
# =============================================================================

print("SECTION 6: Graph Construction Tests")
print("-" * 70)

# Test 6.1: graph_from_faces_and_adjacencies
graph_faces = [
    rectangular_face(4, 4, origin=(0, 0), label="Node1"),
    rectangular_face(4, 4, origin=(4, 0), label="Node2"),
]
graph_adjacencies = [("Node1", "Node2")]

topo_graph = graph_from_faces_and_adjacencies(graph_faces, graph_adjacencies)

test(
    "graph_from_faces_and_adjacencies() creates Graph",
    "Graph" in str(type(topo_graph)),
    f"Type: {type(topo_graph)}"
)

# Test 6.2: Graph has correct vertex count
vertices = Graph.Vertices(topo_graph)
test(
    "Graph has correct number of vertices",
    len(vertices) == 2,
    f"Vertices: {len(vertices)}"
)

# Test 6.3: Graph has correct edge count
edges = Graph.Edges(topo_graph)
test(
    "Graph has correct number of edges",
    len(edges) == 1,
    f"Edges: {len(edges)}"
)

# Test 6.4: Graph vertices have metadata
vertex1 = vertices[0]
v_label = get_metadata(vertex1, "label")
test(
    "Graph vertices have metadata",
    v_label in ["Node1", "Node2"],
    f"Vertex label: {v_label}"
)

print()

# =============================================================================
# SECTION 7: Type Verification Tests
# =============================================================================

print("SECTION 7: Type Verification (TopologicPy Native)")
print("-" * 70)

# Test 7.1: All faces are TopologicPy Face objects
all_faces_correct = all("Face" in str(type(f)) for f in gs.faces())
test(
    "All GraphShape faces are TopologicPy Face objects",
    all_faces_correct,
    f"Checked {len(gs.faces())} faces"
)

# Test 7.2: All vertices are TopologicPy Vertex objects
all_vertices_correct = all("Vertex" in str(type(v)) for v in gs.vertices())
test(
    "All GraphShape vertices are TopologicPy Vertex objects",
    all_vertices_correct,
    f"Checked {len(gs.vertices())} vertices"
)

# Test 7.3: All edges are TopologicPy Edge objects
all_edges_correct = all("Edge" in str(type(e)) for e in gs.edges())
test(
    "All GraphShape edges are TopologicPy Edge objects",
    all_edges_correct,
    f"Checked {len(gs.edges())} edges"
)

# Test 7.4: Cluster is TopologicPy Cluster
test(
    "GraphShape.cluster is TopologicPy Cluster",
    "Cluster" in str(type(gs.cluster)),
    f"Type: {type(gs.cluster).__name__}"
)

# Test 7.5: Graph is TopologicPy Graph
test(
    "GraphShape.graph is TopologicPy Graph",
    "Graph" in str(type(gs.graph)),
    f"Type: {type(gs.graph).__name__}"
)

print()

# =============================================================================
# FINAL RESULTS
# =============================================================================

print("=" * 70)
print(f"FINAL RESULTS: {tests_passed}/{tests_total} tests passed")
print("=" * 70)

if tests_passed == tests_total:
    print("🎉 ALL TESTS PASSED!")
    print("✅ TopologicPy-native architecture is working correctly")
    print()
    print("Key achievements:")
    print("  • All geometry as TopologicPy Face objects")
    print("  • All topology as TopologicPy Graph objects")
    print("  • Metadata in TopologicPy Dictionary")
    print("  • No conversion layer needed")
    print("  • Validation uses TopologicPy methods")
    sys.exit(0)
else:
    print(f"⚠️  {tests_total - tests_passed} test(s) failed")
    print("Please review the failed tests above")
    sys.exit(1)
