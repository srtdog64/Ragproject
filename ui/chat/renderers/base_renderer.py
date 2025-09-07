# ui/chat/renderers/base_renderer.py
"""
Base code renderer class
"""
from PySide6.QtGui import QTextCharFormat, QColor, QFont, QTextCursor
import re


class BaseCodeRenderer:
    """Base class for language-specific code renderers"""
    
    def __init__(self):
        self.setup_formats()
        
    def setup_formats(self):
        """Setup text formats for syntax highlighting"""
        # Base code format
        self.code_format = QTextCharFormat()
        self.code_format.setFontFamily("Consolas, Monaco, 'Courier New', monospace")
        self.code_format.setFontPointSize(10)
        
        # Keyword format
        self.keyword_format = QTextCharFormat(self.code_format)
        self.keyword_format.setForeground(QColor("#d73a49"))
        self.keyword_format.setFontWeight(QFont.Bold)
        
        # String format
        self.string_format = QTextCharFormat(self.code_format)
        self.string_format.setForeground(QColor("#032f62"))
        
        # Comment format
        self.comment_format = QTextCharFormat(self.code_format)
        self.comment_format.setForeground(QColor("#6a737d"))
        self.comment_format.setFontItalic(True)
        
        # Number format
        self.number_format = QTextCharFormat(self.code_format)
        self.number_format.setForeground(QColor("#005cc5"))
        
        # Function/method format
        self.function_format = QTextCharFormat(self.code_format)
        self.function_format.setForeground(QColor("#6f42c1"))
        
        # Class format
        self.class_format = QTextCharFormat(self.code_format)
        self.class_format.setForeground(QColor("#e36209"))
        self.class_format.setFontWeight(QFont.Bold)
        
        # Operator format
        self.operator_format = QTextCharFormat(self.code_format)
        self.operator_format.setForeground(QColor("#d73a49"))
        
        # Built-in/special format
        self.builtin_format = QTextCharFormat(self.code_format)
        self.builtin_format.setForeground(QColor("#005cc5"))
        self.builtin_format.setFontWeight(QFont.Bold)
    
    def get_keywords(self):
        """Get language keywords - override in subclasses"""
        return []
    
    def get_builtin_functions(self):
        """Get built-in functions - override in subclasses"""
        return []
    
    def get_builtin_values(self):
        """Get built-in values - override in subclasses"""
        return []
    
    def get_operators(self):
        """Get operators - override in subclasses"""
        return ['+', '-', '*', '/', '%', '=', '==', '!=', '<', '>', '<=', '>=', 
                '&&', '||', '!', '&', '|', '^', '~', '<<', '>>', '+=', '-=', 
                '*=', '/=', '%=', '&=', '|=', '^=', '<<=', '>>=']
    
    def get_comment_pattern(self):
        """Get comment pattern - override in subclasses"""
        return '//'
    
    def render_line(self, cursor: QTextCursor, line: str, line_number: int = 0):
        """Render a single line of code with syntax highlighting"""
        # Preserve indentation
        leading_spaces = len(line) - len(line.lstrip())
        if leading_spaces > 0:
            cursor.insertText(' ' * leading_spaces, self.code_format)
            line = line.lstrip()
        
        # Check for comments
        comment_pattern = self.get_comment_pattern()
        if comment_pattern and comment_pattern in line:
            comment_pos = line.index(comment_pattern)
            # Render pre-comment part
            self.render_tokens(cursor, line[:comment_pos])
            # Render comment
            cursor.insertText(line[comment_pos:], self.comment_format)
        else:
            self.render_tokens(cursor, line)
    
    def render_tokens(self, cursor: QTextCursor, text: str):
        """Tokenize and render text with appropriate formatting"""
        if not text:
            return
        
        keywords = self.get_keywords()
        builtins = self.get_builtin_functions()
        values = self.get_builtin_values()
        operators = self.get_operators()
        
        # Process character by character for more accurate tokenization
        i = 0
        while i < len(text):
            # Check for strings
            if i < len(text) and text[i] in '"\'':
                quote = text[i]
                j = i + 1
                while j < len(text):
                    if text[j] == '\\':
                        j += 2  # Skip escaped character
                    elif text[j] == quote:
                        j += 1
                        break
                    else:
                        j += 1
                string_token = text[i:j]
                cursor.insertText(string_token, self.string_format)
                i = j
            # Check for numbers
            elif text[i].isdigit():
                j = i
                while j < len(text) and (text[j].isdigit() or text[j] == '.'):
                    j += 1
                num_token = text[i:j]
                cursor.insertText(num_token, self.number_format)
                i = j
            # Check for words (keywords, identifiers)
            elif text[i].isalpha() or text[i] == '_':
                j = i
                while j < len(text) and (text[j].isalnum() or text[j] == '_'):
                    j += 1
                word = text[i:j]
                if word in keywords:
                    cursor.insertText(word, self.keyword_format)
                elif word in builtins or word in values:
                    cursor.insertText(word, self.builtin_format)
                else:
                    cursor.insertText(word, self.code_format)
                i = j
            # Check for operators
            elif text[i] in '+-*/%=<>!&|^~:':
                j = i + 1
                # Handle multi-character operators
                while j < len(text) and text[j] in '=<>&|+-':
                    j += 1
                op = text[i:j]
                if op in operators:
                    cursor.insertText(op, self.operator_format)
                else:
                    cursor.insertText(op, self.code_format)
                i = j
            # Check for whitespace
            elif text[i] in ' \t':
                j = i
                while j < len(text) and text[j] in ' \t':
                    j += 1
                ws = text[i:j]
                cursor.insertText(ws, self.code_format)
                i = j
            # Handle other characters (parentheses, brackets, etc.)
            else:
                cursor.insertText(text[i], self.code_format)
                i += 1
    
    def render_line_as_html(self, line: str, line_number: int = 0) -> str:
        """Render a single line of code as HTML with syntax highlighting"""
        # Handle empty lines
        if not line:
            return '&nbsp;'
        
        # Calculate leading spaces/tabs
        leading_spaces = 0
        i = 0
        while i < len(line) and line[i] in ' \t':
            if line[i] == ' ':
                leading_spaces += 1
            else:  # tab
                leading_spaces += 4
            i += 1
        
        # Create indentation HTML
        indent_html = '&nbsp;' * leading_spaces
        
        # Get the actual code content (after indentation)
        code_content = line[i:]
        
        # If no code content, just return indentation
        if not code_content:
            return indent_html if indent_html else '&nbsp;'
        
        # Check for comments
        comment_pattern = self.get_comment_pattern()
        
        if comment_pattern and comment_pattern in code_content:
            comment_pos = code_content.index(comment_pattern)
            # Render pre-comment part
            pre_comment = self.render_tokens_as_html(code_content[:comment_pos])
            # Render comment
            comment_html = f'<span style="color:#6b7280;font-style:italic;">{self.escape_html(code_content[comment_pos:])}</span>'
            return indent_html + pre_comment + comment_html
        else:
            # No comment, render the whole line
            return indent_html + self.render_tokens_as_html(code_content)
    
    def render_tokens_as_html(self, text: str) -> str:
        """Tokenize and render text as HTML with appropriate formatting"""
        if not text:
            return ''
        
        keywords = self.get_keywords()
        builtins = self.get_builtin_functions()
        values = self.get_builtin_values()
        operators = self.get_operators()
        
        # Process character by character for more accurate tokenization
        html = ''
        i = 0
        while i < len(text):
            # Check for strings
            if i < len(text) and text[i] in '"\'':
                quote = text[i]
                j = i + 1
                while j < len(text):
                    if text[j] == '\\':
                        j += 2  # Skip escaped character
                    elif text[j] == quote:
                        j += 1
                        break
                    else:
                        j += 1
                string_token = text[i:j]
                html += f'<span style="color:#059669;">{self.escape_html(string_token)}</span>'
                i = j
            # Check for numbers
            elif text[i].isdigit():
                j = i
                while j < len(text) and (text[j].isdigit() or text[j] == '.'):
                    j += 1
                num_token = text[i:j]
                html += f'<span style="color:#0891b2;">{self.escape_html(num_token)}</span>'
                i = j
            # Check for words (keywords, identifiers)
            elif text[i].isalpha() or text[i] == '_':
                j = i
                while j < len(text) and (text[j].isalnum() or text[j] == '_'):
                    j += 1
                word = text[i:j]
                if word in keywords:
                    html += f'<span style="color:#dc2626;font-weight:600;">{self.escape_html(word)}</span>'
                elif word in builtins or word in values:
                    html += f'<span style="color:#7c3aed;font-weight:500;">{self.escape_html(word)}</span>'
                else:
                    html += self.escape_html(word)
                i = j
            # Check for operators
            elif text[i] in '+-*/%=<>!&|^~:':
                j = i + 1
                # Handle multi-character operators
                while j < len(text) and text[j] in '=<>&|+-':
                    j += 1
                op = text[i:j]
                html += f'<span style="color:#ea580c;">{self.escape_html(op)}</span>'
                i = j
            # Check for whitespace
            elif text[i] in ' \t':
                j = i
                while j < len(text) and text[j] in ' \t':
                    j += 1
                ws = text[i:j]
                html += ws.replace(' ', '&nbsp;').replace('\t', '&nbsp;' * 4)
                i = j
            # Handle other characters (parentheses, brackets, etc.)
            else:
                html += self.escape_html(text[i])
                i += 1
        
        return html
    
    def escape_html(self, text: str) -> str:
        """Escape HTML special characters"""
        return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&#39;')
