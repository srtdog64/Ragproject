# ui/chat/markdown_renderer.py
"""
Enhanced Markdown renderer with proper code block support
"""
from PySide6.QtWidgets import QTextEdit, QApplication
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import (
    QTextCursor, QTextCharFormat, QTextBlockFormat, 
    QFont, QColor, QTextDocument, QTextOption,
    QTextTableFormat, QTextLength
)
import re
from .renderers import get_renderer


class MarkdownRenderer:
    """Enhanced markdown renderer with better code block support"""
    
    def __init__(self, text_edit: QTextEdit, config_manager=None):
        self.text_edit = text_edit
        self.config = config_manager
        self.setup_styles()
        
    def setup_styles(self):
        """Setup text formats for different markdown elements"""
        # Get font sizes from config
        base_font_size = 10
        code_font_size = 10
        if self.config:
            base_font_size = self.config.get("ui.font_size", 10, "qt")
            code_font_size = self.config.get("ui.code_font_size", 10, "qt")
        
        # Headers
        self.h1_format = QTextCharFormat()
        self.h1_format.setFontPointSize(base_font_size + 10)  # Dynamic sizing
        self.h1_format.setFontWeight(QFont.Bold)
        
        self.h2_format = QTextCharFormat()
        self.h2_format.setFontPointSize(base_font_size + 8)
        self.h2_format.setFontWeight(QFont.Bold)
        
        self.h3_format = QTextCharFormat()
        self.h3_format.setFontPointSize(base_font_size + 6)
        self.h3_format.setFontWeight(QFont.Bold)
        
        # Text formatting
        self.bold_format = QTextCharFormat()
        self.bold_format.setFontWeight(QFont.Bold)
        
        self.italic_format = QTextCharFormat()
        self.italic_format.setFontItalic(True)
        
        # Code formats
        self.inline_code_format = QTextCharFormat()
        self.inline_code_format.setFontFamily("Consolas, Monaco, 'Courier New', monospace")
        self.inline_code_format.setBackground(QColor("#f5f5f5"))
        self.inline_code_format.setForeground(QColor("#d73a49"))
        
        self.code_block_format = QTextBlockFormat()
        self.code_block_format.setBackground(QColor("#f6f8fa"))
        self.code_block_format.setLeftMargin(20)
        self.code_block_format.setRightMargin(20)
        self.code_block_format.setTopMargin(10)
        self.code_block_format.setBottomMargin(10)
        
        self.code_text_format = QTextCharFormat()
        self.code_text_format.setFontFamily("Consolas, Monaco, 'Courier New', monospace")
        self.code_text_format.setFontPointSize(code_font_size)  # Use config font size
        
        # List format
        self.list_format = QTextBlockFormat()
        self.list_format.setLeftMargin(20)
        
        # Link format
        self.link_format = QTextCharFormat()
        self.link_format.setForeground(QColor("#0366d6"))
        self.link_format.setFontUnderline(True)
        
    def render_markdown(self, markdown_text: str):
        """Render markdown text with proper formatting"""
        # Clear the text edit
        self.text_edit.clear()
        
        # Split text into blocks for processing
        blocks = self.split_into_blocks(markdown_text)
        
        cursor = self.text_edit.textCursor()
        cursor.movePosition(QTextCursor.Start)
        
        for block in blocks:
            self.render_block(cursor, block)
    
    def split_into_blocks(self, text: str) -> list:
        """Split markdown text into logical blocks"""
        blocks = []
        lines = text.split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # Check for code block
            if line.strip().startswith('```'):
                # Find the end of code block
                code_lines = [line]
                i += 1
                while i < len(lines):
                    code_lines.append(lines[i])
                    if lines[i].strip().startswith('```'):
                        break
                    i += 1
                blocks.append({
                    'type': 'code_block',
                    'content': '\n'.join(code_lines)
                })
                i += 1
                continue
            
            # Check for headers
            if line.startswith('#'):
                level = len(line) - len(line.lstrip('#'))
                blocks.append({
                    'type': f'h{min(level, 6)}',
                    'content': line.lstrip('#').strip()
                })
                i += 1
                continue
            
            # Check for lists
            if re.match(r'^[\s]*[-*+]\s', line) or re.match(r'^[\s]*\d+\.\s', line):
                list_lines = [line]
                i += 1
                while i < len(lines) and (re.match(r'^[\s]*[-*+]\s', lines[i]) or 
                                         re.match(r'^[\s]*\d+\.\s', lines[i]) or
                                         lines[i].startswith('  ')):
                    list_lines.append(lines[i])
                    i += 1
                blocks.append({
                    'type': 'list',
                    'content': '\n'.join(list_lines)
                })
                continue
            
            # Regular paragraph
            if line.strip():
                blocks.append({
                    'type': 'paragraph',
                    'content': line
                })
            else:
                blocks.append({
                    'type': 'empty',
                    'content': ''
                })
            i += 1
        
        return blocks
    
    def render_block(self, cursor: QTextCursor, block: dict):
        """Render a single block with appropriate formatting"""
        block_type = block['type']
        content = block['content']
        
        if block_type == 'code_block':
            self.render_code_block(cursor, content)
        elif block_type.startswith('h'):
            level = int(block_type[1])
            self.render_header(cursor, content, level)
        elif block_type == 'list':
            self.render_list(cursor, content)
        elif block_type == 'paragraph':
            self.render_paragraph(cursor, content)
        elif block_type == 'empty':
            cursor.insertBlock()
    
    def render_code_block(self, cursor: QTextCursor, content: str):
        """Render a code block with proper formatting and indentation"""
        lines = content.split('\n')
        
        # Extract language if specified
        language = ''
        if lines[0].startswith('```'):
            language = lines[0][3:].strip()
            lines = lines[1:-1] if len(lines) > 2 else lines[1:]
        
        # Insert language label if specified
        if language:
            cursor.insertBlock()
            lang_format = QTextCharFormat()
            lang_format.setFontWeight(QFont.Bold)
            lang_format.setForeground(QColor("#6f42c1"))
            cursor.insertText(f"[{language}]", lang_format)
        
        # Apply code block format
        cursor.insertBlock()
        cursor.setBlockFormat(self.code_block_format)
        
        # Insert code with preserved indentation
        for i, line in enumerate(lines):
            if i > 0:
                cursor.insertBlock()
                cursor.setBlockFormat(self.code_block_format)
            
            # Preserve indentation and apply syntax highlighting
            self.insert_code_line(cursor, line, language)
        
        # Reset block format for next content
        cursor.insertBlock()
        cursor.setBlockFormat(QTextBlockFormat())
    
    def insert_code_line(self, cursor: QTextCursor, line: str, language: str):
        """Insert a line of code using language-specific renderer"""
        # Get appropriate renderer for the language
        renderer = get_renderer(language)
        
        # Use the renderer to render the line
        renderer.render_line(cursor, line)
    
    # Legacy methods - kept for backward compatibility but now using modular renderers
    # These can be removed if no other code depends on them
    
    def render_header(self, cursor: QTextCursor, content: str, level: int):
        """Render a header"""
        cursor.insertBlock()
        
        if level == 1:
            cursor.insertText(content, self.h1_format)
        elif level == 2:
            cursor.insertText(content, self.h2_format)
        else:
            cursor.insertText(content, self.h3_format)
        
        cursor.insertBlock()
    
    def render_list(self, cursor: QTextCursor, content: str):
        """Render a list"""
        lines = content.split('\n')
        cursor.insertBlock()
        
        for line in lines:
            if line.strip():
                cursor.setBlockFormat(self.list_format)
                # Process inline formatting
                self.render_inline_formatting(cursor, line)
                cursor.insertBlock()
    
    def render_paragraph(self, cursor: QTextCursor, content: str):
        """Render a paragraph with inline formatting"""
        cursor.insertBlock()
        self.render_inline_formatting(cursor, content)
    
    def render_inline_formatting(self, cursor: QTextCursor, text: str):
        """Apply inline formatting (bold, italic, code, links)"""
        # Pattern for inline elements
        pattern = r'(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`|\[([^\]]+)\]\(([^)]+)\))'
        
        parts = re.split(pattern, text)
        
        for part in parts:
            if not part:
                continue
            
            if part.startswith('**') and part.endswith('**'):
                # Bold
                cursor.insertText(part[2:-2], self.bold_format)
            elif part.startswith('*') and part.endswith('*'):
                # Italic
                cursor.insertText(part[1:-1], self.italic_format)
            elif part.startswith('`') and part.endswith('`'):
                # Inline code
                cursor.insertText(part[1:-1], self.inline_code_format)
            elif part.startswith('['):
                # Link - extract text and URL
                match = re.match(r'\[([^\]]+)\]\(([^)]+)\)', part)
                if match:
                    link_text = match.group(1)
                    cursor.insertText(link_text, self.link_format)
            else:
                # Regular text
                cursor.insertText(part)
