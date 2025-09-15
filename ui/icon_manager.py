"""
Icon utility module for the RAG application.
Provides functions to load and use SVG icons from the icons directory.
"""

import os
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtCore import QSize, QRect


class IconManager:
    """Manages icons for the application."""
    
    def __init__(self):
        self.icons_dir = os.path.join(os.path.dirname(__file__), 'icons')
        self._icon_cache = {}
    
    def get_icon(self, icon_name: str, size: int = 24, with_padding: bool = False) -> QIcon:
        """
        Get a QIcon from the icons directory.
        
        Args:
            icon_name: Name of the icon file (without .svg extension)
            size: Size of the icon in pixels
            with_padding: Add padding around icon for button spacing
            
        Returns:
            QIcon object
        """
        cache_key = f"{icon_name}_{size}_{with_padding}"
        
        if cache_key in self._icon_cache:
            return self._icon_cache[cache_key]
        
        icon_path = os.path.join(self.icons_dir, f"{icon_name}.svg")
        
        if not os.path.exists(icon_path):
            # Return empty icon if file doesn't exist
            return QIcon()
        
        # Create QIcon from SVG
        icon = QIcon()
        
        if with_padding:
            # Create larger pixmap with padding but transparent background
            padded_size = size + 8
            pixmap = QPixmap(QSize(padded_size, padded_size))
            pixmap.fill(QColor(0, 0, 0, 0))  # Fully transparent
            
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            
            # Render icon centered with padding
            renderer = QSvgRenderer(icon_path)
            icon_rect = QRect(4, 4, size, size)
            renderer.render(painter, icon_rect)
            
            painter.end()
        else:
            # Simple icon without padding
            pixmap = QPixmap(QSize(size, size))
            pixmap.fill(QColor(0, 0, 0, 0))  # Fully transparent
            
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            renderer = QSvgRenderer(icon_path)
            renderer.render(painter)
            painter.end()
        
        icon.addPixmap(pixmap)
        
        # Cache the icon
        self._icon_cache[cache_key] = icon
        
        return icon
    
    def get_pixmap(self, icon_name: str, size: int = 24) -> QPixmap:
        """
        Get a QPixmap from the icons directory.
        
        Args:
            icon_name: Name of the icon file (without .svg extension)
            size: Size of the icon in pixels
            
        Returns:
            QPixmap object
        """
        icon_path = os.path.join(self.icons_dir, f"{icon_name}.svg")
        
        if not os.path.exists(icon_path):
            return QPixmap()
        
        renderer = QSvgRenderer(icon_path)
        pixmap = QPixmap(QSize(size, size))
        pixmap.fill(QColor(0, 0, 0, 0))  # Transparent background
        
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        
        return pixmap


# Global instance
icon_manager = IconManager()


def get_icon(icon_name: str, size: int = 24, with_padding: bool = False) -> QIcon:
    """Convenience function to get an icon."""
    return icon_manager.get_icon(icon_name, size, with_padding)


def get_pixmap(icon_name: str, size: int = 24) -> QPixmap:
    """Convenience function to get a pixmap."""
    return icon_manager.get_pixmap(icon_name, size)


# Icon name constants for easy reference
class Icons:
    """Icon name constants."""
    SETTINGS = "settings"
    CPU = "cpu"
    ACTIVITY = "activity" 
    TARGET = "target"
    SCISSORS = "scissors"
    GLOBE = "globe"
    TOOL = "tool"
    SAVE = "save"
    SEND = "send"
    FILE = "file"
    FOLDER = "folder"
    REFRESH_CW = "refresh-cw"
    LIGHTBULB = "lightbulb"
    CLOCK = "clock"
    PLUS = "plus"
    MINUS = "minus"
    TRASH = "trash"
