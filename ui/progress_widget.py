"""
Progress Bar Widget for Async Operations
Handles progress tracking for long-running tasks
"""
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
import requests
import json
import time
from typing import Optional, Dict, Any

class AsyncProgressDialog(QDialog):
    """Progress dialog for async operations"""
    
    # Signals
    taskCompleted = Signal(dict)
    taskFailed = Signal(str)
    progressUpdated = Signal(int, int, str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.task_id: Optional[str] = None
        self.base_url = "http://localhost:7001"
        self.polling_timer = QTimer()
        self.polling_timer.timeout.connect(self.poll_status)
        
        self.setupUI()
        
    def setupUI(self):
        """Setup the progress dialog UI"""
        self.setWindowTitle("Processing...")
        self.setModal(True)
        self.setMinimumWidth(400)  # Reduced from 500
        
        layout = QVBoxLayout()
        
        # Title label
        self.titleLabel = QLabel("Starting task...")
        self.titleLabel.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(self.titleLabel)
        
        # Status label
        self.statusLabel = QLabel("Initializing...")
        self.statusLabel.setStyleSheet("color: #666;")
        layout.addWidget(self.statusLabel)
        
        # Progress bar
        self.progressBar = QProgressBar()
        self.progressBar.setMinimum(0)
        self.progressBar.setMaximum(100)
        layout.addWidget(self.progressBar)
        
        # Details text
        self.detailsText = QTextEdit()
        self.detailsText.setReadOnly(True)
        self.detailsText.setMaximumHeight(150)
        self.detailsText.setStyleSheet("font-family: monospace; font-size: 10px;")
        layout.addWidget(self.detailsText)
        
        # Buttons
        buttonLayout = QHBoxLayout()
        
        self.cancelButton = QPushButton("Cancel")
        self.cancelButton.clicked.connect(self.cancel_task)
        buttonLayout.addWidget(self.cancelButton)
        
        self.hideButton = QPushButton("Hide")
        self.hideButton.clicked.connect(self.hide)
        self.hideButton.setEnabled(False)  # Disabled until task completes
        buttonLayout.addWidget(self.hideButton)
        
        layout.addLayout(buttonLayout)
        
        self.setLayout(layout)
    
    def start_task(self, task_type: str, task_id: str, title: str = "Processing"):
        """Start monitoring a task"""
        self.task_id = task_id
        self.titleLabel.setText(title)
        self.statusLabel.setText(f"Task ID: {task_id[:8]}...")
        self.progressBar.setValue(0)
        self.detailsText.clear()
        self.cancelButton.setEnabled(True)
        self.hideButton.setEnabled(False)
        
        self.log(f"Starting {task_type} task: {task_id}")
        
        # Start polling (less frequent to avoid timeout)
        self.polling_timer.start(1000)  # Poll every 1 second instead of 500ms
        
    def poll_status(self):
        """Poll the task status"""
        if not self.task_id:
            return
            
        try:
            # Longer timeout for status checks
            response = requests.get(
                f"{self.base_url}/api/ingest/status/{self.task_id}",
                timeout=30  # 30 seconds timeout
            )
            
            if response.status_code == 200:
                status = response.json()
                self.update_progress(status)
            else:
                self.log(f"Status check failed: {response.status_code}")
                
        except Exception as e:
            self.log(f"Error polling status: {e}")
    
    def update_progress(self, status: Dict[str, Any]):
        """Update progress based on status"""
        task_status = status.get("status", "unknown")
        progress = status.get("progress", 0)
        total = status.get("total", 100)
        current_item = status.get("current_item", "")
        percentage = status.get("progress_percentage", 0)
        
        # Update UI
        self.progressBar.setValue(int(percentage))
        self.statusLabel.setText(f"{current_item} ({progress}/{total})")
        
        # Emit signal for external handling
        self.progressUpdated.emit(progress, total, current_item)
        
        # Check completion status
        if task_status == "completed":
            self.handle_completion(status)
        elif task_status == "failed":
            self.handle_failure(status)
        elif task_status == "cancelled":
            self.handle_cancellation()
    
    def handle_completion(self, status: Dict[str, Any]):
        """Handle task completion"""
        self.polling_timer.stop()
        
        result = status.get("result", {})
        self.statusLabel.setText("✅ Task completed successfully!")
        self.progressBar.setValue(100)
        
        # Log results
        self.log("Task completed!")
        self.log(f"Result: {json.dumps(result, indent=2)}")
        
        # Enable hide button, disable cancel
        self.cancelButton.setEnabled(False)
        self.hideButton.setEnabled(True)
        
        # Emit completion signal
        self.taskCompleted.emit(result)
        
        # Auto-close after 2 seconds
        QTimer.singleShot(2000, self.accept)
    
    def handle_failure(self, status: Dict[str, Any]):
        """Handle task failure"""
        self.polling_timer.stop()
        
        error = status.get("error", "Unknown error")
        self.statusLabel.setText(f"❌ Task failed: {error}")
        
        self.log(f"Task failed: {error}")
        
        # Enable hide button, disable cancel
        self.cancelButton.setEnabled(False)
        self.hideButton.setEnabled(True)
        
        # Emit failure signal
        self.taskFailed.emit(error)
    
    def handle_cancellation(self):
        """Handle task cancellation"""
        self.polling_timer.stop()
        
        self.statusLabel.setText("⚠️ Task cancelled")
        self.log("Task was cancelled")
        
        # Enable hide button, disable cancel
        self.cancelButton.setEnabled(False)
        self.hideButton.setEnabled(True)
    
    def cancel_task(self):
        """Cancel the current task"""
        if not self.task_id:
            return
            
        try:
            response = requests.delete(
                f"{self.base_url}/api/ingest/tasks/{self.task_id}",
                timeout=5
            )
            
            if response.status_code == 200:
                self.log("Cancellation request sent")
                self.statusLabel.setText("Cancelling...")
            else:
                self.log(f"Failed to cancel: {response.status_code}")
                
        except Exception as e:
            self.log(f"Error cancelling task: {e}")
    
    def log(self, message: str):
        """Add message to details log"""
        timestamp = time.strftime("%H:%M:%S")
        self.detailsText.append(f"[{timestamp}] {message}")
        # Auto-scroll to bottom
        scrollbar = self.detailsText.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())


class IngestProgressWidget(QWidget):
    """Widget for managing document ingestion with progress tracking"""
    
    # Signals
    ingestionCompleted = Signal(dict)
    ingestionFailed = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.base_url = "http://localhost:7001"
        self.current_dialog: Optional[AsyncProgressDialog] = None
        
        self.setupUI()
    
    def setupUI(self):
        """Setup the UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Progress info label
        self.infoLabel = QLabel("No active ingestion")
        self.infoLabel.setStyleSheet("padding: 5px;")
        layout.addWidget(self.infoLabel)
        
        # Inline progress bar (for embedding in other widgets)
        self.progressBar = QProgressBar()
        self.progressBar.setVisible(False)
        layout.addWidget(self.progressBar)
        
        self.setLayout(layout)
    
    def start_ingestion(self, documents: list, batch_size: int = 10) -> Optional[str]:
        """
        Start document ingestion and show progress dialog
        
        Returns:
            Task ID if successful, None otherwise
        """
        try:
            # Send ingestion request
            response = requests.post(
                f"{self.base_url}/api/ingest",
                json={
                    "documents": documents,
                    "batch_size": batch_size
                },
                timeout=30  # Increased timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                task_id = result.get("task_id")
                
                # Create and show progress dialog
                self.current_dialog = AsyncProgressDialog(self)
                self.current_dialog.taskCompleted.connect(self.on_task_completed)
                self.current_dialog.taskFailed.connect(self.on_task_failed)
                self.current_dialog.progressUpdated.connect(self.update_inline_progress)
                
                self.current_dialog.start_task(
                    "ingestion",
                    task_id,
                    f"Ingesting {len(documents)} documents"
                )
                
                # Show dialog
                self.current_dialog.show()
                
                # Update inline widgets
                self.infoLabel.setText(f"Ingesting {len(documents)} documents...")
                self.progressBar.setVisible(True)
                self.progressBar.setValue(0)
                
                return task_id
                
            else:
                QMessageBox.critical(
                    self,
                    "Ingestion Failed",
                    f"Failed to start ingestion: {response.text}"
                )
                return None
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to start ingestion: {str(e)}"
            )
            return None
    
    def update_inline_progress(self, current: int, total: int, message: str):
        """Update inline progress indicators"""
        if total > 0:
            percentage = int((current / total) * 100)
            self.progressBar.setValue(percentage)
            self.infoLabel.setText(f"{message} ({current}/{total})")
    
    def on_task_completed(self, result: dict):
        """Handle task completion"""
        total_chunks = result.get("total_chunks", 0)
        processed_docs = result.get("processed_documents", 0)
        
        self.infoLabel.setText(f"✅ Ingested {processed_docs} documents ({total_chunks} chunks)")
        self.progressBar.setValue(100)
        
        # Hide progress bar after delay
        QTimer.singleShot(3000, lambda: self.progressBar.setVisible(False))
        
        # Emit completion signal
        self.ingestionCompleted.emit(result)
    
    def on_task_failed(self, error: str):
        """Handle task failure"""
        self.infoLabel.setText(f"❌ Ingestion failed: {error}")
        self.progressBar.setVisible(False)
        
        # Emit failure signal
        self.ingestionFailed.emit(error)
    
    def get_active_tasks(self) -> list:
        """Get list of active ingestion tasks"""
        try:
            response = requests.get(
                f"{self.base_url}/api/ingest/tasks/active",
                timeout=5
            )
            
            if response.status_code == 200:
                return response.json()
            return []
            
        except Exception:
            return []


if __name__ == "__main__":
    # Test the progress widget
    import sys
    app = QApplication(sys.argv)
    
    # Test window
    window = QMainWindow()
    window.setWindowTitle("Progress Widget Test")
    
    # Create progress widget
    progress_widget = IngestProgressWidget()
    
    # Add test button
    test_button = QPushButton("Test Ingestion")
    
    def test_ingestion():
        # Create test documents
        docs = [
            {
                "id": f"test-{i}",
                "title": f"Test Document {i}",
                "source": "test",
                "text": f"This is test document {i}"
            }
            for i in range(10)
        ]
        
        # Start ingestion
        task_id = progress_widget.start_ingestion(docs)
        if task_id:
            print(f"Started ingestion task: {task_id}")
    
    test_button.clicked.connect(test_ingestion)
    
    # Layout
    central_widget = QWidget()
    layout = QVBoxLayout()
    layout.addWidget(progress_widget)
    layout.addWidget(test_button)
    central_widget.setLayout(layout)
    
    window.setCentralWidget(central_widget)
    window.resize(600, 400)
    window.show()
    
    sys.exit(app.exec())
