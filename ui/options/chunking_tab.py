# ui/options/chunking_tab.py
"""
Chunking Strategy Configuration Tab
"""
from PySide6.QtWidgets import *
from PySide6.QtCore import Qt, Signal
from ..icon_manager import get_icon, Icons


class ChunkingTab(QWidget):
    """Chunking strategy configuration tab"""
    
    # Signal for strategy change
    strategyChanged = Signal(str)
    paramsChanged = Signal(dict)  # Add params change signal
    contextChunksChanged = Signal(int)  # Signal for topKs change
    
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
        <div style='background-color: #e3f2fd; padding: 10px; border-radius: 5px; color: #000000;'>
        <b>Chunking Strategy:</b><br>
        Choose how documents are split into chunks for indexing.
        Different strategies work better for different document types.
        </div>
        """)
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # Strategy configuration
        self.chunking_strategies = [
            {
                "name": "Adaptive (Smart)",
                "id": "adaptive",
                "description": "Intelligently adapts chunk size based on content structure",
                "icon": ""
            },
            {
                "name": "Fixed Size",
                "id": "fixed",
                "description": "Fixed size chunks with overlap",
                "icon": ""
            },
            {
                "name": "Sentence-based",
                "id": "sentence",
                "description": "Splits on sentence boundaries",
                "icon": ""
            },
            {
                "name": "Paragraph-based",
                "id": "paragraph",
                "description": "Keeps paragraphs together",
                "icon": ""
            },
            {
                "name": "Semantic",
                "id": "semantic",
                "description": "Groups semantically similar content",
                "icon": ""
            },
            {
                "name": "Markdown-aware",
                "id": "markdown",
                "description": "Preserves markdown structure",
                "icon": ""
            }
        ]
        
        # Current strategy
        current_layout = QHBoxLayout()
        current_label = QLabel("Current Strategy:")
        current_label.setStyleSheet("color: #000000;")
        current_layout.addWidget(current_label)
        
        current_strategy = self.config.get("chunker.default_strategy", "adaptive", "server")
        self.currentStrategyLabel = QLabel(current_strategy.capitalize())
        self.currentStrategyLabel.setStyleSheet("font-weight: bold; color: #ff6b35;")
        current_layout.addWidget(self.currentStrategyLabel)
        current_layout.addStretch()
        layout.addLayout(current_layout)
        
        # Strategy selection with ComboBox for backward compatibility
        strategy_group = QGroupBox("Select Strategy")
        strategy_group.setStyleSheet("QGroupBox { color: #000000; font-weight: bold; }")
        strategy_layout = QVBoxLayout()
        
        # Add ComboBox at the top
        self.strategyCombo = QComboBox()
        for strategy in self.chunking_strategies:
            self.strategyCombo.addItem(strategy['name'], strategy['id'])
        
        # Set current strategy in ComboBox
        current_index = self.strategyCombo.findData(current_strategy)
        if current_index >= 0:
            self.strategyCombo.setCurrentIndex(current_index)
        
        # Connect ComboBox change
        self.strategyCombo.currentTextChanged.connect(self.onStrategyComboChanged)
        
        strategy_layout.addWidget(self.strategyCombo)
        strategy_layout.addSpacing(10)
        
        # Radio buttons as before
        self.strategy_radios = {}
        for strategy in self.chunking_strategies:
            radio_layout = QHBoxLayout()
            
            # Icon and name
            radio = QRadioButton(f"{strategy['name']}")
            radio.setStyleSheet("color: #000000;")
            radio.setToolTip(strategy['description'])
            radio.toggled.connect(lambda checked, s=strategy: self.onRadioToggled(s) if checked else None)
            self.strategy_radios[strategy['id']] = radio
            
            # Description
            desc = QLabel(strategy['description'])
            desc.setStyleSheet("color: #666; font-size: 11px; margin-left: 30px;")
            
            radio_layout.addWidget(radio)
            radio_layout.addStretch()
            
            strategy_layout.addLayout(radio_layout)
            strategy_layout.addWidget(desc)
            strategy_layout.addSpacing(5)
        
        # Select current strategy
        if current_strategy in self.strategy_radios:
            self.strategy_radios[current_strategy].setChecked(True)
        
        strategy_group.setLayout(strategy_layout)
        layout.addWidget(strategy_group)
        
        # Parameters
        params_group = QGroupBox("Chunking Parameters")
        params_group.setStyleSheet("QGroupBox { color: #000000; font-weight: bold; }")
        params_layout = QFormLayout()
        
        # Max tokens
        self.maxTokensSpin = QSpinBox()
        self.maxTokensSpin.setRange(100, 2000)
        self.maxTokensSpin.setValue(self.config.get("chunker.default_params.maxTokens", 512, "server"))
        max_tokens_label = QLabel("Max Tokens:")
        max_tokens_label.setStyleSheet("color: #000000;")
        params_layout.addRow(max_tokens_label, self.maxTokensSpin)
        
        # Overlap
        self.overlapSpin = QSpinBox()
        self.overlapSpin.setRange(0, 500)
        self.overlapSpin.setValue(self.config.get("chunker.default_params.overlap", 200, "server"))
        overlap_label = QLabel("Overlap:")
        overlap_label.setStyleSheet("color: #000000;")
        params_layout.addRow(overlap_label, self.overlapSpin)
        
        # Window size (for adaptive)
        self.windowSizeSpin = QSpinBox()
        self.windowSizeSpin.setRange(500, 5000)
        self.windowSizeSpin.setValue(self.config.get("chunker.default_params.windowSize", 1200, "server"))
        window_size_label = QLabel("Window Size:")
        window_size_label.setStyleSheet("color: #000000;")
        params_layout.addRow(window_size_label, self.windowSizeSpin)
        
        # Semantic threshold
        self.semanticSlider = QSlider(Qt.Horizontal)
        self.semanticSlider.setRange(50, 95)
        self.semanticSlider.setValue(int(self.config.get("chunker.default_params.semanticThreshold", 0.82, "server") * 100))
        self.semanticLabel = QLabel(f"{self.semanticSlider.value() / 100:.2f}")
        self.semanticLabel.setStyleSheet("color: #000000;")
        self.semanticSlider.valueChanged.connect(lambda v: self.semanticLabel.setText(f"{v / 100:.2f}"))
        
        semantic_layout = QHBoxLayout()
        semantic_layout.addWidget(self.semanticSlider)
        semantic_layout.addWidget(self.semanticLabel)
        semantic_threshold_label = QLabel("Semantic Threshold:")
        semantic_threshold_label.setStyleSheet("color: #000000;")
        params_layout.addRow(semantic_threshold_label, semantic_layout)
        
        # topKs (for RAG retrieval)
        self.contextChunksSpin = QSpinBox()
        self.contextChunksSpin.setRange(1, 50)
        self.contextChunksSpin.setValue(self.config.get("policy.defaulttopK", 20, "server"))
        self.contextChunksSpin.setToolTip("Number of topKs to retrieve for each question")
        topks_label = QLabel("topKs:")
        topks_label.setStyleSheet("color: #000000;")
        params_layout.addRow(topks_label, self.contextChunksSpin)
        
        params_group.setLayout(params_layout)
        layout.addWidget(params_group)
        
        # Apply button
        apply_btn = QPushButton("Apply Chunking Settings")
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
        apply_btn.clicked.connect(self.applySettings)
        layout.addWidget(apply_btn)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def onRadioToggled(self, strategy):
        """Handle radio button toggle"""
        # Update ComboBox to match
        index = self.strategyCombo.findData(strategy['id'])
        if index >= 0:
            self.strategyCombo.setCurrentIndex(index)
    
    def onStrategyComboChanged(self, text):
        """Handle strategy ComboBox change"""
        # Find the strategy ID from the text
        for strategy in self.chunking_strategies:
            if strategy['name'] == text:
                # Update radio buttons to match
                if strategy['id'] in self.strategy_radios:
                    self.strategy_radios[strategy['id']].setChecked(True)
                # Emit signal
                self.strategyChanged.emit(strategy['id'])
                break
    
    def applySettings(self):
        """Apply chunking settings"""
        # Get selected strategy
        selected_strategy = None
        for strategy_id, radio in self.strategy_radios.items():
            if radio.isChecked():
                selected_strategy = strategy_id
                break
        
        if not selected_strategy:
            QMessageBox.warning(self, "No Strategy", "Please select a chunking strategy")
            return
        
        # Save settings
        self.config.set("chunker.default_strategy", selected_strategy, "server")
        self.config.set("chunker.default_params.maxTokens", self.maxTokensSpin.value(), "server")
        self.config.set("chunker.default_params.overlap", self.overlapSpin.value(), "server")
        self.config.set("chunker.default_params.windowSize", self.windowSizeSpin.value(), "server")
        self.config.set("chunker.default_params.semanticThreshold", self.semanticSlider.value() / 100, "server")
        self.config.set("policy.defaulttopK", self.contextChunksSpin.value(), "server")
        
        # Update display
        self.currentStrategyLabel.setText(selected_strategy.capitalize())
        
        # Emit signal
        self.strategyChanged.emit(selected_strategy)
        
        # Emit params changed signal
        params = {
            'maxTokens': self.maxTokensSpin.value(),
            'overlap': self.overlapSpin.value(),
            'windowSize': self.windowSizeSpin.value(),
            'semanticThreshold': self.semanticSlider.value() / 100
        }
        self.paramsChanged.emit(params)
        
        # Emit topKs changed signal
        self.contextChunksChanged.emit(self.contextChunksSpin.value())
        
        QMessageBox.information(self, "Success", 
                              f"Chunking strategy changed to: {selected_strategy}")
