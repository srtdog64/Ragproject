# ui/options/reranker_tab.py
"""
Reranker Configuration Tab
"""
from PySide6.QtWidgets import *
from PySide6.QtCore import Qt


class RerankerTab(QWidget):
    """Reranker configuration tab"""
    
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
        <b>Reranking Models:</b><br>
        Choose the reranking strategy to improve search result relevance.
        Different rerankers work better for different use cases.
        </div>
        """)
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # Reranker models configuration
        self.reranker_models = [
            {
                "name": "Identity (None)",
                "type": "identity",
                "description": "No reranking - use original retrieval scores",
                "params": {}
            },
            {
                "name": "Simple Score",
                "type": "simple",
                "description": "Fast heuristic reranking based on recency and title matching",
                "params": {
                    "boost_recent": True,
                    "boost_title_match": True
                }
            },
            {
                "name": "BM25",
                "type": "bm25",
                "description": "Traditional keyword-based reranking, good for exact matches",
                "params": {
                    "k1": 1.2,
                    "b": 0.75
                }
            },
            {
                "name": "Cross-Encoder",
                "type": "cross-encoder",
                "description": "Deep learning model for semantic reranking (slower but accurate)",
                "params": {
                    "model": "cross-encoder/ms-marco-MiniLM-L-6-v2",
                    "device": "cpu"
                }
            },
            {
                "name": "Hybrid",
                "type": "hybrid",
                "description": "Combines multiple reranking strategies for best results",
                "params": {
                    "weights": {
                        "semantic": 0.5,
                        "bm25": 0.3,
                        "simple": 0.2
                    }
                }
            },
            {
                "name": "Cohere API",
                "type": "cohere",
                "description": "Cloud-based reranking using Cohere (requires API key)",
                "params": {
                    "model": "rerank-english-v2.0",
                    "api_key": ""
                }
            }
        ]
        
        # Current reranker display
        current_layout = QHBoxLayout()
        current_layout.addWidget(QLabel("Current Reranker:"))
        
        current_type = self.config.get("reranker.type", "simple", "server")
        self.currentRerankerLabel = QLabel(current_type)
        self.currentRerankerLabel.setStyleSheet("font-weight: bold; color: #5EAF08;")
        current_layout.addWidget(self.currentRerankerLabel)
        current_layout.addStretch()
        layout.addLayout(current_layout)
        
        # Reranker selection
        models_group = QGroupBox("Select Reranker")
        models_layout = QVBoxLayout()
        
        self.reranker_radios = {}
        for model in self.reranker_models:
            radio = QRadioButton(model['name'])
            radio.setToolTip(model['description'])
            self.reranker_radios[model['type']] = radio
            models_layout.addWidget(radio)
            
            # Description label
            desc = QLabel(f"   {model['description']}")
            desc.setStyleSheet("color: #666; font-size: 11px; margin-left: 20px; margin-bottom: 10px;")
            models_layout.addWidget(desc)
            
            # Add parameters section for some rerankers
            if model['type'] == 'cohere':
                # API key input for Cohere
                api_layout = QHBoxLayout()
                api_layout.addWidget(QLabel("   API Key:"))
                self.cohereApiKeyInput = QLineEdit()
                self.cohereApiKeyInput.setEchoMode(QLineEdit.Password)
                self.cohereApiKeyInput.setPlaceholderText("Enter Cohere API key")
                api_layout.addWidget(self.cohereApiKeyInput)
                api_layout.addStretch()
                models_layout.addLayout(api_layout)
        
        # Select current reranker
        if current_type in self.reranker_radios:
            self.reranker_radios[current_type].setChecked(True)
        
        models_group.setLayout(models_layout)
        layout.addWidget(models_group)
        
        # Apply button
        apply_btn = QPushButton("Apply Reranker")
        apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff6b35;
                color: black;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #E64A19;
            }
        """)
        apply_btn.clicked.connect(self.applyReranker)
        layout.addWidget(apply_btn)
        
        # Performance tips
        tips = QLabel("""
        <div style='background-color: #fff3e0; padding: 10px; border-radius: 5px; margin-top: 10px;'>
        <b>Tips:</b><br>
        • <b>Identity:</b> Fastest, uses original scores<br>
        • <b>Simple:</b> Fast, good for news/blogs<br>
        • <b>BM25:</b> Good for Korean text and exact matches<br>
        • <b>Cross-Encoder:</b> Best quality but slower<br>
        • <b>Hybrid:</b> Balanced performance and quality<br>
        • <b>Cohere:</b> Cloud-based, excellent quality
        </div>
        """)
        tips.setWordWrap(True)
        layout.addWidget(tips)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def applyReranker(self):
        """Apply selected reranker"""
        selected_type = None
        selected_model = None
        
        for model in self.reranker_models:
            if self.reranker_radios[model['type']].isChecked():
                selected_type = model['type']
                selected_model = model
                break
        
        if selected_type:
            # Special handling for Cohere API key
            if selected_type == 'cohere' and hasattr(self, 'cohereApiKeyInput'):
                api_key = self.cohereApiKeyInput.text().strip()
                if api_key:
                    selected_model['params']['api_key'] = api_key
                else:
                    QMessageBox.warning(self, "API Key Required", 
                                      "Please enter a Cohere API key to use this reranker.")
                    return
            
            # Save to config
            self.config.set("reranker.type", selected_type, "server")
            
            # Save parameters
            for key, value in selected_model['params'].items():
                if key != 'api_key':  # Don't save API key to config file
                    self.config.set(f"reranker.{key}", value, "server")
            
            # Update display
            self.currentRerankerLabel.setText(selected_type)
            
            QMessageBox.information(self, "Success", 
                                  f"Reranker changed to: {selected_model['name']}")
