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
            "Pipeline": ["query_expansion", "context_compression", "parsing", "prompt"],
            "Retrieval": ["retrieval", "policy"],  # reranking 제거 (중복)
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
                            elif isinstance(sub_value, list):
                                widget = QLineEdit()
                                widget.setText(", ".join(map(str, sub_value)))
                            else:
                                widget = QLineEdit()
                                widget.setText(str(sub_value))
                            
                            self.var_widgets[full_key] = widget
                            group_layout.addRow(f"{sub_key}:", widget)
            
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
    
    def getDefaultSystemVariables(self):
        """Get default system variables"""
        return {
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
                "topK": self.config.get("pipeline.retrieval.topK", None, "server")
            },
            "reranking": {
                "enabled": self.config.get("pipeline.reranking.enabled", True, "server"),
                "topK": self.config.get("pipeline.reranking.topK", None, "server")
            },
            "policy": {
                "defaultTopK": self.config.get("policy.defaultTopK", 10, "server"),
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
            elif isinstance(widget, QLineEdit):
                text = widget.text()
                # Try to parse as list if contains comma
                if "," in text:
                    value = [item.strip() for item in text.split(",")]
                else:
                    value = text
            else:
                continue
            
            # Save to config
            self.config.set(key, value, "server")
        
        QMessageBox.information(self, "Success", 
                              "System variables updated successfully!")
