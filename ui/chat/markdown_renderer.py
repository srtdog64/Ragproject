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


class MarkdownRenderer:
    """Enhanced markdown renderer with better code block support"""
    
    def __init__(self, text_edit: QTextEdit):
        self.text_edit = text_edit
        self.setup_styles()
        
    def setup_styles(self):
        """Setup text formats for different markdown elements"""
        # Headers
        self.h1_format = QTextCharFormat()
        self.h1_format.setFontPointSize(20)
        self.h1_format.setFontWeight(QFont.Bold)
        
        self.h2_format = QTextCharFormat()
        self.h2_format.setFontPointSize(18)
        self.h2_format.setFontWeight(QFont.Bold)
        
        self.h3_format = QTextCharFormat()
        self.h3_format.setFontPointSize(16)
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
        self.code_text_format.setFontPointSize(10)
        
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
        """Insert a line of code with basic syntax highlighting"""
        # Basic syntax highlighting
        if language.lower() in ['python', 'py']:
            self.highlight_python(cursor, line)
        elif language.lower() in ['javascript', 'js', 'typescript', 'ts']:
            self.highlight_javascript(cursor, line)
        elif language.lower() in ['java', 'c', 'cpp', 'c++', 'csharp', 'c#']:
            self.highlight_c_style(cursor, line)
        else:
            # Default: just insert with code format
            cursor.insertText(line, self.code_text_format)
    
    def highlight_python(self, cursor: QTextCursor, line: str):
        """Apply Python syntax highlighting"""
        keywords = [
            'def', 'class', 'if', 'elif', 'else', 'for', 'while', 'return',
            'import', 'from', 'as', 'try', 'except', 'finally', 'with',
            'lambda', 'pass', 'break', 'continue', 'global', 'nonlocal',
            'assert', 'yield', 'raise', 'del', 'in', 'is', 'not', 'and', 'or'
        ]
        
        # Apply highlighting
        self.apply_syntax_highlighting(cursor, line, keywords, language='python')
    
    def highlight_javascript(self, cursor: QTextCursor, line: str):
        """Apply JavaScript syntax highlighting"""
        keywords = [
            'function', 'var', 'let', 'const', 'if', 'else', 'for', 'while',
            'return', 'class', 'extends', 'import', 'export', 'from', 'async',
            'await', 'try', 'catch', 'finally', 'throw', 'new', 'this',
            'super', 'typeof', 'instanceof', 'in', 'of', 'delete'
        ]
        
        self.apply_syntax_highlighting(cursor, line, keywords, language='javascript')
    
    def highlight_c_style(self, cursor: QTextCursor, line: str):
        """Apply C-style syntax highlighting"""
        keywords = [
            'if', 'else', 'for', 'while', 'do', 'switch', 'case', 'default',
            'break', 'continue', 'return', 'void', 'int', 'float', 'double',
            'char', 'bool', 'true', 'false', 'class', 'public', 'private',
            'protected', 'static', 'const', 'new', 'delete', 'this', 'using',
            'namespace', 'try', 'catch', 'throw', 'finally'
        ]
        
        self.apply_syntax_highlighting(cursor, line, keywords, language='c')
    
    def apply_syntax_highlighting(self, cursor: QTextCursor, line: str, 
                                 keywords: list, language: str):
        """Apply syntax highlighting to a line of code"""
        # Create formats
        keyword_format = QTextCharFormat(self.code_text_format)
        keyword_format.setForeground(QColor("#d73a49"))
        keyword_format.setFontWeight(QFont.Bold)
        
        string_format = QTextCharFormat(self.code_text_format)
        string_format.setForeground(QColor("#032f62"))
        
        comment_format = QTextCharFormat(self.code_text_format)
        comment_format.setForeground(QColor("#6a737d"))
        comment_format.setFontItalic(True)
        
        number_format = QTextCharFormat(self.code_text_format)
        number_format.setForeground(QColor("#005cc5"))
        
        # Check for comment
        comment_start = '#' if language == 'python' else '//'
        if comment_start in line:
            comment_pos = line.index(comment_start)
            # Insert pre-comment part
            self.highlight_line_part(cursor, line[:comment_pos], keywords, 
                                    keyword_format, string_format, number_format)
            # Insert comment
            cursor.insertText(line[comment_pos:], comment_format)
            return
        
        # Process the entire line
        self.highlight_line_part(cursor, line, keywords, keyword_format, 
                                string_format, number_format)
    
    def highlight_line_part(self, cursor: QTextCursor, text: str, keywords: list,
                           keyword_format, string_format, number_format):
        """Highlight part of a line"""
        # Simple tokenization
        tokens = re.findall(r'("[^"]*"|\'[^\']*\'|\b\w+\b|\W+)', text)
        
        for token in tokens:
            if token.startswith('"') or token.startswith("'"):
                # String
                cursor.insertText(token, string_format)
            elif token in keywords:
                # Keyword
                cursor.insertText(token, keyword_format)
            elif token.isdigit():
                # Number
                cursor.insertText(token, number_format)
            else:
                # Default
                cursor.insertText(token, self.code_text_format)
    
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
