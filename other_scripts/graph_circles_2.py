import networkx as nx
import plotly.graph_objects as go
import math

def create_room_graph():
    # Create a graph representing rooms
    G = nx.Graph()
    
    # Define room nodes
    rooms = [
        "Living Room", "Kitchen", "Bedroom", "Bathroom", 
        "Dining Room", "Study", "Garage", "Porch", "Office", "Hallway"
    ]
    G.add_nodes_from(rooms)
    
    # Add edges (connections between rooms)
    edges = [
        ("Living Room", "Kitchen"),
        ("Kitchen", "Dining Room"),
        ("Dining Room", "Bedroom"),
        ("Bedroom", "Bathroom"),
        ("Bathroom", "Study"),
        ("Study", "Office"),
        ("Office", "Garage"),
        ("Garage", "Porch"),
        ("Porch", "Hallway"),
        ("Hallway", "Living Room"),
        ("Kitchen", "Study"),
        ("Bedroom", "Office")
    ]
    G.add_edges_from(edges)
    
    # Calculate positions in a circular layout
    n = len(rooms)
    center = (0, 0)
    radius = 3.5
    
    positions = {}
    for i, room in enumerate(rooms):
        angle = 2 * math.pi * i / n
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)
        positions[room] = (x, y)
    
    # Extract coordinates for plotting
    x_coords = [positions[node][0] for node in rooms]
    y_coords = [positions[node][1] for node in rooms]
    
    # Create the figure
    fig = go.Figure()
    
    # Add edges between nodes
    edge_x = []
    edge_y = []
    for edge in G.edges():
        x0, y0 = positions[edge[0]]
        x1, y1 = positions[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
    
    fig.add_trace(go.Scatter(
        x=edge_x,
        y=edge_y,
        mode='lines',
        line=dict(width=2, color='gray'),
        hoverinfo='none'
    ))
    
    # Add nodes as circles
    fig.add_trace(go.Scatter(
        x=x_coords,
        y=y_coords,
        mode='markers+text',
        marker=dict(
            size=40,
            color='lightblue',
            line=dict(width=2, color='darkblue')
        ),
        text=rooms,
        textposition="middle center",
        hovertemplate='<b>%{text}</b><extra></extra>'
    ))
    
    # Customize layout
    fig.update_layout(
        title="Cyrano de Berzerac's Mansion - Room Layout",
        showlegend=False,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        width=800,
        height=800,
        font=dict(size=12)
    )
    
    # Save and display
    fig.show()

# Run the script
if __name__ == "__main__":
    create_room_graph()
