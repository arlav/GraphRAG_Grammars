"""
TopologicViz Bokeh Renderer

Interactive visualization of bubble diagrams and graph layouts using Bokeh.

Features:
- Interactive pan/zoom
- Hover tooltips with room info
- Circle selection
- Dynamic edge highlighting
- Multiple output modes (notebook, HTML, server)
"""

from typing import Dict, List, Tuple, Optional, Any, Union
import math

from bokeh.plotting import figure, show, output_notebook, output_file, save
from bokeh.models import (
    ColumnDataSource, 
    HoverTool, 
    TapTool,
    Circle as BokehCircle,
    MultiLine,
    LabelSet,
    Range1d,
    Title,
    CustomJS,
    Div,
    Slider,
    Button,
)
from bokeh.layouts import column, row
from bokeh.io import push_notebook
from bokeh.palettes import Category20

from .adapter import VizData, CircleData, EdgeData, TopologicAdapter
from .colors import RoomColors, ColorScheme, get_room_color


class BokehRenderer:
    """
    Bokeh-based renderer for bubble diagrams and graph visualizations.
    
    Usage:
        renderer = BokehRenderer()
        
        # From VizData
        renderer.render(viz_data)
        
        # From CircleNode dict directly
        renderer.render_bubble_diagram(circles, edges)
        
        # Get figure for custom composition
        fig = renderer.create_figure(viz_data)
    """
    
    def __init__(
        self,
        color_scheme: Union[str, ColorScheme] = "default",
        notebook_mode: bool = True
    ):
        """
        Initialize renderer.
        
        Args:
            color_scheme: Color scheme name or ColorScheme instance
            notebook_mode: If True, call output_notebook() on first render
        """
        if isinstance(color_scheme, str):
            self.colors = RoomColors.get_scheme(color_scheme)
        else:
            self.colors = color_scheme
        
        self.notebook_mode = notebook_mode
        self._notebook_initialized = False
        self.adapter = TopologicAdapter()
        
        # Default figure settings
        self.default_width = 800
        self.default_height = 800
        self.default_tools = "pan,wheel_zoom,box_zoom,reset,save"
    
    def _ensure_notebook(self):
        """Initialize notebook output if needed."""
        if self.notebook_mode and not self._notebook_initialized:
            output_notebook()
            self._notebook_initialized = True
    
    def _prepare_circle_data(self, viz_data: VizData) -> ColumnDataSource:
        """
        Convert VizData circles to Bokeh ColumnDataSource.
        
        Returns:
            ColumnDataSource with x, y, radius, color, room_type, area, node_id
        """
        data = {
            'x': [],
            'y': [],
            'radius': [],
            'color': [],
            'room_type': [],
            'area': [],
            'node_id': [],
            'label': [],  # For display
        }
        
        for node_id, circle in viz_data.circles.items():
            data['x'].append(circle.x)
            data['y'].append(circle.y)
            data['radius'].append(circle.radius)
            data['color'].append(self.colors.get_room_color(circle.room_type))
            data['room_type'].append(circle.room_type)
            data['area'].append(circle.area)
            data['node_id'].append(node_id)
            data['label'].append(f"{circle.room_type}\n{circle.area:.1f}m²")
        
        return ColumnDataSource(data=data)
    
    def _prepare_edge_data(self, viz_data: VizData) -> ColumnDataSource:
        """
        Convert VizData edges to Bokeh ColumnDataSource for MultiLine.
        
        Returns:
            ColumnDataSource with xs, ys (lists of x,y coordinate pairs)
        """
        data = {
            'xs': [],
            'ys': [],
            'source_id': [],
            'target_id': [],
        }
        
        for edge in viz_data.edges:
            data['xs'].append([edge.source_pos[0], edge.target_pos[0]])
            data['ys'].append([edge.source_pos[1], edge.target_pos[1]])
            data['source_id'].append(edge.source_id)
            data['target_id'].append(edge.target_id)
        
        return ColumnDataSource(data=data)
    
    def create_figure(
        self,
        viz_data: VizData,
        width: Optional[int] = None,
        height: Optional[int] = None,
        title: Optional[str] = None,
        show_labels: bool = True,
        show_edges: bool = True,
        show_hover: bool = True,
        tools: Optional[str] = None,
    ) -> figure:
        """
        Create a Bokeh figure from VizData.
        
        Args:
            viz_data: VizData to render
            width: Figure width in pixels
            height: Figure height in pixels
            title: Override title (uses viz_data.title if None)
            show_labels: Show room labels
            show_edges: Show edge connections
            show_hover: Enable hover tooltips
            tools: Override default tools
            
        Returns:
            Bokeh figure object
        """
        width = width or self.default_width
        height = height or self.default_height
        title = title or viz_data.title
        tools = tools or self.default_tools
        
        # Compute bounds with equal aspect ratio
        bounds = viz_data.bounds(margin=3.0)
        x_range = bounds[2] - bounds[0]
        y_range = bounds[3] - bounds[1]
        
        # Create figure
        p = figure(
            width=width,
            height=height,
            title=title,
            tools=tools,
            x_axis_label="X (m)",
            y_axis_label="Y (m)",
            match_aspect=True,  # Maintain equal aspect ratio
            x_range=Range1d(bounds[0], bounds[2]),
            y_range=Range1d(bounds[1], bounds[3]),
        )
        
        # Style
        p.title.text_font_size = "16pt"
        p.title.text_font_style = "bold"
        p.grid.grid_line_color = self.colors.grid_color
        p.grid.grid_line_alpha = 0.5
        
        # Prepare data sources
        circle_source = self._prepare_circle_data(viz_data)
        
        # Draw edges first (behind circles)
        if show_edges and viz_data.edges:
            edge_source = self._prepare_edge_data(viz_data)
            p.multi_line(
                xs='xs',
                ys='ys',
                source=edge_source,
                line_color=self.colors.edge_color,
                line_width=2,
                line_alpha=self.colors.edge_alpha,
                line_dash='dashed',
            )
        
        # Draw circles
        circles = p.circle(
            x='x',
            y='y',
            radius='radius',
            source=circle_source,
            fill_color='color',
            fill_alpha=self.colors.circle_alpha,
            line_color='black',
            line_width=2,
        )
        
        # Add hover tool
        if show_hover:
            hover = HoverTool(
                renderers=[circles],
                tooltips=[
                    ("Room", "@room_type"),
                    ("Area", "@area{0.1} m²"),
                    ("Radius", "@radius{0.2} m"),
                    ("ID", "@node_id"),
                ],
                mode='mouse'
            )
            p.add_tools(hover)
        
        # Add labels
        if show_labels:
            labels = LabelSet(
                x='x',
                y='y',
                text='room_type',
                source=circle_source,
                text_font_size='9pt',
                text_font_style='bold',
                text_align='center',
                text_baseline='middle',
                text_color=self.colors.label_text,
                background_fill_color=self.colors.label_background,
                background_fill_alpha=self.colors.label_alpha,
            )
            p.add_layout(labels)
        
        return p
    
    def render(
        self,
        viz_data: VizData,
        **kwargs
    ) -> Optional[Any]:
        """
        Render VizData and display.
        
        Args:
            viz_data: VizData to render
            **kwargs: Passed to create_figure()
            
        Returns:
            Bokeh handle (for push_notebook updates) or None
        """
        self._ensure_notebook()
        fig = self.create_figure(viz_data, **kwargs)
        
        if self.notebook_mode:
            handle = show(fig, notebook_handle=True)
            return handle
        else:
            show(fig)
            return None
    
    def render_bubble_diagram(
        self,
        circles: Dict[str, Any],
        edges: List[dict],
        title: str = "Bubble Diagram",
        **kwargs
    ) -> Optional[Any]:
        """
        Render directly from CircleNode dict and edges.
        
        Args:
            circles: Dict of CircleNode objects (from Phase2 notebook)
            edges: List of edge dicts with 'a', 'b' keys
            title: Diagram title
            **kwargs: Passed to create_figure()
            
        Returns:
            Bokeh handle or None
        """
        viz_data = self.adapter.from_circle_nodes(circles, edges, title=title)
        return self.render(viz_data, **kwargs)
    
    def render_topologic_graph(
        self,
        graph,
        title: str = "TopologicPy Graph",
        **kwargs
    ) -> Optional[Any]:
        """
        Render directly from TopologicPy Graph.
        
        Args:
            graph: TopologicPy Graph object
            title: Diagram title
            **kwargs: Passed to create_figure()
            
        Returns:
            Bokeh handle or None
        """
        viz_data = self.adapter.from_topologic_graph(graph, title=title)
        return self.render(viz_data, **kwargs)
    
    def save_html(
        self,
        viz_data: VizData,
        filepath: str,
        **kwargs
    ):
        """
        Save visualization to standalone HTML file.
        
        Args:
            viz_data: VizData to render
            filepath: Output file path
            **kwargs: Passed to create_figure()
        """
        output_file(filepath)
        fig = self.create_figure(viz_data, **kwargs)
        save(fig)
        print(f"✅ Saved to {filepath}")
    
    def create_interactive_figure(
        self,
        viz_data: VizData,
        width: Optional[int] = None,
        height: Optional[int] = None,
        title: Optional[str] = None,
    ) -> column:
        """
        Create figure with interactive controls.
        
        Includes:
        - Opacity slider for circles
        - Toggle for labels/edges
        - Selection highlighting
        
        Args:
            viz_data: VizData to render
            width: Figure width
            height: Figure height
            title: Override title
            
        Returns:
            Bokeh layout with figure and controls
        """
        width = width or self.default_width
        height = height or self.default_height
        title = title or viz_data.title
        
        # Prepare data sources
        circle_source = self._prepare_circle_data(viz_data)
        edge_source = self._prepare_edge_data(viz_data) if viz_data.edges else None
        
        # Compute bounds
        bounds = viz_data.bounds(margin=3.0)
        
        # Create figure
        p = figure(
            width=width,
            height=height,
            title=title,
            tools="pan,wheel_zoom,box_zoom,tap,reset,save",
            x_axis_label="X (m)",
            y_axis_label="Y (m)",
            match_aspect=True,
            x_range=Range1d(bounds[0], bounds[2]),
            y_range=Range1d(bounds[1], bounds[3]),
        )
        
        p.title.text_font_size = "16pt"
        p.grid.grid_line_alpha = 0.5
        
        # Draw edges
        if edge_source:
            edges_glyph = p.multi_line(
                xs='xs', ys='ys',
                source=edge_source,
                line_color=self.colors.edge_color,
                line_width=2,
                line_alpha=0.4,
                line_dash='dashed',
                name='edges'
            )
        
        # Draw circles
        circles_glyph = p.circle(
            x='x', y='y', radius='radius',
            source=circle_source,
            fill_color='color',
            fill_alpha=0.7,
            line_color='black',
            line_width=2,
            name='circles',
            selection_fill_color=self.colors.selection_color,
            selection_line_color='black',
            nonselection_fill_alpha=0.4,
        )
        
        # Labels
        labels = LabelSet(
            x='x', y='y', text='room_type',
            source=circle_source,
            text_font_size='9pt',
            text_font_style='bold',
            text_align='center',
            text_baseline='middle',
            background_fill_color='white',
            background_fill_alpha=0.85,
        )
        p.add_layout(labels)
        
        # Hover tool
        hover = HoverTool(
            renderers=[circles_glyph],
            tooltips=[
                ("Room", "@room_type"),
                ("Area", "@area{0.1} m²"),
                ("Radius", "@radius{0.2} m"),
                ("ID", "@node_id"),
            ],
        )
        p.add_tools(hover)
        
        # Create controls
        opacity_slider = Slider(
            start=0.1, end=1.0, value=0.7, step=0.1,
            title="Circle Opacity"
        )
        
        # JavaScript callback for opacity
        opacity_callback = CustomJS(
            args=dict(circles=circles_glyph),
            code="""
            circles.glyph.fill_alpha = cb_obj.value;
            """
        )
        opacity_slider.js_on_change('value', opacity_callback)
        
        # Info div
        info_div = Div(
            text=f"<b>Circles:</b> {viz_data.num_circles} | <b>Edges:</b> {viz_data.num_edges}",
            width=300
        )
        
        # Layout
        controls = row(opacity_slider, info_div)
        layout = column(controls, p)
        
        return layout
    
    def render_interactive(
        self,
        viz_data: VizData,
        **kwargs
    ) -> Optional[Any]:
        """
        Render interactive visualization with controls.
        
        Args:
            viz_data: VizData to render
            **kwargs: Passed to create_interactive_figure()
            
        Returns:
            Bokeh handle or None
        """
        self._ensure_notebook()
        layout = self.create_interactive_figure(viz_data, **kwargs)
        
        if self.notebook_mode:
            handle = show(layout, notebook_handle=True)
            return handle
        else:
            show(layout)
            return None


def render_bubble_diagram(
    circles: Dict[str, Any],
    edges: List[dict],
    title: str = "Bubble Diagram",
    color_scheme: str = "default",
    **kwargs
) -> Optional[Any]:
    """
    Convenience function to render bubble diagram.
    
    Args:
        circles: Dict of CircleNode objects
        edges: List of edge dicts
        title: Diagram title
        color_scheme: Color scheme name
        **kwargs: Passed to BokehRenderer.render()
        
    Returns:
        Bokeh handle or None
    """
    renderer = BokehRenderer(color_scheme=color_scheme)
    return renderer.render_bubble_diagram(circles, edges, title=title, **kwargs)
