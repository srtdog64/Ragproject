# ui/options/database_tab.py
"""
Database configuration tab for the options widget
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QFileDialog,
    QFormLayout, QComboBox, QSpinBox, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from pathlib import Path
import yaml
import os


class DatabaseTab(QWidget):
    """Tab for database configuration"""
    
    # Signal emitted when database path changes
    database_changed = Signal(str)
    
    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        self.init_ui()
        self.load_config()
    
    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        # Database Settings Group
        db_group = QGroupBox("Database Settings")
        db_layout = QFormLayout()
        
        # Store Type
        self.store_type_combo = QComboBox()
        self.store_type_combo.addItems(["chroma", "faiss", "memory"])
        self.store_type_combo.currentTextChanged.connect(self.on_store_type_changed)
        db_layout.addRow("Store Type:", self.store_type_combo)
        
        # Database Path
        path_layout = QHBoxLayout()
        self.db_path_edit = QLineEdit()
        self.db_path_edit.setPlaceholderText("E:\\Ragproject\\chroma_db")
        
        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self.browse_folder)
        
        path_layout.addWidget(self.db_path_edit)
        path_layout.addWidget(self.browse_btn)
        db_layout.addRow("Database Path:", path_layout)
        
        # Collection Name
        self.collection_edit = QLineEdit()
        self.collection_edit.setPlaceholderText("rag_documents")
        db_layout.addRow("Collection Name:", self.collection_edit)
        
        # Info label
        self.info_label = QLabel()
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet("color: #666; font-size: 10pt;")
        db_layout.addRow("", self.info_label)
        
        db_group.setLayout(db_layout)
        layout.addWidget(db_group)
        
        # Statistics Group
        stats_group = QGroupBox("Database Statistics")
        stats_layout = QFormLayout()
        
        # Vector Count
        self.vector_count_label = QLabel("0")
        self.vector_count_label.setStyleSheet("font-weight: bold;")
        stats_layout.addRow("Total Vectors:", self.vector_count_label)
        
        # Database Size
        self.db_size_label = QLabel("0 MB")
        self.db_size_label.setStyleSheet("font-weight: bold;")
        stats_layout.addRow("Database Size:", self.db_size_label)
        
        # Collections
        self.collections_label = QLabel("0")
        self.collections_label.setStyleSheet("font-weight: bold;")
        stats_layout.addRow("Collections:", self.collections_label)
        
        # Refresh button
        self.refresh_btn = QPushButton("Refresh Statistics")
        self.refresh_btn.clicked.connect(self.refresh_statistics)
        stats_layout.addRow("", self.refresh_btn)
        
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)
        
        # Actions
        actions_layout = QHBoxLayout()
        
        self.apply_btn = QPushButton("Apply Changes")
        self.apply_btn.clicked.connect(self.apply_changes)
        
        self.reset_btn = QPushButton("Reset to Default")
        self.reset_btn.clicked.connect(self.reset_to_default)
        
        self.clear_db_btn = QPushButton("Clear Database")
        self.clear_db_btn.clicked.connect(self.clear_database)
        self.clear_db_btn.setStyleSheet("QPushButton { color: red; }")
        
        actions_layout.addWidget(self.apply_btn)
        actions_layout.addWidget(self.reset_btn)
        actions_layout.addWidget(self.clear_db_btn)
        actions_layout.addStretch()
        
        layout.addLayout(actions_layout)
        layout.addStretch()
        
        self.setLayout(layout)
    
    def load_config(self):
        """Load current configuration"""
        try:
            config_path = Path("config/config.yaml")
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    
                store_config = config.get('store', {})
                self.store_type_combo.setCurrentText(store_config.get('type', 'chroma'))
                self.db_path_edit.setText(store_config.get('persist_directory', 'E:\\Ragproject\\chroma_db'))
                self.collection_edit.setText(store_config.get('collection_name', 'rag_documents'))
                
                self.on_store_type_changed(self.store_type_combo.currentText())
                self.refresh_statistics()
        except Exception as e:
            print(f"Error loading database config: {e}")
    
    def on_store_type_changed(self, store_type):
        """Handle store type change"""
        if store_type == "memory":
            self.db_path_edit.setEnabled(False)
            self.browse_btn.setEnabled(False)
            self.info_label.setText("Memory store: Data will be lost when server restarts!")
            self.info_label.setStyleSheet("color: orange; font-size: 10pt;")
        elif store_type == "chroma":
            self.db_path_edit.setEnabled(True)
            self.browse_btn.setEnabled(True)
            self.info_label.setText("ChromaDB: Persistent vector storage with full-text search")
            self.info_label.setStyleSheet("color: green; font-size: 10pt;")
        elif store_type == "faiss":
            self.db_path_edit.setEnabled(True)
            self.browse_btn.setEnabled(True)
            self.info_label.setText("FAISS: High-performance similarity search (not yet implemented)")
            self.info_label.setStyleSheet("color: blue; font-size: 10pt;")
    
    def browse_folder(self):
        """Browse for database folder"""
        current_path = self.db_path_edit.text() or "E:\\Ragproject"
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Database Directory",
            current_path,
            QFileDialog.ShowDirsOnly
        )
        
        if folder:
            self.db_path_edit.setText(folder)
    
    def refresh_statistics(self):
        """Refresh database statistics"""
        try:
            db_path = self.db_path_edit.text()
            if not db_path or not os.path.exists(db_path):
                self.vector_count_label.setText("N/A")
                self.db_size_label.setText("N/A")
                self.collections_label.setText("N/A")
                return
            
            # Calculate database size
            total_size = 0
            collection_count = 0
            
            for root, dirs, files in os.walk(db_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    total_size += os.path.getsize(file_path)
                # Count directories as collections (for ChromaDB)
                if root != db_path:
                    collection_count += len(dirs)
                    dirs.clear()  # Don't recurse into subdirectories
            
            # Format size
            size_mb = total_size / (1024 * 1024)
            self.db_size_label.setText(f"{size_mb:.2f} MB")
            
            # Try to get vector count from server
            import requests
            try:
                response = requests.get("http://localhost:7001/api/rag/stats", timeout=2)
                if response.status_code == 200:
                    data = response.json()
                    self.vector_count_label.setText(str(data.get('total_vectors', 0)))
                else:
                    self.vector_count_label.setText("Server offline")
            except:
                self.vector_count_label.setText("Server offline")
            
            # Set collection count
            self.collections_label.setText(str(max(1, collection_count)))
            
        except Exception as e:
            print(f"Error refreshing statistics: {e}")
            self.vector_count_label.setText("Error")
            self.db_size_label.setText("Error")
            self.collections_label.setText("Error")
    
    def apply_changes(self):
        """Apply database configuration changes"""
        try:
            config_path = Path("config/config.yaml")
            
            # Load current config
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # Update store section
            if 'store' not in config:
                config['store'] = {}
            
            config['store']['type'] = self.store_type_combo.currentText()
            config['store']['persist_directory'] = self.db_path_edit.text()
            config['store']['collection_name'] = self.collection_edit.text()
            
            # Save config
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, allow_unicode=True, sort_keys=False)
            
            # Emit signal
            self.database_changed.emit(self.db_path_edit.text())
            
            QMessageBox.information(self, "Success", 
                                  "Database configuration saved.\nRestart the server for changes to take effect.")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save configuration: {e}")
    
    def reset_to_default(self):
        """Reset to default database configuration"""
        self.store_type_combo.setCurrentText("chroma")
        self.db_path_edit.setText("E:\\Ragproject\\chroma_db")
        self.collection_edit.setText("rag_documents")
        self.on_store_type_changed("chroma")
    
    def clear_database(self):
        """Clear the database (with confirmation)"""
        reply = QMessageBox.warning(
            self,
            "Clear Database",
            "Are you sure you want to clear the entire database?\n"
            "This will delete all vectors and cannot be undone!",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                import requests
                # Call server endpoint to clear database
                response = requests.post("http://localhost:7001/api/database/clear")
                if response.status_code == 200:
                    QMessageBox.information(self, "Success", "Database cleared successfully!")
                    self.refresh_statistics()
                else:
                    QMessageBox.warning(self, "Warning", 
                                       "Could not clear database through server.\n"
                                       "You may need to manually delete the database folder.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to clear database: {e}")
