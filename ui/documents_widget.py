"""
Documents Tab Widget for RAG Qt Application
Provides both simple and advanced document management
"""
import json
import sys
import os
from typing import List, Dict
from pathlib import Path
from PySide6.QtWidgets import *
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QAction
import os
import subprocess
import platform

# Import file loaders
try:
    from ui.file_loaders import FileLoader, BatchLoader
except ImportError:
    # Fallback if file_loaders is not available
    print("Warning: file_loaders module not found, using fallback")
    class FileLoader:
        def load_file(self, path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    text = f.read()
                    return {
                        "id": str(Path(path).stem),
                        "title": Path(path).stem,
                        "source": str(Path(path).parent),
                        "text": text
                    }
            except:
                return None
    
    class BatchLoader:
        def __init__(self):
            self.loader = FileLoader()
        
        def load_directory(self, directory):
            docs = []
            for file in Path(directory).iterdir():
                if file.suffix in ['.txt', '.md', '.pdf']:
                    doc = self.loader.load_file(file)
                    if doc:
                        docs.append(doc)
            return docs

# System path setup for rag module
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'rag'))

# Import folder watcher
try:
    from watchers.folder_watcher import FolderWatcher
except ImportError:
    FolderWatcher = None  # Will handle gracefully if not available

# Import selective ingest widget
try:
    from .selective_ingest_widget import SelectiveIngestWidget
except ImportError:
    # Fallback to simple widget if not available
    class SelectiveIngestWidget(QWidget):
        def __init__(self):
            super().__init__()
            layout = QVBoxLayout()
            layout.addWidget(QLabel("Advanced features not available"))
            self.setLayout(layout)
            self.ingestRequested = Signal(list)

# Import icon manager
from .icon_manager import get_icon, Icons


class DocumentsWidget(QWidget):
    """Document management widget with basic and advanced features"""
    
    documentsChanged = Signal(int)  # Emit document count
    selectiveIngestRequested = Signal(list)  # Emit selected documents for ingestion
    foldersUpdated = Signal(list)  # Emit watched folders list
    
    def __init__(self, config_manager):
        super().__init__()
        self.config = config_manager
        self.documents = []
        
        # Initialize folder watcher
        self.folder_watcher = None
        self.watched_folders = []
        if FolderWatcher:
            try:
                self.folder_watcher = FolderWatcher(ingest_callback=self.auto_ingest_document)
            except Exception as e:
                print(f"Could not initialize folder watcher: {e}")
        
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout()
        
        # Title
        titleLabel = QLabel("Document Management Center")
        titleLabel.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px 0;")
        layout.addWidget(titleLabel)
        
        # Create tab widget for document management
        self.tabWidget = QTabWidget()
        
        # Tab 1: Basic document management
        self.basicTab = self.createBasicTab()
        self.tabWidget.addTab(self.basicTab, "Document List")
        self.tabWidget.setTabIcon(0, get_icon(Icons.FILE))
        
        # Tab 2: Advanced selective ingestion
        self.advancedTab = SelectiveIngestWidget()
        self.advancedTab.ingestRequested.connect(self.selectiveIngestRequested.emit)
        self.tabWidget.addTab(self.advancedTab, "Selective Ingest")
        self.tabWidget.setTabIcon(1, get_icon(Icons.TARGET))
        
        # Tab 3: Folder Watching (if available)
        if self.folder_watcher:
            self.watchTab = self.createWatchTab()
            self.tabWidget.addTab(self.watchTab, "Auto-Ingest")
            self.tabWidget.setTabIcon(2, get_icon(Icons.FOLDER))
        
        layout.addWidget(self.tabWidget)
        self.setLayout(layout)
    
    def createBasicTab(self):
        """Create the basic document management tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # File operations toolbar
        fileToolbar = QHBoxLayout()
        
        loadFileBtn = QPushButton("Load File(s)")
        loadFileBtn.setIcon(get_icon(Icons.FILE))
        loadFileBtn.setToolTip("Load one or more files (Ctrl+Click for multiple selection)")
        loadFileBtn.clicked.connect(self.loadFile)
        loadFileBtn.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                background-color: #5EAF08;
                color: black;
                border-radius: 4px;
                font-weight: bold;
                hover: cursor;
            }
            QPushButton:hover {
                background-color: #5EAF08;
            }
        """)
        
        loadDirBtn = QPushButton("Load Directory")
        loadDirBtn.setIcon(get_icon(Icons.FOLDER))
        loadDirBtn.setToolTip("Load all supported files from a directory")
        loadDirBtn.clicked.connect(self.loadDirectory)
        loadDirBtn.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                background-color: #5EAF08;
                color: black;
                border-radius: 4px;
                font-weight: bold;
                hover: cursor;
            }
            QPushButton:hover {
                background-color: #5EAF08;
            }
        """)
        
        loadSampleBtn = QPushButton("Load Samples")
        loadSampleBtn.setIcon(get_icon(Icons.FILE))
        loadSampleBtn.setToolTip("Load sample documents")
        loadSampleBtn.clicked.connect(self.loadSampleDocs)
        loadSampleBtn.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                background-color: #FF9800;
                color: black;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        
        fileToolbar.addWidget(loadFileBtn)
        fileToolbar.addWidget(loadDirBtn)
        fileToolbar.addWidget(loadSampleBtn)
        fileToolbar.addStretch()
        
        clearBtn = QPushButton("Clear All")
        clearBtn.setIcon(get_icon(Icons.TRASH))
        clearBtn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: black;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        clearBtn.clicked.connect(self.clearDocuments)
        fileToolbar.addWidget(clearBtn)
        
        layout.addLayout(fileToolbar)
        
        # Stats display
        self.statsLabel = QLabel("Documents: 0 | Total Size: 0 KB")
        self.statsLabel.setStyleSheet("padding: 10px; background-color: #f5f5f5; border-radius: 4px;")
        layout.addWidget(self.statsLabel)
        
        # Document list with context menu
        self.docList = QListWidget()
        self.docList.setAlternatingRowColors(True)
        self.docList.setContextMenuPolicy(Qt.CustomContextMenu)
        self.docList.customContextMenuRequested.connect(self.showContextMenu)
        layout.addWidget(self.docList)
        
        # Export/Import buttons
        exportLayout = QHBoxLayout()
        
        exportBtn = QPushButton("Export Documents")
        exportBtn.setIcon(get_icon(Icons.SAVE))
        exportBtn.clicked.connect(self.exportDocuments)
        exportLayout.addWidget(exportBtn)
        
        importBtn = QPushButton("Import Documents")
        importBtn.setIcon(get_icon(Icons.FOLDER))
        importBtn.clicked.connect(self.importDocuments)
        exportLayout.addWidget(importBtn)
        
        exportLayout.addStretch()
        layout.addLayout(exportLayout)
        
        widget.setLayout(layout)
        return widget
    
    def loadFile(self):
        """Load single or multiple files"""
        filenames, _ = QFileDialog.getOpenFileNames(
            self, "Select File(s)",
            str(Path.home()),
            "Supported Files (*.pdf *.md *.txt);;PDF Files (*.pdf);;Markdown Files (*.md);;Text Files (*.txt);;All Files (*.*)"
        )
        
        if filenames:
            loader = FileLoader()
            loaded_count = 0
            failed_files = []
            
            for filename in filenames:
                try:
                    doc = loader.load_file(filename)  # Changed from load to load_file
                    
                    if doc:
                        self.documents.append(doc)
                        loaded_count += 1
                    else:
                        failed_files.append(Path(filename).name)
                        
                except Exception as e:
                    print(f"Error loading {filename}: {e}")
                    failed_files.append(Path(filename).name)
            
            # Update UI
            if loaded_count > 0:
                self.updateDocumentList()
                self.updateAdvancedTab()
    
    def auto_ingest_document(self, file_path):
        """Callback for automatic document ingestion from folder watcher"""
        from pathlib import Path
        import requests
        
        print(f"Auto-ingesting: {Path(file_path).name}")
        
        # Load the document
        loader = FileLoader()
        doc = loader.load_file(file_path)
        
        if doc:
            try:
                # Send to server for ingestion
                response = requests.post(
                    f"{self.config.get_server_url()}/api/ingest",
                    json={"documents": [doc]},
                    headers={"Content-Type": "application/json"},
                    timeout=60
                )
                
                if response.status_code == 200:
                    print(f"Successfully ingested: {Path(file_path).name}")
                    # Add to documents list
                    self.documents.append(doc)
                    self.updateDocumentList()
                    self.documentsChanged.emit(len(self.documents))
                else:
                    print(f"Failed to ingest: {Path(file_path).name}")
                    
            except Exception as e:
                print(f"Error during auto-ingest: {str(e)}")
        else:
            print(f"Could not load file: {Path(file_path).name}")
    
    def createWatchTab(self):
        """Create folder watching tab for auto-ingestion"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Info
        info = QLabel("""
        <div style='background-color: #e8f5e9; padding: 10px; border-radius: 5px;'>
        <b>📂 Automatic Document Ingestion:</b><br>
        Add folders to watch. Any new documents (PDF, MD, TXT) added to these folders
        will be automatically ingested into the RAG system.
        </div>
        """)
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # Watched folders list
        folders_group = QGroupBox("Watched Folders")
        folders_layout = QVBoxLayout()
        
        self.folders_list = QListWidget()
        self.folders_list.setMinimumHeight(100)  # Reduced from 150
        folders_layout.addWidget(self.folders_list)
        
        # Folder controls
        folder_btns = QHBoxLayout()
        
        add_folder_btn = QPushButton("➕ Add Folder")
        add_folder_btn.clicked.connect(self.addWatchFolder)
        add_folder_btn.setStyleSheet("""
            QPushButton {
                background-color: #397B06;
                color: black;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5EAF08;
            }
        """)
        
        remove_folder_btn = QPushButton("➖ Remove Folder")
        remove_folder_btn.clicked.connect(self.removeWatchFolder)
        remove_folder_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: black;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        
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
        
        # Queue status
        self.queue_status = QLabel("Queue: 0 files pending")
        self.queue_status.setStyleSheet("padding: 5px; color: #666;")
        watcher_layout.addWidget(self.queue_status)
        
        # Control buttons
        control_btns = QHBoxLayout()
        
        self.start_watch_btn = QPushButton("▶️ Start Watching")
        self.start_watch_btn.setStyleSheet("""
            QPushButton {
                background-color: #5EAF08;
                color: black;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                hover: cursor;
            }
            QPushButton:hover {
                background-color: #5EAF08;
            }
        """)
        self.start_watch_btn.clicked.connect(self.startWatching)
        
        self.stop_watch_btn = QPushButton("⏹️ Stop Watching")
        self.stop_watch_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: black;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #F57C00;
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
        
        # Activity log
        log_group = QGroupBox("Activity Log")
        log_layout = QVBoxLayout()
        
        self.activity_log = QTextEdit()
        self.activity_log.setReadOnly(True)
        self.activity_log.setMaximumHeight(100)
        log_layout.addWidget(self.activity_log)
        
        clear_log_btn = QPushButton("Clear Log")
        clear_log_btn.clicked.connect(lambda: self.activity_log.clear())
        log_layout.addWidget(clear_log_btn)
        
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        # Load saved folders
        self.loadWatchedFolders()
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def loadWatchedFolders(self):
        """Load watched folders from config"""
        watched_folders = self.config.get("documents.watched_folders", [], "client")
        for folder in watched_folders:
            if Path(folder).exists():
                self.watched_folders.append(folder)
                self.folders_list.addItem(folder)
                if self.folder_watcher:
                    self.folder_watcher.add_folder(folder)
    
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
                self.config.set("documents.watched_folders", self.watched_folders, "client")
                self.foldersUpdated.emit(self.watched_folders)
                self.activity_log.append(f"Added folder: {Path(folder).name}")
    
    def removeWatchFolder(self):
        """Remove selected folder from watch list"""
        current = self.folders_list.currentItem()
        if current and self.folder_watcher:
            folder = current.text()
            if self.folder_watcher.remove_folder(folder):
                self.watched_folders.remove(folder)
                self.folders_list.takeItem(self.folders_list.row(current))
                self.config.set("documents.watched_folders", self.watched_folders, "client")
                self.foldersUpdated.emit(self.watched_folders)
                self.activity_log.append(f"Removed folder: {Path(folder).name}")
    
    def startWatching(self):
        """Start the folder watcher"""
        if self.folder_watcher and self.watched_folders:
            self.folder_watcher.start()
            self.watcher_status.setText("Status: Watching...")
            self.start_watch_btn.setEnabled(False)
            self.stop_watch_btn.setEnabled(True)
            self.activity_log.append("▶️ Started folder watching")
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
            self.activity_log.append("⏹️ Stopped folder watching")
            
            # Show results
            if loaded_count > 0 and not failed_files:
                QMessageBox.information(
                    self, "Success", 
                    f"Successfully loaded {loaded_count} file(s)"
                )
            elif loaded_count > 0 and failed_files:
                QMessageBox.warning(
                    self, "Partial Success",
                    f"Loaded {loaded_count} file(s).\n\n"
                    f"Failed to load:\n" + "\n".join(failed_files)
                )
            else:
                QMessageBox.critical(
                    self, "Error",
                    f"Failed to load any files"
                )
    
    def loadDirectory(self):
        """Load all supported files from a directory"""
        directory = QFileDialog.getExistingDirectory(
            self, "Select Directory",
            str(Path.home()),
            QFileDialog.ShowDirsOnly
        )
        
        if directory:
            try:
                batch_loader = BatchLoader()
                loaded_docs = batch_loader.load_directory(directory)
                
                if loaded_docs:
                    self.documents.extend(loaded_docs)
                    self.updateDocumentList()
                    self.updateAdvancedTab()
                    QMessageBox.information(
                        self, "Success",
                        f"Loaded {len(loaded_docs)} documents from {directory}"
                    )
                else:
                    QMessageBox.warning(self, "Warning", "No supported files found in directory")
                    
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error loading directory: {str(e)}")
    
    def loadSampleDocs(self):
        """Load sample documents"""
        samples = [
            {
                "id": "sample-001",
                "title": "RAG System Overview",
                "source": "samples",
                "text": """
                RAG (Retrieval-Augmented Generation) is an AI framework that combines 
                information retrieval with text generation. The system works by:
                1. Chunking documents into smaller pieces
                2. Creating embeddings for each chunk
                3. Storing embeddings in a vector database
                4. Retrieving relevant chunks for queries
                5. Generating answers based on retrieved context
                
                This approach allows for more accurate and contextual responses
                compared to pure generation models.
                """
            },
            {
                "id": "sample-002",
                "title": "Chunking Strategies Guide",
                "source": "samples",
                "text": """
                Different chunking strategies are suitable for different document types:
                
                - Sentence-based: Best for Q&A and conversational content
                - Paragraph-based: Ideal for structured documents and manuals
                - Sliding window: Good for long narratives and novels
                - Adaptive: Automatically selects the best approach
                - Simple overlap: Fast processing with configurable overlap
                
                Choose your strategy based on document structure and use case.
                """
            },
            {
                "id": "sample-003",
                "title": "Embedding Models",
                "source": "samples",
                "text": """
                Embedding models convert text into numerical vectors that capture
                semantic meaning. Popular models include:
                
                - Sentence-BERT: Efficient and accurate for sentence embeddings
                - OpenAI Embeddings: High quality but requires API access
                - Multilingual models: Support for multiple languages
                
                The choice of embedding model affects retrieval quality and speed.
                """
            }
        ]
        
        self.documents.extend(samples)
        self.updateDocumentList()
        self.updateAdvancedTab()
        QMessageBox.information(self, "Success", f"Loaded {len(samples)} sample documents")
    
    def clearDocuments(self):
        """Clear all documents"""
        if self.documents:
            reply = QMessageBox.question(
                self, "Confirm Clear",
                f"Remove all {len(self.documents)} documents?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.documents.clear()
                self.updateDocumentList()
                self.updateAdvancedTab()
    
    def auto_ingest_document(self, file_path):
        """Callback for automatic document ingestion from folder watcher"""
        from pathlib import Path
        import requests
        
        print(f"Auto-ingesting: {Path(file_path).name}")
        
        # Load the document
        loader = FileLoader()
        doc = loader.load_file(file_path)
        
        if doc:
            try:
                # Send to server for ingestion
                response = requests.post(
                    f"{self.config.get_server_url()}/api/ingest",
                    json={"documents": [doc]},
                    headers={"Content-Type": "application/json"},
                    timeout=60
                )
                
                if response.status_code == 200:
                    print(f"Successfully ingested: {Path(file_path).name}")
                    # Add to documents list
                    self.documents.append(doc)
                    self.updateDocumentList()
                    self.documentsChanged.emit(len(self.documents))
                else:
                    print(f"Failed to ingest: {Path(file_path).name}")
                    
            except Exception as e:
                print(f"Error during auto-ingest: {str(e)}")
        else:
            print(f"Could not load file: {Path(file_path).name}")
    
    def createWatchTab(self):
        """Create folder watching tab for auto-ingestion"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Info
        info = QLabel("""
        <div style='background-color: #e8f5e9; padding: 10px; border-radius: 5px;'>
        <b>📂 Automatic Document Ingestion:</b><br>
        Add folders to watch. Any new documents (PDF, MD, TXT) added to these folders
        will be automatically ingested into the RAG system.
        </div>
        """)
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # Watched folders list
        folders_group = QGroupBox("Watched Folders")
        folders_layout = QVBoxLayout()
        
        self.folders_list = QListWidget()
        self.folders_list.setMinimumHeight(100)  # Reduced from 150
        folders_layout.addWidget(self.folders_list)
        
        # Folder controls
        folder_btns = QHBoxLayout()
        
        add_folder_btn = QPushButton("➕ Add Folder")
        add_folder_btn.clicked.connect(self.addWatchFolder)
        add_folder_btn.setStyleSheet("""
            QPushButton {
                background-color: #397B06;
                color: black;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5EAF08;
            }
        """)
        
        remove_folder_btn = QPushButton("➖ Remove Folder")
        remove_folder_btn.clicked.connect(self.removeWatchFolder)
        remove_folder_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: black;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        
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
        
        # Queue status
        self.queue_status = QLabel("Queue: 0 files pending")
        self.queue_status.setStyleSheet("padding: 5px; color: #666;")
        watcher_layout.addWidget(self.queue_status)
        
        # Control buttons
        control_btns = QHBoxLayout()
        
        self.start_watch_btn = QPushButton("▶️ Start Watching")
        self.start_watch_btn.setStyleSheet("""
            QPushButton {
                background-color: #5EAF08;
                color: black;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                hover: cursor;
            }
            QPushButton:hover {
                background-color: #5EAF08;
            }
        """)
        self.start_watch_btn.clicked.connect(self.startWatching)
        
        self.stop_watch_btn = QPushButton("⏹️ Stop Watching")
        self.stop_watch_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: black;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #F57C00;
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
        
        # Activity log
        log_group = QGroupBox("Activity Log")
        log_layout = QVBoxLayout()
        
        self.activity_log = QTextEdit()
        self.activity_log.setReadOnly(True)
        self.activity_log.setMaximumHeight(100)
        log_layout.addWidget(self.activity_log)
        
        clear_log_btn = QPushButton("Clear Log")
        clear_log_btn.clicked.connect(lambda: self.activity_log.clear())
        log_layout.addWidget(clear_log_btn)
        
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        # Load saved folders
        self.loadWatchedFolders()
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def loadWatchedFolders(self):
        """Load watched folders from config"""
        watched_folders = self.config.get("documents.watched_folders", [], "client")
        for folder in watched_folders:
            if Path(folder).exists():
                self.watched_folders.append(folder)
                self.folders_list.addItem(folder)
                if self.folder_watcher:
                    self.folder_watcher.add_folder(folder)
    
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
                self.config.set("documents.watched_folders", self.watched_folders, "client")
                self.foldersUpdated.emit(self.watched_folders)
                self.activity_log.append(f"Added folder: {Path(folder).name}")
    
    def removeWatchFolder(self):
        """Remove selected folder from watch list"""
        current = self.folders_list.currentItem()
        if current and self.folder_watcher:
            folder = current.text()
            if self.folder_watcher.remove_folder(folder):
                self.watched_folders.remove(folder)
                self.folders_list.takeItem(self.folders_list.row(current))
                self.config.set("documents.watched_folders", self.watched_folders, "client")
                self.foldersUpdated.emit(self.watched_folders)
                self.activity_log.append(f"Removed folder: {Path(folder).name}")
    
    def startWatching(self):
        """Start the folder watcher"""
        if self.folder_watcher and self.watched_folders:
            self.folder_watcher.start()
            self.watcher_status.setText("Status: Watching...")
            self.start_watch_btn.setEnabled(False)
            self.stop_watch_btn.setEnabled(True)
            self.activity_log.append("▶️ Started folder watching")
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
            self.activity_log.append("⏹️ Stopped folder watching")
    
    def updateDocumentList(self):
        """Update the document list display"""
        self.docList.clear()
        
        for i, doc in enumerate(self.documents):
            title = doc.get('title', 'Untitled')
            source = doc.get('source', 'Unknown')
            text_len = len(doc.get('text', ''))
            
            item_text = f"[{i+1}] {title}\n    Source: {source} | Size: {text_len} chars"
            self.docList.addItem(item_text)
        
        # Update stats
        total_size = sum(len(doc.get('text', '')) for doc in self.documents)
        self.statsLabel.setText(
            f"Documents: {len(self.documents)} | "
            f"Total Size: {total_size // 1024} KB"
        )
        
        # Emit signal
        self.documentsChanged.emit(len(self.documents))
    
    def updateAdvancedTab(self):
        """Update the advanced tab with current documents"""
        self.advancedTab.updateDocuments(self.documents)
    
    def exportDocuments(self):
        """Export documents to JSON"""
        if not self.documents:
            QMessageBox.warning(self, "No Documents", "No documents to export")
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Documents",
            str(Path.home() / "documents.json"),
            "JSON Files (*.json)"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(self.documents, f, indent=2, ensure_ascii=False)
                QMessageBox.information(self, "Success", f"Exported {len(self.documents)} documents")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Export failed: {str(e)}")
    
    def importDocuments(self):
        """Import documents from JSON"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Import Documents",
            str(Path.home()),
            "JSON Files (*.json)"
        )
        
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    imported_docs = json.load(f)
                
                if isinstance(imported_docs, list):
                    self.documents.extend(imported_docs)
                    self.updateDocumentList()
                    self.updateAdvancedTab()
                    QMessageBox.information(self, "Success", f"Imported {len(imported_docs)} documents")
                else:
                    QMessageBox.warning(self, "Warning", "Invalid document format")
                    
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Import failed: {str(e)}")
    
    def getDocuments(self) -> List[Dict]:
        """Get all documents"""
        return self.documents
    
    def getSelectedDocuments(self) -> List[Dict]:
        """Get selected documents from advanced tab"""
        if hasattr(self.advancedTab, 'selectedIndices'):
            return [self.documents[i] for i in sorted(self.advancedTab.selectedIndices)]
        return []
    
    def showContextMenu(self, position):
        """Show context menu on right-click"""
        item = self.docList.itemAt(position)
        if not item:
            return
        
        # Get the document index from the item
        row = self.docList.row(item)
        if row < 0 or row >= len(self.documents):
            return
        
        doc = self.documents[row]
        source_path = doc.get('source', '')
        
        # Create context menu
        menu = QMenu(self)
        
        # Add "Open in Explorer/Finder" action
        open_folder_action = QAction("Open Folder", self)
        open_folder_action.triggered.connect(lambda: self.openFolder(source_path))
        menu.addAction(open_folder_action)
        
        # Add "Open File" action if it's a file path
        if 'title' in doc:
            # Try to find the actual file
            file_path = None
            if source_path and os.path.isdir(source_path):
                # Look for file with matching title in the source directory
                for ext in ['.txt', '.md', '.pdf', '.json']:
                    potential_path = os.path.join(source_path, doc['title'] + ext)
                    if os.path.exists(potential_path):
                        file_path = potential_path
                        break
            elif source_path and os.path.isfile(source_path):
                file_path = source_path
            
            if file_path and os.path.exists(file_path):
                open_file_action = QAction("Open File", self)
                open_file_action.triggered.connect(lambda: self.openFile(file_path))
                menu.addAction(open_file_action)
        
        menu.addSeparator()
        
        # Add "Copy Path" action
        if source_path:
            copy_path_action = QAction("Copy Path", self)
            copy_path_action.triggered.connect(lambda: self.copyToClipboard(source_path))
            menu.addAction(copy_path_action)
        
        # Add "Remove Document" action
        remove_action = QAction("🗑️ Remove Document", self)
        remove_action.triggered.connect(lambda: self.removeDocument(row))
        menu.addAction(remove_action)
        
        # Show the menu at cursor position
        menu.exec_(self.docList.mapToGlobal(position))
    
    def openFolder(self, path):
        """Open folder in system file explorer"""
        if not path or not os.path.exists(path):
            QMessageBox.warning(self, "Warning", "Path does not exist")
            return
        
        # Get the directory path
        if os.path.isfile(path):
            folder_path = os.path.dirname(path)
        else:
            folder_path = path
        
        try:
            system = platform.system()
            if system == "Windows":
                os.startfile(folder_path)
            elif system == "Darwin":  # macOS
                subprocess.run(["open", folder_path])
            else:  # Linux
                subprocess.run(["xdg-open", folder_path])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not open folder: {e}")
    
    def openFile(self, file_path):
        """Open file with default system application"""
        if not file_path or not os.path.exists(file_path):
            QMessageBox.warning(self, "Warning", "File does not exist")
            return
        
        try:
            system = platform.system()
            if system == "Windows":
                os.startfile(file_path)
            elif system == "Darwin":  # macOS
                subprocess.run(["open", file_path])
            else:  # Linux
                subprocess.run(["xdg-open", file_path])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not open file: {e}")
    
    def copyToClipboard(self, text):
        """Copy text to clipboard"""
        from PySide6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        # Show brief notification
        QMessageBox.information(self, "Copied", "Path copied to clipboard", QMessageBox.Ok)
    
    def removeDocument(self, index):
        """Remove a document from the list"""
        if 0 <= index < len(self.documents):
            doc = self.documents[index]
            reply = QMessageBox.question(
                self, "Confirm Remove",
                f"Remove '{doc.get('title', 'Untitled')}'?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.documents.pop(index)
                self.updateDocumentList()
                self.updateAdvancedTab()
    
    def auto_ingest_document(self, file_path):
        """Callback for automatic document ingestion from folder watcher"""
        from pathlib import Path
        import requests
        
        print(f"Auto-ingesting: {Path(file_path).name}")
        
        # Load the document
        loader = FileLoader()
        doc = loader.load_file(file_path)
        
        if doc:
            try:
                # Send to server for ingestion
                response = requests.post(
                    f"{self.config.get_server_url()}/api/ingest",
                    json={"documents": [doc]},
                    headers={"Content-Type": "application/json"},
                    timeout=60
                )
                
                if response.status_code == 200:
                    print(f"Successfully ingested: {Path(file_path).name}")
                    # Add to documents list
                    self.documents.append(doc)
                    self.updateDocumentList()
                    self.documentsChanged.emit(len(self.documents))
                else:
                    print(f"Failed to ingest: {Path(file_path).name}")
                    
            except Exception as e:
                print(f"Error during auto-ingest: {str(e)}")
        else:
            print(f"Could not load file: {Path(file_path).name}")
    
    def createWatchTab(self):
        """Create folder watching tab for auto-ingestion"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Info
        info = QLabel("""
        <div style='background-color: #e8f5e9; padding: 10px; border-radius: 5px;'>
        <b>📂 Automatic Document Ingestion:</b><br>
        Add folders to watch. Any new documents (PDF, MD, TXT) added to these folders
        will be automatically ingested into the RAG system.
        </div>
        """)
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # Watched folders list
        folders_group = QGroupBox("Watched Folders")
        folders_layout = QVBoxLayout()
        
        self.folders_list = QListWidget()
        self.folders_list.setMinimumHeight(100)  # Reduced from 150
        folders_layout.addWidget(self.folders_list)
        
        # Folder controls
        folder_btns = QHBoxLayout()
        
        add_folder_btn = QPushButton("➕ Add Folder")
        add_folder_btn.clicked.connect(self.addWatchFolder)
        add_folder_btn.setStyleSheet("""
            QPushButton {
                background-color: #397B06;
                color: black;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5EAF08;
            }
        """)
        
        remove_folder_btn = QPushButton("➖ Remove Folder")
        remove_folder_btn.clicked.connect(self.removeWatchFolder)
        remove_folder_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: black;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        
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
        
        # Queue status
        self.queue_status = QLabel("Queue: 0 files pending")
        self.queue_status.setStyleSheet("padding: 5px; color: #666;")
        watcher_layout.addWidget(self.queue_status)
        
        # Control buttons
        control_btns = QHBoxLayout()
        
        self.start_watch_btn = QPushButton("▶️ Start Watching")
        self.start_watch_btn.setStyleSheet("""
            QPushButton {
                background-color: #5EAF08;
                color: black;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                hover: cursor;
            }
            QPushButton:hover {
                background-color: #5EAF08;
            }
        """)
        self.start_watch_btn.clicked.connect(self.startWatching)
        
        self.stop_watch_btn = QPushButton("⏹️ Stop Watching")
        self.stop_watch_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: black;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #F57C00;
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
        
        # Activity log
        log_group = QGroupBox("Activity Log")
        log_layout = QVBoxLayout()
        
        self.activity_log = QTextEdit()
        self.activity_log.setReadOnly(True)
        self.activity_log.setMaximumHeight(100)
        log_layout.addWidget(self.activity_log)
        
        clear_log_btn = QPushButton("Clear Log")
        clear_log_btn.clicked.connect(lambda: self.activity_log.clear())
        log_layout.addWidget(clear_log_btn)
        
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        # Load saved folders
        self.loadWatchedFolders()
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def loadWatchedFolders(self):
        """Load watched folders from config"""
        watched_folders = self.config.get("documents.watched_folders", [], "client")
        for folder in watched_folders:
            if Path(folder).exists():
                self.watched_folders.append(folder)
                self.folders_list.addItem(folder)
                if self.folder_watcher:
                    self.folder_watcher.add_folder(folder)
    
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
                self.config.set("documents.watched_folders", self.watched_folders, "client")
                self.foldersUpdated.emit(self.watched_folders)
                self.activity_log.append(f"Added folder: {Path(folder).name}")
    
    def removeWatchFolder(self):
        """Remove selected folder from watch list"""
        current = self.folders_list.currentItem()
        if current and self.folder_watcher:
            folder = current.text()
            if self.folder_watcher.remove_folder(folder):
                self.watched_folders.remove(folder)
                self.folders_list.takeItem(self.folders_list.row(current))
                self.config.set("documents.watched_folders", self.watched_folders, "client")
                self.foldersUpdated.emit(self.watched_folders)
                self.activity_log.append(f"Removed folder: {Path(folder).name}")
    
    def startWatching(self):
        """Start the folder watcher"""
        if self.folder_watcher and self.watched_folders:
            self.folder_watcher.start()
            self.watcher_status.setText("Status: Watching...")
            self.start_watch_btn.setEnabled(False)
            self.stop_watch_btn.setEnabled(True)
            self.activity_log.append("▶️ Started folder watching")
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
            self.activity_log.append("⏹️ Stopped folder watching")
