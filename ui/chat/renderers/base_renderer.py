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
        
        # Enhanced tokenization pattern
        token_pattern = r'''
            ("(?:[^"\\]|\\.)*")|           # Double-quoted strings
            ('(?:[^'\\]|\\.)*')|           # Single-quoted strings
            (\b\d+\.?\d*[eE]?[+-]?\d*\b)|  # Numbers (int, float, scientific)
            (\b\w+\b)|                      # Words (identifiers, keywords)
            ([\+\-\*/%=<>!&\|\^~]+)|       # Operators
            (\S)                            # Any other non-whitespace
        '''
        
        tokens = re.findall(token_pattern, text, re.VERBOSE)
        
        for token_groups in tokens:
            # Find which group matched
            for i, token in enumerate(token_groups):
                if token:
                    if i in [0, 1]:  # String groups
                        cursor.insertText(token, self.string_format)
                    elif i == 2:  # Number group
                        cursor.insertText(token, self.number_format)
                    elif i == 3:  # Word group
                        if token in keywords:
                            cursor.insertText(token, self.keyword_format)
                        elif token in builtins:
                            cursor.insertText(token, self.builtin_format)
                        elif token in values:
                            cursor.insertText(token, self.builtin_format)
                        else:
                            cursor.insertText(token, self.code_format)
                    elif i == 4:  # Operator group
                        if token in operators:
                            cursor.insertText(token, self.operator_format)
                        else:
                            cursor.insertText(token, self.code_format)
                    else:  # Other
                        cursor.insertText(token, self.code_format)
                    break
        
        # Handle remaining whitespace
        remaining = re.sub(token_pattern, '', text, flags=re.VERBOSE)
        if remaining:
            cursor.insertText(remaining, self.code_format)
