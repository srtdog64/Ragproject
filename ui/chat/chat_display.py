# ui/chat/chat_display.py
"""
Enhanced chat display widget with improved code rendering
"""
from PySide6.QtWidgets import QTextBrowser, QMenu, QApplication, QToolTip
from PySide6.QtCore import Qt, Signal, QTimer, QUrl
from PySide6.QtGui import QTextCursor, QTextCharFormat, QFont, QColor, QAction, QTextBlockFormat
from .markdown_renderer import MarkdownRenderer
import re


class ChatDisplay(QTextBrowser):
    """Enhanced chat display with markdown support"""
    
    def __init__(self, config_manager=None):
        super().__init__()
        self.config = config_manager
        self.setReadOnly(True)
        self.setAcceptRichText(True)
        
        # Setup markdown renderer with config
        self.markdown_renderer = MarkdownRenderer(self, config_manager)
        
        # Setup styles
        self.setup_styles()
        
        # Setup context menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        
        # Setup anchor click handling - IMPORTANT: Prevent default navigation
        self.setOpenExternalLinks(False)  # Handle links internally
        self.setOpenLinks(False)  # Disable automatic link opening
        self.anchorClicked.connect(self.handle_anchor_click)
        
        # Message tracking
        self.messages = []
        self.current_streaming_message = None
        self.code_blocks = []  # Store code blocks for copying
        
    def setup_styles(self):
        """Setup display styles"""
        # Set default font
        font = QFont("Segoe UI", 10)
        self.setFont(font)
        
        # Set style sheet for overall appearance
        self.setStyleSheet("""
            QTextBrowser {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 10px;
                selection-background-color: #b3d9ff;
            }
        """)
        
    def add_message(self, role: str, content: str, streaming: bool = False):
        """Add a message to the display"""
        if streaming and self.current_streaming_message:
            # Update existing streaming message
            self.update_streaming_message(content)
        else:
            # Add new message
            self.append_message(role, content, streaming)
    
    def append_message(self, role: str, content: str, streaming: bool):
        """Append a new message"""
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        
        # Add spacing between messages
        if self.messages:
            cursor.insertBlock()
            cursor.insertBlock()
        
        # Insert role header
        role_format = QTextCharFormat()
        role_format.setFontWeight(QFont.Bold)
        role_format.setFontPointSize(11)
        
        if role == "user":
            role_format.setForeground(QColor("#0066cc"))
            cursor.insertText("👤 You", role_format)
        else:
            role_format.setForeground(QColor("#008800"))
            cursor.insertText("🤖 Assistant", role_format)
        
        cursor.insertBlock()
        
        # Store message info
        message_info = {
            'role': role,
            'content': content,
            'start_position': cursor.position(),
            'streaming': streaming
        }
        
        if streaming:
            self.current_streaming_message = message_info
        
        self.messages.append(message_info)
        
        # Render content
        self.render_content(content, cursor.position())
        
        # Scroll to bottom
        self.ensureCursorVisible()
    
    def update_streaming_message(self, new_content: str):
        """Update the current streaming message"""
        if not self.current_streaming_message:
            return
        
        # Get the position range to replace
        start_pos = self.current_streaming_message['start_position']
        
        cursor = self.textCursor()
        cursor.setPosition(start_pos)
        cursor.movePosition(QTextCursor.End, QTextCursor.KeepAnchor)
        
        # Remove old content
        cursor.removeSelectedText()
        
        # Update message info
        self.current_streaming_message['content'] = new_content
        
        # Render new content
        self.render_content(new_content, start_pos)
        
        # Scroll to bottom
        self.ensureCursorVisible()
    
    def finish_streaming(self):
        """Mark streaming as finished"""
        if self.current_streaming_message:
            self.current_streaming_message['streaming'] = False
            self.current_streaming_message = None
    
    def render_content(self, content: str, start_position: int):
        """Render content with markdown support"""
        cursor = self.textCursor()
        
        # Ensure cursor is at the correct position
        if start_position > self.document().characterCount():
            start_position = self.document().characterCount() - 1
        
        cursor.setPosition(max(0, start_position))
        
        # Check if content contains code blocks
        if '```' in content:
            self.render_with_code_blocks(content, cursor)
        else:
            # Simple rendering for non-code content
            self.render_simple_markdown(content, cursor)
    
    def render_with_code_blocks(self, content: str, cursor: QTextCursor):
        """Render content with proper code block handling"""
        parts = re.split(r'(```[\s\S]*?```)', content)
        
        for part in parts:
            if part.startswith('```') and part.endswith('```'):
                # Code block
                self.render_code_block(part, cursor)
            else:
                # Regular content
                if part.strip():
                    self.render_simple_markdown(part, cursor)
    
    def filter_code_content(self, lines: list, language: str) -> str:
        """Filter out non-code content and auto-correct indentation"""
        code_lines = []
        in_docstring = False
        docstring_quotes = None
        min_indent = float('inf')  # Track minimum indentation
        
        # First pass: collect code lines and find minimum indentation
        temp_lines = []
        for line in lines:
            # Check if line contains Korean
            has_korean = any('\uac00' <= char <= '\ud7a3' for char in line)
            
            # Handle docstrings for Python
            if language.lower() in ['python', 'py']:
                if '"""' in line or "'''" in line:
                    if not in_docstring:
                        in_docstring = True
                        docstring_quotes = '"""' if '"""' in line else "'''"
                        temp_lines.append(line)
                    elif docstring_quotes in line:
                        in_docstring = False
                        docstring_quotes = None
                        temp_lines.append(line)
                    else:
                        temp_lines.append(line)
                    continue
                
                # Inside docstring - keep it
                if in_docstring:
                    temp_lines.append(line)
                    continue
            
            # If line has Korean, check if it's a standalone description or part of code
            if has_korean:
                stripped = line.strip()
                
                # Skip pure Korean description lines
                if stripped and stripped[0] >= '\uac00' and stripped[0] <= '\ud7a3':
                    # Check if it looks like a description line
                    if not any(char in stripped for char in ['=', '(', ')', '[', ']', '{', '}', ';', ':', '<', '>']):
                        continue  # Skip pure Korean description
                
                # Handle comments with Korean
                if language.lower() in ['python', 'py']:
                    if '#' in line:
                        # Keep the code part before the comment
                        code_part = line.split('#')[0]
                        if code_part.strip():
                            temp_lines.append(code_part.rstrip())
                        # Skip if it's only a Korean comment
                        continue
                    # Check if line has code structure
                    elif any(keyword in line for keyword in ['def ', 'class ', 'import ', 'from ', 'return ', 'if ', 'for ', 'while ', 'print(', '=']):
                        temp_lines.append(line)
                    else:
                        # Likely a Korean description, skip
                        continue
                        
                elif language.lower() in ['javascript', 'js', 'typescript', 'ts', 'java', 'c', 'cpp', 'c++', 'csharp', 'cs', 'c#']:
                    if '//' in line:
                        # Keep the code part before the comment
                        code_part = line.split('//')[0]
                        if code_part.strip():
                            temp_lines.append(code_part.rstrip())
                        continue
                    # Check for code structure
                    elif any(keyword in line for keyword in ['{', '}', ';', 'public', 'private', 'class', 'void', 'int', 'string', 'var', 'let', 'const', 'function']):
                        temp_lines.append(line)
                    else:
                        # Skip Korean descriptions
                        continue
                else:
                    # For other languages, be conservative
                    if any(char in line for char in ['=', '(', ')', '{', '}', '[', ']', ';']):
                        temp_lines.append(line)
                    else:
                        continue
            else:
                # No Korean, keep the line as is
                temp_lines.append(line)
        
        # Second pass: find minimum indentation (excluding empty lines)
        for line in temp_lines:
            if line.strip():  # Non-empty line
                # Count leading spaces/tabs
                indent = 0
                for char in line:
                    if char == ' ':
                        indent += 1
                    elif char == '\t':
                        indent += 4  # Consider tab as 4 spaces
                    else:
                        break
                min_indent = min(min_indent, indent)
        
        # If no non-empty lines or min_indent is still inf, use 0
        if min_indent == float('inf'):
            min_indent = 0
        
        # Third pass: normalize indentation
        for line in temp_lines:
            if not line.strip():  # Empty line
                code_lines.append('')
            else:
                # Remove minimum indentation from each line
                spaces_to_remove = min_indent
                i = 0
                while i < len(line) and spaces_to_remove > 0:
                    if line[i] == ' ':
                        spaces_to_remove -= 1
                        i += 1
                    elif line[i] == '\t':
                        spaces_to_remove -= 4
                        i += 1
                    else:
                        break
                code_lines.append(line[i:])
        
    def auto_indent_code(self, lines: list, language: str) -> list:
        """Auto-correct indentation based on language syntax"""
        if not lines:
            return lines
        
        indented_lines = []
        indent_level = 0
        indent_size = 4  # Standard indent size
        
        # Language-specific indentation rules
        if language.lower() in ['python', 'py']:
            # Python: indent after :, dedent for return/break/continue/pass
            for line in lines:
                stripped = line.strip()
                if not stripped:
                    indented_lines.append('')
                    continue
                
                # Check for dedent keywords first
                if stripped.startswith(('return', 'break', 'continue', 'pass')):
                    indented_lines.append(' ' * (indent_level * indent_size) + stripped)
                    if indent_level > 0 and not stripped.endswith(':'):
                        indent_level -= 1
                elif stripped.startswith(('elif', 'else', 'except', 'finally')):
                    if indent_level > 0:
                        indent_level -= 1
                    indented_lines.append(' ' * (indent_level * indent_size) + stripped)
                    if stripped.endswith(':'):
                        indent_level += 1
                else:
                    indented_lines.append(' ' * (indent_level * indent_size) + stripped)
                    # Check if line ends with : (new block)
                    if stripped.endswith(':'):
                        indent_level += 1
                    
        elif language.lower() in ['csharp', 'cs', 'c#', 'java', 'cpp', 'c++', 'c', 'javascript', 'js', 'typescript', 'ts']:
            # C-style languages: track { and }
            for line in lines:
                stripped = line.strip()
                if not stripped:
                    indented_lines.append('')
                    continue
                
                # Check for closing brace first
                if stripped.startswith('}'):
                    if indent_level > 0:
                        indent_level -= 1
                    indented_lines.append(' ' * (indent_level * indent_size) + stripped)
                    # Check if there's an opening brace on the same line
                    if '{' in stripped:
                        indent_level += 1
                else:
                    # Normal line
                    indented_lines.append(' ' * (indent_level * indent_size) + stripped)
                    
                    # Count braces
                    open_braces = stripped.count('{')
                    close_braces = stripped.count('}')
                    indent_level += (open_braces - close_braces)
                    
                    # Ensure indent_level doesn't go negative
                    if indent_level < 0:
                        indent_level = 0
        else:
            # For other languages, just normalize existing indentation
            return self.normalize_indentation(lines)
        
        return indented_lines
    
    def normalize_indentation(self, lines: list) -> list:
        """Normalize indentation by removing minimum common indentation"""
        if not lines:
            return lines
        
        # Find minimum indentation
        min_indent = float('inf')
        for line in lines:
            if line.strip():  # Non-empty line
                indent = 0
                for char in line:
                    if char == ' ':
                        indent += 1
                    elif char == '\t':
                        indent += 4
                    else:
                        break
                min_indent = min(min_indent, indent)
        
        if min_indent == float('inf'):
            min_indent = 0
        
        # Remove minimum indentation
        normalized_lines = []
        for line in lines:
            if not line.strip():
                normalized_lines.append('')
            else:
                spaces_to_remove = min_indent
                i = 0
                while i < len(line) and spaces_to_remove > 0:
                    if line[i] == ' ':
                        spaces_to_remove -= 1
                        i += 1
                    elif line[i] == '\t':
                        spaces_to_remove -= 4
                        i += 1
                    else:
                        break
                normalized_lines.append(line[i:])
        
        return normalized_lines
    
    def auto_correct_indentation(self, lines: list, language: str) -> list:
        """Auto-correct indentation based on language syntax"""
        if not lines:
            return lines
        
        corrected_lines = []
        indent_level = 0
        indent_size = 4  # Standard indent size
        
        # Language-specific indentation rules
        if language.lower() in ['csharp', 'cs', 'c#', 'java', 'cpp', 'c++', 'c', 'javascript', 'js', 'typescript', 'ts']:
            # C-style languages: track { and }
            for line in lines:
                stripped = line.strip()
                if not stripped:
                    corrected_lines.append('')
                    continue
                
                # Check for closing brace first
                if stripped.startswith('}'):
                    if indent_level > 0:
                        indent_level -= 1
                    corrected_lines.append(' ' * (indent_level * indent_size) + stripped)
                    # Check if there's an opening brace on the same line after the closing brace
                    if '{' in stripped[1:]:
                        indent_level += 1
                else:
                    # Normal line
                    corrected_lines.append(' ' * (indent_level * indent_size) + stripped)
                    
                    # Count braces
                    open_braces = stripped.count('{')
                    close_braces = stripped.count('}')
                    indent_level += (open_braces - close_braces)
                    
                    # Ensure indent_level doesn't go negative
                    if indent_level < 0:
                        indent_level = 0
                        
        elif language.lower() in ['python', 'py']:
            # Python: indent after :, dedent for specific keywords
            for line in lines:
                stripped = line.strip()
                if not stripped:
                    corrected_lines.append('')
                    continue
                
                # Check for dedent keywords first
                if stripped.startswith(('return', 'break', 'continue', 'pass')):
                    corrected_lines.append(' ' * (indent_level * indent_size) + stripped)
                    if indent_level > 0 and not stripped.endswith(':'):
                        indent_level -= 1
                elif stripped.startswith(('elif', 'else', 'except', 'finally')):
                    if indent_level > 0:
                        indent_level -= 1
                    corrected_lines.append(' ' * (indent_level * indent_size) + stripped)
                    if stripped.endswith(':'):
                        indent_level += 1
                else:
                    corrected_lines.append(' ' * (indent_level * indent_size) + stripped)
                    # Check if line ends with : (new block)
                    if stripped.endswith(':'):
                        indent_level += 1
        else:
            # For other languages, just normalize existing indentation
            return self.normalize_indentation(lines)
        
        return corrected_lines
    
    def render_code_block(self, code_block: str, cursor: QTextCursor):
        """Render a code block with auto-corrected indentation and line numbers"""
        lines = code_block.split('\n')
        
        # Extract language
        language = ''
        if lines[0].startswith('```'):
            language = lines[0][3:].strip()
            lines = lines[1:-1] if lines and lines[-1] == '```' else lines[1:]
        
        # Format language display
        display_language = language.upper()
        if language.lower() in ['csharp', 'cs']:
            display_language = 'C#'
        elif language.lower() == 'cpp':
            display_language = 'C++'
        elif language.lower() == 'js':
            display_language = 'JavaScript'
        elif language.lower() == 'py':
            display_language = 'Python'
        
        # Auto-correct indentation for the code
        corrected_lines = self.auto_correct_indentation(lines, language)
        code_content = '\n'.join(corrected_lines)
        
        # Store code block for later copying
        if not hasattr(self, 'code_blocks'):
            self.code_blocks = []
        code_block_index = len(self.code_blocks)
        self.code_blocks.append(code_content)
        
        # Insert a block for spacing
        cursor.insertBlock()
        
        # Create container with header
        container_start = f'''
        <div style="border:1px solid #d1d5db;border-radius:6px;margin:8px 0;overflow:hidden;">
            <div style="background:#f3f4f6;padding:8px 12px;border-bottom:1px solid #d1d5db;display:flex;justify-content:space-between;align-items:center;">
                <span style="color:#6b7280;font-weight:600;font-size:12px;font-family:Consolas,Monaco,monospace;">{display_language if display_language else 'CODE'}</span>
                <span>
                    <a href="copy:{code_block_index}" style="color:#3b82f6;text-decoration:none;font-size:12px;font-family:Consolas,Monaco,monospace;">📋 Copy</a>
                </span>
            </div>
            <div style="background:#f9fafb;padding:0;overflow-x:auto;">
                <table style="width:100%;margin:0;padding:0;border:none;border-collapse:collapse;border-spacing:0;">
        '''
        
        cursor.insertHtml(container_start)
        
        # Process each line with line numbers
        code_lines = code_content.split('\n')
        for i, line in enumerate(code_lines, 1):
            # Preserve original spaces/tabs
            # HTML will render them properly with white-space: pre
            
            # Apply simple highlighting
            highlighted = self.simple_syntax_highlight(line, language)
            
            # Create table row with light theme and no spacing
            row_html = f'''
                <tr style="margin:0;padding:0;">
                    <td style="padding:0 8px;text-align:right;color:#6b7280;font-size:12px;background:#f3f4f6;border-right:1px solid #e5e7eb;min-width:40px;user-select:none;font-family:Consolas,Monaco,monospace;vertical-align:top;line-height:18px;">{i}</td>
                    <td style="padding:0 12px;font-size:13px;font-family:Consolas,Monaco,monospace;line-height:18px;background:#f9fafb;color:#374151;white-space:pre;overflow-x:auto;">{highlighted}</td>
                </tr>
            '''
            cursor.insertHtml(row_html)
        
        # Close table and container
        cursor.insertHtml('</table></div></div>')
        
        # Insert spacing after code block
        cursor.insertBlock()
    
    def simple_syntax_highlight(self, text: str, language: str) -> str:
        """Enhanced syntax highlighting with light theme colors"""
        if not text:
            return ''
        
        # Preserve leading whitespace
        leading_ws = ''
        i = 0
        while i < len(text) and text[i] in ' \t':
            leading_ws += text[i]  # Keep spaces and tabs as-is
            i += 1
        
        # Get the code part after indentation
        code_part = text[i:]
        
        if not code_part:
            return leading_ws
        
        # Check for comments first
        if language.lower() in ['python', 'py'] and code_part.strip().startswith('#'):
            return leading_ws + f'<span style="color:#6b7280;font-style:italic;">{self.escape_html(code_part)}</span>'
        elif language.lower() in ['csharp', 'cs', 'c#', 'java', 'js', 'javascript', 'typescript', 'ts', 'cpp', 'c++', 'c']:
            if code_part.strip().startswith('//'):
                return leading_ws + f'<span style="color:#6b7280;font-style:italic;">{self.escape_html(code_part)}</span>'
        
        # Process the code part
        result = ''
        j = 0
        while j < len(code_part):
            # Check for strings
            if code_part[j] in '"\'':
                quote = code_part[j]
                k = j + 1
                while k < len(code_part):
                    if code_part[k] == '\\':
                        k += 2
                    elif code_part[k] == quote:
                        k += 1
                        break
                    else:
                        k += 1
                string_part = code_part[j:k]
                result += f'<span style="color:#059669;">{self.escape_html(string_part)}</span>'
                j = k
            # Check for numbers
            elif code_part[j].isdigit():
                k = j
                while k < len(code_part) and (code_part[k].isdigit() or code_part[k] in '.xXbBoO'):
                    k += 1
                num_part = code_part[j:k]
                result += f'<span style="color:#0891b2;">{self.escape_html(num_part)}</span>'
                j = k
            # Check for words (keywords, identifiers)
            elif code_part[j].isalpha() or code_part[j] == '_':
                k = j
                while k < len(code_part) and (code_part[k].isalnum() or code_part[k] == '_'):
                    k += 1
                word = code_part[j:k]
                
                # Check if it's a keyword
                is_keyword = False
                if language.lower() in ['csharp', 'cs', 'c#']:
                    keywords = ['using', 'namespace', 'public', 'private', 'protected', 'internal',
                               'class', 'struct', 'interface', 'enum', 'static', 'void', 'int', 
                               'string', 'bool', 'double', 'float', 'if', 'else', 'for', 'foreach',
                               'while', 'return', 'new', 'this', 'var', 'const', 'readonly']
                    types = ['int', 'string', 'bool', 'double', 'float', 'void', 'var']
                    if word in keywords:
                        result += f'<span style="color:#dc2626;font-weight:600;">{self.escape_html(word)}</span>'
                        is_keyword = True
                    elif word in types:
                        result += f'<span style="color:#7c3aed;">{self.escape_html(word)}</span>'
                        is_keyword = True
                elif language.lower() in ['python', 'py']:
                    keywords = ['def', 'class', 'if', 'elif', 'else', 'for', 'while', 'return',
                               'import', 'from', 'as', 'try', 'except', 'finally', 'with', 'lambda',
                               'pass', 'break', 'continue', 'global', 'nonlocal', 'assert', 'yield']
                    builtins = ['True', 'False', 'None', 'print', 'len', 'range', 'int', 'str', 'list']
                    if word in keywords:
                        result += f'<span style="color:#dc2626;font-weight:600;">{self.escape_html(word)}</span>'
                        is_keyword = True
                    elif word in builtins:
                        result += f'<span style="color:#7c3aed;">{self.escape_html(word)}</span>'
                        is_keyword = True
                elif language.lower() in ['javascript', 'js', 'typescript', 'ts']:
                    keywords = ['function', 'const', 'let', 'var', 'if', 'else', 'for', 'while', 'return',
                               'class', 'extends', 'new', 'this', 'import', 'export', 'from', 'as',
                               'async', 'await', 'try', 'catch', 'finally', 'throw', 'typeof', 'instanceof']
                    types = ['string', 'number', 'boolean', 'any', 'void', 'interface', 'type', 'enum']
                    if word in keywords:
                        result += f'<span style="color:#dc2626;font-weight:600;">{self.escape_html(word)}</span>'
                        is_keyword = True
                    elif word in types and language.lower() in ['typescript', 'ts']:
                        result += f'<span style="color:#7c3aed;">{self.escape_html(word)}</span>'
                        is_keyword = True
                
                if not is_keyword:
                    # Check if it's a function/method call (followed by parenthesis)
                    if k < len(code_part) and code_part[k] == '(':
                        result += f'<span style="color:#2563eb;">{self.escape_html(word)}</span>'
                    else:
                        result += self.escape_html(word)
                j = k
            # Handle operators and other characters
            else:
                if code_part[j] in '()[]{}' :
                    result += f'<span style="color:#6b7280;">{self.escape_html(code_part[j])}</span>'
                elif code_part[j] in '+-*/%=<>!&|^~':
                    result += f'<span style="color:#ea580c;">{self.escape_html(code_part[j])}</span>'
                else:
                    result += self.escape_html(code_part[j])
                j += 1
        
        return leading_ws + result
    
    def highlight_python_line(self, cursor: QTextCursor, line: str):
        """Apply Python syntax highlighting to a line"""
        # Define formats
        keyword_format = QTextCharFormat()
        keyword_format.setFontFamily("Consolas, Monaco, monospace")
        keyword_format.setFontPointSize(9)
        keyword_format.setForeground(QColor("#cf222e"))  # Red for keywords
        keyword_format.setFontWeight(QFont.Bold)
        
        string_format = QTextCharFormat()
        string_format.setFontFamily("Consolas, Monaco, monospace")
        string_format.setFontPointSize(9)
        string_format.setForeground(QColor("#0a3069"))  # Blue for strings
        
        comment_format = QTextCharFormat()
        comment_format.setFontFamily("Consolas, Monaco, monospace")
        comment_format.setFontPointSize(9)
        comment_format.setForeground(QColor("#6e7781"))  # Gray for comments
        comment_format.setFontItalic(True)
        
        function_format = QTextCharFormat()
        function_format.setFontFamily("Consolas, Monaco, monospace")
        function_format.setFontPointSize(9)
        function_format.setForeground(QColor("#8250df"))  # Purple for functions
        
        default_format = QTextCharFormat()
        default_format.setFontFamily("Consolas, Monaco, monospace")
        default_format.setFontPointSize(9)
        default_format.setForeground(QColor("#24292e"))
        
        # Python keywords
        keywords = [
            'def', 'class', 'if', 'elif', 'else', 'for', 'while', 'return',
            'import', 'from', 'as', 'try', 'except', 'finally', 'with',
            'lambda', 'pass', 'break', 'continue', 'global', 'nonlocal',
            'assert', 'yield', 'raise', 'del', 'in', 'is', 'not', 'and', 'or',
            'True', 'False', 'None'
        ]
        
        # Check for comment
        if '#' in line:
            comment_pos = line.index('#')
            # Insert pre-comment part
            self.highlight_python_tokens(cursor, line[:comment_pos], keywords, 
                                        keyword_format, string_format, function_format, default_format)
            # Insert comment
            cursor.insertText(line[comment_pos:], comment_format)
        else:
            # Process the entire line
            self.highlight_python_tokens(cursor, line, keywords, 
                                        keyword_format, string_format, function_format, default_format)
    
    def highlight_python_tokens(self, cursor, text, keywords, keyword_format, 
                               string_format, function_format, default_format):
        """Tokenize and highlight Python code"""
        # Simple tokenization using regex
        import re
        
        # Pattern to match strings, keywords, functions, and other tokens
        pattern = r'("""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\'|"[^"]*"|\'[^\']*\'|\b\w+\b|[^\w\s]+|\s+)'
        tokens = re.findall(pattern, text)
        
        for token in tokens:
            if not token:
                continue
            
            # Check for strings
            if (token.startswith('"') and token.endswith('"')) or \
               (token.startswith("'") and token.endswith("'")):
                cursor.insertText(token, string_format)
            # Check for keywords
            elif token in keywords:
                cursor.insertText(token, keyword_format)
            # Check for function definitions (simple heuristic)
            elif token == 'def' or (len(tokens) > tokens.index(token) + 1 and 
                                   tokens[tokens.index(token) - 1] == 'def'):
                cursor.insertText(token, function_format)
            # Default
            else:
                cursor.insertText(token, default_format)
    
    def highlight_javascript_line(self, cursor: QTextCursor, line: str):
        """Apply JavaScript syntax highlighting to a line"""
        # Similar to Python but with JS keywords
        keyword_format = QTextCharFormat()
        keyword_format.setFontFamily("Consolas, Monaco, monospace")
        keyword_format.setFontPointSize(9)
        keyword_format.setForeground(QColor("#cf222e"))
        keyword_format.setFontWeight(QFont.Bold)
        
        default_format = QTextCharFormat()
        default_format.setFontFamily("Consolas, Monaco, monospace")
        default_format.setFontPointSize(9)
        default_format.setForeground(QColor("#24292e"))
        
        # For now, just insert with default format
        cursor.insertText(line, default_format)
    
    def render_simple_markdown(self, text: str, cursor: QTextCursor):
        """Render simple markdown (bold, italic, inline code)"""
        if not text.strip():
            return
        
        # Split by inline code first
        parts = re.split(r'(`[^`]+`)', text)
        
        for part in parts:
            if part.startswith('`') and part.endswith('`'):
                # Inline code
                code_format = QTextCharFormat()
                code_format.setFontFamily("Consolas, Monaco, monospace")
                code_format.setBackground(QColor("#f6f8fa"))
                code_format.setForeground(QColor("#0550ae"))
                cursor.insertText(part[1:-1], code_format)
            else:
                # Check for bold and italic
                self.render_text_formatting(part, cursor)
    
    def render_text_formatting(self, text: str, cursor: QTextCursor):
        """Render text with bold and italic formatting"""
        # Pattern for bold and italic
        pattern = r'(\*\*[^*]+\*\*|\*[^*]+\*)'
        parts = re.split(pattern, text)
        
        for part in parts:
            if not part:
                continue
            
            text_format = QTextCharFormat()
            
            if part.startswith('**') and part.endswith('**'):
                # Bold
                text_format.setFontWeight(QFont.Bold)
                cursor.insertText(part[2:-2], text_format)
            elif part.startswith('*') and part.endswith('*'):
                # Italic
                text_format.setFontItalic(True)
                cursor.insertText(part[1:-1], text_format)
            else:
                # Regular text
                cursor.insertText(part)
    
    def show_context_menu(self, position):
        """Show custom context menu"""
        menu = QMenu(self)
        
        # Copy action
        copy_action = QAction("Copy", self)
        copy_action.triggered.connect(self.copy)
        menu.addAction(copy_action)
        
        # Select All action
        select_all_action = QAction("Select All", self)
        select_all_action.triggered.connect(self.selectAll)
        menu.addAction(select_all_action)
        
        menu.addSeparator()
        
        # Copy code blocks action
        if self.code_blocks:
            copy_code_action = QAction("Copy All Code Blocks", self)
            copy_code_action.triggered.connect(self.copy_all_code_blocks)
            menu.addAction(copy_code_action)
        
        # Clear action
        clear_action = QAction("Clear Chat", self)
        clear_action.triggered.connect(self.clear_chat)
        menu.addAction(clear_action)
        
        menu.exec_(self.mapToGlobal(position))
    
    def handle_anchor_click(self, url):
        """Handle clicks on anchor links (like copy buttons)"""
        print(f"[ChatDisplay] Anchor clicked: {url.toString()}")  # Debug log
        
        url_str = url.toString()
        
        if url_str.startswith('copy:'):
            # Extract code block index
            try:
                index = int(url_str.split(':')[1])
                print(f"[ChatDisplay] Copying code block {index}")  # Debug log
                
                if 0 <= index < len(self.code_blocks):
                    # Copy code block to clipboard
                    clipboard = QApplication.clipboard()
                    clipboard.setText(self.code_blocks[index])
                    print(f"[ChatDisplay] Code copied: {len(self.code_blocks[index])} chars")  # Debug log
                    
                    # Show feedback tooltip
                    try:
                        # Get current cursor position for tooltip
                        cursor_rect = self.cursorRect()
                        if cursor_rect.isValid():
                            global_pos = self.mapToGlobal(cursor_rect.center())
                        else:
                            global_pos = self.mapToGlobal(self.rect().center())
                        
                        QToolTip.showText(global_pos, "✅ Code copied to clipboard!")
                    except Exception as e:
                        print(f"[ChatDisplay] Tooltip error: {e}")  # Debug log
                else:
                    print(f"[ChatDisplay] Invalid code block index: {index}")  # Debug log
                    
            except (ValueError, IndexError) as e:
                print(f"[ChatDisplay] Error parsing copy link: {e}")  # Debug log
            except Exception as e:
                print(f"[ChatDisplay] Unexpected error: {e}")  # Debug log
        
        # Important: Prevent any default handling
        # This stops the browser from trying to navigate
    
    def copy_all_code_blocks(self):
        """Extract and copy all code blocks to clipboard"""
        if self.code_blocks:
            clipboard = QApplication.clipboard()
            all_code = '\n\n'.join(self.code_blocks)
            clipboard.setText(all_code)
            
            QToolTip.showText(self.mapToGlobal(self.rect().center()), 
                             f"✅ {len(self.code_blocks)} code blocks copied!", 
                             self, rect=self.rect(), msecShowTime=2000)
    
    def clear_chat(self):
        """Clear all messages"""
        self.clear()
        self.messages = []
        self.current_streaming_message = None
        self.code_blocks = []
    
    def escape_html(self, text: str) -> str:
        """Escape HTML special characters"""
        return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&#39;')
    
    def get_all_messages(self):
        """Get all messages as a list"""
        return [{'role': msg['role'], 'content': msg['content']} 
                for msg in self.messages if not msg.get('streaming', False)]
