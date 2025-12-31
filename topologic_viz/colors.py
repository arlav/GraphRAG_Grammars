"""
TopologicViz Color Schemes

Provides consistent color palettes for room types and visualization elements.
"""

from typing import Dict, Optional
from dataclasses import dataclass, field


@dataclass
class ColorScheme:
    """
    Complete color scheme for bubble diagram visualization.
    """
    # Room type colors
    room_colors: Dict[str, str] = field(default_factory=dict)
    
    # UI colors
    edge_color: str = "#333333"
    edge_hover_color: str = "#0066cc"
    background_color: str = "#ffffff"
    grid_color: str = "#eeeeee"
    label_background: str = "#ffffff"
    label_text: str = "#333333"
    
    # Selection colors
    selection_color: str = "#ff6600"
    highlight_color: str = "#ffcc00"
    
    # Opacity values
    circle_alpha: float = 0.7
    edge_alpha: float = 0.4
    label_alpha: float = 0.85
    
    def get_room_color(self, room_type: str, default: str = "#dddddd") -> str:
        """Get color for a room type with fallback."""
        return self.room_colors.get(room_type, default)


class RoomColors:
    """
    Predefined room color palettes.
    """
    
    # Default palette (pastel, high contrast between room types)
    DEFAULT: Dict[str, str] = {
        "Entrance": "#ff9999",      # Light red
        "Kitchen": "#ffcc99",       # Light orange
        "Living": "#99ccff",        # Light blue
        "LivingRoom": "#99ccff",    # Light blue
        "Dining": "#99ffcc",        # Light teal
        "DiningRoom": "#99ffcc",    # Light teal
        "Bedroom": "#99ff99",       # Light green
        "MasterBedroom": "#66cc66", # Darker green
        "Bathroom": "#cc99ff",      # Light purple
        "Toilet": "#cc99ff",        # Light purple
        "WC": "#cc99ff",            # Light purple
        "Corridor": "#cccccc",      # Gray
        "Hallway": "#cccccc",       # Gray
        "Hall": "#cccccc",          # Gray
        "Balcony": "#ffffcc",       # Light yellow
        "Terrace": "#ffffcc",       # Light yellow
        "Storage": "#ffeeee",       # Very light pink
        "Closet": "#ffeeee",        # Very light pink
        "Utility": "#eeffee",       # Very light green
        "Laundry": "#eeffee",       # Very light green
        "Office": "#99cccc",        # Light cyan
        "Study": "#99cccc",         # Light cyan
        "Garage": "#aaaaaa",        # Medium gray
    }
    
    # Swiss dataset palette (based on typical Swiss apartment colors)
    SWISS: Dict[str, str] = {
        "Entrance": "#e8c4b8",      # Warm beige
        "Kitchen": "#f5d6a8",       # Warm yellow
        "Living": "#b8d4e8",        # Cool blue
        "LivingRoom": "#b8d4e8",
        "Bedroom": "#c8e8c4",       # Fresh green
        "Bathroom": "#d4b8e8",      # Soft purple
        "Corridor": "#d4d4d4",      # Neutral gray
        "Balcony": "#f5f5b8",       # Pale yellow
    }
    
    # Architectural palette (professional, muted)
    ARCHITECTURAL: Dict[str, str] = {
        "Entrance": "#c9b8a8",
        "Kitchen": "#d4c4a8",
        "Living": "#a8b8c4",
        "LivingRoom": "#a8b8c4",
        "Bedroom": "#b8c8b4",
        "Bathroom": "#b8b0c4",
        "Corridor": "#c0c0c0",
        "Balcony": "#d8d8b0",
    }
    
    # High contrast (accessibility)
    HIGH_CONTRAST: Dict[str, str] = {
        "Entrance": "#ff6b6b",
        "Kitchen": "#ffa94d",
        "Living": "#4dabf7",
        "LivingRoom": "#4dabf7",
        "Bedroom": "#51cf66",
        "Bathroom": "#cc5de8",
        "Corridor": "#868e96",
        "Balcony": "#fcc419",
    }
    
    @classmethod
    def get_scheme(cls, name: str = "default") -> ColorScheme:
        """
        Get a complete ColorScheme by name.
        
        Args:
            name: One of 'default', 'swiss', 'architectural', 'high_contrast'
            
        Returns:
            ColorScheme instance
        """
        palettes = {
            "default": cls.DEFAULT,
            "swiss": cls.SWISS,
            "architectural": cls.ARCHITECTURAL,
            "high_contrast": cls.HIGH_CONTRAST,
        }
        
        room_colors = palettes.get(name.lower(), cls.DEFAULT)
        return ColorScheme(room_colors=room_colors)
    
    @classmethod
    def get_color(cls, room_type: str, palette: str = "default") -> str:
        """
        Get color for a specific room type.
        
        Args:
            room_type: Room label
            palette: Palette name
            
        Returns:
            Hex color string
        """
        palettes = {
            "default": cls.DEFAULT,
            "swiss": cls.SWISS,
            "architectural": cls.ARCHITECTURAL,
            "high_contrast": cls.HIGH_CONTRAST,
        }
        
        colors = palettes.get(palette.lower(), cls.DEFAULT)
        return colors.get(room_type, "#dddddd")


# Convenience function
def get_room_color(room_type: str, palette: str = "default") -> str:
    """Get color for a room type from specified palette."""
    return RoomColors.get_color(room_type, palette)
