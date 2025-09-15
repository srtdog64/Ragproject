# ui/logs_widget.py
"""
Logs Tab Widget for RAG Qt Application  
"""
from datetime import datetime
from pathlib import Path
from PySide6.QtWidgets import *
from PySide6.QtCore import Signal
from PySide6.QtGui import QTextCursor, QColor, QTextCharFormat


class LogsWidget(QWidget):
    """Enhanced logging widget with filtering and export capabilities"""
    
    def __init__(self, config_manager):
        super().__init__()
        self.config = config_manager
        self.logBuffer = []
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout()
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        # Log level filter
        toolbar.addWidget(QLabel("Level:"))
        self.levelCombo = QComboBox()
        self.levelCombo.addItems(["ALL", "DEBUG", "INFO", "WARNING", "ERROR"])
        self.levelCombo.setCurrentText("INFO")
        self.levelCombo.currentTextChanged.connect(self.filterLogs)
        toolbar.addWidget(self.levelCombo)
        
        # Search
        toolbar.addWidget(QLabel("Search:"))
        self.searchEdit = QLineEdit()
        self.searchEdit.setPlaceholderText("Filter logs...")
        self.searchEdit.textChanged.connect(self.filterLogs)
        toolbar.addWidget(self.searchEdit)
        
        toolbar.addStretch()
        
        # Auto-scroll checkbox
        self.autoScrollCheck = QCheckBox("Auto-scroll")
        self.autoScrollCheck.setChecked(True)
        toolbar.addWidget(self.autoScrollCheck)
        
        # Clear button
        clearBtn = QPushButton("Clear")
        clearBtn.clicked.connect(self.clearLogs)
        toolbar.addWidget(clearBtn)
        
        # Export button
        exportBtn = QPushButton("Export")
        exportBtn.clicked.connect(self.exportLogs)
        toolbar.addWidget(exportBtn)
        
        layout.addLayout(toolbar)
        
        # Log display
        self.logDisplay = QTextEdit()
        self.logDisplay.setReadOnly(True)
        self.logDisplay.setStyleSheet("""
            QTextEdit {
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                font-size: 12px;
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #333;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.logDisplay)
        
        # Status bar
        self.statusLabel = QLabel("0 log entries")
        self.statusLabel.setStyleSheet("color: #666; padding: 5px;")
        layout.addWidget(self.statusLabel)
        
        self.setLayout(layout)
    
    def log(self, message: str, level: str = "INFO"):
        """Add a log entry"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        
        # Store in buffer
        entry = {
            "timestamp": timestamp,
            "level": level,
            "message": message
        }
        self.logBuffer.append(entry)
        
        # Limit buffer size
        max_entries = self.config.get("logging.max_log_lines", 1000)
        if len(self.logBuffer) > max_entries:
            self.logBuffer = self.logBuffer[-max_entries:]
        
        # Add to display
        self.addLogEntry(entry)
        
        # Update status
        self.updateStatus()
    
    def addLogEntry(self, entry: dict):
        """Add a log entry to the display with color coding"""
        level = entry['level']
        timestamp = entry['timestamp']
        message = entry['message']
        
        # Color coding by level
        colors = {
            "DEBUG": "#808080",
            "INFO": "#00b4d8",
            "WARNING": "#ffc107",
            "ERROR": "#f44336",
            "SUCCESS": "#397B06"
        }
        
        color = colors.get(level, "#d4d4d4")
        
        # Format the log entry
        html = f"""
        <span style="color: #666;">[{timestamp}]</span>
        <span style="color: {color}; font-weight: bold;"> [{level:7}]</span>
        <span style="color: #d4d4d4;"> {message}</span>
        """
        
        # Check if entry matches filter
        if self.matchesFilter(entry):
            cursor = self.logDisplay.textCursor()
            cursor.movePosition(QTextCursor.End)
            cursor.insertHtml(html + "<br>")
            
            # Auto-scroll if enabled
            if self.autoScrollCheck.isChecked():
                scrollbar = self.logDisplay.verticalScrollBar()
                scrollbar.setValue(scrollbar.maximum())
    
    def matchesFilter(self, entry: dict) -> bool:
        """Check if log entry matches current filters"""
        # Level filter
        level_filter = self.levelCombo.currentText()
        if level_filter != "ALL":
            levels = ["DEBUG", "INFO", "WARNING", "ERROR"]
            try:
                entry_idx = levels.index(entry['level'])
                filter_idx = levels.index(level_filter)
                if entry_idx < filter_idx:
                    return False
            except ValueError:
                pass
        
        # Search filter
        search_text = self.searchEdit.text().lower()
        if search_text:
            if search_text not in entry['message'].lower():
                return False
        
        return True
    
    def filterLogs(self):
        """Re-filter all logs based on current filters"""
        self.logDisplay.clear()
        
        for entry in self.logBuffer:
            self.addLogEntry(entry)
        
        self.updateStatus()
    
    def clearLogs(self):
        """Clear all logs"""
        reply = QMessageBox.question(
            self, "Clear Logs",
            "Clear all log entries?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.logBuffer.clear()
            self.logDisplay.clear()
            self.updateStatus()
    
    def exportLogs(self):
        """Export logs to file"""
        if not self.logBuffer:
            QMessageBox.warning(self, "No Logs", "No logs to export")
            return
        
        fileName, _ = QFileDialog.getSaveFileName(
            self, "Export Logs",
            f"rag_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "Text Files (*.txt);;Log Files (*.log)"
        )
        
        if fileName:
            try:
                with open(fileName, 'w', encoding='utf-8') as f:
                    for entry in self.logBuffer:
                        f.write(f"[{entry['timestamp']}] [{entry['level']:7}] {entry['message']}\n")
                
                QMessageBox.information(
                    self, "Success",
                    f"Exported {len(self.logBuffer)} log entries to {fileName}"
                )
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export logs: {str(e)}")
    
    def updateStatus(self):
        """Update status label"""
        total = len(self.logBuffer)
        
        # Count by level
        level_counts = {}
        for entry in self.logBuffer:
            level = entry['level']
            level_counts[level] = level_counts.get(level, 0) + 1
        
        # Build status text
        status_text = f"{total} log entries"
        if level_counts:
            details = []
            for level in ["ERROR", "WARNING", "INFO", "DEBUG"]:
                if level in level_counts:
                    details.append(f"{level_counts[level]} {level.lower()}")
            
            if details:
                status_text += f" ({', '.join(details)})"
        
        self.statusLabel.setText(status_text)
    
    # Convenience methods for different log levels
    def debug(self, message: str):
        """Log debug message"""
        self.log(message, "DEBUG")
    
    def info(self, message: str):
        """Log info message"""
        self.log(message, "INFO")
    
    def warning(self, message: str):
        """Log warning message"""
        self.log(message, "WARNING")
    
    def error(self, message: str):
        """Log error message"""
        self.log(message, "ERROR")
    
    def success(self, message: str):
        """Log success message"""
        self.log(message, "SUCCESS")
