# ui/chat_widget.py
"""
Chat Tab Widget for RAG Qt Application
"""
from datetime import datetime
from typing import Dict, Optional
from PySide6.QtWidgets import *
from PySide6.QtCore import Signal, Qt, QEvent
from PySide6.QtGui import QKeySequence, QAction
from .toggle_switch import ToggleSwitch
from .chat.chat_display import ChatDisplay
from .chat.chat_exporter import ChatExportDialog, ChatExporter
from .icon_manager import get_icon, Icons


class ChatWidget(QWidget):
    """Chat interface widget with enhanced features"""
    
    ingestRequested = Signal()
    questionAsked = Signal(str, int, bool)  # question, topK, strict_mode
    
    def __init__(self, config_manager):
        super().__init__()
        self.config = config_manager
        self.chat_history = []  # Store messages for export
        self.isProcessing = False  # Flag to prevent double-sending
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout()
        
        # Top toolbar
        topToolbar = QHBoxLayout()
        
        # Ingest button with progress bar
        self.ingestBtn = QPushButton("Ingest Documents")
        self.ingestBtn.clicked.connect(lambda: self.ingestRequested.emit())
        self.ingestBtn.setToolTip("Index documents to vector store")
        self.ingestBtn.setStyleSheet("""
            QPushButton {
                background-color: #4caf50;
                color: black;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
                color: black;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        topToolbar.addWidget(self.ingestBtn)
        
        # Progress bar (initially hidden)
        self.progressBar = QProgressBar()
        self.progressBar.setTextVisible(True)
        self.progressBar.hide()  # Initially hidden
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
        model_label = QLabel("Model:")
        model_label.setStyleSheet("color: #000000;")
        topToolbar.addWidget(model_label)
        self.modelLabel = QLabel(self.config.get_current_model())
        self.modelLabel.setStyleSheet("font-weight: bold; color: #1976d2;")
        topToolbar.addWidget(self.modelLabel)
        
        separator_label = QLabel("  |  ")
        separator_label.setStyleSheet("color: #000000;")
        topToolbar.addWidget(separator_label)
        
        # topK setting with better labeling
        contextLabel = QLabel("Retrieve:")
        contextLabel.setToolTip(
            "Number of documents to retrieve from vector store.\n"
            "These will be reranked to select the best context."
        )
        topToolbar.addWidget(contextLabel)
        
        self.topKSpin = QSpinBox()
        self.topKSpin.setRange(1, 100)  # Increased max from 20 to 100
        # Get default from server config's retrieval.retrieve_k
        default_topk = 20
        try:
            server_config = self.config._load_config("config/config.yaml")
            if 'retrieval' in server_config and 'retrieve_k' in server_config['retrieval']:
                default_topk = server_config['retrieval']['retrieve_k']
        except:
            pass
        self.topKSpin.setValue(default_topk)  # Use retrieval.retrieve_k
        self.topKSpin.setToolTip(
            "How many documents to retrieve from vector store:\n"
            "• 5-10: Quick facts\n"
            "• 10-20: Standard (recommended)\n"
            "• 20-50: Comprehensive analysis\n"
            "• 50+: Exhaustive research"
        )
        self.topKSpin.valueChanged.connect(self.updateContextLabel)
        topToolbar.addWidget(self.topKSpin)
        
        # Context info label
        self.contextInfoLabel = QLabel("")
        self.updateContextLabel(self.topKSpin.value())
        topToolbar.addWidget(self.contextInfoLabel)
        
        # Clear button
        clearBtn = QPushButton("Clear Chat")
        clearBtn.clicked.connect(self.clearChat)
        topToolbar.addWidget(clearBtn)
        
        # Export button
        exportBtn = QPushButton("Export")
        exportBtn.setIcon(get_icon(Icons.SAVE))
        exportBtn.clicked.connect(self.exportChat)
        exportBtn.setToolTip("Export chat to Markdown file")
        exportBtn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: black;
                padding: 5px 10px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1976D2;
                color: black;
            }
        """)
        topToolbar.addWidget(exportBtn)
        
        # Chat display area
        self.chatDisplay = ChatDisplay(self.config)
        
        # Keep reference to markdown renderer for backward compatibility
        self.markdown_renderer = self.chatDisplay.markdown_renderer
        
        # Input area with mode selection
        inputLayout = QVBoxLayout()
        
        # Input field and controls row
        inputRowLayout = QHBoxLayout()
        
        self.inputField = QTextEdit()
        self.inputField.setMaximumHeight(100)
        self.inputField.setPlaceholderText("Ask a question... (Shift+Enter for new line, Enter to send)")
        
        inputRowLayout.addWidget(self.inputField)
        
        # Button controls group
        buttonGroup = QWidget()
        buttonLayout = QVBoxLayout()
        buttonLayout.setContentsMargins(0, 0, 0, 0)
        buttonLayout.setSpacing(2)
        
        # Send button
        self.sendBtn = QPushButton("Send")
        self.sendBtn.setIcon(get_icon(Icons.SEND))
        self.sendBtn.setMinimumHeight(35)  # Reduced from 40
        self.sendBtn.setMinimumWidth(70)   # Reduced from 80
        self.sendBtn.setStyleSheet("""
            QPushButton {
                background-color: #1976d2;
                color: black;
                font-weight: bold;
                border-radius: 4px;
                padding: 8px 12px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #1565c0;
                color: black;
            }
        """)
        buttonLayout.addWidget(self.sendBtn)
        
        # Compact mode toggle below send button using custom toggle switch
        toggleLayout = QHBoxLayout()
        toggleLayout.setSpacing(5)
        
        toggleLabel = QLabel("Strict")
        toggleLabel.setStyleSheet("font-size: 11px; color: #666;")
        toggleLayout.addWidget(toggleLabel)
        
        self.strictModeToggle = ToggleSwitch()
        self.strictModeToggle.setToolTip(
            "<b>OFF (Normal Mode):</b><br>"
            "Uses both RAG database and general AI knowledge.<br>"
            "Best for general questions and creative tasks.<br><br>"
            "<b>ON (Strict Mode):</b><br>"
            "Searches ONLY within your indexed documents.<br>"
            "Ensures answers come exclusively from your data.<br>"
            "No external knowledge or assumptions."
        )
        self.strictModeToggle.toggled.connect(self.onModeChanged)
        toggleLayout.addWidget(self.strictModeToggle)
        
        buttonLayout.addLayout(toggleLayout)
        
        buttonGroup.setLayout(buttonLayout)
        inputRowLayout.addWidget(buttonGroup)
        
        inputLayout.addLayout(inputRowLayout)
        
        # Connect signals
        self.sendBtn.clicked.connect(self.onSendMessage)
        
        # Setup Enter key handling
        self.inputField.installEventFilter(self)
        
        # Add all to layout
        layout.addLayout(topToolbar)
        layout.addWidget(self.chatDisplay)
        layout.addLayout(inputLayout)
        
        self.setLayout(layout)
    
    def updateContextLabel(self, value):
        """Update context info label based on value"""
        if value <= 5:
            info = "(Minimal)"
            color = "#ff9800"  # Orange
        elif value <= 20:
            info = "(Standard)"
            color = "#4caf50"  # Green
        elif value <= 50:
            info = "(Extended)"
            color = "#2196f3"  # Blue
        else:
            info = "(Maximum)"
            color = "#9c27b0"  # Purple
        
        self.contextInfoLabel.setText(info)
        self.contextInfoLabel.setStyleSheet(f"color: {color}; font-weight: bold;")
    
    def eventFilter(self, obj, event):
        """Handle Enter key in input field"""
        if obj == self.inputField and event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Return and not event.modifiers():
                self.onSendMessage()
                return True
        return super().eventFilter(obj, event)
    
    def onSendMessage(self):
        """Handle sending message"""
        # Check if already processing
        if self.isProcessing:
            return
        
        question = self.inputField.toPlainText().strip()
        if question:
            # Set processing flag and disable input
            self.isProcessing = True
            self.setInputEnabled(False)
            
            # Add user message
            self.addMessage("You", question)
            
            # Clear input field immediately after getting the text
            self.inputField.clear()
            
            # Emit signal to send question
            # For now, don't use strict mode
            self.questionAsked.emit(question, self.topKSpin.value(), False)
    
    def setInputEnabled(self, enabled: bool):
        """Enable/disable input controls during processing"""
        self.inputField.setEnabled(enabled)
        self.sendBtn.setEnabled(enabled)
        
        # Update processing flag
        self.isProcessing = not enabled
        
        if not enabled:
            # Change button to show processing
            self.sendBtn.setText("Generating...")
            self.sendBtn.setIcon(get_icon(Icons.CLOCK))
            self.sendBtn.setStyleSheet("""
                QPushButton {
                    background-color: #ffc107;
                    color: black;
                    font-weight: bold;
                    border-radius: 4px;
                    padding: 8px 12px;
                    font-size: 13px;
                }
            """)
        else:
            # Restore button based on mode
            self.onModeChanged(self.strictModeToggle.isChecked())
    
    def onModeChanged(self, checked):
        """Handle mode change - UI only for now"""
        if checked:
            self.sendBtn.setText("Send")
            self.sendBtn.setIcon(get_icon("lock"))
            self.sendBtn.setToolTip("Strict Mode: Only use RAG context (Coming soon)")
            self.sendBtn.setStyleSheet("""
                QPushButton {
                    background-color: #ff6b35;
                    color: black;
                    font-weight: bold;
                    border-radius: 4px;
                    padding: 8px 12px;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background-color: #ff5722;
                    color: black;
                }
            """)
        else:
            self.sendBtn.setText("Send")
            self.sendBtn.setIcon(get_icon(Icons.SEND))
            self.sendBtn.setToolTip("Normal Mode: RAG + General Knowledge")
            self.sendBtn.setStyleSheet("""
                QPushButton {
                    background-color: #1976d2;
                    color: black;
                    font-weight: bold;
                    border-radius: 4px;
                    padding: 8px 12px;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background-color: #1565c0;
                    color: black;
                }
            """)
    
    def addMessage(self, sender: str, message: str, metadata: Optional[Dict] = None):
        """Add a message to the chat display with markdown rendering"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Store in history for export
        self.chat_history.append({
            'sender': sender,
            'message': message,
            'timestamp': timestamp,
            'metadata': metadata
        })
        
        # Determine role for ChatDisplay
        role = 'user' if sender == "You" else 'assistant'
        
        # If it's an assistant message with metadata, append context info
        display_message = message
        if role == 'assistant' and metadata:
            # Add metadata info at the end of the message
            metadata_lines = []
            
            # Model info
            if 'model' in metadata:
                metadata_lines.append(f"Model: {metadata['model']}")
            
            # Context count - show both retrieved and reranked if available
            if 'retrievedCount' in metadata:
                retrieved = metadata['retrievedCount']
                metadata_lines.append(f"Retrieved: {retrieved}")
            
            if 'rerankedCount' in metadata:
                reranked = metadata['rerankedCount']
                metadata_lines.append(f"Reranked: {reranked}")
            
            # Always show final context count if ctxIds exist
            if 'ctxIds' in metadata and metadata['ctxIds']:
                ctx_count = len(metadata['ctxIds'])
                metadata_lines.append(f"Context Used: {ctx_count}")
            
            # Response time
            if 'latencyMs' in metadata:
                time_str = f"{metadata['latencyMs']}ms"
                if metadata['latencyMs'] > 1000:
                    time_str = f"{metadata['latencyMs']/1000:.1f}s"
                metadata_lines.append(f"Time: {time_str}")
            
            # Append metadata to message if we have any
            if metadata_lines:
                display_message = f"{message}\n\n---\n*{' | '.join(metadata_lines)}*"
        
        # Add message using ChatDisplay's enhanced rendering
        self.chatDisplay.add_message(role, display_message)
        
        # Auto-scroll to bottom
        if self.config.get("chat.auto_scroll", True):
            scrollbar = self.chatDisplay.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
    
    def clearChat(self):
        """Clear the chat display and history"""
        self.chatDisplay.clear_chat()  # Use ChatDisplay's clear method
        self.chat_history.clear()
    
    def exportChat(self):
        """Export chat to markdown file"""
        if not self.chat_history:
            QMessageBox.information(self, "No Messages", "No chat messages to export.")
            return
        
        # Show export dialog
        dialog = ChatExportDialog(self)
        dialog.exportRequested.connect(self.performExport)
        dialog.exec_()
    
    def performExport(self, filepath: str, options: dict):
        """Perform the actual export"""
        success = ChatExporter.export_to_markdown(
            self.chat_history,
            filepath,
            options
        )
        
        if success:
            reply = QMessageBox.information(
                self, "Export Successful",
                f"Chat exported to:\n{filepath}\n\nOpen file?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                import os
                import platform
                if platform.system() == "Windows":
                    os.startfile(filepath)
                elif platform.system() == "Darwin":  # macOS
                    os.system(f"open '{filepath}'")
                else:  # Linux
                    os.system(f"xdg-open '{filepath}'")
        else:
            QMessageBox.critical(self, "Export Failed", "Failed to export chat.")
    
    def setIngestionProgress(self, value: int, maximum: int = 100, text: str = ""):
        """Update ingestion progress bar"""
        if value == 0 and maximum > 0:
            # Starting ingestion
            self.ingestBtn.setEnabled(False)
            self.progressBar.setVisible(True)  # Ensure visibility
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
            self.progressBar.setVisible(True)  # Ensure visibility during update
            self.progressBar.setValue(value)
            if text:
                self.progressBar.setFormat(text)
            else:
                percentage = int((value / maximum) * 100) if maximum > 0 else 0
                self.progressBar.setFormat(f"{percentage}%")
    
    def hideIngestionProgress(self):
        """Hide the ingestion progress bar"""
        self.progressBar.setVisible(False)
        self.progressBar.setValue(0)
    
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
    
    def setContextChunks(self, value: int):
        """Set the topKs value from external source"""
        self.topKSpin.setValue(value)
    
    def getContextChunks(self) -> int:
        """Get the current topKs value"""
        return self.topKSpin.value()
