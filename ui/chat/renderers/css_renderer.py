# ui/chat/renderers/css_renderer.py
"""
CSS/SCSS/SASS code renderer
"""
from .base_renderer import BaseCodeRenderer
import re


class CssRenderer(BaseCodeRenderer):
    """CSS/SCSS/SASS code renderer"""
    
    def get_keywords(self):
        """CSS keywords and properties"""
        return [
            'color', 'background', 'background-color', 'background-image',
            'background-position', 'background-repeat', 'background-size',
            'border', 'border-width', 'border-style', 'border-color',
            'border-radius', 'margin', 'padding', 'width', 'height',
            'min-width', 'max-width', 'min-height', 'max-height',
            'display', 'position', 'top', 'right', 'bottom', 'left',
            'float', 'clear', 'overflow', 'z-index', 'opacity',
            'font', 'font-family', 'font-size', 'font-weight', 'font-style',
            'text-align', 'text-decoration', 'text-transform', 'line-height',
            'letter-spacing', 'word-spacing', 'white-space', 'vertical-align',
            'flex', 'flex-direction', 'flex-wrap', 'justify-content',
            'align-items', 'align-content', 'grid', 'grid-template',
            'grid-template-columns', 'grid-template-rows', 'gap',
            'transform', 'transition', 'animation', 'box-shadow',
            'text-shadow', 'cursor', 'visibility', 'content'
        ]
    
    def get_builtin_values(self):
        """CSS values and units"""
        return [
            'inherit', 'initial', 'unset', 'auto', 'none', 'block', 'inline',
            'inline-block', 'flex', 'grid', 'absolute', 'relative', 'fixed',
            'sticky', 'static', 'bold', 'normal', 'italic', 'center', 'left',
            'right', 'justify', 'uppercase', 'lowercase', 'capitalize',
            'transparent', 'solid', 'dashed', 'dotted', 'hidden', 'visible',
            'scroll', 'pointer', 'default', 'ease', 'linear', 'ease-in',
            'ease-out', 'ease-in-out'
        ]
    
    def get_comment_pattern(self):
        """CSS comment pattern (not used in standard rendering)"""
        return None  # CSS uses /* */ for comments
    
    def render_line(self, cursor, line, line_number=0):
        """Render CSS line with syntax highlighting"""
        # Preserve indentation
        leading_spaces = len(line) - len(line.lstrip())
        if leading_spaces > 0:
            cursor.insertText(' ' * leading_spaces, self.code_format)
            line = line.lstrip()
        
        # Check for different CSS patterns
        if '/*' in line or '*/' in line:
            # Comment
            cursor.insertText(line, self.comment_format)
        elif line.strip().startswith('@'):
            # At-rule (@media, @import, etc.)
            self.render_at_rule(cursor, line)
        elif '{' in line or '}' in line:
            # Selector or block delimiter
            self.render_selector_or_block(cursor, line)
        elif ':' in line and not line.strip().startswith('//'):
            # Property declaration
            self.render_property(cursor, line)
        else:
            # Default rendering
            cursor.insertText(line, self.code_format)
    
    def render_at_rule(self, cursor, line):
        """Render CSS at-rules"""
        parts = line.split(None, 1)
        if parts:
            cursor.insertText(parts[0], self.keyword_format)
            if len(parts) > 1:
                cursor.insertText(' ' + parts[1], self.code_format)
    
    def render_selector_or_block(self, cursor, line):
        """Render CSS selectors and block delimiters"""
        # Simple rendering for selectors
        parts = re.split(r'([{}])', line)
        for part in parts:
            if part in '{}':
                cursor.insertText(part, self.operator_format)
            else:
                cursor.insertText(part, self.function_format)
    
    def render_property(self, cursor, line):
        """Render CSS property declarations"""
        if ':' in line:
            prop, value = line.split(':', 1)
            # Property name
            cursor.insertText(prop.strip(), self.keyword_format)
            cursor.insertText(': ', self.operator_format)
            
            # Property value
            value = value.strip()
            if value.endswith(';'):
                cursor.insertText(value[:-1], self.string_format)
                cursor.insertText(';', self.operator_format)
            else:
                cursor.insertText(value, self.string_format)
        else:
            cursor.insertText(line, self.code_format)
