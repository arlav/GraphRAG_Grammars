# TopologicViz

A visualization library for TopologicPy bubble diagrams and graph structures.

## Features

- **Multiple Backends**: Bokeh (interactive) and Matplotlib (static)
- **TopologicPy Integration**: Direct conversion from TopologicPy Graphs
- **Interactive Visualization**: Pan, zoom, hover tooltips with Bokeh
- **Color Schemes**: Default, Swiss, Architectural, High Contrast
- **Export**: HTML standalone files, image export

## Installation

```bash
# From the library directory
pip install -e .

# With all dependencies
pip install -e ".[all]"
```

## Quick Start

### From CircleNode dict (Phase2 notebook)

```python
from topologic_viz import BokehRenderer

renderer = BokehRenderer()
renderer.render_bubble_diagram(circles, edges, title="My Bubble Diagram")
```

### From TopologicPy Graph

```python
from topologic_viz import BokehRenderer

renderer = BokehRenderer()
renderer.render_topologic_graph(topo_graph, title="Graph Visualization")
```

### Interactive with controls

```python
from topologic_viz import BokehRenderer, TopologicAdapter

adapter = TopologicAdapter()
viz_data = adapter.from_circle_nodes(circles, edges)

renderer = BokehRenderer()
renderer.render_interactive(viz_data)
```

### Save to HTML

```python
viz_data = adapter.from_circle_nodes(circles, edges)
renderer.save_html(viz_data, "output.html")
```

## Color Schemes

```python
# Available schemes: default, swiss, architectural, high_contrast
renderer = BokehRenderer(color_scheme="swiss")
```

## Matplotlib Fallback

```python
from topologic_viz import MatplotlibRenderer

renderer = MatplotlibRenderer()
fig, ax = renderer.render_bubble_diagram(circles, edges)
```

## Library Structure

```
topologic_viz/
├── __init__.py           # Main exports
├── adapter.py            # VizData, CircleData, EdgeData, TopologicAdapter
├── bokeh_renderer.py     # BokehRenderer (interactive)
├── matplotlib_renderer.py # MatplotlibRenderer (static)
├── colors.py             # RoomColors, ColorScheme
└── setup.py              # Installation config
```

## API Reference

### TopologicAdapter

Converts TopologicPy objects to visualization-ready `VizData`:

- `from_circle_nodes(circles, edges)` - From Phase2 CircleNode dict
- `from_topologic_graph(graph)` - From TopologicPy Graph
- `from_node_edge_lists(nodes, edges)` - From raw lists

### BokehRenderer

Interactive visualization:

- `render(viz_data)` - Render VizData in notebook
- `render_bubble_diagram(circles, edges)` - Direct from CircleNodes
- `render_topologic_graph(graph)` - Direct from TopologicPy Graph
- `render_interactive(viz_data)` - With opacity slider controls
- `save_html(viz_data, filepath)` - Export standalone HTML
- `create_figure(viz_data)` - Get Bokeh figure for composition

### MatplotlibRenderer

Static visualization (matplotlib):

- `render(viz_data)` - Render to matplotlib
- `render_bubble_diagram(circles, edges)` - Direct from CircleNodes
- `save(viz_data, filepath)` - Save to image file

## Requirements

- Python >= 3.8
- numpy
- bokeh >= 3.0 (for BokehRenderer)
- matplotlib >= 3.5 (for MatplotlibRenderer)
- topologicpy (optional, for graph conversion)
