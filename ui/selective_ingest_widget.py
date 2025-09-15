"""
Advanced Document Ingestion Widget
Provides selective document ingestion with batch control
"""
from typing import List, Dict, Set
from PySide6.QtWidgets import *
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont, QColor
from .icon_manager import get_icon, Icons


class SelectiveIngestWidget(QWidget):
    """Widget for selective document ingestion"""
    
    ingestRequested = Signal(list)  # Emit selected documents
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.documents = []
        self.selectedIndices = set()
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout()
        
        # Title
        titleLabel = QLabel("Selective Document Ingestion")
        titleLabel.setStyleSheet("font-size: 14px; font-weight: bold; margin: 10px 0;")
        layout.addWidget(titleLabel)
        
        # Control buttons
        controlLayout = QHBoxLayout()
        
        selectAllBtn = QPushButton("Select All")
        selectAllBtn.clicked.connect(self.selectAll)
        controlLayout.addWidget(selectAllBtn)
        
        selectNoneBtn = QPushButton("Select None")
        selectNoneBtn.clicked.connect(self.selectNone)
        controlLayout.addWidget(selectNoneBtn)
        
        invertBtn = QPushButton("Invert Selection")
        invertBtn.clicked.connect(self.invertSelection)
        controlLayout.addWidget(invertBtn)
        
        controlLayout.addStretch()
        
        # Document count label
        self.countLabel = QLabel("0 documents selected")
        controlLayout.addWidget(self.countLabel)
        
        layout.addLayout(controlLayout)
        
        # Document list with checkboxes
        self.docList = QListWidget()
        self.docList.setSelectionMode(QListWidget.MultiSelection)
        self.docList.itemChanged.connect(self.onItemChanged)
        layout.addWidget(self.docList)
        
        # Batch control
        batchLayout = QHBoxLayout()
        
        batchLayout.addWidget(QLabel("Batch Size:"))
        
        self.batchSizeSpinner = QSpinBox()
        self.batchSizeSpinner.setRange(1, 100)
        self.batchSizeSpinner.setValue(10)
        self.batchSizeSpinner.setToolTip("Number of documents to process in each batch")
        batchLayout.addWidget(self.batchSizeSpinner)
        
        batchLayout.addWidget(QLabel("Delay (sec):"))
        
        self.delaySpinner = QDoubleSpinBox()
        self.delaySpinner.setRange(0.0, 10.0)
        self.delaySpinner.setSingleStep(0.5)
        self.delaySpinner.setValue(0.5)
        self.delaySpinner.setToolTip("Delay between batches to avoid overloading")
        batchLayout.addWidget(self.delaySpinner)
        
        batchLayout.addStretch()
        
        layout.addLayout(batchLayout)
        
        # Ingest button
        self.ingestBtn = QPushButton("Ingest Selected Documents")
        self.ingestBtn.setIcon(get_icon(Icons.SAVE))
        self.ingestBtn.setStyleSheet("""
            QPushButton {
                background-color: #397B06;
                color: black;
                font-weight: bold;
                padding: 10px;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.ingestBtn.clicked.connect(self.onIngestClicked)
        layout.addWidget(self.ingestBtn)
        
        # Progress bar
        self.progressBar = QProgressBar()
        self.progressBar.setTextVisible(True)
        self.progressBar.hide()
        layout.addWidget(self.progressBar)
        
        # Status label
        self.statusLabel = QLabel("")
        self.statusLabel.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(self.statusLabel)
        
        self.setLayout(layout)
    
    def updateDocuments(self, documents: List[Dict]):
        """Update the document list"""
        self.documents = documents
        self.docList.clear()
        self.selectedIndices.clear()
        
        for i, doc in enumerate(documents):
            # Create item with checkbox
            item = QListWidgetItem()
            
            # Format display text
            title = doc.get('title', 'Untitled')
            source = doc.get('source', 'Unknown')
            text_preview = doc.get('text', '')[:100]
            if len(doc.get('text', '')) > 100:
                text_preview += "..."
            
            display_text = f"[{i+1}] {title}\n    Source: {source}\n    Preview: {text_preview}"
            item.setText(display_text)
            
            # Enable checkbox
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            
            self.docList.addItem(item)
        
        self.updateCountLabel()
    
    def onItemChanged(self, item):
        """Handle item check state change"""
        index = self.docList.row(item)
        if item.checkState() == Qt.Checked:
            self.selectedIndices.add(index)
        else:
            self.selectedIndices.discard(index)
        self.updateCountLabel()
    
    def selectAll(self):
        """Select all documents"""
        for i in range(self.docList.count()):
            item = self.docList.item(i)
            item.setCheckState(Qt.Checked)
    
    def selectNone(self):
        """Deselect all documents"""
        for i in range(self.docList.count()):
            item = self.docList.item(i)
            item.setCheckState(Qt.Unchecked)
    
    def invertSelection(self):
        """Invert current selection"""
        for i in range(self.docList.count()):
            item = self.docList.item(i)
            if item.checkState() == Qt.Checked:
                item.setCheckState(Qt.Unchecked)
            else:
                item.setCheckState(Qt.Checked)
    
    def updateCountLabel(self):
        """Update the selection count label"""
        count = len(self.selectedIndices)
        total = len(self.documents)
        self.countLabel.setText(f"{count}/{total} documents selected")
        self.ingestBtn.setEnabled(count > 0)
    
    def onIngestClicked(self):
        """Handle ingest button click"""
        if not self.selectedIndices:
            QMessageBox.warning(self, "No Selection", "Please select documents to ingest.")
            return
        
        # Get selected documents
        selected_docs = [self.documents[i] for i in sorted(self.selectedIndices)]
        
        # Show confirmation
        reply = QMessageBox.question(
            self, "Confirm Ingestion",
            f"Ingest {len(selected_docs)} selected documents?\n"
            f"Batch size: {self.batchSizeSpinner.value()}\n"
            f"Delay between batches: {self.delaySpinner.value()}s",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Emit signal with selected documents and settings
            self.ingestRequested.emit(selected_docs)
            self.statusLabel.setText(f"Ingesting {len(selected_docs)} documents...")
    
    def setProgress(self, current: int, total: int, message: str = ""):
        """Update progress bar"""
        if current == 0:
            self.progressBar.show()
            self.progressBar.setMaximum(total)
            self.progressBar.setValue(0)
            self.ingestBtn.setEnabled(False)
        elif current >= total:
            self.progressBar.hide()
            self.progressBar.setValue(0)
            self.ingestBtn.setEnabled(True)
            self.statusLabel.setText("Ingestion complete!")
        else:
            self.progressBar.setValue(current)
            if message:
                self.progressBar.setFormat(message)
    
    def getBatchSettings(self):
        """Get batch processing settings"""
        return {
            'batch_size': self.batchSizeSpinner.value(),
            'delay': self.delaySpinner.value()
        }
