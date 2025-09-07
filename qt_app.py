# qt_app.py
"""
RAG System Qt6 Interface - Modular Architecture
Main application with separated UI components
"""
import sys
import os
from pathlib import Path
from typing import Dict, Optional

from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *

import requests
import yaml

# Add paths
sys.path.append(os.path.join(os.path.dirname(__file__), 'rag'))

# Import UI components
from ui import (
    ChatWidget, 
    DocumentsWidget, 
    OptionsWidget,  # Use original options widget
    LogsWidget,
    ConfigManager
)


class RagWorkerThread(QThread):
    """Background worker for API calls"""
    finished = Signal(dict)
    error = Signal(str)
    progress = Signal(str)
    progressUpdate = Signal(int, int, str)  # current, total, message
    
    def __init__(self, config_manager):
        super().__init__()
        self.config = config_manager
        self.baseUrl = self.config.get_server_url()
        
        # Load system variables
        try:
            import yaml
            with open('config/system_variables.yaml', 'r') as f:
                sys_vars = yaml.safe_load(f)
                self.timeout = sys_vars['timeouts']['ingest_request']  # 600 seconds
        except:
            self.timeout = 300  # Fallback to 5 minutes
            
        self.task = None
        self.payload = None
    
    def setTask(self, task: str, payload=None):
        print(f"[Worker] setTask called: task={task}, payload={payload}")  # Debug log
        self.task = task
        self.payload = payload
    
    def run(self):
        print(f"[Worker] run() started with task: {self.task}")  # Debug log
        try:
            if self.task == "health":
                self.progress.emit("Checking server...")
                response = requests.get(f"{self.baseUrl}/health", timeout=5)
                self.finished.emit({"task": "health", "result": response.json()})
                
            elif self.task == "ingest":
                self.progress.emit("Ingesting documents...")
                
                # Batch processing for large document sets
                batch_size = 10
                docs = self.payload
                total_docs = len(docs)
                
                if total_docs > batch_size:
                    # Process in batches
                    ingested_chunks = 0
                    processed_docs = 0
                    
                    for i in range(0, total_docs, batch_size):
                        batch = docs[i:i + batch_size]
                        current_batch_size = len(batch)
                        
                        # Update progress before processing
                        self.progressUpdate.emit(processed_docs, total_docs, 
                                               f"Processing {processed_docs}/{total_docs} documents...")
                        
                        response = requests.post(
                            f"{self.baseUrl}/ingest",
                            json={"documents": batch},
                            timeout=self.timeout
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            ingested_chunks += result.get("ingestedChunks", 0)
                            processed_docs += current_batch_size
                            
                            # Update progress after processing
                            self.progressUpdate.emit(processed_docs, total_docs,
                                                   f"Processed {processed_docs}/{total_docs} documents")
                    
                    self.finished.emit({
                        "task": "ingest", 
                        "result": {
                            "ingestedChunks": ingested_chunks,
                            "documentCount": total_docs
                        }
                    })
                else:
                    # Small batch, process all at once
                    self.progressUpdate.emit(0, total_docs, "Processing documents...")
                    
                    response = requests.post(
                        f"{self.baseUrl}/ingest",
                        json={"documents": docs},
                        timeout=self.timeout
                    )
                    
                    self.progressUpdate.emit(total_docs, total_docs, "Complete!")
                    self.finished.emit({"task": "ingest", "result": response.json()})
                
            elif self.task == "ask":
                self.progress.emit("Getting answer...")
                print(f"[Worker] Sending question to server: {self.baseUrl}/ask")  # Debug log
                
                # Include model info in request if available
                provider = self.config.get_current_provider()
                model = self.config.get_current_model()
                
                request_payload = {
                    **self.payload,
                    "provider": provider,  # Changed from model_provider
                    "model": model  # Changed from model_name
                }
                
                print(f"[Worker] Request payload: {request_payload}")  # Debug log
                
                response = requests.post(
                    f"{self.baseUrl}/ask",
                    json=request_payload,
                    timeout=self.timeout
                )
                print(f"[Worker] Response received: {response.status_code}")  # Debug log
                self.finished.emit({"task": "ask", "result": response.json()})
            
            elif self.task == "set_strategy":
                self.progress.emit("Setting strategy...")
                # Simply update config instead of API call
                strategy = self.payload
                self.config.set("chunker.default_strategy", strategy, 'server')
                self.finished.emit({"task": "set_strategy", "result": {"strategy": strategy}})
            
            elif self.task == "set_params":
                self.progress.emit("Setting parameters...")
                # Simply update config instead of API call
                params = self.payload
                self.config.set("chunker.default_params", params, 'server')
                self.finished.emit({"task": "set_params", "result": {"status": "ok"}})
                
            elif self.task == "reload_config":
                self.progress.emit("Reloading configuration...")
                response = requests.get(f"{self.baseUrl}/config/reload", timeout=5)
                self.finished.emit({"task": "reload_config", "result": {"status": "ok"}})
                
        except requests.ConnectionError as e:
            self.error.emit(f"Cannot connect to server at {self.baseUrl}\n"
                          f"Please check:\n"
                          f"1. Server is running (python start_server.py)\n"
                          f"2. Server URL in config/qt_app_config.yaml\n"
                          f"Error: {str(e)}")
        except requests.Timeout:
            self.error.emit(f"Request timed out after {self.timeout} seconds")
        except Exception as e:
            self.error.emit(f"Error: {str(e)}")


class MainWindow(QMainWindow):
    """Main application window with modular UI components"""
    
    def __init__(self):
        super().__init__()
        
        # Initialize configuration manager
        self.config = ConfigManager()
        
        # Initialize worker thread
        self.worker = RagWorkerThread(self.config)
        self.worker.finished.connect(self.handleResult)
        self.worker.error.connect(self.handleError)
        self.worker.progress.connect(self.updateStatus)
        self.worker.progressUpdate.connect(self.updateIngestionProgress)
        
        # Server status
        self.serverOnline = False
        
        # Response timeout timer
        self.responseTimer = QTimer()
        self.responseTimer.timeout.connect(self.handleResponseTimeout)
        self.responseTimer.setSingleShot(True)
        
        # Initialize UI
        self.initUI()
        
        # Setup timers
        self.setupTimers()
        
        # Initial checks
        self.checkServer()
        # Update vector count on startup
        QTimer.singleShot(1000, self.updateVectorCount)  # Slight delay to ensure server is ready
        # No need to load strategies anymore - they're static
    
    def initUI(self):
        """Initialize the user interface"""
        # Window settings
        self.setWindowTitle("RAG System - Modular Qt6 Interface")
        self.setGeometry(100, 100, 1400, 900)
        
        # Apply style
        self.applyStyle()
        
        # Create central widget
        central = QWidget()
        self.setCentralWidget(central)
        
        # Main layout
        layout = QVBoxLayout()
        
        # Create tab widget
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)
        
        # Create and add tabs
        self.createTabs()
        
        layout.addWidget(self.tabs)
        central.setLayout(layout)
        
        # Create menus
        self.createMenus()
        
        # Create status bar
        self.createStatusBar()
    
    def applyStyle(self):
        """Apply application styling"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QTabWidget::pane {
                border: 1px solid #ddd;
                background-color: white;
                border-radius: 4px;
            }
            QTabBar::tab {
                padding: 10px 20px;
                margin-right: 2px;
                background-color: #e0e0e0;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 3px solid #1976d2;
            }
            QTabBar::tab:hover {
                background-color: #f0f0f0;
            }
            QStatusBar {
                background-color: #ffffff;
                border-top: 1px solid #e0e0e0;
            }
        """)
    
    def createTabs(self):
        """Create and configure tabs"""
        # Chat tab
        self.chatWidget = ChatWidget(self.config)
        self.chatWidget.ingestRequested.connect(self.ingestDocuments)
        self.chatWidget.questionAsked.connect(self.askQuestion)
        self.tabs.addTab(self.chatWidget, "💬 Chat")
        
        # Documents tab
        self.docWidget = DocumentsWidget(self.config)
        self.docWidget.documentsChanged.connect(self.onDocumentsChanged)
        self.docWidget.selectiveIngestRequested.connect(self.ingestSelectedDocuments)
        self.tabs.addTab(self.docWidget, "📚 Documents")
        
        # Options tab
        self.optionsWidget = OptionsWidget(self.config)
        self.optionsWidget.strategyChanged.connect(self.applyStrategy)
        self.optionsWidget.paramsChanged.connect(self.applyParams)
        self.optionsWidget.modelChanged.connect(self.onModelChanged)
        self.optionsWidget.configReloaded.connect(self.reloadConfig)
        # Remove reference to loadChunkingStrategies
        self.optionsWidget.strategyCombo.currentTextChanged.connect(
            self.optionsWidget.onStrategyComboChanged
        )
        self.tabs.addTab(self.optionsWidget, "⚙️ Options")
        
        # Logs tab
        self.logsWidget = LogsWidget(self.config)
        self.tabs.addTab(self.logsWidget, "📜 Logs")
    
    def createMenus(self):
        """Create application menus"""
        menubar = self.menuBar()
        
        # File menu
        fileMenu = menubar.addMenu("&File")
        
        loadFileAction = QAction("📄 Load File...", self)
        loadFileAction.setShortcut("Ctrl+O")
        loadFileAction.triggered.connect(self.docWidget.loadFile)
        fileMenu.addAction(loadFileAction)
        
        loadDirAction = QAction("📁 Load Directory...", self)
        loadDirAction.setShortcut("Ctrl+D")
        loadDirAction.triggered.connect(self.docWidget.loadDirectory)
        fileMenu.addAction(loadDirAction)
        
        fileMenu.addSeparator()
        
        exportDocsAction = QAction("💾 Export Documents...", self)
        exportDocsAction.triggered.connect(self.docWidget.exportDocuments)
        fileMenu.addAction(exportDocsAction)
        
        exportLogsAction = QAction("📝 Export Logs...", self)
        exportLogsAction.triggered.connect(self.logsWidget.exportLogs)
        fileMenu.addAction(exportLogsAction)
        
        fileMenu.addSeparator()
        
        exitAction = QAction("Exit", self)
        exitAction.setShortcut("Ctrl+Q")
        exitAction.triggered.connect(self.close)
        fileMenu.addAction(exitAction)
        
        # Server menu
        serverMenu = menubar.addMenu("&Server")
        
        checkStatusAction = QAction("🔍 Check Status", self)
        checkStatusAction.setShortcut("F5")
        checkStatusAction.triggered.connect(self.checkServer)
        serverMenu.addAction(checkStatusAction)
        
        serverMenu.addSeparator()
        
        ingestAction = QAction("📥 Ingest Documents", self)
        ingestAction.setShortcut("Ctrl+I")
        ingestAction.triggered.connect(self.ingestDocuments)
        serverMenu.addAction(ingestAction)
        
        serverMenu.addSeparator()
        
        reloadConfigAction = QAction("🔄 Reload Configuration", self)
        reloadConfigAction.triggered.connect(self.reloadConfig)
        serverMenu.addAction(reloadConfigAction)
        
        # View menu
        viewMenu = menubar.addMenu("&View")
        
        for i, (name, icon) in enumerate([
            ("Chat", "💬"),
            ("Documents", "📚"),
            ("Options", "⚙️"),
            ("Logs", "📜")
        ]):
            action = QAction(f"{icon} {name}", self)
            action.setShortcut(f"Alt+{i+1}")
            action.triggered.connect(lambda checked, idx=i: self.tabs.setCurrentIndex(idx))
            viewMenu.addAction(action)
        
        # Help menu
        helpMenu = menubar.addMenu("&Help")
        
        configInfoAction = QAction("📋 Configuration Info", self)
        configInfoAction.triggered.connect(self.showConfigInfo)
        helpMenu.addAction(configInfoAction)
        
        helpMenu.addSeparator()
        
        aboutAction = QAction("ℹ️ About", self)
        aboutAction.triggered.connect(self.showAbout)
        helpMenu.addAction(aboutAction)
        
        aboutQtAction = QAction("About Qt", self)
        aboutQtAction.triggered.connect(lambda: QMessageBox.aboutQt(self))
        helpMenu.addAction(aboutQtAction)
    
    def createStatusBar(self):
        """Create status bar with indicators"""
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        
        # Server status
        self.serverStatusLabel = QLabel("🔴 Server: Checking...")
        self.serverStatusLabel.setStyleSheet("padding: 5px;")
        self.statusBar.addPermanentWidget(self.serverStatusLabel)
        
        # Model status  
        provider = self.config.get_current_provider()
        model = self.config.get_current_model()
        self.modelStatusLabel = QLabel(f"🧠 {provider}: {model}")
        self.modelStatusLabel.setStyleSheet("padding: 5px;")
        self.statusBar.addPermanentWidget(self.modelStatusLabel)
        
        # Strategy status - fetch from server or use default
        strategy = self.fetchCurrentStrategy()
        self.strategyStatusLabel = QLabel(f"📦 Strategy: {strategy}")
        self.strategyStatusLabel.setStyleSheet("padding: 5px;")
        self.statusBar.addPermanentWidget(self.strategyStatusLabel)
        
        # Vector count from database
        self.vectorCountLabel = QLabel("🗃️ Vectors: --")
        self.vectorCountLabel.setStyleSheet("padding: 5px;")
        self.vectorCountLabel.setToolTip("Total vectors stored in the database")
        self.statusBar.addPermanentWidget(self.vectorCountLabel)
    
    def fetchCurrentStrategy(self) -> str:
        """Fetch current strategy from server at startup"""
        # Don't fail if server is not available
        if not hasattr(self, 'config'):
            return "adaptive"
            
        try:
            import requests
            # Short timeout for startup
            response = requests.get(
                f"{self.config.get_server_url()}/api/chunkers/strategy", 
                timeout=1
            )
            if response.status_code == 200:
                data = response.json()
                strategy = data.get('strategy', 'adaptive')
                print(f"Loaded strategy from server: {strategy}")
                return strategy
        except requests.exceptions.ConnectionError:
            print("Server not available, using default strategy")
        except requests.exceptions.Timeout:
            print("Server timeout, using default strategy")
        except Exception as e:
            print(f"Could not fetch strategy: {e}")
        
        # Fallback to config or default
        strategy = self.config.get("chunker.default_strategy", "adaptive", 'server')
        print(f"Using default strategy: {strategy}")
        return strategy
    
    def setupTimers(self):
        """Setup automatic timers"""
        # Server health check timer
        self.serverCheckTimer = QTimer()
        self.serverCheckTimer.timeout.connect(self.checkServer)
        interval = self.config.get("server.health_check_interval", 10) * 1000
        self.serverCheckTimer.start(interval)
    
    def checkServer(self):
        """Check server status"""
        if not self.worker.isRunning():
            self.worker.setTask("health")
            self.worker.start()
    

    def ingestDocuments(self):
        """Ingest documents to server"""
        # Check if folder watcher is busy
        if hasattr(self.docWidget, 'folder_watcher') and self.docWidget.folder_watcher:
            if self.docWidget.folder_watcher.is_busy():
                reply = QMessageBox.question(
                    self, "Watcher Active",
                    "Folder watcher is processing files. Do you want to proceed anyway?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply != QMessageBox.Yes:
                    return
        
        docs = self.docWidget.getDocuments()
        if not docs:
            QMessageBox.warning(self, "No Documents", "No documents to ingest")
            return
        
        if not self.serverOnline:
            QMessageBox.warning(self, "Server Offline", "Server is not available")
            return
        
        reply = QMessageBox.question(
            self, "Confirm Ingestion",
            f"Ingest {len(docs)} documents using current chunking strategy?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Show progress
            self.chatWidget.setIngestionProgress(0, len(docs), "Preparing...")
            
            # Process in batches for progress updates
            self.worker.setTask("ingest", docs)
            self.worker.start()
            self.logsWidget.info(f"Starting ingestion of {len(docs)} documents")
    
    def askQuestion(self, question: str, topK: int, strict_mode: bool = False):
        """Send question to server"""
        print(f"[MainWindow] askQuestion called: {question[:50]}...")  # Debug log
        
        if not self.serverOnline:
            print("[MainWindow] Server is offline")  # Debug log
            QMessageBox.warning(self, "Server Offline", "Server is not available")
            # Re-enable input if server is offline
            self.chatWidget.setInputEnabled(True)
            return
        
        # Check if worker is already running - if health check, ignore it
        if self.worker.isRunning():
            current_task = getattr(self.worker, 'task', None)
            if current_task == "health":
                # Stop health check and proceed with question
                print("[MainWindow] Stopping health check to process question")  # Debug log
                self.worker.terminate()
                self.worker.wait(500)  # Wait up to 500ms for termination
            elif current_task == "ask":
                print("[MainWindow] Already processing a question, ignoring request")  # Debug log
                return
            else:
                print(f"[MainWindow] Worker busy with task: {current_task}, queuing question")  # Debug log
        
        # Note: User message is already added in chat_widget.onSendMessage
        # Don't add it again here to avoid duplicate
        
        payload = {
            "question": question,
            "k": topK
            # strict_mode will be implemented later
        }
        
        print(f"[MainWindow] Setting worker task with payload: {payload}")  # Debug log
        self.worker.setTask("ask", payload)
        print(f"[MainWindow] Starting worker...")  # Debug log
        self.worker.start()
        
        # Start response timeout timer (30 seconds)
        self.responseTimer.start(30000)
        
        self.logsWidget.info(f"Asking question with top_k={topK}")
    
    def handleResponseTimeout(self):
        """Handle response timeout"""
        print("[MainWindow] Response timeout!")  # Debug log
        
        # Terminate worker if still running
        if self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait(1000)  # Wait up to 1 second for termination
        
        # Re-enable input
        self.chatWidget.setInputEnabled(True)
        
        # Show error message
        self.chatWidget.addMessage("Assistant", 
            "⚠️ Request timed out. The server might be busy or unresponsive. Please try again.")
        
        self.logsWidget.error("Request timed out after 30 seconds")
    
    def applyStrategy(self, strategy: str):
        """Apply selected chunking strategy"""
        if self.serverOnline:
            self.worker.setTask("set_strategy", strategy)
            self.worker.start()
            self.logsWidget.info(f"Applying strategy: {strategy}")
    
    def applyParams(self, params: Dict):
        """Apply chunking parameters"""
        if self.serverOnline:
            self.worker.setTask("set_params", params)
            self.worker.start()
            self.logsWidget.info("Applying chunking parameters")
    
    def onModelChanged(self, provider: str, model: str):
        """Handle model change"""
        self.modelStatusLabel.setText(f"🧠 {provider}: {model}")
        self.chatWidget.updateModelLabel(provider, model)
        self.logsWidget.success(f"Model changed to {provider}: {model}")
    
    def updateVectorCount(self):
        """Update vector count from server - shows total vectors in DB"""
        try:
            import requests
            response = requests.get(
                f"{self.config.get_server_url()}/api/rag/stats",
                timeout=5  # Increased timeout
            )
            
            print(f"[VectorCount] API Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                vector_count = data.get('total_vectors', 0)
                namespace = data.get('namespace', 'default')
                store_type = data.get('store_type', 'unknown')
                status = data.get('status', 'ok')
                
                # Log the response for debugging
                print(f"[VectorCount] Full Response: {data}")
                print(f"[VectorCount] Store Type: {store_type}")
                print(f"[VectorCount] Vector Count: {vector_count}")
                print(f"[VectorCount] Namespace: {namespace}")
                
                # Format with thousands separator
                if vector_count > 0:
                    self.vectorCountLabel.setText(f"🗃️ Vectors: {vector_count:,}")
                    self.vectorCountLabel.setToolTip(
                        f"Total vectors in '{namespace}' namespace\n"
                        f"Store: {store_type}\n"
                        f"Status: {status}\n"
                        f"Click to refresh"
                    )
                    self.vectorCountLabel.setStyleSheet("padding: 5px; color: #1a7f37;")  # Green for success
                else:
                    self.vectorCountLabel.setText(f"🗃️ Vectors: 0")
                    self.vectorCountLabel.setToolTip(
                        f"No vectors in '{namespace}' namespace yet.\n"
                        f"Store: {store_type}\n"
                        f"Ingest documents to create vectors."
                    )
                    self.vectorCountLabel.setStyleSheet("padding: 5px; color: #cf222e;")  # Red for empty
                    
                self.logsWidget.debug(f"Vector count: {vector_count:,} in '{namespace}' ({store_type})")
            else:
                # Non-200 response
                try:
                    error_data = response.json()
                    error_msg = error_data.get('detail', 'Unknown error')
                    print(f"[VectorCount] API Error: {error_msg}")
                except:
                    error_msg = f"Status {response.status_code}"
                
                self.vectorCountLabel.setText(f"🗃️ Vectors: Error")
                self.vectorCountLabel.setToolTip(f"Server error: {error_msg}")
                self.vectorCountLabel.setStyleSheet("padding: 5px; color: #d1242f;")
                self.logsWidget.warning(f"Vector count API error: {error_msg}")
                
        except requests.exceptions.Timeout:
            print("[VectorCount] Request timed out")
            self.vectorCountLabel.setText(f"🗃️ Vectors: --")
            self.vectorCountLabel.setToolTip("Request timed out. Server may be busy.")
            self.vectorCountLabel.setStyleSheet("padding: 5px; color: #6e7781;")  # Gray for timeout
            self.logsWidget.debug("Vector count request timed out")
            
        except requests.exceptions.ConnectionError as e:
            print(f"[VectorCount] Connection error: {e}")
            self.vectorCountLabel.setText(f"🗃️ Vectors: Offline")
            self.vectorCountLabel.setToolTip("Cannot connect to server. Check if server is running.")
            self.vectorCountLabel.setStyleSheet("padding: 5px; color: #6e7781;")  # Gray for offline
            self.logsWidget.debug("Cannot connect to server for vector count")
            
        except Exception as e:
            # Unknown error
            print(f"[VectorCount] Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            
            self.vectorCountLabel.setText(f"🗃️ Vectors: --")
            self.vectorCountLabel.setToolTip(f"Error: {str(e)}")
            self.vectorCountLabel.setStyleSheet("padding: 5px; color: #6e7781;")  # Gray for error
            self.logsWidget.debug(f"Unexpected error updating vector count: {e}")
    
    def onDocumentsChanged(self, count: int):
        """Handle document count change - triggers vector count update"""
        # Simply update the vector count from the database
        self.updateVectorCount()
    
    def ingestSelectedDocuments(self, docs):
        """Ingest selected documents from advanced tab"""
        if not docs:
            QMessageBox.warning(self, "No Documents", "No documents selected")
            return
        
        if not self.serverOnline:
            QMessageBox.warning(self, "Server Offline", "Server is not available")
            return
        
        # Get batch settings from advanced tab
        batch_settings = self.docWidget.advancedTab.getBatchSettings()
        
        # Show progress in advanced tab
        self.docWidget.advancedTab.setProgress(0, len(docs), "Starting...")
        
        # Process documents with batch settings
        self.worker.setTask("ingest", docs)
        self.worker.start()
        self.logsWidget.info(f"Starting selective ingestion of {len(docs)} documents")
        self.logsWidget.info(f"Batch size: {batch_settings['batch_size']}, Delay: {batch_settings['delay']}s")
    
    def reloadConfig(self):
        """Reload server configuration"""
        if self.serverOnline:
            self.worker.setTask("reload_config")
            self.worker.start()
            self.logsWidget.info("Reloading configuration")
    
    def handleResult(self, data: Dict):
        """Handle worker thread results"""
        task = data["task"]
        result = data["result"]
        
        # Stop response timer if running
        if self.responseTimer.isActive():
            self.responseTimer.stop()
        
        if task == "health":
            status = result.get("status", "unknown")
            if status == "ok":
                self.serverOnline = True
                self.serverStatusLabel.setText("🟢 Server: Online")
                self.serverStatusLabel.setStyleSheet("color: green; padding: 5px;")
                self.logsWidget.success("Server is online")
                
                # Update vector count when server comes online
                self.updateVectorCount()
                
                # Also fetch current strategy when server is confirmed online
                try:
                    strategy = self.fetchCurrentStrategy()
                    self.strategyStatusLabel.setText(f"📦 Strategy: {strategy}")
                except:
                    pass  # Don't fail if strategy fetch fails
            else:
                self.serverOnline = False
                self.serverStatusLabel.setText("🔴 Server: Offline")
                self.serverStatusLabel.setStyleSheet("color: red; padding: 5px;")
                self.logsWidget.error("Server is offline")
            
        elif task == "ingest":
            chunks = result.get("ingestedChunks", 0)
            docs = result.get("documentCount", 0)
            
            # Update progress to 100% then hide
            self.chatWidget.setIngestionProgress(docs, docs, "Complete!")
            # Hide progress bar after a short delay
            QTimer.singleShot(1000, lambda: self.chatWidget.hideIngestionProgress())
            
            QMessageBox.information(
                self, "Ingestion Complete",
                f"✅ Successfully ingested {docs} documents into {chunks} chunks"
            )
            self.logsWidget.success(f"Ingested {docs} documents into {chunks} chunks")
            
            # Update vector count display
            self.updateVectorCount()
            
        elif task == "ask":
            answer = result.get("answer", "No answer")
            metadata = {
                "ctxIds": result.get("ctxIds", []),
                "latencyMs": result.get("latencyMs", 0),
                "model": f"{self.config.get_current_provider()}: {self.config.get_current_model()}"
            }
            self.chatWidget.addMessage("Assistant", answer, metadata)
            self.logsWidget.info(f"Answer generated in {metadata['latencyMs']}ms")
            # Re-enable input after answer is received
            self.chatWidget.setInputEnabled(True)
        
        elif task == "set_strategy":
            strategy = result.get("strategy", "unknown")
            self.strategyStatusLabel.setText(f"📦 Strategy: {strategy}")
            QMessageBox.information(self, "Success", f"Strategy changed to: {strategy}")
            self.logsWidget.success(f"Changed strategy to: {strategy}")
        
        elif task == "set_params":
            QMessageBox.information(self, "Success", "Parameters updated successfully")
            self.logsWidget.success("Updated chunking parameters")
        
        elif task == "reload_config":
            QMessageBox.information(self, "Success", "Configuration reloaded")
            self.logsWidget.success("Configuration reloaded")
        
        # Update model status
        provider = self.config.get_current_provider()
        model = self.config.get_current_model()
        self.modelStatusLabel.setText(f"🧠 {provider}: {model}")
    
    def handleError(self, error: str):
        """Handle worker thread errors"""
        # Hide progress bar if visible
        self.chatWidget.setIngestionProgress(100, 100)
        
        # Re-enable input if it was disabled
        self.chatWidget.setInputEnabled(True)
        
        QMessageBox.critical(self, "Error", error)
        self.logsWidget.error(error)
        self.serverOnline = False
        self.serverStatusLabel.setText("🔴 Server: Error")
        self.serverStatusLabel.setStyleSheet("color: red; padding: 5px;")
    
    def updateIngestionProgress(self, current: int, total: int, message: str):
        """Update ingestion progress bar"""
        if total > 0:
            percentage = int((current / total) * 100)
            self.chatWidget.setIngestionProgress(current, total, f"{message} ({percentage}%)")
    
    def updateStatus(self, message: str):
        """Update status bar message"""
        self.statusBar.showMessage(message, 3000)
    
    def showConfigInfo(self):
        """Show configuration information dialog"""
        info = f"""
        <h3>Configuration Information</h3>
        
        <h4>Server Configuration</h4>
        <p><b>URL:</b> {self.config.get_server_url()}</p>
        <p><b>Provider:</b> {self.config.get_current_provider()}</p>
        <p><b>Model:</b> {self.config.get_current_model()}</p>
        
        <h4>Configuration Files</h4>
        <ul>
        <li><b>Server:</b> config/config.yaml</li>
        <li><b>Qt App:</b> config/qt_app_config.yaml</li>
        <li><b>Chunkers:</b> rag/chunkers/config.json</li>
        </ul>
        
        <h4>System Status</h4>
        <p><b>Server:</b> {'🟢 Online' if self.serverOnline else '🔴 Offline'}</p>
        <p><b>Documents:</b> {len(self.docWidget.getDocuments())}</p>
        <p><b>Log Entries:</b> {len(self.logsWidget.logBuffer)}</p>
        """
        
        dialog = QMessageBox(self)
        dialog.setWindowTitle("Configuration Information")
        dialog.setTextFormat(Qt.RichText)
        dialog.setText(info)
        dialog.exec()
    
    def showAbout(self):
        """Show about dialog"""
        QMessageBox.about(
            self, "About RAG System",
            """<h2>RAG System Qt6 Interface</h2>
            <p><b>Version 4.0</b> - Modular Architecture</p>
            
            <p>A Retrieval-Augmented Generation system with:</p>
            <ul>
            <li>🧠 Multiple LLM provider support (Gemini, OpenAI, Claude)</li>
            <li>📦 Real-time chunking strategy selection</li>
            <li>🎛️ Configurable parameters</li>
            <li>📚 Multi-format document support (PDF, MD, TXT)</li>
            <li>📊 Advanced logging and monitoring</li>
            <li>⚙️ Modular UI architecture</li>
            </ul>
            
            <p><b>Components:</b></p>
            <ul>
            <li>Chat Interface - Interactive Q&A</li>
            <li>Document Manager - File ingestion</li>
            <li>Options Panel - System configuration</li>
            <li>Log Viewer - System monitoring</li>
            </ul>
            
            <p>© 2025 RAG System Development Team</p>"""
        )
    
    def closeEvent(self, event):
        """Handle application close event"""
        self.serverCheckTimer.stop()
        
        # Save any pending configurations
        self.logsWidget.info("Application closing")
        
        event.accept()


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("RAG System")
    app.setOrganizationName("RAG Development")
    
    # Set style
    app.setStyle("Fusion")
    
    # Set application icon
    icon_path = Path("icon.png")
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
