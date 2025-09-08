# ui/options/variables_tab.py
"""
System Variables Configuration Tab
"""
from PySide6.QtWidgets import *
from PySide6.QtCore import Qt
import os


class VariablesTab(QWidget):
    """System variables configuration tab"""
    
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config = config_manager
        self.parent_widget = parent
        self.setupUI()
        
    def setupUI(self):
        """Setup the UI"""
        layout = QVBoxLayout()
        
        # Info
        info = QLabel("""
        <div style='background-color: #e3f2fd; padding: 10px; border-radius: 5px;'>
        <b>🔧 System Variables:</b><br>
        Fine-tune advanced system parameters for optimal performance.
        </div>
        """)
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # Create scroll area for variables
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()
        
        # Get system variables
        system_vars = self.getDefaultSystemVariables()
        
        # Organize by category
        categories = {
            "UI Settings": ["ui"],
            "Pipeline": ["query_expansion", "context_compression", "parsing", "prompt"],
            "Retrieval": ["retrieval", "policy"],
            "Ingestion": ["ingester", "documents"],
            "Storage": ["store"],
            "Logging": ["logging"],
            "CORS": ["cors"]
        }
        
        self.var_widgets = {}
        
        for category, keys in categories.items():
            group = QGroupBox(category)
            group_layout = QFormLayout()
            
            for key in keys:
                if key in system_vars:
                    var_data = system_vars[key]
                    
                    if isinstance(var_data, dict):
                        # Handle nested variables
                        for sub_key, sub_value in var_data.items():
                            full_key = f"{key}.{sub_key}"
                            
                            # Skip if already added or if it's reranking (duplicate)
                            if full_key == "reranking.enabled" or full_key == "reranking.context_chunk":
                                continue
                            
                            # Rename context_chunk to default_context_chunks for clarity
                            display_name = sub_key
                            if key == "policy" and sub_key == "defaultcontext_chunk":
                                display_name = "default_context_chunks"
                            elif sub_key == "context_chunk":
                                display_name = "context_chunks_max"
                            
                            if isinstance(sub_value, bool):
                                widget = QCheckBox()
                                widget.setChecked(sub_value)
                            elif isinstance(sub_value, (int, float)):
                                if isinstance(sub_value, float):
                                    widget = QDoubleSpinBox()
                                    widget.setRange(0, 100)
                                    widget.setDecimals(2)
                                    widget.setValue(sub_value)
                                else:
                                    widget = QSpinBox()
                                    widget.setRange(0, 100000)
                                    widget.setValue(sub_value)
                            elif key == "store" and sub_key == "persist_directory":
                                # For persist_directory, create folder browser widget
                                widget = self.createStorageWidget(sub_value)
                            elif isinstance(sub_value, list):
                                # For watched_folders, create a special widget
                                if sub_key == "watched_folders":
                                    widget = self.createFolderWidget(sub_value)
                                else:
                                    widget = QLineEdit()
                                    widget.setText(", ".join(map(str, sub_value)))
                            else:
                                widget = QLineEdit()
                                widget.setText(str(sub_value))
                            
                            self.var_widgets[full_key] = widget
                            group_layout.addRow(f"{display_name}:", widget)
            
            group.setLayout(group_layout)
            scroll_layout.addWidget(group)
        
        # Apply button
        apply_btn = QPushButton("Apply Variables")
        apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #607D8B;
                color: white;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #455A64;
            }
        """)
        apply_btn.clicked.connect(self.applyVariables)
        scroll_layout.addWidget(apply_btn)
        
        scroll_layout.addStretch()
        scroll_widget.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        
        layout.addWidget(scroll_area)
        self.setLayout(layout)
    
    def createFolderWidget(self, folders):
        """Create a widget for folder selection with browse button"""
        container = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # List widget for folders
        self.folder_list = QListWidget()
        self.folder_list.setMaximumHeight(100)
        for folder in folders:
            self.folder_list.addItem(folder)
        
        # Buttons
        btn_layout = QVBoxLayout()
        
        add_btn = QPushButton("Add...")
        add_btn.clicked.connect(self.addFolder)
        btn_layout.addWidget(add_btn)
        
        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(self.removeFolder)
        btn_layout.addWidget(remove_btn)
        
        btn_layout.addStretch()
        
        layout.addWidget(self.folder_list)
        layout.addLayout(btn_layout)
        
        container.setLayout(layout)
        return container
    
    def addFolder(self):
        """Add a folder to watched folders list"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Folder to Watch",
            "",
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        
        if folder:
            # Check if folder already exists
            items = [self.folder_list.item(i).text() for i in range(self.folder_list.count())]
            if folder not in items:
                self.folder_list.addItem(folder)
    
    def removeFolder(self):
        """Remove selected folder from list"""
        current_item = self.folder_list.currentItem()
        if current_item:
            self.folder_list.takeItem(self.folder_list.row(current_item))
    
    def createStorageWidget(self, current_path):
        """Create a widget for storage path selection with browse button"""
        container = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Path input
        self.storage_path = QLineEdit()
        self.storage_path.setText(current_path or "./chroma_db")
        
        # Browse button
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browseStoragePath)
        
        layout.addWidget(self.storage_path)
        layout.addWidget(browse_btn)
        
        container.setLayout(layout)
        return container
    
    def browseStoragePath(self):
        """Browse for storage directory"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Storage Directory",
            self.storage_path.text() if hasattr(self, 'storage_path') else "",
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        
        if folder and hasattr(self, 'storage_path'):
            self.storage_path.setText(folder)
    
    def getDefaultSystemVariables(self):
        """Get default system variables"""
        return {
            "ui": {
                "font_size": self.config.get("ui.font_size", 10, "qt"),
                "code_font_size": self.config.get("ui.code_font_size", 10, "qt"),
                "default_context_chunks": self.config.get("ui.defaults.top_k", 10, "qt"),
                "auto_scroll": self.config.get("chat.auto_scroll", True, "qt")
            },
            "query_expansion": {
                "enabled": self.config.get("pipeline.query_expansion.enabled", True, "server"),
                "expansions": self.config.get("pipeline.query_expansion.expansions", 0, "server")
            },
            "context_compression": {
                "enabled": self.config.get("pipeline.context_compression.enabled", True, "server")
            },
            "parsing": {
                "enabled": self.config.get("pipeline.parsing.enabled", True, "server"),
                "format": self.config.get("pipeline.parsing.format", "markdown-qa", "server")
            },
            "prompt": {
                "system_message": self.config.get("pipeline.prompt.system_message", "Be precise and helpful.", "server"),
                "system_hint": self.config.get("pipeline.prompt.system_hint", "You are a helpful RAG assistant.", "server")
            },
            "retrieval": {
                "enabled": self.config.get("pipeline.retrieval.enabled", True, "server"),
                "context_chunks_max": self.config.get("pipeline.retrieval.context_chunk", None, "server")  # Renamed for clarity
            },
            "policy": {
                "default_context_chunks": self.config.get("policy.defaultcontext_chunk", 10, "server"),
                "maxContextChars": self.config.get("policy.maxContextChars", 12000, "server")
            },
            "ingester": {
                "batch_size": self.config.get("ingester.batch_size", 100, "server"),
                "max_parallel": self.config.get("ingester.max_parallel", 8, "server")
            },
            "documents": {
                "watched_folders": self.config.get("documents.watched_folders", [], "server")
            },
            "store": {
                "type": self.config.get("store.type", "chroma", "server"),
                "collection_name": self.config.get("store.collection_name", "rag_documents", "server"),
                "persist_directory": self.config.get("store.persist_directory", "./chroma_db", "server")
            },
            "logging": {
                "level": self.config.get("logging.level", "INFO", "server"),
                "file": self.config.get("logging.file", None, "server"),
                "format": self.config.get("logging.format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s", "server")
            },
            "cors": {
                "allow_origins": self.config.get("cors.allow_origins", ["http://localhost:*"], "server"),
                "allow_methods": self.config.get("cors.allow_methods", ["*"], "server"),
                "allow_headers": self.config.get("cors.allow_headers", ["*"], "server"),
                "allow_credentials": self.config.get("cors.allow_credentials", True, "server")
            }
        }
    
    def applyVariables(self):
        """Apply system variables"""
        for key, widget in self.var_widgets.items():
            if isinstance(widget, QCheckBox):
                value = widget.isChecked()
            elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                value = widget.value()
            elif isinstance(widget, QWidget):  # Custom widgets
                # Check if it's our custom folder widget
                if hasattr(self, 'folder_list') and key == "documents.watched_folders":
                    value = [self.folder_list.item(i).text() 
                            for i in range(self.folder_list.count())]
                elif hasattr(self, 'storage_path') and key == "store.persist_directory":
                    value = self.storage_path.text()
                else:
                    continue
            elif isinstance(widget, QLineEdit):
                text = widget.text()
                # Try to parse as list if contains comma
                if "," in text:
                    value = [item.strip() for item in text.split(",")]
                else:
                    value = text
            else:
                continue
            
            # Handle renamed variables
            save_key = key
            if "default_context_chunks" in key:
                if key == "ui.default_context_chunks":
                    save_key = "ui.defaults.top_k"
                elif key == "policy.default_context_chunks":
                    save_key = "policy.defaultcontext_chunk"
            elif "context_chunks_max" in key:
                save_key = key.replace("context_chunks_max", "context_chunk")
            
            # Save to correct config source (qt or server)
            if key.startswith("ui."):
                self.config.set(save_key, value, "qt")
            else:
                self.config.set(save_key, value, "server")
        
        QMessageBox.information(self, "Success", 
                              "System variables updated successfully!")
