"""
TopologicPy Helper Functions

Convenience functions for creating and manipulating TopologicPy primitives.
All functions return pure TopologicPy objects (Face, Vertex, Graph, etc.)

Philosophy: TopologicPy all the way down, Python for ergonomics.
"""

from typing import Optional
from topologicpy.Vertex import Vertex
from topologicpy.Edge import Edge
from topologicpy.Face import Face
from topologicpy.Topology import Topology
from topologicpy.Dictionary import Dictionary
from topologicpy.Cluster import Cluster
from topologicpy.Graph import Graph


# ============================================================================
# FACE CREATION HELPERS
# ============================================================================

def rectangular_face(
    width: float,
    height: float,
    origin: tuple[float, float] = (0.0, 0.0),
    label: Optional[str] = None,
    **metadata
) -> Face:
    """
    Create a rectangular Face with optional metadata.

    Args:
        width: Width of rectangle
        height: Height of rectangle
        origin: Bottom-left corner (x, y)
        label: Optional label for the face
        **metadata: Additional key-value pairs to store in Dictionary

    Returns:
        Face with attached Dictionary containing metadata

    Example:
        >>> kitchen = rectangular_face(5, 4, origin=(0, 0), label="Kitchen", area=20)
        >>> area = face_area(kitchen)
    """
    x, y = origin

    # Create vertices (counter-clockwise from bottom-left)
    vertices = [
        Vertex.ByCoordinates(x, y, 0),
        Vertex.ByCoordinates(x + width, y, 0),
        Vertex.ByCoordinates(x + width, y + height, 0),
        Vertex.ByCoordinates(x, y + height, 0),
    ]

    # Create face
    face = Face.ByVertices(vertices)

    # Build metadata dictionary
    meta = {
        "width": width,
        "height": height,
        "origin_x": x,
        "origin_y": y,
        "area": width * height,
    }

    if label:
        meta["label"] = label

    meta.update(metadata)

    # Attach dictionary to face
    keys = list(meta.keys())
    values = list(meta.values())
    d = Dictionary.ByKeysValues(keys, values)
    face = Topology.SetDictionary(face, d)

    return face


def square_face(
    size: float,
    origin: tuple[float, float] = (0.0, 0.0),
    label: Optional[str] = None,
    **metadata
) -> Face:
    """
    Create a square Face (convenience wrapper for rectangular_face).

    Args:
        size: Side length of square
        origin: Bottom-left corner (x, y)
        label: Optional label for the face
        **metadata: Additional metadata

    Returns:
        Square Face with attached Dictionary

    Example:
        >>> bathroom = square_face(3, origin=(10, 0), label="Bathroom")
    """
    return rectangular_face(size, size, origin, label, is_square=True, **metadata)


# ============================================================================
# METADATA UTILITIES
# ============================================================================

def get_metadata(topology: Topology, key: str, default=None):
    """
    Get metadata value from Topology's Dictionary.

    Args:
        topology: Any Topology object with attached Dictionary
        key: Metadata key to retrieve
        default: Value to return if key not found

    Returns:
        Metadata value or default

    Example:
        >>> label = get_metadata(face, "label", "Unknown")
        >>> width = get_metadata(face, "width", 0.0)
    """
    d = Topology.Dictionary(topology)
    if not d:
        return default

    keys = Dictionary.Keys(d)
    if key not in keys:
        return default

    values = Dictionary.Values(d)
    return values[keys.index(key)]


def set_metadata(topology: Topology, **kwargs) -> Topology:
    """
    Add/update metadata on a Topology.

    Merges new metadata with existing Dictionary.

    Args:
        topology: Topology to modify
        **kwargs: Key-value pairs to add

    Returns:
        Topology with updated Dictionary

    Example:
        >>> face = set_metadata(face, room_type="Kitchen", floor=2)
    """
    # Get existing dictionary
    existing_dict = Topology.Dictionary(topology)

    if existing_dict:
        existing_keys = Dictionary.Keys(existing_dict)
        existing_values = Dictionary.Values(existing_dict)
        existing_data = dict(zip(existing_keys, existing_values))
    else:
        existing_data = {}

    # Merge with new data
    existing_data.update(kwargs)

    # Create new dictionary
    keys = list(existing_data.keys())
    values = list(existing_data.values())
    new_dict = Dictionary.ByKeysValues(keys, values)

    return Topology.SetDictionary(topology, new_dict)


def get_all_metadata(topology: Topology) -> dict:
    """
    Get all metadata from Topology's Dictionary as a Python dict.

    Args:
        topology: Topology object

    Returns:
        Dictionary of all metadata key-value pairs

    Example:
        >>> meta = get_all_metadata(face)
        >>> print(meta)
        {'label': 'Kitchen', 'width': 5, 'height': 4, 'area': 20}
    """
    d = Topology.Dictionary(topology)
    if not d:
        return {}

    keys = Dictionary.Keys(d)
    values = Dictionary.Values(d)
    return dict(zip(keys, values))


# ============================================================================
# GEOMETRIC QUERIES (delegating to TopologicPy)
# ============================================================================

def face_centroid(face: Face) -> Vertex:
    """
    Get centroid of a Face as a Vertex.

    Args:
        face: Face object

    Returns:
        Vertex at the centroid

    Example:
        >>> centroid = face_centroid(kitchen_face)
        >>> x, y, z = Vertex.Coordinates(centroid)
    """
    return Topology.Centroid(face)


def faces_adjacent(face1: Face, face2: Face, tolerance: float = 0.01) -> bool:
    """
    Check if two Faces share an edge (are adjacent).

    Uses TopologicPy's SharedEdges to detect shared boundaries.

    Args:
        face1: First Face
        face2: Second Face
        tolerance: Distance tolerance for adjacency

    Returns:
        True if faces share at least one edge

    Example:
        >>> adjacent = faces_adjacent(kitchen, living_room)
    """
    try:
        shared = Topology.SharedEdges(face1, face2)
        return len(shared) > 0
    except:
        return False


def faces_overlap(face1: Face, face2: Face, tolerance: float = 0.01) -> bool:
    """
    Check if two Faces overlap (intersect with non-zero area).

    Args:
        face1: First Face
        face2: Second Face
        tolerance: Minimum area to consider as overlap

    Returns:
        True if faces overlap

    Example:
        >>> overlapping = faces_overlap(room1, room2)
    """
    try:
        intersection = Topology.Intersect(face1, face2)
        if not intersection:
            return False

        # Check if intersection has meaningful area
        area = Face.Area(intersection)
        return area > tolerance
    except:
        return False


def face_area(face: Face) -> float:
    """
    Get area of a Face.

    Args:
        face: Face object

    Returns:
        Area in square units

    Example:
        >>> area = face_area(bedroom)
    """
    return Face.Area(face)


def faces_bounding_box(faces: list[Face]) -> tuple[float, float, float, float]:
    """
    Calculate bounding box containing all faces.

    Args:
        faces: List of Face objects

    Returns:
        (min_x, min_y, max_x, max_y)

    Example:
        >>> bbox = faces_bounding_box([kitchen, living, bedroom])
        >>> min_x, min_y, max_x, max_y = bbox
    """
    all_coords = []

    for face in faces:
        vertices = Face.Vertices(face)
        for vertex in vertices:
            x, y, z = Vertex.Coordinates(vertex)
            all_coords.append((x, y))

    if not all_coords:
        return (0.0, 0.0, 0.0, 0.0)

    xs = [c[0] for c in all_coords]
    ys = [c[1] for c in all_coords]

    return (min(xs), min(ys), max(xs), max(ys))


# ============================================================================
# GRAPH CONSTRUCTION
# ============================================================================

def graph_from_faces_and_adjacencies(
    faces: list[Face],
    adjacencies: list[tuple[str, str]]
) -> Graph:
    """
    Create a Topologic Graph from faces and adjacency pairs.

    Creates vertices at face centroids and edges for each adjacency.
    Metadata from faces is copied to corresponding graph vertices.

    Args:
        faces: List of Face objects (must have 'label' metadata)
        adjacencies: List of (label1, label2) tuples

    Returns:
        Topologic Graph with vertices at centroids

    Example:
        >>> faces = [kitchen_face, living_face, bedroom_face]
        >>> adjacencies = [("Kitchen", "Living"), ("Living", "Bedroom")]
        >>> graph = graph_from_faces_and_adjacencies(faces, adjacencies)
    """
    # Build face lookup by label
    face_dict = {}
    vertex_dict = {}

    for face in faces:
        label = get_metadata(face, "label")
        if not label:
            continue

        face_dict[label] = face

        # Create vertex at centroid
        centroid = face_centroid(face)

        # Copy face metadata to vertex
        face_meta_dict = Topology.Dictionary(face)
        if face_meta_dict:
            centroid = Topology.SetDictionary(centroid, face_meta_dict)

        vertex_dict[label] = centroid

    # Create edges
    graph_edges = []
    for label1, label2 in adjacencies:
        if label1 in vertex_dict and label2 in vertex_dict:
            edge = Edge.ByVertices([vertex_dict[label1], vertex_dict[label2]])
            graph_edges.append(edge)

    # Create graph
    vertices_list = list(vertex_dict.values())

    # Handle edge cases
    if not graph_edges and len(vertices_list) >= 2:
        # Graph requires at least one edge, create connecting edge if needed
        dummy_edge = Edge.ByVertices([vertices_list[0], vertices_list[1]])
        graph_edges = [dummy_edge]

    if not graph_edges or len(vertices_list) < 2:
        raise ValueError(
            f"Cannot create graph: need at least 2 vertices and 1 edge. "
            f"Got {len(vertices_list)} vertices, {len(graph_edges)} edges"
        )

    graph = Graph.ByVerticesEdges(vertices_list, graph_edges)

    return graph


# ============================================================================
# VERTEX UTILITIES
# ============================================================================

def vertex_coordinates(vertex: Vertex) -> tuple[float, float, float]:
    """
    Get (x, y, z) coordinates from a Vertex.

    Args:
        vertex: Vertex object

    Returns:
        Tuple of (x, y, z) coordinates

    Example:
        >>> x, y, z = vertex_coordinates(centroid)
    """
    return Vertex.Coordinates(vertex)


def vertex_at(x: float, y: float, z: float = 0.0, **metadata) -> Vertex:
    """
    Create a Vertex at given coordinates with optional metadata.

    Args:
        x: X coordinate
        y: Y coordinate
        z: Z coordinate (default 0.0)
        **metadata: Optional metadata to attach

    Returns:
        Vertex with attached Dictionary

    Example:
        >>> v = vertex_at(5.0, 10.0, label="corner")
    """
    vertex = Vertex.ByCoordinates(x, y, z)

    if metadata:
        keys = list(metadata.keys())
        values = list(metadata.values())
        d = Dictionary.ByKeysValues(keys, values)
        vertex = Topology.SetDictionary(vertex, d)

    return vertex
