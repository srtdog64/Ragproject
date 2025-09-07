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
    
    def __init__(self):
        super().__init__()
        self.setReadOnly(True)
        self.setAcceptRichText(True)
        
        # Setup markdown renderer
        self.markdown_renderer = MarkdownRenderer(self)
        
        # Setup styles
        self.setup_styles()
        
        # Setup context menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        
        # Setup anchor click handling
        self.anchorClicked.connect(self.handle_anchor_click)
        self.setOpenExternalLinks(False)  # Handle links internally
        
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
    
    def render_code_block(self, code_block: str, cursor: QTextCursor):
        """Render a code block with proper formatting and copy button"""
        lines = code_block.split('\n')
        
        # Extract language
        language = ''
        if lines[0].startswith('```'):
            language = lines[0][3:].strip()
            lines = lines[1:-1] if lines[-1] == '```' else lines[1:]
        
        # Store code content for copying
        code_content = '\n'.join(lines)
        
        # Store code block for later copying
        if not hasattr(self, 'code_blocks'):
            self.code_blocks = []
        code_block_index = len(self.code_blocks)
        self.code_blocks.append(code_content)
        
        # Insert a block for the code container
        cursor.insertBlock()
        
        # Create the header block format
        header_format = QTextBlockFormat()
        header_format.setBackground(QColor("#f0f0f0"))
        header_format.setTopMargin(5)
        header_format.setBottomMargin(0)
        header_format.setLeftMargin(10)
        header_format.setRightMargin(10)
        
        cursor.setBlockFormat(header_format)
        
        # Insert language label and copy button in header
        if language:
            lang_format = QTextCharFormat()
            lang_format.setFontWeight(QFont.Bold)
            lang_format.setForeground(QColor("#6f42c1"))
            lang_format.setFontFamily("Consolas, Monaco, monospace")
            lang_format.setFontPointSize(9)
            cursor.insertText(f"{language}", lang_format)
        
        # Add copy button
        cursor.insertText("  ")
        copy_format = QTextCharFormat()
        copy_format.setForeground(QColor("#0366d6"))
        copy_format.setFontUnderline(True)
        copy_format.setAnchor(True)
        copy_format.setAnchorHref(f"copy:{code_block_index}")
        copy_format.setToolTip("Click to copy code")
        cursor.insertText("📋 Copy", copy_format)
        
        # Create code block format
        code_block_format = QTextBlockFormat()
        code_block_format.setBackground(QColor("#f6f8fa"))
        code_block_format.setLeftMargin(10)
        code_block_format.setRightMargin(10)
        code_block_format.setTopMargin(0)
        code_block_format.setBottomMargin(5)
        
        # Insert code lines
        code_format = QTextCharFormat()
        code_format.setFontFamily("Consolas, Monaco, 'Courier New', monospace")
        code_format.setFontPointSize(9)
        code_format.setForeground(QColor("#24292e"))
        
        for i, line in enumerate(lines):
            cursor.insertBlock()
            cursor.setBlockFormat(code_block_format)
            
            # Apply syntax highlighting
            if language.lower() in ['python', 'py']:
                self.highlight_python_line(cursor, line)
            elif language.lower() in ['javascript', 'js', 'typescript', 'ts']:
                self.highlight_javascript_line(cursor, line)
            else:
                # No highlighting, just insert the line
                cursor.insertText(line, code_format)
        
        # Reset format for next content
        cursor.insertBlock()
        default_format = QTextBlockFormat()
        cursor.setBlockFormat(default_format)
    
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
        url_str = url.toString()
        
        if url_str.startswith('copy:'):
            # Extract code block index
            try:
                index = int(url_str.split(':')[1])
                if 0 <= index < len(self.code_blocks):
                    # Copy code block to clipboard
                    clipboard = QApplication.clipboard()
                    clipboard.setText(self.code_blocks[index])
                    
                    # Show feedback
                    QToolTip.showText(self.mapToGlobal(self.cursorRect().center()), 
                                     "✅ Code copied to clipboard!", self, rect=self.rect(), msecShowTime=2000)
            except (ValueError, IndexError):
                pass
    
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
    
    def get_all_messages(self):
        """Get all messages as a list"""
        return [{'role': msg['role'], 'content': msg['content']} 
                for msg in self.messages if not msg.get('streaming', False)]
