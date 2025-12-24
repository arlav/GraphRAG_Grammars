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
- Immutable data structures (functional approach)
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Callable, Optional, Any
from collections import deque
import networkx as nx

from .shapes import Rectangle, Point, merge_rectangles_bounding_box


# =============================================================================
# GRAPH-SHAPE DUAL REPRESENTATION
# =============================================================================

@dataclass
class GraphShape:
    """
    Dual representation: topology (graph) + geometry (shapes).

    This is the fundamental data structure in our grammar system.
    Every configuration has BOTH a graph and shapes, which must stay consistent.

    Attributes:
        shapes: Dictionary mapping node_id → Rectangle
        edges: List of (node_id_a, node_id_b) tuples representing adjacencies
        metadata: Optional global metadata

    Invariants:
        - Every node in edges must have a corresponding shape
        - Adjacent nodes in graph should have adjacent shapes (share boundary)
        - No overlapping shapes (except possibly at boundaries)

    Examples:
        >>> # 2x2 grid
        >>> shapes = {
        ...     'n0': Rectangle(5, 5, Point(0, 0)),
        ...     'n1': Rectangle(5, 5, Point(5, 0)),
        ...     'n2': Rectangle(5, 5, Point(0, 5)),
        ...     'n3': Rectangle(5, 5, Point(5, 5))
        ... }
        >>> edges = [('n0', 'n1'), ('n0', 'n2'), ('n1', 'n3'), ('n2', 'n3')]
        >>> gs = GraphShape(shapes, edges)
        >>> gs.num_nodes()
        4
        >>> gs.total_area()
        100.0
    """
    shapes: Dict[str, Rectangle]
    edges: List[Tuple[str, str]]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate consistency."""
        # Check all edges reference existing nodes
        all_nodes = set(self.shapes.keys())
        for a, b in self.edges:
            if a not in all_nodes:
                raise ValueError(f"Edge references non-existent node: {a}")
            if b not in all_nodes:
                raise ValueError(f"Edge references non-existent node: {b}")

    # -------------------------------------------------------------------------
    # Basic Queries
    # -------------------------------------------------------------------------

    def num_nodes(self) -> int:
        """Number of nodes (shapes)."""
        return len(self.shapes)

    def num_edges(self) -> int:
        """Number of edges (adjacencies)."""
        return len(self.edges)

    def total_area(self) -> float:
        """Total area of all shapes."""
        return sum(rect.area() for rect in self.shapes.values())

    def get_neighbors(self, node_id: str) -> List[str]:
        """Get all nodes adjacent to given node."""
        neighbors = []
        for a, b in self.edges:
            if a == node_id:
                neighbors.append(b)
            elif b == node_id:
                neighbors.append(a)
        return neighbors

    def degree(self, node_id: str) -> int:
        """Degree of node (number of neighbors)."""
        return len(self.get_neighbors(node_id))

    def is_connected(self) -> bool:
        """Check if graph is connected (all nodes reachable from any node)."""
        if not self.shapes:
            return True

        # BFS from first node
        visited = set()
        queue = deque([next(iter(self.shapes.keys()))])
        visited.add(queue[0])

        while queue:
            current = queue.popleft()
            for neighbor in self.get_neighbors(current):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)

        return len(visited) == self.num_nodes()

    # -------------------------------------------------------------------------
    # NetworkX Integration
    # -------------------------------------------------------------------------

    def to_networkx(self) -> nx.Graph:
        """
        Convert to NetworkX graph for analysis.

        Adds node attributes: pos (centroid), width, height, area
        """
        G = nx.Graph()

        for node_id, rect in self.shapes.items():
            centroid = rect.centroid()
            G.add_node(
                node_id,
                pos=(centroid.x, centroid.y),
                width=rect.width,
                height=rect.height,
                area=rect.area(),
                **rect.metadata
            )

        for a, b in self.edges:
            G.add_edge(a, b)

        return G

    # -------------------------------------------------------------------------
    # Validation
    # -------------------------------------------------------------------------

    def validate(self, tolerance: float = 0.1) -> Tuple[bool, List[str]]:
        """
        Validate graph-shape consistency.

        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []

        # Check 1: All edges reference existing nodes
        for a, b in self.edges:
            if a not in self.shapes:
                issues.append(f"Edge references non-existent node: {a}")
            if b not in self.shapes:
                issues.append(f"Edge references non-existent node: {b}")

        # Check 2: Graph is connected
        if not self.is_connected():
            issues.append("Graph is not connected (has multiple components)")

        # Check 3: No overlapping shapes
        overlaps = self.find_overlaps(tolerance)
        if overlaps:
            issues.append(f"Found {len(overlaps)} overlapping shape pairs")

        # Check 4: Adjacent nodes have adjacent shapes
        non_adjacent = []
        for a, b in self.edges:
            rect_a = self.shapes[a]
            rect_b = self.shapes[b]
            if not rect_a.is_adjacent_to(rect_b, tolerance):
                non_adjacent.append((a, b))

        if non_adjacent:
            issues.append(f"Found {len(non_adjacent)} edges without geometric adjacency")

        # Check 5: No isolated nodes (all nodes have at least one edge)
        isolated = [node_id for node_id in self.shapes.keys() if self.degree(node_id) == 0]
        if isolated:
            issues.append(f"Found {len(isolated)} isolated nodes: {isolated}")

        is_valid = len(issues) == 0
        return (is_valid, issues)

    def validate_dict(self, tolerance: float = 0.1) -> Dict[str, bool]:
        """
        Validate graph-shape consistency (dictionary format).

        Returns:
            Dictionary of validation checks and their results
        """
        is_valid, issues = self.validate(tolerance)

        return {
            'all_edges_valid': not any('non-existent node' in issue for issue in issues),
            'graph_connected': not any('not connected' in issue for issue in issues),
            'no_overlaps': not any('overlapping' in issue for issue in issues),
            'adjacencies_valid': not any('without geometric adjacency' in issue for issue in issues),
            'no_isolated_nodes': not any('isolated nodes' in issue for issue in issues)
        }

    def find_overlaps(self, tolerance: float = 0.1) -> List[Tuple[str, str]]:
        """
        Find all pairs of overlapping shapes.

        Returns:
            List of (node_id_a, node_id_b) tuples for overlapping shapes
        """
        overlaps = []
        nodes = list(self.shapes.keys())

        for i, node_a in enumerate(nodes):
            for node_b in nodes[i+1:]:
                rect_a = self.shapes[node_a]
                rect_b = self.shapes[node_b]
                if rect_a.overlaps(rect_b, tolerance):
                    overlaps.append((node_a, node_b))

        return overlaps

    def find_missing_adjacencies(self, tolerance: float = 0.1) -> List[Tuple[str, str]]:
        """
        Find geometric adjacencies that are not represented in the graph.

        Returns:
            List of (node_id_a, node_id_b) tuples for adjacent shapes without edges
        """
        edge_set = set()
        for a, b in self.edges:
            edge_set.add((min(a, b), max(a, b)))

        missing = []
        nodes = list(self.shapes.keys())

        for i, node_a in enumerate(nodes):
            for node_b in nodes[i+1:]:
                edge_key = (min(node_a, node_b), max(node_a, node_b))
                if edge_key not in edge_set:
                    rect_a = self.shapes[node_a]
                    rect_b = self.shapes[node_b]
                    if rect_a.is_adjacent_to(rect_b, tolerance):
                        missing.append((node_a, node_b))

        return missing

    def bounding_box(self) -> Tuple[float, float, float, float]:
        """
        Calculate bounding box containing all shapes.

        Returns:
            (min_x, min_y, max_x, max_y)
        """
        if not self.shapes:
            return (0, 0, 0, 0)

        min_x = min(rect.origin.x for rect in self.shapes.values())
        min_y = min(rect.origin.y for rect in self.shapes.values())
        max_x = max(rect.origin.x + rect.width for rect in self.shapes.values())
        max_y = max(rect.origin.y + rect.height for rect in self.shapes.values())

        return (min_x, min_y, max_x, max_y)

    # -------------------------------------------------------------------------
    # Factory Methods
    # -------------------------------------------------------------------------

    @classmethod
    def from_grid(cls, base: Rectangle, rows: int, cols: int) -> 'GraphShape':
        """
        Create GraphShape from grid subdivision of base rectangle.

        Args:
            base: Rectangle to subdivide
            rows: Number of rows
            cols: Number of columns

        Returns:
            GraphShape with grid topology
        """
        grid = base.subdivide_grid(rows, cols)

        shapes = {}
        edges = []

        # Create nodes with cell_[row]_[col] naming
        for i in range(rows):
            for j in range(cols):
                node_id = f"cell_{i}_{j}"
                shapes[node_id] = grid[i][j]

        # Create edges for adjacent cells
        for i in range(rows):
            for j in range(cols):
                current = f"cell_{i}_{j}"

                # Right neighbor
                if j < cols - 1:
                    right = f"cell_{i}_{j+1}"
                    edges.append((current, right))

                # Top neighbor
                if i < rows - 1:
                    top = f"cell_{i+1}_{j}"
                    edges.append((current, top))

        return cls(shapes=shapes, edges=edges)

    @classmethod
    def from_horizontal_split(
        cls,
        base: Rectangle,
        ratios: List[float],
        labels: Optional[List[str]] = None
    ) -> 'GraphShape':
        """
        Create GraphShape from horizontal subdivision.

        Args:
            base: Rectangle to subdivide
            ratios: List of width ratios (should sum to ~1.0)
            labels: Optional list of node labels (default: n0, n1, ...)

        Returns:
            GraphShape with linear chain topology
        """
        if labels is None:
            labels = [f"n{i}" for i in range(len(ratios))]

        if len(labels) != len(ratios):
            raise ValueError("Number of labels must match number of ratios")

        # Normalize ratios
        total = sum(ratios)
        normalized = [r / total for r in ratios]

        # Create shapes
        shapes = {}
        current_x = base.origin.x

        for i, (ratio, label) in enumerate(zip(normalized, labels)):
            width = base.width * ratio
            rect = Rectangle(
                width=width,
                height=base.height,
                origin=Point(current_x, base.origin.y)
            )
            shapes[label] = rect
            current_x += width

        # Create linear chain edges
        edges = []
        for i in range(len(labels) - 1):
            edges.append((labels[i], labels[i+1]))

        return cls(shapes=shapes, edges=edges)

    # -------------------------------------------------------------------------
    # Serialization
    # -------------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'shapes': {
                node_id: rect.to_dict()
                for node_id, rect in self.shapes.items()
            },
            'edges': self.edges,
            'metadata': self.metadata
        }


# =============================================================================
# TRANSFORMATION RULES
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
    """
    name: str
    description: str
    pattern: Callable[[GraphShape, str], bool]
    transform: Callable[[GraphShape, str, Dict], GraphShape]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def can_apply(self, gs: GraphShape, node_id: str) -> bool:
        """Check if rule can be applied to given node."""
        if node_id not in gs.shapes:
            return False
        return self.pattern(gs, node_id)

    def apply(self, gs: GraphShape, node_id: str, **params) -> GraphShape:
        """
        Apply transformation to given node.

        Args:
            gs: GraphShape to transform
            node_id: Target node to transform
            **params: Rule-specific parameters (e.g., ratio=0.5)

        Returns:
            New GraphShape after transformation
        """
        if not self.can_apply(gs, node_id):
            raise ValueError(
                f"Rule '{self.name}' cannot be applied to node '{node_id}'. "
                f"Pattern check failed."
            )

        return self.transform(gs, node_id, params)


# =============================================================================
# RULE LIBRARY
# =============================================================================

class RuleLibrary:
    """
    Collection of standard graph-shape transformation rules.

    All rules follow the pattern:
    1. Graph transformation (add/remove/merge nodes and edges)
    2. Shape transformation (subdivide/merge/adjust rectangles)
    3. Maintain consistency (graph structure = shape adjacency)
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
            Rectangle → subdivide_horizontal(ratio)

        Args:
            default_ratio: Default split position (0 < ratio < 1)

        Examples:
            >>> rule = RuleLibrary.split_horizontal(0.4)
            >>> new_gs = rule.apply(gs, 'n0', ratio=0.4)
            # n0 is split into n0_L (40%) and n0_R (60%)
        """
        def pattern(gs: GraphShape, node_id: str) -> bool:
            # Can split any node
            return True

        def transform(gs: GraphShape, node_id: str, params: Dict) -> GraphShape:
            ratio = params.get('ratio', default_ratio)

            # Get original rectangle and neighbors
            rect = gs.shapes[node_id]
            neighbors = gs.get_neighbors(node_id)

            # SHAPE TRANSFORMATION: Subdivide rectangle
            left_rect, right_rect = rect.subdivide_horizontal(ratio)

            # GRAPH TRANSFORMATION: Create new nodes and edges
            left_id = f"{node_id}_L"
            right_id = f"{node_id}_R"

            # Build new shapes dict
            new_shapes = gs.shapes.copy()
            del new_shapes[node_id]
            new_shapes[left_id] = left_rect
            new_shapes[right_id] = right_rect

            # Build new edges list
            new_edges = []

            # Add edge between split nodes
            new_edges.append((left_id, right_id))

            # Reconnect neighbors to BOTH new nodes
            for neighbor in neighbors:
                new_edges.append((left_id, neighbor))
                new_edges.append((right_id, neighbor))

            # Keep all other edges (that don't involve node_id)
            for a, b in gs.edges:
                if a != node_id and b != node_id:
                    new_edges.append((a, b))

            return GraphShape(
                shapes=new_shapes,
                edges=new_edges,
                metadata={
                    **gs.metadata,
                    'last_rule': 'split_horizontal',
                    'split_node': node_id,
                    'split_ratio': ratio
                }
            )

        return GraphShapeRule(
            name=f"split_horizontal_{default_ratio}",
            description=f"Split node horizontally at ratio {default_ratio}",
            pattern=pattern,
            transform=transform,
            metadata={'type': 'subdivision', 'direction': 'horizontal'}
        )

    @staticmethod
    def split_vertical(default_ratio: float = 0.5) -> GraphShapeRule:
        """
        Split a node vertically (bottom | top).

        Similar to split_horizontal but divides along vertical axis.
        """
        def pattern(gs: GraphShape, node_id: str) -> bool:
            return True

        def transform(gs: GraphShape, node_id: str, params: Dict) -> GraphShape:
            ratio = params.get('ratio', default_ratio)

            rect = gs.shapes[node_id]
            neighbors = gs.get_neighbors(node_id)

            # SHAPE: Subdivide vertically
            bottom_rect, top_rect = rect.subdivide_vertical(ratio)

            # GRAPH: Create new nodes
            bottom_id = f"{node_id}_B"
            top_id = f"{node_id}_T"

            new_shapes = gs.shapes.copy()
            del new_shapes[node_id]
            new_shapes[bottom_id] = bottom_rect
            new_shapes[top_id] = top_rect

            new_edges = []
            new_edges.append((bottom_id, top_id))

            for neighbor in neighbors:
                new_edges.append((bottom_id, neighbor))
                new_edges.append((top_id, neighbor))

            for a, b in gs.edges:
                if a != node_id and b != node_id:
                    new_edges.append((a, b))

            return GraphShape(
                shapes=new_shapes,
                edges=new_edges,
                metadata={
                    **gs.metadata,
                    'last_rule': 'split_vertical',
                    'split_node': node_id,
                    'split_ratio': ratio
                }
            )

        return GraphShapeRule(
            name=f"split_vertical_{default_ratio}",
            description=f"Split node vertically at ratio {default_ratio}",
            pattern=pattern,
            transform=transform,
            metadata={'type': 'subdivision', 'direction': 'vertical'}
        )

    @staticmethod
    def merge_adjacent() -> GraphShapeRule:
        """
        Merge two adjacent nodes into one.

        Graph transformation:
            n0 + n1 → n0_n1
            Remove edge (n0, n1)
            Merge neighbor connections

        Shape transformation:
            Bounding box of both rectangles

        Note: Requires selecting TWO nodes. Uses 'target_neighbor' parameter.
        """
        def pattern(gs: GraphShape, node_id: str) -> bool:
            # Can merge if node has at least one neighbor
            return len(gs.get_neighbors(node_id)) > 0

        def transform(gs: GraphShape, node_id: str, params: Dict) -> GraphShape:
            # Get neighbor to merge with
            neighbor_id = params.get('neighbor_id')
            if neighbor_id is None:
                # Default: merge with first neighbor
                neighbors = gs.get_neighbors(node_id)
                if not neighbors:
                    raise ValueError(f"Node {node_id} has no neighbors to merge with")
                neighbor_id = neighbors[0]

            if neighbor_id not in gs.shapes:
                raise ValueError(f"Neighbor {neighbor_id} does not exist")

            # Check if they are actually adjacent
            if neighbor_id not in gs.get_neighbors(node_id):
                raise ValueError(f"Nodes {node_id} and {neighbor_id} are not adjacent")

            rect_a = gs.shapes[node_id]
            rect_b = gs.shapes[neighbor_id]

            # SHAPE: Merge into bounding box
            merged_rect = merge_rectangles_bounding_box([rect_a, rect_b])

            # GRAPH: Create merged node
            merged_id = f"{node_id}+{neighbor_id}"

            new_shapes = gs.shapes.copy()
            del new_shapes[node_id]
            del new_shapes[neighbor_id]
            new_shapes[merged_id] = merged_rect

            # Build new edges
            new_edges = []
            for a, b in gs.edges:
                # Replace references to old nodes with merged node
                new_a = merged_id if a in [node_id, neighbor_id] else a
                new_b = merged_id if b in [node_id, neighbor_id] else b

                # Skip self-loops and duplicates
                if new_a != new_b:
                    edge = tuple(sorted([new_a, new_b]))  # Normalize
                    if edge not in [tuple(sorted([e[0], e[1]])) for e in new_edges]:
                        new_edges.append((new_a, new_b))

            return GraphShape(
                shapes=new_shapes,
                edges=new_edges,
                metadata={
                    **gs.metadata,
                    'last_rule': 'merge_adjacent',
                    'merged_nodes': [node_id, neighbor_id]
                }
            )

        return GraphShapeRule(
            name="merge_adjacent",
            description="Merge two adjacent nodes into bounding box",
            pattern=pattern,
            transform=transform,
            metadata={'type': 'merge'}
        )

    @staticmethod
    def split_grid(rows: int = 2, cols: int = 2) -> GraphShapeRule:
        """
        Split a node into uniform grid.

        Graph transformation:
            n0 → n0_r0c0, n0_r0c1, ..., n0_r(rows-1)c(cols-1)
            Add edges for grid adjacencies (4-connectivity)

        Shape transformation:
            Rectangle → subdivide_grid(rows, cols)
        """
        def pattern(gs: GraphShape, node_id: str) -> bool:
            return True

        def transform(gs: GraphShape, node_id: str, params: Dict) -> GraphShape:
            actual_rows = params.get('rows', rows)
            actual_cols = params.get('cols', cols)

            rect = gs.shapes[node_id]
            neighbors = gs.get_neighbors(node_id)

            # SHAPE: Subdivide into grid
            grid_rects = rect.subdivide_grid(actual_rows, actual_cols)

            # GRAPH: Create grid nodes and edges
            new_shapes = gs.shapes.copy()
            del new_shapes[node_id]

            grid_nodes = {}  # (row, col) → node_id
            for row in range(actual_rows):
                for col in range(actual_cols):
                    cell_id = f"{node_id}_r{row}c{col}"
                    new_shapes[cell_id] = grid_rects[row][col]
                    grid_nodes[(row, col)] = cell_id

            # Build new edges
            new_edges = []

            # Grid internal edges (4-connectivity)
            for row in range(actual_rows):
                for col in range(actual_cols):
                    current_id = grid_nodes[(row, col)]

                    # Right neighbor
                    if col + 1 < actual_cols:
                        right_id = grid_nodes[(row, col + 1)]
                        new_edges.append((current_id, right_id))

                    # Bottom neighbor
                    if row + 1 < actual_rows:
                        bottom_id = grid_nodes[(row + 1, col)]
                        new_edges.append((current_id, bottom_id))

            # Connect border cells to original neighbors
            for row in range(actual_rows):
                for col in range(actual_cols):
                    # Cells on the border connect to all original neighbors
                    # (This is simplified - could be more sophisticated)
                    cell_id = grid_nodes[(row, col)]
                    for neighbor in neighbors:
                        new_edges.append((cell_id, neighbor))

            # Keep all other edges
            for a, b in gs.edges:
                if a != node_id and b != node_id:
                    new_edges.append((a, b))

            return GraphShape(
                shapes=new_shapes,
                edges=new_edges,
                metadata={
                    **gs.metadata,
                    'last_rule': 'split_grid',
                    'grid_size': (actual_rows, actual_cols)
                }
            )

        return GraphShapeRule(
            name=f"split_grid_{rows}x{cols}",
            description=f"Split node into {rows}×{cols} grid",
            pattern=pattern,
            transform=transform,
            metadata={'type': 'subdivision', 'grid': (rows, cols)}
        )


# =============================================================================
# RULE SEQUENCES & COMPOSITION
# =============================================================================

class RuleSequence:
    """
    Sequence of rules to apply in order.

    Allows composing multiple transformations into higher-level operations.
    """

    def __init__(self, rules: List[Tuple[GraphShapeRule, str, Dict]]):
        """
        Args:
            rules: List of (rule, target_node_id, params) tuples
        """
        self.rules = rules

    def apply(self, gs: GraphShape) -> GraphShape:
        """Apply all rules in sequence."""
        current = gs
        for rule, node_id, params in self.rules:
            current = rule.apply(current, node_id, **params)
        return current

    def __len__(self):
        return len(self.rules)


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def apply_rule_to_all_nodes(gs: GraphShape, rule: GraphShapeRule, **params) -> GraphShape:
    """
    Apply rule to all nodes in graph.

    Useful for batch transformations like "split all rooms horizontally".
    """
    current = gs
    for node_id in list(gs.shapes.keys()):
        if rule.can_apply(current, node_id):
            current = rule.apply(current, node_id, **params)
    return current


def find_applicable_nodes(gs: GraphShape, rule: GraphShapeRule) -> List[str]:
    """Find all nodes where rule can be applied."""
    return [
        node_id
        for node_id in gs.shapes.keys()
        if rule.can_apply(gs, node_id)
    ]
