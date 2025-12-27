"""
Graph + Shape Transformation Rules

This module implements the core idea:
    Graph transformation → Shape transformation

Every rule transforms BOTH the graph topology AND the geometric shapes
simultaneously, maintaining consistency between the two representations.

Philosophy:
- Graph and shapes are dual representations of the same configuration
- Transformations are bidirectional (can be composed, reversed)
- Rules are pure functions (no side effects)
- TopologicPy primitives throughout (Cluster + Graph)

ARCHITECTURE (REFACTORED):
- Uses TopologicPy Cluster (for Face geometries)
- Uses TopologicPy Graph (for topology - vertices at centroids, edges for adjacencies)
- No custom Rectangle classes - all geometry is Face objects
- All metadata in TopologicPy Dictionary objects
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Tuple, Dict, Callable, Optional, Any
from dataclasses import dataclass, field

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
    set_metadata,
    get_all_metadata,
    face_centroid,
    faces_adjacent,
    faces_overlap,
    face_area,
    faces_bounding_box,
    graph_from_faces_and_adjacencies,
    vertex_coordinates,
)


# =============================================================================
# GRAPH-SHAPE DUAL REPRESENTATION
# =============================================================================

class GraphShape(BaseModel):
    """
    Dual representation: topology (graph) + geometry (shapes).

    This is the fundamental data structure in our grammar system.
    Every configuration has BOTH a graph and shapes, which must stay consistent.

    REFACTORED ARCHITECTURE:
    - cluster: Cluster of Face objects (room geometries)
    - graph: Graph with vertices at room centroids, edges for adjacencies

    All geometry is stored as TopologicPy Faces, all topology as TopologicPy Graph.
    No custom classes, no networkx dependency.

    Attributes:
        cluster: Cluster of Faces (room geometries)
        graph: Graph connecting room centroids (topology)

    Invariants:
        - Every graph vertex has metadata with 'label' key matching a Face
        - Adjacent vertices in graph should have adjacent Faces (share boundary)
        - No overlapping Faces (except possibly at boundaries)

    Examples:
        >>> # Create 2x2 grid
        >>> faces = [
        ...     rectangular_face(5, 5, origin=(0, 0), label="n0"),
        ...     rectangular_face(5, 5, origin=(5, 0), label="n1"),
        ...     rectangular_face(5, 5, origin=(0, 5), label="n2"),
        ...     rectangular_face(5, 5, origin=(5, 5), label="n3"),
        ... ]
        >>> adjacencies = [("n0", "n1"), ("n0", "n2"), ("n1", "n3"), ("n2", "n3")]
        >>> gs = GraphShape.from_faces_and_adjacencies(faces, adjacencies)
        >>> gs.total_area()
        100.0
    """

    cluster: Any  # TopologicPy Cluster (from topologic_core)
    graph: Any    # TopologicPy Graph (from topologic_core)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    # -------------------------------------------------------------------------
    # Basic Queries
    # -------------------------------------------------------------------------

    def faces(self) -> List[Face]:
        """Get all faces from cluster."""
        return Cluster.Faces(self.cluster)

    def vertices(self) -> List[Vertex]:
        """Get all graph vertices (at room centroids)."""
        return Graph.Vertices(self.graph)

    def edges(self) -> List[Edge]:
        """Get all graph edges (room adjacencies)."""
        return Graph.Edges(self.graph)

    def num_nodes(self) -> int:
        """Number of nodes (faces)."""
        return len(self.faces())

    def num_edges(self) -> int:
        """Number of edges (adjacencies)."""
        return len(self.edges())

    def total_area(self) -> float:
        """Total area of all shapes."""
        return sum(face_area(f) for f in self.faces())

    def bounding_box(self) -> Tuple[float, float, float, float]:
        """
        Calculate bounding box containing all shapes.

        Returns:
            (min_x, min_y, max_x, max_y)
        """
        return faces_bounding_box(self.faces())

    def get_face_by_label(self, label: str) -> Optional[Face]:
        """Get Face by its label metadata."""
        for face in self.faces():
            if get_metadata(face, "label") == label:
                return face
        return None

    def get_vertex_by_label(self, label: str) -> Optional[Vertex]:
        """Get graph Vertex by its label metadata."""
        for vertex in self.vertices():
            if get_metadata(vertex, "label") == label:
                return vertex
        return None

    def get_neighbors(self, label: str) -> List[str]:
        """
        Get all node labels adjacent to given node.

        Args:
            label: Node label

        Returns:
            List of neighbor labels
        """
        vertex = self.get_vertex_by_label(label)
        if not vertex:
            return []

        neighbors = []
        for edge in self.edges():
            edge_verts = Edge.Vertices(edge)
            if len(edge_verts) != 2:
                continue

            v1, v2 = edge_verts
            label1 = get_metadata(v1, "label")
            label2 = get_metadata(v2, "label")

            if label1 == label:
                neighbors.append(label2)
            elif label2 == label:
                neighbors.append(label1)

        return neighbors

    def degree(self, label: str) -> int:
        """Degree of node (number of neighbors)."""
        return len(self.get_neighbors(label))

    # -------------------------------------------------------------------------
    # Validation
    # -------------------------------------------------------------------------

    def find_overlaps(self, tolerance: float = 0.01) -> List[Tuple[str, str]]:
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

    def find_missing_adjacencies(self, tolerance: float = 0.01) -> List[Tuple[str, str]]:
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

    def validate(self, tolerance: float = 0.01) -> Tuple[bool, List[str]]:
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
            face1 = self.get_face_by_label(label1)
            face2 = self.get_face_by_label(label2)

            if face1 and face2:
                if not faces_adjacent(face1, face2, tolerance):
                    issues.append(f"Graph edge without geometric adjacency: {label1} ↔ {label2}")

        return (len(issues) == 0, issues)

    # -------------------------------------------------------------------------
    # Factory Methods
    # -------------------------------------------------------------------------

    @classmethod
    def from_faces_and_adjacencies(
        cls,
        faces: List[Face],
        adjacencies: List[Tuple[str, str]]
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
        origin: Tuple[float, float] = (0.0, 0.0)
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
                label = f"cell_{r}_{c}"

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
                    adjacencies.append((label, f"cell_{r}_{c-1}"))
                if r > 0:  # Bottom neighbor
                    adjacencies.append((label, f"cell_{r-1}_{c}"))

        return cls.from_faces_and_adjacencies(faces, adjacencies)

    @classmethod
    def from_horizontal_split(
        cls,
        base_width: float,
        base_height: float,
        ratios: List[float],
        labels: Optional[List[str]] = None,
        origin: Tuple[float, float] = (0.0, 0.0)
    ) -> "GraphShape":
        """
        Create GraphShape from horizontal subdivision.

        Splits a rectangle horizontally into sections with linear topology.

        Args:
            base_width: Width of base rectangle
            base_height: Height of base rectangle
            ratios: Width ratios for each section (must sum to ~1.0)
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

        if len(labels) != len(ratios):
            raise ValueError("Number of labels must match number of ratios")

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


# =============================================================================
# TRANSFORMATION RULES (To be implemented in future notebooks)
# =============================================================================

@dataclass
class GraphShapeRule:
    """
    A rule that transforms both graph and shapes simultaneously.

    A rule consists of:
    - name: Human-readable identifier
    - description: What the rule does
    - pattern: Function that checks if rule can be applied to a node
    - transform: Function that applies the transformation

    Examples:
        >>> rule = RuleLibrary.split_horizontal()
        >>> # Apply to node 'n0' in graphshape
        >>> new_gs = rule.apply(graphshape, 'n0')

    Note: Transformation rules will be implemented using TopologicPy Face
    subdivision methods in future notebooks.
    """
    name: str
    description: str
    pattern: Callable[[GraphShape, str], bool]
    transform: Callable[[GraphShape, str, Dict], GraphShape]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def can_apply(self, gs: GraphShape, node_label: str) -> bool:
        """Check if rule can be applied to given node."""
        if not gs.get_face_by_label(node_label):
            return False
        return self.pattern(gs, node_label)

    def apply(self, gs: GraphShape, node_label: str, **params) -> GraphShape:
        """
        Apply transformation to given node.

        Args:
            gs: GraphShape to transform
            node_label: Target node label to transform
            **params: Rule-specific parameters (e.g., ratio=0.5)

        Returns:
            New GraphShape after transformation
        """
        if not self.can_apply(gs, node_label):
            raise ValueError(
                f"Rule '{self.name}' cannot be applied to node '{node_label}'. "
                f"Pattern check failed."
            )

        return self.transform(gs, node_label, params)


class RuleLibrary:
    """
    Collection of standard graph-shape transformation rules.

    All rules follow the pattern:
    1. Graph transformation (add/remove/merge nodes and edges)
    2. Shape transformation (subdivide/merge/adjust Faces)
    3. Maintain consistency (graph structure = shape adjacency)

    Note: Rule implementations will be added in future notebooks.
    They will use TopologicPy Face methods for geometric operations.
    """

    @staticmethod
    def split_horizontal(default_ratio: float = 0.5) -> GraphShapeRule:
        """
        Split a node horizontally (left | right).

        Graph transformation:
            n0 → n0_L + n0_R
            Add edge: (n0_L, n0_R)
            Reconnect neighbors: each neighbor connects to BOTH new nodes

        Shape transformation:
            Face → split horizontally using TopologicPy methods

        Args:
            default_ratio: Default split position (0 < ratio < 1)

        Note: Full implementation requires TopologicPy Face splitting methods.
        To be implemented in future notebooks.
        """
        def pattern(gs: GraphShape, node_label: str) -> bool:
            # Can split any node
            return True

        def transform(gs: GraphShape, node_label: str, params: Dict) -> GraphShape:
            # TODO: Implement using TopologicPy Face splitting
            raise NotImplementedError(
                "Rule transformations to be implemented in future notebooks "
                "using TopologicPy Face subdivision methods"
            )

        return GraphShapeRule(
            name=f"split_horizontal_{default_ratio}",
            description=f"Split node horizontally at ratio {default_ratio}",
            pattern=pattern,
            transform=transform,
            metadata={'type': 'subdivision', 'direction': 'horizontal'}
        )


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def apply_rule_to_all_nodes(gs: GraphShape, rule: GraphShapeRule, **params) -> GraphShape:
    """
    Apply rule to all nodes in graph.

    Useful for batch transformations like "split all rooms horizontally".
    """
    current = gs
    all_labels = [get_metadata(f, "label") for f in gs.faces()]

    for label in all_labels:
        if label and rule.can_apply(current, label):
            current = rule.apply(current, label, **params)

    return current


def find_applicable_nodes(gs: GraphShape, rule: GraphShapeRule) -> List[str]:
    """Find all node labels where rule can be applied."""
    applicable = []

    for face in gs.faces():
        label = get_metadata(face, "label")
        if label and rule.can_apply(gs, label):
            applicable.append(label)

    return applicable
