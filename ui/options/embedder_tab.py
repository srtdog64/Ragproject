# ui/options/embedder_tab.py
"""
Embedder Model Configuration Tab
"""
from PySide6.QtWidgets import *
from PySide6.QtCore import Qt


class EmbedderTab(QWidget):
    """Embedder configuration tab"""
    
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
        <b>🧠 Embedding Model Configuration:</b><br>
        Select the embedding model for semantic search.
        Different models offer different trade-offs between speed and quality.
        </div>
        """)
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # Embedder models configuration
        self.embedder_models = [
            {
                "name": "HuggingFace Sentence Transformers",
                "type": "huggingface",
                "models": [
                    ("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2", "Multilingual MiniLM L12 v2 (384d) ⭐ CURRENT"),
                    ("sentence-transformers/all-MiniLM-L6-v2", "All MiniLM L6 v2 (384d) - English Fast"),
                    ("sentence-transformers/all-mpnet-base-v2", "All MPNet Base v2 (768d) - English Quality"),
                    ("sentence-transformers/paraphrase-MiniLM-L6-v2", "Paraphrase MiniLM L6 v2 (384d)"),
                    ("sentence-transformers/paraphrase-multilingual-mpnet-base-v2", "Multilingual MPNet Base v2 (768d)"),
                    ("sentence-transformers/distiluse-base-multilingual-cased-v2", "DistilUSE Multilingual v2 (512d)"),
                    ("sentence-transformers/LaBSE", "LaBSE (768d) - 109 Languages"),
                    ("sentence-transformers/xlm-r-100langs-bert-base-nli-stsb-mean-tokens", "XLM-R 100langs (768d)"),
                    ("intfloat/e5-small-v2", "E5 Small v2 (384d) - Fast"),
                    ("intfloat/e5-base-v2", "E5 Base v2 (768d) - Balanced"),
                    ("intfloat/e5-large-v2", "E5 Large v2 (1024d) - Quality"),
                    ("jhgan/ko-sroberta-multitask", "Korean RoBERTa (768d) - Korean optimized"),
                    ("multi-qa-MiniLM-L6-cos-v1", "QA MiniLM (384d) - QA optimized"),
                    ("BAAI/bge-small-en-v1.5", "BGE Small English v1.5 (384d)"),
                    ("BAAI/bge-base-en-v1.5", "BGE Base English v1.5 (768d)"),
                    ("BAAI/bge-large-en-v1.5", "BGE Large English v1.5 (1024d)")
                ]
            },
            {
                "name": "Semantic (E5 Models)",
                "type": "semantic",
                "models": [
                    ("multilingual-e5-large", "Multilingual E5 Large (1024d) - Best quality"),
                    ("multilingual-e5-base", "Multilingual E5 Base (768d) - Balanced"),
                    ("multilingual-e5-small", "Multilingual E5 Small (384d) - Fast"),
                    ("multilingual-small", "Multilingual MiniLM (384d) - Fastest"),
                    ("all-MiniLM-L6-v2", "English MiniLM (384d) - English only"),
                    ("all-mpnet-base-v2", "English MPNet (768d) - High quality")
                ]
            },
            {
                "name": "OpenAI API",
                "type": "openai",
                "models": [
                    ("text-embedding-3-large", "Ada-3 Large (3072d) - Best quality"),
                    ("text-embedding-3-small", "Ada-3 Small (1536d) - Cost effective"),
                    ("text-embedding-ada-002", "Ada-2 (1536d) - Legacy")
                ]
            },
            {
                "name": "Cohere API",
                "type": "cohere",
                "models": [
                    ("embed-english-v3.0", "English v3 (1024d)"),
                    ("embed-multilingual-v3.0", "Multilingual v3 (1024d)"),
                    ("embed-english-light-v3.0", "English Light v3 (384d)"),
                    ("embed-multilingual-light-v3.0", "Multilingual Light v3 (384d)")
                ]
            }
        ]
        
        # Current embedder display
        current_layout = QHBoxLayout()
        current_layout.addWidget(QLabel("Current Embedder:"))
        
        current_type = self.config.get("embedder.type", "semantic", "server")
        current_model = self.config.get("embedder.model", "multilingual-small", "server")
        self.currentEmbedderLabel = QLabel(f"{current_type}: {current_model}")
        self.currentEmbedderLabel.setStyleSheet("font-weight: bold; color: #4CAF50;")
        current_layout.addWidget(self.currentEmbedderLabel)
        current_layout.addStretch()
        layout.addLayout(current_layout)
        
        # Embedder selection
        for embedder_type in self.embedder_models:
            group = QGroupBox(embedder_type["name"])
            group_layout = QVBoxLayout()
            
            for model_key, model_desc in embedder_type["models"]:
                radio = QRadioButton(model_desc)
                radio.setProperty("embedder_type", embedder_type["type"])
                radio.setProperty("model_key", model_key)
                
                # Check if this is the current model
                if embedder_type["type"] == current_type and model_key == current_model:
                    radio.setChecked(True)
                
                group_layout.addWidget(radio)
            
            group.setLayout(group_layout)
            layout.addWidget(group)
        
        # Cache directory
        cache_group = QGroupBox("Cache Settings")
        cache_layout = QVBoxLayout()
        
        cache_info = QLabel("""
        <small style='color: #666;'>
        Cache directory for downloaded models (leave empty for default)
        </small>
        """)
        
        self.cache_input = QLineEdit()
        self.cache_input.setPlaceholderText("Default: ~/.cache/sentence_transformers")
        cache_dir = self.config.get("embedder.cache_dir", "", "server")
        if cache_dir:
            self.cache_input.setText(cache_dir)
        
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browseCacheDir)
        
        cache_row = QHBoxLayout()
        cache_row.addWidget(self.cache_input)
        cache_row.addWidget(browse_btn)
        
        cache_layout.addLayout(cache_row)
        cache_layout.addWidget(cache_info)
        cache_group.setLayout(cache_layout)
        layout.addWidget(cache_group)
        
        # Apply button
        apply_btn = QPushButton("Apply Embedder")
        apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        apply_btn.clicked.connect(self.applyEmbedder)
        layout.addWidget(apply_btn)
        
        # Warning about changing embedder
        warning = QLabel("""
        <div style='background-color: #fff3e0; padding: 10px; border-radius: 5px; margin-top: 10px;'>
        <b>⚠️ Warning:</b> Changing the embedder requires re-ingesting all documents
        as embeddings are model-specific.
        </div>
        """)
        warning.setWordWrap(True)
        layout.addWidget(warning)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def browseCacheDir(self):
        """Browse for cache directory"""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Cache Directory",
            self.cache_input.text() or ""
        )
        if directory:
            self.cache_input.setText(directory)
    
    def applyEmbedder(self):
        """Apply selected embedder"""
        selected_type = None
        selected_model = None
        
        # Find selected radio button
        for widget in self.findChildren(QRadioButton):
            if widget.isChecked():
                selected_type = widget.property("embedder_type")
                selected_model = widget.property("model_key")
                break
        
        if not selected_type or not selected_model:
            QMessageBox.warning(self, "No Selection", 
                              "Please select an embedding model")
            return
        
        # Confirm if changing embedder
        current_type = self.config.get("embedder.type", "semantic", "server")
        current_model = self.config.get("embedder.model", "multilingual-small", "server")
        
        if current_type != selected_type or current_model != selected_model:
            reply = QMessageBox.question(
                self, "Confirm Change",
                "Changing the embedder requires re-ingesting all documents.\n"
                "Are you sure you want to continue?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                return
        
        # Save settings
        self.config.set("embedder.type", selected_type, "server")
        self.config.set("embedder.model", selected_model, "server")
        
        # Save cache dir if specified
        cache_dir = self.cache_input.text().strip()
        if cache_dir:
            self.config.set("embedder.cache_dir", cache_dir, "server")
        
        # Update display
        self.currentEmbedderLabel.setText(f"{selected_type}: {selected_model}")
        
        QMessageBox.information(self, "Success", 
                              f"Embedder changed to: {selected_type}/{selected_model}\n"
                              "Please re-ingest your documents.")
