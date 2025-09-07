# ui/chat/renderers/typescript_renderer.py
"""
TypeScript-specific code renderer
"""
from .base_renderer import BaseCodeRenderer


class TypeScriptRenderer(BaseCodeRenderer):
    """TypeScript specific code renderer"""
    
    def get_keywords(self):
        """TypeScript keywords"""
        return [
            # JavaScript keywords
            'function', 'const', 'let', 'var', 'if', 'else', 'for', 'while', 'return',
            'class', 'extends', 'new', 'this', 'import', 'export', 'from', 'as',
            'async', 'await', 'try', 'catch', 'finally', 'throw', 'typeof', 'instanceof',
            'switch', 'case', 'default', 'break', 'continue', 'do', 'yield',
            'delete', 'in', 'of', 'with', 'debugger', 'super', 'static',
            
            # TypeScript specific
            'interface', 'type', 'enum', 'namespace', 'module', 'declare',
            'abstract', 'implements', 'private', 'protected', 'public',
            'readonly', 'get', 'set', 'keyof', 'infer', 'is', 'never',
            'unknown', 'any', 'void', 'null', 'undefined'
        ]
    
    def get_builtin_values(self):
        """TypeScript built-in values"""
        return ['true', 'false', 'null', 'undefined', 'NaN', 'Infinity']
    
    def get_builtin_functions(self):
        """Common TypeScript/JavaScript methods and types"""
        return [
            # Built-in objects
            'Object', 'Array', 'String', 'Number', 'Boolean', 'Date', 'RegExp',
            'Map', 'Set', 'WeakMap', 'WeakSet', 'Promise', 'Symbol', 'Error',
            
            # Common methods
            'console', 'log', 'error', 'warn', 'info', 'debug',
            'JSON', 'stringify', 'parse', 'Math', 'random', 'floor', 'ceil',
            'setTimeout', 'setInterval', 'clearTimeout', 'clearInterval',
            
            # TypeScript utility types
            'Partial', 'Required', 'Readonly', 'Record', 'Pick', 'Omit',
            'Exclude', 'Extract', 'NonNullable', 'ReturnType', 'InstanceType'
        ]
    
    def get_types(self):
        """TypeScript types"""
        return [
            'string', 'number', 'boolean', 'any', 'void', 'never', 'unknown',
            'object', 'symbol', 'bigint', 'undefined', 'null'
        ]
    
    def get_comment_pattern(self):
        """TypeScript uses // for single-line comments"""
        return '//'
    
    def render_line(self, cursor, line, line_number=0):
        """Override to apply auto-indentation correction"""
        # Use base class rendering which now includes proper indentation
        super().render_line(cursor, line, line_number)
