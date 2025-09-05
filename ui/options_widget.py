# ui/options_widget.py
"""
Options Tab Widget for RAG Qt Application
Simplified version with static chunking strategies
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
        
        # Static chunking strategies
        self.strategies = [
            {
                "name": "sentence",
                "description": "Splits text at sentence boundaries. Best for Q&A and chat logs."
            },
            {
                "name": "paragraph", 
                "description": "Splits text at paragraph boundaries. Ideal for structured documents."
            },
            {
                "name": "sliding_window",
                "description": "Uses a fixed-size sliding window with overlap. Good for long narratives."
            },
            {
                "name": "adaptive",
                "description": "Automatically selects the best strategy based on content type."
            },
            {
                "name": "simple_overlap",
                "description": "Simple fixed-size chunks with overlap. Fast and predictable."
            }
        ]
        
        # Get current strategy from server on initialization
        self.currentStrategy = self.fetchCurrentStrategyFromServer()
        self.initUI()
        
    def fetchCurrentStrategyFromServer(self) -> str:
        """Fetch current strategy from server on initialization"""
        try:
            import requests
            response = requests.get(f"{self.config.get_server_url()}/api/chunkers/current")
            if response.status_code == 200:
                data = response.json()
                strategy = data.get('strategy', 'adaptive')
                print(f"Fetched current strategy from server: {strategy}")
                return strategy
        except Exception as e:
            print(f"Failed to fetch strategy from server: {e}")
        
        # Fallback to config or default
        return self.config.get("chunker.default_strategy", "adaptive", 'server')
    
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
        """Create chunking strategy section (static)"""
        group = QGroupBox("📦 Chunking Strategy")
        layout = QVBoxLayout()
        
        # Current strategy display
        self.currentStrategyLabel = QLabel(f"Current Strategy: {self.currentStrategy}")
        self.currentStrategyLabel.setStyleSheet("font-weight: bold; color: #1976d2;")
        layout.addWidget(self.currentStrategyLabel)
        
        # Server sync indicator
        self.syncStatusLabel = QLabel("✅ Synced with server")
        self.syncStatusLabel.setStyleSheet("color: green; font-size: 11px;")
        layout.addWidget(self.syncStatusLabel)
        
        # Strategy selector
        selectorLayout = QHBoxLayout()
        selectorLayout.addWidget(QLabel("Select Strategy:"))
        
        self.strategyCombo = QComboBox()
        self.strategyCombo.setMinimumWidth(200)
        
        # Add static strategies
        for strategy in self.strategies:
            self.strategyCombo.addItem(strategy['name'])
        
        # Set current strategy from server
        self.strategyCombo.setCurrentText(self.currentStrategy)
        self.strategyCombo.currentTextChanged.connect(self.onStrategyComboChanged)
        selectorLayout.addWidget(self.strategyCombo)
        
        self.applyStrategyBtn = QPushButton("Apply Strategy")
        self.applyStrategyBtn.clicked.connect(self.onStrategyApply)
        selectorLayout.addWidget(self.applyStrategyBtn)
        
        # Refresh button to sync with server
        self.refreshStrategyBtn = QPushButton("🔄")
        self.refreshStrategyBtn.setToolTip("Refresh from server")
        self.refreshStrategyBtn.clicked.connect(self.onRefreshStrategy)
        self.refreshStrategyBtn.setMaximumWidth(30)
        selectorLayout.addWidget(self.refreshStrategyBtn)
        
        selectorLayout.addStretch()
        layout.addLayout(selectorLayout)
        
        # Strategy description
        self.strategyDescLabel = QLabel()
        self.strategyDescLabel.setWordWrap(True)
        self.strategyDescLabel.setStyleSheet("color: #666; margin-top: 10px;")
        self.onStrategyComboChanged()  # Initialize description
        layout.addWidget(self.strategyDescLabel)
        
        group.setLayout(layout)
        return group
    
    def createParametersSection(self) -> QGroupBox:
        """Create chunking parameters section"""
        group = QGroupBox("🎛️ Chunking Parameters")
        layout = QFormLayout()
        
        self.paramInputs = {}
        
        # Get parameters from server or config
        default_params = self.fetchCurrentParamsFromServer()
        
        params = [
            ("maxTokens", "Max Tokens:", QSpinBox, (100, 5000, default_params.get('maxTokens', 512)), 
             "Maximum tokens per chunk"),
            ("windowSize", "Window Size:", QSpinBox, (200, 10000, default_params.get('windowSize', 1200)),
             "Size of sliding window in characters"),
            ("overlap", "Overlap:", QSpinBox, (0, 1000, default_params.get('overlap', 200)),
             "Characters to overlap between chunks"),
            ("semanticThreshold", "Semantic Threshold:", QDoubleSpinBox, (0.0, 1.0, default_params.get('semanticThreshold', 0.82)),
             "Similarity threshold for semantic chunking"),
            ("sentenceMinLen", "Min Sentence Length:", QSpinBox, (1, 100, default_params.get('sentenceMinLen', 10)),
             "Minimum sentence length in characters"),
            ("paragraphMinLen", "Min Paragraph Length:", QSpinBox, (10, 500, default_params.get('paragraphMinLen', 50)),
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
        self.languageCombo.setCurrentText(default_params.get('language', 'ko'))
        self.languageCombo.setToolTip("Language for text processing")
        self.paramInputs["language"] = self.languageCombo
        layout.addRow("Language:", self.languageCombo)
        
        # Button layout
        buttonLayout = QHBoxLayout()
        
        # Apply parameters button
        applyParamsBtn = QPushButton("Apply Parameters")
        applyParamsBtn.clicked.connect(self.onParamsApply)
        buttonLayout.addWidget(applyParamsBtn)
        
        # Refresh params button
        refreshParamsBtn = QPushButton("🔄")
        refreshParamsBtn.setToolTip("Refresh from server")
        refreshParamsBtn.clicked.connect(self.onRefreshParams)
        refreshParamsBtn.setMaximumWidth(30)
        buttonLayout.addWidget(refreshParamsBtn)
        
        layout.addRow("", buttonLayout)
        
        group.setLayout(layout)
        return group
    
    def fetchCurrentParamsFromServer(self) -> Dict:
        """Fetch current parameters from server"""
        try:
            import requests
            response = requests.get(f"{self.config.get_server_url()}/api/chunkers/params")
            if response.status_code == 200:
                params = response.json()
                print(f"Fetched params from server: {params}")
                return params
        except Exception as e:
            print(f"Failed to fetch params from server: {e}")
        
        # Fallback to config
        return self.config.get("chunker.default_params", {}, 'server')
    
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
        """
        
        infoLabel = QLabel(configInfo)
        infoLabel.setStyleSheet("padding: 10px; background-color: #f5f5f5; border-radius: 4px;")
        layout.addWidget(infoLabel)
        
        # Save config button
        saveConfigBtn = QPushButton("💾 Save Current Settings to Config")
        saveConfigBtn.clicked.connect(self.onSaveConfig)
        layout.addWidget(saveConfigBtn)
        
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
                "gemini-1.5-pro": "Advanced model with extended context window",
                "gemini-1.5-flash": "Fast model for quick responses"
            },
            "openai": {
                "gpt-3.5-turbo": "Fast and cost-effective for most tasks",
                "gpt-4": "Most capable model for complex reasoning",
                "gpt-4-turbo": "GPT-4 with improved speed and lower cost",
                "gpt-4o": "Optimized GPT-4 variant",
                "gpt-4o-mini": "Smaller, faster GPT-4 variant"
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
    
    def onRefreshStrategy(self):
        """Refresh strategy from server"""
        strategy = self.fetchCurrentStrategyFromServer()
        self.currentStrategy = strategy
        self.strategyCombo.setCurrentText(strategy)
        self.currentStrategyLabel.setText(f"Current Strategy: {strategy}")
        self.syncStatusLabel.setText("✅ Synced with server")
        self.syncStatusLabel.setStyleSheet("color: green; font-size: 11px;")
    
    def onStrategyApply(self):
        """Apply selected strategy"""
        strategy = self.strategyCombo.currentText()
        if strategy:
            try:
                import requests
                # Send to server first
                response = requests.post(
                    f"{self.config.get_server_url()}/api/chunkers/strategy",
                    json={"strategy": strategy},
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    self.currentStrategy = strategy
                    self.currentStrategyLabel.setText(f"Current Strategy: {strategy}")
                    
                    # Save to config
                    self.config.set("chunker.default_strategy", strategy, 'server')
                    
                    # Update sync status
                    self.syncStatusLabel.setText("✅ Applied to server")
                    self.syncStatusLabel.setStyleSheet("color: green; font-size: 11px;")
                    
                    # Emit signal
                    self.strategyChanged.emit(strategy)
                    
                    QMessageBox.information(self, "Success", f"Strategy changed to: {strategy}")
                else:
                    raise Exception(f"Server returned {response.status_code}")
                    
            except Exception as e:
                # Fallback to local config only
                print(f"Failed to apply to server: {e}")
                self.config.set("chunker.default_strategy", strategy, 'server')
                self.currentStrategy = strategy
                self.currentStrategyLabel.setText(f"Current Strategy: {strategy}")
                
                self.syncStatusLabel.setText("⚠️ Server not synced")
                self.syncStatusLabel.setStyleSheet("color: orange; font-size: 11px;")
                
                QMessageBox.warning(self, "Warning", 
                                   f"Strategy saved locally but server sync failed: {e}")
    
    def onRefreshParams(self):
        """Refresh parameters from server"""
        params = self.fetchCurrentParamsFromServer()
        self.updateParams(params)
        QMessageBox.information(self, "Success", "Parameters refreshed from server")
    
    def onParamsApply(self):
        """Apply chunking parameters"""
        params = self.getParams()
        
        try:
            import requests
            # Send to server
            response = requests.post(
                f"{self.config.get_server_url()}/api/chunkers/params",
                json=params,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                # Save to config
                self.config.set("chunker.default_params", params, 'server')
                
                # Emit signal
                self.paramsChanged.emit(params)
                
                QMessageBox.information(self, "Success", "Parameters updated successfully")
            else:
                raise Exception(f"Server returned {response.status_code}")
                
        except Exception as e:
            # Fallback to local config
            print(f"Failed to apply params to server: {e}")
            self.config.set("chunker.default_params", params, 'server')
            self.paramsChanged.emit(params)
            
            QMessageBox.warning(self, "Warning", 
                              f"Parameters saved locally but server sync failed: {e}")
    
    def onStrategyComboChanged(self):
        """Update description when combo selection changes"""
        current = self.strategyCombo.currentText()
        for strategy in self.strategies:
            if strategy['name'] == current:
                self.strategyDescLabel.setText(f"📝 {strategy['description']}")
                break
    
    def onSaveConfig(self):
        """Save all current settings to config files"""
        try:
            # Model settings
            provider = self.providerCombo.currentText()
            model = self.modelCombo.currentText()
            self.config.set_model(provider, model)
            self.config.set("llm.temperature", self.temperatureSpin.value(), 'server')
            self.config.set("llm.max_tokens", self.maxTokensSpin.value(), 'server')
            
            # Chunking settings
            self.config.set("chunker.default_strategy", self.currentStrategy, 'server')
            self.config.set("chunker.default_params", self.getParams(), 'server')
            
            QMessageBox.information(self, "Success", "All settings saved to configuration files")
            
            # Emit reload signal
            self.configReloaded.emit()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save configuration: {str(e)}")
    
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
    
    # Simplified methods - no API calls needed
    def updateStrategies(self, strategies: List[Dict]):
        """Legacy method - now does nothing since strategies are static"""
        pass
    
    def updateParams(self, params: Dict):
        """Update parameter values from external source"""
        for key, value in params.items():
            if key in self.paramInputs:
                widget = self.paramInputs[key]
                if isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                    widget.setValue(value)
                elif isinstance(widget, QComboBox):
                    widget.setCurrentText(str(value))
