# ui/options_widget.py
"""
Options Tab Widget for RAG Qt Application
Enhanced version with embedding models and chunking strategies
"""
from typing import Dict, List
from PySide6.QtWidgets import *
from PySide6.QtCore import Signal, Qt, QThread
from PySide6.QtGui import QFont
from pathlib import Path
import json
import logging
import sys
import os

logger = logging.getLogger(__name__)


class OptionsWidget(QWidget):
    """Enhanced options widget for system configuration"""
    
    strategyChanged = Signal(str)
    paramsChanged = Signal(dict)
    modelChanged = Signal(str, str)  # provider, model
    configReloaded = Signal()
    embeddingModelChanged = Signal(str, int)  # model_name, dimension
    foldersUpdated = Signal(list)  # List of watched folders
    
    def __init__(self, config_manager):
        super().__init__()
        self.config = config_manager
        
        # Embedding models configuration
        self.embedding_models = [
            {
                "name": "Multilingual MiniLM",
                "model_id": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
                "dim": 384,
                "description": "Best for multiple languages, balanced performance"
            },
            {
                "name": "E5 Small v2",
                "model_id": "intfloat/e5-small-v2",
                "dim": 384,
                "description": "Efficient and accurate for English"
            },
            {
                "name": "All MiniLM L6",
                "model_id": "sentence-transformers/all-MiniLM-L6-v2",
                "dim": 384,
                "description": "Fast and lightweight"
            },
            {
                "name": "All MPNet Base",
                "model_id": "sentence-transformers/all-mpnet-base-v2",
                "dim": 768,
                "description": "Highest quality, larger size"
            }
        ]
        
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
            response = requests.get(f"{self.config.get_server_url()}/api/chunkers/strategy")
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
        # Main layout with tabs
        layout = QVBoxLayout()
        
        # Title
        titleLabel = QLabel("⚙️ System Configuration")
        titleLabel.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px 0;")
        layout.addWidget(titleLabel)
        
        # Create tabs for different option categories
        self.tabs = QTabWidget()
        
        # Tab 1: LLM Models
        llmTab = self.createLLMTab()
        self.tabs.addTab(llmTab, "🤖 LLM Models")
        
        # Tab 2: Embedding Models
        embeddingTab = self.createEmbeddingTab()
        self.tabs.addTab(embeddingTab, "🧠 Embedding Models")
        
        # Tab 3: Chunking Strategy
        chunkingTab = self.createChunkingTab()
        self.tabs.addTab(chunkingTab, "✂️ Chunking")
        
        # Tab 4: Server Settings
        serverTab = self.createServerTab()
        self.tabs.addTab(serverTab, "🌐 Server")
        
        # Tab 5: System Variables
        variablesTab = self.createVariablesTab()
        self.tabs.addTab(variablesTab, "🔧 Variables")
        
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
        
        self.setLayout(layout)
    
    def createLLMTab(self):
        """Create LLM models configuration tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Model Configuration Section
        modelGroup = self.createModelSection()
        layout.addWidget(modelGroup)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def createVariablesTab(self):
        """Create system variables configuration tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Info
        info = QLabel("""
        <div style='background-color: #fff3e0; padding: 10px; border-radius: 5px;'>
        <b>🔧 System Variables:</b><br>
        Configure system-wide parameters used across server and client components.
        These values control timeouts, limits, and processing parameters.
        </div>
        """)
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # Load current variables
        try:
            import yaml
            with open('config/system_variables.yaml', 'r') as f:
                self.sys_vars = yaml.safe_load(f)
        except:
            self.sys_vars = self.getDefaultSystemVariables()
        
        # Create sections
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()
        
        # Timeout Settings
        timeout_group = QGroupBox("⏱️ Timeout Settings (seconds)")
        timeout_layout = QFormLayout()
        
        self.timeout_inputs = {}
        for key, value in self.sys_vars.get('timeouts', {}).items():
            spin = QSpinBox()
            spin.setRange(1, 3600)
            spin.setValue(value)
            spin.setSuffix(" sec")
            label = key.replace('_', ' ').title()
            timeout_layout.addRow(f"{label}:", spin)
            self.timeout_inputs[key] = spin
        
        timeout_group.setLayout(timeout_layout)
        scroll_layout.addWidget(timeout_group)
        
        # Limits Settings
        limits_group = QGroupBox("📏 Processing Limits")
        limits_layout = QFormLayout()
        
        self.limit_inputs = {}
        for key, value in self.sys_vars.get('limits', {}).items():
            if isinstance(value, int):
                spin = QSpinBox()
                spin.setRange(1, 100000)
                spin.setValue(value)
                label = key.replace('_', ' ').title()
                limits_layout.addRow(f"{label}:", spin)
                self.limit_inputs[key] = spin
        
        limits_group.setLayout(limits_layout)
        scroll_layout.addWidget(limits_group)
        
        # Apply button
        apply_vars_btn = QPushButton("Apply Variables")
        apply_vars_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        apply_vars_btn.clicked.connect(self.applySystemVariables)
        scroll_layout.addWidget(apply_vars_btn)
        
        scroll_layout.addStretch()
        scroll_widget.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        
        layout.addWidget(scroll_area)
        widget.setLayout(layout)
        return widget
    
    def getDefaultSystemVariables(self):
        """Get default system variables"""
        return {
            'timeouts': {
                'server_request': 300,
                'ingest_request': 600,
                'health_check': 5
            },
            'limits': {
                'max_context_chars': 8000,
                'max_chunks_per_request': 20,
                'default_top_k': 5,
                'batch_size': 10
            },
            'file_processing': {
                'supported_extensions': ['.pdf', '.txt', '.md', '.json', '.docx'],
                'max_file_size_mb': 50,
                'chunk_overlap': 200,
                'chunk_size': 1200
            }
        }
    
    def applySystemVariables(self):
        """Apply system variables"""
        try:
            # Update timeouts
            for key, widget in self.timeout_inputs.items():
                self.sys_vars['timeouts'][key] = widget.value()
            
            # Update limits
            for key, widget in self.limit_inputs.items():
                self.sys_vars['limits'][key] = widget.value()
            
            # Save to file
            import yaml
            with open('config/system_variables.yaml', 'w') as f:
                yaml.dump(self.sys_vars, f, default_flow_style=False)
            
            QMessageBox.information(self, "Success", "System variables updated successfully!")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save variables: {str(e)}")
    
    def createEmbeddingTab(self):
        """Create embedding model configuration tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Info about namespaces
        info = QLabel("""
        <div style='background-color: #e3f2fd; padding: 10px; border-radius: 5px;'>
        <b>🎯 Smart Namespace Management:</b><br>
        Each embedding model maintains its own vector space. You can switch between models
        without losing your indexed documents! Each model's data is stored separately.
        </div>
        """)
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # Current namespaces
        namespaces_group = QGroupBox("📚 Available Vector Spaces")
        namespaces_layout = QVBoxLayout()
        
        self.namespaces_list = QListWidget()
        self.namespaces_list.setMaximumHeight(150)
        namespaces_layout.addWidget(self.namespaces_list)
        
        refresh_btn = QPushButton("🔄 Refresh Namespaces")
        refresh_btn.clicked.connect(self.refreshNamespaces)
        namespaces_layout.addWidget(refresh_btn)
        
        namespaces_group.setLayout(namespaces_layout)
        layout.addWidget(namespaces_group)
        
        # Model selection
        models_group = QGroupBox("🤖 Select Embedding Model")
        models_layout = QVBoxLayout()
        
        self.model_radios = {}
        for model in self.embedding_models:
            radio = QRadioButton(f"{model['name']} ({model['dim']}d)")
            radio.setToolTip(f"{model['model_id']}\n{model['description']}")
            self.model_radios[model['model_id']] = radio
            models_layout.addWidget(radio)
            
            desc = QLabel(f"   {model['description']}")
            desc.setStyleSheet("color: #666; font-size: 11px; margin-left: 20px;")
            models_layout.addWidget(desc)
        
        # Select first by default
        list(self.model_radios.values())[0].setChecked(True)
        
        models_group.setLayout(models_layout)
        layout.addWidget(models_group)
        
        # Apply button
        apply_btn = QPushButton("Apply Model Change")
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
        apply_btn.clicked.connect(self.applyEmbeddingModel)
        layout.addWidget(apply_btn)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def createVariablesTab(self):
        """Create system variables configuration tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Info
        info = QLabel("""
        <div style='background-color: #fff3e0; padding: 10px; border-radius: 5px;'>
        <b>🔧 System Variables:</b><br>
        Configure system-wide parameters used across server and client components.
        These values control timeouts, limits, and processing parameters.
        </div>
        """)
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # Load current variables
        try:
            import yaml
            with open('config/system_variables.yaml', 'r') as f:
                self.sys_vars = yaml.safe_load(f)
        except:
            self.sys_vars = self.getDefaultSystemVariables()
        
        # Create sections
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()
        
        # Timeout Settings
        timeout_group = QGroupBox("⏱️ Timeout Settings (seconds)")
        timeout_layout = QFormLayout()
        
        self.timeout_inputs = {}
        for key, value in self.sys_vars.get('timeouts', {}).items():
            spin = QSpinBox()
            spin.setRange(1, 3600)
            spin.setValue(value)
            spin.setSuffix(" sec")
            label = key.replace('_', ' ').title()
            timeout_layout.addRow(f"{label}:", spin)
            self.timeout_inputs[key] = spin
        
        timeout_group.setLayout(timeout_layout)
        scroll_layout.addWidget(timeout_group)
        
        # Limits Settings
        limits_group = QGroupBox("📏 Processing Limits")
        limits_layout = QFormLayout()
        
        self.limit_inputs = {}
        for key, value in self.sys_vars.get('limits', {}).items():
            if isinstance(value, int):
                spin = QSpinBox()
                spin.setRange(1, 100000)
                spin.setValue(value)
                label = key.replace('_', ' ').title()
                limits_layout.addRow(f"{label}:", spin)
                self.limit_inputs[key] = spin
        
        limits_group.setLayout(limits_layout)
        scroll_layout.addWidget(limits_group)
        
        # Apply button
        apply_vars_btn = QPushButton("Apply Variables")
        apply_vars_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        apply_vars_btn.clicked.connect(self.applySystemVariables)
        scroll_layout.addWidget(apply_vars_btn)
        
        scroll_layout.addStretch()
        scroll_widget.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        
        layout.addWidget(scroll_area)
        widget.setLayout(layout)
        return widget
    
    def getDefaultSystemVariables(self):
        """Get default system variables"""
        return {
            'timeouts': {
                'server_request': 300,
                'ingest_request': 600,
                'health_check': 5
            },
            'limits': {
                'max_context_chars': 8000,
                'max_chunks_per_request': 20,
                'default_top_k': 5,
                'batch_size': 10
            },
            'file_processing': {
                'supported_extensions': ['.pdf', '.txt', '.md', '.json', '.docx'],
                'max_file_size_mb': 50,
                'chunk_overlap': 200,
                'chunk_size': 1200
            }
        }
    
    def applySystemVariables(self):
        """Apply system variables"""
        try:
            # Update timeouts
            for key, widget in self.timeout_inputs.items():
                self.sys_vars['timeouts'][key] = widget.value()
            
            # Update limits
            for key, widget in self.limit_inputs.items():
                self.sys_vars['limits'][key] = widget.value()
            
            # Save to file
            import yaml
            with open('config/system_variables.yaml', 'w') as f:
                yaml.dump(self.sys_vars, f, default_flow_style=False)
            
            QMessageBox.information(self, "Success", "System variables updated successfully!")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save variables: {str(e)}")
    
    def createFolderWatchTab(self):
        """Create folder watching configuration tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Info
        info = QLabel("""
        <div style='background-color: #f3e5f5; padding: 10px; border-radius: 5px;'>
        <b>📂 Automatic Document Ingestion:</b><br>
        Add folders to watch, and any new documents (PDF, MD, TXT) added to these folders
        will be automatically ingested into the RAG system.
        </div>
        """)
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # Watched folders list
        folders_group = QGroupBox("Watched Folders")
        folders_layout = QVBoxLayout()
        
        self.folders_list = QListWidget()
        folders_layout.addWidget(self.folders_list)
        
        # Folder controls
        folder_btns = QHBoxLayout()
        
        add_folder_btn = QPushButton("➕ Add Folder")
        add_folder_btn.clicked.connect(self.addWatchFolder)
        
        remove_folder_btn = QPushButton("➖ Remove Folder")
        remove_folder_btn.clicked.connect(self.removeWatchFolder)
        
        folder_btns.addWidget(add_folder_btn)
        folder_btns.addWidget(remove_folder_btn)
        folder_btns.addStretch()
        
        folders_layout.addLayout(folder_btns)
        folders_group.setLayout(folders_layout)
        layout.addWidget(folders_group)
        
        # Watcher controls
        watcher_group = QGroupBox("Watcher Control")
        watcher_layout = QVBoxLayout()
        
        # Status
        self.watcher_status = QLabel("Status: ⏹️ Not running")
        self.watcher_status.setStyleSheet("padding: 10px; background-color: #f0f0f0; border-radius: 5px;")
        watcher_layout.addWidget(self.watcher_status)
        
        # Control buttons
        control_btns = QHBoxLayout()
        
        self.start_watch_btn = QPushButton("▶️ Start Watching")
        self.start_watch_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.start_watch_btn.clicked.connect(self.startWatching)
        
        self.stop_watch_btn = QPushButton("⏹️ Stop Watching")
        self.stop_watch_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:disabled {
                background-color: #ccc;
            }
        """)
        self.stop_watch_btn.clicked.connect(self.stopWatching)
        self.stop_watch_btn.setEnabled(False)
        
        control_btns.addWidget(self.start_watch_btn)
        control_btns.addWidget(self.stop_watch_btn)
        control_btns.addStretch()
        
        watcher_layout.addLayout(control_btns)
        watcher_group.setLayout(watcher_layout)
        layout.addWidget(watcher_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def createVariablesTab(self):
        """Create system variables configuration tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Info
        info = QLabel("""
        <div style='background-color: #fff3e0; padding: 10px; border-radius: 5px;'>
        <b>🔧 System Variables:</b><br>
        Configure system-wide parameters used across server and client components.
        These values control timeouts, limits, and processing parameters.
        </div>
        """)
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # Load current variables
        try:
            import yaml
            with open('config/system_variables.yaml', 'r') as f:
                self.sys_vars = yaml.safe_load(f)
        except:
            self.sys_vars = self.getDefaultSystemVariables()
        
        # Create sections
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()
        
        # Timeout Settings
        timeout_group = QGroupBox("⏱️ Timeout Settings (seconds)")
        timeout_layout = QFormLayout()
        
        self.timeout_inputs = {}
        for key, value in self.sys_vars.get('timeouts', {}).items():
            spin = QSpinBox()
            spin.setRange(1, 3600)
            spin.setValue(value)
            spin.setSuffix(" sec")
            label = key.replace('_', ' ').title()
            timeout_layout.addRow(f"{label}:", spin)
            self.timeout_inputs[key] = spin
        
        timeout_group.setLayout(timeout_layout)
        scroll_layout.addWidget(timeout_group)
        
        # Limits Settings
        limits_group = QGroupBox("📏 Processing Limits")
        limits_layout = QFormLayout()
        
        self.limit_inputs = {}
        for key, value in self.sys_vars.get('limits', {}).items():
            if isinstance(value, int):
                spin = QSpinBox()
                spin.setRange(1, 100000)
                spin.setValue(value)
                label = key.replace('_', ' ').title()
                limits_layout.addRow(f"{label}:", spin)
                self.limit_inputs[key] = spin
        
        limits_group.setLayout(limits_layout)
        scroll_layout.addWidget(limits_group)
        
        # Apply button
        apply_vars_btn = QPushButton("Apply Variables")
        apply_vars_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        apply_vars_btn.clicked.connect(self.applySystemVariables)
        scroll_layout.addWidget(apply_vars_btn)
        
        scroll_layout.addStretch()
        scroll_widget.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        
        layout.addWidget(scroll_area)
        widget.setLayout(layout)
        return widget
    
    def getDefaultSystemVariables(self):
        """Get default system variables"""
        return {
            'timeouts': {
                'server_request': 300,
                'ingest_request': 600,
                'health_check': 5
            },
            'limits': {
                'max_context_chars': 8000,
                'max_chunks_per_request': 20,
                'default_top_k': 5,
                'batch_size': 10
            },
            'file_processing': {
                'supported_extensions': ['.pdf', '.txt', '.md', '.json', '.docx'],
                'max_file_size_mb': 50,
                'chunk_overlap': 200,
                'chunk_size': 1200
            }
        }
    
    def applySystemVariables(self):
        """Apply system variables"""
        try:
            # Update timeouts
            for key, widget in self.timeout_inputs.items():
                self.sys_vars['timeouts'][key] = widget.value()
            
            # Update limits
            for key, widget in self.limit_inputs.items():
                self.sys_vars['limits'][key] = widget.value()
            
            # Save to file
            import yaml
            with open('config/system_variables.yaml', 'w') as f:
                yaml.dump(self.sys_vars, f, default_flow_style=False)
            
            QMessageBox.information(self, "Success", "System variables updated successfully!")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save variables: {str(e)}")
    
    def createChunkingTab(self):
        """Create chunking configuration tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Chunking Strategy Section  
        strategyGroup = self.createStrategySection()
        layout.addWidget(strategyGroup)
        
        # Parameters Section
        paramsGroup = self.createParametersSection()
        layout.addWidget(paramsGroup)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def createVariablesTab(self):
        """Create system variables configuration tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Info
        info = QLabel("""
        <div style='background-color: #fff3e0; padding: 10px; border-radius: 5px;'>
        <b>🔧 System Variables:</b><br>
        Configure system-wide parameters used across server and client components.
        These values control timeouts, limits, and processing parameters.
        </div>
        """)
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # Load current variables
        try:
            import yaml
            with open('config/system_variables.yaml', 'r') as f:
                self.sys_vars = yaml.safe_load(f)
        except:
            self.sys_vars = self.getDefaultSystemVariables()
        
        # Create sections
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()
        
        # Timeout Settings
        timeout_group = QGroupBox("⏱️ Timeout Settings (seconds)")
        timeout_layout = QFormLayout()
        
        self.timeout_inputs = {}
        for key, value in self.sys_vars.get('timeouts', {}).items():
            spin = QSpinBox()
            spin.setRange(1, 3600)
            spin.setValue(value)
            spin.setSuffix(" sec")
            label = key.replace('_', ' ').title()
            timeout_layout.addRow(f"{label}:", spin)
            self.timeout_inputs[key] = spin
        
        timeout_group.setLayout(timeout_layout)
        scroll_layout.addWidget(timeout_group)
        
        # Limits Settings
        limits_group = QGroupBox("📏 Processing Limits")
        limits_layout = QFormLayout()
        
        self.limit_inputs = {}
        for key, value in self.sys_vars.get('limits', {}).items():
            if isinstance(value, int):
                spin = QSpinBox()
                spin.setRange(1, 100000)
                spin.setValue(value)
                label = key.replace('_', ' ').title()
                limits_layout.addRow(f"{label}:", spin)
                self.limit_inputs[key] = spin
        
        limits_group.setLayout(limits_layout)
        scroll_layout.addWidget(limits_group)
        
        # Apply button
        apply_vars_btn = QPushButton("Apply Variables")
        apply_vars_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        apply_vars_btn.clicked.connect(self.applySystemVariables)
        scroll_layout.addWidget(apply_vars_btn)
        
        scroll_layout.addStretch()
        scroll_widget.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        
        layout.addWidget(scroll_area)
        widget.setLayout(layout)
        return widget
    
    def getDefaultSystemVariables(self):
        """Get default system variables"""
        return {
            'timeouts': {
                'server_request': 300,
                'ingest_request': 600,
                'health_check': 5
            },
            'limits': {
                'max_context_chars': 8000,
                'max_chunks_per_request': 20,
                'default_top_k': 5,
                'batch_size': 10
            },
            'file_processing': {
                'supported_extensions': ['.pdf', '.txt', '.md', '.json', '.docx'],
                'max_file_size_mb': 50,
                'chunk_overlap': 200,
                'chunk_size': 1200
            }
        }
    
    def applySystemVariables(self):
        """Apply system variables"""
        try:
            # Update timeouts
            for key, widget in self.timeout_inputs.items():
                self.sys_vars['timeouts'][key] = widget.value()
            
            # Update limits
            for key, widget in self.limit_inputs.items():
                self.sys_vars['limits'][key] = widget.value()
            
            # Save to file
            import yaml
            with open('config/system_variables.yaml', 'w') as f:
                yaml.dump(self.sys_vars, f, default_flow_style=False)
            
            QMessageBox.information(self, "Success", "System variables updated successfully!")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save variables: {str(e)}")
    
    def createServerTab(self):
        """Create server settings tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Server Info Section
        serverGroup = self.createServerInfoSection()
        layout.addWidget(serverGroup)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def createVariablesTab(self):
        """Create system variables configuration tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Info
        info = QLabel("""
        <div style='background-color: #fff3e0; padding: 10px; border-radius: 5px;'>
        <b>🔧 System Variables:</b><br>
        Configure system-wide parameters used across server and client components.
        These values control timeouts, limits, and processing parameters.
        </div>
        """)
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # Load current variables
        try:
            import yaml
            with open('config/system_variables.yaml', 'r') as f:
                self.sys_vars = yaml.safe_load(f)
        except:
            self.sys_vars = self.getDefaultSystemVariables()
        
        # Create sections
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()
        
        # Timeout Settings
        timeout_group = QGroupBox("⏱️ Timeout Settings (seconds)")
        timeout_layout = QFormLayout()
        
        self.timeout_inputs = {}
        for key, value in self.sys_vars.get('timeouts', {}).items():
            spin = QSpinBox()
            spin.setRange(1, 3600)
            spin.setValue(value)
            spin.setSuffix(" sec")
            label = key.replace('_', ' ').title()
            timeout_layout.addRow(f"{label}:", spin)
            self.timeout_inputs[key] = spin
        
        timeout_group.setLayout(timeout_layout)
        scroll_layout.addWidget(timeout_group)
        
        # Limits Settings
        limits_group = QGroupBox("📏 Processing Limits")
        limits_layout = QFormLayout()
        
        self.limit_inputs = {}
        for key, value in self.sys_vars.get('limits', {}).items():
            if isinstance(value, int):
                spin = QSpinBox()
                spin.setRange(1, 100000)
                spin.setValue(value)
                label = key.replace('_', ' ').title()
                limits_layout.addRow(f"{label}:", spin)
                self.limit_inputs[key] = spin
        
        limits_group.setLayout(limits_layout)
        scroll_layout.addWidget(limits_group)
        
        # Apply button
        apply_vars_btn = QPushButton("Apply Variables")
        apply_vars_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        apply_vars_btn.clicked.connect(self.applySystemVariables)
        scroll_layout.addWidget(apply_vars_btn)
        
        scroll_layout.addStretch()
        scroll_widget.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        
        layout.addWidget(scroll_area)
        widget.setLayout(layout)
        return widget
    
    def getDefaultSystemVariables(self):
        """Get default system variables"""
        return {
            'timeouts': {
                'server_request': 300,
                'ingest_request': 600,
                'health_check': 5
            },
            'limits': {
                'max_context_chars': 8000,
                'max_chunks_per_request': 20,
                'default_top_k': 5,
                'batch_size': 10
            },
            'file_processing': {
                'supported_extensions': ['.pdf', '.txt', '.md', '.json', '.docx'],
                'max_file_size_mb': 50,
                'chunk_overlap': 200,
                'chunk_size': 1200
            }
        }
    
    def applySystemVariables(self):
        """Apply system variables"""
        try:
            # Update timeouts
            for key, widget in self.timeout_inputs.items():
                self.sys_vars['timeouts'][key] = widget.value()
            
            # Update limits
            for key, widget in self.limit_inputs.items():
                self.sys_vars['limits'][key] = widget.value()
            
            # Save to file
            import yaml
            with open('config/system_variables.yaml', 'w') as f:
                yaml.dump(self.sys_vars, f, default_flow_style=False)
            
            QMessageBox.information(self, "Success", "System variables updated successfully!")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save variables: {str(e)}")
    
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
    
    # New methods for enhanced features
    def refreshNamespaces(self):
        """Refresh the list of available namespaces"""
        self.namespaces_list.clear()
        
        # This would connect to ChromaDB and list collections
        # For now, showing mock data
        try:
            import requests
            response = requests.get(f"{self.config.get_server_url()}/api/namespaces")
            if response.status_code == 200:
                namespaces = response.json()
                for ns in namespaces:
                    self.namespaces_list.addItem(f"{ns['name']} ({ns['count']} docs)")
        except:
            # Mock data for demo
            namespaces = [
                "rag_documents_multilingual_minilm_a1b2c3d4 (1,234 docs)",
                "rag_documents_e5_small_v2_e5f6g7h8 (567 docs)",
                "rag_documents_all_minilm_i9j0k1l2 (89 docs)"
            ]
            for ns in namespaces:
                self.namespaces_list.addItem(ns)
    
    def applyEmbeddingModel(self):
        """Apply embedding model change"""
        selected_model = None
        for model_id, radio in self.model_radios.items():
            if radio.isChecked():
                # Find model info
                for model in self.embedding_models:
                    if model['model_id'] == model_id:
                        selected_model = model
                        break
                break
        
        if selected_model:
            reply = QMessageBox.information(
                self, "Model Change",
                f"Switching to: {selected_model['name']}\n\n"
                f"The system will now use the vector space for this model.\n"
                f"If this is a new model, you'll need to ingest documents.\n"
                f"If you've used this model before, your existing index will be available!",
                QMessageBox.Ok | QMessageBox.Cancel
            )
            
            if reply == QMessageBox.Ok:
                self.embeddingModelChanged.emit(
                    selected_model['model_id'],
                    selected_model['dim']
                )
                # Refresh namespaces to show current
                self.refreshNamespaces()
    
    # Folder watching methods
    def addWatchFolder(self):
        """Add a folder to watch list"""
        folder = QFileDialog.getExistingDirectory(
            self, "Select Folder to Watch",
            str(Path.home())
        )
        
        if folder and folder not in self.watched_folders:
            if self.folder_watcher and self.folder_watcher.add_folder(folder):
                self.watched_folders.append(folder)
                self.folders_list.addItem(folder)
                self.foldersUpdated.emit(self.watched_folders)
    
    def removeWatchFolder(self):
        """Remove selected folder from watch list"""
        current = self.folders_list.currentItem()
        if current and self.folder_watcher:
            folder = current.text()
            if self.folder_watcher.remove_folder(folder):
                self.watched_folders.remove(folder)
                self.folders_list.takeItem(self.folders_list.row(current))
                self.foldersUpdated.emit(self.watched_folders)
    
    def startWatching(self):
        """Start the folder watcher"""
        if self.folder_watcher and self.watched_folders:
            self.folder_watcher.start()
            self.watcher_status.setText("Status: ✅ Watching...")
            self.start_watch_btn.setEnabled(False)
            self.stop_watch_btn.setEnabled(True)
        else:
            QMessageBox.warning(self, "No Folders", 
                              "Please add at least one folder to watch first.")
    
    def stopWatching(self):
        """Stop the folder watcher"""
        if self.folder_watcher:
            self.folder_watcher.stop()
            self.watcher_status.setText("Status: ⏹️ Stopped")
            self.start_watch_btn.setEnabled(True)
            self.stop_watch_btn.setEnabled(False)
    
    def auto_ingest_document(self, file_path):
        """Callback for automatic document ingestion"""
        from pathlib import Path
        
        # Here you would call the actual ingest API
        # For now, just log it
        print(f"Auto-ingesting: {Path(file_path).name}")
    
    def saveAllSettings(self):
        """Save all settings across all tabs"""
        try:
            # Save LLM settings
            provider = self.providerCombo.currentText()
            model = self.modelCombo.currentText()
            self.config.set_model(provider, model)
            self.config.set("llm.temperature", self.temperatureSpin.value(), 'server')
            self.config.set("llm.max_tokens", self.maxTokensSpin.value(), 'server')
            
            # Save chunking settings
            self.config.set("chunker.default_strategy", self.currentStrategy, 'server')
            self.config.set("chunker.default_params", self.getParams(), 'server')
            
            # Save watched folders
            self.config.set("options.watched_folders", self.watched_folders, 'client')
            
            QMessageBox.information(self, "Success", "All settings saved successfully!")
            self.configReloaded.emit()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save settings: {str(e)}")
    
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
