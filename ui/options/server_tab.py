# ui/options/server_tab.py
"""
Server Configuration Tab
"""
from PySide6.QtWidgets import *
from PySide6.QtCore import Qt
import os


class ServerTab(QWidget):
    """Server configuration tab"""
    
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config = config_manager
        self.parent_widget = parent
        self.setupUI()
        
    def setupUI(self):
        """Setup the UI"""
        layout = QVBoxLayout()
        
        # Info
        info = QLabel("""
        <div style='background-color: #e3f2fd; padding: 10px; border-radius: 5px;'>
        <b>🌐 Server Configuration:</b><br>
        Configure server URL and API keys for various services.
        </div>
        """)
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # Server URL
        url_group = QGroupBox("Server URL")
        url_layout = QVBoxLayout()
        
        self.url_input = QLineEdit()
        self.url_input.setText(self.config.get_server_url())
        self.url_input.setPlaceholderText("http://localhost:7001")
        
        url_info = QLabel("""
        <small style='color: #666;'>
        RAG server endpoint (default: http://localhost:7001)
        </small>
        """)
        
        url_layout.addWidget(self.url_input)
        url_layout.addWidget(url_info)
        url_group.setLayout(url_layout)
        layout.addWidget(url_group)
        
        # API Keys
        keys_group = QGroupBox("API Keys")
        keys_layout = QFormLayout()
        
        # OpenAI
        self.openai_input = QLineEdit()
        self.openai_input.setEchoMode(QLineEdit.Password)
        self.openai_input.setPlaceholderText("sk-...")
        openai_key = os.getenv("OPENAI_API_KEY", "")
        if openai_key:
            self.openai_input.setText("*" * 20)
        keys_layout.addRow("OpenAI API Key:", self.openai_input)
        
        # Claude
        self.claude_input = QLineEdit()
        self.claude_input.setEchoMode(QLineEdit.Password)
        self.claude_input.setPlaceholderText("sk-ant-...")
        claude_key = os.getenv("ANTHROPIC_API_KEY", "")
        if claude_key:
            self.claude_input.setText("*" * 20)
        keys_layout.addRow("Claude API Key:", self.claude_input)
        
        # Gemini
        self.gemini_input = QLineEdit()
        self.gemini_input.setEchoMode(QLineEdit.Password)
        self.gemini_input.setPlaceholderText("AIza...")
        gemini_key = os.getenv("GEMINI_API_KEY", "")
        if gemini_key:
            self.gemini_input.setText("*" * 20)
        keys_layout.addRow("Gemini API Key:", self.gemini_input)
        
        # Cohere
        self.cohere_input = QLineEdit()
        self.cohere_input.setEchoMode(QLineEdit.Password)
        self.cohere_input.setPlaceholderText("...")
        cohere_key = os.getenv("COHERE_API_KEY", "")
        if cohere_key:
            self.cohere_input.setText("*" * 20)
        keys_layout.addRow("Cohere API Key:", self.cohere_input)
        
        keys_group.setLayout(keys_layout)
        layout.addWidget(keys_group)
        
        # Server Options
        options_group = QGroupBox("Server Options")
        options_layout = QFormLayout()
        
        # Host
        self.host_input = QLineEdit()
        self.host_input.setText(self.config.get("server.host", "0.0.0.0", "server"))
        options_layout.addRow("Host:", self.host_input)
        
        # Port
        self.port_spin = QSpinBox()
        self.port_spin.setRange(1024, 65535)
        self.port_spin.setValue(self.config.get("server.port", 7001, "server"))
        options_layout.addRow("Port:", self.port_spin)
        
        # Log level
        self.log_combo = QComboBox()
        self.log_combo.addItems(["debug", "info", "warning", "error", "critical"])
        current_log = self.config.get("server.log_level", "info", "server")
        self.log_combo.setCurrentText(current_log)
        options_layout.addRow("Log Level:", self.log_combo)
        
        # Auto-reload
        self.reload_check = QCheckBox("Auto-reload on changes")
        self.reload_check.setChecked(self.config.get("server.reload", True, "server"))
        options_layout.addRow("", self.reload_check)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        # Apply button
        apply_btn = QPushButton("Apply Server Settings")
        apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: black;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7B1FA2;
            }
        """)
        apply_btn.clicked.connect(self.applySettings)
        layout.addWidget(apply_btn)
        
        # Warning
        warning = QLabel("""
        <div style='background-color: #fff3e0; padding: 10px; border-radius: 5px; margin-top: 10px;'>
        <b>Note:</b> API keys are stored as environment variables.
        Server restart may be required for some changes to take effect.
        </div>
        """)
        warning.setWordWrap(True)
        layout.addWidget(warning)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def applySettings(self):
        """Apply server settings"""
        # Save server URL
        self.config.set("server.url", self.url_input.text(), "app")
        
        # Save server options
        self.config.set("server.host", self.host_input.text(), "server")
        self.config.set("server.port", self.port_spin.value(), "server")
        self.config.set("server.log_level", self.log_combo.currentText(), "server")
        self.config.set("server.reload", self.reload_check.isChecked(), "server")
        
        # Handle API keys (only if changed from placeholder)
        api_keys_changed = False
        
        if self.openai_input.text() and not self.openai_input.text().startswith("*"):
            os.environ["OPENAI_API_KEY"] = self.openai_input.text()
            api_keys_changed = True
        
        if self.claude_input.text() and not self.claude_input.text().startswith("*"):
            os.environ["ANTHROPIC_API_KEY"] = self.claude_input.text()
            api_keys_changed = True
        
        if self.gemini_input.text() and not self.gemini_input.text().startswith("*"):
            os.environ["GEMINI_API_KEY"] = self.gemini_input.text()
            api_keys_changed = True
        
        if self.cohere_input.text() and not self.cohere_input.text().startswith("*"):
            os.environ["COHERE_API_KEY"] = self.cohere_input.text()
            api_keys_changed = True
        
        msg = "Server settings updated successfully!"
        if api_keys_changed:
            msg += "\nAPI keys have been set as environment variables."
        
        QMessageBox.information(self, "Success", msg)
