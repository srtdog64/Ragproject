# ui/toggle_switch.py
"""
Custom Toggle Switch Widget for PySide6
"""
from PySide6.QtCore import Qt, QRect, QPropertyAnimation, Signal, Property, QEasingCurve
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor, QBrush, QPen


class ToggleSwitch(QWidget):
    """Custom toggle switch widget"""
    
    toggled = Signal(bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(60, 30)
        
        self._checked = False
        self._pos = 2
        
        # Animation for smooth transition
        self.animation = QPropertyAnimation(self, b"position")
        self.animation.setEasingCurve(QEasingCurve.InOutCubic)
        self.animation.setDuration(200)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Background
        if self._checked:
            bg_color = QColor("#4CAF50")  # Green when on
        else:
            bg_color = QColor("#cccccc")  # Gray when off
            
        painter.setBrush(QBrush(bg_color))
        painter.setPen(QPen(Qt.NoPen))
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 
                                self.height() / 2, self.height() / 2)
        
        # Circle (handle)
        painter.setBrush(QBrush(QColor("white")))
        painter.drawEllipse(QRect(self._pos, 2, 26, 26))
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.toggle()
            
    def toggle(self):
        """Toggle the switch state"""
        self._checked = not self._checked
        
        # Animate position
        if self._checked:
            self.animation.setEndValue(32)  # Move to right
        else:
            self.animation.setEndValue(2)   # Move to left
            
        self.animation.start()
        self.toggled.emit(self._checked)
        
    def isChecked(self):
        """Return the current state"""
        return self._checked
        
    def setChecked(self, checked):
        """Set the state programmatically"""
        if self._checked != checked:
            self.toggle()
            
    @Property(int)
    def position(self):
        return self._pos
        
    @position.setter
    def position(self, pos):
        self._pos = pos
        self.update()
