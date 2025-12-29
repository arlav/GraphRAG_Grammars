import networkx as nx
import plotly.graph_objects as go
import math

def create_room_graph_with_touching_circles():
    # Define your graph (rooms = nodes, connections = edges)
    G = nx.Graph()
    rooms = [
        "Living Room", "Kitchen", "Bedroom", "Bathroom", "Guest Room",
        "Dining Room", "Library", "Home Office", "Garage", "Porch"
    ]
    G.add_nodes_from(rooms)

    # Connect rooms in a circular layout (you can customize edges)
    edges = [
        ("Living Room", "Kitchen"),
        ("Kitchen", "Bedroom"),
        ("Bedroom", "Bathroom"),
        ("Bathroom", "Guest Room"),
        ("Guest Room", "Dining Room"),
        ("Dining Room", "Library"),
        ("Library", "Home Office"),
        ("Home Office", "Garage"),
        ("Garage", "Porch"),
        ("Porch", "Living Room"),
    ]
    G.add_edges_from(edges)

    # Calculate positions using circular layout
    n = len(rooms)
    angle_step = 2 * math.pi / n
    positions = {}
    for i, room in enumerate(rooms):
        angle = i * angle_step
        positions[room] = (math.cos(angle), math.sin(angle))

    # Adjust for circle radius to ensure they touch (not overlap)
    # We'll use a simple circle packing approach: centers at radius r apart
    circle_radius = 0.15  # Adjust for size — smaller = more compact, larger = more space
    positions = {}
    for i, room in enumerate(rooms):
        angle = i * angle_step
        positions[room] = (math.cos(angle), math.sin(angle))

    # Convert positions to plotly coordinates
    x_coords = [positions[node][0] for node in rooms]
    y_coords = [positions[node][1] for node in rooms]

    # Create plotly figure
    fig = go.Figure()

    # Add nodes (circles)
    fig.add_trace(go.Scatter(
        x=x_coords,
        y=y_coords,
        mode='markers',
        marker=dict(
            size=20,  # Circle size
            color='lightblue',
            line=dict(color='darkblue', width=2),
            opacity=0.8
        ),
        name='Rooms',
        hoverinfo='text',
        text=rooms  # Show room names on hover
    ))

    # Add edges (lines between nodes)
    edge_x = []
    edge_y = []
    for edge in G.edges():
        x0, y0 = positions[edge[0]]
        x1, y1 = positions[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    fig.add_trace(go.Scatter(
        x=edge_x, y=edge_y,
        mode='lines',
        line=dict(width=2, color='darkgray'),
        hoverinfo='none',
        showlegend=False
    ))

    # Update layout
    fig.update_layout(
        title="Cyrano de Berzerac's Mansion - Room Layout",
        showlegend=False,
        hovermode='closest',
        margin=dict(l=0, r=0, b=0, t=30),
        width=800,
        height=800,
        font=dict(size=12)
    )

    # Show in browser
    fig.show()

# Run the script
if __name__ == "__main__":
    create_room_graph_with_touching_circles()
