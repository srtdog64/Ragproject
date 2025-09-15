# ui/chat/chat_history.py
"""
Chat history display area with scrollable message list
"""
from PySide6.QtWidgets import *
from PySide6.QtCore import Signal, Qt
from .chat_message import ChatMessage

class ChatHistory(QScrollArea):
    """
    Scrollable chat history area
    """
    
    retryRequested = Signal(str)  # Propagate retry requests
    
    def __init__(self):
        super().__init__()
        self.messages = []
        self.initUI()
    
    def initUI(self):
        # Set up scroll area
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setStyleSheet("""
            QScrollArea {
                background-color: gray;
                border: 1px solid #ddd;
                border-radius: 5px;
            }
        """)
        
        # Container widget for messages
        self.container = QWidget()
        self.layout = QVBoxLayout()
        self.layout.setAlignment(Qt.AlignTop)
        self.layout.setSpacing(10)
        self.layout.setContentsMargins(10, 10, 10, 10)
        
        # Welcome message
        self.showWelcomeMessage()
        
        self.container.setLayout(self.layout)
        self.setWidget(self.container)
    
    def showWelcomeMessage(self):
        """Show welcome message when chat is empty"""
        welcome = QLabel("""
        <div style='text-align: center; color: #666; padding: 20px;'>
            <h2>Welcome to RAG Chat!</h2>
            <p>Ask questions about your ingested documents.</p>
            <p style='font-size: 12px; color: #999;'>
                Tip: Make sure to ingest documents first from the Documents tab.
            </p>
        </div>
        """)
        welcome.setWordWrap(True)
        welcome.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(welcome)
        self.welcome_widget = welcome
    
    def addMessage(self, text: str, is_user: bool = True, 
                   show_retry: bool = False, original_question: str = None):
        """
        Add a new message to the chat history
        
        Args:
            text: Message text
            is_user: True if user message
            show_retry: Show retry button for failed messages
            original_question: Original question for retry
        
        Returns:
            The created ChatMessage widget
        """
        # Remove welcome message if it exists
        if hasattr(self, 'welcome_widget'):
            self.welcome_widget.deleteLater()
            del self.welcome_widget
        
        # Create message widget
        message = ChatMessage(
            text=text,
            is_user=is_user,
            show_retry=show_retry,
            original_question=original_question
        )
        
        # Connect retry signal
        if show_retry:
            message.retryRequested.connect(self.retryRequested.emit)
        
        # Add to layout and list
        self.layout.addWidget(message)
        self.messages.append(message)
        
        # Scroll to bottom after adding message
        QTimer.singleShot(100, self.scrollToBottom)
        
        return message
    
    def updateLastMessage(self, text: str, success: bool = True):
        """
        Update the last message (useful for updating after retry)
        
        Args:
            text: New message text
            success: Whether the operation was successful
        """
        if self.messages and not self.messages[-1].is_user:
            self.messages[-1].updateMessage(text, success)
    
    def scrollToBottom(self):
        """Scroll to the bottom of the chat"""
        scrollbar = self.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def clearHistory(self):
        """Clear all messages"""
        for message in self.messages:
            message.deleteLater()
        self.messages.clear()
        self.showWelcomeMessage()
    
    def getHistory(self) -> list:
        """
        Get chat history as list of dicts
        
        Returns:
            List of message dictionaries
        """
        history = []
        for message in self.messages:
            history.append({
                'text': message.text,
                'is_user': message.is_user,
                'timestamp': message.timestamp
            })
        return history

from PySide6.QtCore import QTimer
