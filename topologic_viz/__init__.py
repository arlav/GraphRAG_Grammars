"""
TopologicViz - Visualization adapters for TopologicPy

A flexible visualization library for TopologicPy geometry and graph structures.
Supports multiple backends: Bokeh (interactive), Matplotlib (static), PyVista (3D).

Usage:
    from topologic_viz import BokehRenderer, TopologicAdapter
    
    # From CircleNode dict
    renderer = BokehRenderer()
    renderer.render_bubble_diagram(circles, edges)
    
    # From TopologicPy Graph
    adapter = TopologicAdapter()
    viz_data = adapter.graph_to_viz_data(topo_graph)
    renderer.render_from_viz_data(viz_data)
"""

from .adapter import TopologicAdapter, VizData, CircleData, EdgeData
from .bokeh_renderer import BokehRenderer, render_bubble_diagram as bokeh_render
from .matplotlib_renderer import MatplotlibRenderer, visualize_bubble_diagram as mpl_render
from .colors import RoomColors, ColorScheme

__version__ = "0.1.0"
__all__ = [
    # Core
    "TopologicAdapter",
    "VizData",
    "CircleData", 
    "EdgeData",
    # Renderers
    "BokehRenderer",
    "MatplotlibRenderer",
    # Color schemes
    "RoomColors",
    "ColorScheme",
    # Convenience functions
    "bokeh_render",
    "mpl_render",
]
