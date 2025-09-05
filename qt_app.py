# qt_app.py
"""
Qt6 RAG Interface with File Loading Support
"""
import sys
import json
import os
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


class RagWorkerThread(QThread):
    """Background worker for API calls"""
    finished = Signal(dict)
    error = Signal(str)
    progress = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.baseUrl = "http://localhost:7001"
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
                    timeout=30
                )
                self.finished.emit({"task": "ingest", "result": response.json()})
                
            elif self.task == "ask":
                self.progress.emit("Getting answer...")
                response = requests.post(
                    f"{self.baseUrl}/ask",
                    json=self.payload,
                    timeout=30
                )
                self.finished.emit({"task": "ask", "result": response.json()})
                
        except requests.ConnectionError:
            self.error.emit("Cannot connect to server. Please run: python run_server.py")
        except Exception as e:
            self.error.emit(f"Error: {str(e)}")


class ChatWidget(QWidget):
    """Chat interface widget"""
    def __init__(self):
        super().__init__()
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout()
        
        # Settings bar
        settingsLayout = QHBoxLayout()
        settingsLayout.addWidget(QLabel("Top K:"))
        
        self.topKSpin = QSpinBox()
        self.topKSpin.setRange(1, 20)
        self.topKSpin.setValue(5)
        settingsLayout.addWidget(self.topKSpin)
        
        settingsLayout.addStretch()
        
        clearBtn = QPushButton("Clear Chat")
        clearBtn.clicked.connect(self.clearChat)
        settingsLayout.addWidget(clearBtn)
        
        # Chat display
        self.chatDisplay = QTextBrowser()
        
        # Input area
        inputLayout = QHBoxLayout()
        self.inputField = QLineEdit()
        self.inputField.setPlaceholderText("Ask a question...")
        
        self.sendBtn = QPushButton("Send")
        
        inputLayout.addWidget(self.inputField)
        inputLayout.addWidget(self.sendBtn)
        
        # Add to main layout
        layout.addLayout(settingsLayout)
        layout.addWidget(self.chatDisplay)
        layout.addLayout(inputLayout)
        
        self.setLayout(layout)
    
    def addMessage(self, sender: str, message: str, metadata: Dict = None):
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        html = f"""
        <div style="margin: 10px 0;">
            <b>{sender}</b> <span style="color: #888;">[{timestamp}]</span>
            <div style="margin-top: 5px;">{message}</div>
        """
        
        if metadata:
            html += '<div style="color: #666; font-size: 0.9em; margin-top: 5px;">'
            if metadata.get("ctxIds"):
                html += f'Contexts: {len(metadata["ctxIds"])} | '
            if metadata.get("latencyMs"):
                html += f'Time: {metadata["latencyMs"]}ms'
            html += '</div>'
        
        html += "</div><hr>"
        
        self.chatDisplay.append(html)
    
    def clearChat(self):
        self.chatDisplay.clear()
    
    def getQuestion(self) -> str:
        return self.inputField.text().strip()
    
    def clearInput(self):
        self.inputField.clear()
    
    def getTopK(self) -> int:
        return self.topKSpin.value()


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
        
        loadFileBtn = QPushButton("Load File (PDF/MD/TXT)")
        loadFileBtn.clicked.connect(self.loadFile)
        
        loadDirBtn = QPushButton("Load Directory")
        loadDirBtn.clicked.connect(self.loadDirectory)
        
        fileToolbar.addWidget(loadFileBtn)
        fileToolbar.addWidget(loadDirBtn)
        fileToolbar.addStretch()
        
        # Document toolbar
        toolbar = QHBoxLayout()
        
        addBtn = QPushButton("Add Manual")
        addBtn.clicked.connect(self.addDocument)
        
        loadJsonBtn = QPushButton("Load Sample Docs")
        loadJsonBtn.clicked.connect(self.loadSampleDocs)
        
        clearBtn = QPushButton("Clear All")
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
        
        # Add to layout
        layout.addLayout(fileToolbar)
        layout.addLayout(toolbar)
        layout.addLayout(formLayout)
        layout.addWidget(QLabel("Documents:"))
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
                # If PDF loading fails due to missing library, inform user
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
                
                # Show preview
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
            
            # Add to list
            display_text = f"{doc['id']}: {doc['title']}"
            if doc_type != "unknown":
                display_text += f" [{doc_type.upper()}]"
            self.docList.addItem(display_text)
        
        # Update stats
        stats = f"{len(self.documents)} documents"
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
        
        self.initUI()
        self.checkServer()
    
    def initUI(self):
        self.setWindowTitle("RAG System - Qt6 Interface")
        self.setGeometry(100, 100, 1200, 800)
        
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
        self.tabs.addTab(self.chatWidget, "Chat")
        
        # Documents tab
        self.docWidget = DocumentWidget()
        self.tabs.addTab(self.docWidget, "Documents")
        
        # Logs tab
        self.logWidget = QPlainTextEdit()
        self.logWidget.setReadOnly(True)
        self.tabs.addTab(self.logWidget, "Logs")
        
        layout.addWidget(self.tabs)
        central.setLayout(layout)
        
        # Create menu
        self.createMenu()
        
        # Status bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        
        self.serverStatus = QLabel("Server: Unknown")
        self.statusBar.addPermanentWidget(self.serverStatus)
    
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
        ingestAction.triggered.connect(self.ingestDocuments)
        serverMenu.addAction(ingestAction)
        
        # Help menu
        helpMenu = menubar.addMenu("Help")
        
        aboutAction = QAction("About", self)
        aboutAction.triggered.connect(self.showAbout)
        helpMenu.addAction(aboutAction)
    
    def checkServer(self):
        self.worker.setTask("health")
        self.worker.start()
    
    def ingestDocuments(self):
        docs = self.docWidget.getDocuments()
        if not docs:
            QMessageBox.warning(self, "Warning", "No documents to ingest")
            return
        
        reply = QMessageBox.question(
            self, "Confirm",
            f"Ingest {len(docs)} documents?",
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
                self.serverStatus.setText("Server: Online")
                self.serverStatus.setStyleSheet("color: green;")
            else:
                self.serverStatus.setText("Server: Offline")
                self.serverStatus.setStyleSheet("color: red;")
            self.log(f"Server status: {status}")
            
        elif task == "ingest":
            chunks = result.get("ingestedChunks", 0)
            docs = result.get("documentCount", 0)
            QMessageBox.information(
                self, "Success",
                f"Ingested {docs} documents into {chunks} chunks"
            )
            self.log(f"Ingested {docs} documents")
            
        elif task == "ask":
            answer = result.get("answer", "No answer")
            metadata = {
                "ctxIds": result.get("ctxIds", []),
                "latencyMs": result.get("latencyMs", 0)
            }
            self.chatWidget.addMessage("Assistant", answer, metadata)
            self.log(f"Answered in {metadata['latencyMs']}ms")
    
    def handleError(self, error: str):
        QMessageBox.critical(self, "Error", error)
        self.log(f"ERROR: {error}")
    
    def updateStatus(self, message: str):
        self.statusBar.showMessage(message, 3000)
    
    def log(self, message: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.logWidget.appendPlainText(f"[{timestamp}] {message}")
    
    def showAbout(self):
        QMessageBox.about(
            self, "About",
            """<h2>RAG System Qt6 Interface</h2>
            <p>Retrieval-Augmented Generation System</p>
            <p><b>Supported Files:</b></p>
            <ul>
                <li>PDF Files (.pdf)</li>
                <li>Markdown Files (.md)</li>
                <li>Text Files (.txt)</li>
                <li>JSON Documents</li>
            </ul>
            <p>Version 1.0</p>"""
        )


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
