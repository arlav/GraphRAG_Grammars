# GraphRAG + Shape Grammars: Detailed Development Plan

## Executive Summary

This system transforms **abstract spatial graphs** from the Swiss Dwelling Dataset into **concrete 3D building layouts** using a three-phase pipeline:

1. **Phase 1 (🔨 In Progress)**: GraphRAG generates new adjacency graphs using LLM + Kuzu graph database
2. **Phase 2 (📋 Planned)**: Shape grammar converts graphs to 2D geometric floor plans
3. **Phase 3 (📋 Planned)**: Topologic extrusion creates 3D models as Topologic JSON

## Complete Data Pipeline

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         INPUT: Swiss Dwelling Dataset                     │
│  JSON Format: {"vertices": {...}, "edges": {...}}                        │
│  Fields: node_name, roomtype, x, y, z, connectivity                      │
└──────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                PHASE 1: GraphRAG Generation (IN PROGRESS)                 │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │ 1. Load Swiss JSON → Kuzu graph database                          │  │
│  │ 2. Seed with "Entrance" node (copy props from best example)       │  │
│  │ 3. Iterative LLM loop:                                             │  │
│  │    - Query all graphs for candidate neighbors                     │  │
│  │    - LLM picks action: ADD node or CONNECT nodes                  │  │
│  │    - Copy properties from matching examples                       │  │
│  │ 4. Output: TopologicPy Graph object (nodes + edges, no geometry)  │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│  Technologies: Kuzu, TopologicPy, OpenAI API                             │
└──────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                     PHASE 2: Shape Grammar (PLANNED)                      │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │ INPUT: TopologicPy Graph (abstract topology)                      │  │
│  │                                                                    │  │
│  │ Step 2.1: Shape Assignment                                         │  │
│  │   - Map room labels → parametric shapes                           │  │
│  │   - Rectangles: Living (5×4m), Bedroom (3.5×3m), Bath (2×2.5m)   │  │
│  │   - L-shapes: Kitchen (often corner positions)                    │  │
│  │   - Polygons: Entrance/Hallway (adaptive)                         │  │
│  │                                                                    │  │
│  │ Step 2.2: Initial Layout (Force-Directed)                          │  │
│  │   - Compute positions using graph structure                       │  │
│  │   - Spring forces for edges, repulsion for non-adjacent           │  │
│  │   - Output: rough positioning (may have gaps/overlaps)            │  │
│  │                                                                    │  │
│  │ Step 2.3: Constraint Solving (Geometric Alignment)                 │  │
│  │   - For each edge: align shapes to share boundary                 │  │
│  │   - Find closest edges between adjacent rooms                     │  │
│  │   - Make them collinear + match lengths                           │  │
│  │   - Iterative refinement until convergence                        │  │
│  │                                                                    │  │
│  │ Step 2.4: Validation & Variation                                   │  │
│  │   - Check: no gaps, areas match constraints, plausible layout     │  │
│  │   - Generate N variations by sampling parameters                  │  │
│  │                                                                    │  │
│  │ OUTPUT: 2D Geometric Layout                                        │  │
│  │   - Polygons with coordinates (scikit-geometry Polygon objects)   │  │
│  │   - Room labels, areas, adjacencies preserved                     │  │
│  │   - Export formats: SVG, DXF, GeoJSON, matplotlib                 │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│  Technologies: scikit-geometry, COMPAS, SciPy, NetworkX                  │
└──────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                  PHASE 3: 3D Topologic Model (FUTURE)                     │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │ INPUT: 2D Layout (polygons + metadata)                            │  │
│  │                                                                    │  │
│  │ Step 3.1: Extrusion                                                │  │
│  │   - Extrude room polygons to height (e.g., 2.7m ceiling)          │  │
│  │   - Create TopologicPy Cells (3D volumes)                         │  │
│  │   - Attach room dictionaries to Cells                             │  │
│  │                                                                    │  │
│  │ Step 3.2: Walls, Doors, Windows                                    │  │
│  │   - Shared edges → Walls with Doors                               │  │
│  │   - Exterior edges → Walls with Windows                           │  │
│  │   - Create TopologicPy Faces for walls                            │  │
│  │   - Create Faces with apertures for openings                      │  │
│  │                                                                    │  │
│  │ Step 3.3: CellComplex Assembly                                     │  │
│  │   - Combine Cells into single CellComplex                         │  │
│  │   - Validate topology (manifold, watertight)                      │  │
│  │   - Attach building-level metadata                                │  │
│  │                                                                    │  │
│  │ OUTPUT: TopologicPy JSON                                           │  │
│  │   - Full 3D topological model (vertices, edges, faces, cells)     │  │
│  │   - Dictionaries at all levels (room data, door types, etc.)      │  │
│  │   - Compatible with TopologicPy ecosystem                         │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│  Technologies: TopologicPy, COMPAS (mesh ops), optional IFC export       │
└──────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                 ┌──────────────────────────────────┐
                 │  FINAL OUTPUT: Topologic JSON     │
                 │  - 3D building model              │
                 │  - Can be imported to Grasshopper │
                 │  - Can be visualized in Topology  │
                 │  - Suitable for further analysis  │
                 └──────────────────────────────────┘
```

---

## Phase 2 Deep Dive: Shape Grammar Implementation

### 2.1 Parametric Shape Library

#### Architecture

```python
# src/grammar/shapes.py

from pydantic import BaseModel, validator, Field
from typing import Tuple, List, Dict, Any
from enum import Enum

class RoomFunction(str, Enum):
    """Standard room classifications."""
    LIVING = "Living"
    DINING = "Dining"
    KITCHEN = "Kitchen"
    BEDROOM = "Bedroom"
    BATHROOM = "Bathroom"
    ENTRANCE = "Entrance"
    HALLWAY = "Hallway"
    STORAGE = "Storage"
    BALCONY = "Balcony"

class ShapeType(str, Enum):
    """Available shape primitives."""
    RECTANGLE = "rectangle"
    L_SHAPE = "l_shape"
    POLYGON = "polygon"

class BaseShape(BaseModel):
    """Base class for all parametric room shapes."""

    shape_type: ShapeType
    room_function: RoomFunction
    min_area: float = Field(gt=0, description="Minimum area in m²")
    max_area: float = Field(gt=0, description="Maximum area in m²")
    aspect_ratio_range: Tuple[float, float] = Field(
        default=(0.5, 2.0),
        description="(min, max) width/height ratio"
    )

    @validator('max_area')
    def validate_area_range(cls, v, values):
        if 'min_area' in values and v < values['min_area']:
            raise ValueError("max_area must be >= min_area")
        return v

    def generate_polygon(self, **kwargs):
        """Generate geometry. Implemented by subclasses."""
        raise NotImplementedError

    def validate_constraints(self, polygon) -> bool:
        """Check if generated polygon satisfies constraints."""
        raise NotImplementedError

class RectangularRoom(BaseShape):
    """Simple rectangular room shape."""

    shape_type: ShapeType = ShapeType.RECTANGLE
    width: float = Field(gt=0, description="Width in meters")
    height: float = Field(gt=0, description="Height in meters")

    @validator('width', 'height')
    def validate_dimensions(cls, v):
        if v < 1.5:
            raise ValueError("Minimum dimension is 1.5m (building codes)")
        return v

    def generate_polygon(self, anchor=(0.0, 0.0), rotation=0.0):
        """
        Generate rectangle at anchor point with optional rotation.

        Args:
            anchor: (x, y) tuple for bottom-left corner
            rotation: Rotation in degrees (0 = axis-aligned)

        Returns:
            Polygon2 from scikit-geometry
        """
        from skgeom import Point2, Polygon
        import numpy as np

        # Define corners (counter-clockwise)
        corners = np.array([
            [0, 0],
            [self.width, 0],
            [self.width, self.height],
            [0, self.height]
        ])

        # Apply rotation if needed
        if rotation != 0.0:
            angle = np.radians(rotation)
            rot_matrix = np.array([
                [np.cos(angle), -np.sin(angle)],
                [np.sin(angle), np.cos(angle)]
            ])
            corners = corners @ rot_matrix.T

        # Translate to anchor
        corners += np.array(anchor)

        # Convert to scikit-geometry
        points = [Point2(x, y) for x, y in corners]
        return Polygon(points)

    def validate_constraints(self, polygon) -> bool:
        """Check area and aspect ratio constraints."""
        area = abs(polygon.area())  # scikit-geometry returns signed area

        if not (self.min_area <= area <= self.max_area):
            return False

        aspect_ratio = self.width / self.height
        min_ar, max_ar = self.aspect_ratio_range
        return min_ar <= aspect_ratio <= max_ar

class LShapedRoom(BaseShape):
    """L-shaped room (common for kitchens in corners)."""

    shape_type: ShapeType = ShapeType.L_SHAPE

    # Define L-shape as two rectangles
    arm1_width: float = Field(gt=0)
    arm1_length: float = Field(gt=0)
    arm2_width: float = Field(gt=0)
    arm2_length: float = Field(gt=0)

    def generate_polygon(self, anchor=(0.0, 0.0), rotation=0.0):
        """
        Generate L-shape. Configuration:

          arm2_length
        ┌─────────┐
        │ Arm 2   │ arm2_width
        │       ┌─┘
        │       │ Arm 1 (arm1_width)
        │       │
        └───────┘
         arm1_length
        """
        from skgeom import Point2, Polygon
        import numpy as np

        # Define L-shape vertices (counter-clockwise)
        corners = np.array([
            [0, 0],
            [self.arm1_length, 0],
            [self.arm1_length, self.arm1_width],
            [self.arm2_length, self.arm1_width],
            [self.arm2_length, self.arm1_width + self.arm2_width],
            [0, self.arm1_width + self.arm2_width]
        ])

        # Apply rotation and translation (same as rectangle)
        if rotation != 0.0:
            angle = np.radians(rotation)
            rot_matrix = np.array([
                [np.cos(angle), -np.sin(angle)],
                [np.sin(angle), np.cos(angle)]
            ])
            corners = corners @ rot_matrix.T

        corners += np.array(anchor)
        points = [Point2(x, y) for x, y in corners]
        return Polygon(points)

    def validate_constraints(self, polygon) -> bool:
        area = abs(polygon.area())
        return self.min_area <= area <= self.max_area

# Shape assignment rules based on Swiss dwelling dataset patterns
SHAPE_DEFAULTS: Dict[RoomFunction, BaseShape] = {
    RoomFunction.LIVING: RectangularRoom(
        room_function=RoomFunction.LIVING,
        width=5.0, height=4.0,
        min_area=15.0, max_area=30.0,
        aspect_ratio_range=(0.6, 1.8)
    ),
    RoomFunction.KITCHEN: LShapedRoom(
        room_function=RoomFunction.KITCHEN,
        arm1_width=2.5, arm1_length=3.0,
        arm2_width=2.0, arm2_length=4.0,
        min_area=8.0, max_area=15.0
    ),
    RoomFunction.BEDROOM: RectangularRoom(
        room_function=RoomFunction.BEDROOM,
        width=3.5, height=3.0,
        min_area=9.0, max_area=20.0,  # Swiss building code: bedrooms ≥ 9m²
        aspect_ratio_range=(0.7, 1.5)
    ),
    RoomFunction.BATHROOM: RectangularRoom(
        room_function=RoomFunction.BATHROOM,
        width=2.0, height=2.5,
        min_area=3.5, max_area=8.0,
        aspect_ratio_range=(0.6, 1.4)
    ),
    RoomFunction.ENTRANCE: RectangularRoom(
        room_function=RoomFunction.ENTRANCE,
        width=1.8, height=2.0,
        min_area=2.0, max_area=6.0,
        aspect_ratio_range=(0.5, 2.0)
    ),
}

def assign_shape(room_label: str, props: Dict[str, Any]) -> BaseShape:
    """
    Assign a shape template to a room based on label and properties.

    Args:
        room_label: Room name from GraphRAG (e.g., "Living", "Kitchen")
        props: Dictionary with room metadata (may include area, dimensions)

    Returns:
        BaseShape instance with parameters tuned to this room
    """
    # Normalize label
    label_lower = room_label.lower()

    # Try to match room function
    for func in RoomFunction:
        if func.value.lower() in label_lower:
            shape = SHAPE_DEFAULTS.get(func)
            if shape:
                # TODO: Adjust dimensions based on props (e.g., actual area)
                return shape.copy(deep=True)

    # Default: rectangular with generic dimensions
    return RectangularRoom(
        room_function=RoomFunction.HALLWAY,
        width=3.0, height=3.0,
        min_area=5.0, max_area=15.0
    )
```

#### Testing Strategy

```python
# tests/test_shapes.py

import pytest
from src.grammar.shapes import RectangularRoom, LShapedRoom, assign_shape

def test_rectangular_room_creation():
    room = RectangularRoom(
        room_function="Living",
        width=5.0, height=4.0,
        min_area=15.0, max_area=30.0
    )
    polygon = room.generate_polygon()

    assert abs(polygon.area() - 20.0) < 0.01
    assert len(polygon.coords) == 4
    assert room.validate_constraints(polygon)

def test_rectangular_room_rotation():
    room = RectangularRoom(
        room_function="Bedroom",
        width=4.0, height=3.0,
        min_area=10.0, max_area=15.0
    )

    # Rotation should preserve area
    poly0 = room.generate_polygon(rotation=0)
    poly45 = room.generate_polygon(rotation=45)
    poly90 = room.generate_polygon(rotation=90)

    assert abs(poly0.area() - poly45.area()) < 0.01
    assert abs(poly0.area() - poly90.area()) < 0.01

def test_l_shaped_room():
    kitchen = LShapedRoom(
        room_function="Kitchen",
        arm1_width=2.5, arm1_length=3.0,
        arm2_width=2.0, arm2_length=4.0,
        min_area=8.0, max_area=15.0
    )
    polygon = kitchen.generate_polygon()

    # L-shape area = arm1_area + arm2_area - overlap
    expected_area = (3.0 * 2.5) + (4.0 * 2.0)
    assert abs(polygon.area() - expected_area) < 0.1
    assert len(polygon.coords) == 6  # L-shape has 6 vertices

def test_shape_assignment():
    # Test various room labels
    living_shape = assign_shape("Living Room", {})
    assert living_shape.room_function == "Living"
    assert living_shape.shape_type == "rectangle"

    kitchen_shape = assign_shape("Kitchen", {})
    assert kitchen_shape.room_function == "Kitchen"
    assert kitchen_shape.shape_type == "l_shape"

    # Unknown room type should get default
    unknown_shape = assign_shape("Mystery Room", {})
    assert unknown_shape.shape_type == "rectangle"
```

### 2.2 Constraint-Based Alignment

#### Core Algorithm

The challenge: Given a graph where edges represent "should be adjacent", position rectangular/polygonal shapes so that:
1. **Adjacent rooms share a common edge** (no gaps)
2. **Non-adjacent rooms don't overlap**
3. **Areas and aspect ratios stay within bounds**

**Approach: Iterative Constraint Satisfaction**

```python
# src/grammar/constraints.py

from typing import List, Tuple, Dict
from dataclasses import dataclass
import numpy as np
from skgeom import Point2, Segment2, Polygon
from scipy.optimize import minimize

@dataclass
class ShapeNode:
    """A room shape with position and geometry."""
    id: str
    label: str
    shape_template: BaseShape
    polygon: Polygon
    position: np.ndarray  # (x, y) anchor point
    rotation: float = 0.0  # degrees
    fixed: bool = False  # If True, don't move during optimization

@dataclass
class AdjacencyConstraint:
    """Constraint that two rooms should share an edge."""
    node_a: str
    node_b: str
    weight: float = 1.0  # Importance of this constraint

class LayoutOptimizer:
    """Optimize room positions to satisfy adjacency constraints."""

    def __init__(self, shapes: List[ShapeNode], constraints: List[AdjacencyConstraint]):
        self.shapes = {s.id: s for s in shapes}
        self.constraints = constraints

    def compute_initial_positions(self, graph) -> Dict[str, np.ndarray]:
        """
        Compute initial positions using force-directed layout.

        This gives a rough positioning based on graph structure.
        """
        import networkx as nx

        # Convert to NetworkX graph
        G = nx.Graph()
        for shape in self.shapes.values():
            G.add_node(shape.id)
        for constraint in self.constraints:
            G.add_edge(constraint.node_a, constraint.node_b, weight=constraint.weight)

        # Spring layout (scale by average shape size)
        avg_size = np.mean([s.shape_template.width for s in self.shapes.values()
                           if hasattr(s.shape_template, 'width')])
        positions = nx.spring_layout(G, k=avg_size*2, iterations=100)

        # Convert to our format
        return {node_id: np.array([pos[0]*10, pos[1]*10])
                for node_id, pos in positions.items()}

    def find_closest_edges(self, poly_a: Polygon, poly_b: Polygon) -> Tuple[Segment2, Segment2]:
        """
        Find the pair of edges (one from each polygon) that are closest.

        Returns:
            (edge_from_a, edge_from_b) as Segment2 objects
        """
        edges_a = list(poly_a.edges)
        edges_b = list(poly_b.edges)

        min_dist = float('inf')
        best_pair = None

        for ea in edges_a:
            for eb in edges_b:
                # Distance between edge midpoints (heuristic)
                mid_a = ea.source() + (ea.target() - ea.source()) * 0.5
                mid_b = eb.source() + (eb.target() - eb.source()) * 0.5
                dist = np.sqrt((mid_a.x() - mid_b.x())**2 + (mid_a.y() - mid_b.y())**2)

                if dist < min_dist:
                    min_dist = dist
                    best_pair = (ea, eb)

        return best_pair

    def align_edge_to_edge(self, shape_a: ShapeNode, shape_b: ShapeNode,
                          edge_a: Segment2, edge_b: Segment2) -> ShapeNode:
        """
        Translate and rotate shape_b so that edge_b aligns with edge_a.

        Returns:
            Updated shape_b with new position and rotation
        """
        # Get edge vectors
        vec_a = np.array([edge_a.target().x() - edge_a.source().x(),
                         edge_a.target().y() - edge_a.source().y()])
        vec_b = np.array([edge_b.target().x() - edge_b.source().x(),
                         edge_b.target().y() - edge_b.source().y()])

        # Compute rotation to align vec_b with vec_a
        angle_a = np.arctan2(vec_a[1], vec_a[0])
        angle_b = np.arctan2(vec_b[1], vec_b[0])
        rotation_needed = np.degrees(angle_a - angle_b)

        # Rotate shape_b
        new_rotation = shape_b.rotation + rotation_needed
        new_polygon = shape_b.shape_template.generate_polygon(
            anchor=shape_b.position,
            rotation=new_rotation
        )

        # Translate so edges coincide
        # TODO: Implement precise edge-to-edge translation

        return ShapeNode(
            id=shape_b.id,
            label=shape_b.label,
            shape_template=shape_b.shape_template,
            polygon=new_polygon,
            position=shape_b.position,  # Updated
            rotation=new_rotation,
            fixed=shape_b.fixed
        )

    def optimize(self, max_iterations=50) -> List[ShapeNode]:
        """
        Main optimization loop: iteratively adjust shapes to satisfy constraints.

        Algorithm:
        1. Initialize positions with force-directed layout
        2. For each constraint (room pair):
           a. Find closest edges
           b. Align them (rotate + translate)
           c. Adjust sizes if needed
        3. Repeat until convergence or max iterations
        """
        # Step 1: Initial positions
        initial_pos = self.compute_initial_positions(None)  # TODO: pass actual graph
        for node_id, pos in initial_pos.items():
            self.shapes[node_id].position = pos
            # Regenerate polygon at new position
            self.shapes[node_id].polygon = self.shapes[node_id].shape_template.generate_polygon(
                anchor=pos, rotation=self.shapes[node_id].rotation
            )

        # Step 2: Iterative refinement
        for iteration in range(max_iterations):
            print(f"Iteration {iteration+1}/{max_iterations}")

            changes_made = False

            for constraint in self.constraints:
                shape_a = self.shapes[constraint.node_a]
                shape_b = self.shapes[constraint.node_b]

                # Skip if both are fixed
                if shape_a.fixed and shape_b.fixed:
                    continue

                # Find closest edges
                edge_a, edge_b = self.find_closest_edges(shape_a.polygon, shape_b.polygon)

                # Align them (modify the non-fixed shape, or shape_b if both movable)
                if not shape_a.fixed:
                    # Move shape_a to align with shape_b
                    # (For simplicity, always move shape_b to shape_a)
                    pass

                if not shape_b.fixed:
                    updated_shape_b = self.align_edge_to_edge(shape_a, shape_b, edge_a, edge_b)

                    # Check if change is significant
                    pos_change = np.linalg.norm(updated_shape_b.position - shape_b.position)
                    if pos_change > 0.01:  # 1cm threshold
                        self.shapes[shape_b.id] = updated_shape_b
                        changes_made = True

            # Check convergence
            if not changes_made:
                print(f"Converged after {iteration+1} iterations")
                break

        return list(self.shapes.values())
```

#### COMPAS Integration for Complex Operations

```python
# src/geometry/compas_bridge.py

from compas.geometry import Polygon as CompasPolygon, Point as CompasPoint
from compas_cgal.booleans import boolean_union, boolean_intersection
from skgeom import Polygon as SkPolygon
from typing import List

def skgeom_to_compas(poly: SkPolygon) -> CompasPolygon:
    """Convert scikit-geometry Polygon to COMPAS Polygon."""
    points = [CompasPoint(p.x(), p.y(), 0.0) for p in poly.coords]
    return CompasPolygon(points)

def compas_to_skgeom(poly: CompasPolygon) -> SkPolygon:
    """Convert COMPAS Polygon to scikit-geometry Polygon."""
    from skgeom import Point2
    points = [Point2(p.x, p.y) for p in poly.points]
    return SkPolygon(points)

def check_overlap(poly_a: SkPolygon, poly_b: SkPolygon) -> bool:
    """
    Check if two polygons overlap using COMPAS boolean operations.

    Returns True if intersection area > 0.
    """
    compas_a = skgeom_to_compas(poly_a)
    compas_b = skgeom_to_compas(poly_b)

    try:
        intersection = boolean_intersection(compas_a, compas_b)
        # Check if intersection has area
        return intersection and len(intersection.points) > 0
    except Exception:
        return False

def merge_polygons(polygons: List[SkPolygon]) -> SkPolygon:
    """
    Merge multiple polygons into single outline using boolean union.

    Useful for creating building footprint from individual rooms.
    """
    if not polygons:
        return None

    compas_polys = [skgeom_to_compas(p) for p in polygons]
    union = compas_polys[0]

    for poly in compas_polys[1:]:
        union = boolean_union(union, poly)

    return compas_to_skgeom(union)
```

### 2.3 Graph-to-Shape Materializer

```python
# src/grammar/materializer.py

from topologicpy.Graph import Graph as TPGraph
from topologicpy.Vertex import Vertex as TPVertex
from topologicpy.Dictionary import Dictionary as TPDict
from topologicpy.Topology import Topology
from typing import List, Dict
import json

from src.grammar.shapes import assign_shape, ShapeNode
from src.grammar.constraints import LayoutOptimizer, AdjacencyConstraint

def graph_to_layout(topologic_graph: TPGraph) -> Dict:
    """
    Convert TopologicPy Graph (from GraphRAG) to 2D geometric layout.

    Pipeline:
    1. Extract nodes and edges from TopologicPy Graph
    2. Assign shape templates to each node
    3. Create initial ShapeNodes with rough positions
    4. Run constraint optimization
    5. Return layout as dict with polygons + metadata

    Args:
        topologic_graph: Output from GraphRAG (Phase 1)

    Returns:
        dict with structure:
        {
            'rooms': [
                {
                    'id': 'n0',
                    'label': 'Living',
                    'polygon': [[x0,y0], [x1,y1], ...],  # vertices
                    'area': 20.5,
                    'props': {...}  # original properties
                },
                ...
            ],
            'adjacencies': [
                {'a': 'n0', 'b': 'n1'},
                ...
            ]
        }
    """
    # Step 1: Extract graph data
    vertices = Graph.Vertices(topologic_graph)
    edges = Graph.Edges(topologic_graph)

    # Step 2: Create ShapeNodes
    shape_nodes = []
    for i, vertex in enumerate(vertices):
        # Get vertex dictionary
        vertex_dict = Topology.Dictionary(vertex)
        if vertex_dict:
            props = {
                k: TPDict.ValueAtKey(vertex_dict, k)
                for k in TPDict.Keys(vertex_dict)
            }
        else:
            props = {}

        # Extract label
        label = props.get('label') or props.get('roomtype') or f'room_{i}'

        # Assign shape template
        shape_template = assign_shape(label, props)

        # Create ShapeNode (initial position will be set by optimizer)
        node = ShapeNode(
            id=f'n{i}',
            label=label,
            shape_template=shape_template,
            polygon=None,  # Will be generated
            position=np.array([0.0, 0.0]),
            rotation=0.0,
            fixed=(i == 0)  # Fix first node as anchor
        )
        shape_nodes.append(node)

    # Step 3: Create adjacency constraints from edges
    constraints = []
    for edge in edges:
        start_v = Graph.StartVertex(edge)
        end_v = Graph.EndVertex(edge)

        # Find indices
        start_idx = vertices.index(start_v)
        end_idx = vertices.index(end_v)

        constraint = AdjacencyConstraint(
            node_a=f'n{start_idx}',
            node_b=f'n{end_idx}',
            weight=1.0
        )
        constraints.append(constraint)

    # Step 4: Optimize layout
    optimizer = LayoutOptimizer(shape_nodes, constraints)
    optimized_shapes = optimizer.optimize(max_iterations=50)

    # Step 5: Format output
    rooms = []
    for shape in optimized_shapes:
        polygon_coords = [
            [p.x(), p.y()] for p in shape.polygon.coords
        ]
        rooms.append({
            'id': shape.id,
            'label': shape.label,
            'polygon': polygon_coords,
            'area': abs(shape.polygon.area()),
            'props': {}  # TODO: Preserve original props
        })

    adjacencies = [
        {'a': c.node_a, 'b': c.node_b}
        for c in constraints
    ]

    return {
        'rooms': rooms,
        'adjacencies': adjacencies,
        'metadata': {
            'num_rooms': len(rooms),
            'total_area': sum(r['area'] for r in rooms),
            'source': 'graphrag_shape_grammar'
        }
    }
```

### 2.4 Visualization

```python
# src/utils/visualization.py

import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MPLPolygon
from matplotlib.collections import PatchCollection
import numpy as np

# Room type color mapping
ROOM_COLORS = {
    'Living': '#FFE5B4',    # Peach
    'Dining': '#FFDAB9',    # Peach puff
    'Kitchen': '#FFA07A',   # Light salmon
    'Bedroom': '#B0E0E6',   # Powder blue
    'Bathroom': '#ADD8E6',  # Light blue
    'Entrance': '#F0E68C',  # Khaki
    'Hallway': '#F5F5DC',   # Beige
}

def visualize_layout(layout: Dict, save_path: str = None, show=True):
    """
    Visualize 2D layout with matplotlib.

    Args:
        layout: Output from graph_to_layout()
        save_path: Optional path to save figure
        show: If True, display figure
    """
    fig, ax = plt.subplots(figsize=(12, 12))

    patches = []
    colors = []

    for room in layout['rooms']:
        # Create polygon patch
        vertices = np.array(room['polygon'])
        patch = MPLPolygon(vertices, closed=True)
        patches.append(patch)

        # Get color for room type
        color = ROOM_COLORS.get(room['label'], '#CCCCCC')
        colors.append(color)

        # Add label at centroid
        centroid = vertices.mean(axis=0)
        ax.text(centroid[0], centroid[1],
               f"{room['label']}\n{room['area']:.1f}m²",
               ha='center', va='center',
               fontsize=10, fontweight='bold')

    # Add patches to axes
    collection = PatchCollection(patches, facecolors=colors,
                                edgecolors='black', linewidths=2)
    ax.add_collection(collection)

    # Set equal aspect and auto-scale
    ax.set_aspect('equal')
    ax.autoscale()
    ax.grid(True, alpha=0.3)
    ax.set_xlabel('X (meters)')
    ax.set_ylabel('Y (meters)')
    ax.set_title(f"Floor Plan - {layout['metadata']['num_rooms']} rooms, " +
                f"{layout['metadata']['total_area']:.1f}m² total")

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')

    if show:
        plt.show()

    return fig, ax

def export_svg(layout: Dict, output_path: str):
    """Export layout to SVG format."""
    # TODO: Use svgwrite library
    pass

def export_dxf(layout: Dict, output_path: str):
    """Export layout to DXF format (AutoCAD)."""
    # TODO: Use ezdxf library
    pass
```

---

## Phase 3 Preview: 3D Topologic Model

```python
# src/topology/extrude_3d.py

from topologicpy.Cell import Cell
from topologicpy.Face import Face
from topologicpy.CellComplex import CellComplex
from typing import Dict, List

def layout_to_topologic_json(layout_2d: Dict, floor_height: float = 2.7) -> str:
    """
    Extrude 2D layout to 3D Topologic model.

    Steps:
    1. For each room polygon: extrude to Cell (height = floor_height)
    2. Find shared edges: create Faces with door apertures
    3. Find exterior edges: create Faces with window apertures
    4. Assemble into CellComplex
    5. Export to Topologic JSON

    Args:
        layout_2d: Output from graph_to_layout()
        floor_height: Ceiling height in meters

    Returns:
        JSON string in TopologicPy format
    """
    cells = []

    for room in layout_2d['rooms']:
        # Create Face from polygon
        from topologicpy.Vertex import Vertex
        from topologicpy.Wire import Wire
        from topologicpy.Face import Face

        vertices_2d = room['polygon']
        tp_vertices = [Vertex.ByCoordinates(x, y, 0) for x, y in vertices_2d]

        # Create wire (closed loop)
        wire = Wire.ByVertices(tp_vertices, close=True)
        base_face = Face.ByWire(wire)

        # Extrude to cell
        cell = Cell.ByThickenedFace(base_face, thickness=floor_height,
                                    bothSides=False)

        # Attach room metadata
        from topologicpy.Dictionary import Dictionary
        props = {
            'room_id': room['id'],
            'room_label': room['label'],
            'area': room['area'],
            'volume': room['area'] * floor_height
        }
        keys = list(props.keys())
        vals = list(props.values())
        cell_dict = Dictionary.ByKeysValues(keys, vals)
        cell = Topology.SetDictionary(cell, cell_dict)

        cells.append(cell)

    # TODO: Add doors/windows on shared/exterior edges
    # TODO: Assemble cells into CellComplex
    # TODO: Export to JSON

    cell_complex = CellComplex.ByCells(cells)

    # Export to JSON
    json_str = Topology.JSONString(cell_complex)
    return json_str
```

---

## Complete Implementation Roadmap

### Phase 2 Detailed Timeline (6 weeks)

#### Week 1: Shape Library Foundation
- [x] Understand Swiss dwelling dataset format
- [ ] Design Pydantic shape schema (`BaseShape`, `RectangularRoom`, `LShapedRoom`)
- [ ] Implement shape generation with scikit-geometry
- [ ] Create shape assignment rules (room type → shape template)
- [ ] Write unit tests (area, aspect ratio, rotation)
- [ ] Document API

**Deliverables**:
- `src/grammar/shapes.py` (200 lines)
- `tests/test_shapes.py` (150 lines)
- Example notebook: `notebooks/02a_shape_library_demo.ipynb`

#### Week 2: Constraint Solver - Part 1 (Initial Layout)
- [ ] Implement force-directed layout with NetworkX
- [ ] Create `ShapeNode` and `AdjacencyConstraint` dataclasses
- [ ] Build `LayoutOptimizer` skeleton
- [ ] Test with simple 2-3 room graphs
- [ ] Visualize initial positions (before alignment)

**Deliverables**:
- `src/grammar/constraints.py` (initial version, 150 lines)
- Test with rectangle-only layouts
- Visualization showing force-directed positions

#### Week 3: Constraint Solver - Part 2 (Alignment)
- [ ] Implement `find_closest_edges()` algorithm
- [ ] Implement `align_edge_to_edge()` with rotation
- [ ] Add translation to make edges collinear
- [ ] Test alignment on pairs of rectangles
- [ ] Handle edge length matching

**Deliverables**:
- Complete edge alignment algorithm
- Tests for 2-room adjacency (various orientations)
- Debug visualization showing before/after alignment

#### Week 4: Global Optimization & COMPAS Integration
- [ ] Implement iterative optimization loop
- [ ] Add convergence criteria
- [ ] Integrate COMPAS for overlap detection
- [ ] Add constraint relaxation (soft constraints)
- [ ] Test with 5-6 room layouts

**Deliverables**:
- Complete `LayoutOptimizer.optimize()` method
- `src/geometry/compas_bridge.py` (100 lines)
- Tests with complex topologies (star, chain, grid)

#### Week 5: Graph-to-Layout Pipeline
- [ ] Implement `graph_to_layout()` materializer
- [ ] Extract data from TopologicPy Graph
- [ ] Map GraphRAG output to ShapeNodes
- [ ] Run full pipeline: Graph → Layout
- [ ] Test with Phase 1 outputs (various apartment types)

**Deliverables**:
- `src/grammar/materializer.py` (200 lines)
- End-to-end test: Swiss JSON → GraphRAG → Layout
- Example outputs (5-10 generated layouts)

#### Week 6: Visualization & Export
- [ ] Implement matplotlib visualization
- [ ] Add room labels and area annotations
- [ ] Export to SVG (using `svgwrite`)
- [ ] Export to DXF (using `ezdxf`)
- [ ] Create variation generator (parameter sampling)
- [ ] Polish documentation and examples

**Deliverables**:
- `src/utils/visualization.py` (150 lines)
- Export functions for SVG, DXF
- Notebook: `notebooks/03_shape_grammar_complete.ipynb`
- 20+ example layouts from GraphRAG

---

## Success Metrics

### Phase 2 Complete When:

1. **Functional Requirements**:
   - ✅ Any TopologicPy Graph can be converted to 2D layout
   - ✅ Adjacent rooms share boundaries (gap < 5cm tolerance)
   - ✅ Non-adjacent rooms don't overlap
   - ✅ Room areas within ±10% of target
   - ✅ Can process 10-room layouts in <30 seconds

2. **Quality Requirements**:
   - ✅ Layouts are visually plausible (no weird angles, reasonable proportions)
   - ✅ 80% of generated layouts pass validation (no gaps/overlaps)
   - ✅ Can generate 10+ variations from one graph

3. **Technical Requirements**:
   - ✅ All unit tests pass (>90% coverage)
   - ✅ Code follows project style guidelines
   - ✅ Documented API with examples
   - ✅ Integration tests with Phase 1 outputs

---

## Technology Decisions

### Why scikit-geometry?
- **Pros**: Fast, precise 2D computational geometry, Polygon/Point primitives
- **Cons**: Limited documentation, C++ binding can be tricky
- **Alternative**: Shapely (more Pythonic, but slower)

### Why COMPAS?
- **Pros**: Architectural focus, excellent boolean operations via CGAL, good docs
- **Cons**: Heavier dependency, some overlap with scikit-geometry
- **Usage**: Complex operations (union, intersection), mesh generation

### Why NOT immediate 3D?
- **Reason**: 2D layout is already complex (constraint solving is NP-hard)
- **Strategy**: Validate 2D approach first, then extend to 3D
- **Benefit**: 2D layouts are useful on their own (floor plan generation)

---

## Next Steps

1. **Approve this plan** ← YOU ARE HERE
2. **Week 1: Start shape library implementation**
3. **Set up development environment** (install scikit-geometry, COMPAS)
4. **Create project structure** (src/, tests/, notebooks/)
5. **Begin coding** (TDD approach: tests first, then implementation)

---

## Questions for Clarification

1. **Swiss dwelling dataset access**: These are located here: /Users/td3003/import_export/msd_json)
2. **Building codes**: Should we enforce Swiss building regulations (min bedroom area, etc.) -No need
3. **Performance requirements**: How many rooms should we optimize for? (Currently targeting 10-15)
4. **Phase 3 priority**: How important is 3D output vs. perfecting 2D layouts? - Perfect 2d layouts first.
5. **Visualization**: Do you need real-time interactive viz (e.g., Streamlit) or static images OK? -Static images are ok initially. 

Let me know if you'd like me to adjust any part of this plan!
