"""
Bidirectional Converters: LayoutState ↔ GraphShape

Enables interoperability between Phase 2 (rules.py) and Phase 3/4 (core.py) architectures.

ARCHITECTURE BRIDGE:
- LayoutState (core.py): Mutable geometry-centric transformation substrate
- GraphShape (rules.py): Immutable graph-centric dual representation

CONVERSION PATTERNS:
1. LayoutState → GraphShape: For validation (overlaps, adjacency)
2. GraphShape → LayoutState: For transformation (shape grammar pipeline)
3. Combined validation: LayoutState checks + GraphShape geometric validation

USE CASES:
- Validate LayoutState using GraphShape.validate() (geometric consistency)
- Transform GraphShape using LayoutState pipeline (shape grammar)
- Export LayoutState as GraphShape for rule-based operations
- Apply GraphShape rules then convert back to LayoutState

Author: GraphRAG Shape Grammar Engine
Date: 2025-12-31 (Phase 4)
"""

from typing import List, Tuple

# Import from both architectures
from .core import (
    LayoutState,
    Shape,
    LayoutEdge,
    Phase,
    ShapeType,
    create_shape_from_face,
)

from .rules import GraphShape

from .topologic_helpers import (
    get_metadata,
    set_metadata,
    face_area,
    recognize_shape_type,
)

from topologicpy.Face import Face
from topologicpy.Edge import Edge


# ============================================================================
# LayoutState → GraphShape
# ============================================================================

def layout_state_to_graph_shape(layout: LayoutState) -> GraphShape:
    """
    Convert LayoutState to GraphShape.

    Creates TopologicPy Cluster from Shape Faces and Graph from edges.
    Metadata already exists in Face Dictionaries (single source).

    Args:
        layout: LayoutState to convert

    Returns:
        GraphShape instance with same geometry and topology

    Example:
        >>> layout = LayoutState(...)
        >>> layout.add_shape(create_circle_shape("s1", "Kitchen", 0, 0, 2.5))
        >>> gs = layout_state_to_graph_shape(layout)
        >>> is_valid, issues = gs.validate()

    Notes:
        - All metadata preserved (stored in Face Dictionaries)
        - LayoutState uses shape_id, GraphShape uses label
        - Assumes shape_id == label for compatibility
        - Edges converted from LayoutEdge to Graph adjacencies
    """
    # Extract faces (already have metadata in Dictionaries)
    faces = [shape.face for shape in layout.shapes.values()]

    # Ensure all faces have 'label' metadata (GraphShape requirement)
    updated_faces = []
    for face in faces:
        shape_id = get_metadata(face, "shape_id")
        label = get_metadata(face, "label")

        # If label missing, use shape_id as label
        if not label and shape_id:
            face = set_metadata(face, label=shape_id)

        updated_faces.append(face)

    # Extract adjacencies as (label, label) pairs
    adjacencies = []
    for edge in layout.edges:
        # LayoutState uses shape_id, GraphShape uses label
        # Assume they're equivalent
        adjacencies.append((edge.source_id, edge.target_id))

    # Use GraphShape factory method
    return GraphShape.from_faces_and_adjacencies(updated_faces, adjacencies)


# ============================================================================
# GraphShape → LayoutState
# ============================================================================

def graph_shape_to_layout_state(
    gs: GraphShape,
    phase: Phase = Phase.ARRANGED
) -> LayoutState:
    """
    Convert GraphShape to LayoutState.

    Creates Shape wrappers around GraphShape Faces and extracts edges from Graph.

    Args:
        gs: GraphShape to convert
        phase: Phase to assign to LayoutState (default ARRANGED)

    Returns:
        LayoutState instance with same geometry and topology

    Example:
        >>> gs = GraphShape.from_grid(20, 15, rows=2, cols=2)
        >>> layout = graph_shape_to_layout_state(gs, Phase.RECTANGLES)
        >>> layout.validate()

    Notes:
        - Ensures all required metadata exists in Dictionaries
        - Adds shape_id (from label), room_type, target_area, shape_type
        - Extracts Graph edges as LayoutEdge instances
    """
    # Create shapes from faces
    shapes = {}

    for face in gs.faces():
        # Get or infer metadata from Dictionary
        label = get_metadata(face, "label", "unknown")
        shape_id = get_metadata(face, "shape_id", label)  # Use label as fallback
        room_type = get_metadata(face, "room_type", label)

        # Get target_area (or use actual area)
        target_area = get_metadata(face, "target_area")
        if target_area is None:
            target_area = face_area(face)
            # Update Dictionary with computed area
            face = set_metadata(face, target_area=target_area)

        # Ensure shape_id in Dictionary
        if not get_metadata(face, "shape_id"):
            face = set_metadata(face, shape_id=shape_id)

        # Ensure room_type in Dictionary
        if not get_metadata(face, "room_type"):
            face = set_metadata(face, room_type=room_type)

        # Ensure shape_type in Dictionary
        if not get_metadata(face, "shape_type"):
            shape_type_str = recognize_shape_type(face)
            face = set_metadata(face, shape_type=shape_type_str)

        # Create Shape wrapper
        shape = Shape(face)
        shapes[shape_id] = shape

    # Extract edges from graph
    edges = []
    for graph_edge in gs.edges():
        verts = Edge.Vertices(graph_edge)
        if len(verts) == 2:
            label1 = get_metadata(verts[0], "label")
            label2 = get_metadata(verts[1], "label")

            if label1 and label2:
                # Use labels as shape IDs
                edges.append(LayoutEdge(label1, label2, "CONNECTS"))

    return LayoutState(
        phase=phase,
        shapes=shapes,
        edges=edges,
        is_valid=False
    )


# ============================================================================
# VALIDATION BRIDGE
# ============================================================================

def validate_layout_with_graph_shape(
    layout: LayoutState,
    tolerance: float = 0.01
) -> Tuple[bool, List[str]]:
    """
    Validate LayoutState using combined LayoutState + GraphShape validation.

    Provides comprehensive validation by combining:
    - LayoutState.validate(): Area errors, edge validity
    - GraphShape.validate(): Overlaps, geometric adjacency

    Args:
        layout: LayoutState to validate
        tolerance: Geometric tolerance for overlap/adjacency detection

    Returns:
        Tuple of (is_valid, list_of_issues)

    Example:
        >>> is_valid, issues = validate_layout_with_graph_shape(layout)
        >>> if not is_valid:
        ...     for issue in issues:
        ...         print(f"  ⚠️  {issue}")

    Notes:
        - Catches both topological issues (LayoutState) and geometric issues (GraphShape)
        - Overlapping faces detected by GraphShape
        - Missing adjacencies detected by GraphShape
        - Area mismatches detected by LayoutState
    """
    all_issues = []

    # LayoutState validation (area, edges)
    layout_issues = layout.validate()
    for category, issue_list in layout_issues.items():
        all_issues.extend(issue_list)

    # GraphShape validation (overlaps, adjacency)
    try:
        gs = layout_state_to_graph_shape(layout)
        gs_valid, gs_issues = gs.validate(tolerance)
        all_issues.extend(gs_issues)
    except Exception as e:
        all_issues.append(f"GraphShape conversion failed: {str(e)}")

    return (len(all_issues) == 0, all_issues)


# ============================================================================
# ADVANCED CONVERSIONS
# ============================================================================

def extract_subgraph_to_layout_state(
    gs: GraphShape,
    node_labels: List[str],
    phase: Phase = Phase.ARRANGED
) -> LayoutState:
    """
    Extract subset of GraphShape nodes as LayoutState.

    Useful for applying transformations to specific regions.

    Args:
        gs: Source GraphShape
        node_labels: List of node labels to extract
        phase: Phase to assign

    Returns:
        LayoutState containing only specified nodes and their edges

    Example:
        >>> gs = GraphShape.from_grid(30, 20, rows=3, cols=3)
        >>> # Extract center 4 cells
        >>> labels = ["cell_1_1", "cell_1_2", "cell_2_1", "cell_2_2"]
        >>> sub_layout = extract_subgraph_to_layout_state(gs, labels)
    """
    # Get all faces
    all_faces = gs.faces()

    # Filter to requested labels
    selected_faces = []
    label_set = set(node_labels)

    for face in all_faces:
        label = get_metadata(face, "label")
        if label in label_set:
            selected_faces.append(face)

    # Get edges between selected nodes
    all_edges = gs.edges()
    selected_edges = []

    for edge in all_edges:
        verts = Edge.Vertices(edge)
        if len(verts) == 2:
            label1 = get_metadata(verts[0], "label")
            label2 = get_metadata(verts[1], "label")

            # Only include edge if both endpoints are selected
            if label1 in label_set and label2 in label_set:
                selected_edges.append((label1, label2))

    # Create temporary GraphShape with subset
    temp_gs = GraphShape.from_faces_and_adjacencies(selected_faces, selected_edges)

    # Convert to LayoutState
    return graph_shape_to_layout_state(temp_gs, phase)


def merge_layouts(
    layout1: LayoutState,
    layout2: LayoutState,
    rename_conflicts: bool = True
) -> LayoutState:
    """
    Merge two LayoutStates into one.

    Args:
        layout1: First layout
        layout2: Second layout
        rename_conflicts: If True, rename conflicting shape IDs in layout2

    Returns:
        New LayoutState containing shapes and edges from both inputs

    Example:
        >>> layout_kitchen = LayoutState(...)
        >>> layout_bedroom = LayoutState(...)
        >>> full_layout = merge_layouts(layout_kitchen, layout_bedroom)

    Notes:
        - If rename_conflicts=False and IDs conflict, raises ValueError
        - Merged layout phase is Phase.ARRANGED (needs validation)
        - No spatial arrangement performed (shapes may overlap)
    """
    merged = LayoutState(phase=Phase.ARRANGED)

    # Add shapes from layout1
    for shape in layout1.shapes.values():
        merged.add_shape(shape)

    # Add shapes from layout2 (with optional renaming)
    shape_id_map = {}  # Old ID -> New ID for edge updates

    for shape in layout2.shapes.values():
        old_id = shape.id

        if old_id in merged.shapes:
            if not rename_conflicts:
                raise ValueError(f"Shape ID conflict: '{old_id}' exists in both layouts")

            # Generate unique ID
            new_id = f"{old_id}_2"
            counter = 2
            while new_id in merged.shapes:
                counter += 1
                new_id = f"{old_id}_{counter}"

            # Update shape_id in Dictionary
            shape.set(shape_id=new_id)
            shape_id_map[old_id] = new_id
        else:
            shape_id_map[old_id] = old_id

        merged.add_shape(shape)

    # Add edges from layout1
    for edge in layout1.edges:
        merged.add_edge(edge)

    # Add edges from layout2 (with renamed IDs)
    for edge in layout2.edges:
        new_source = shape_id_map.get(edge.source_id, edge.source_id)
        new_target = shape_id_map.get(edge.target_id, edge.target_id)

        merged.add_edge(LayoutEdge(new_source, new_target, edge.relation))

    merged.is_valid = False  # Needs validation
    return merged


# ============================================================================
# METADATA SYNCHRONIZATION
# ============================================================================

def ensure_metadata_consistency(layout: LayoutState) -> None:
    """
    Ensure all shapes have consistent metadata in Dictionaries.

    Validates and repairs:
    - shape_id exists
    - room_type exists
    - target_area exists
    - shape_type exists

    Args:
        layout: LayoutState to check and repair (modified in-place)

    Example:
        >>> ensure_metadata_consistency(layout)
        >>> # All shapes now have complete metadata

    Notes:
        - Modifies shape Dictionaries in-place
        - Uses geometry recognition for missing shape_type
        - Uses actual area for missing target_area
    """
    for shape_id, shape in layout.shapes.items():
        repairs = {}

        # Check shape_id
        if not get_metadata(shape.face, "shape_id"):
            repairs["shape_id"] = shape_id

        # Check room_type
        if not get_metadata(shape.face, "room_type"):
            repairs["room_type"] = f"Room_{shape_id}"

        # Check target_area
        if not get_metadata(shape.face, "target_area"):
            repairs["target_area"] = shape.area

        # Check shape_type
        if not get_metadata(shape.face, "shape_type"):
            shape_type_str = recognize_shape_type(shape.face)
            repairs["shape_type"] = shape_type_str

        # Apply repairs if needed
        if repairs:
            shape.set(**repairs)


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def count_shape_types(layout: LayoutState) -> dict:
    """
    Count shapes by type in layout.

    Args:
        layout: LayoutState to analyze

    Returns:
        Dictionary mapping ShapeType to count

    Example:
        >>> counts = count_shape_types(layout)
        >>> print(f"Circles: {counts[ShapeType.CIRCLE]}")
        >>> print(f"Rectangles: {counts[ShapeType.RECTANGLE]}")
    """
    from collections import Counter
    types = [shape.shape_type for shape in layout.shapes.values()]
    return dict(Counter(types))


def summarize_layout(layout: LayoutState) -> str:
    """
    Generate human-readable summary of LayoutState.

    Args:
        layout: LayoutState to summarize

    Returns:
        Multi-line string summary

    Example:
        >>> print(summarize_layout(layout))
        LayoutState Summary:
          Phase: ARRANGED
          Shapes: 8 (4 circles, 4 rectangles)
          Edges: 12
          Total Area: 156.3 m²
          Valid: True
    """
    type_counts = count_shape_types(layout)
    type_str = ", ".join(f"{count} {stype.name.lower()}s"
                         for stype, count in sorted(type_counts.items()))

    return f"""LayoutState Summary:
  Phase: {layout.phase.name}
  Shapes: {len(layout.shapes)} ({type_str})
  Edges: {len(layout.edges)}
  Total Area: {layout.total_area():.1f} m²
  Valid: {layout.is_valid}"""


def print_validation_report(layout: LayoutState, tolerance: float = 0.01) -> None:
    """
    Print detailed validation report.

    Args:
        layout: LayoutState to validate
        tolerance: Geometric tolerance

    Example:
        >>> print_validation_report(layout)
        ════════════════════════════════════════
        LAYOUT VALIDATION REPORT
        ════════════════════════════════════════
        Phase: ARRANGED
        Shapes: 8
        Edges: 12

        ✅ VALID - No issues found

        ════════════════════════════════════════
    """
    print("═" * 40)
    print("LAYOUT VALIDATION REPORT")
    print("═" * 40)
    print(f"Phase: {layout.phase.name}")
    print(f"Shapes: {len(layout.shapes)}")
    print(f"Edges: {len(layout.edges)}")
    print()

    is_valid, issues = validate_layout_with_graph_shape(layout, tolerance)

    if is_valid:
        print("✅ VALID - No issues found")
    else:
        print(f"❌ INVALID - {len(issues)} issue(s) found:")
        print()
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")

    print()
    print("═" * 40)
