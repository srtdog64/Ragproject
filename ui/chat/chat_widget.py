# ui/chat/chat_widget.py
"""
Main chat widget that combines all chat components
"""
from PySide6.QtWidgets import *
from PySide6.QtCore import Signal, Qt
from .chat_history import ChatHistory
from .chat_input import ChatInput
from .chat_worker import RagWorkerThread

class ChatWidget(QWidget):
    """
    Main chat widget combining history, input, and worker thread
    """
    
    def __init__(self, config_manager):
        super().__init__()
        self.config = config_manager
        self.worker = None
        self.current_question = None
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Title
        title = QLabel("RAG Chat Interface")
        title.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                padding: 10px;
                background-color: #f0f0f0;
                border-bottom: 2px solid #ddd;
            }
        """)
        layout.addWidget(title)
        
        # Chat history
        self.history = ChatHistory()
        self.history.retryRequested.connect(self.retryQuestion)
        layout.addWidget(self.history, 1)
        
        # Status bar
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("""
            QLabel {
                padding: 5px;
                background-color: #f9f9f9;
                border-top: 1px solid #ddd;
                font-size: 11px;
                color: #666;
            }
        """)
        layout.addWidget(self.status_label)
        
        # Input area
        self.input_widget = ChatInput()
        self.input_widget.messageSent.connect(self.sendMessage)
        layout.addWidget(self.input_widget)
        
        # Control buttons
        controls = QHBoxLayout()
        controls.setContentsMargins(10, 5, 10, 5)
        
        clear_btn = QPushButton("🗑️ Clear Chat")
        clear_btn.clicked.connect(self.clearChat)
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff6b6b;
                color: black;
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
            }
        """)
        
        export_btn = QPushButton("Export Chat")
        export_btn.clicked.connect(self.exportChat)
        export_btn.setStyleSheet("""
            QPushButton {
                background-color: #4ecdc4;
                color: black;
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
            }
        """)
        
        controls.addWidget(clear_btn)
        controls.addWidget(export_btn)
        controls.addStretch()
        
        # K value selector
        k_label = QLabel("Top K:")
        self.k_spinner = QSpinBox()
        self.k_spinner.setRange(1, 20)
        self.k_spinner.setValue(5)
        self.k_spinner.setToolTip("Number of relevant chunks to retrieve")
        
        controls.addWidget(k_label)
        controls.addWidget(self.k_spinner)
        
        layout.addLayout(controls)
        
        self.setLayout(layout)
    
    def sendMessage(self, message: str):
        """Send a message to the RAG system"""
        if not message.strip():
            return
        
        # Add user message to history
        self.history.addMessage(message, is_user=True)
        
        # Store current question for potential retry
        self.current_question = message
        
        # Disable input while processing
        self.input_widget.setEnabled(False)
        self.status_label.setText("Processing...")
        
        # Create and start worker thread
        self.worker = RagWorkerThread(self.config.get_server_url())
        self.worker.setQuestion(message, self.k_spinner.value())
        
        # Connect signals
        self.worker.responseReceived.connect(self.handleResponse)
        self.worker.errorOccurred.connect(self.handleError)
        self.worker.progressUpdate.connect(self.updateStatus)
        self.worker.retryAvailable.connect(self.enableRetry)
        
        # Start processing
        self.worker.start()
    
    def handleResponse(self, response: str):
        """Handle successful response from RAG system"""
        # Add assistant response to history
        self.history.addMessage(response, is_user=False)
        
        # Re-enable input
        self.input_widget.setEnabled(True)
        self.status_label.setText("Ready")
        
        # Clean up worker
        if self.worker:
            self.worker.quit()
            self.worker = None
    
    def handleError(self, error_msg: str):
        """Handle error from RAG system"""
        # Add error message to history (will be shown with retry button)
        self.history.addMessage(
            f"Error: {error_msg}",
            is_user=False,
            show_retry=True,
            original_question=self.current_question
        )
        
        # Re-enable input
        self.input_widget.setEnabled(True)
        self.status_label.setText("Error occurred - retry available")
        
        # Clean up worker
        if self.worker:
            self.worker.quit()
            self.worker = None
    
    def enableRetry(self, question: str):
        """Enable retry for a failed question"""
        # Already handled in handleError with show_retry=True
        pass
    
    def retryQuestion(self, question: str):
        """Retry a failed question"""
        self.status_label.setText("Retrying...")
        
        # Update the last message to show retrying
        self.history.updateLastMessage("⏳ Retrying...", success=True)
        
        # Disable input while retrying
        self.input_widget.setEnabled(False)
        
        # Create and start worker thread for retry
        self.worker = RagWorkerThread(self.config.get_server_url())
        self.worker.setQuestion(question, self.k_spinner.value())
        
        # Connect signals for retry
        self.worker.responseReceived.connect(self.handleRetryResponse)
        self.worker.errorOccurred.connect(self.handleRetryError)
        self.worker.progressUpdate.connect(self.updateStatus)
        
        # Start retry
        self.worker.start()
    
    def handleRetryResponse(self, response: str):
        """Handle successful retry response"""
        # Update the last message with the successful response
        self.history.updateLastMessage(response, success=True)
        
        # Re-enable input
        self.input_widget.setEnabled(True)
        self.status_label.setText("Retry successful")
        
        # Clean up worker
        if self.worker:
            self.worker.quit()
            self.worker = None
    
    def handleRetryError(self, error_msg: str):
        """Handle failed retry"""
        # Update the last message to show it still failed
        self.history.updateLastMessage(
            f"Retry failed: {error_msg}",
            success=False
        )
        
        # Re-enable input
        self.input_widget.setEnabled(True)
        self.status_label.setText("Retry failed")
        
        # Clean up worker
        if self.worker:
            self.worker.quit()
            self.worker = None
    
    def updateStatus(self, status: str):
        """Update status label"""
        self.status_label.setText(status)
    
    def clearChat(self):
        """Clear chat history"""
        reply = QMessageBox.question(
            self, "Clear Chat",
            "Are you sure you want to clear the chat history?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.history.clearHistory()
            self.status_label.setText("Chat cleared")
    
    def exportChat(self):
        """Export chat history to file"""
        from datetime import datetime
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Chat",
            f"chat_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "JSON Files (*.json);;Text Files (*.txt)"
        )
        
        if filename:
            history = self.history.getHistory()
            
            try:
                if filename.endswith('.json'):
                    import json
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(history, f, indent=2, ensure_ascii=False)
                else:
                    with open(filename, 'w', encoding='utf-8') as f:
                        for msg in history:
                            role = "User" if msg['is_user'] else "Assistant"
                            f.write(f"[{msg['timestamp']}] {role}: {msg['text']}\n\n")
                
                QMessageBox.information(self, "Success", f"Chat exported to {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export chat: {str(e)}")
