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


def circle_face(
    center_x: float,
    center_y: float,
    radius: float,
    num_segments: int = 32,
    label: Optional[str] = None,
    **metadata
) -> Face:
    """
    Create circular Face (polygon approximation).

    Args:
        center_x, center_y: Circle center coordinates
        radius: Circle radius
        num_segments: Number of polygon sides (default 32 for smooth circle)
        label: Optional label for the face
        **metadata: Additional key-value pairs to store in Dictionary

    Returns:
        Face with attached Dictionary containing metadata

    Example:
        >>> circle = circle_face(5, 5, 2.5, label="Living", room_type="Living")
        >>> area = face_area(circle)  # ≈ π * 2.5²
    """
    import math
    from topologicpy.Wire import Wire

    # Generate vertices around circle
    vertices = []
    for i in range(num_segments):
        angle = 2 * math.pi * i / num_segments
        x = center_x + radius * math.cos(angle)
        y = center_y + radius * math.sin(angle)
        vertices.append(Vertex.ByCoordinates(x, y, 0))

    # Create wire from vertices (closed loop)
    wire = Wire.ByVertices(vertices, close=True)

    # Create face from wire
    face = Face.ByWire(wire)

    # Build metadata dictionary
    meta = {
        "center_x": center_x,
        "center_y": center_y,
        "radius": radius,
        "area": math.pi * radius ** 2,
        "shape_type": "CIRCLE",
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


def lshape_face(
    center_x: float,
    center_y: float,
    arm1_length: float,
    arm1_width: float,
    arm2_length: float,
    arm2_width: float,
    rotation: float = 0.0,
    label: Optional[str] = None,
    **metadata
) -> Face:
    """
    Create L-shaped Face using TopologicPy.

    Configuration:
        ┌────────┐  ← arm1 (horizontal)
        │        │
        │  ┌─────┘
        │  │ arm2 (vertical)
        │  │
        └──┘

    Args:
        center_x, center_y: Center of L-shape
        arm1_length: Horizontal arm length
        arm1_width: Horizontal arm width
        arm2_length: Vertical arm length
        arm2_width: Vertical arm width
        rotation: Rotation in degrees (counter-clockwise)
        label: Optional label for the face
        **metadata: Additional metadata

    Returns:
        Face with 6 vertices and attached Dictionary

    Example:
        >>> lshape = lshape_face(5, 5, 4, 1.5, 4, 1.5, label="Kitchen")
    """
    import math
    from topologicpy.Wire import Wire

    # Define in local coordinates (origin at bottom-left)
    local_vertices = [
        (0, 0),                                            # 0: Bottom-left
        (arm2_width, 0),                                   # 1: Inner corner bottom
        (arm2_width, arm2_length - arm1_width),            # 2: Inner corner top
        (arm1_length, arm2_length - arm1_width),           # 3: Top-right of arm1
        (arm1_length, arm2_length),                        # 4: Top-right corner
        (0, arm2_length),                                  # 5: Top-left corner
    ]

    # Compute local centroid
    cx_local = sum(x for x, _ in local_vertices) / 6
    cy_local = sum(y for _, y in local_vertices) / 6

    # Center at origin
    centered = [(x - cx_local, y - cy_local) for x, y in local_vertices]

    # Rotate and translate
    theta = math.radians(rotation)
    cos_theta = math.cos(theta)
    sin_theta = math.sin(theta)

    vertices = []
    for lx, ly in centered:
        x_rot = lx * cos_theta - ly * sin_theta
        y_rot = lx * sin_theta + ly * cos_theta
        vertices.append(Vertex.ByCoordinates(x_rot + center_x, y_rot + center_y, 0))

    # Create face
    wire = Wire.ByVertices(vertices, close=True)
    face = Face.ByWire(wire)

    # Build metadata
    meta = {
        "center_x": center_x,
        "center_y": center_y,
        "arm1_length": arm1_length,
        "arm1_width": arm1_width,
        "arm2_length": arm2_length,
        "arm2_width": arm2_width,
        "rotation": rotation,
        "shape_type": "L_SHAPE",
    }

    if label:
        meta["label"] = label

    meta.update(metadata)

    # Attach dictionary
    keys = list(meta.keys())
    values = list(meta.values())
    d = Dictionary.ByKeysValues(keys, values)
    face = Topology.SetDictionary(face, d)

    return face


def tshape_face(
    center_x: float,
    center_y: float,
    top_length: float,
    top_width: float,
    stem_length: float,
    stem_width: float,
    rotation: float = 0.0,
    label: Optional[str] = None,
    **metadata
) -> Face:
    """
    Create T-shaped Face using TopologicPy.

    Configuration:
        ┌─────────────┐ ← top (horizontal bar)
        │             │
        ├──┐      ┌───┤
           │ stem │   ← stem (vertical)
           └──────┘

    Args:
        center_x, center_y: Center of T-shape
        top_length: Top bar length
        top_width: Top bar width
        stem_length: Stem length
        stem_width: Stem width
        rotation: Rotation in degrees
        label: Optional label
        **metadata: Additional metadata

    Returns:
        Face with 8 vertices and attached Dictionary

    Example:
        >>> tshape = tshape_face(10, 10, 6, 1.5, 4, 2, label="Corridor")
    """
    import math
    from topologicpy.Wire import Wire

    stem_left = -stem_width / 2
    stem_right = stem_width / 2
    top_left = -top_length / 2
    top_right = top_length / 2

    local_vertices = [
        (stem_left, 0),                               # 0: Bottom-left of stem
        (stem_right, 0),                              # 1: Bottom-right of stem
        (stem_right, stem_length),                    # 2: Top-right of stem
        (top_right, stem_length),                     # 3: Right side of top
        (top_right, stem_length + top_width),         # 4: Top-right corner
        (top_left, stem_length + top_width),          # 5: Top-left corner
        (top_left, stem_length),                      # 6: Left side of top
        (stem_left, stem_length),                     # 7: Top-left of stem
    ]

    # Center, rotate, translate
    cx_local = sum(x for x, _ in local_vertices) / 8
    cy_local = sum(y for _, y in local_vertices) / 8
    centered = [(x - cx_local, y - cy_local) for x, y in local_vertices]

    theta = math.radians(rotation)
    cos_theta = math.cos(theta)
    sin_theta = math.sin(theta)

    vertices = []
    for lx, ly in centered:
        x_rot = lx * cos_theta - ly * sin_theta
        y_rot = lx * sin_theta + ly * cos_theta
        vertices.append(Vertex.ByCoordinates(x_rot + center_x, y_rot + center_y, 0))

    wire = Wire.ByVertices(vertices, close=True)
    face = Face.ByWire(wire)

    # Build metadata
    meta = {
        "center_x": center_x,
        "center_y": center_y,
        "top_length": top_length,
        "top_width": top_width,
        "stem_length": stem_length,
        "stem_width": stem_width,
        "rotation": rotation,
        "shape_type": "T_SHAPE",
    }

    if label:
        meta["label"] = label

    meta.update(metadata)

    keys = list(meta.keys())
    values = list(meta.values())
    d = Dictionary.ByKeysValues(keys, values)
    face = Topology.SetDictionary(face, d)

    return face


def ushape_face(
    center_x: float,
    center_y: float,
    total_width: float,
    total_height: float,
    side_width: float,
    gap_width: float,
    rotation: float = 0.0,
    label: Optional[str] = None,
    **metadata
) -> Face:
    """
    Create U-shaped Face using TopologicPy.

    Configuration:
        ┌───┐     ┌───┐
        │   │     │   │ ← sides
        │   └─────┘   │ ← gap at top
        └─────────────┘

    Args:
        center_x, center_y: Center of U-shape
        total_width: Overall width
        total_height: Overall height
        side_width: Width of vertical sides
        gap_width: Width of gap at top center
        rotation: Rotation in degrees
        label: Optional label
        **metadata: Additional metadata

    Returns:
        Face with 8 vertices and attached Dictionary

    Example:
        >>> ushape = ushape_face(15, 15, 6, 5, 2, 2, label="Living")
    """
    import math
    from topologicpy.Wire import Wire

    hw = total_width / 2
    hh = total_height / 2
    gap_half = gap_width / 2
    inner_top = hh - side_width

    local_vertices = [
        (-hw, -hh),              # 0: Bottom-left
        (hw, -hh),               # 1: Bottom-right
        (hw, hh),                # 2: Top-right outer
        (gap_half, hh),          # 3: Top-right inner
        (gap_half, inner_top),   # 4: Inner top-right
        (-gap_half, inner_top),  # 5: Inner top-left
        (-gap_half, hh),         # 6: Top-left inner
        (-hw, hh),               # 7: Top-left outer
    ]

    theta = math.radians(rotation)
    cos_theta = math.cos(theta)
    sin_theta = math.sin(theta)

    vertices = []
    for lx, ly in local_vertices:
        x_rot = lx * cos_theta - ly * sin_theta
        y_rot = lx * sin_theta + ly * cos_theta
        vertices.append(Vertex.ByCoordinates(x_rot + center_x, y_rot + center_y, 0))

    wire = Wire.ByVertices(vertices, close=True)
    face = Face.ByWire(wire)

    # Build metadata
    meta = {
        "center_x": center_x,
        "center_y": center_y,
        "total_width": total_width,
        "total_height": total_height,
        "side_width": side_width,
        "gap_width": gap_width,
        "rotation": rotation,
        "shape_type": "U_SHAPE",
    }

    if label:
        meta["label"] = label

    meta.update(metadata)

    keys = list(meta.keys())
    values = list(meta.values())
    d = Dictionary.ByKeysValues(keys, values)
    face = Topology.SetDictionary(face, d)

    return face


def polygon_face(
    vertices_coords: list[tuple[float, float]],
    label: Optional[str] = None,
    **metadata
) -> Face:
    """
    Create generic polygon Face from vertex coordinates.

    Args:
        vertices_coords: List of (x, y) tuples defining polygon vertices
        label: Optional label for the face
        **metadata: Additional metadata

    Returns:
        Face with attached Dictionary

    Example:
        >>> pentagon = polygon_face(
        ...     [(0,0), (2,0), (3,1.5), (1,3), (-1,1.5)],
        ...     label="Custom"
        ... )
    """
    from topologicpy.Wire import Wire

    # Create vertices
    vertices = [Vertex.ByCoordinates(x, y, 0) for x, y in vertices_coords]

    # Create wire and face
    wire = Wire.ByVertices(vertices, close=True)
    face = Face.ByWire(wire)

    # Build metadata
    meta = {
        "num_vertices": len(vertices_coords),
        "shape_type": "POLYGON",
    }

    if label:
        meta["label"] = label

    meta.update(metadata)

    keys = list(meta.keys())
    values = list(meta.values())
    d = Dictionary.ByKeysValues(keys, values)
    face = Topology.SetDictionary(face, d)

    return face


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


def compute_grid_occupancy(face: Face, grid_size: int = 3) -> list[list[bool]]:
    """
    Compute bounding box grid occupancy pattern for shape classification.

    Divides the face's bounding box into a grid and checks which cells
    the face occupies. This creates a distinctive pattern for each shape type:

    - Rectangle: All cells occupied (solid block)
    - L-Shape: Corner + two adjacent edges (~6-7 cells in L pattern)
    - T-Shape: Middle row/column + perpendicular strip (~5-6 cells in T pattern)
    - U-Shape: Three sides, middle of one edge empty (~8 cells)
    - Circle: Most cells except corners (~5-8 cells, rounded)

    Args:
        face: TopologicPy Face to analyze
        grid_size: Grid dimensions (default 3x3)

    Returns:
        2D boolean array [row][col] where True = cell occupied by face

    Example:
        >>> tshape = tshape_face(0, 0, 6, 1.5, 4, 2)
        >>> grid = compute_grid_occupancy(tshape)
        >>> # grid might look like:
        >>> # [[False, True,  False],   # Top row
        >>> #  [False, True,  False],   # Middle row
        >>> #  [True,  True,  True ]]   # Bottom row (T pattern)
    """
    from topologicpy.Vertex import Vertex as TopVertex
    from topologicpy.Face import Face as TopFace

    # Get bounding box
    min_x, min_y, max_x, max_y = faces_bounding_box([face])

    # Handle degenerate case (zero-size bounding box)
    if max_x - min_x < 1e-6 or max_y - min_y < 1e-6:
        # Degenerate face, return empty grid
        return [[False] * grid_size for _ in range(grid_size)]

    # Create grid
    grid = [[False] * grid_size for _ in range(grid_size)]

    # Calculate cell dimensions
    cell_width = (max_x - min_x) / grid_size
    cell_height = (max_y - min_y) / grid_size

    # For each grid cell, check if face occupies it
    for row in range(grid_size):
        for col in range(grid_size):
            # Cell center point
            cell_cx = min_x + (col + 0.5) * cell_width
            cell_cy = min_y + (row + 0.5) * cell_height

            # Create test vertex at cell center
            test_point = TopVertex.ByCoordinates(cell_cx, cell_cy, 0)

            # Check if point is inside face
            # TopologicPy: Topology.Contains(container, content)
            try:
                from topologicpy.Topology import Topology as TopTopo
                is_inside = TopTopo.Contains(face, test_point)
                grid[row][col] = is_inside
            except Exception:
                # If Contains fails, assume not occupied
                grid[row][col] = False

    return grid


def classify_from_grid_pattern(grid: list[list[bool]]) -> str:
    """
    Classify shape type from 3x3 grid occupancy pattern.

    Pattern recognition rules:
    - Rectangle: All 9 cells occupied
    - L-Shape: 5-7 cells in L configuration (corner + two edges)
    - T-Shape: 5-7 cells in T configuration (middle column/row + perpendicular)
    - U-Shape: 6-8 cells in U configuration (three sides, one gap)
    - Circle: 5-8 cells with corners empty

    Args:
        grid: 3x3 boolean grid from compute_grid_occupancy()

    Returns:
        Shape type name as string

    Example:
        >>> grid = [[False, True, False],
        ...         [False, True, False],
        ...         [True,  True, True ]]
        >>> classify_from_grid_pattern(grid)
        'T_SHAPE'
    """
    # Count occupied cells
    occupied = sum(sum(row) for row in grid)

    # All cells = rectangle
    if occupied == 9:
        return "RECTANGLE"

    # Too few cells = not a recognizable shape
    if occupied < 5:
        return "POLYGON"

    # Analyze pattern (3x3 grid indices):
    # [0,0] [0,1] [0,2]
    # [1,0] [1,1] [1,2]
    # [2,0] [2,1] [2,2]

    # T-Shape detection: middle column or middle row heavily occupied
    # + perpendicular strip at one end
    middle_col_occupied = grid[0][1] + grid[1][1] + grid[2][1]
    middle_row_occupied = grid[1][0] + grid[1][1] + grid[1][2]

    # Vertical T: middle column full + top or bottom row
    if middle_col_occupied == 3:
        top_row = grid[0][0] + grid[0][1] + grid[0][2]
        bottom_row = grid[2][0] + grid[2][1] + grid[2][2]
        if top_row >= 2 or bottom_row >= 2:
            return "T_SHAPE"

    # Horizontal T: middle row full + left or right column
    if middle_row_occupied == 3:
        left_col = grid[0][0] + grid[1][0] + grid[2][0]
        right_col = grid[0][2] + grid[1][2] + grid[2][2]
        if left_col >= 2 or right_col >= 2:
            return "T_SHAPE"

    # U-Shape detection: has vertical or horizontal gap creating U pattern
    # Patterns: vertical gap (U rotated) or horizontal gap (normal U)
    # Check for center column/row being empty while edges are occupied

    # Vertical U (gap in middle columns)
    left_col = grid[0][0] + grid[1][0] + grid[2][0]
    middle_col = grid[0][1] + grid[1][1] + grid[2][1]
    right_col = grid[0][2] + grid[1][2] + grid[2][2]

    # Horizontal U (gap in middle rows)
    top_row = grid[0][0] + grid[0][1] + grid[0][2]
    middle_row = grid[1][0] + grid[1][1] + grid[1][2]
    bottom_row = grid[2][0] + grid[2][1] + grid[2][2]

    # Vertical U: left and right columns full, middle has gaps
    if left_col >= 2 and right_col >= 2 and middle_col <= 1 and occupied >= 6:
        return "U_SHAPE"

    # Horizontal U: top and bottom rows full, middle has gaps
    if top_row >= 2 and bottom_row >= 2 and middle_row <= 1 and occupied >= 6:
        return "U_SHAPE"

    # L-Shape detection: two perpendicular sides occupied
    # Common patterns: (top+left), (top+right), (bottom+left), (bottom+right)
    sides_occupied = sum([
        top_row >= 2,
        bottom_row >= 2,
        left_col >= 2,
        right_col >= 2
    ])

    if sides_occupied == 2:
        # Check for perpendicular configuration
        if (top_row >= 2 and left_col >= 2) or \
           (top_row >= 2 and right_col >= 2) or \
           (bottom_row >= 2 and left_col >= 2) or \
           (bottom_row >= 2 and right_col >= 2):
            return "L_SHAPE"

    # Circle detection: corners mostly empty, center and edges occupied
    corners_occupied = grid[0][0] + grid[0][2] + grid[2][0] + grid[2][2]
    if corners_occupied <= 1 and grid[1][1] and occupied >= 5:
        return "CIRCLE"

    # Default: unknown polygon
    return "POLYGON"


def recognize_shape_type(face: Face) -> str:
    """
    Recognize shape type from Face using multi-tier classification.

    Classification strategy (in order of preference):
    1. Read 'shape_type' from Dictionary metadata (fastest, most reliable)
    2. Geometric analysis using 3×3 grid occupancy pattern (robust)
    3. Vertex count heuristics (fast fallback)

    Returns shape_type as string (compatible with ShapeType enum names):
    - "RECTANGLE": All grid cells occupied or 4 vertices
    - "L_SHAPE": L-pattern in grid or 6 vertices
    - "T_SHAPE": T-pattern in grid or 8 vertices
    - "U_SHAPE": U-pattern in grid or 8 vertices
    - "CIRCLE": Circular pattern in grid or 16+ vertices
    - "POLYGON": Other patterns

    Args:
        face: TopologicPy Face to analyze

    Returns:
        Shape type name as string

    Example:
        >>> face = circle_face(0, 0, 5)
        >>> recognize_shape_type(face)
        'CIRCLE'
        >>> face = lshape_face(0, 0, 4, 1.5, 4, 1.5)
        >>> recognize_shape_type(face)
        'L_SHAPE'
    """
    # TIER 1: Check metadata (fastest, most reliable when available)
    shape_type_meta = get_metadata(face, "shape_type")
    if shape_type_meta:
        return shape_type_meta

    # TIER 2: Geometric analysis using grid occupancy pattern (robust)
    try:
        grid = compute_grid_occupancy(face, grid_size=3)
        shape_from_grid = classify_from_grid_pattern(grid)

        # If grid classification is confident (not POLYGON), use it
        if shape_from_grid != "POLYGON":
            return shape_from_grid
    except Exception:
        # If grid analysis fails, fall through to vertex count
        pass

    # TIER 3: Vertex count heuristics (fast fallback)
    vertices = Face.Vertices(face)
    n = len(vertices)

    if n == 4:
        return "RECTANGLE"
    elif n == 6:
        return "L_SHAPE"
    elif n == 8:
        # Ambiguous - could be T or U
        # Grid analysis should have caught this, but if not, default to T
        return "T_SHAPE"
    elif n >= 16:
        # High vertex count suggests approximated circle
        return "CIRCLE"
    else:
        return "POLYGON"


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
