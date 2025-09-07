# ui/options/llm_tab.py
"""
LLM Model Configuration Tab
"""
from PySide6.QtWidgets import *
from PySide6.QtCore import Qt, Signal


class LLMTab(QWidget):
    """LLM Model configuration tab"""
    
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
        <b>🤖 Language Model Configuration:</b><br>
        Select and configure your preferred Large Language Model.
        Each provider requires API keys set in the Server tab.
        </div>
        """)
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # Initialize model_combo first
        self.model_combo = QComboBox()
        
        # Current model display
        current_layout = QHBoxLayout()
        current_layout.addWidget(QLabel("Current Model:"))
        
        provider = self.config.get_current_provider()
        model = self.config.get_current_model()
        self.currentModelLabel = QLabel(f"{provider}: {model}")
        self.currentModelLabel.setStyleSheet("font-weight: bold; color: #2196F3;")
        current_layout.addWidget(self.currentModelLabel)
        current_layout.addStretch()
        layout.addLayout(current_layout)
        
        # Provider selection
        provider_group = QGroupBox("Select Provider")
        provider_layout = QVBoxLayout()
        
        self.provider_radios = {}
        providers = ["openai", "claude", "gemini"]
        
        for provider in providers:
            radio = QRadioButton(provider.capitalize())
            self.provider_radios[provider] = radio
            radio.toggled.connect(lambda checked, p=provider: self.onProviderChanged(p) if checked else None)
            provider_layout.addWidget(radio)
        
        # Select current provider
        current_provider = self.config.get_current_provider()
        if current_provider in self.provider_radios:
            self.provider_radios[current_provider].setChecked(True)
        
        provider_group.setLayout(provider_layout)
        layout.addWidget(provider_group)
        
        # Model selection
        model_group = QGroupBox("Select Model")
        model_layout = QVBoxLayout()
        model_layout.addWidget(self.model_combo)
        model_group.setLayout(model_layout)
        layout.addWidget(model_group)
        
        # Load models for current provider
        self.loadModelsForProvider(current_provider)
        
        # Temperature control
        temp_group = QGroupBox("Temperature (Creativity)")
        temp_layout = QVBoxLayout()
        
        self.temp_slider = QSlider(Qt.Horizontal)
        self.temp_slider.setRange(0, 100)
        self.temp_slider.setValue(int(self.config.get("llm.temperature", 0.7, "server") * 100))
        self.temp_slider.valueChanged.connect(self.onTempChanged)
        
        self.temp_label = QLabel(f"Temperature: {self.temp_slider.value() / 100:.2f}")
        
        temp_info = QLabel("""
        <small style='color: #666;'>
        0.0 = Deterministic, 1.0 = Creative
        </small>
        """)
        
        temp_layout.addWidget(self.temp_label)
        temp_layout.addWidget(self.temp_slider)
        temp_layout.addWidget(temp_info)
        temp_group.setLayout(temp_layout)
        layout.addWidget(temp_group)
        
        # Max tokens
        tokens_group = QGroupBox("Max Tokens")
        tokens_layout = QVBoxLayout()
        
        self.tokens_spin = QSpinBox()
        self.tokens_spin.setRange(100, 32000)
        self.tokens_spin.setSingleStep(100)
        self.tokens_spin.setValue(self.config.get("llm.max_tokens", 4096, "server"))
        
        tokens_info = QLabel("""
        <small style='color: #666;'>
        Maximum response length (1 token ≈ 4 characters)
        </small>
        """)
        
        tokens_layout.addWidget(self.tokens_spin)
        tokens_layout.addWidget(tokens_info)
        tokens_group.setLayout(tokens_layout)
        layout.addWidget(tokens_group)
        
        # Apply button
        apply_btn = QPushButton("Apply LLM Settings")
        apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        apply_btn.clicked.connect(self.applySettings)
        layout.addWidget(apply_btn)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def onProviderChanged(self, provider):
        """Handle provider change"""
        self.loadModelsForProvider(provider)
    
    def loadModelsForProvider(self, provider):
        """Load available models for selected provider"""
        self.model_combo.clear()
        
        # Get available models from config
        models = self.config.get(f"llm.available_models.{provider}", [], "server")
        
        if not models:
            # Default models if not in config
            default_models = {
                "openai": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
                "claude": ["claude-3-5-sonnet", "claude-3-opus", "claude-3-sonnet", "claude-3-haiku"],
                "gemini": ["gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash"]
            }
            models = default_models.get(provider, [])
        
        for model in models:
            self.model_combo.addItem(model)
        
        # Select current model if it matches
        current_model = self.config.get_current_model()
        if current_model in models:
            self.model_combo.setCurrentText(current_model)
    
    def onTempChanged(self, value):
        """Handle temperature slider change"""
        temp = value / 100
        self.temp_label.setText(f"Temperature: {temp:.2f}")
    
    def applySettings(self):
        """Apply LLM settings"""
        # Get selected provider
        provider = None
        for prov, radio in self.provider_radios.items():
            if radio.isChecked():
                provider = prov
                break
        
        if not provider:
            QMessageBox.warning(self, "No Provider", "Please select a provider")
            return
        
        # Get selected model
        model = self.model_combo.currentText()
        if not model:
            QMessageBox.warning(self, "No Model", "Please select a model")
            return
        
        # Save settings
        self.config.set("llm.type", provider, "server")
        self.config.set("llm.model", model, "server")
        self.config.set("llm.temperature", self.temp_slider.value() / 100, "server")
        self.config.set("llm.max_tokens", self.tokens_spin.value(), "server")
        
        # Update display
        self.currentModelLabel.setText(f"{provider}: {model}")
        
        # Emit signal
        self.modelChanged.emit(provider, model)
        
        QMessageBox.information(self, "Success", 
                              f"LLM settings updated:\n{provider}: {model}")
