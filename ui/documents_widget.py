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

# Import file loader
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'rag'))
from file_loader import FileLoader, BatchLoader
from .selective_ingest_widget import SelectiveIngestWidget


class DocumentsWidget(QWidget):
    """Document management widget with basic and advanced features"""
    
    documentsChanged = Signal(int)  # Emit document count
    selectiveIngestRequested = Signal(list)  # Emit selected documents for ingestion
    
    def __init__(self, config_manager):
        super().__init__()
        self.config = config_manager
        self.documents = []
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout()
        
        # Title
        titleLabel = QLabel("📚 Document Management Center")
        titleLabel.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px 0;")
        layout.addWidget(titleLabel)
        
        # Create tab widget for document management
        self.tabWidget = QTabWidget()
        
        # Tab 1: Basic document management
        self.basicTab = self.createBasicTab()
        self.tabWidget.addTab(self.basicTab, "📋 Document List")
        
        # Tab 2: Advanced selective ingestion
        self.advancedTab = SelectiveIngestWidget()
        self.advancedTab.ingestRequested.connect(self.selectiveIngestRequested.emit)
        self.tabWidget.addTab(self.advancedTab, "🎯 Selective Ingest")
        
        layout.addWidget(self.tabWidget)
        self.setLayout(layout)
    
    def createBasicTab(self):
        """Create the basic document management tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # File operations toolbar
        fileToolbar = QHBoxLayout()
        
        loadFileBtn = QPushButton("📄 Load File")
        loadFileBtn.setToolTip("Load PDF, Markdown, or Text file")
        loadFileBtn.clicked.connect(self.loadFile)
        loadFileBtn.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                background-color: #2196F3;
                color: white;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        
        loadDirBtn = QPushButton("📁 Load Directory")
        loadDirBtn.setToolTip("Load all supported files from a directory")
        loadDirBtn.clicked.connect(self.loadDirectory)
        loadDirBtn.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                background-color: #2196F3;
                color: white;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        
        loadSampleBtn = QPushButton("📋 Load Samples")
        loadSampleBtn.setToolTip("Load sample documents")
        loadSampleBtn.clicked.connect(self.loadSampleDocs)
        loadSampleBtn.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                background-color: #FF9800;
                color: white;
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
        
        clearBtn = QPushButton("🗑️ Clear All")
        clearBtn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
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
        
        # Document list
        self.docList = QListWidget()
        self.docList.setAlternatingRowColors(True)
        layout.addWidget(self.docList)
        
        # Export/Import buttons
        exportLayout = QHBoxLayout()
        
        exportBtn = QPushButton("💾 Export Documents")
        exportBtn.clicked.connect(self.exportDocuments)
        exportLayout.addWidget(exportBtn)
        
        importBtn = QPushButton("📂 Import Documents")
        importBtn.clicked.connect(self.importDocuments)
        exportLayout.addWidget(importBtn)
        
        exportLayout.addStretch()
        layout.addLayout(exportLayout)
        
        widget.setLayout(layout)
        return widget
    
    def loadFile(self):
        """Load a single file"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Select File",
            str(Path.home()),
            "Supported Files (*.pdf *.md *.txt);;PDF Files (*.pdf);;Markdown Files (*.md);;Text Files (*.txt);;All Files (*.*)"
        )
        
        if filename:
            try:
                loader = FileLoader()
                doc = loader.load(filename)
                
                if doc:
                    self.documents.append(doc)
                    self.updateDocumentList()
                    self.updateAdvancedTab()
                    QMessageBox.information(self, "Success", f"Loaded: {doc['title']}")
                else:
                    QMessageBox.warning(self, "Warning", f"Could not load file: {filename}")
                    
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error loading file: {str(e)}")
    
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
