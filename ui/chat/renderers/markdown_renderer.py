# ui/chat/renderers/markdown_renderer.py
"""
Markdown code renderer
"""
from .base_renderer import BaseCodeRenderer
import re


class MarkdownCodeRenderer(BaseCodeRenderer):
    """Markdown code renderer"""
    
    def render_line(self, cursor, line, line_number=0):
        """Render Markdown line with syntax highlighting"""
        # Preserve indentation
        leading_spaces = len(line) - len(line.lstrip())
        if leading_spaces > 0:
            cursor.insertText(' ' * leading_spaces, self.code_format)
            line = line.lstrip()
        
        # Headers
        if line.startswith('#'):
            level = len(line) - len(line.lstrip('#'))
            cursor.insertText('#' * level, self.keyword_format)
            cursor.insertText(line[level:], self.code_format)
        # Bold
        elif '**' in line or '__' in line:
            self.render_with_formatting(cursor, line)
        # Lists
        elif re.match(r'^[-*+]\s', line) or re.match(r'^\d+\.\s', line):
            self.render_list_item(cursor, line)
        # Links
        elif '[' in line and '](' in line:
            self.render_with_links(cursor, line)
        # Code blocks
        elif line.startswith('```'):
            cursor.insertText(line, self.operator_format)
        # Blockquote
        elif line.startswith('>'):
            cursor.insertText('>', self.operator_format)
            cursor.insertText(line[1:], self.code_format)
        # Horizontal rule
        elif re.match(r'^[-*_]{3,}$', line.strip()):
            cursor.insertText(line, self.operator_format)
        else:
            cursor.insertText(line, self.code_format)
    
    def render_with_formatting(self, cursor, text):
        """Render text with bold/italic formatting"""
        pattern = r'(\*\*[^*]+\*\*|\*[^*]+\*|__[^_]+__|_[^_]+_|`[^`]+`)'
        parts = re.split(pattern, text)
        
        for part in parts:
            if not part:
                continue
            if part.startswith('**') and part.endswith('**'):
                cursor.insertText('**', self.operator_format)
                cursor.insertText(part[2:-2], self.keyword_format)
                cursor.insertText('**', self.operator_format)
            elif part.startswith('__') and part.endswith('__'):
                cursor.insertText('__', self.operator_format)
                cursor.insertText(part[2:-2], self.keyword_format)
                cursor.insertText('__', self.operator_format)
            elif part.startswith('*') and part.endswith('*'):
                cursor.insertText('*', self.operator_format)
                cursor.insertText(part[1:-1], self.function_format)
                cursor.insertText('*', self.operator_format)
            elif part.startswith('_') and part.endswith('_'):
                cursor.insertText('_', self.operator_format)
                cursor.insertText(part[1:-1], self.function_format)
                cursor.insertText('_', self.operator_format)
            elif part.startswith('`') and part.endswith('`'):
                cursor.insertText('`', self.operator_format)
                cursor.insertText(part[1:-1], self.string_format)
                cursor.insertText('`', self.operator_format)
            else:
                cursor.insertText(part, self.code_format)
    
    def render_list_item(self, cursor, line):
        """Render list items"""
        match = re.match(r'^([-*+]|\d+\.)\s', line)
        if match:
            marker = match.group(1)
            cursor.insertText(marker, self.operator_format)
            cursor.insertText(line[len(marker):], self.code_format)
        else:
            cursor.insertText(line, self.code_format)
    
    def render_with_links(self, cursor, text):
        """Render text with links"""
        pattern = r'(\[([^\]]+)\]\(([^)]+)\))'
        parts = re.split(pattern, text)
        
        i = 0
        while i < len(parts):
            if i + 3 < len(parts) and parts[i].startswith('['):
                # Link found
                cursor.insertText('[', self.operator_format)
                cursor.insertText(parts[i+1], self.function_format)
                cursor.insertText('](', self.operator_format)
                cursor.insertText(parts[i+2], self.string_format)
                cursor.insertText(')', self.operator_format)
                i += 4
            else:
                if parts[i]:
                    cursor.insertText(parts[i], self.code_format)
                i += 1
