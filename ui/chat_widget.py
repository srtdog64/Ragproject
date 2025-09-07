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
from .chat.markdown_renderer import MarkdownRenderer
from .chat.chat_exporter import ChatExportDialog, ChatExporter


class ChatWidget(QWidget):
    """Chat interface widget with enhanced features"""
    
    ingestRequested = Signal()
    questionAsked = Signal(str, int, bool)  # question, topK, strict_mode
    
    def __init__(self, config_manager):
        super().__init__()
        self.config = config_manager
        self.markdown_renderer = MarkdownRenderer()
        self.chat_history = []  # Store messages for export
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
        topToolbar.addWidget(QLabel("Model:"))
        self.modelLabel = QLabel(self.config.get_current_model())
        self.modelLabel.setStyleSheet("font-weight: bold; color: #1976d2;")
        topToolbar.addWidget(self.modelLabel)
        
        topToolbar.addWidget(QLabel("  |  "))
        
        # Context Chunks setting with better labeling
        contextLabel = QLabel("Context Chunks:")
        contextLabel.setToolTip(
            "Number of document chunks to include as context.\n"
            "Higher values = more context but slower responses."
        )
        topToolbar.addWidget(contextLabel)
        
        self.topKSpin = QSpinBox()
        self.topKSpin.setRange(1, 100)  # Increased max from 20 to 100
        self.topKSpin.setValue(self.config.get("ui.defaults.top_k", 10))  # Default to 10
        self.topKSpin.setToolTip(
            "How many document chunks to retrieve:\n"
            "• 1-5: Quick facts\n"
            "• 5-20: Standard (recommended)\n"
            "• 20-50: Complex analysis\n"
            "• 50+: Comprehensive research"
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
        exportBtn = QPushButton("💾 Export")
        exportBtn.clicked.connect(self.exportChat)
        exportBtn.setToolTip("Export chat to Markdown file")
        exportBtn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 5px 10px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        topToolbar.addWidget(exportBtn)
        
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
        self.sendBtn = QPushButton("🚀 Send")
        self.sendBtn.setMinimumHeight(40)
        self.sendBtn.setMinimumWidth(80)
        self.sendBtn.setStyleSheet("""
            QPushButton {
                background-color: #1976d2;
                color: white;
                font-weight: bold;
                border-radius: 4px;
                padding: 8px 12px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #1565c0;
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
        question = self.inputField.toPlainText().strip()
        if question:
            # For now, don't use strict mode
            self.questionAsked.emit(question, self.topKSpin.value(), False)
            self.inputField.clear()
    
    def onModeChanged(self, checked):
        """Handle mode change - UI only for now"""
        if checked:
            self.sendBtn.setText("🔒 Send")
            self.sendBtn.setToolTip("Strict Mode: Only use RAG context (Coming soon)")
            self.sendBtn.setStyleSheet("""
                QPushButton {
                    background-color: #ff6b35;
                    color: white;
                    font-weight: bold;
                    border-radius: 4px;
                    padding: 8px 12px;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background-color: #ff5722;
                }
            """)
        else:
            self.sendBtn.setText("🚀 Send")
            self.sendBtn.setToolTip("Normal Mode: RAG + General Knowledge")
            self.sendBtn.setStyleSheet("""
                QPushButton {
                    background-color: #1976d2;
                    color: white;
                    font-weight: bold;
                    border-radius: 4px;
                    padding: 8px 12px;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background-color: #1565c0;
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
        
        # Render message based on sender
        if sender == "Assistant":
            # Use markdown renderer for assistant messages
            rendered_message = self.markdown_renderer.render(message)
        else:
            # Use plain text renderer for user messages
            rendered_message = self.markdown_renderer.render_plain_text(message)
        
        # Format message with HTML
        html = f"""
        <div style="margin: 10px 0;">
            <div style="display: flex; align-items: center; margin-bottom: 5px;">
                <span style="font-size: 20px; margin-right: 8px;">{avatar}</span>
                <b style="color: {color}; font-size: 15px;">{sender}</b>
                <span style="color: #888; margin-left: 10px; font-size: 12px;">[{timestamp}]</span>
            </div>
            <div style="padding: 12px; background-color: {bg_color}; 
                        border-radius: 8px; border-left: 3px solid {color};">
                {rendered_message}
            </div>
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
        """Clear the chat display and history"""
        self.chatDisplay.clear()
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
