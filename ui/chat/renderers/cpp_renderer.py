# ui/chat/renderers/cpp_renderer.py
"""
C/C++ code renderer
"""
from .base_renderer import BaseCodeRenderer


class CppRenderer(BaseCodeRenderer):
    """C/C++ code renderer"""
    
    def get_keywords(self):
        """C/C++ keywords"""
        return [
            'alignas', 'alignof', 'and', 'and_eq', 'asm', 'auto', 'bitand',
            'bitor', 'bool', 'break', 'case', 'catch', 'char', 'char8_t',
            'char16_t', 'char32_t', 'class', 'compl', 'concept', 'const',
            'consteval', 'constexpr', 'constinit', 'const_cast', 'continue',
            'co_await', 'co_return', 'co_yield', 'decltype', 'default', 'delete',
            'do', 'double', 'dynamic_cast', 'else', 'enum', 'explicit', 'export',
            'extern', 'false', 'float', 'for', 'friend', 'goto', 'if', 'inline',
            'int', 'long', 'mutable', 'namespace', 'new', 'noexcept', 'not',
            'not_eq', 'nullptr', 'operator', 'or', 'or_eq', 'private', 'protected',
            'public', 'register', 'reinterpret_cast', 'requires', 'return',
            'short', 'signed', 'sizeof', 'static', 'static_assert', 'static_cast',
            'struct', 'switch', 'template', 'this', 'thread_local', 'throw',
            'true', 'try', 'typedef', 'typeid', 'typename', 'union', 'unsigned',
            'using', 'virtual', 'void', 'volatile', 'wchar_t', 'while', 'xor',
            'xor_eq', 'override', 'final'
        ]
    
    def get_builtin_functions(self):
        """C/C++ standard library functions"""
        return [
            'printf', 'scanf', 'cout', 'cin', 'endl', 'malloc', 'free',
            'calloc', 'realloc', 'memcpy', 'memmove', 'memset', 'memcmp',
            'strlen', 'strcpy', 'strncpy', 'strcat', 'strncat', 'strcmp',
            'strncmp', 'strchr', 'strrchr', 'strstr', 'strtok', 'atoi',
            'atof', 'atol', 'abs', 'fabs', 'sqrt', 'pow', 'sin', 'cos',
            'tan', 'log', 'exp', 'ceil', 'floor', 'round', 'push_back',
            'pop_back', 'begin', 'end', 'size', 'empty', 'clear', 'insert',
            'erase', 'find', 'sort', 'reverse', 'swap', 'min', 'max'
        ]
    
    def get_builtin_values(self):
        """C/C++ built-in values"""
        return ['true', 'false', 'nullptr', 'NULL']
    
    def get_comment_pattern(self):
        """C/C++ comment pattern"""
        return '//'
