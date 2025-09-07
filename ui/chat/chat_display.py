# ui/chat/chat_display.py
"""
Enhanced chat display widget with improved code rendering
- Fixes: indentation preservation & per-line grid with line numbers
"""
from PySide6.QtWidgets import QTextBrowser, QMenu, QApplication, QToolTip
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QTextCursor, QTextCharFormat, QFont, QColor, QAction
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

        # Prevent default navigation; handle links internally
        self.setOpenExternalLinks(False)
        self.setOpenLinks(False)
        self.anchorClicked.connect(self.handle_anchor_click)

        # Message tracking
        self.messages = []
        self.current_streaming_message = None
        self.code_blocks = []  # Store raw code blocks for copy

    def setup_styles(self):
        """Setup display styles"""
        font = QFont("Segoe UI", 10)
        self.setFont(font)
        self.setStyleSheet("""
            QTextBrowser {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 10px;
                selection-background-color: #b3d9ff;
            }
            /* Mild monospace for inline code inside markdown */
            .inline-code {
                background: #f6f8fa;
                color: #0550ae;
                font-family: Consolas, Monaco, monospace;
                padding: 1px 3px;
                border-radius: 3px;
            }
        """)

    # ---------- Public API ----------

    def add_message(self, role: str, content: str, streaming: bool = False):
        """Add a message to the display"""
        if streaming and self.current_streaming_message:
            self.update_streaming_message(content)
        else:
            self.append_message(role, content, streaming)

    def append_message(self, role: str, content: str, streaming: bool):
        """Append a new message"""
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)

        # Spacing between messages
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

        start_pos = self.current_streaming_message['start_position']
        cursor = self.textCursor()
        cursor.setPosition(start_pos)
        cursor.movePosition(QTextCursor.End, QTextCursor.KeepAnchor)
        cursor.removeSelectedText()

        self.current_streaming_message['content'] = new_content
        self.render_content(new_content, start_pos)
        self.ensureCursorVisible()

    def finish_streaming(self):
        """Mark streaming as finished"""
        if self.current_streaming_message:
            self.current_streaming_message['streaming'] = False
            self.current_streaming_message = None

    # ---------- Rendering ----------

    def render_content(self, content: str, start_position: int):
        """Render content with markdown+code support"""
        cursor = self.textCursor()
        if start_position > self.document().characterCount():
            start_position = self.document().characterCount() - 1
        cursor.setPosition(max(0, start_position))

        if '```' in content:
            self.render_with_code_blocks(content, cursor)
        else:
            self.render_simple_markdown(content, cursor)

    def render_with_code_blocks(self, content: str, cursor: QTextCursor):
        """Render content with proper code block handling"""
        parts = re.split(r'(```[\s\S]*?```)', content)
        for part in parts:
            if part.startswith('```') and part.endswith('```'):
                self.render_code_block(part, cursor)
            else:
                if part.strip():
                    self.render_simple_markdown(part, cursor)

    def filter_code_content(self, lines: list, language: str) -> str:
        """
        Filter out non-code content from code blocks while preserving code indentation.
        (Keeps docstrings/comments tied to code; drops pure Korean description lines.)
        """
        code_lines = []
        in_docstring = False
        docstring_quotes = None

        for line in lines:
            has_korean = any('\uac00' <= ch <= '\ud7a3' for ch in line)

            if language and language.lower() in ['python', 'py']:
                if '"""' in line or "'''" in line:
                    if not in_docstring:
                        in_docstring = True
                        docstring_quotes = '"""' if '"""' in line else "'''"
                        code_lines.append(line)
                    elif docstring_quotes in line:
                        in_docstring = False
                        docstring_quotes = None
                        code_lines.append(line)
                    else:
                        code_lines.append(line)
                    continue
                if in_docstring:
                    code_lines.append(line)
                    continue

            if has_korean:
                stripped = line.strip()
                if stripped and ('\uac00' <= stripped[0] <= '\ud7a3'):
                    if not any(sym in stripped for sym in ['=', '(', ')', '[', ']', '{', '}', ';', ':', '<', '>']):
                        continue
                if language and language.lower() in ['python', 'py']:
                    if '#' in line:
                        code_part = line.split('#')[0]
                        if code_part.rstrip():
                            code_lines.append(code_part.rstrip())
                        continue
                    elif any(kw in line for kw in ['def ', 'class ', 'import ', 'from ', 'return ', 'if ', 'for ', 'while ', 'print(', '=']):
                        code_lines.append(line)
                    else:
                        continue
                elif language and language.lower() in ['javascript', 'js', 'typescript', 'ts', 'java', 'c', 'cpp', 'c++', 'csharp', 'cs', 'c#']:
                    if '//' in line:
                        code_part = line.split('//')[0]
                        if code_part.rstrip():
                            code_lines.append(code_part.rstrip())
                        continue
                    elif any(kw in line for kw in ['{', '}', ';', 'public', 'private', 'class', 'void', 'int', 'string', 'var', 'let', 'const', 'function']):
                        code_lines.append(line)
                    else:
                        continue
                else:
                    if any(sym in line for sym in ['=', '(', ')', '{', '}', '[', ']', ';']):
                        code_lines.append(line)
                    else:
                        continue
            else:
                code_lines.append(line)

        return '\n'.join(code_lines)

    def render_code_block(self, code_block: str, cursor: QTextCursor):
        """
        Render a code block with:
        - Line numbers gutter
        - Per-line grid (table rows/columns)
        - Correct indentation (no collapse) and explicit line breaks
        """
        lines = code_block.split('\n')

        # Extract language
        language = ''
        if lines and lines[0].startswith('```'):
            language = lines[0][3:].strip()
            if lines and lines[-1] == '```':
                lines = lines[1:-1]
            else:
                lines = lines[1:]

        # Filter non-code descriptions while preserving indentation
        code_content = self.filter_code_content(lines, language)

        # Save raw for clipboard copy
        if not hasattr(self, 'code_blocks'):
            self.code_blocks = []
        code_block_index = len(self.code_blocks)
        self.code_blocks.append(code_content)

        # Build HTML once (avoids per-line insertHtml issues/newline collapse)
        from .renderers import get_renderer
        renderer = get_renderer(language)

        code_lines = code_content.split('\n')

        # Header
        header_html = f"""
<div style="border:1px solid #d1d5db;border-radius:6px;margin:8px 0;font-family:Consolas,Monaco,monospace;">
  <div style="background:#f3f4f6;padding:8px 12px;border-bottom:1px solid #e5e7eb;">
    <span style="color:#7c3aed;font-weight:bold;font-size:12px;">{(language.upper() if language else 'CODE')}</span>
    <a href="copy:{code_block_index}" style="color:#2563eb;text-decoration:none;font-size:12px;float:right;">📋 Copy Code</a>
    <div style="clear:both;"></div>
  </div>
  <!-- Code grid: table ensures row/column lines & preserves layout in Qt's HTML subset -->
  <div style="background:#ffffff;">
    <table style="border-collapse:collapse;width:100%;table-layout:fixed;font-size:12px;">
      <colgroup>
        <col style="width:52px;">   <!-- gutter -->
        <col>                       <!-- code -->
      </colgroup>
"""
        # Rows
        rows_html_parts = []
        # We avoid <pre> and use per-line rows; indentation is preserved by &nbsp; from renderer.
        # Also explicitly avoid '\n' nodes; use table rows instead.
        for i, raw_line in enumerate(code_lines, start=1):
            line_html = renderer.render_line_as_html(raw_line)
            # Line number cell
            ln_cell = (
                f'<td style="vertical-align:top;border-right:1px solid #e5e7eb;'
                f'background:#f9fafb;color:#9ca3af;text-align:right;padding:2px 8px;'
                f'user-select:none;">{i}</td>'
            )
            # Code cell (horizontal scroll if supported; else expands)
            code_cell = (
                '<td style="vertical-align:top;padding:2px 10px;white-space:nowrap;">'
                f'{line_html if line_html else "&nbsp;"}'
                '</td>'
            )
            # Row border to create grid separation between lines
            row_html = f'<tr style="border-bottom:1px solid #f3f4f6;">{ln_cell}{code_cell}</tr>'
            rows_html_parts.append(row_html)

        # Footer/close
        footer_html = """
    </table>
  </div>
</div>
"""
        full_html = header_html + "".join(rows_html_parts) + footer_html
        cursor.insertHtml(full_html)
        cursor.insertBlock()  # spacing after block

    # ---------- Simple markdown ----------

    def render_simple_markdown(self, text: str, cursor: QTextCursor):
        """Render simple markdown (bold, italic, inline code)"""
        if not text.strip():
            return
        parts = re.split(r'(`[^`]+`)', text)
        for part in parts:
            if part.startswith('`') and part.endswith('`'):
                code_format = QTextCharFormat()
                code_format.setFontFamily("Consolas, Monaco, monospace")
                code_format.setBackground(QColor("#f6f8fa"))
                code_format.setForeground(QColor("#0550ae"))
                cursor.insertText(part[1:-1], code_format)
            else:
                self.render_text_formatting(part, cursor)

    def render_text_formatting(self, text: str, cursor: QTextCursor):
        """Render text with bold and italic formatting"""
        pattern = r'(\*\*[^*]+\*\*|\*[^*]+\*)'
        parts = re.split(pattern, text)
        for part in parts:
            if not part:
                continue
            text_format = QTextCharFormat()
            if part.startswith('**') and part.endswith('**'):
                text_format.setFontWeight(QFont.Bold)
                cursor.insertText(part[2:-2], text_format)
            elif part.startswith('*') and part.endswith('*'):
                text_format.setFontItalic(True)
                cursor.insertText(part[1:-1], text_format)
            else:
                cursor.insertText(part)

    # ---------- Context menu & utilities ----------

    def show_context_menu(self, position):
        """Show custom context menu"""
        menu = QMenu(self)

        copy_action = QAction("Copy", self)
        copy_action.triggered.connect(self.copy)
        menu.addAction(copy_action)

        select_all_action = QAction("Select All", self)
        select_all_action.triggered.connect(self.selectAll)
        menu.addAction(select_all_action)
        menu.addSeparator()

        if self.code_blocks:
            copy_code_action = QAction("Copy All Code Blocks", self)
            copy_code_action.triggered.connect(self.copy_all_code_blocks)
            menu.addAction(copy_code_action)

        clear_action = QAction("Clear Chat", self)
        clear_action.triggered.connect(self.clear_chat)
        menu.addAction(clear_action)

        menu.exec_(self.mapToGlobal(position))

    def handle_anchor_click(self, url: QUrl):
        """Handle clicks on anchor links (like copy buttons)"""
        url_str = url.toString()
        if url_str.startswith('copy:'):
            try:
                index = int(url_str.split(':')[1])
                if 0 <= index < len(self.code_blocks):
                    clipboard = QApplication.clipboard()
                    clipboard.setText(self.code_blocks[index])

                    # Feedback tooltip near center
                    try:
                        cursor_rect = self.cursorRect()
                        if cursor_rect.isValid():
                            global_pos = self.mapToGlobal(cursor_rect.center())
                        else:
                            global_pos = self.mapToGlobal(self.rect().center())
                        QToolTip.showText(global_pos, "✅ Code copied to clipboard!")
                    except Exception as _:
                        pass
            except Exception as _:
                pass
        # prevent default navigation

    def copy_all_code_blocks(self):
        """Extract and copy all code blocks to clipboard"""
        if self.code_blocks:
            clipboard = QApplication.clipboard()
            all_code = '\n\n'.join(self.code_blocks)
            clipboard.setText(all_code)
            QToolTip.showText(
                self.mapToGlobal(self.rect().center()),
                f"✅ {len(self.code_blocks)} code blocks copied!",
                self,
                rect=self.rect(),
                msecShowTime=2000
            )

    def clear_chat(self):
        """Clear all messages"""
        self.clear()
        self.messages = []
        self.current_streaming_message = None
        self.code_blocks = []

    def escape_html(self, text: str) -> str:
        """Escape HTML special characters"""
        return (
            text.replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#39;')
        )

    def get_all_messages(self):
        """Get all messages as a list"""
        return [
            {'role': msg['role'], 'content': msg['content']}
            for msg in self.messages if not msg.get('streaming', False)
        ]
