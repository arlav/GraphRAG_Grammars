"""
TopologicViz Adapter Module

Provides data structures and conversion utilities for translating
TopologicPy objects into visualization-ready formats.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Any, Set
import math

# Type aliases
Point2D = Tuple[float, float]
Point3D = Tuple[float, float, float]


@dataclass
class CircleData:
    """
    Visualization-ready circle data.
    
    Attributes:
        node_id: Unique identifier
        center: (x, y) position
        radius: Circle radius
        room_type: Room label/type
        area: Room area in m²
        props: Additional properties dict
    """
    node_id: str
    center: Point2D
    radius: float
    room_type: str = "Room"
    area: float = 0.0
    props: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def x(self) -> float:
        return self.center[0]
    
    @property
    def y(self) -> float:
        return self.center[1]
    
    def bounds(self) -> Tuple[float, float, float, float]:
        """Return (min_x, min_y, max_x, max_y)"""
        return (
            self.x - self.radius,
            self.y - self.radius,
            self.x + self.radius,
            self.y + self.radius
        )


@dataclass
class EdgeData:
    """
    Visualization-ready edge data.
    
    Attributes:
        source_id: Source node ID
        target_id: Target node ID
        source_pos: (x, y) of source
        target_pos: (x, y) of target
        props: Additional properties
    """
    source_id: str
    target_id: str
    source_pos: Point2D
    target_pos: Point2D
    props: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def midpoint(self) -> Point2D:
        return (
            (self.source_pos[0] + self.target_pos[0]) / 2,
            (self.source_pos[1] + self.target_pos[1]) / 2
        )
    
    @property
    def length(self) -> float:
        dx = self.target_pos[0] - self.source_pos[0]
        dy = self.target_pos[1] - self.source_pos[1]
        return math.sqrt(dx * dx + dy * dy)


@dataclass
class VizData:
    """
    Complete visualization data container.
    
    Bundles all elements needed for rendering a bubble diagram
    or graph visualization.
    """
    circles: Dict[str, CircleData] = field(default_factory=dict)
    edges: List[EdgeData] = field(default_factory=list)
    title: str = "Bubble Diagram"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def bounds(self, margin: float = 5.0) -> Tuple[float, float, float, float]:
        """
        Compute bounding box for all circles.
        
        Returns:
            (min_x, min_y, max_x, max_y) with margin
        """
        if not self.circles:
            return (-10, -10, 10, 10)
        
        min_x = min_y = float('inf')
        max_x = max_y = float('-inf')
        
        for circle in self.circles.values():
            bx0, by0, bx1, by1 = circle.bounds()
            min_x = min(min_x, bx0)
            min_y = min(min_y, by0)
            max_x = max(max_x, bx1)
            max_y = max(max_y, by1)
        
        return (min_x - margin, min_y - margin, max_x + margin, max_y + margin)
    
    @property
    def num_circles(self) -> int:
        return len(self.circles)
    
    @property
    def num_edges(self) -> int:
        return len(self.edges)


class TopologicAdapter:
    """
    Adapter for converting TopologicPy objects to VizData.
    
    Handles:
    - CircleNode dicts (from Phase2 notebook)
    - TopologicPy Graph objects
    - Raw node/edge lists
    """
    
    def __init__(self):
        pass
    
    def from_circle_nodes(
        self,
        circles: Dict[str, Any],  # Dict[str, CircleNode]
        edges: List[dict],
        title: str = "Bubble Diagram"
    ) -> VizData:
        """
        Convert CircleNode dict and edge list to VizData.
        
        Args:
            circles: Dict mapping node_id → CircleNode objects
            edges: List of edge dicts with 'a', 'b' keys
            title: Diagram title
            
        Returns:
            VizData ready for rendering
        """
        viz_data = VizData(title=title)
        
        # Convert circles
        for node_id, circle in circles.items():
            # Handle both CircleNode dataclass and dict
            if hasattr(circle, 'get_position'):
                # CircleNode dataclass
                x, y = circle.get_position()
                radius = circle.radius
                room_type = circle.room_type
                area = circle.area
            else:
                # Dict format
                x, y = circle.get('center', (0, 0))
                radius = circle.get('radius', 1.0)
                room_type = circle.get('room_type', 'Room')
                area = circle.get('area', 0.0)
            
            viz_data.circles[node_id] = CircleData(
                node_id=node_id,
                center=(x, y),
                radius=radius,
                room_type=room_type,
                area=area
            )
        
        # Convert edges
        for edge in edges:
            a, b = edge['a'], edge['b']
            if a in viz_data.circles and b in viz_data.circles:
                viz_data.edges.append(EdgeData(
                    source_id=a,
                    target_id=b,
                    source_pos=viz_data.circles[a].center,
                    target_pos=viz_data.circles[b].center
                ))
        
        return viz_data
    
    def from_topologic_graph(
        self,
        graph,  # TopologicPy Graph
        title: str = "Graph Visualization"
    ) -> VizData:
        """
        Convert TopologicPy Graph to VizData.
        
        Extracts:
        - Vertex positions from coordinates
        - Metadata from vertex dictionaries
        - Edge connectivity
        
        Args:
            graph: TopologicPy Graph object
            title: Diagram title
            
        Returns:
            VizData ready for rendering
        """
        # Import here to avoid hard dependency
        try:
            from topologicpy.Graph import Graph
            from topologicpy.Vertex import Vertex
            from topologicpy.Topology import Topology
            from topologicpy.Dictionary import Dictionary
        except ImportError:
            raise ImportError("TopologicPy not installed. Install with: pip install topologicpy")
        
        viz_data = VizData(title=title)
        
        # Get vertices
        vertices = Graph.Vertices(graph)
        vertex_map = {}  # Map vertex to ID
        
        for i, vertex in enumerate(vertices):
            x = Vertex.X(vertex)
            y = Vertex.Y(vertex)
            
            # Extract dictionary metadata
            vertex_dict = Topology.Dictionary(vertex)
            props = {}
            node_id = f"v{i}"
            room_type = "Room"
            area = 0.0
            radius = 1.0
            
            if vertex_dict:
                keys = Dictionary.Keys(vertex_dict)
                values = Dictionary.Values(vertex_dict)
                props = dict(zip(keys, values)) if keys and values else {}
                
                node_id = props.get('node_id', node_id)
                room_type = props.get('room_type', room_type)
                area = float(props.get('area', area))
                radius = float(props.get('radius', radius))
            
            viz_data.circles[node_id] = CircleData(
                node_id=node_id,
                center=(x, y),
                radius=radius,
                room_type=room_type,
                area=area,
                props=props
            )
            
            vertex_map[id(vertex)] = node_id
        
        # Get edges
        topo_edges = Graph.Edges(graph)
        for edge in topo_edges:
            # Get edge vertices
            from topologicpy.Edge import Edge
            edge_vertices = Edge.Vertices(edge)
            if len(edge_vertices) >= 2:
                v1, v2 = edge_vertices[0], edge_vertices[1]
                id1 = vertex_map.get(id(v1))
                id2 = vertex_map.get(id(v2))
                
                if id1 and id2 and id1 in viz_data.circles and id2 in viz_data.circles:
                    viz_data.edges.append(EdgeData(
                        source_id=id1,
                        target_id=id2,
                        source_pos=viz_data.circles[id1].center,
                        target_pos=viz_data.circles[id2].center
                    ))
        
        return viz_data
    
    def from_node_edge_lists(
        self,
        nodes: List[dict],
        edges: List[dict],
        positions: Optional[Dict[str, Point2D]] = None,
        title: str = "Graph"
    ) -> VizData:
        """
        Convert raw node/edge lists to VizData.
        
        Args:
            nodes: List of node dicts with 'id', 'label', optionally 'area', 'radius'
            edges: List of edge dicts with 'a', 'b'
            positions: Optional dict mapping node_id → (x, y)
            title: Diagram title
            
        Returns:
            VizData (positions will be zeros if not provided)
        """
        viz_data = VizData(title=title)
        
        # Default layout if no positions
        grid_size = max(1, int(math.ceil(math.sqrt(len(nodes)))))
        spacing = 10.0
        
        for i, node in enumerate(nodes):
            node_id = node['id']
            room_type = node.get('label', 'Room')
            
            # Get position
            if positions and node_id in positions:
                x, y = positions[node_id]
            else:
                row = i // grid_size
                col = i % grid_size
                x, y = col * spacing, row * spacing
            
            # Get area and radius
            props = node.get('props', {})
            if isinstance(props, str):
                import json
                try:
                    props = json.loads(props)
                except:
                    props = {}
            
            area = float(props.get('area', node.get('area', 10.0)))
            radius = float(node.get('radius', math.sqrt(area / math.pi)))
            
            viz_data.circles[node_id] = CircleData(
                node_id=node_id,
                center=(x, y),
                radius=radius,
                room_type=room_type,
                area=area,
                props=props
            )
        
        # Convert edges
        for edge in edges:
            a, b = edge['a'], edge['b']
            if a in viz_data.circles and b in viz_data.circles:
                viz_data.edges.append(EdgeData(
                    source_id=a,
                    target_id=b,
                    source_pos=viz_data.circles[a].center,
                    target_pos=viz_data.circles[b].center
                ))
        
        return viz_data


def area_to_radius(area: float) -> float:
    """Convert area to equivalent circle radius."""
    return math.sqrt(area / math.pi)


def radius_to_area(radius: float) -> float:
    """Convert circle radius to area."""
    return math.pi * radius * radius
