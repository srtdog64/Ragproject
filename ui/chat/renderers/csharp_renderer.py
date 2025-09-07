# ui/chat/renderers/csharp_renderer.py
"""
C# code renderer
"""
from .base_renderer import BaseCodeRenderer


class CSharpRenderer(BaseCodeRenderer):
    """C# specific code renderer"""
    
    def get_keywords(self):
        """C# keywords"""
        return [
            # Control flow
            'if', 'else', 'switch', 'case', 'default', 'for', 'foreach', 'while', 'do',
            'break', 'continue', 'return', 'goto', 'throw', 'try', 'catch', 'finally',
            'when', 'yield',
            
            # Type keywords
            'class', 'struct', 'interface', 'enum', 'delegate', 'namespace', 'using',
            'public', 'private', 'protected', 'internal', 'static', 'const', 'readonly',
            'volatile', 'sealed', 'abstract', 'virtual', 'override', 'extern', 'unsafe',
            'fixed', 'partial', 'async', 'await',
            
            # Value types
            'bool', 'byte', 'sbyte', 'char', 'decimal', 'double', 'float', 'int', 'uint',
            'long', 'ulong', 'short', 'ushort', 'void', 'object', 'string', 'dynamic',
            
            # Other keywords
            'new', 'this', 'base', 'sizeof', 'typeof', 'nameof', 'is', 'as', 'in', 'out',
            'ref', 'params', 'get', 'set', 'value', 'where', 'select', 'from', 'let',
            'orderby', 'group', 'into', 'join', 'equals', 'by', 'on', 'ascending',
            'descending', 'var', 'lock', 'checked', 'unchecked', 'stackalloc',
            'implicit', 'explicit', 'operator', 'event', 'add', 'remove'
        ]
    
    def get_builtin_values(self):
        """C# built-in values"""
        return ['true', 'false', 'null', 'default']
    
    def get_builtin_functions(self):
        """Common C# methods and types"""
        return [
            # System types
            'Console', 'WriteLine', 'ReadLine', 'Write', 'Read',
            'String', 'Int32', 'Int64', 'Double', 'Boolean', 'DateTime',
            'List', 'Dictionary', 'Array', 'IEnumerable', 'IList', 'ICollection',
            'Task', 'Action', 'Func', 'Predicate',
            
            # Common methods
            'ToString', 'Equals', 'GetHashCode', 'GetType', 'Parse', 'TryParse',
            'Format', 'IsNullOrEmpty', 'IsNullOrWhiteSpace', 'Join', 'Split',
            'Contains', 'IndexOf', 'Substring', 'Replace', 'Trim', 'ToUpper', 'ToLower',
            'Add', 'Remove', 'Clear', 'Count', 'FirstOrDefault', 'Where', 'Select',
            'OrderBy', 'GroupBy', 'Any', 'All', 'Sum', 'Average', 'Max', 'Min',
            
            # Attributes
            'Serializable', 'Obsolete', 'DllImport', 'Conditional', 'DebuggerDisplay'
        ]
    
    def get_comment_pattern(self):
        """C# uses // for single-line comments"""
        return '//'
    
    def render_line_as_html(self, line: str, line_number: int = 0) -> str:
        """Override to handle C# specific syntax like attributes and regions"""
        # Check for attributes
        stripped = line.strip()
        if stripped.startswith('[') and ']' in stripped:
            # This might be an attribute
            return super().render_line_as_html(line, line_number)
        
        # Check for preprocessor directives
        if stripped.startswith('#'):
            # Handle #region, #endregion, #if, etc.
            indent = len(line) - len(line.lstrip())
            indent_html = '&nbsp;' * indent
            return f'{indent_html}<span style="color:#9a9a9a;font-style:italic;">{self.escape_html(stripped)}</span>'
        
        # Check for XML documentation comments
        if stripped.startswith('///'):
            indent = len(line) - len(line.lstrip())
            indent_html = '&nbsp;' * indent
            return f'{indent_html}<span style="color:#6a9955;">{self.escape_html(stripped)}</span>'
        
        # Use base implementation for everything else
        return super().render_line_as_html(line, line_number)
