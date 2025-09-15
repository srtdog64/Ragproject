"""
Embedder Model Configuration Tab - Fixed Style Reset
"""
from PySide6.QtWidgets import *
from PySide6.QtCore import Qt


class EmbedderTab(QWidget):
    """Embedder configuration tab with proper style management"""
    
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
        <b>Embedding Model Configuration:</b><br>
        Select the embedding model for semantic search.
        Different models offer different trade-offs between speed and quality.
        </div>
        """)
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # Current embedder display
        current_layout = QHBoxLayout()
        current_layout.addWidget(QLabel("Current Embedder:"))
        
        # Get current settings once
        current_type = self.config.get("embedder.type", "huggingface", "server")
        current_model = self.config.get("embedder.model", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2", "server")
        self.currentEmbedderLabel = QLabel(f"{current_type}: {current_model}")
        self.currentEmbedderLabel.setStyleSheet("font-weight: bold; color: #4CAF50;")
        self.currentEmbedderLabel.setWordWrap(True)
        current_layout.addWidget(self.currentEmbedderLabel, 1)
        layout.addLayout(current_layout)
        
        # Create scroll area for model selection
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()
        
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.addLayout(layout)
        
        # Embedder models configuration
        self.embedder_models = [
            {
                "name": "HuggingFace Sentence Transformers",
                "type": "huggingface",
                "models": [
                    ("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2", "Multilingual MiniLM L12 v2 (384d)"),
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
        
        # Create collapsible groups for each embedder type
        self.radio_buttons = []
        for embedder_type in self.embedder_models:
            group = QGroupBox(embedder_type["name"])
            group.setCheckable(False)
            group_layout = QVBoxLayout()
            
            # Add radio buttons
            for model_key, model_desc in embedder_type["models"]:
                # Check if this is the current model and add star if it is
                is_current = (embedder_type["type"] == current_type and model_key == current_model)
                display_text = f"{model_desc} ⭐ CURRENT" if is_current else model_desc
                
                radio = QRadioButton(display_text)
                radio.setProperty("embedder_type", embedder_type["type"])
                radio.setProperty("model_key", model_key)
                radio.setProperty("original_desc", model_desc)  # Store original description
                
                # Check if this is the current model
                if is_current:
                    radio.setChecked(True)
                    radio.setStyleSheet("font-weight: bold;")
                
                # Store reference to radio button
                self.radio_buttons.append(radio)
                group_layout.addWidget(radio)
            
            group.setLayout(group_layout)
            scroll_layout.addWidget(group)
        
        scroll_widget.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_widget)
        
        # Set minimum and maximum height for scroll area
        scroll_area.setMinimumHeight(200)
        scroll_area.setMaximumHeight(400)
        
        main_layout.addWidget(scroll_area, 1)  # Give it stretch factor
        
        # Cache directory
        cache_group = QGroupBox("Cache Settings")
        cache_layout = QVBoxLayout()
        
        cache_info = QLabel("Cache directory for downloaded models (leave empty for default)")
        cache_layout.addWidget(cache_info)
        
        cache_input_layout = QHBoxLayout()
        self.cache_input = QLineEdit()
        self.cache_input.setPlaceholderText("Default: ~/.cache/sentence_transformers")
        
        # Load existing cache dir if set
        cache_dir = self.config.get("embedder.cache_dir", "", "server")
        if cache_dir:
            self.cache_input.setText(cache_dir)
        
        cache_input_layout.addWidget(self.cache_input)
        
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browseCacheDir)
        cache_input_layout.addWidget(browse_btn)
        
        cache_layout.addLayout(cache_input_layout)
        cache_group.setLayout(cache_layout)
        
        main_layout.addWidget(cache_group)
        
        # Apply button
        apply_btn = QPushButton("Apply Embedder")
        apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: black;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        apply_btn.clicked.connect(self.applyEmbedder)
        main_layout.addWidget(apply_btn)
        
        # Warning about changing embedder
        warning = QLabel("""
        <div style='background-color: #fff3e0; padding: 10px; border-radius: 5px; margin-top: 10px;'>
        <b>Warning:</b> Changing the embedder requires re-ingesting all documents
        as embeddings are model-specific.
        </div>
        """)
        warning.setWordWrap(True)
        main_layout.addWidget(warning)
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("Save All Settings")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: black;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        save_btn.clicked.connect(self.saveAllSettings)
        button_layout.addWidget(save_btn)
        
        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: black;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        reset_btn.clicked.connect(self.resetToDefaults)
        button_layout.addWidget(reset_btn)
        
        button_layout.addStretch()
        main_layout.addLayout(button_layout)
        
        # Add stretch at bottom
        main_layout.addStretch()
        
        self.setLayout(main_layout)
    
    def browseCacheDir(self):
        """Browse for cache directory"""
        directory = QFileDialog.getExistingDirectory(
            self, "Select Cache Directory",
            self.cache_input.text() or ""
        )
        if directory:
            self.cache_input.setText(directory)
    
    def updateCurrentDisplay(self, embedder_type: str, model_key: str):
        """Update the current embedder display and refresh radio button labels"""
        # Update the current display label
        self.currentEmbedderLabel.setText(f"{embedder_type}: {model_key}")
        
        # Update all radio buttons to refresh the CURRENT star
        for radio in self.radio_buttons:
            stored_type = radio.property("embedder_type")
            stored_model = radio.property("model_key")
            original_desc = radio.property("original_desc")
            
            # Check if this is now the current model
            is_current = (stored_type == embedder_type and stored_model == model_key)
            
            # Update the display text
            display_text = f"{original_desc} ⭐ CURRENT" if is_current else original_desc
            radio.setText(display_text)
            
            # Update style - just bold for current, normal for others
            if is_current:
                radio.setStyleSheet("font-weight: bold;")
            else:
                radio.setStyleSheet("font-weight: normal;")
    
    def applyEmbedder(self):
        """Apply selected embedder"""
        selected_type = None
        selected_model = None
        
        # Find selected radio button
        for radio in self.radio_buttons:
            if radio.isChecked():
                selected_type = radio.property("embedder_type")
                selected_model = radio.property("model_key")
                break
        
        if not selected_type or not selected_model:
            QMessageBox.warning(self, "No Selection", 
                              "Please select an embedding model")
            return
        
        # Confirm if changing embedder
        current_type = self.config.get("embedder.type", "huggingface", "server")
        current_model = self.config.get("embedder.model", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2", "server")
        
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
        self.updateCurrentDisplay(selected_type, selected_model)
        
        QMessageBox.information(self, "Success", 
                              f"Embedder changed to: {selected_type}/{selected_model}\n"
                              "Please re-ingest your documents.")
    
    def saveAllSettings(self):
        """Save all settings"""
        self.applyEmbedder()
        if self.parent_widget:
            self.parent_widget.saveAllSettings()
    
    def resetToDefaults(self):
        """Reset to default settings"""
        reply = QMessageBox.question(
            self, "Reset to Defaults",
            "This will reset all embedder settings to defaults.\n"
            "Are you sure?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Reset to default embedder
            self.config.set("embedder.type", "huggingface", "server")
            self.config.set("embedder.model", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2", "server")
            self.config.set("embedder.cache_dir", "", "server")
            
            # Update UI
            self.cache_input.clear()
            
            # Find and check the default radio button
            for radio in self.radio_buttons:
                if (radio.property("embedder_type") == "huggingface" and 
                    radio.property("model_key") == "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"):
                    radio.setChecked(True)
                    break
            
            # Update display
            self.updateCurrentDisplay("huggingface", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
            
            QMessageBox.information(self, "Reset Complete", 
                                  "Embedder settings have been reset to defaults.")
