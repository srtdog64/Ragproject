# ui/chat/code_block_widget.py
"""
Enhanced code block widget with copy button
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QTextEdit, QLabel, QApplication
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QSyntaxHighlighter, QTextCharFormat, QColor
import re


class CodeBlockWidget(QWidget):
    """Widget for displaying code with copy functionality"""
    
    def __init__(self, code: str, language: str = ""):
        super().__init__()
        self.code = code
        self.language = language
        self.setupUI()
        
    def setupUI(self):
        """Setup the UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header with language and copy button
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(10, 5, 10, 5)
        
        # Language label
        if self.language:
            lang_label = QLabel(f"[{self.language}]")
            lang_label.setStyleSheet("""
                QLabel {
                    color: #6f42c1;
                    font-weight: bold;
                    font-family: 'Consolas', 'Monaco', monospace;
                    font-size: 12px;
                }
            """)
            header_layout.addWidget(lang_label)
        
        header_layout.addStretch()
        
        # Copy button
        copy_btn = QPushButton("📋 Copy")
        copy_btn.clicked.connect(self.copy_code)
        copy_btn.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 12px;
                color: #333;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
                border-color: #b0b0b0;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
        """)
        header_layout.addWidget(copy_btn)
        
        # Header widget
        header_widget = QWidget()
        header_widget.setStyleSheet("background-color: #f6f8fa; border-bottom: 1px solid #e1e4e8;")
        header_widget.setLayout(header_layout)
        layout.addWidget(header_widget)
        
        # Code display area
        self.code_display = QTextEdit()
        self.code_display.setPlainText(self.code)
        self.code_display.setReadOnly(True)
        self.code_display.setFont(QFont("Consolas", 10))
        self.code_display.setStyleSheet("""
            QTextEdit {
                background-color: #f6f8fa;
                border: none;
                padding: 10px;
                color: #24292e;
            }
        """)
        
        # Apply syntax highlighting if language is specified
        if self.language:
            self.highlighter = CodeHighlighter(self.code_display.document(), self.language)
        
        layout.addWidget(self.code_display)
        
        # Container styling
        self.setStyleSheet("""
            CodeBlockWidget {
                border: 1px solid #e1e4e8;
                border-radius: 6px;
                margin: 5px 0;
            }
        """)
        
        self.setLayout(layout)
    
    def copy_code(self):
        """Copy code to clipboard"""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.code)
        
        # Update button text temporarily
        sender = self.sender()
        original_text = sender.text()
        sender.setText("✅ Copied!")
        sender.setStyleSheet("""
            QPushButton {
                background-color: #d4edda;
                border: 1px solid #c3e6cb;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 12px;
                color: #155724;
            }
        """)
        
        # Reset after 2 seconds
        QTimer.singleShot(2000, lambda: self.reset_button(sender, original_text))
    
    def reset_button(self, button, original_text):
        """Reset button to original state"""
        button.setText(original_text)
        button.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 12px;
                color: #333;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
                border-color: #b0b0b0;
            }
        """)


class CodeHighlighter(QSyntaxHighlighter):
    """Simple syntax highlighter for code"""
    
    def __init__(self, document, language):
        super().__init__(document)
        self.language = language.lower()
        self.setup_patterns()
        
    def setup_patterns(self):
        """Setup highlighting patterns based on language"""
        self.patterns = []
        
        # Keywords
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#d73a49"))
        keyword_format.setFontWeight(QFont.Bold)
        
        if self.language in ['python', 'py']:
            keywords = [
                'def', 'class', 'if', 'elif', 'else', 'for', 'while', 'return',
                'import', 'from', 'as', 'try', 'except', 'finally', 'with',
                'lambda', 'pass', 'break', 'continue', 'True', 'False', 'None'
            ]
        elif self.language in ['javascript', 'js', 'typescript', 'ts']:
            keywords = [
                'function', 'var', 'let', 'const', 'if', 'else', 'for', 'while',
                'return', 'class', 'extends', 'import', 'export', 'async', 'await',
                'true', 'false', 'null', 'undefined', 'new', 'this'
            ]
        else:
            keywords = []
        
        for keyword in keywords:
            pattern = f'\\b{keyword}\\b'
            self.patterns.append((pattern, keyword_format))
        
        # Strings
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#032f62"))
        
        # Double quotes
        self.patterns.append((r'"[^"\\]*(\\.[^"\\]*)*"', string_format))
        # Single quotes
        self.patterns.append((r"'[^'\\]*(\\.[^'\\]*)*'", string_format))
        
        # Comments
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#6a737d"))
        comment_format.setFontItalic(True)
        
        if self.language in ['python', 'py']:
            self.patterns.append((r'#[^\n]*', comment_format))
        else:
            self.patterns.append((r'//[^\n]*', comment_format))
        
        # Numbers
        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#005cc5"))
        self.patterns.append((r'\b\d+\.?\d*\b', number_format))
    
    def highlightBlock(self, text):
        """Apply highlighting to a block of text"""
        for pattern, format in self.patterns:
            expression = re.compile(pattern)
            for match in expression.finditer(text):
                self.setFormat(match.start(), match.end() - match.start(), format)
