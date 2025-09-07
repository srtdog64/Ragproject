# ui/chat/renderers/javascript_renderer.py
"""
JavaScript/TypeScript code renderer
"""
from .base_renderer import BaseCodeRenderer


class JavaScriptRenderer(BaseCodeRenderer):
    """JavaScript/TypeScript code renderer"""
    
    def get_keywords(self):
        """JavaScript keywords"""
        return [
            'async', 'await', 'break', 'case', 'catch', 'class', 'const',
            'continue', 'debugger', 'default', 'delete', 'do', 'else', 'export',
            'extends', 'finally', 'for', 'function', 'if', 'import', 'in',
            'instanceof', 'let', 'new', 'return', 'super', 'switch', 'this',
            'throw', 'try', 'typeof', 'var', 'void', 'while', 'with', 'yield',
            'enum', 'implements', 'interface', 'package', 'private', 'protected',
            'public', 'static', 'await', 'of', 'as', 'from', 'get', 'set',
            'namespace', 'type', 'declare', 'readonly', 'abstract', 'override'
        ]
    
    def get_builtin_functions(self):
        """JavaScript built-in objects and functions"""
        return [
            'Array', 'Boolean', 'Date', 'Error', 'Function', 'JSON', 'Math',
            'Number', 'Object', 'Promise', 'Proxy', 'Reflect', 'RegExp',
            'String', 'Symbol', 'console', 'document', 'window', 'global',
            'process', 'Buffer', 'setTimeout', 'setInterval', 'clearTimeout',
            'clearInterval', 'setImmediate', 'clearImmediate', 'require',
            'module', 'exports', '__dirname', '__filename', 'parseInt',
            'parseFloat', 'isNaN', 'isFinite', 'encodeURI', 'decodeURI',
            'encodeURIComponent', 'decodeURIComponent', 'alert', 'confirm',
            'prompt', 'Map', 'Set', 'WeakMap', 'WeakSet', 'Intl'
        ]
    
    def get_builtin_values(self):
        """JavaScript built-in values"""
        return ['true', 'false', 'null', 'undefined', 'NaN', 'Infinity']
    
    def get_operators(self):
        """JavaScript operators"""
        return [
            '+', '-', '*', '/', '%', '**', '=', '==', '===', '!=', '!==',
            '<', '>', '<=', '>=', '&&', '||', '!', '&', '|', '^', '~',
            '<<', '>>', '>>>', '+=', '-=', '*=', '/=', '%=', '**=', '&=',
            '|=', '^=', '<<=', '>>=', '>>>=', '++', '--', '?', ':', '.',
            '...', '=>', '?.'
        ]
    
    def get_comment_pattern(self):
        """JavaScript comment pattern"""
        return '//'
