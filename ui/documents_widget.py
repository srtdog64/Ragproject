# ui/documents_widget.py
"""
Documents Tab Widget for RAG Qt Application
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


class DocumentsWidget(QWidget):
    """Document management widget with file loading support"""
    
    documentsChanged = Signal(int)  # Emit document count
    
    def __init__(self, config_manager):
        super().__init__()
        self.config = config_manager
        self.documents = []
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout()
        
        # Title
        titleLabel = QLabel("📚 Document Management")
        titleLabel.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px 0;")
        layout.addWidget(titleLabel)
        
        # File operations toolbar
        fileToolbar = QHBoxLayout()
        
        loadFileBtn = QPushButton("📄 Load File")
        loadFileBtn.setToolTip("Load PDF, Markdown, or Text file")
        loadFileBtn.clicked.connect(self.loadFile)
        
        loadDirBtn = QPushButton("📁 Load Directory")
        loadDirBtn.setToolTip("Load all supported files from a directory")
        loadDirBtn.clicked.connect(self.loadDirectory)
        
        loadSampleBtn = QPushButton("📋 Load Samples")
        loadSampleBtn.setToolTip("Load sample documents")
        loadSampleBtn.clicked.connect(self.loadSampleDocs)
        
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
                padding: 5px 10px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        clearBtn.clicked.connect(self.clearDocuments)
        fileToolbar.addWidget(clearBtn)
        
        layout.addLayout(fileToolbar)
        
        # Manual document entry
        manualGroup = QGroupBox("Add Document Manually")
        manualLayout = QFormLayout()
        
        self.idEdit = QLineEdit()
        self.idEdit.setPlaceholderText("Auto-generated if empty")
        
        self.titleEdit = QLineEdit()
        self.titleEdit.setPlaceholderText("Document title")
        
        self.sourceEdit = QLineEdit()
        self.sourceEdit.setPlaceholderText("Source URL or reference")
        
        self.textEdit = QPlainTextEdit()
        self.textEdit.setMaximumHeight(100)
        self.textEdit.setPlaceholderText("Document content...")
        
        manualLayout.addRow("ID:", self.idEdit)
        manualLayout.addRow("Title:", self.titleEdit)
        manualLayout.addRow("Source:", self.sourceEdit)
        manualLayout.addRow("Content:", self.textEdit)
        
        addBtn = QPushButton("➕ Add Document")
        addBtn.clicked.connect(self.addDocument)
        manualLayout.addRow("", addBtn)
        
        manualGroup.setLayout(manualLayout)
        layout.addWidget(manualGroup)
        
        # Document list
        listGroup = QGroupBox("Loaded Documents")
        listLayout = QVBoxLayout()
        
        # Search bar
        searchLayout = QHBoxLayout()
        self.searchEdit = QLineEdit()
        self.searchEdit.setPlaceholderText("🔍 Search documents...")
        self.searchEdit.textChanged.connect(self.filterDocuments)
        searchLayout.addWidget(self.searchEdit)
        
        listLayout.addLayout(searchLayout)
        
        # Document list widget
        self.docList = QListWidget()
        self.docList.setSelectionMode(QListWidget.ExtendedSelection)
        self.docList.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.docList.customContextMenuRequested.connect(self.showContextMenu)
        listLayout.addWidget(self.docList)
        
        # Statistics
        self.statsLabel = QLabel("No documents loaded")
        self.statsLabel.setStyleSheet("font-weight: bold; color: #666; padding: 10px;")
        listLayout.addWidget(self.statsLabel)
        
        listGroup.setLayout(listLayout)
        layout.addWidget(listGroup)
        
        self.setLayout(layout)
    
    def loadFile(self):
        """Load a single file"""
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
                self, "Recursive Search?",
                "Include subdirectories?",
                QMessageBox.Yes | QMessageBox.No
            )
            recursive = reply == QMessageBox.Yes
            
            try:
                # Create progress dialog
                progress = QProgressDialog("Scanning directory...", "Cancel", 0, 100, self)
                progress.setWindowModality(Qt.WindowModality.WindowModal)
                progress.show()
                
                files = FileLoader.scan_directory(directory, recursive)
                
                if not files:
                    progress.close()
                    QMessageBox.information(self, "No Files", "No supported files found.")
                    return
                
                progress.setLabelText(f"Found {len(files)} files. Loading...")
                progress.setMaximum(len(files))
                
                docs = []
                for i, file in enumerate(files):
                    if progress.wasCanceled():
                        break
                    
                    progress.setValue(i)
                    try:
                        doc = FileLoader.load_file(file)
                        docs.append(doc)
                    except Exception as e:
                        print(f"Failed to load {file}: {e}")
                
                progress.close()
                
                if docs:
                    self.documents.extend(docs)
                    self.updateList()
                    QMessageBox.information(self, "Success", f"Loaded {len(docs)} documents")
                    
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load directory: {str(e)}")
    
    def loadSampleDocs(self):
        """Load sample documents"""
        try:
            sample_path = Path("sample_docs.json")
            if not sample_path.exists():
                # Create sample docs if not exists
                sample_data = {
                    "documents": [
                        {
                            "id": "sample_1",
                            "title": "Introduction to RAG",
                            "source": "sample",
                            "text": "Retrieval-Augmented Generation (RAG) is a technique that enhances LLM responses by retrieving relevant information from a knowledge base.",
                            "type": "sample"
                        },
                        {
                            "id": "sample_2",
                            "title": "Chunking Strategies",
                            "source": "sample",
                            "text": "Different chunking strategies include sentence-based, paragraph-based, sliding window, and semantic chunking. Each has its own advantages.",
                            "type": "sample"
                        }
                    ]
                }
                with open(sample_path, 'w', encoding='utf-8') as f:
                    json.dump(sample_data, f, indent=2, ensure_ascii=False)
            
            with open(sample_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.documents.extend(data.get("documents", []))
                self.updateList()
                QMessageBox.information(self, "Success", f"Loaded {len(data.get('documents', []))} sample documents")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load sample docs: {str(e)}")
    
    def addDocument(self):
        """Add document manually"""
        doc_id = self.idEdit.text() or f"doc_{len(self.documents) + 1}"
        title = self.titleEdit.text()
        source = self.sourceEdit.text() or "manual"
        text = self.textEdit.toPlainText()
        
        if not title or not text:
            QMessageBox.warning(self, "Warning", "Title and Content are required")
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
        
        QMessageBox.information(self, "Success", f"Added document: {title}")
    
    def clearDocuments(self):
        """Clear all documents"""
        if self.documents:
            reply = QMessageBox.question(
                self, "Confirm Clear",
                f"Remove all {len(self.documents)} documents?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.documents = []
                self.updateList()
    
    def filterDocuments(self):
        """Filter documents based on search text"""
        search_text = self.searchEdit.text().lower()
        
        for i in range(self.docList.count()):
            item = self.docList.item(i)
            text = item.text().lower()
            item.setHidden(search_text not in text)
    
    def showContextMenu(self, position):
        """Show context menu for document list"""
        menu = QMenu(self)
        
        # Get selected items
        selected = self.docList.selectedItems()
        
        if selected:
            viewAction = menu.addAction("👁️ View Details")
            viewAction.triggered.connect(self.viewSelectedDocuments)
            
            deleteAction = menu.addAction("🗑️ Delete Selected")
            deleteAction.triggered.connect(self.deleteSelectedDocuments)
            
            menu.addSeparator()
        
        exportAction = menu.addAction("💾 Export All to JSON")
        exportAction.triggered.connect(self.exportDocuments)
        
        menu.exec(self.docList.mapToGlobal(position))
    
    def viewSelectedDocuments(self):
        """View details of selected documents"""
        selected = self.docList.selectedItems()
        if not selected:
            return
        
        # Get indices of selected items
        indices = [self.docList.row(item) for item in selected]
        
        for idx in indices[:5]:  # Show max 5 at once
            if idx < len(self.documents):
                doc = self.documents[idx]
                
                dialog = QDialog(self)
                dialog.setWindowTitle(f"Document: {doc['title']}")
                dialog.setModal(True)
                dialog.resize(600, 400)
                
                layout = QVBoxLayout()
                
                # Document info
                infoText = f"""
                <b>ID:</b> {doc['id']}<br>
                <b>Title:</b> {doc['title']}<br>
                <b>Source:</b> {doc.get('source', 'N/A')}<br>
                <b>Type:</b> {doc.get('type', 'N/A')}<br>
                <b>Length:</b> {len(doc.get('text', ''))} characters
                """
                
                infoLabel = QLabel(infoText)
                layout.addWidget(infoLabel)
                
                # Document content
                contentEdit = QTextEdit()
                contentEdit.setReadOnly(True)
                contentEdit.setPlainText(doc.get('text', ''))
                layout.addWidget(contentEdit)
                
                # Close button
                closeBtn = QPushButton("Close")
                closeBtn.clicked.connect(dialog.close)
                layout.addWidget(closeBtn)
                
                dialog.setLayout(layout)
                dialog.show()
    
    def deleteSelectedDocuments(self):
        """Delete selected documents"""
        selected = self.docList.selectedItems()
        if not selected:
            return
        
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Delete {len(selected)} selected documents?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Get indices and remove in reverse order
            indices = sorted([self.docList.row(item) for item in selected], reverse=True)
            for idx in indices:
                if idx < len(self.documents):
                    del self.documents[idx]
            
            self.updateList()
    
    def exportDocuments(self):
        """Export documents to JSON"""
        if not self.documents:
            QMessageBox.warning(self, "Warning", "No documents to export")
            return
        
        fileName, _ = QFileDialog.getSaveFileName(
            self, "Export Documents", 
            "documents.json",
            "JSON Files (*.json)"
        )
        
        if fileName:
            try:
                with open(fileName, 'w', encoding='utf-8') as f:
                    json.dump({"documents": self.documents}, f, indent=2, ensure_ascii=False)
                QMessageBox.information(self, "Success", f"Exported {len(self.documents)} documents")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export: {str(e)}")
    
    def updateList(self):
        """Update the document list display"""
        self.docList.clear()
        
        # Group by type
        type_counts = {}
        type_icons = {
            "pdf": "📄",
            "md": "📝",
            "txt": "📃",
            "manual": "✏️",
            "sample": "📋",
            "unknown": "📎"
        }
        
        for doc in self.documents:
            doc_type = doc.get("type", "unknown")
            type_counts[doc_type] = type_counts.get(doc_type, 0) + 1
            
            # Create list item with rich formatting
            icon = type_icons.get(doc_type, "📎")
            title = doc['title'][:50] + "..." if len(doc['title']) > 50 else doc['title']
            text_preview = doc.get('text', '')[:100] + "..." if len(doc.get('text', '')) > 100 else doc.get('text', '')
            
            display_text = f"{icon} [{doc['id']}] {title}"
            item = QListWidgetItem(display_text)
            item.setToolTip(f"Source: {doc.get('source', 'N/A')}\n\nPreview:\n{text_preview}")
            
            self.docList.addItem(item)
        
        # Update statistics
        total = len(self.documents)
        if total == 0:
            self.statsLabel.setText("No documents loaded")
        else:
            stats_text = f"📊 Total: {total} documents"
            if type_counts:
                details = ", ".join([f"{count} {dtype}" for dtype, count in type_counts.items()])
                stats_text += f" ({details})"
            
            # Calculate total text size
            total_chars = sum(len(doc.get('text', '')) for doc in self.documents)
            if total_chars > 1000000:
                size_text = f"{total_chars / 1000000:.1f}M"
            elif total_chars > 1000:
                size_text = f"{total_chars / 1000:.1f}K"
            else:
                size_text = str(total_chars)
            
            stats_text += f" | {size_text} characters total"
            self.statsLabel.setText(stats_text)
        
        # Emit signal
        self.documentsChanged.emit(total)
    
    def getDocuments(self) -> List[Dict]:
        """Get all loaded documents"""
        return self.documents
