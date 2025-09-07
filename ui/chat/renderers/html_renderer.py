# ui/chat/renderers/html_renderer.py
"""
HTML/XML code renderer
"""
from .base_renderer import BaseCodeRenderer
import re


class HtmlRenderer(BaseCodeRenderer):
    """HTML/XML code renderer"""
    
    def render_line(self, cursor, line, line_number=0):
        """Render HTML line with tag highlighting"""
        # Preserve indentation
        leading_spaces = len(line) - len(line.lstrip())
        if leading_spaces > 0:
            cursor.insertText(' ' * leading_spaces, self.code_format)
            line = line.lstrip()
        
        # Pattern for HTML elements
        pattern = r'(<[^>]+>)|([^<]+)'
        matches = re.findall(pattern, line)
        
        for tag, text in matches:
            if tag:
                # Parse tag components
                self.render_tag(cursor, tag)
            elif text:
                cursor.insertText(text, self.code_format)
    
    def render_tag(self, cursor, tag):
        """Render an HTML tag with syntax highlighting"""
        # Pattern to parse tag components
        tag_pattern = r'<(/?)(\w+)((?:\s+[\w-]+(?:=["\'][^"\']*["\'])?)*)\s*(/?)>'
        match = re.match(tag_pattern, tag)
        
        if match:
            closing_slash, tag_name, attributes, self_closing = match.groups()
            
            # Opening bracket
            cursor.insertText('<', self.operator_format)
            
            # Closing slash if present
            if closing_slash:
                cursor.insertText('/', self.operator_format)
            
            # Tag name
            cursor.insertText(tag_name, self.keyword_format)
            
            # Attributes
            if attributes:
                self.render_attributes(cursor, attributes)
            
            # Self-closing slash if present
            if self_closing:
                cursor.insertText('/', self.operator_format)
            
            # Closing bracket
            cursor.insertText('>', self.operator_format)
        else:
            # Fallback for non-standard tags
            cursor.insertText(tag, self.code_format)
    
    def render_attributes(self, cursor, attributes_str):
        """Render HTML attributes with syntax highlighting"""
        # Pattern for attributes
        attr_pattern = r'\s+([\w-]+)(?:=(["\'])([^"\']*)\2)?'
        matches = re.findall(attr_pattern, attributes_str)
        
        for attr_name, quote, attr_value in matches:
            cursor.insertText(' ', self.code_format)
            cursor.insertText(attr_name, self.function_format)
            
            if quote:
                cursor.insertText('=', self.operator_format)
                cursor.insertText(quote + attr_value + quote, self.string_format)
