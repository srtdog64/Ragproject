# ui/chat/chat_input.py
"""
Chat input area with send button and keyboard shortcuts
"""
from PySide6.QtWidgets import *
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QKeyEvent, QFont

class ChatInput(QWidget):
    """
    Chat input widget with text area and send button
    """
    
    messageSent = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.initUI()
    
    def initUI(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 5, 10, 10)
        
        # Input text area
        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText("Type your message here... (Shift+Enter for new line, Enter to send)")
        self.input_text.setMaximumHeight(100)
        self.input_text.setFont(QFont("Arial", 10))
        self.input_text.installEventFilter(self)
        
        # Send button
        self.send_btn = QPushButton("Send 📤")
        self.send_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: black;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.send_btn.clicked.connect(self.sendMessage)
        self.send_btn.setMinimumHeight(35)  # Reduced from 40
        
        layout.addWidget(self.input_text, 1)
        layout.addWidget(self.send_btn)
        
        self.setLayout(layout)
    
    def eventFilter(self, obj, event):
        """Handle Enter key for sending messages"""
        if obj == self.input_text and event.type() == event.KeyPress:
            key_event = QKeyEvent(event)
            if key_event.key() == Qt.Key_Return:
                if key_event.modifiers() & Qt.ShiftModifier:
                    # Shift+Enter: new line
                    return False
                else:
                    # Enter: send message
                    self.sendMessage()
                    return True
        return False
    
    def sendMessage(self):
        """Send the message"""
        message = self.input_text.toPlainText().strip()
        if message:
            self.messageSent.emit(message)
            self.input_text.clear()
    
    def setEnabled(self, enabled: bool):
        """Enable/disable input controls"""
        self.input_text.setEnabled(enabled)
        self.send_btn.setEnabled(enabled)
    
    def focusInput(self):
        """Set focus to input text area"""
        self.input_text.setFocus()
