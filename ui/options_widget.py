# ui/options_widget_modular.py
"""
Modular Options Widget with separated tabs
"""
from PySide6.QtWidgets import *
from PySide6.QtCore import Signal
from .config_manager import ConfigManager
from .options import (
    LLMTab,
    EmbedderTab,
    RerankerTab,
    ChunkingTab,
    ServerTab,
    VariablesTab
)
from .options.database_tab import DatabaseTab


class OptionsWidget(QWidget):
    """Options configuration widget with modular tabs"""
    
    # Signals
    strategyChanged = Signal(str)
    paramsChanged = Signal(dict)
    configReloaded = Signal()  # Add configReloaded signal
    modelChanged = Signal(str, str)  # Add modelChanged signal (provider, model)
    contextChunksChanged = Signal(int)  # Signal for topKs change
    
    def __init__(self, config_manager=None):
        super().__init__()
        # Accept config_manager but create our own if not provided
        self.config = config_manager if config_manager else ConfigManager()
        
        # Create proxy attributes for backward compatibility
        self.strategyCombo = None  # Will be set after chunking_tab creation
        
        self.initUI()
        
    def initUI(self):
        """Initialize the user interface"""
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("⚙️ System Configuration")
        title.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            padding: 10px;
            background-color: #f0f0f0;
            border-radius: 5px;
        """)
        layout.addWidget(title)
        
        # Create tab widget
        self.tabs = QTabWidget()
        
        # Create and add tabs
        self.llm_tab = LLMTab(self.config, self)
        self.llm_tab.modelChanged.connect(self.modelChanged)  # Connect modelChanged signal
        self.tabs.addTab(self.llm_tab, "🤖 LLM Models")
        
        self.embedder_tab = EmbedderTab(self.config, self)
        self.tabs.addTab(self.embedder_tab, "🧠 Embedding")
        
        self.reranker_tab = RerankerTab(self.config, self)
        self.tabs.addTab(self.reranker_tab, "🎯 Reranker")
        
        self.chunking_tab = ChunkingTab(self.config, self)
        self.chunking_tab.strategyChanged.connect(self.strategyChanged)
        self.chunking_tab.paramsChanged.connect(self.paramsChanged)  # Connect params signal
        self.chunking_tab.contextChunksChanged.connect(self.contextChunksChanged)  # Connect topKs signal
        self.tabs.addTab(self.chunking_tab, "✂️ Chunking")
        
        # Set strategyCombo reference for backward compatibility
        self.strategyCombo = self.chunking_tab.strategyCombo
        
        self.server_tab = ServerTab(self.config, self)
        self.tabs.addTab(self.server_tab, "🌐 Server")
        
        self.variables_tab = VariablesTab(self.config, self)
        self.tabs.addTab(self.variables_tab, "🔧 Variables")
        
        self.database_tab = DatabaseTab(self.config)
        self.tabs.addTab(self.database_tab, "💾 Database")
        
        layout.addWidget(self.tabs)
        
        # Save all settings button
        saveAllBtn = QPushButton("💾 Save All Settings")
        saveAllBtn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        saveAllBtn.clicked.connect(self.saveAllSettings)
        layout.addWidget(saveAllBtn)
        
        # Reload config button
        reloadBtn = QPushButton("🔄 Reload Configuration")
        reloadBtn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 8px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        reloadBtn.clicked.connect(self.reloadConfig)
        layout.addWidget(reloadBtn)
        
        self.setLayout(layout)
    
    def saveAllSettings(self):
        """Save all settings across all tabs"""
        try:
            # Apply settings from each tab before saving
            if hasattr(self, 'variables_tab'):
                print("[Options] Applying variables before save")  # Debug
                self.variables_tab.applyVariables()
            
            if hasattr(self, 'server_tab'):
                print("[Options] Applying server settings")  # Debug
                # Get values from server tab if it has an apply method
                if hasattr(self.server_tab, 'applySettings'):
                    self.server_tab.applySettings()
            
            if hasattr(self, 'llm_tab'):
                print("[Options] Applying LLM settings")  # Debug
                # Get current model selection
                if hasattr(self.llm_tab, 'applySettings'):
                    self.llm_tab.applySettings()
            
            # Save config files
            self.config.save_config("config/config.yaml", self.config.server_config)
            self.config.save_config("config/qt_app_config.yaml", self.config.app_config)
            
            print(f"[Options] Saved server config: {self.config.server_config}")  # Debug
            
            QMessageBox.information(self, "Success", 
                                  "All settings saved successfully!")
        except Exception as e:
            import traceback
            print(f"[Options] Save error: {traceback.format_exc()}")  # Debug
            QMessageBox.critical(self, "Error", 
                               f"Failed to save settings: {e}")
    
    def reloadConfig(self):
        """Reload configuration from files"""
        try:
            # Reload configs
            self.config.server_config = self.config._load_config("config/config.yaml")
            self.config.app_config = self.config._load_config("config/qt_app_config.yaml")
            
            # Refresh all tabs
            self.refreshAllTabs()
            
            # Emit signal
            self.configReloaded.emit()
            
            QMessageBox.information(self, "Success", 
                                  "Configuration reloaded successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", 
                               f"Failed to reload configuration: {e}")
    
    def refreshAllTabs(self):
        """Refresh all tabs with current configuration"""
        # Remove and recreate all tabs
        self.tabs.clear()
        
        # Recreate tabs
        self.llm_tab = LLMTab(self.config, self)
        self.llm_tab.modelChanged.connect(self.modelChanged)  # Connect modelChanged signal
        self.tabs.addTab(self.llm_tab, "🤖 LLM Models")
        
        self.embedder_tab = EmbedderTab(self.config, self)
        self.tabs.addTab(self.embedder_tab, "🧠 Embedding")
        
        self.reranker_tab = RerankerTab(self.config, self)
        self.tabs.addTab(self.reranker_tab, "🎯 Reranker")
        
        self.chunking_tab = ChunkingTab(self.config, self)
        self.chunking_tab.strategyChanged.connect(self.strategyChanged)
        self.chunking_tab.paramsChanged.connect(self.paramsChanged)  # Connect params signal
        self.chunking_tab.contextChunksChanged.connect(self.contextChunksChanged)  # Connect topKs signal
        self.tabs.addTab(self.chunking_tab, "✂️ Chunking")
        
        # Set strategyCombo reference for backward compatibility
        self.strategyCombo = self.chunking_tab.strategyCombo
        
        self.server_tab = ServerTab(self.config, self)
        self.tabs.addTab(self.server_tab, "🌐 Server")
        
        self.variables_tab = VariablesTab(self.config, self)
        self.tabs.addTab(self.variables_tab, "🔧 Variables")
        
        self.database_tab = DatabaseTab(self.config)
        self.tabs.addTab(self.database_tab, "💾 Database")
    
    def onStrategyComboChanged(self, text):
        """Forward to chunking tab's method"""
        if hasattr(self, 'chunking_tab'):
            self.chunking_tab.onStrategyComboChanged(text)
