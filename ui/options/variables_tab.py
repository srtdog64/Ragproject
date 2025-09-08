"""
Variables Tab for Options Widget
System-wide configuration variables
"""
from PySide6.QtWidgets import *
from PySide6.QtCore import *

class VariablesTab(QWidget):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("System Variables")
        title.setStyleSheet("font-size: 14px; font-weight: bold; padding: 5px;")
        layout.addWidget(title)
        
        # Description
        desc = QLabel("Fine-tune advanced system parameters for optimal performance.")
        desc.setStyleSheet("color: #666; padding: 5px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # Scroll area for variables
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()
        
        self.var_widgets = {}
        
        # UI Settings section
        ui_group = self.create_group_box("UI Settings")
        ui_layout = QFormLayout()
        
        self.font_size = QSpinBox()
        self.font_size.setRange(8, 20)
        self.font_size.setValue(self.config.get("ui.font_size", 10, "app"))
        ui_layout.addRow("Font Size:", self.font_size)
        self.var_widgets["ui.font_size"] = self.font_size
        
        self.code_font_size = QSpinBox()
        self.code_font_size.setRange(8, 20)
        self.code_font_size.setValue(self.config.get("ui.code_font_size", 10, "app"))
        ui_layout.addRow("Code Font Size:", self.code_font_size)
        self.var_widgets["ui.code_font_size"] = self.code_font_size
        
        self.auto_scroll = QCheckBox()
        self.auto_scroll.setChecked(self.config.get("ui.auto_scroll", True, "app"))
        ui_layout.addRow("Auto Scroll:", self.auto_scroll)
        self.var_widgets["ui.auto_scroll"] = self.auto_scroll
        
        ui_group.setLayout(ui_layout)
        scroll_layout.addWidget(ui_group)
        
        # Retrieval section - SIMPLIFIED CONFIGURATION
        retrieval_group = self.create_group_box("Retrieval & Search")
        retrieval_layout = QFormLayout()
        
        # Retrieve K - How many to get from vector store
        self.retrieve_k = QSpinBox()
        self.retrieve_k.setRange(1, 100)
        self.retrieve_k.setValue(self.config.get("retrieval.retrieve_k", 20, "server"))
        self.retrieve_k.setToolTip("Number of documents to retrieve from vector store")
        retrieval_layout.addRow("Retrieve from Store:", self.retrieve_k)
        self.var_widgets["retrieval.retrieve_k"] = self.retrieve_k
        
        # Rerank K - How many to keep after reranking
        self.rerank_k = QSpinBox()
        self.rerank_k.setRange(1, 100) # Set initial max range high, will be controlled by retrieve_k
        self.rerank_k.setValue(self.config.get("retrieval.rerank_k", 5, "server"))
        self.rerank_k.setToolTip("Number of documents to keep after reranking (final context)")
        retrieval_layout.addRow("Context after Rerank:", self.rerank_k)
        self.var_widgets["retrieval.rerank_k"] = self.rerank_k

        # --- CORRECTED VALIDATION LOGIC ---
        # Connect the signal from retrieve_k to the validation slot
        self.retrieve_k.valueChanged.connect(self.update_rerank_k_validation)
        # Initialize the validation state when the UI is first created
        self.update_rerank_k_validation(self.retrieve_k.value())
        
        # Max context chars
        self.max_context_chars = QSpinBox()
        self.max_context_chars.setRange(1000, 50000)
        self.max_context_chars.setSingleStep(1000)
        self.max_context_chars.setValue(self.config.get("retrieval.max_context_chars", 12000, "server"))
        self.max_context_chars.setSuffix(" chars")
        self.max_context_chars.setToolTip("Maximum characters to include in context")
        retrieval_layout.addRow("Max Context Size:", self.max_context_chars)
        self.var_widgets["retrieval.max_context_chars"] = self.max_context_chars
        
        retrieval_group.setLayout(retrieval_layout)
        scroll_layout.addWidget(retrieval_group)
        
        # Pipeline section
        pipeline_group = self.create_group_box("Pipeline")
        pipeline_layout = QFormLayout()
        
        self.query_expansion = QSpinBox()
        self.query_expansion.setRange(0, 5)
        self.query_expansion.setValue(self.config.get("pipeline.query_expansion.expansions", 0, "server"))
        self.query_expansion.setToolTip("Number of query expansions (0 = disabled)")
        pipeline_layout.addRow("Query Expansions:", self.query_expansion)
        self.var_widgets["pipeline.query_expansion.expansions"] = self.query_expansion
        
        pipeline_group.setLayout(pipeline_layout)
        scroll_layout.addWidget(pipeline_group)
        
        # Ingestion section
        ingestion_group = self.create_group_box("Ingestion")
        ingestion_layout = QFormLayout()
        
        self.batch_size = QSpinBox()
        self.batch_size.setRange(1, 1000)
        self.batch_size.setValue(self.config.get("ingester.batch_size", 100, "server"))
        ingestion_layout.addRow("Batch Size:", self.batch_size)
        self.var_widgets["ingester.batch_size"] = self.batch_size
        
        self.max_parallel = QSpinBox()
        self.max_parallel.setRange(1, 32)
        self.max_parallel.setValue(self.config.get("ingester.max_parallel", 8, "server"))
        ingestion_layout.addRow("Max Parallel:", self.max_parallel)
        self.var_widgets["ingester.max_parallel"] = self.max_parallel
        
        ingestion_group.setLayout(ingestion_layout)
        scroll_layout.addWidget(ingestion_group)
        
        # Apply button
        apply_btn = QPushButton("Apply Variables")
        apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #607D8B;
                color: white;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #455A64;
            }
        """)
        apply_btn.clicked.connect(self.applyVariables)
        scroll_layout.addWidget(apply_btn)
        
        scroll_layout.addStretch()
        scroll_widget.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        
        layout.addWidget(scroll_area)
        self.setLayout(layout)
    
    def create_group_box(self, title):
        """Create a styled group box"""
        group = QGroupBox(title)
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #ccc;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        return group
    
    def update_rerank_k_validation(self, retrieve_k_value):
        """
        Ensures that rerank_k cannot be set higher than retrieve_k.
        This is connected to the valueChanged signal of retrieve_k.
        """
        # 1. Update the maximum allowed value for rerank_k
        self.rerank_k.setMaximum(retrieve_k_value)
        
        # 2. If the current rerank_k value is now higher than the new max,
        #    automatically lower it. This ensures the constraint is always met.
        if self.rerank_k.value() > retrieve_k_value:
            self.rerank_k.setValue(retrieve_k_value)
    
    def applyVariables(self):
        """Apply all variable changes"""
        for key, widget in self.var_widgets.items():
            if isinstance(widget, QCheckBox):
                value = widget.isChecked()
            elif isinstance(widget, QSpinBox):
                value = widget.value()
            elif isinstance(widget, QLineEdit):
                value = widget.text()
            else:
                continue
            
            # Determine which config file to update
            if key.startswith("ui."):
                self.config.set(key, value, "app")
            else:
                self.config.set(key, value, "server")
        
        # Save configs
        self.config.save_config("config/config.yaml", self.config.server_config)
        self.config.save_config("config/qt_app_config.yaml", self.config.app_config)
        
        QMessageBox.information(self, "Success", "Variables applied successfully!")

