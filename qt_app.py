# qt_app_final.py
"""
Qt6 RAG Interface with Configuration Management
"""
import sys
import json
import os
import yaml
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *

import requests

# Import file loader
sys.path.append(os.path.join(os.path.dirname(__file__), 'rag'))
from file_loader import FileLoader, BatchLoader


class AppConfig:
    """Application configuration manager"""
    def __init__(self):
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        """Load configuration from YAML file"""
        config_path = Path("config/qt_app_config.yaml")
        if not config_path.exists():
            # Fallback to defaults if config file doesn't exist
            return {
                "server": {"url": "http://localhost:8000", "timeout": 30},
                "ui": {
                    "defaults": {"top_k": 5},
                    "window": {"width": 1400, "height": 900}
                }
            }
        
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def get(self, key: str, default=None):
        """Get configuration value by dot notation"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, default)
            else:
                return default
        return value


# Global config instance
app_config = AppConfig()


class RagWorkerThread(QThread):
    """Background worker for API calls"""
    finished = Signal(dict)
    error = Signal(str)
    progress = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.baseUrl = app_config.get("server.url", "http://localhost:8000")
        self.timeout = app_config.get("server.timeout", 30)
        self.task = None
        self.payload = None
    
    def setTask(self, task: str, payload=None):
        self.task = task
        self.payload = payload
    
    def run(self):
        try:
            if self.task == "health":
                self.progress.emit("Checking server...")
                response = requests.get(f"{self.baseUrl}/health", timeout=5)
                self.finished.emit({"task": "health", "result": response.json()})
                
            elif self.task == "ingest":
                self.progress.emit("Ingesting documents...")
                response = requests.post(
                    f"{self.baseUrl}/ingest",
                    json={"documents": self.payload},
                    timeout=self.timeout
                )
                self.finished.emit({"task": "ingest", "result": response.json()})
                
            elif self.task == "ask":
                self.progress.emit("Getting answer...")
                response = requests.post(
                    f"{self.baseUrl}/ask",
                    json=self.payload,
                    timeout=self.timeout
                )
                self.finished.emit({"task": "ask", "result": response.json()})
            
            elif self.task == "get_strategies":
                self.progress.emit("Getting strategies...")
                response = requests.get(f"{self.baseUrl}/api/chunkers/strategies", timeout=5)
                self.finished.emit({"task": "get_strategies", "result": response.json()})
            
            elif self.task == "set_strategy":
                self.progress.emit("Setting strategy...")
                response = requests.post(
                    f"{self.baseUrl}/api/chunkers/strategy",
                    json={"strategy": self.payload},
                    timeout=5
                )
                self.finished.emit({"task": "set_strategy", "result": response.json()})
            
            elif self.task == "get_params":
                self.progress.emit("Getting parameters...")
                response = requests.get(f"{self.baseUrl}/api/chunkers/params", timeout=5)
                self.finished.emit({"task": "get_params", "result": response.json()})
            
            elif self.task == "set_params":
                self.progress.emit("Setting parameters...")
                response = requests.post(
                    f"{self.baseUrl}/api/chunkers/params",
                    json=self.payload,
                    timeout=5
                )
                self.finished.emit({"task": "set_params", "result": response.json()})
                
        except requests.ConnectionError as e:
            self.error.emit(f"Cannot connect to server at {self.baseUrl}. Please check:\n"
                          f"1. Server is running (python server.py)\n"
                          f"2. Server is on correct port (check config.yaml)\n"
                          f"Error: {str(e)}")
        except requests.Timeout:
            self.error.emit(f"Request timed out after {self.timeout} seconds")
        except Exception as e:
            self.error.emit(f"Error: {str(e)}")


class ChatWidget(QWidget):
    """Chat interface widget with Ingest button"""
    
    ingestRequested = Signal()  # Signal for ingest request
    
    def __init__(self):
        super().__init__()
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout()
        
        # Top toolbar with Ingest button
        topToolbar = QHBoxLayout()
        
        # Ingest Documents button
        self.ingestBtn = QPushButton("📥 Ingest Documents")
        self.ingestBtn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.ingestBtn.clicked.connect(self.ingestRequested.emit)
        topToolbar.addWidget(self.ingestBtn)
        
        topToolbar.addStretch()
        
        # Settings
        topToolbar.addWidget(QLabel("Top K:"))
        
        self.topKSpin = QSpinBox()
        self.topKSpin.setRange(1, 20)
        default_top_k = app_config.get("ui.defaults.top_k", 5)
        self.topKSpin.setValue(default_top_k)
        topToolbar.addWidget(self.topKSpin)
        
        clearBtn = QPushButton("Clear Chat")
        clearBtn.clicked.connect(self.clearChat)
        topToolbar.addWidget(clearBtn)
        
        # Chat display
        self.chatDisplay = QTextBrowser()
        self.chatDisplay.setOpenExternalLinks(True)
        
        # Input area
        inputLayout = QHBoxLayout()
        self.inputField = QLineEdit()
        self.inputField.setPlaceholderText("Ask a question...")
        max_length = app_config.get("chat.max_message_length", 10000)
        self.inputField.setMaxLength(max_length)
        
        self.sendBtn = QPushButton("Send")
        
        inputLayout.addWidget(self.inputField)
        inputLayout.addWidget(self.sendBtn)
        
        # Add to main layout
        layout.addLayout(topToolbar)
        layout.addWidget(self.chatDisplay)
        layout.addLayout(inputLayout)
        
        self.setLayout(layout)
    
    def addMessage(self, sender: str, message: str, metadata: Dict = None):
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Color based on sender
        color = "#1e88e5" if sender == "You" else "#43a047"
        
        html = f"""
        <div style="margin: 10px 0;">
            <b style="color: {color};">{sender}</b> <span style="color: #888;">[{timestamp}]</span>
            <div style="margin-top: 5px; padding: 10px; background-color: #f5f5f5; border-radius: 5px;">
                {message}
            </div>
        """
        
        if metadata:
            html += '<div style="color: #666; font-size: 0.9em; margin-top: 5px;">'
            if metadata.get("ctxIds"):
                html += f'📚 Contexts: {len(metadata["ctxIds"])} | '
            if metadata.get("latencyMs"):
                html += f'⏱️ Time: {metadata["latencyMs"]}ms'
            html += '</div>'
        
        html += "</div><hr>"
        
        self.chatDisplay.append(html)
        
        # Auto-scroll if enabled
        if app_config.get("chat.auto_scroll", True):
            scrollbar = self.chatDisplay.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
    
    def clearChat(self):
        self.chatDisplay.clear()
    
    def getQuestion(self) -> str:
        return self.inputField.text().strip()
    
    def clearInput(self):
        self.inputField.clear()
    
    def getTopK(self) -> int:
        return self.topKSpin.value()


class OptionsWidget(QWidget):
    """Options widget for chunking strategy configuration"""
    
    def __init__(self):
        super().__init__()
        self.strategies = []
        self.currentStrategy = ""
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout()
        
        # Title
        titleLabel = QLabel("⚙️ Chunking Strategy Configuration")
        titleLabel.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px 0;")
        layout.addWidget(titleLabel)
        
        # Server URL display
        serverInfoLayout = QHBoxLayout()
        serverInfoLayout.addWidget(QLabel("Server URL:"))
        serverUrlLabel = QLabel(app_config.get("server.url", "http://localhost:8000"))
        serverUrlLabel.setStyleSheet("font-weight: bold; color: #666;")
        serverInfoLayout.addWidget(serverUrlLabel)
        serverInfoLayout.addStretch()
        layout.addLayout(serverInfoLayout)
        
        # Strategy selection
        strategyGroup = QGroupBox("Strategy Selection")
        strategyLayout = QVBoxLayout()
        
        # Current strategy display
        self.currentStrategyLabel = QLabel("Current Strategy: Loading...")
        self.currentStrategyLabel.setStyleSheet("font-weight: bold; color: #1976d2;")
        strategyLayout.addWidget(self.currentStrategyLabel)
        
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
        strategyLayout.addLayout(selectorLayout)
        
        # Strategy description
        self.strategyDescLabel = QLabel()
        self.strategyDescLabel.setWordWrap(True)
        self.strategyDescLabel.setStyleSheet("color: #666; margin-top: 10px;")
        strategyLayout.addWidget(self.strategyDescLabel)
        
        strategyGroup.setLayout(strategyLayout)
        layout.addWidget(strategyGroup)
        
        # Parameters configuration
        paramsGroup = QGroupBox("Chunking Parameters")
        paramsLayout = QFormLayout()
        
        # Parameter inputs
        self.paramInputs = {}
        
        params = [
            ("maxTokens", "Max Tokens:", QSpinBox, (100, 5000, 512)),
            ("windowSize", "Window Size:", QSpinBox, (200, 10000, 1200)),
            ("overlap", "Overlap:", QSpinBox, (0, 1000, 200)),
            ("semanticThreshold", "Semantic Threshold:", QDoubleSpinBox, (0.0, 1.0, 0.82)),
            ("sentenceMinLen", "Min Sentence Length:", QSpinBox, (1, 100, 10)),
            ("paragraphMinLen", "Min Paragraph Length:", QSpinBox, (10, 500, 50)),
        ]
        
        for key, label, widget_class, (min_val, max_val, default) in params:
            widget = widget_class()
            if widget_class == QSpinBox:
                widget.setRange(min_val, max_val)
                widget.setValue(default)
            else:  # QDoubleSpinBox
                widget.setRange(min_val, max_val)
                widget.setSingleStep(0.01)
                widget.setValue(default)
            
            self.paramInputs[key] = widget
            paramsLayout.addRow(label, widget)
        
        # Language selector
        self.languageCombo = QComboBox()
        self.languageCombo.addItems(["ko", "en"])
        self.paramInputs["language"] = self.languageCombo
        paramsLayout.addRow("Language:", self.languageCombo)
        
        # Apply parameters button
        applyParamsBtn = QPushButton("Apply Parameters")
        applyParamsBtn.clicked.connect(self.onParamsApply)
        paramsLayout.addRow("", applyParamsBtn)
        
        paramsGroup.setLayout(paramsLayout)
        layout.addWidget(paramsGroup)
        
        # Information panel
        infoGroup = QGroupBox("Strategy Guide")
        infoLayout = QVBoxLayout()
        
        infoText = """
        <b>🎯 Strategy Selection Guide:</b><br>
        • <b>sentence</b>: Best for Q&A, chat logs, short content<br>
        • <b>paragraph</b>: Ideal for structured documents, manuals<br>
        • <b>sliding_window</b>: Good for long narratives, novels<br>
        • <b>adaptive</b>: Automatically chooses best approach<br>
        • <b>simple_overlap</b>: Simple fixed-size chunks with overlap<br>
        <br>
        <b>📊 Parameter Guidelines:</b><br>
        • <b>Max Tokens</b>: Maximum tokens per chunk (affects LLM context)<br>
        • <b>Window Size</b>: Size of sliding window in characters<br>
        • <b>Overlap</b>: Characters to overlap between chunks<br>
        • <b>Semantic Threshold</b>: Similarity threshold for semantic chunking<br>
        """
        
        infoLabel = QLabel(infoText)
        infoLabel.setWordWrap(True)
        infoLayout.addWidget(infoLabel)
        
        infoGroup.setLayout(infoLayout)
        layout.addWidget(infoGroup)
        
        layout.addStretch()
        self.setLayout(layout)
    
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
        
        # Update description
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
    
    def getSelectedStrategy(self) -> str:
        return self.strategyCombo.currentText()
    
    def getParams(self) -> Dict:
        params = {}
        for key, widget in self.paramInputs.items():
            if isinstance(widget, QSpinBox):
                params[key] = widget.value()
            elif isinstance(widget, QDoubleSpinBox):
                params[key] = widget.value()
            elif isinstance(widget, QComboBox):
                params[key] = widget.currentText()
        return params
    
    def onStrategyApply(self):
        """Placeholder for apply button - will be connected in MainWindow"""
        pass
    
    def onParamsApply(self):
        """Placeholder for params apply - will be connected in MainWindow"""
        pass
    
    def onRefreshStrategies(self):
        """Placeholder for refresh - will be connected in MainWindow"""
        pass


class DocumentWidget(QWidget):
    """Document management widget with file loading support"""
    def __init__(self):
        super().__init__()
        self.documents = []
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout()
        
        # File toolbar
        fileToolbar = QHBoxLayout()
        
        loadFileBtn = QPushButton("📄 Load File (PDF/MD/TXT)")
        loadFileBtn.clicked.connect(self.loadFile)
        
        loadDirBtn = QPushButton("📁 Load Directory")
        loadDirBtn.clicked.connect(self.loadDirectory)
        
        fileToolbar.addWidget(loadFileBtn)
        fileToolbar.addWidget(loadDirBtn)
        fileToolbar.addStretch()
        
        # Document toolbar
        toolbar = QHBoxLayout()
        
        addBtn = QPushButton("➕ Add Manual")
        addBtn.clicked.connect(self.addDocument)
        
        loadJsonBtn = QPushButton("📋 Load Sample Docs")
        loadJsonBtn.clicked.connect(self.loadSampleDocs)
        
        clearBtn = QPushButton("🗑️ Clear All")
        clearBtn.clicked.connect(self.clearDocuments)
        
        toolbar.addWidget(addBtn)
        toolbar.addWidget(loadJsonBtn)
        toolbar.addWidget(clearBtn)
        toolbar.addStretch()
        
        # Document form
        formLayout = QFormLayout()
        
        self.idEdit = QLineEdit()
        self.titleEdit = QLineEdit()
        self.sourceEdit = QLineEdit()
        self.textEdit = QPlainTextEdit()
        self.textEdit.setMaximumHeight(150)
        
        formLayout.addRow("ID:", self.idEdit)
        formLayout.addRow("Title:", self.titleEdit)
        formLayout.addRow("Source:", self.sourceEdit)
        formLayout.addRow("Text:", self.textEdit)
        
        # Document list
        self.docList = QListWidget()
        
        # Stats
        self.statsLabel = QLabel("0 documents loaded")
        self.statsLabel.setStyleSheet("font-weight: bold; color: #666;")
        
        # Add to layout
        layout.addLayout(fileToolbar)
        layout.addLayout(toolbar)
        layout.addLayout(formLayout)
        layout.addWidget(QLabel("<b>Documents:</b>"))
        layout.addWidget(self.docList)
        layout.addWidget(self.statsLabel)
        
        self.setLayout(layout)
    
    def loadFile(self):
        """Load a single file (PDF, MD, TXT)"""
        fileName, _ = QFileDialog.getOpenFileName(
            self, 
            "Select File", 
            "",
            "Supported Files (*.pdf *.md *.txt);;PDF Files (*.pdf);;Markdown Files (*.md);;Text Files (*.txt)"
        )
        
        if fileName:
            try:
                doc = FileLoader.load_file(fileName)
                self.documents.append(doc)
                self.updateList()
                QMessageBox.information(self, "Success", f"Loaded: {doc['title']}")
            except Exception as e:
                if "pdf" in fileName.lower() and "PyPDF2" in str(e):
                    QMessageBox.warning(
                        self, "PDF Support", 
                        "PDF support requires PyPDF2.\nInstall with: pip install PyPDF2"
                    )
                else:
                    QMessageBox.critical(self, "Error", f"Failed to load file: {str(e)}")
    
    def loadDirectory(self):
        """Load all supported files from a directory"""
        directory = QFileDialog.getExistingDirectory(self, "Select Directory")
        
        if directory:
            reply = QMessageBox.question(
                self, "Recursive?",
                "Include subdirectories?",
                QMessageBox.Yes | QMessageBox.No
            )
            recursive = reply == QMessageBox.Yes
            
            try:
                files = FileLoader.scan_directory(directory, recursive)
                if not files:
                    QMessageBox.information(self, "No Files", "No supported files found.")
                    return
                
                reply = QMessageBox.question(
                    self, "Confirm",
                    f"Found {len(files)} files. Load all?",
                    QMessageBox.Yes | QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    docs = BatchLoader.load_files(files)
                    self.documents.extend(docs)
                    self.updateList()
                    QMessageBox.information(self, "Success", f"Loaded {len(docs)} documents")
                    
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load directory: {str(e)}")
    
    def addDocument(self):
        doc_id = self.idEdit.text() or f"doc_{len(self.documents) + 1}"
        title = self.titleEdit.text()
        source = self.sourceEdit.text() or "manual"
        text = self.textEdit.toPlainText()
        
        if not title or not text:
            QMessageBox.warning(self, "Warning", "Title and Text are required")
            return
        
        doc = {
            "id": doc_id,
            "title": title,
            "source": source,
            "text": text,
            "type": "manual"
        }
        
        self.documents.append(doc)
        self.updateList()
        
        # Clear form
        self.idEdit.clear()
        self.titleEdit.clear()
        self.sourceEdit.clear()
        self.textEdit.clear()
    
    def loadSampleDocs(self):
        try:
            with open("sample_docs.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                self.documents.extend(data.get("documents", []))
                self.updateList()
                QMessageBox.information(self, "Success", f"Loaded {len(data.get('documents', []))} documents")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load sample docs: {str(e)}")
    
    def clearDocuments(self):
        if self.documents:
            reply = QMessageBox.question(
                self, "Confirm",
                f"Clear all {len(self.documents)} documents?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.documents = []
                self.updateList()
    
    def updateList(self):
        self.docList.clear()
        
        # Group by type
        type_counts = {}
        for doc in self.documents:
            doc_type = doc.get("type", "unknown")
            type_counts[doc_type] = type_counts.get(doc_type, 0) + 1
            
            # Add to list with icon
            icon = "📄" if doc_type == "pdf" else "📝" if doc_type == "md" else "📋"
            display_text = f"{icon} {doc['id']}: {doc['title']}"
            self.docList.addItem(display_text)
        
        # Update stats
        stats = f"📊 {len(self.documents)} documents"
        if type_counts:
            stats += " ("
            stats += ", ".join([f"{count} {dtype}" for dtype, count in type_counts.items()])
            stats += ")"
        self.statsLabel.setText(stats)
    
    def getDocuments(self) -> List[Dict]:
        return self.documents


class MainWindow(QMainWindow):
    """Main application window"""
    def __init__(self):
        super().__init__()
        self.worker = RagWorkerThread()
        self.worker.finished.connect(self.handleResult)
        self.worker.error.connect(self.handleError)
        self.worker.progress.connect(self.updateStatus)
        
        # Server check timer
        self.serverCheckTimer = QTimer()
        self.serverCheckTimer.timeout.connect(self.checkServer)
        check_interval = app_config.get("server.health_check_interval", 10) * 1000
        self.serverCheckTimer.start(check_interval)
        
        self.initUI()
        self.checkServer()
        
        # Auto-load strategies if enabled
        if app_config.get("options.auto_load_strategies", True):
            QTimer.singleShot(1000, self.loadChunkingStrategies)
    
    def initUI(self):
        title = app_config.get("ui.window.title", "RAG System - Qt6 Interface")
        self.setWindowTitle(title)
        
        width = app_config.get("ui.window.width", 1400)
        height = app_config.get("ui.window.height", 900)
        self.setGeometry(100, 100, width, height)
        
        # Set application style
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QTabWidget::pane {
                border: 1px solid #ddd;
                background-color: white;
            }
            QTabBar::tab {
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 2px solid #1976d2;
            }
        """)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        
        # Main layout
        layout = QVBoxLayout()
        
        # Tabs
        self.tabs = QTabWidget()
        
        # Chat tab
        self.chatWidget = ChatWidget()
        self.chatWidget.sendBtn.clicked.connect(self.askQuestion)
        self.chatWidget.inputField.returnPressed.connect(self.askQuestion)
        self.chatWidget.ingestRequested.connect(self.ingestDocuments)
        self.tabs.addTab(self.chatWidget, "💬 Chat")
        
        # Documents tab
        self.docWidget = DocumentWidget()
        self.tabs.addTab(self.docWidget, "📚 Documents")
        
        # Options tab
        self.optionsWidget = OptionsWidget()
        self.optionsWidget.onStrategyApply = self.applyStrategy
        self.optionsWidget.onParamsApply = self.applyParams
        self.optionsWidget.onRefreshStrategies = self.loadChunkingStrategies
        self.optionsWidget.strategyCombo.currentTextChanged.connect(
            self.optionsWidget.onStrategyComboChanged
        )
        self.tabs.addTab(self.optionsWidget, "⚙️ Options")
        
        # Logs tab
        self.logWidget = QPlainTextEdit()
        self.logWidget.setReadOnly(True)
        self.logWidget.setStyleSheet("font-family: 'Consolas', 'Monaco', monospace;")
        self.tabs.addTab(self.logWidget, "📜 Logs")
        
        layout.addWidget(self.tabs)
        central.setLayout(layout)
        
        # Create menu
        self.createMenu()
        
        # Status bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        
        self.serverStatus = QLabel("Server: Checking...")
        self.statusBar.addPermanentWidget(self.serverStatus)
        
        self.strategyStatus = QLabel("Strategy: Loading...")
        self.statusBar.addPermanentWidget(self.strategyStatus)
    
    def createMenu(self):
        menubar = self.menuBar()
        
        # File menu
        fileMenu = menubar.addMenu("File")
        
        loadFileAction = QAction("Load File...", self)
        loadFileAction.setShortcut("Ctrl+O")
        loadFileAction.triggered.connect(self.docWidget.loadFile)
        fileMenu.addAction(loadFileAction)
        
        loadDirAction = QAction("Load Directory...", self)
        loadDirAction.setShortcut("Ctrl+D")
        loadDirAction.triggered.connect(self.docWidget.loadDirectory)
        fileMenu.addAction(loadDirAction)
        
        fileMenu.addSeparator()
        
        exitAction = QAction("Exit", self)
        exitAction.triggered.connect(self.close)
        fileMenu.addAction(exitAction)
        
        # Server menu
        serverMenu = menubar.addMenu("Server")
        
        checkAction = QAction("Check Status", self)
        checkAction.triggered.connect(self.checkServer)
        serverMenu.addAction(checkAction)
        
        ingestAction = QAction("Ingest Documents", self)
        ingestAction.setShortcut("Ctrl+I")
        ingestAction.triggered.connect(self.ingestDocuments)
        serverMenu.addAction(ingestAction)
        
        serverMenu.addSeparator()
        
        reloadConfigAction = QAction("Reload Config", self)
        reloadConfigAction.triggered.connect(self.reloadConfig)
        serverMenu.addAction(reloadConfigAction)
        
        # Help menu
        helpMenu = menubar.addMenu("Help")
        
        configInfoAction = QAction("Config Info", self)
        configInfoAction.triggered.connect(self.showConfigInfo)
        helpMenu.addAction(configInfoAction)
        
        aboutAction = QAction("About", self)
        aboutAction.triggered.connect(self.showAbout)
        helpMenu.addAction(aboutAction)
    
    def checkServer(self):
        if not self.worker.isRunning():
            self.worker.setTask("health")
            self.worker.start()
    
    def loadChunkingStrategies(self):
        """Load available chunking strategies"""
        self.worker.setTask("get_strategies")
        self.worker.start()
    
    def loadChunkingParams(self):
        """Load current chunking parameters"""
        self.worker.setTask("get_params")
        self.worker.start()
    
    def applyStrategy(self):
        """Apply selected chunking strategy"""
        strategy = self.optionsWidget.getSelectedStrategy()
        if strategy:
            self.worker.setTask("set_strategy", strategy)
            self.worker.start()
    
    def applyParams(self):
        """Apply chunking parameters"""
        params = self.optionsWidget.getParams()
        self.worker.setTask("set_params", params)
        self.worker.start()
    
    def reloadConfig(self):
        """Reload server configuration"""
        try:
            response = requests.get(f"{self.worker.baseUrl}/config/reload")
            if response.status_code == 200:
                QMessageBox.information(self, "Success", "Configuration reloaded")
                self.loadChunkingStrategies()
            else:
                QMessageBox.warning(self, "Warning", "Failed to reload configuration")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to reload config: {str(e)}")
    
    def showConfigInfo(self):
        """Show configuration information"""
        info = f"""
        <h3>Configuration Information</h3>
        <p><b>Server URL:</b> {app_config.get("server.url", "Not set")}</p>
        <p><b>Config Files:</b></p>
        <ul>
        <li>Server Config: config/config.yaml</li>
        <li>Qt App Config: config/qt_app_config.yaml</li>
        <li>Chunker Config: rag/chunkers/config.json</li>
        </ul>
        <p><b>Current Settings:</b></p>
        <ul>
        <li>Request Timeout: {app_config.get("server.timeout", 30)} seconds</li>
        <li>Health Check Interval: {app_config.get("server.health_check_interval", 10)} seconds</li>
        <li>Default Top K: {app_config.get("ui.defaults.top_k", 5)}</li>
        </ul>
        """
        QMessageBox.information(self, "Configuration Info", info)
    
    def ingestDocuments(self):
        docs = self.docWidget.getDocuments()
        if not docs:
            QMessageBox.warning(self, "Warning", "No documents to ingest")
            return
        
        reply = QMessageBox.question(
            self, "Confirm",
            f"Ingest {len(docs)} documents using current chunking strategy?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.worker.setTask("ingest", docs)
            self.worker.start()
    
    def askQuestion(self):
        question = self.chatWidget.getQuestion()
        if not question:
            return
        
        self.chatWidget.addMessage("You", question)
        self.chatWidget.clearInput()
        
        payload = {
            "question": question,
            "k": self.chatWidget.getTopK()
        }
        
        self.worker.setTask("ask", payload)
        self.worker.start()
    
    def handleResult(self, data: Dict):
        task = data["task"]
        result = data["result"]
        
        if task == "health":
            status = result.get("status", "unknown")
            if status == "ok":
                self.serverStatus.setText("🟢 Server: Online")
                self.serverStatus.setStyleSheet("color: green;")
            else:
                self.serverStatus.setText("🔴 Server: Offline")
                self.serverStatus.setStyleSheet("color: red;")
            self.log(f"Server status: {status}")
            
        elif task == "ingest":
            chunks = result.get("ingestedChunks", 0)
            docs = result.get("documentCount", 0)
            QMessageBox.information(
                self, "Success",
                f"✅ Ingested {docs} documents into {chunks} chunks"
            )
            self.log(f"Ingested {docs} documents into {chunks} chunks")
            
        elif task == "ask":
            answer = result.get("answer", "No answer")
            metadata = {
                "ctxIds": result.get("ctxIds", []),
                "latencyMs": result.get("latencyMs", 0)
            }
            self.chatWidget.addMessage("Assistant", answer, metadata)
            self.log(f"Answered in {metadata['latencyMs']}ms")
        
        elif task == "get_strategies":
            strategies = result.get("strategies", [])
            current = result.get("current", "unknown")
            self.optionsWidget.updateStrategies(strategies)
            self.strategyStatus.setText(f"📦 Strategy: {current}")
            self.log(f"Loaded {len(strategies)} strategies, current: {current}")
            # Also load parameters
            if strategies:
                self.loadChunkingParams()
        
        elif task == "set_strategy":
            strategy = result.get("strategy", "unknown")
            self.strategyStatus.setText(f"📦 Strategy: {strategy}")
            QMessageBox.information(self, "Success", f"Strategy changed to: {strategy}")
            self.log(f"Changed strategy to: {strategy}")
            # Reload strategies to update UI
            self.loadChunkingStrategies()
        
        elif task == "get_params":
            params = result
            self.optionsWidget.updateParams(params)
            self.log("Loaded chunking parameters")
        
        elif task == "set_params":
            QMessageBox.information(self, "Success", "Parameters updated")
            self.log("Updated chunking parameters")
            # Reload params to confirm
            self.loadChunkingParams()
    
    def handleError(self, error: str):
        QMessageBox.critical(self, "Error", error)
        self.log(f"ERROR: {error}")
        self.serverStatus.setText("🔴 Server: Error")
        self.serverStatus.setStyleSheet("color: red;")
    
    def updateStatus(self, message: str):
        self.statusBar.showMessage(message, 3000)
    
    def log(self, message: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.logWidget.appendPlainText(f"[{timestamp}] {message}")
        
        # Limit log lines
        max_lines = app_config.get("logging.max_log_lines", 1000)
        doc = self.logWidget.document()
        if doc.lineCount() > max_lines:
            cursor = QTextCursor(doc)
            cursor.movePosition(QTextCursor.Start)
            cursor.movePosition(QTextCursor.Down, QTextCursor.KeepAnchor, doc.lineCount() - max_lines)
            cursor.removeSelectedText()
    
    def showAbout(self):
        QMessageBox.about(
            self, "About",
            """<h2>RAG System Qt6 Interface</h2>
            <p>Retrieval-Augmented Generation System with Real-time Chunking Control</p>
            <p><b>Features:</b></p>
            <ul>
                <li>Real-time chunking strategy selection</li>
                <li>Configurable chunking parameters</li>
                <li>Document ingestion with multiple strategies</li>
                <li>Support for PDF, Markdown, and Text files</li>
                <li>Configuration-based settings management</li>
            </ul>
            <p><b>Configuration Files:</b></p>
            <ul>
                <li>config/config.yaml - Server configuration</li>
                <li>config/qt_app_config.yaml - Qt app settings</li>
            </ul>
            <p>Version 3.0</p>"""
        )
    
    def closeEvent(self, event):
        """Handle application close event"""
        self.serverCheckTimer.stop()
        event.accept()


def main():
    app = QApplication(sys.argv)
    
    # Set application style from config
    theme = app_config.get("ui.theme", "Fusion")
    app.setStyle(theme)
    
    # Set application icon if available
    icon_path = Path("icon.png")
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
