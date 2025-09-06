# ui/chat_widget.py
"""
Chat Tab Widget for RAG Qt Application
"""
from datetime import datetime
from typing import Dict, Optional
from PySide6.QtWidgets import *
from PySide6.QtCore import Signal, Qt, QEvent
from PySide6.QtGui import QKeySequence


class ChatWidget(QWidget):
    """Chat interface widget with enhanced features"""
    
    ingestRequested = Signal()
    questionAsked = Signal(str, int)  # question, topK
    
    def __init__(self, config_manager):
        super().__init__()
        self.config = config_manager
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout()
        
        # Top toolbar
        topToolbar = QHBoxLayout()
        
        # Ingest button with progress bar
        self.ingestBtn = QPushButton("📥 Ingest Documents")
        self.ingestBtn.clicked.connect(lambda: self.ingestRequested.emit())
        self.ingestBtn.setToolTip("Index documents to vector store")
        self.ingestBtn.setStyleSheet("""
            QPushButton {
                background-color: #4caf50;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        topToolbar.addWidget(self.ingestBtn)
        
        # Progress bar (initially hidden)
        self.progressBar = QProgressBar()
        self.progressBar.setTextVisible(True)
        self.progressBar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ddd;
                border-radius: 4px;
                text-align: center;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #4caf50;
                border-radius: 3px;
            }
        """)
        self.progressBar.hide()
        topToolbar.addWidget(self.progressBar)
        
        topToolbar.addStretch()
        
        # Model selector
        topToolbar.addWidget(QLabel("Model:"))
        self.modelLabel = QLabel(self.config.get_current_model())
        self.modelLabel.setStyleSheet("font-weight: bold; color: #1976d2;")
        topToolbar.addWidget(self.modelLabel)
        
        topToolbar.addWidget(QLabel("  |  "))
        
        # Top K setting
        topToolbar.addWidget(QLabel("Top K:"))
        self.topKSpin = QSpinBox()
        self.topKSpin.setRange(1, 20)
        self.topKSpin.setValue(self.config.get("ui.defaults.top_k", 5))
        self.topKSpin.setToolTip("Number of context chunks to retrieve")
        topToolbar.addWidget(self.topKSpin)
        
        # Clear button
        clearBtn = QPushButton("Clear Chat")
        clearBtn.clicked.connect(self.clearChat)
        topToolbar.addWidget(clearBtn)
        
        # Chat display area
        self.chatDisplay = QTextBrowser()
        self.chatDisplay.setOpenExternalLinks(True)
        self.chatDisplay.setStyleSheet("""
            QTextBrowser {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 10px;
                font-family: 'Segoe UI', 'Arial', sans-serif;
                font-size: 14px;
            }
        """)
        
        # Input area
        inputLayout = QHBoxLayout()
        
        self.inputField = QTextEdit()
        self.inputField.setMaximumHeight(100)
        self.inputField.setPlaceholderText("Ask a question... (Shift+Enter for new line, Enter to send)")
        
        # Send button
        self.sendBtn = QPushButton("Send 📤")
        self.sendBtn.setMinimumHeight(60)
        self.sendBtn.setStyleSheet("""
            QPushButton {
                background-color: #1976d2;
                color: white;
                font-weight: bold;
                border-radius: 4px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
        """)
        
        inputLayout.addWidget(self.inputField)
        inputLayout.addWidget(self.sendBtn)
        
        # Connect signals
        self.sendBtn.clicked.connect(self.onSendMessage)
        
        # Setup Enter key handling
        self.inputField.installEventFilter(self)
        
        # Add all to layout
        layout.addLayout(topToolbar)
        layout.addWidget(self.chatDisplay)
        layout.addLayout(inputLayout)
        
        self.setLayout(layout)
    
    def eventFilter(self, obj, event):
        """Handle Enter key in input field"""
        if obj == self.inputField and event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Return and not event.modifiers():
                self.onSendMessage()
                return True
        return super().eventFilter(obj, event)
    
    def onSendMessage(self):
        """Handle sending message"""
        question = self.inputField.toPlainText().strip()
        if question:
            self.questionAsked.emit(question, self.topKSpin.value())
            self.inputField.clear()
    
    def addMessage(self, sender: str, message: str, metadata: Optional[Dict] = None):
        """Add a message to the chat display"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Determine styling based on sender
        if sender == "You":
            avatar = "👤"
            color = "#1e88e5"
            bg_color = "#e3f2fd"
        elif sender == "Assistant":
            avatar = "🤖"
            color = "#43a047"
            bg_color = "#f1f8e9"
        else:
            avatar = "ℹ️"
            color = "#666"
            bg_color = "#f5f5f5"
        
        # Format message with HTML
        html = f"""
        <div style="margin: 10px 0;">
            <div style="display: flex; align-items: center; margin-bottom: 5px;">
                <span style="font-size: 20px; margin-right: 8px;">{avatar}</span>
                <b style="color: {color}; font-size: 15px;">{sender}</b>
                <span style="color: #888; margin-left: 10px; font-size: 12px;">[{timestamp}]</span>
            </div>
            <div style="margin-left: 35px; padding: 12px; background-color: {bg_color}; 
                        border-radius: 8px; border-left: 3px solid {color};">
                <div style="white-space: pre-wrap; word-wrap: break-word;">{message}</div>
        """
        
        # Add metadata if present
        if metadata:
            html += '<div style="margin-top: 10px; padding-top: 10px; border-top: 1px solid #e0e0e0;">'
            html += '<span style="color: #666; font-size: 12px;">'
            
            if metadata.get("model"):
                html += f'🧠 Model: {metadata["model"]} | '
            if metadata.get("ctxIds"):
                html += f'📚 Contexts: {len(metadata["ctxIds"])} | '
            if metadata.get("latencyMs"):
                html += f'⏱️ Time: {metadata["latencyMs"]}ms'
            
            html += '</span></div>'
        
        html += """
            </div>
        </div>
        """
        
        self.chatDisplay.append(html)
        
        # Auto-scroll to bottom
        if self.config.get("chat.auto_scroll", True):
            scrollbar = self.chatDisplay.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
    
    def clearChat(self):
        """Clear the chat display"""
        self.chatDisplay.clear()
    
    def setIngestionProgress(self, value: int, maximum: int = 100, text: str = ""):
        """Update ingestion progress bar"""
        if value == 0 and maximum > 0:
            # Starting ingestion
            self.ingestBtn.setEnabled(False)
            self.progressBar.show()
            self.progressBar.setMaximum(maximum)
            self.progressBar.setValue(0)
            self.progressBar.setFormat(text if text else "%p%")
        elif value >= maximum:
            # Ingestion complete
            self.ingestBtn.setEnabled(True)
            self.progressBar.hide()
            self.progressBar.setValue(0)
        else:
            # Update progress
            self.progressBar.setValue(value)
            if text:
                self.progressBar.setFormat(text)
            else:
                percentage = int((value / maximum) * 100) if maximum > 0 else 0
                self.progressBar.setFormat(f"{percentage}%")
    
    def updateModelLabel(self, provider: str, model: str):
        """Update the model label"""
        self.modelLabel.setText(f"{provider}: {model}")
        
        # Color code by provider
        colors = {
            "openai": "#10a37f",
            "gemini": "#4285f4",
            "claude": "#7c3aed"
        }
        color = colors.get(provider, "#666")
        self.modelLabel.setStyleSheet(f"font-weight: bold; color: {color};")
