"""
TopologicViz Matplotlib Renderer

Static visualization using matplotlib (fallback from original notebook).
Provides compatibility with environments without Bokeh.
"""

from typing import Dict, List, Tuple, Optional, Any, Union
import math

from .adapter import VizData, CircleData, EdgeData, TopologicAdapter
from .colors import RoomColors, ColorScheme, get_room_color


class MatplotlibRenderer:
    """
    Matplotlib-based renderer for bubble diagrams.
    
    Provides static visualizations compatible with the original Phase2 notebook.
    Use BokehRenderer for interactive visualizations.
    """
    
    def __init__(
        self,
        color_scheme: Union[str, ColorScheme] = "default"
    ):
        """
        Initialize renderer.
        
        Args:
            color_scheme: Color scheme name or ColorScheme instance
        """
        if isinstance(color_scheme, str):
            self.colors = RoomColors.get_scheme(color_scheme)
        else:
            self.colors = color_scheme
        
        self.adapter = TopologicAdapter()
    
    def render(
        self,
        viz_data: VizData,
        figsize: Tuple[int, int] = (12, 12),
        show_labels: bool = True,
        show_edges: bool = True,
        title: Optional[str] = None,
        ax = None,
    ):
        """
        Render VizData using matplotlib.
        
        Args:
            viz_data: VizData to render
            figsize: Figure size in inches
            show_labels: Show room labels
            show_edges: Draw edges
            title: Override title
            ax: Existing axes to draw on
            
        Returns:
            matplotlib figure and axes
        """
        import matplotlib.pyplot as plt
        from matplotlib.patches import Circle as MplCircle
        from matplotlib.collections import LineCollection
        
        title = title or viz_data.title
        
        # Create figure if no axes provided
        if ax is None:
            fig, ax = plt.subplots(figsize=figsize)
        else:
            fig = ax.get_figure()
        
        # Draw edges first (behind circles)
        if show_edges and viz_data.edges:
            edge_lines = []
            for edge in viz_data.edges:
                edge_lines.append([
                    edge.source_pos,
                    edge.target_pos
                ])
            
            lc = LineCollection(
                edge_lines,
                colors=self.colors.edge_color,
                linewidths=1.5,
                alpha=self.colors.edge_alpha,
                linestyles='dashed'
            )
            ax.add_collection(lc)
        
        # Draw circles
        for node_id, circle in viz_data.circles.items():
            color = self.colors.get_room_color(circle.room_type)
            
            mpl_circle = MplCircle(
                circle.center,
                circle.radius,
                facecolor=color,
                edgecolor='black',
                linewidth=2,
                alpha=self.colors.circle_alpha
            )
            ax.add_patch(mpl_circle)
            
            # Label
            if show_labels:
                label_text = f"{circle.room_type}\n{circle.area:.1f}m²"
                ax.text(
                    circle.x, circle.y, label_text,
                    ha='center', va='center',
                    fontsize=9, weight='bold',
                    bbox=dict(
                        boxstyle='round,pad=0.3',
                        facecolor=self.colors.label_background,
                        alpha=self.colors.label_alpha,
                        edgecolor='none'
                    )
                )
        
        # Set equal aspect and limits
        ax.set_aspect('equal')
        
        # Compute bounds
        bounds = viz_data.bounds(margin=5.0)
        ax.set_xlim(bounds[0], bounds[2])
        ax.set_ylim(bounds[1], bounds[3])
        
        ax.set_title(title, fontsize=16, weight='bold')
        ax.grid(True, alpha=0.3)
        ax.set_xlabel('X (m)', fontsize=12)
        ax.set_ylabel('Y (m)', fontsize=12)
        
        plt.tight_layout()
        
        return fig, ax
    
    def render_bubble_diagram(
        self,
        circles: Dict[str, Any],
        edges: List[dict],
        title: str = "Bubble Diagram",
        **kwargs
    ):
        """
        Render directly from CircleNode dict and edges.
        
        Args:
            circles: Dict of CircleNode objects
            edges: List of edge dicts
            title: Diagram title
            **kwargs: Passed to render()
            
        Returns:
            matplotlib figure and axes
        """
        viz_data = self.adapter.from_circle_nodes(circles, edges, title=title)
        return self.render(viz_data, **kwargs)
    
    def render_topologic_graph(
        self,
        graph,
        title: str = "TopologicPy Graph",
        **kwargs
    ):
        """
        Render directly from TopologicPy Graph.
        
        Args:
            graph: TopologicPy Graph object
            title: Diagram title
            **kwargs: Passed to render()
            
        Returns:
            matplotlib figure and axes
        """
        viz_data = self.adapter.from_topologic_graph(graph, title=title)
        return self.render(viz_data, **kwargs)
    
    def save(
        self,
        viz_data: VizData,
        filepath: str,
        dpi: int = 150,
        **kwargs
    ):
        """
        Save visualization to image file.
        
        Args:
            viz_data: VizData to render
            filepath: Output file path (.png, .pdf, .svg)
            dpi: Resolution
            **kwargs: Passed to render()
        """
        import matplotlib.pyplot as plt
        
        fig, ax = self.render(viz_data, **kwargs)
        fig.savefig(filepath, dpi=dpi, bbox_inches='tight')
        plt.close(fig)
        print(f"✅ Saved to {filepath}")


# Convenience function matching original notebook API
def visualize_bubble_diagram(
    circles: Dict[str, Any],
    edges: List[dict],
    title: str = "Bubble Diagram",
    show_labels: bool = True,
    show_edges: bool = True,
    figsize: Tuple[int, int] = (12, 12),
    color_scheme: str = "default",
):
    """
    Drop-in replacement for original visualize_bubble_diagram().
    
    Args:
        circles: Dict of CircleNode objects
        edges: List of edge dicts
        title: Plot title
        show_labels: Show room type labels
        show_edges: Draw edges between connected circles
        figsize: Figure size
        color_scheme: Color scheme name
    """
    import matplotlib.pyplot as plt
    
    renderer = MatplotlibRenderer(color_scheme=color_scheme)
    fig, ax = renderer.render_bubble_diagram(
        circles, edges,
        title=title,
        show_labels=show_labels,
        show_edges=show_edges,
        figsize=figsize
    )
    plt.show()
