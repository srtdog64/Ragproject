# qt_app.py
"""
RAG System Qt6 Interface - Modular Architecture
Main application with separated UI components
"""
import sys
import os
import json
import time
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
from ui.progress_widget import IngestProgressWidget, AsyncProgressDialog


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
                self.progress.emit("Starting document ingestion...")
                print("[Worker] Starting ingest task")  # Debug
                
                docs = self.payload
                total_docs = len(docs)
                print(f"[Worker] Total documents to ingest: {total_docs}")  # Debug
                
                # Send initial ingestion request to start async task
                self.progressUpdate.emit(0, total_docs, "Creating ingestion task...")
                
                try:
                    response = requests.post(
                        f"{self.baseUrl}/api/ingest",
                        json={
                            "documents": docs,
                            "batch_size": 10  # Configurable batch size
                        },
                        timeout=30  # Increased timeout for initial request
                    )
                    print(f"[Worker] Ingest POST response: {response.status_code}")  # Debug
                    
                    if response.status_code == 200:
                        result = response.json()
                        task_id = result.get("task_id")
                        print(f"[Worker] Got task_id: {task_id}")  # Debug
                        
                        self.progress.emit(f"Task {task_id[:8]}... created")
                        
                        # Poll for task status indefinitely until completion
                        while True:
                            try:
                                status_url = f"{self.baseUrl}/api/ingest/status/{task_id}"
                                print(f"[Worker] Polling status: {status_url}")  # Debug
                                
                                # No timeout or very long timeout for status checks
                                status_response = requests.get(status_url, timeout=60)  # 60 seconds timeout
                                print(f"[Worker] Status response: {status_response.status_code}")  # Debug
                                
                                if status_response.status_code == 200:
                                    status = status_response.json()
                                    print(f"[Worker] Status data: {json.dumps(status, indent=2)}")  # Debug
                                    
                                    # Update progress
                                    progress = status.get("progress", 0)
                                    total = status.get("total", total_docs)
                                    current_item = status.get("current_item", "Processing...")
                                    percentage = status.get("progress_percentage", 0)
                                    task_status = status.get("status")
                                    
                                    print(f"[Worker] Progress: {progress}/{total} ({percentage:.1f}%) - Status: {task_status}")  # Debug
                                    
                                    # Emit progress update
                                    self.progressUpdate.emit(
                                        progress, total, 
                                        f"{current_item} ({percentage:.1f}%)"
                                    )
                                    
                                    # Check task status
                                    if task_status == "completed":
                                        print("[Worker] Task completed!")  # Debug
                                        final_result = status.get("result", {})
                                        self.progressUpdate.emit(total, total, "Ingestion complete!")
                                        self.finished.emit({
                                            "task": "ingest",
                                            "result": {
                                                "ingestedChunks": final_result.get("total_chunks", 0),
                                                "documentCount": final_result.get("processed_documents", 0),
                                                "task_id": task_id
                                            }
                                        })
                                        break
                                        
                                    elif task_status == "failed":
                                        error = status.get("error", "Unknown error")
                                        print(f"[Worker] Task failed: {error}")  # Debug
                                        self.error.emit(f"Ingestion failed: {error}")
                                        break
                                        
                                    elif task_status == "cancelled":
                                        print("[Worker] Task cancelled")  # Debug
                                        self.error.emit("Ingestion task was cancelled")
                                        break
                                else:
                                    print(f"[Worker] Status check failed: {status_response.text}")  # Debug
                                
                                # Longer delay between polls to avoid overwhelming the server
                                time.sleep(1.0)  # 1 second delay
                                
                            except Exception as e:
                                print(f"[Worker] Error checking task status: {e}")  # Debug
                                self.error.emit(f"Error checking task status: {e}")
                                break
                            
                    else:
                        print(f"[Worker] Failed to start ingestion: {response.text}")  # Debug
                        self.error.emit(f"Failed to start ingestion: {response.text}")
                        
                except Exception as e:
                    print(f"[Worker] Exception in ingest task: {e}")  # Debug
                    import traceback
                    print(traceback.format_exc())  # Debug
                    self.error.emit(f"Ingestion error: {str(e)}")
                
            elif self.task == "ask":
                self.progress.emit("Getting answer...")
                print(f"[Worker] Sending question to server: {self.baseUrl}/api/ask")  # Debug log
                
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
                    f"{self.baseUrl}/api/ask",
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
                
            elif self.task == "get_vector_count":
                try:
                    response = requests.get(
                        f"{self.baseUrl}/api/rag/stats",
                        timeout=5  # Shorter timeout for background task
                    )
                    if response.status_code == 200:
                        self.finished.emit({"task": "get_vector_count", "result": response.json()})
                    else:
                        self.finished.emit({"task": "get_vector_count", "result": {"error": response.status_code}})
                except Exception as e:
                    self.finished.emit({"task": "get_vector_count", "result": {"error": str(e)}})
                
            elif self.task == "reload_config":
                self.progress.emit("Reloading configuration...")
                response = requests.get(f"{self.baseUrl}/api/config/reload", timeout=5)
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
        self.optionsWidget.contextChunksChanged.connect(self.chatWidget.setContextChunks)  # Connect topKs
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
        """Update vector count from server - non-blocking"""
        # Use worker thread for network request
        if not self.worker.isRunning():
            self.worker.setTask("get_vector_count")
            self.worker.start()
        else:
            # If worker is busy, skip this update
            self.logsWidget.debug("Skipping vector count update - worker busy")
    
    def onDocumentsChanged(self, count: int):
        """Handle document count change - triggers vector count update"""
        # Simply update the vector count from the database
        self.updateVectorCount()
    
    def onIngestionCompleted(self, result: dict):
        """Handle completion of async ingestion"""
        total_chunks = result.get("total_chunks", 0)
        processed_docs = result.get("processed_documents", 0)
        
        QMessageBox.information(
            self, "Ingestion Complete",
            f"✅ Successfully processed {processed_docs} documents\n"
            f"Generated {total_chunks} chunks"
        )
        
        self.logsWidget.success(f"Ingestion completed: {processed_docs} docs, {total_chunks} chunks")
        
        # Update vector count
        self.updateVectorCount()
    
    def onIngestionFailed(self, error: str):
        """Handle ingestion failure"""
        QMessageBox.critical(
            self, "Ingestion Failed",
            f"Failed to ingest documents:\n{error}"
        )
        
        self.logsWidget.error(f"Ingestion failed: {error}")
    
    def ingestSelectedDocuments(self, docs):
        """Ingest selected documents from advanced tab"""
        if not docs:
            QMessageBox.warning(self, "No Documents", "No documents selected")
            return
        
        if not self.serverOnline:
            QMessageBox.warning(self, "Server Offline", "Server is not available")
            return
        
        # Use the new progress widget
        progress_widget = IngestProgressWidget(self)
        progress_widget.ingestionCompleted.connect(self.onIngestionCompleted)
        progress_widget.ingestionFailed.connect(self.onIngestionFailed)
        
        # Get batch settings from advanced tab
        batch_settings = self.docWidget.advancedTab.getBatchSettings()
        batch_size = batch_settings.get('batch_size', 10)
        
        # Start ingestion with progress tracking
        task_id = progress_widget.start_ingestion(docs, batch_size=batch_size)
        
        if task_id:
            self.logsWidget.info(f"Started ingestion task: {task_id[:8]}...")
            self.logsWidget.info(f"Processing {len(docs)} documents with batch size {batch_size}")
        else:
            self.logsWidget.error("Failed to start ingestion task")
    
    def reloadConfig(self):
        """Reload server configuration"""
        if self.serverOnline:
            self.worker.setTask("reload_config")
            self.worker.start()
            self.logsWidget.info("Reloading configuration")
    
    def handleResult(self, data: Dict):
        """Handle worker thread results"""
        print(f"[Main] handleResult called with data: {json.dumps(data, indent=2)}")  # Debug
        
        task = data["task"]
        result = data["result"]
        
        print(f"[Main] Task: {task}, Result type: {type(result)}")  # Debug
        
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
            print(f"[Main] Processing ingest result: {result}")  # Debug
            chunks = result.get("ingestedChunks", 0)
            docs = result.get("documentCount", 0)
            task_id = result.get("task_id", "")
            
            print(f"[Main] Chunks: {chunks}, Docs: {docs}, Task ID: {task_id}")  # Debug
            
            # Update progress to 100% then hide
            self.chatWidget.setIngestionProgress(docs, docs, "Complete!")
            # Hide progress bar after a short delay
            QTimer.singleShot(1000, lambda: self.chatWidget.hideIngestionProgress())
            
            QMessageBox.information(
                self, "Ingestion Complete",
                f"✅ Successfully ingested {docs} documents into {chunks} chunks\n"
                f"Task ID: {task_id[:8]}..."
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
        
        elif task == "get_vector_count":
            if "error" in result:
                self.vectorCountLabel.setText("🗃️ Vectors: --")
                self.vectorCountLabel.setToolTip(f"Error: {result.get('error')}")
                self.vectorCountLabel.setStyleSheet("padding: 5px; color: #6e7781;")
            else:
                vector_count = result.get('total_vectors', 0)
                namespace = result.get('namespace', 'default')
                store_type = result.get('store_type', 'unknown')
                
                if vector_count > 0:
                    self.vectorCountLabel.setText(f"🗃️ Vectors: {vector_count:,}")
                    self.vectorCountLabel.setToolTip(
                        f"Total vectors in '{namespace}' namespace\n"
                        f"Store type: {store_type}"
                    )
                    self.vectorCountLabel.setStyleSheet("padding: 5px; color: #1a7f37;")
                else:
                    self.vectorCountLabel.setText("🗃️ Vectors: 0")
                    self.vectorCountLabel.setToolTip(
                        f"No vectors in '{namespace}' namespace yet.\n"
                        f"Store: {store_type}\n"
                        f"Ingest documents to create vectors."
                    )
                    self.vectorCountLabel.setStyleSheet("padding: 5px; color: #cf222e;")
                
                self.logsWidget.debug(f"Vector count: {vector_count:,} in '{namespace}' ({store_type})")
        
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
            
            <p>© JDW</p>"""
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
