# ui/options_widget.py
"""
Options Tab Widget for RAG Qt Application
"""
from typing import Dict, List
from PySide6.QtWidgets import *
from PySide6.QtCore import Signal


class OptionsWidget(QWidget):
    """Options widget for system configuration"""
    
    strategyChanged = Signal(str)
    paramsChanged = Signal(dict)
    modelChanged = Signal(str, str)  # provider, model
    configReloaded = Signal()
    
    def __init__(self, config_manager):
        super().__init__()
        self.config = config_manager
        self.strategies = []
        self.currentStrategy = ""
        self.initUI()
    
    def initUI(self):
        # Main scroll area
        scrollArea = QScrollArea()
        scrollWidget = QWidget()
        scrollLayout = QVBoxLayout()
        
        # Title
        titleLabel = QLabel("⚙️ System Configuration")
        titleLabel.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px 0;")
        scrollLayout.addWidget(titleLabel)
        
        # Model Configuration Section
        modelGroup = self.createModelSection()
        scrollLayout.addWidget(modelGroup)
        
        # Chunking Strategy Section  
        strategyGroup = self.createStrategySection()
        scrollLayout.addWidget(strategyGroup)
        
        # Parameters Section
        paramsGroup = self.createParametersSection()
        scrollLayout.addWidget(paramsGroup)
        
        # Server Info Section
        serverGroup = self.createServerInfoSection()
        scrollLayout.addWidget(serverGroup)
        
        scrollLayout.addStretch()
        scrollWidget.setLayout(scrollLayout)
        scrollArea.setWidget(scrollWidget)
        scrollArea.setWidgetResizable(True)
        
        # Main layout
        mainLayout = QVBoxLayout()
        mainLayout.addWidget(scrollArea)
        self.setLayout(mainLayout)
    
    def createModelSection(self) -> QGroupBox:
        """Create LLM model configuration section"""
        group = QGroupBox("🧠 LLM Model Configuration")
        layout = QVBoxLayout()
        
        # Current model display
        currentLayout = QHBoxLayout()
        currentLayout.addWidget(QLabel("Current Model:"))
        
        provider = self.config.get_current_provider()
        model = self.config.get_current_model()
        self.currentModelLabel = QLabel(f"{provider}: {model}")
        self.currentModelLabel.setStyleSheet("font-weight: bold; color: #4285f4;")
        currentLayout.addWidget(self.currentModelLabel)
        currentLayout.addStretch()
        layout.addLayout(currentLayout)
        
        # Model selector
        selectorLayout = QFormLayout()
        
        # Provider selector
        self.providerCombo = QComboBox()
        self.providerCombo.setMinimumWidth(200)
        available_models = self.config.get_available_models()
        self.providerCombo.addItems(list(available_models.keys()))
        self.providerCombo.setCurrentText(provider)
        self.providerCombo.currentTextChanged.connect(self.onProviderChanged)
        selectorLayout.addRow("Provider:", self.providerCombo)
        
        # Model selector
        self.modelCombo = QComboBox()
        self.modelCombo.setMinimumWidth(300)
        self.updateModelList()
        self.modelCombo.setCurrentText(model)
        selectorLayout.addRow("Model:", self.modelCombo)
        
        # Temperature setting
        self.temperatureSpin = QDoubleSpinBox()
        self.temperatureSpin.setRange(0.0, 2.0)
        self.temperatureSpin.setSingleStep(0.1)
        self.temperatureSpin.setValue(self.config.get("llm.temperature", 0.7, 'server'))
        self.temperatureSpin.setToolTip("Higher values = more creative, lower = more focused")
        selectorLayout.addRow("Temperature:", self.temperatureSpin)
        
        # Max tokens setting
        self.maxTokensSpin = QSpinBox()
        self.maxTokensSpin.setRange(100, 32000)
        self.maxTokensSpin.setSingleStep(100)
        self.maxTokensSpin.setValue(self.config.get("llm.max_tokens", 2048, 'server'))
        selectorLayout.addRow("Max Tokens:", self.maxTokensSpin)
        
        layout.addLayout(selectorLayout)
        
        # Apply button
        applyModelBtn = QPushButton("Apply Model Settings")
        applyModelBtn.setStyleSheet("""
            QPushButton {
                background-color: #4285f4;
                color: white;
                font-weight: bold;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #357ae8;
            }
        """)
        applyModelBtn.clicked.connect(self.onModelApply)
        layout.addWidget(applyModelBtn)
        
        # Model descriptions
        self.modelDescLabel = QLabel()
        self.modelDescLabel.setWordWrap(True)
        self.modelDescLabel.setStyleSheet("color: #666; margin-top: 10px; padding: 10px; background-color: #f5f5f5; border-radius: 4px;")
        self.updateModelDescription()
        layout.addWidget(self.modelDescLabel)
        
        group.setLayout(layout)
        return group
    
    def createStrategySection(self) -> QGroupBox:
        """Create chunking strategy section"""
        group = QGroupBox("📦 Chunking Strategy")
        layout = QVBoxLayout()
        
        # Current strategy display
        self.currentStrategyLabel = QLabel("Current Strategy: Loading...")
        self.currentStrategyLabel.setStyleSheet("font-weight: bold; color: #1976d2;")
        layout.addWidget(self.currentStrategyLabel)
        
        # Strategy selector
        selectorLayout = QHBoxLayout()
        selectorLayout.addWidget(QLabel("Select Strategy:"))
        
        self.strategyCombo = QComboBox()
        self.strategyCombo.setMinimumWidth(200)
        selectorLayout.addWidget(self.strategyCombo)
        
        self.applyStrategyBtn = QPushButton("Apply")
        self.applyStrategyBtn.clicked.connect(self.onStrategyApply)
        selectorLayout.addWidget(self.applyStrategyBtn)
        
        self.refreshStrategiesBtn = QPushButton("🔄 Refresh")
        self.refreshStrategiesBtn.clicked.connect(self.onRefreshStrategies)
        selectorLayout.addWidget(self.refreshStrategiesBtn)
        
        selectorLayout.addStretch()
        layout.addLayout(selectorLayout)
        
        # Strategy description
        self.strategyDescLabel = QLabel()
        self.strategyDescLabel.setWordWrap(True)
        self.strategyDescLabel.setStyleSheet("color: #666; margin-top: 10px;")
        layout.addWidget(self.strategyDescLabel)
        
        group.setLayout(layout)
        return group
    
    def createParametersSection(self) -> QGroupBox:
        """Create chunking parameters section"""
        group = QGroupBox("🎛️ Chunking Parameters")
        layout = QFormLayout()
        
        self.paramInputs = {}
        
        params = [
            ("maxTokens", "Max Tokens:", QSpinBox, (100, 5000, 512), 
             "Maximum tokens per chunk"),
            ("windowSize", "Window Size:", QSpinBox, (200, 10000, 1200),
             "Size of sliding window in characters"),
            ("overlap", "Overlap:", QSpinBox, (0, 1000, 200),
             "Characters to overlap between chunks"),
            ("semanticThreshold", "Semantic Threshold:", QDoubleSpinBox, (0.0, 1.0, 0.82),
             "Similarity threshold for semantic chunking"),
            ("sentenceMinLen", "Min Sentence Length:", QSpinBox, (1, 100, 10),
             "Minimum sentence length in characters"),
            ("paragraphMinLen", "Min Paragraph Length:", QSpinBox, (10, 500, 50),
             "Minimum paragraph length in characters"),
        ]
        
        for key, label, widget_class, (min_val, max_val, default), tooltip in params:
            widget = widget_class()
            if widget_class == QSpinBox:
                widget.setRange(min_val, max_val)
                widget.setValue(default)
            else:  # QDoubleSpinBox
                widget.setRange(min_val, max_val)
                widget.setSingleStep(0.01)
                widget.setValue(default)
            
            widget.setToolTip(tooltip)
            self.paramInputs[key] = widget
            layout.addRow(label, widget)
        
        # Language selector
        self.languageCombo = QComboBox()
        self.languageCombo.addItems(["ko", "en", "ja", "zh"])
        self.languageCombo.setToolTip("Language for text processing")
        self.paramInputs["language"] = self.languageCombo
        layout.addRow("Language:", self.languageCombo)
        
        # Apply parameters button
        applyParamsBtn = QPushButton("Apply Parameters")
        applyParamsBtn.clicked.connect(self.onParamsApply)
        layout.addRow("", applyParamsBtn)
        
        group.setLayout(layout)
        return group
    
    def createServerInfoSection(self) -> QGroupBox:
        """Create server information section"""
        group = QGroupBox("🖥️ Server Information")
        layout = QVBoxLayout()
        
        # Server URL
        urlLayout = QHBoxLayout()
        urlLayout.addWidget(QLabel("Server URL:"))
        urlLabel = QLabel(self.config.get_server_url())
        urlLabel.setStyleSheet("font-weight: bold; color: #666;")
        urlLayout.addWidget(urlLabel)
        urlLayout.addStretch()
        layout.addLayout(urlLayout)
        
        # Config paths
        configInfo = """
        <b>Configuration Files:</b><br>
        • Server: config/config.yaml<br>
        • Qt App: config/qt_app_config.yaml<br>
        • Chunkers: rag/chunkers/config.json<br>
        """
        
        infoLabel = QLabel(configInfo)
        infoLabel.setStyleSheet("padding: 10px; background-color: #f5f5f5; border-radius: 4px;")
        layout.addWidget(infoLabel)
        
        # Reload config button
        reloadBtn = QPushButton("🔄 Reload All Configurations")
        reloadBtn.clicked.connect(self.onReloadConfig)
        layout.addWidget(reloadBtn)
        
        # Strategy guide
        guideText = """
        <b>🎯 Strategy Selection Guide:</b><br>
        • <b>sentence</b>: Q&A, chat logs, short content<br>
        • <b>paragraph</b>: Structured documents, manuals<br>
        • <b>sliding_window</b>: Long narratives, novels<br>
        • <b>adaptive</b>: Auto-selects best approach<br>
        • <b>simple_overlap</b>: Fixed-size chunks with overlap<br>
        """
        
        guideLabel = QLabel(guideText)
        guideLabel.setWordWrap(True)
        guideLabel.setStyleSheet("margin-top: 10px; padding: 10px; background-color: #e8f4f8; border-radius: 4px;")
        layout.addWidget(guideLabel)
        
        group.setLayout(layout)
        return group
    
    def updateModelList(self):
        """Update model list based on selected provider"""
        self.modelCombo.clear()
        provider = self.providerCombo.currentText()
        available_models = self.config.get_available_models()
        
        if provider in available_models:
            self.modelCombo.addItems(available_models[provider])
    
    def updateModelDescription(self):
        """Update model description based on selection"""
        provider = self.providerCombo.currentText()
        model = self.modelCombo.currentText()
        
        descriptions = {
            "gemini": {
                "gemini-pro": "Google's versatile model for text generation",
                "gemini-pro-vision": "Multimodal model supporting text and images",
                "gemini-1.5-pro": "Advanced model with extended context window"
            },
            "openai": {
                "gpt-3.5-turbo": "Fast and cost-effective for most tasks",
                "gpt-4": "Most capable model for complex reasoning",
                "gpt-4-turbo": "GPT-4 with improved speed and lower cost"
            },
            "claude": {
                "claude-3-opus": "Most powerful Claude model",
                "claude-3-sonnet": "Balanced performance and cost",
                "claude-3-haiku": "Fast and lightweight model"
            }
        }
        
        desc = descriptions.get(provider, {}).get(model, "Model information not available")
        self.modelDescLabel.setText(f"ℹ️ {desc}")
    
    def onProviderChanged(self):
        """Handle provider change"""
        self.updateModelList()
        self.updateModelDescription()
    
    def onModelApply(self):
        """Apply model settings"""
        provider = self.providerCombo.currentText()
        model = self.modelCombo.currentText()
        
        # Save to config
        self.config.set_model(provider, model)
        self.config.set("llm.temperature", self.temperatureSpin.value(), 'server')
        self.config.set("llm.max_tokens", self.maxTokensSpin.value(), 'server')
        
        # Update display
        self.currentModelLabel.setText(f"{provider}: {model}")
        
        # Emit signal
        self.modelChanged.emit(provider, model)
        
        QMessageBox.information(self, "Success", f"Model changed to {provider}: {model}")
    
    def onStrategyApply(self):
        """Apply selected strategy"""
        strategy = self.strategyCombo.currentText()
        if strategy:
            self.strategyChanged.emit(strategy)
    
    def onParamsApply(self):
        """Apply chunking parameters"""
        params = self.getParams()
        self.paramsChanged.emit(params)
    
    def onRefreshStrategies(self):
        """Refresh strategies - to be connected externally"""
        pass
    
    def onReloadConfig(self):
        """Reload configuration"""
        self.configReloaded.emit()
    
    def updateStrategies(self, strategies: List[Dict]):
        """Update the strategies list"""
        self.strategies = strategies
        self.strategyCombo.clear()
        
        if not strategies:
            self.currentStrategyLabel.setText("Current Strategy: No strategies available")
            self.strategyDescLabel.setText("❌ Could not load strategies. Check server connection.")
            return
        
        for strategy in strategies:
            self.strategyCombo.addItem(strategy['name'])
            if strategy.get('active'):
                self.currentStrategy = strategy['name']
                self.currentStrategyLabel.setText(f"Current Strategy: {strategy['name']}")
                self.strategyCombo.setCurrentText(strategy['name'])
        
        self.onStrategyComboChanged()
    
    def onStrategyComboChanged(self):
        """Update description when combo selection changes"""
        current = self.strategyCombo.currentText()
        for strategy in self.strategies:
            if strategy['name'] == current:
                self.strategyDescLabel.setText(f"📝 {strategy['description']}")
                break
    
    def updateParams(self, params: Dict):
        """Update parameter values"""
        for key, value in params.items():
            if key in self.paramInputs:
                widget = self.paramInputs[key]
                if isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                    widget.setValue(value)
                elif isinstance(widget, QComboBox):
                    widget.setCurrentText(str(value))
    
    def getParams(self) -> Dict:
        """Get current parameter values"""
        params = {}
        for key, widget in self.paramInputs.items():
            if isinstance(widget, QSpinBox):
                params[key] = widget.value()
            elif isinstance(widget, QDoubleSpinBox):
                params[key] = widget.value()
            elif isinstance(widget, QComboBox):
                params[key] = widget.currentText()
        return params
