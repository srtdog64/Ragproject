# ui/chat/chat_message.py
"""
Individual chat message component with retry functionality
"""
from PySide6.QtWidgets import *
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont, QTextCursor
from datetime import datetime

class ChatMessage(QWidget):
    """
    Individual chat message bubble with retry button for failed messages
    """
    
    retryRequested = Signal(str)  # Emit the original question for retry
    
    def __init__(self, text: str, is_user: bool = True, timestamp: str = None, 
                 show_retry: bool = False, original_question: str = None):
        """
        Initialize chat message
        
        Args:
            text: Message text
            is_user: True if user message, False if assistant
            timestamp: Message timestamp
            show_retry: Show retry button for failed messages
            original_question: Original question for retry (if applicable)
        """
        super().__init__()
        self.text = text
        self.is_user = is_user
        self.timestamp = timestamp or datetime.now().strftime("%H:%M")
        self.show_retry = show_retry
        self.original_question = original_question
        self.initUI()
    
    def initUI(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)
        
        # Message container
        message_container = QWidget()
        message_layout = QVBoxLayout()
        message_layout.setContentsMargins(0, 0, 0, 0)
        message_layout.setSpacing(2)
        
        # Header with role and timestamp
        header = QLabel(f"{'You' if self.is_user else 'Assistant'} • {self.timestamp}")
        header.setStyleSheet("""
            color: #666;
            font-size: 11px;
            margin-bottom: 2px;
        """)
        message_layout.addWidget(header)
        
        # Message text
        self.text_widget = QTextEdit()
        self.text_widget.setPlainText(self.text)
        self.text_widget.setReadOnly(True)
        self.text_widget.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Style based on sender
        if self.is_user:
            self.text_widget.setStyleSheet("""
                QTextEdit {
                    background-color: #DCF8C6;
                    border: 1px solid #B8E994;
                    border-radius: 10px;
                    padding: 8px;
                    font-size: 13px;
                }
            """)
        else:
            if self.show_retry:
                # Failed message style
                self.text_widget.setStyleSheet("""
                    QTextEdit {
                        background-color: #FFE4E1;
                        border: 1px solid #FFA07A;
                        border-radius: 10px;
                        padding: 8px;
                        font-size: 13px;
                        color: #8B0000;
                    }
                """)
            else:
                # Normal assistant message
                self.text_widget.setStyleSheet("""
                    QTextEdit {
                        background-color: #F0F0F0;
                        border: 1px solid #D0D0D0;
                        border-radius: 10px;
                        padding: 8px;
                        font-size: 13px;
                    }
                """)
        
        # Auto-resize text widget
        self.text_widget.document().contentsChanged.connect(self._adjustHeight)
        self._adjustHeight()
        
        message_layout.addWidget(self.text_widget)
        
        # Retry button for failed messages
        if self.show_retry and not self.is_user:
            retry_container = QHBoxLayout()
            retry_container.setContentsMargins(0, 5, 0, 0)
            
            retry_btn = QPushButton("Retry")
            retry_btn.setStyleSheet("""
                QPushButton {
                    background-color: #FF6B6B;
                    color: black;
                    border: none;
                    border-radius: 4px;
                    padding: 5px 10px;
                    font-size: 12px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #FF5252;
                }
            """)
            retry_btn.clicked.connect(self._onRetryClicked)
            retry_btn.setMaximumWidth(80)
            
            retry_container.addWidget(retry_btn)
            retry_container.addStretch()
            
            message_layout.addLayout(retry_container)
        
        message_container.setLayout(message_layout)
        
        # Align message based on sender
        if self.is_user:
            layout.addStretch()
            layout.addWidget(message_container, 0)
            message_container.setMaximumWidth(500)
        else:
            layout.addWidget(message_container, 0)
            layout.addStretch()
            message_container.setMaximumWidth(600)
        
        self.setLayout(layout)
    
    def _adjustHeight(self):
        """Adjust text widget height based on content"""
        doc_height = self.text_widget.document().size().height()
        margins = self.text_widget.contentsMargins()
        height = doc_height + margins.top() + margins.bottom() + 16  # Extra padding
        self.text_widget.setFixedHeight(min(int(height), 300))  # Max height 300px
    
    def _onRetryClicked(self):
        """Handle retry button click"""
        if self.original_question:
            self.retryRequested.emit(self.original_question)
    
    def updateMessage(self, new_text: str, success: bool = True):
        """
        Update message text (useful for updating failed messages after retry)
        
        Args:
            new_text: New message text
            success: Whether the retry was successful
        """
        self.text = new_text
        self.text_widget.setPlainText(new_text)
        self.show_retry = not success
        
        # Update style based on success
        if not self.is_user:
            if success:
                self.text_widget.setStyleSheet("""
                    QTextEdit {
                        background-color: #F0F0F0;
                        border: 1px solid #D0D0D0;
                        border-radius: 10px;
                        padding: 8px;
                        font-size: 13px;
                    }
                """)
            else:
                self.text_widget.setStyleSheet("""
                    QTextEdit {
                        background-color: #FFE4E1;
                        border: 1px solid #FFA07A;
                        border-radius: 10px;
                        padding: 8px;
                        font-size: 13px;
                        color: #8B0000;
                    }
                """)
