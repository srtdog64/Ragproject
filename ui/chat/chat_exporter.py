# ui/chat/chat_exporter.py
"""
Chat Export Dialog and Functionality
Export chat history to Markdown format
"""
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from PySide6.QtWidgets import *
from PySide6.QtCore import Qt, Signal
from ..icon_manager import get_icon, Icons


class ChatExportDialog(QDialog):
    """Dialog for exporting chat history"""
    
    exportRequested = Signal(str, dict)  # filepath, options
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Export Chat History")
        self.setModal(True)
        self.setMinimumWidth(400)   # Reduced from 500
        self.setMinimumHeight(300)  # Reduced from 400
        self.initUI()
        
    def initUI(self):
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("Export Chat to Markdown")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Export options
        options_group = QGroupBox("Export Options")
        options_layout = QVBoxLayout()
        
        # Include metadata
        self.include_metadata = QCheckBox("Include metadata (timestamps, model info)")
        self.include_metadata.setChecked(True)
        options_layout.addWidget(self.include_metadata)
        
        # Include system messages
        self.include_system = QCheckBox("Include system messages")
        self.include_system.setChecked(False)
        options_layout.addWidget(self.include_system)
        
        # Format as conversation
        self.format_conversation = QCheckBox("Format as conversation (Q&A style)")
        self.format_conversation.setChecked(True)
        options_layout.addWidget(self.format_conversation)
        
        # Include code blocks
        self.preserve_code = QCheckBox("Preserve code block formatting")
        self.preserve_code.setChecked(True)
        options_layout.addWidget(self.preserve_code)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        # File selection
        file_group = QGroupBox("Save Location")
        file_layout = QVBoxLayout()
        
        # Filename
        filename_layout = QHBoxLayout()
        filename_layout.addWidget(QLabel("Filename:"))
        
        self.filename_edit = QLineEdit()
        default_name = f"chat_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        self.filename_edit.setText(default_name)
        filename_layout.addWidget(self.filename_edit)
        
        file_layout.addLayout(filename_layout)
        
        # Directory
        dir_layout = QHBoxLayout()
        dir_layout.addWidget(QLabel("Directory:"))
        
        self.dir_edit = QLineEdit()
        self.dir_edit.setText(str(Path.home() / "Documents"))
        self.dir_edit.setReadOnly(True)
        dir_layout.addWidget(self.dir_edit)
        
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_directory)
        dir_layout.addWidget(browse_btn)
        
        file_layout.addLayout(dir_layout)
        
        # Full path preview
        self.path_preview = QLabel()
        self.path_preview.setStyleSheet("color: #666; font-size: 11px; margin-top: 5px;")
        self.update_path_preview()
        file_layout.addWidget(self.path_preview)
        
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)
        
        # Preview area
        preview_group = QGroupBox("Preview")
        preview_layout = QVBoxLayout()
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setMaximumHeight(150)
        self.preview_text.setPlainText("# Chat Export\n\n## Conversation\n\n**You:** Hello\n\n**Assistant:** Hi! How can I help you today?\n\n...")
        preview_layout.addWidget(self.preview_text)
        
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        export_btn = QPushButton("Export")
        export_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: black;
                padding: 6px 20px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        export_btn.clicked.connect(self.export_chat)
        button_layout.addWidget(export_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Connect signals
        self.filename_edit.textChanged.connect(self.update_path_preview)
        
    def browse_directory(self):
        """Browse for export directory"""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Export Directory",
            self.dir_edit.text()
        )
        
        if directory:
            self.dir_edit.setText(directory)
            self.update_path_preview()
    
    def update_path_preview(self):
        """Update the full path preview"""
        full_path = Path(self.dir_edit.text()) / self.filename_edit.text()
        self.path_preview.setText(f"Full path: {full_path}")
    
    def export_chat(self):
        """Handle export button click"""
        # Get full path
        full_path = Path(self.dir_edit.text()) / self.filename_edit.text()
        
        # Ensure .md extension
        if not full_path.suffix == '.md':
            full_path = full_path.with_suffix('.md')
        
        # Gather options
        options = {
            'include_metadata': self.include_metadata.isChecked(),
            'include_system': self.include_system.isChecked(),
            'format_conversation': self.format_conversation.isChecked(),
            'preserve_code': self.preserve_code.isChecked()
        }
        
        # Emit signal and close
        self.exportRequested.emit(str(full_path), options)
        self.accept()


class ChatExporter:
    """Handles chat export functionality"""
    
    @staticmethod
    def export_to_markdown(
        messages: List[Dict],
        filepath: str,
        options: Dict
    ) -> bool:
        """
        Export chat messages to markdown file
        
        Args:
            messages: List of message dictionaries with 'sender', 'message', 'timestamp', etc.
            filepath: Path to save the markdown file
            options: Export options dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Build markdown content
            content = ChatExporter._build_markdown(messages, options)
            
            # Write to file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return True
            
        except Exception as e:
            print(f"Export failed: {e}")
            return False
    
    @staticmethod
    def _build_markdown(messages: List[Dict], options: Dict) -> str:
        """
        Build markdown content from messages
        
        Args:
            messages: List of message dictionaries
            options: Export options
            
        Returns:
            Markdown formatted string
        """
        lines = []
        
        # Header
        lines.append("# Chat Export")
        lines.append("")
        lines.append(f"*Exported on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # Messages
        if options.get('format_conversation', True):
            lines.append("## Conversation")
            lines.append("")
            
            for msg in messages:
                sender = msg.get('sender', 'Unknown')
                message = msg.get('message', '')
                timestamp = msg.get('timestamp', '')
                
                # Skip system messages if not included
                if sender == 'System' and not options.get('include_system', False):
                    continue
                
                # Format sender
                if sender == 'You':
                    lines.append(f"### You")
                elif sender == 'Assistant':
                    lines.append(f"### Assistant")
                else:
                    lines.append(f"### {sender}")
                
                # Add timestamp if included
                if options.get('include_metadata', True) and timestamp:
                    lines.append(f"*{timestamp}*")
                    lines.append("")
                
                # Add message
                if options.get('preserve_code', True):
                    # Preserve code blocks
                    lines.append(message)
                else:
                    # Simple text
                    lines.append(message.replace('```', ''))
                
                lines.append("")
                lines.append("---")
                lines.append("")
        else:
            # Simple format
            lines.append("## Messages")
            lines.append("")
            
            for msg in messages:
                sender = msg.get('sender', 'Unknown')
                message = msg.get('message', '')
                
                if sender == 'System' and not options.get('include_system', False):
                    continue
                
                lines.append(f"**{sender}:** {message}")
                lines.append("")
        
        # Footer
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("*Generated by RAG System*")
        
        return '\n'.join(lines)
