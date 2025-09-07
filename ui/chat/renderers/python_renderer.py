# ui/chat/renderers/python_renderer.py
"""
Python-specific code renderer
"""
import re
from .base_renderer import BaseCodeRenderer


class PythonRenderer(BaseCodeRenderer):
    """Python code renderer with syntax highlighting"""
    
    def get_keywords(self):
        """Python keywords"""
        return [
            'False', 'None', 'True', 'and', 'as', 'assert', 'async', 'await',
            'break', 'class', 'continue', 'def', 'del', 'elif', 'else', 'except',
            'finally', 'for', 'from', 'global', 'if', 'import', 'in', 'is',
            'lambda', 'nonlocal', 'not', 'or', 'pass', 'raise', 'return', 'try',
            'while', 'with', 'yield', 'match', 'case'
        ]
    
    def get_builtin_functions(self):
        """Python built-in functions"""
        return [
            'abs', 'all', 'any', 'ascii', 'bin', 'bool', 'breakpoint', 'bytearray',
            'bytes', 'callable', 'chr', 'classmethod', 'compile', 'complex',
            'delattr', 'dict', 'dir', 'divmod', 'enumerate', 'eval', 'exec',
            'filter', 'float', 'format', 'frozenset', 'getattr', 'globals',
            'hasattr', 'hash', 'help', 'hex', 'id', 'input', 'int', 'isinstance',
            'issubclass', 'iter', 'len', 'list', 'locals', 'map', 'max',
            'memoryview', 'min', 'next', 'object', 'oct', 'open', 'ord', 'pow',
            'print', 'property', 'range', 'repr', 'reversed', 'round', 'set',
            'setattr', 'slice', 'sorted', 'staticmethod', 'str', 'sum', 'super',
            'tuple', 'type', 'vars', 'zip', '__import__'
        ]
    
    def get_builtin_values(self):
        """Python built-in values"""
        return ['True', 'False', 'None', 'self', 'cls']
    
    def get_operators(self):
        """Python operators"""
        return [
            '+', '-', '*', '/', '//', '%', '**', '=', '==', '!=', '<', '>',
            '<=', '>=', 'and', 'or', 'not', 'in', 'is', '&', '|', '^', '~',
            '<<', '>>', '+=', '-=', '*=', '/=', '//=', '%=', '**=', '&=',
            '|=', '^=', '<<=', '>>=', ':=', '->', '=>'
        ]
    
    def get_comment_pattern(self):
        """Python comment pattern"""
        return '#'
    
    def render_line(self, cursor, line, line_number=0):
        """Enhanced Python line rendering with better indentation handling"""
        # Special handling for Python decorators
        if line.lstrip().startswith('@'):
            stripped = line.lstrip()
            leading_spaces = len(line) - len(stripped)
            if leading_spaces > 0:
                cursor.insertText(' ' * leading_spaces, self.code_format)
            
            # Find decorator name
            match = re.match(r'(@\w+)', stripped)
            if match:
                cursor.insertText(match.group(1), self.builtin_format)
                remaining = stripped[len(match.group(1)):]
                self.render_tokens(cursor, remaining)
            else:
                cursor.insertText(stripped, self.code_format)
        else:
            # Use base class rendering
            super().render_line(cursor, line, line_number)
